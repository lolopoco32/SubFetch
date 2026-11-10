# SubFetch 🎬

**SubFetch** is a lightweight, clean, and cross-platform desktop application written in Python and Tkinter for searching, downloading, and automatically playing subtitles alongside your local video files using OpenSubtitles.

---

## Key Features

- **Batch Processing**: Easily process an entire season, a whole collection, or an entire folder in one go to fetch subtitles for all your video files simultaneously.
- **Drag & Drop Interface**: Easily drop any video file—or even an entire folder—directly into the application window to kick off hash calculation and subtitle search.
- **Smart Hash & Text Search**: Computes OpenSubtitles exact movie hashes while automatically guessing and extracting clean titles for fallback keyword searches.
- **Multi-Language Support**:
  - **Interface Languages**: English, Romanian, Italian.
  - **Subtitle Search Languages**: English, Romanian, Italian, Hungarian, French, German, Spanish.
- **Integrated Video Playback**: Automatically downloads and opens the video with your preferred player. Supported players (native & Flatpak):
  - **mpv**, **VLC**, **Celluloid**, **SMPlayer**, **Totem**, **MPlayer**.
- **Diacritics Repair**: Features built-in automatic character correction for Romanian legacy diacritics (`º`, `ª`, `þ`, `Þ`, etc.).
- **Dual OpenSubtitles Querying**: Queries both OpenSubtitles REST API and web search endpoints concurrently for maximum coverage.
- **Archive Extraction**: Automatically extracts and decompresses `.srt` files wrapped in `.zip` or `.gz` archives.
- **Persistent Settings**: Saves your UI language, subtitle language preferences, and diacritic choices locally in `~/.config/subfetch.json`.
- **Movie Poster Artwork**: Automatically fetches and displays high-res movie posters directly in the application interface upon file selection.
- **IMDb Quick Integration**: Instantly access and view movie details on IMDb with a dedicated info button.

---

## Supported Formats

- **Video Extensions**: `.mkv`, `.mp4`, `.avi`, `.mov`, `.webm`, `.m4v`, `.mpg`, `.mpeg`, `.wmv`, `.flv`, `.ts`
- **Subtitle Extensions**: `.srt`, `.sub`, `.ass`, `.ssa`, `.vtt`

---

## Requirements

- **Python 3.6+** (uses standard libraries: `tkinter`, `urllib`, `gzip`, `zipfile`, `json`, `threading`, `queue`, `struct`, `pillow`).
- *(Optional)* `tkinterdnd2` or system `tkdnd` for Drag & Drop functionality (falls back gracefully to file selection if unavailable).

---

## Quick Start

Run the script directly using Python:

```bash
python3 subfetch.py
```

You can also pass a video file path directly when launching:

```bash
python3 subfetch.py /path/to/movie.mkv
```

---

## Usage Guide

1. **Select a Video**: Drag and drop a movie file onto the drop panel or click it to choose a file manually.
2. **Review Results**: SubFetch instantly computes the file hash and fetches available subtitles.
3. **Download or Play**:
   - Double-click any subtitle result (or press `Enter`) to download and play immediately.
   - Click **Download and play** to launch your selected media player with the downloaded subtitle attached.
   - Click **Download only** to save the `.srt` file next to your video file.

---

## Configuration

SubFetch stores configuration settings under `~/.config/subfetch.json` (or `$XDG_CONFIG_HOME/subfetch.json`):

```json
{
  "ui_lang": "English",
  "search_lang": "English",
  "fix_diacritics": false
}
```

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPLv3). Anyone is free to modify and redistribute this software, provided that any derivative works are also open-sourced under the same license terms.
