import sys
import os
import re
import json
import argparse
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Hardened scope for playlist orchestrations without total channel control
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CACHE_FILE = "cache.json"
TOKEN_FILE = "token.json"  # Securely track authenticated user states locally
MAX_DURATION_SECONDS = 15 * 60  # 15 minutes

BLACKLIST = [
    "live", "remix", "cover", "full album", "full ep", 
    "slowed", "sped up", "reaction"
]

# ---------------- AUTH (HARDENED FOR DISTRIBUTION) ----------------

def authenticate(log_callback=None):
    """
    Handles local token generation, re-authentication via refresh tokens,
    and fallback modes for headless environments.
    """
    creds = None
    
    # 1. Load an existing authorization token if present
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            log_msg("[!] Token file corrupted. Re-authenticating...", log_callback)

    # 2. If token is missing or dead, walk through standard OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None  # Force a full login if refresh fails
                
        if not creds:
            if not os.path.exists("client_secret.json"):
                raise FileNotFoundError(
                    "Missing 'client_secret.json'. Please place your Google Cloud Console "
                    "OAuth credentials in the root folder before execution."
                )
                
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            
            # Robust server binding fallback for headless/remote development
            try:
                creds = flow.run_local_server(port=0, open_browser=True)
            except Exception:
                log_msg("[!] UI Browser environment missing. Falling back to console verification loop...", log_callback)
                creds = flow.run_local_server(port=0, open_browser=False)

        # 3. Cache the token so they don't have to re-login every time they sync
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

# ---------------- CACHE ----------------

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

# ---------------- UTILS ----------------

def iso8601_to_seconds(duration):
    match = re.match(r'PT((?P<h>\d+)H)?((?P<m>\d+)M)?((?P<s>\d+)S)?', duration)
    hours = int(match.group('h') or 0)
    minutes = int(match.group('m') or 0)
    seconds = int(match.group('s') or 0)
    return hours * 3600 + minutes * 60 + seconds

def is_valid_video(title, duration_seconds):
    title_lower = title.lower()
    if duration_seconds > MAX_DURATION_SECONDS:
        return False
    for word in BLACKLIST:
        if word in title_lower:
            return False
    return True

def log_msg(msg, log_callback=None):
    if log_callback:
        log_callback(msg)
    else:
        print(msg)

# ---------------- SEARCH ----------------

def search_video(youtube, query, log_callback=None):
    log_msg(f"  Searching API for: {query}", log_callback)
    try:
        search_response = youtube.search().list(
            q=query, part="snippet", type="video", maxResults=5
        ).execute()
    except Exception as e:
        log_msg(f"  [!] Search failed (Check quota limitations): {e}", log_callback)
        return None

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    if not video_ids:
        return None

    details = youtube.videos().list(
        part="contentDetails,snippet", id=",".join(video_ids)
    ).execute()

    topic_candidates = []
    fallback_candidates = []

    for item in details.get("items", []):
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        duration_seconds = iso8601_to_seconds(item["contentDetails"]["duration"])

        if is_valid_video(title, duration_seconds):
            if "topic" in channel.lower():
                topic_candidates.append(item)
            else:
                fallback_candidates.append(item)

    chosen = topic_candidates[0] if topic_candidates else (fallback_candidates[0] if fallback_candidates else None)
    if not chosen:
        return None

    return {
        "video_id": chosen["id"],
        "channel": chosen["snippet"]["channelTitle"],
        "duration": iso8601_to_seconds(chosen["contentDetails"]["duration"]),
        "last_verified": datetime.utcnow().isoformat()
    }

# ---------------- PLAYLIST MANAGEMENT ----------------

