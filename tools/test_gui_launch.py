#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from launcher.launcher_window import LauncherWindow

ARTIFACT_DIR = Path("/home/nemesy/.gemini/antigravity-ide/brain/b8d8417a-cc11-40ef-9c2c-1009c4d46bd9")

def main():
    app = QApplication(sys.argv)
    window = LauncherWindow()
    user_sav = str(BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav")
    window._launch_game_session("nemesy2", user_sav)

    gc = window.game_client

    def snap(name):
        if gc.top_screen_widget.image:
            gc.top_screen_widget.image.save(str(ARTIFACT_DIR / name))
            print(f"📸 Salvato {name}")

    QTimer.singleShot(3000, lambda: snap("gui_debug_t3s.png"))
    QTimer.singleShot(6000, lambda: snap("gui_debug_t6s.png"))
    QTimer.singleShot(9000, lambda: snap("gui_debug_t9s.png"))
    QTimer.singleShot(11000, lambda: (snap("gui_debug_t11s.png"), gc._on_close_to_launcher(), app.quit()))

    app.exec()
    print("✔ Test GUI completato.")

if __name__ == "__main__":
    main()
