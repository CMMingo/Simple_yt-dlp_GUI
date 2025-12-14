"""
yt-dlp GUI — PySide6 Version
"""

# ==================================================
# IMPORTS
# ==================================================

import subprocess
import threading
import queue
import os
import json
import sys
from typing import cast

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QTextEdit,
    QProgressBar, QFileDialog, QTabWidget, QButtonGroup, QMessageBox, QAbstractButton
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPalette, QColor


# ==================================================
# SETTINGS FILE MANAGEMENT
# ==================================================

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "theme": "dark",
    "download_folder": os.getcwd()
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(theme, download_folder):
    data = {
        "theme": theme,
        "download_folder": download_folder
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

settings = load_settings()


# ==================================================
# ENSURE yt-dlp IS AVAILABLE & UPDATED
# ==================================================

yt_dlp_path = os.path.join(os.path.dirname(__file__), "yt-dlp.exe")
try:
    subprocess.run([yt_dlp_path, "--update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except FileNotFoundError:
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "Error", "yt-dlp was not found in PATH")
    sys.exit(1)


# ==================================================
# SIGNAL HANDLER (for thread-safe GUI updates)
# ==================================================

class SignalHandler(QObject):
    output_signal = Signal(str)
    process_finished = Signal()

signal_handler = SignalHandler()


# ==================================================
# MAIN APPLICATION WINDOW
# ==================================================

class YtDlpGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_theme = settings["theme"]
        self.download_folder = settings["download_folder"]
        self.process_running = False
        self.output_queue = queue.Queue()

        self.init_ui()
        self.apply_theme()
        self.validate()

        # Connect signals
        signal_handler.output_signal.connect(self.append_output)
        signal_handler.process_finished.connect(self.on_process_finished)

        # Start queue processor
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_queue)
        self.queue_timer.start(100)

    def init_ui(self):
        self.setWindowTitle("yt-dlp GUI")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(700, 500)

        # Central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs
        self.create_download_tab()
        self.create_settings_tab()

    def create_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # Download type
        type_label = QLabel("Download type")
        layout.addWidget(type_label)

        type_layout = QHBoxLayout()
        self.radio_audio = QRadioButton("Audio (MP3)")
        self.radio_video = QRadioButton("Video (MP4)")
        self.radio_audio.setChecked(True)

        self.type_group = QButtonGroup()
        self.type_group.addButton(self.radio_audio)
        self.type_group.addButton(self.radio_video)

        type_layout.addWidget(self.radio_audio)
        type_layout.addWidget(self.radio_video)

        self.format_entry = QLineEdit()
        self.format_entry.setPlaceholderText("Enter format code (e.g.: 'video_code+audio_code')")
        self.format_entry.setMaximumWidth(300)
        self.format_entry.setVisible(False)
        type_layout.addWidget(self.format_entry)
        type_layout.addStretch()

        layout.addLayout(type_layout)

        # URL
        layout.addSpacing(10)
        url_label = QLabel("URL")
        layout.addWidget(url_label)

        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("Enter video URL")
        layout.addWidget(self.url_entry)

        # Filename
        layout.addSpacing(10)
        filename_label = QLabel("Output filename (optional)")
        layout.addWidget(filename_label)

        self.filename_entry = QLineEdit()
        self.filename_entry.setPlaceholderText("Leave empty to keep the video title name")
        layout.addWidget(self.filename_entry)

        # Download folder
        layout.addSpacing(10)
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Download folder")
        folder_layout.addWidget(folder_label)

        self.folder_entry = QLineEdit(self.download_folder)
        folder_layout.addWidget(self.folder_entry)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.choose_folder)
        browse_btn.setMaximumWidth(100)
        folder_layout.addWidget(browse_btn)

        layout.addLayout(folder_layout)

        # Progress bar
        layout.addSpacing(10)
        self.progress = QProgressBar()
        self.progress.setMaximum(0)  # Indeterminate mode
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Output
        layout.addSpacing(10)
        output_label = QLabel("Output")
        layout.addWidget(output_label)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Download")

        # Connect signals for validation
        self.radio_audio.toggled.connect(self.on_type_changed)
        self.radio_video.toggled.connect(self.on_type_changed)
        self.url_entry.textChanged.connect(self.validate)

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        theme_label = QLabel("Theme")
        layout.addWidget(theme_label)

        self.radio_dark = QRadioButton("Dark")
        self.radio_light = QRadioButton("Light")

        if self.current_theme == "dark":
            self.radio_dark.setChecked(True)
        else:
            self.radio_light.setChecked(True)

        self.radio_dark.toggled.connect(lambda: self.change_theme("dark"))
        self.radio_light.toggled.connect(lambda: self.change_theme("light"))

        layout.addWidget(self.radio_dark)
        layout.addWidget(self.radio_light)
        layout.addStretch()

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Settings")

    def on_type_changed(self):
        is_video = self.radio_video.isChecked()
        self.format_entry.setVisible(is_video)
        self.validate()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_entry.setText(folder)
            save_settings(self.current_theme, self.download_folder)

    def validate(self):
        if self.process_running:
            self.download_btn.setEnabled(False)
            return

        has_url = bool(self.url_entry.text().strip())
        self.download_btn.setEnabled(has_url)

    def append_output(self, text):
        self.output.moveCursor(self.output.textCursor().MoveOperation.End)
        self.output.insertPlainText(text)
        self.output.moveCursor(self.output.textCursor().MoveOperation.End)

    def run_process(self, command):
        try:
            self.process_running = True

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                signal_handler.output_signal.emit(line)

            process.wait()

        finally:
            signal_handler.process_finished.emit()

    def on_process_finished(self):
        self.process_running = False
        self.progress.setVisible(False)
        self.validate()

    def start_download(self):
        self.append_output("\n--- Download started ---\n")
        self.progress.setVisible(True)

        base = self.filename_entry.text().strip() or "%(title)s"
        output_template = os.path.join(self.download_folder, base + ".%(ext)s")

        # Audio download
        if self.radio_audio.isChecked():
            cmd = [yt_dlp_path, "-x", "--audio-format", "mp3", "-o", output_template, self.url_entry.text()]
            threading.Thread(target=self.run_process, args=(cmd,), daemon=True).start()
            return

        # Video: list formats first if no format specified
        if not self.format_entry.text().strip():
            self.append_output("\nListing formats...\n")
            cmd = [yt_dlp_path, "-F", self.url_entry.text()]
            threading.Thread(target=self.run_process, args=(cmd,), daemon=True).start()
            return

        # Video: actual download
        cmd = [
            yt_dlp_path,
            "-f",
            self.format_entry.text(),
            "--merge-output-format",
            "mp4",
            "-o",
            output_template,
            self.url_entry.text()
        ]

        threading.Thread(target=self.run_process, args=(cmd,), daemon=True).start()

    def change_theme(self, theme):
        self.current_theme = theme
        self.apply_theme()
        save_settings(self.current_theme, self.download_folder)

    def apply_theme(self):
        if self.current_theme == "dark":
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 30, 30))
            palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Button, QColor(74, 74, 74))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(92, 157, 237))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

            app = cast(QApplication, QApplication.instance())
            app.setPalette(palette)

            # Additional styling for specific widgets
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton {
                    background-color: #4a4a4a;
                    color: #ffffff;
                    border: none;
                    padding: 8px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:disabled {
                    background-color: #333333;
                    color: #666666;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QProgressBar {
                    border: 1px solid #555555;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #5c9ded;
                }
                QLabel {
                    color: #ffffff;
                }
                QRadioButton {
                    color: #ffffff;
                }
                QTabWidget::pane {
                    background-color: #2d2d2d;
                    border: none;
                }
                QTabBar::tab {
                    background-color: #4a4a4a;
                    color: #ffffff;
                }
                QTabBar::tab:selected {
                    background-color: #5c9ded;
                }
            """)
        else:
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(242, 242, 242))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(242, 242, 242))
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(92, 157, 237))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

            app = cast(QApplication, QApplication.instance())
            app.setPalette(palette)

            self.setStyleSheet("""
                QWidget {
                    background-color: #f2f2f2;
                    color: #000000;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: #000000;
                    border: 1px solid #cccccc;
                    padding: 8px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton:disabled {
                    background-color: #f0f0f0;
                    color: #999999;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #5c9ded;
                }
                QLabel {
                    color: #000000;
                }
                QRadioButton {
                    color: #000000;
                }
                QTabWidget::pane {
                    border: none;
                }
                QTabBar::tab {
                    background-color: #e0e0e0;
                    color: #000000;
                }
                QTabBar::tab:selected {
                    background-color: #5c9ded;
                }
            """)

    def process_queue(self):
        while not self.output_queue.empty():
            self.append_output(self.output_queue.get())


# ==================================================
# APPLICATION ENTRY POINT
# ==================================================

def main():
    app = QApplication(sys.argv)
    window = YtDlpGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
