import sys
import os
import re
import json
import argparse
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube"]
CACHE_FILE = "cache.json"

BLACKLIST = [
    "live",
    "remix",
    "cover",
    "full album",
    "full ep",
    "slowed",
    "sped up",
    "reaction"
]

# ---------------- AUTH ----------------

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)

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
    match = re.match(
        r'PT((?P<h>\d+)H)?((?P<m>\d+)M)?((?P<s>\d+)S)?',
        duration
    )
    hours = int(match.group('h') or 0)
    minutes = int(match.group('m') or 0)
    seconds = int(match.group('s') or 0)
    return hours * 3600 + minutes * 60 + seconds

def is_valid_video(title, duration_seconds, max_duration_seconds, allow_live):
    title_lower = title.lower()

    # Dynamic duration check
    if duration_seconds > max_duration_seconds:
        return False

    for word in BLACKLIST:
        # If the user explicitly checked off "allow live", bypass the "live" keyword ban
        if word == "live" and allow_live:
            continue
        if word in title_lower:
            return False

    return True

def log_msg(msg, log_callback=None):
    if log_callback:
        log_callback(msg)
    else:
        print(msg)

# ---------------- SEARCH ----------------

def search_video(youtube, query, max_duration_seconds, allow_live, log_callback=None):
    log_msg(f"  Searching API for: {query}", log_callback)
    search_response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=5
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response["items"]]
    if not video_ids:
        return None

    details = youtube.videos().list(
        part="contentDetails,snippet",
        id=",".join(video_ids)
    ).execute()

    topic_candidates = []
    fallback_candidates = []

    for item in details["items"]:
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        duration_seconds = iso8601_to_seconds(item["contentDetails"]["duration"])

        # Feed custom user parameters directly into evaluation rule
        if is_valid_video(title, duration_seconds, max_duration_seconds, allow_live):
            if "topic" in channel.lower():
                topic_candidates.append(item)
            else:
                fallback_candidates.append(item)

    chosen = None
    if topic_candidates:
        chosen = topic_candidates[0]
    elif fallback_candidates:
        chosen = fallback_candidates[0]

    if not chosen:
        return None

    return {
        "video_id": chosen["id"],
        "channel": chosen["snippet"]["channelTitle"],
        "duration": iso8601_to_seconds(chosen["contentDetails"]["duration"]),
        "last_verified": datetime.utcnow().isoformat()
    }

# ---------------- PLAYLIST ----------------

def get_or_create_playlist(youtube, title, privacy, log_callback=None):
    playlists = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
    ).execute()

    for item in playlists["items"]:
        if item["snippet"]["title"] == title:
            log_msg(f"Found existing playlist: {title}", log_callback)
            return item["id"]

    log_msg(f"Creating new playlist: {title}", log_callback)
    response = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": "Managed via API"
            },
            "status": {"privacyStatus": privacy}
        }
    ).execute()

    return response["id"]

def get_playlist_items(youtube, playlist_id):
    items = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    ).execute()

    results = {}
    for item in items["items"]:
        video_id = item["snippet"]["resourceId"]["videoId"]
        playlist_item_id = item["id"]
        results[video_id] = playlist_item_id

    return results

def add_to_playlist(youtube, playlist_id, video_id, log_callback=None):
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    ).execute()
    log_msg("  Added to playlist", log_callback)

def remove_from_playlist(youtube, playlist_item_id, log_callback=None):
    youtube.playlistItems().delete(
        id=playlist_item_id
    ).execute()
    log_msg("  Removed from playlist", log_callback)

# ---------------- FILE ----------------

def read_playlist_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# ---------------- CORE SYNC (GUI + CLI) ----------------

def sync_playlist(filepath, title=None, privacy="private", max_duration_minutes=15, allow_live=False,
                  log_callback=None, progress_callback=None):
    youtube = authenticate()
    cache = load_cache()

    # Convert minutes input into total integer seconds for verification
    max_duration_seconds = int(max_duration_minutes) * 60

    playlist_title = title if title else os.path.splitext(os.path.basename(filepath))[0]

    log_msg(f"Syncing playlist: {playlist_title}", log_callback)
    log_msg(f"Privacy: {privacy} | Max Duration: {max_duration_minutes}m | Allow Live: {allow_live}", log_callback)

    playlist_id = get_or_create_playlist(youtube, playlist_title, privacy, log_callback)
    existing_items = get_playlist_items(youtube, playlist_id)

    desired_tracks = read_playlist_file(filepath)
    total = len(desired_tracks)
    desired_video_ids = set()

    for index, track in enumerate(desired_tracks, start=1):
        log_msg(f"Processing: {track}", log_callback)

        if track in cache:
            # Check cached matches against the *current* parameter choices
            video_data = cache[track]
            if video_data["duration"] <= max_duration_seconds:
                log_msg("  Using cached match", log_callback)
            else:
                log_msg("  Cached entry violates current duration selection. Re-searching...", log_callback)
                video_data = search_video(youtube, track, max_duration_seconds, allow_live, log_callback)
        else:
            video_data = search_video(youtube, track, max_duration_seconds, allow_live, log_callback)
            if video_data:
                cache[track] = video_data
                log_msg(f"  Cached: {video_data['video_id']}", log_callback)
            else:
                log_msg("  Skipped (no match template rules satisfied)", log_callback)
                if progress_callback:
                    progress_callback(index, total)
                continue

        if video_data:
            video_id = video_data["video_id"]
            desired_video_ids.add(video_id)

            if video_id not in existing_items:
                log_msg("  Not in playlist, adding...", log_callback)
                add_to_playlist(youtube, playlist_id, video_id, log_callback)
            else:
                log_msg("  Already present", log_callback)

        if progress_callback:
            progress_callback(index, total)

    for video_id, playlist_item_id in existing_items.items():
        if video_id not in desired_video_ids:
            log_msg("Removing outdated track", log_callback)
            remove_from_playlist(youtube, playlist_item_id, log_callback)

    save_cache(cache)
    log_msg("Sync complete.", log_callback)

# ---------------- CLI ENTRYPOINT ----------------

def cli_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("playlist_file")
    parser.add_argument("--title")
    parser.add_argument("--privacy", choices=["private", "public", "unlisted"], default="private")
    # Added new execution runtime arguments
    parser.add_argument("--max-duration", type=int, default=15, help="Max duration threshold in minutes")
    parser.add_argument("--allow-live", action="store_true", help="Allow matching live performance video items")
    args = parser.parse_args()

    filepath = args.playlist_file
    title = args.title if args.title else os.path.splitext(os.path.basename(filepath))[0]

    sync_playlist(filepath, title=title, privacy=args.privacy, max_duration_minutes=args.max_duration, allow_live=args.allow_live)

if __name__ == "__main__":
    cli_main()
