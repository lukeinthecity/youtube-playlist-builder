# 🎵 YouTube Playlist Sync (Utility Edition)

A secure, desktop-first automation utility that compiles and syncs YouTube playlists directly from plain-text `.txt` files. By communicating natively with the YouTube Data API v3 from your local environment, this tool completely eliminates the friction of heavy web-app interfaces and browser-bloat.

---

## ✨ Core Mechanics & Features

* **True Idempotent Syncing:** Your text file is the single source of truth. The engine automatically adds missing tracks, skips duplicates, and cleanly prunes remote tracks that have been deleted from the local file.
* **Smart Audio Curation:** * Prioritizes official video configurations by auto-selecting **"- Topic"** channel uploads.
  * Aggressively blocks low-fidelity tracks using an internal word blacklist (`remix`, `cover`, `slowed`, `sped up`, `reaction`, etc.).
* **Dynamic Audio Filters:**
  * **User-Defined Durations:** Set precise maximum video lengths to smoothly include everything from quick 2-minute tracks to massive 30+ minute ambient soundscapes and progressive epics.
  * **Conditional Live Inclusions:** Toggle the inclusion of live performances on the fly, bypassing the standard keyword filters when you want to capture concerts or session recordings.
* **Quota Preservation Engine:** Video lookups are mapped and preserved inside a local cache file. This massively slashes expensive search quota usage (100 units per search) and makes subsequent sync executions instantaneous.
* **Dual Execution Modes:** Fully operational via a streamlined terminal interface or a native cross-platform desktop UI window.

---

## 📦 Project Structure

```text
youtube-playlist-builder/
│
├── main.py             # Core API Engine, Filter Validation & CLI Entrypoint
├── gui.py              # Tkinter-based Desktop UI with Custom Filter Controls
├── .gitignore          # Firewall configuration excluding local keys & caches
├── README.md           # Documentation
├── client_secret.json  # USER PROVIDED: Google Cloud Console OAuth Key
├── token.json          # AUTOMATIC: Secured OAuth Session Persistence Token
└── cache.json          # AUTOMATIC: Persistent Track-to-Video API Mapping Cache
```

---

## 🐍 Setup & Environment Initialization

### 1. Initialize Virtual Environment
Navigate to your project directory inside your terminal and establish an isolated virtual environment:

```bash
# Create the environment
python -m venv venv

# Activate on Windows (Command Prompt):
venv\Scripts\activate

# Activate on Mac / Linux:
source venv/bin/activate
```

### 2. Install Dependencies
Install the required Google API integration components and optional UI enhancements:

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

# Optional: Enables seamless drag-and-drop integration in the GUI layout
pip install tkinterdnd2
```

---

## 🔐 Google Cloud Configuration Gate (Linking the API to the GUI)

Because this utility is entirely open-source, it does not share a centralized server key. You must supply your own secure credentials from the Google Cloud Console. The GUI is built to automatically detect these credentials as long as they are placed in the root folder under a specific name.

Follow these exact steps to set up your back-end connection:

### Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Log in with your standard Google/YouTube account.
3. Click the project dropdown menu in the top-left corner (next to the logo) and click **New Project**.
4. Name your project (e.g., `Youtubelist Builder`) and click **Create**.

### Step 2: Enable the YouTube Data API v3
1. Ensure your new project is selected in the top-left dropdown.
2. In the left-hand sidebar, navigate to **APIs & Services** > **Library**.
3. In the search bar, type **YouTube Data API v3** and click on it.
4. Click the blue **Enable** button.

### Step 3: Configure the OAuth Consent Screen
Before Google will hand over desktop keys, you must configure a local consent profile:
1. In the left sidebar, click **APIs & Services** > **OAuth consent screen**.
2. Select **User Type: External** and click **Create**.
3. Fill in the mandatory app details:
   * **App name:** `Playlist Builder`
   * **User support email:** Choose your email address from the dropdown.
   * **Developer contact information:** Type your email address.
4. Click **Save and Continue** (you can skip the *Scopes* and *Optional Info* screens by clicking save at the bottom).
5. **Crucial Back-End Step:** On the final **Test users** screen, click **+ Add Users**, type your exact YouTube email address, and click **Add**. If you skip this step, Google will block your application during login! Click **Save and Continue**.

### Step 4: Generate and Download the Desktop Secret Key
1. In the left sidebar, click **APIs & Services** > **Credentials**.
2. Click **+ Create Credentials** at the top of the page and select **OAuth client ID**.
3. Set the **Application type** dropdown to **Desktop app**.
4. Name it anything you like (e.g., `Desktop Sync Client`) and click **Create**.
5. A popup window will show your client secrets. Click **Download JSON**.

### Step 5: Link the API Key to the GUI Workspace
1. Locate the downloaded file on your computer (it usually has a long string of numbers, like `client_secret_xxxxxxxx.json`).
2. Move or copy this file directly into your `Youtubelist-builder` project directory.
3. Rename the file to exactly: `client_secret.json`

Once `client_secret.json` is sitting cleanly alongside `gui.py`, the backend handshake is complete! When you click **Sync Playlist** in the GUI, it will automatically detect this key, open a brief browser window to authenticate your YouTube profile safely, and generate your local `token.json` session file.

---

## 🚀 Execution Guide

### Method A: Plain-Text CLI Sync Engine
The command-line interface treats your local `.txt` filename as the default playlist name and updates it on the fly. Create a standard text file (e.g., `solarpunk.txt`) with tracks ordered line-by-line:

```text
Vashti Bunyan - Diamond Day
Nick Drake - Northern Sky
Tycho - Dive
```

Run the sync using standard execution flags to customize duration thresholds and performance preferences:

```bash
# Basic Private Sync (Default 15-minute runtime cap, Live tracks filtered out)
python main.py solarpunk.txt

# Sync long-form tracks (e.g., extend max limit to 45 minutes)
python main.py ambient.txt --max-duration 45

# Sync concert sets or sessions by explicitly lifting the live performance ban
python main.py live_sessions.txt --allow-live

# Full-featured parameter run
python main.py solarpunk.txt --title "Solarpunk Custom Epic" --max-duration 30 --allow-live --privacy unlisted
```

### Method B: Graphical Desktop Interface
For a seamless, interactive configuration flow, launch the multi-threaded desktop GUI dashboard:

```bash
python gui.py
```

* **Automatic Credentials Handshake:** You don't need to manually paste API keys into the interface. The application maps directly to your root folder's configuration files on launch.
* **Custom Filtering Controllers:** Adjust the duration spinbox dynamically to shift maximum acceptable video length restrictions from 1 to 180 minutes, or toggle the "Allow Live Tracks" checkbox to dictate inclusion settings instantly.
* **Drag-and-Drop Staging:** Drag any playlist `.txt` file from your desktop files and drop it directly onto the entry field to instantly queue it up for processing.
* **System-Aware Themes:** Automatically tracks your native operating system settings to transition seamlessly between Dark Mode and Light Mode layouts.

---

## 🛡️ Security & State Persistence

This tool separates core public logic from local runtime files. The project's `.gitignore` file contains a dedicated security policy to block private session details from being tracked or exposed to your public git history:

* **`token.json`:** Generated automatically upon your first secure login. It handles re-authentication in the background via secure OAuth2 refresh keys, completely removing the need to log in through a browser window on subsequent runs.
* **`cache.json`:** Safely tracks query maps. If you adjust your duration configurations or decide to allow live tracks, the engine will smartly look past cached entries that violate your new limits and perform fresh searches. If you ever want to reset all query parameters completely, simply delete `cache.json` from your directory.