def get_or_create_playlist(youtube, title, privacy, log_callback=None):
    playlists = youtube.playlists().list(part="snippet", mine=True, maxResults=50).execute()

    for item in playlists.get("items", []):
        if item["snippet"]["title"] == title:
            log_msg(f"Found existing playlist: {title}", log_callback)
            return item["id"]

    log_msg(f"Creating new playlist: {title}", log_callback)
    response = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": "Managed via Local API Sync Engine"},
            "status": {"privacyStatus": privacy}
        }
    ).execute()
    return response["id"]

def get_playlist_items(youtube, playlist_id):
    results = {}
    next_page_token = None
    
    # Open-source scale up: handle playlists exceeding 50 items natively via pagination
    while True:
        items = youtube.playlistItems().list(
            part="snippet", playlistId=playlist_id, maxResults=50, pageToken=next_page_token
        ).execute()

        for item in items.get("items", []):
            video_id = item["snippet"]["resourceId"]["videoId"]
            results[video_id] = item["id"]

        next_page_token = items.get("nextPageToken")
        if not next_page_token:
            break
            
    return results

def add_to_playlist(youtube, playlist_id, video_id, log_callback=None):
    youtube.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
    ).execute()
    log_msg("  Added to playlist", log_callback)

def remove_from_playlist(youtube, playlist_item_id, log_callback=None):
    youtube.playlistItems().delete(id=playlist_item_id).execute()
    log_msg("  Removed from playlist", log_callback)

def read_playlist_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

# ---------------- CORE SYNC ENGINE ----------------

def sync_playlist(filepath, title=None, privacy="private", log_callback=None, progress_callback=None):
    try:
        youtube = authenticate(log_callback)
    except FileNotFoundError as e:
        log_msg(str(e), log_callback)
        raise

    cache = load_cache()
    playlist_title = title if title else os.path.splitext(os.path.basename(filepath))[0]

    log_msg(f"Syncing playlist: {playlist_title}", log_callback)
    playlist_id = get_or_create_playlist(youtube, playlist_title, privacy, log_callback)
    existing_items = get_playlist_items(youtube, playlist_id)

    desired_tracks = read_playlist_file(filepath)
    total = len(desired_tracks)
    desired_video_ids = set()

    for index, track in enumerate(desired_tracks, start=1):
        log_msg(f"Processing ({index}/{total}): {track}", log_callback)

        if track in cache:
            log_msg("  Using cached match", log_callback)
            video_data = cache[track]
        else:
            video_data = search_video(youtube, track, log_callback)
            if video_data:
                cache[track] = video_data
                log_msg(f"  Cached: {video_data['video_id']}", log_callback)
            else:
                log_msg("  Skipped (no match match found)", log_callback)
                if progress_callback:
                    progress_callback(index, total)
                continue

        video_id = video_data["video_id"]
        desired_video_ids.add(video_id)

        if video_id not in existing_items:
            log_msg("  Not in playlist, adding...", log_callback)
            add_to_playlist(youtube, playlist_id, video_id, log_callback)
        else:
            log_msg("  Already present", log_callback)

        if progress_callback:
            progress_callback(index, total)

    # Clean removal of old tracks no longer in source layout
    for video_id, playlist_item_id in existing_items.items():
        if video_id not in desired_video_ids:
            log_msg(f"Removing outdated track (ID: {video_id})", log_callback)
            remove_from_playlist(youtube, playlist_item_id, log_callback)

    save_cache(cache)
    log_msg("Sync complete.", log_callback)

def cli_main():
    parser = argparse.ArgumentParser(description="YouTube Playlist Sync Engine (Open Source Edition)")
    parser.add_argument("playlist_file", help="Path to text file containing tracks.")
    parser.add_argument("--title", help="Override title of target playlist.")
    parser.add_argument("--privacy", choices=["private", "public", "unlisted"], default="private")
    args = parser.parse_args()

    filepath = args.playlist_file
    title = args.title if args.title else os.path.splitext(os.path.basename(filepath))[0]
    sync_playlist(filepath, title=title, privacy=args.privacy)

if __name__ == "__main__":
    cli_main()
