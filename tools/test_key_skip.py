#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QKeyEvent
from launcher.launcher_window import LauncherWindow

ARTIFACT_DIR = Path("/home/nemesy/.gemini/antigravity-ide/brain/b8d8417a-cc11-40ef-9c2c-1009c4d46bd9")

def main():
    app = QApplication(sys.argv)
    window = LauncherWindow()
    user_sav = str(BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav")
    window._launch_game_session("nemesy2", user_sav)

    gc = window.game_client

    def press_key_n():
        print("🎮 Simulazione pressione tasto N (Tasto A)...")
        ev_press = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_N, Qt.KeyboardModifier.NoModifier)
        gc.keyPressEvent(ev_press)
        QTimer.singleShot(150, lambda: gc.keyReleaseEvent(
            QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_N, Qt.KeyboardModifier.NoModifier)
        ))

    # Premi N a t=5s (salta intro)
    QTimer.singleShot(5000, press_key_n)
    # Premi N a t=7s (titolo -> continua)
    QTimer.singleShot(7000, press_key_n)
    # Premi N a t=9s (conferma continua)
    QTimer.singleShot(9000, press_key_n)

    def snap(name):
        if gc.top_screen_widget.image:
            gc.top_screen_widget.image.save(str(ARTIFACT_DIR / name))
            print(f"📸 Salvato {name}")

    QTimer.singleShot(6000, lambda: snap("key_n_t6s.png"))
    QTimer.singleShot(8000, lambda: snap("key_n_t8s.png"))
    QTimer.singleShot(11000, lambda: snap("key_n_t11s.png"))
    QTimer.singleShot(14000, lambda: (snap("key_n_t14s.png"), gc._on_close_to_launcher(), app.quit()))

    app.exec()
    print("✔ Test simulazione tasto N completato.")

if __name__ == "__main__":
    main()
