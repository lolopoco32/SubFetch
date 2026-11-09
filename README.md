# SubFetch 🎬

**SubFetch** is a lightweight, cross-platform Python/Tkinter GUI application designed for quickly searching, downloading, and loading subtitles for local video files using OpenSubtitles APIs.

---

## Features

- **Drag & Drop Support**: Drag any video file directly into the application window to inspect and start searching immediately.
- **Hash-Based & Text Search**: Automatically calculates the OpenSubtitles movie hash for exact matching while providing a manual search box for title/query adjustments.
- **Multi-Language UI & Subtitle Support**:
  - **Interface languages**: English, Romanian, Italian.
  - **Subtitle search languages**: Romanian, English, Italian, Hungarian, French, German, Spanish.
- **Video Player Integration**: Directly launch external media players with the newly downloaded subtitle loaded:
  - System or Flatpak packages: **mpv**, **VLC**, **Celluloid**, **SMPlayer**, **Totem**, **MPlayer**.
- **Diacritics Correction**: Built-in character translation option for fixing Romanian legacy/damaged diacritics.
- **Multi-Source Fetching**: Queries both OpenSubtitles REST API and web search endpoints concurrently.
- **Persistent Preferences**: Saves your UI language, search language, and diacritic preferences locally across sessions (`~/.config/subfetch.json`).

---

## Supported Video & Subtitle Formats

- **Video formats**: `.mkv`, `.mp4`, `.avi`, `.mov`, `.webm`, `.m4v`, `.mpg`, `.mpeg`, `.wmv`, `.flv`, `.ts`
- **Subtitle formats**: `.srt`, `.sub`, `.ass`, `.ssa`, `.vtt` (automatically handles `.gz` and `.zip` archive extraction).

---

## Requirements

- **Python 3.6+**
- Standard Python libraries (`tkinter`, `urllib`, `gzip`, `zipfile`, `json`, `threading`, `queue`, `struct`).
- *(Optional)* `tkinterdnd2` or system `tkdnd` for Drag & Drop support.

---

## Installation & Usage

1. **Clone the repository or download `subfetch.py`**:
   ```bash
   git clone [https://github.com/your-username/subfetch.git](https://github.com/your-username/subfetch.git)
   cd subfetch
