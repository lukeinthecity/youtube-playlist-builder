# 🎵 YouTube Playlist Sync (Utility Edition)

A secure, desktop-first automation utility that compiles and syncs YouTube playlists directly from plain-text `.txt` files. By communicating natively with the YouTube Data API v3 from your local environment, this tool completely eliminates the friction of heavy web-app interfaces and browser-bloat.

---

## ✨ Core Mechanics & Features

* **True Idempotent Syncing:** Your text file is the single source of truth. The engine automatically adds missing tracks, skips duplicates, and cleanly prunes remote tracks that have been deleted from the local file.
* **Smart Audio Curation:** * Prioritizes official video configurations by auto-selecting **"- Topic"** channel uploads.
  * Strictly enforces a **15-minute runtime threshold** to filter out full-length albums or long loops.
  * Aggressively blocks low-fidelity tracks using an internal word blacklist (`live`, `remix`, `cover`, `slowed`, `sped up`, etc.).
* **Quota Preservation Engine:** Video lookups are mapped and preserved inside a local cache file. This massively slashes expensive search quota usage (100 units per search) and makes subsequent sync executions instantaneous.
* **Dual Execution Modes:** Fully operational via a streamlined terminal interface or a native cross-platform desktop UI window.

---

## 📦 Project Structure

```text
youtube-playlist-builder/
│
├── main.py             # Core API Engine, Curation Logic & CLI Entrypoint
├── gui.py              # Tkinter-based Desktop GUI with System Theme Adaptivity
├── .gitignore          # Firewall configuration excluding local keys & caches
├── README.md           # Documentation
│
├── solarpunk.txt       # Example plain-text playlist target
│
├── client_secret.json  # USER PROVIDED: Google Cloud Console OAuth Key
├── token.json          # AUTOMATIC: Secured OAuth Session Persistence Token
└── cache.json          # AUTOMATIC: Persistent Track-to-Video API Mapping Cache
