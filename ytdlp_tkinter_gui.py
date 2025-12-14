"""
yt-dlp GUI – Tkinter version
"""


# ==================================================
# IMPORTS
# ==================================================

import subprocess                       # Run external programs (yt-dlp)
import threading                        # Run long tasks without freezing GUI
import queue                            # Thread-safe communication with GUI
import os                               # File system utilities (paths, cwd)
import json                             # Read/write settings to disk

import tkinter as tk                    # Base GUI library (windows, widgets, events)
from tkinter import ttk                 # Modern themed widgets (buttons, frames, etc.)
from tkinter import messagebox          # Popup dialogs (errors, warnings)
from tkinter import filedialog          # Native folder picker dialog


# ==================================================
# SETTINGS FILE MANAGEMENT
# ==================================================

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "theme": "dark",
    "download_folder": os.getcwd()
}

# Load settings from disk (or return defaults)
def load_settings():
    # If the file does not exist, return defaults
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception: # if the file is corrupted, fall back safely
        return DEFAULT_SETTINGS.copy()


# Save current settings to disk
def save_settings():
    data = {
        "theme": current_theme.get(),
        "download_folder": download_path.get()
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# Load settings immediately at startup
settings = load_settings()


# ==================================================
# ENSURE yt-dlp IS AVAILABLE & UPDATED
# ==================================================

yt_dlp_path = os.path.join(os.path.dirname(__file__), "yt-dlp.exe")
try:
    # Run yt-dlp --update silently
    subprocess.run([yt_dlp_path, "--update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except FileNotFoundError:
    # If yt-dlp is not installed, show error and exit
    messagebox.showerror("Error", "yt-dlp was not found in PATH")
    raise SystemExit


# ==================================================
# MAIN APPLICATION WINDOW
# ==================================================

root = tk.Tk() # main window
root.title("yt-dlp GUI") # window title
root.geometry("1200x650") # initial window size
root.minsize(700, 500) # minimum size (prevents layout breaking)


# ==================================================
# THEME SYSTEM (LIGHT / DARK)
# ==================================================

# ttk styling engine
style = ttk.Style(root)
style.theme_use("clam") # use a theme that allows color customization

THEMES = {
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#ffffff",
        "entry": "#2d2d2d"
    },
    "light": {
        "bg": "#f2f2f2",
        "fg": "#000000",
        "entry": "#ffffff"
    }
}

current_theme = tk.StringVar(value=settings["theme"]) # loaded from settings

# Apply theme colors to all widgets
def apply_theme():
    t = THEMES[current_theme.get()]

    # Window background
    root.configure(bg=t["bg"])
    # ttk widget styles
    style.configure("TFrame", background=t["bg"])
    style.configure("TLabel", background=t["bg"], foreground=t["fg"])
    style.configure("TRadiobutton", background=t["bg"], foreground=t["fg"])
    style.configure("TButton", background="#4a4a4a", foreground=t["fg"])
    style.configure("TEntry", fieldbackground=t["entry"], foreground=t["fg"])
    style.configure("Horizontal.TProgressbar", background="#5c9ded")
    # Text widget must be styled manually
    output.configure(
        bg=t["entry"],
        fg=t["fg"],
        insertbackground=t["fg"]
    )

    save_settings()


# ==================================================
# APPLICATION STATE VARIABLES
# ==================================================

download_type = tk.StringVar(value="audio") # download type (default = audio)
url_var = tk.StringVar() # URL entered by the user
format_var = tk.StringVar() # video format selection
filename_var = tk.StringVar() # optional output filename
download_path = tk.StringVar(value=settings["download_folder"]) # download folder (loaded from settings)

process_running = tk.BooleanVar(value=False) # indicates whether yt-dlp is currently running

output_queue = queue.Queue() # queue used to safely move text from background threads to GUI


# ==================================================
# NOTEBOOK (TABS)
# ==================================================

# Create tab container
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True) # make it fill the entire window

# Create individual tabs
main_tab = ttk.Frame(notebook)
settings_tab = ttk.Frame(notebook)

# Add tabs to notebook
notebook.add(main_tab, text="Download")
notebook.add(settings_tab, text="Settings")


# ==================================================
# DOWNLOAD TAB UI
# ==================================================

# Main layout frame
main = ttk.Frame(main_tab, padding=15)
main.pack(fill="both", expand=True)

# ---- Download type ----

ttk.Label(main, text="Download type").pack(anchor="w")

type_frame = ttk.Frame(main)
type_frame.pack(anchor="w", pady=5)

radio_audio = ttk.Radiobutton(type_frame, text="Audio (MP3)", variable=download_type, value="audio")
radio_video = ttk.Radiobutton(type_frame, text="Video (MP4)", variable=download_type, value="video")

radio_audio.grid(row=0, column=0, sticky="w")
radio_video.grid(row=0, column=1, sticky="w", padx=(20, 5))

# Format entry shown only for video
format_entry = ttk.Entry(type_frame, textvariable=format_var, width=25)
format_entry.grid(row=0, column=2)
format_entry.grid_remove()

# ---- URL ----

ttk.Label(main, text="URL").pack(anchor="w", pady=(10, 0))
ttk.Entry(main, textvariable=url_var).pack(fill="x")

# ---- Filename ----

ttk.Label(main, text="Output filename (optional)").pack(anchor="w", pady=(10, 0))
ttk.Entry(main, textvariable=filename_var, width=40).pack(anchor="w")

# ---- Download folder ----

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        download_path.set(folder)
        save_settings()

folder_frame = ttk.Frame(main)
folder_frame.pack(anchor="w", pady=10)

ttk.Label(folder_frame, text="Download folder").pack(side="left")
ttk.Entry(folder_frame, textvariable=download_path, width=45).pack(side="left", padx=5)
ttk.Button(folder_frame, text="Browse", command=choose_folder).pack(side="left")

# ---- Progress bar ----

progress = ttk.Progressbar(main, mode="indeterminate")
progress.pack(fill="x", pady=10)

# ---- Output area (VERTICAL SCROLL ONLY) ----

ttk.Label(main, text="Output").pack(anchor="w")

output_frame = ttk.Frame(main)
output_frame.pack(fill="both", expand=True)

scrollbar = ttk.Scrollbar(output_frame, orient="vertical")
scrollbar.pack(side="right", fill="y")

output = tk.Text(
    output_frame,
    wrap="word", # prevent horizontal scrolling
    yscrollcommand=scrollbar.set,
    height=10,
    state="disabled"
)
output.pack(fill="both", expand=True)
scrollbar.config(command=output.yview)

# ---- DOWNLOAD BUTTON ----

button_frame = ttk.Frame(main)
button_frame.pack(fill="x", pady=10)

download_btn = ttk.Button(button_frame, text="Download")
download_btn.pack(fill="x")


# ==================================================
# SETTINGS TAB UI
# ==================================================

settings_ui = ttk.Frame(settings_tab, padding=20)
settings_ui.pack(fill="both", expand=True)

# Theme selection
ttk.Label(settings_ui, text="Theme").pack(anchor="w")
ttk.Radiobutton(settings_ui, text="Dark", variable=current_theme, value="dark", command=apply_theme).pack(anchor="w")
ttk.Radiobutton(settings_ui, text="Light", variable=current_theme, value="light", command=apply_theme).pack(anchor="w")


# ==================================================
# HELPER FUNCTIONS
# ==================================================

# Safely append text to output widget
def append_output(text):
    output.configure(state="normal")
    output.insert("end", text)
    output.see("end")
    output.configure(state="disabled")


# Validate UI state and enable/disable button
def validate():
    # Disable button while process is running
    if process_running.get():
        download_btn.config(state="disabled")
        return

    # Enable button only if type selected and URL present
    valid = download_type.get() and url_var.get().strip()
    download_btn.config(state="normal" if valid else "disabled")

    # Show format field only for video
    if download_type.get() == "video":
        format_entry.grid()
    else:
        format_entry.grid_remove()


# Run yt-dlp without freezing GUI
def run_process(command):
    try:
        process_running.set(True)
        progress.start()

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        collected = ""

        for line in process.stdout:
            collected += line
            output_queue.put(line)

        process.wait()

    finally:
        process_running.set(False)
        progress.stop()
        validate()


# Download button action
def start_download():
    append_output("\n--- Download started ---\n")

    base = filename_var.get().strip() or "%(title)s"
    output_template = os.path.join(download_path.get(), base + ".%(ext)s")

    # AUDIO DOWNLOAD
    if download_type.get() == "audio":
        cmd = [yt_dlp_path, "-x", "--audio-format", "mp3", "-o", output_template, url_var.get()]
        threading.Thread(target=run_process, args=(cmd,), daemon=True).start()
        return

    # VIDEO: list formats first
    if not format_var.get().strip():
        append_output("\nListing formats...\n")
        cmd = [yt_dlp_path, "-F", url_var.get()]
        threading.Thread(target=run_process, args=(cmd,), daemon=True).start()
        return

    # VIDEO: actual download
    cmd = [
        yt_dlp_path,
        "-f",
        format_var.get(),
        "--merge-output-format",
        "mp4",
        "-o",
        output_template,
        url_var.get()
    ]

    threading.Thread(target=run_process, args=(cmd,), daemon=True).start()


# ==================================================
# INITIALIZATION & EVENT LOOP
# ==================================================

# React to state changes
download_type.trace_add("write", lambda *_: validate())
url_var.trace_add("write", lambda *_: validate())

# Apply theme once widgets exist
apply_theme()

# Attach button action
download_btn.config(command=start_download)

# Periodically flush output queue
def process_queue():
    while not output_queue.empty():
        append_output(output_queue.get())
    root.after(100, process_queue)

process_queue()

# Start Tkinter event loop
root.mainloop()
