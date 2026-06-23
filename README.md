# 🎵 YouTube Playlist Builder desktop utility

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
* **Dual Execution Modes:** Fully operational via a native cross-platform desktop UI window or a streamlined terminal interface.

---

## 📦 Project Structure

```text
youtube-playlist-builder/
│
├── main.py             # Core API Engine, Filter Validation & CLI Entrypoint
├── gui.py              # Tkinter-based Desktop UI with Custom Filter Controls
├── .gitignore          # Firewall configuration excluding local keys & caches
├── README.md           # Documentation
│
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

Because this utility is entirely open-source, you must supply your own secure credentials from the Google Cloud Console. Follow these steps to generate your keys:

1. **Create Project:** Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project**.
2. **Configure Consent:** Navigate to **APIs & Services > OAuth consent screen**.  Create an **External** app, add your email to **Test users**, and save**.
4. **Generate Keys:** Go to **Credentials > + Create Credentials > OAuth client ID**. Select **Desktop app**, create, and **Download JSON**.
5.  **Configure YouTube API** Click on **API Library**. Search for and enable the **YouTube Data API v3**.
6. **Link to App:** Move the downloaded file into your root folder and rename it exactly to `client_secret.json`.

---

## 🚀 Execution Guide

### Method A: Graphical Desktop Interface (Recommended)
For a seamless, interactive configuration flow, launch the multi-threaded desktop GUI dashboard:

```bash
python gui.py
```

* **Automatic Credentials Handshake:** The application automatically detects `client_secret.json` on launch.
* **Custom Filtering Controllers:** Adjust the duration spinbox to shift maximum acceptable video length restrictions from 1 to 180 minutes, or toggle the "Allow Live Tracks" checkbox to dictate inclusion settings instantly.
* **Drag-and-Drop Staging:** Drag any playlist `.txt` file from your computer and drop it directly onto the entry field to instantly queue it up for processing.
* **System-Aware Themes:** Automatically transitions between Dark Mode and Light Mode layouts based on your OS settings.

### Method B: CLI Sync Engine (For Technical Users)
The command-line interface treats your local `.txt` filename as the playlist name and updates it on the fly. Create a text file with tracks ordered line-by-line (e.g., `my_list.txt`):

```text
Artist - Track Name
Artist - Track Name
```

Run the sync using standard execution flags:

```bash
# Basic Private Sync (Default 15-minute cap, Live filtered out)
python main.py my_list.txt

# Sync with custom constraints
python main.py my_list.txt --max-duration 45 --allow-live --privacy unlisted
```

---

## 🛡️ Security & State Persistence

This tool separates core public logic from local runtime files. 

* **`token.json`:** Generated automatically upon your first secure login. It handles re-authentication in the background via secure OAuth2 refresh keys.
* **`cache.json`:** Safely tracks query maps. If you adjust your duration configurations, the engine will smartly look past cached entries that violate your new limits and perform fresh searches.
