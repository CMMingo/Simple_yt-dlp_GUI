# yt-dlp GUI

A simple, beautiful, and functional Python GUI for **yt-dlp**, allowing audio and video downloads from YouTube and other platforms.

---

## Features

- **Audio or Video downloads:** Select between MP3 audio extraction or MP4 video downloads.
- **Manual format selection:** For video downloads, enter your desired format (no automatic parsing).
- **URL input:** Copy-paste the link of the video/audio you want to download.
- **Optional filename:** Specify a custom output filename.
- **Download folder selection:** Choose where to save downloaded files.
- **Progress bar:** Shows download activity.
- **Thread-safe execution:** Runs yt-dlp without freezing the GUI.
- **Light and Dark modes:** Switch between themes.
- **Persistent settings:** Download folder and theme saved to disk via JSON.
- **Resizable window:** Window can be resized without breaking layout.
- **Output area:** Scrollable vertically, wraps text, never hides download button.
- **Placeholder text:** Format selection box shows "Select output format" when empty.

---

## Requirements

- Python 3.8+
- `yt-dlp` installed and in PATH
- Standard Python libraries (tkinter, threading, subprocess, os, json, re, queue)

Optional for creating standalone `.exe`:
- `PyInstaller` (pip install pyinstaller)

---

## Installation

1. Clone or download this repository.
2. Ensure `yt-dlp` is installed and available in your system PATH.
3. Run the GUI:
```bash
python yt_dlp_gui.py
```

---

## Usage

1. Open the GUI.
2. Select the download type: **Audio (MP3)** or **Video (MP4)**.
3. Paste the video URL in the URL box.
4. Optionally, enter a filename.
5. Select the download folder (default is current working directory).
6. For video, enter the desired format (e.g., `bestvideo+bestaudio`).
7. Click **Download** to start.
8. The progress bar and output area show the download status.

### Notes
- The download button is **disabled** until a URL is provided.
- For video downloads, the format must be entered manually.
- The placeholder in the format box guides you with "Select output format".
- Themes and download folder are persisted between sessions.

---

## Theme System

- **Dark mode:** Default, uses dark backgrounds and light text.
- **Light mode:** Optional, uses light backgrounds and dark text.
- Change themes from the **Settings tab**.

---

## Saving Settings

- Stored in `settings.json` in the same folder as the script.
- Stores:
  - `theme` ("dark" or "light")
  - `download_folder` (string)

---

## Layout Behavior

- Output area scrolls **vertically only**, wraps text to fit window.
- Download button is **always visible**, pinned below the output area.
- Window is resizable; widgets adjust dynamically without hiding essential controls.

---

## Packaging as Executable (.exe)

1. Install PyInstaller:
```bash
pip install pyinstaller
```
2. Create a single-file, windowed executable:
```bash
pyinstaller --onefile --windowed yt_dlp_gui.py
```

If one wants to bundle the yt-dlp executable too:
```bash
pyinstaller --onefile --windowed python_ytdlp_gui.py --add-data "yt-dlp.exe;."
```
3. The `.exe` will appear in the `dist/` folder.

### Important
- The `.exe` **does not bundle `yt-dlp`**. Users must have it installed separately or include a relative path.

---

## Code Highlights

- **Threading & Queue:** Ensures GUI remains responsive while yt-dlp runs.
- **Validation:** Controls enable/disable download button based on URL and download type.
- **Placeholder Text:** Simulates native placeholder in Tkinter Entry widget.
- **Persistent JSON settings:** Reads/writes theme and folder.
- **Resizable layout:** Output area and controls adjust to window size.

---

## Future Extensions (Optional)

- Auto-detect best audio format for video
- Download history
- Drag-and-drop URLs
- Real-time progress parsing for exact percentages
- Packaging `yt-dlp` inside the executable
- Cross-platform builds

---

## License

MIT License

