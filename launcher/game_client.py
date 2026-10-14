#!/usr/bin/env python3
"""
Finestra del Client di Gioco Unificato (PokeMMO Architecture).
Integra il core di melonDS direttamente dentro la finestra:
- Schermo Superiore: Renderizzato in alta definizione nello schermo principale.
- Schermo Touch: A scomparsa tramite pulsante HUD interattivo.
- TCG Scanner: Nel cassetto laterale per iniezioni in tempo reale.
Zero finestre esterne: una singola finestra per tutto il gioco.
"""

import sys
import os
import re
import time
import shutil
import sqlite3
import difflib
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QComboBox, QMessageBox, QSplitter
)
from PyQt6.QtGui import QImage, QPixmap, QPainter, QKeyEvent, QMouseEvent

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurazione del binario Tesseract locale e lingue (eng + ita)
TESSERACT_BIN_DIR = BASE_DIR / "scanner" / ".tesseract_bin"
if (TESSERACT_BIN_DIR / "usr" / "bin" / "tesseract").exists():
    os.environ['LD_LIBRARY_PATH'] = f"{TESSERACT_BIN_DIR}/usr/lib:" + os.environ.get('LD_LIBRARY_PATH', '')
    os.environ['TESSDATA_PREFIX'] = f"{TESSERACT_BIN_DIR}/usr/share/tessdata"
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_BIN_DIR / "usr" / "bin" / "tesseract")

from launcher.ui_theme import STYLE_SHEET
from launcher.core.runner import (
    DSEmulatorThread,
    RETRO_DEVICE_ID_JOYPAD_B, RETRO_DEVICE_ID_JOYPAD_Y,
    RETRO_DEVICE_ID_JOYPAD_SELECT, RETRO_DEVICE_ID_JOYPAD_START,
    RETRO_DEVICE_ID_JOYPAD_UP, RETRO_DEVICE_ID_JOYPAD_DOWN,
    RETRO_DEVICE_ID_JOYPAD_LEFT, RETRO_DEVICE_ID_JOYPAD_RIGHT,
    RETRO_DEVICE_ID_JOYPAD_A, RETRO_DEVICE_ID_JOYPAD_X,
    RETRO_DEVICE_ID_JOYPAD_L, RETRO_DEVICE_ID_JOYPAD_R
)
from scanner.tcg_core import TCGCore
from scanner.injector import PokemonInjector
from scanner.knowledge_engine import CardKnowledgeEngine
from launcher.settings_manager import SettingsManager
from launcher.gamepad_handler import GamepadListener
from launcher.i18n import (
    t, get_language, register_language_listener, unregister_language_listener
)

import platform

system = platform.system()
if system == "Windows":
    core_candidates = [
        BASE_DIR / "launcher" / "core" / "melonds_core.dll",
        BASE_DIR / "launcher" / "core" / "melonds_libretro.dll",
        BASE_DIR / "launcher" / "core" / "melonDS.dll"
    ]
    CORE_LIB_PATH = next((p for p in core_candidates if p.exists()), core_candidates[0])
elif system == "Darwin":
    CORE_LIB_PATH = BASE_DIR / "launcher" / "core" / "melonds_core.dylib"
else:
    CORE_LIB_PATH = BASE_DIR / "launcher" / "core" / "melonds_core.so"


class CardRecognizerWorker(QThread):
    """Thread in background per il riconoscimento intelligente con CardKnowledgeEngine."""
    recognition_completed = pyqtSignal(dict)
    recognition_failed = pyqtSignal(str)

    def __init__(self, shots: dict, tcg_core: TCGCore, parent=None):
        super().__init__(parent)
        self.shots = shots
        self.tcg_core = tcg_core

    def run(self):
        try:
            engine = CardKnowledgeEngine()
            found_card, confidence, method = engine.identify_card_from_captures(self.shots)

            if found_card:
                found_card['confidence'] = confidence
                found_card['method'] = method
                self.recognition_completed.emit(found_card)
            else:
                self.recognition_failed.emit(
                    "Nessuna carta Pokémon riconosciuta con certezza.\n"
                    "Assicurati di inquadrare bene il Nome (in alto), il Numero e l'Anno (in basso)."
                )
        except Exception as e:
            self.recognition_failed.emit(f"Errore scanner: {e}")

class GameScreenWidget(QWidget):
    """Widget che visualizza lo schermo superiore del DS scalato mantenendo 4:3."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #000000; border-radius: 8px;")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, event):
        self.setFocus()
        super().mousePressEvent(event)

    def update_frame(self, qimg: QImage):
        self.image = qimg
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        if self.image:
            # Scala l'immagine 256x192 (4:3) alle dimensioni correnti con aspect ratio conservato
            scaled = self.image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawImage(x, y, scaled)


class TouchScreenWidget(QWidget):
    """Widget per lo schermo touch interattivo con supporto mouse."""
    def __init__(self, emu_thread: DSEmulatorThread, parent=None):
        super().__init__(parent)
        self.emu_thread = emu_thread
        self.image = None
        self.setFixedSize(256, 192)
        self.setStyleSheet("background-color: #000000; border: 2px solid #00e5ff; border-radius: 6px;")

    def update_frame(self, qimg: QImage):
        self.image = qimg
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        if self.image:
            painter.drawImage(0, 0, self.image)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x_rel = max(0.0, min(1.0, event.position().x() / self.width()))
            y_rel = max(0.0, min(1.0, event.position().y() / self.height()))
            self.emu_thread.set_touch(x_rel, y_rel, True)

    def mouseMoveEvent(self, event: QMouseEvent):
        x_rel = max(0.0, min(1.0, event.position().x() / self.width()))
        y_rel = max(0.0, min(1.0, event.position().y() / self.height()))
        self.emu_thread.set_touch(x_rel, y_rel, True)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.emu_thread.set_touch(0.5, 0.5, False)


class GameClientWindow(QMainWindow):
    def __init__(self, username: str, user_save_path: str, rom_path: str, launcher_ref=None):
        super().__init__()
        self.username = username
        self.user_save_path = Path(user_save_path)
        self.rom_path = Path(rom_path)
        self.launcher_ref = launcher_ref

        self.setWindowTitle(f"Pokémon TCG Adventure — [Allenatore: {self.username}]")
        self.resize(1280, 760)
        self.setStyleSheet(STYLE_SHEET)

        self.tcg_core = TCGCore()
        self.injector = PokemonInjector()

        self.cap = None
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self._update_camera_frame)
        self.current_evaluated_card = None
        self.selected_finish = "normale"

        # Stato Scanner Ottico Guidato a 6 Fasi (Fronte, Retro, Zoom Nome, Zoom Numero, Zoom Anno, Zoom Autore)
        self.scan_phase = 1 # 1: Fronte, 2: Retro, 3: Zoom Nome, 4: Zoom Numero, 5: Zoom Anno, 6: Zoom Autore, 7: In elaborazione
        self.scan_shots = {}
        self.card_detection_state = "red"
        self.green_start_time = None
        self.last_green_time = 0.0
        self.phase_cooldown_until = 0.0
        self.phase_transition_msg = ""
        self.flash_counter = 0
        self.is_recognizing = False
        self.recognizer_worker = None
        self.latest_high_res_frame = None
        self.latest_bbox = None

        # Gestore Comandi e Mappatura Tasti Personalizzabili
        self.settings_mgr = SettingsManager()
        self.key_map = self.settings_mgr.get_qt_key_map()
        self.gamepad_listener = None

        self._build_ui()
        self._retranslate_ui()
        register_language_listener(self._retranslate_ui)
        self._start_inprocess_emulator()

    def _build_ui(self):
        central = QWidget(self)
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # ----------------- TOP HUD BAR (Slim Header) -----------------
        top_bar = QFrame()
        top_bar.setObjectName("CardFrame")
        top_bar.setFixedHeight(52)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(14, 4, 14, 4)

        self.lbl_player = QLabel(t("hud_trainer", username=self.username))
        self.lbl_player.setStyleSheet("font-size: 15px;")
        
        self.lbl_status = QLabel(t("hud_status_core"))
        self.lbl_status.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px;")

        top_layout.addWidget(self.lbl_player)
        top_layout.addWidget(self.lbl_status)
        top_layout.addStretch()

        # Bottoni Azione HUD
        self.btn_toggle_touch = QPushButton(t("hud_btn_touch_open"))
        self.btn_toggle_touch.setObjectName("SecondaryButton")
        self.btn_toggle_touch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_touch.clicked.connect(self._toggle_touch_screen)

        self.btn_virtual_box = QPushButton(t("hud_btn_virtual_box"))
        self.btn_virtual_box.setObjectName("SecondaryButton")
        self.btn_virtual_box.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_virtual_box.setStyleSheet("background-color: #17253d; border: 1.5px solid #00e5ff; color: #00e5ff; font-weight: 700; border-radius: 8px; padding: 6px 12px;")
        self.btn_virtual_box.clicked.connect(self._open_virtual_box_dialog)

        self.btn_toggle_scanner = QPushButton(t("hud_btn_scanner"))
        self.btn_toggle_scanner.setObjectName("SecondaryButton")
        self.btn_toggle_scanner.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_scanner.clicked.connect(self._toggle_scanner_drawer)

        self.btn_settings = QPushButton(t("hud_btn_settings"))
        self.btn_settings.setObjectName("SecondaryButton")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self._open_settings_dialog)

        self.btn_back_launcher = QPushButton(t("hud_btn_exit"))
        self.btn_back_launcher.setObjectName("SecondaryButton")
        self.btn_back_launcher.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_launcher.clicked.connect(self._on_close_to_launcher)

        top_layout.addWidget(self.btn_toggle_touch)
        top_layout.addWidget(self.btn_virtual_box)
        top_layout.addWidget(self.btn_toggle_scanner)
        top_layout.addWidget(self.btn_settings)
        top_layout.addWidget(self.btn_back_launcher)

        main_layout.addWidget(top_bar, 0)

        # ----------------- CORPO CENTRALE (Splitter) -----------------
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #1e293b; width: 3px; }")

        # PANNELLO GIOCO INTEGRATO (Nativo In-Process)
        self.game_panel = QFrame()
        self.game_panel.setObjectName("CardFrame")
        game_panel_layout = QVBoxLayout(self.game_panel)
        game_panel_layout.setContentsMargins(12, 12, 12, 12)
        game_panel_layout.setSpacing(10)

        # Schermo Superiore (Principale)
        self.top_screen_widget = GameScreenWidget(self)
        game_panel_layout.addWidget(self.top_screen_widget, 1)

        # Barra inferiore per Schermo Touch (A scomparsa)
        self.touch_drawer = QFrame()
        self.touch_drawer.setObjectName("InnerPanel")
        touch_layout = QHBoxLayout(self.touch_drawer)
        touch_layout.setContentsMargins(10, 8, 10, 8)
        
        self.lbl_touch_title = QLabel(t("touch_title"))
        self.lbl_touch_title.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        touch_layout.addWidget(self.lbl_touch_title)
        touch_layout.addStretch()

        self.emu_thread = DSEmulatorThread(
            rom_path=str(self.rom_path),
            save_path=str(self.user_save_path),
            core_lib_path=str(CORE_LIB_PATH)
        )
        self.touch_screen_widget = TouchScreenWidget(self.emu_thread, self)
        touch_layout.addWidget(self.touch_screen_widget)
        touch_layout.addStretch()

        self.touch_drawer.setVisible(False) # Chiuso di default!
        game_panel_layout.addWidget(self.touch_drawer)

        self.splitter.addWidget(self.game_panel)

        # PANNELLO DESTRO: CASSETTO TCG SCANNER
        self.scanner_panel = QFrame()
        self.scanner_panel.setObjectName("CardFrame")
        self.scanner_panel.setFixedWidth(440)
        scanner_layout = QVBoxLayout(self.scanner_panel)
        scanner_layout.setContentsMargins(18, 14, 18, 14)
        scanner_layout.setSpacing(10)

        self.hdr_scanner = QLabel(t("scanner_header"))
        self.hdr_scanner.setObjectName("HeaderLabel")
        scanner_layout.addWidget(self.hdr_scanner)

        # Riquadro telecamera Verticale TCG (260 x 364 - Rapporto 2.5 : 3.5)
        camera_container = QWidget()
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        camera_layout.setSpacing(8)
        camera_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_camera = QLabel()
        self.lbl_camera.setFixedSize(260, 364)
        self.lbl_camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_camera_standby_placeholder()
        camera_layout.addWidget(self.lbl_camera)

        # Pulsanti Fotocamera & Scatto Manuale
        cam_btns_layout = QHBoxLayout()
        cam_btns_layout.setSpacing(6)

        self.btn_toggle_camera = QPushButton(t("btn_start_cam"))
        self.btn_toggle_camera.setObjectName("SecondaryButton")
        self.btn_toggle_camera.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_camera.setStyleSheet(
            "QPushButton { border: 1.5px solid #00e5ff; color: #00e5ff; font-weight: 700; padding: 10px; border-radius: 8px; }"
            "QPushButton:hover { background-color: rgba(0, 229, 255, 0.15); }"
        )
        self.btn_toggle_camera.clicked.connect(self._toggle_camera_feed)
        cam_btns_layout.addWidget(self.btn_toggle_camera)

        self.btn_manual_capture = QPushButton(t("btn_capture"))
        self.btn_manual_capture.setObjectName("SecondaryButton")
        self.btn_manual_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manual_capture.setEnabled(False)
        self.btn_manual_capture.setStyleSheet(
            "QPushButton { border: 1.5px solid #10b981; color: #10b981; font-weight: 700; padding: 10px; border-radius: 8px; background-color: rgba(16, 185, 129, 0.08); }"
            "QPushButton:hover { background-color: rgba(16, 185, 129, 0.2); }"
            "QPushButton:disabled { border: 1.5px solid #334155; color: #475569; background-color: transparent; }"
        )
        self.btn_manual_capture.clicked.connect(self._on_manual_capture_clicked)
        cam_btns_layout.addWidget(self.btn_manual_capture)

        camera_layout.addLayout(cam_btns_layout)

        scanner_layout.addWidget(camera_container)

        # Ricerca rapida carta
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(t("search_placeholder"))
        self.txt_search.returnPressed.connect(self._on_search_clicked)
        
        self.btn_search = QPushButton(t("btn_search"))
        self.btn_search.setObjectName("SecondaryButton")
        self.btn_search.clicked.connect(self._on_search_clicked)
        
        search_layout.addWidget(self.txt_search)
        search_layout.addWidget(self.btn_search)
        scanner_layout.addLayout(search_layout)

        # Selezione finitura
        fin_layout = QHBoxLayout()
        self.lbl_fin = QLabel("Finish:")
        self.lbl_fin.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.combo_finish = QComboBox()
        self.combo_finish.addItem(t("finish_normal"), "normale")
        self.combo_finish.addItem(t("finish_holo"), "holo")
        self.combo_finish.addItem(t("finish_reverse_holo"), "reverse_holo")
        self.combo_finish.currentIndexChanged.connect(self._on_finish_changed)
        fin_layout.addWidget(self.lbl_fin)
        fin_layout.addWidget(self.combo_finish)
        scanner_layout.addLayout(fin_layout)

        # Scheda Dettagli
        self.details_box = QFrame()
        self.details_box.setObjectName("InnerPanel")
        self.details_layout = QVBoxLayout(self.details_box)
        self.details_layout.setContentsMargins(12, 10, 12, 10)
        self.details_layout.setSpacing(6)

        self.lbl_card_title = QLabel("No card selected")
        self.lbl_card_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #00e5ff;")
        self.lbl_card_meta = QLabel("Search a card or align it in camera view to inspect details.")
        self.lbl_card_meta.setStyleSheet("font-size: 12px; color: #94a3b8;")
        self.lbl_card_meta.setWordWrap(True)
        self.lbl_card_stats = QLabel("")
        self.lbl_card_stats.setStyleSheet("font-size: 12px; color: #cbd5e1;")

        self.details_layout.addWidget(self.lbl_card_title)
        self.details_layout.addWidget(self.lbl_card_meta)
        self.details_layout.addWidget(self.lbl_card_stats)
        scanner_layout.addWidget(self.details_box)

        # Bottone Iniezione
        self.btn_inject = QPushButton(t("btn_inject"))
        self.btn_inject.setObjectName("PlayButton")
        self.btn_inject.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_inject.setEnabled(False)
        self.btn_inject.clicked.connect(self._on_inject_clicked)
        scanner_layout.addWidget(self.btn_inject)

        scanner_layout.addStretch()
        self.splitter.addWidget(self.scanner_panel)
        main_layout.addWidget(self.splitter, 1)

    def _retranslate_ui(self, lang_code=None):
        """Aggiorna le scritte dell'HUD e del Drawer dello Scanner in tempo reale."""
        self.setWindowTitle(t("client_window_title", username=self.username))
        if hasattr(self, 'lbl_player'):
            self.lbl_player.setText(t("hud_trainer", username=self.username))
        if hasattr(self, 'lbl_status'):
            self.lbl_status.setText(t("hud_status_core"))
        if hasattr(self, 'btn_toggle_touch') and hasattr(self, 'touch_drawer'):
            is_vis = self.touch_drawer.isVisible()
            self.btn_toggle_touch.setText(t("hud_btn_touch_close") if is_vis else t("hud_btn_touch_open"))
        if hasattr(self, 'btn_virtual_box'):
            self.btn_virtual_box.setText(t("hud_btn_virtual_box"))
        if hasattr(self, 'btn_toggle_scanner'):
            self.btn_toggle_scanner.setText(t("hud_btn_scanner"))
        if hasattr(self, 'btn_settings'):
            self.btn_settings.setText(t("hud_btn_settings"))
        if hasattr(self, 'btn_back_launcher'):
            self.btn_back_launcher.setText(t("hud_btn_exit"))
        if hasattr(self, 'lbl_touch_title'):
            self.lbl_touch_title.setText(t("touch_title"))
        if hasattr(self, 'hdr_scanner'):
            self.hdr_scanner.setText(t("scanner_header"))
        if hasattr(self, 'btn_toggle_camera'):
            cam_active = self.cap is not None and self.cap.isOpened()
            self.btn_toggle_camera.setText(t("btn_stop_cam") if cam_active else t("btn_start_cam"))
        if hasattr(self, 'btn_manual_capture'):
            self.btn_manual_capture.setText(t("btn_capture"))
        if hasattr(self, 'txt_search'):
            self.txt_search.setPlaceholderText(t("search_placeholder"))
        if hasattr(self, 'btn_search'):
            self.btn_search.setText(t("btn_search"))
        if hasattr(self, 'btn_inject'):
            self.btn_inject.setText(t("btn_inject"))
        if hasattr(self, 'lbl_camera') and not (self.cap is not None and self.cap.isOpened()):
            self._set_camera_standby_placeholder()

    def _start_inprocess_emulator(self):
        """Avvia il thread del core melonDS collegando i frame video direttamente ai widget."""
        self.emu_thread.frame_ready.connect(self._on_frame_ready)
        self.emu_thread.start()

        # Avvio ascolto Gamepad / Controller USB & Bluetooth
        self.gamepad_listener = GamepadListener(self.emu_thread)
        self.gamepad_listener.start()

        # Sequenza Auto-Boot assistita (salto intro, conferma Continua e taglio C-Gear)
        self.auto_boot_active = True
        self.auto_boot_step = 0
        self.boot_start_time = time.time()
        self.auto_boot_timer = QTimer(self)
        self.auto_boot_timer.setInterval(200)
        self.auto_boot_timer.timeout.connect(self._on_auto_boot_tick)
        self.auto_boot_timer.start()

    def _on_auto_boot_tick(self):
        # Se l'Overworld è stato raggiunto (segnale dal worker melonDS), disattiva auto-boot
        if getattr(self.emu_thread, "control_arr", None) and self.emu_thread.control_arr[27] == 2:
            self.auto_boot_active = False
            if hasattr(self, "auto_boot_timer") and self.auto_boot_timer.isActive():
                self.auto_boot_timer.stop()
            return

        if not getattr(self, "auto_boot_active", False):
            if hasattr(self, "auto_boot_timer") and self.auto_boot_timer.isActive():
                self.auto_boot_timer.stop()
            return

        elapsed = time.time() - self.boot_start_time

        # Lista di impulsi pianificati per garantire avanzamento automatico al 100%
        pulses = [
            (2.5, 3),  # START (salta FreeBIOS/Nintendo)
            (5.0, 3),  # START (salta logo Game Freak)
            (7.5, 3),  # START (salta filmato Kyurem)
            (10.0, 3), # START (salta filmato Kyurem backup)
            (13.0, 3), # START (Title 'Premi START')
            (15.0, 3), # START (Title 'Premi START' backup)
            (17.5, 8), # A (apre Menu / seleziona Continua)
            (19.0, 8), # A (mostra scheda profilo allenatore)
            (20.5, 8), # A (conferma caricamento partita)
            (22.0, 8), # A (backup conferma partita)
            (23.5, 8), # A (backup conferma partita)
        ]

        if not hasattr(self, "boot_pulses_fired"):
            self.boot_pulses_fired = set()

        for idx, (target_t, btn_id) in enumerate(pulses):
            if elapsed >= target_t and idx not in self.boot_pulses_fired:
                self.boot_pulses_fired.add(idx)
                self._pulse_key(btn_id)

        if elapsed >= 27.0:
            self.auto_boot_active = False
            self.auto_boot_timer.stop()

    def _pulse_key(self, joypad_id: int, duration_ms: int = 150):
        self.emu_thread.set_key(joypad_id, True)
        QTimer.singleShot(duration_ms, lambda: self.emu_thread.set_key(joypad_id, False))

    def _open_settings_dialog(self):
        from launcher.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.keybindings_changed.connect(self._reload_keybindings)
        dlg.exec()

    def _open_virtual_box_dialog(self):
        from launcher.virtual_box_dialog import VirtualBoxDialog
        host = self.centralWidget() or self
        if hasattr(self, 'vbox_dialog') and self.vbox_dialog:
            self.vbox_dialog.show()
            self.vbox_dialog.raise_()
            return
        self.vbox_dialog = VirtualBoxDialog(
            username=self.username,
            user_save_path=str(self.user_save_path),
            parent=host,
            emu_thread=getattr(self, 'emu_thread', None)
        )
        self.vbox_dialog.show()
        self.vbox_dialog.raise_()

    def _reload_keybindings(self):
        self.key_map = self.settings_mgr.get_qt_key_map()

    def _on_frame_ready(self, top_img: QImage, bot_img: QImage):
        if getattr(self, "auto_boot_active", False) and getattr(self.emu_thread, "control_arr", None) and self.emu_thread.control_arr[27] == 2:
            self.auto_boot_active = False
            if hasattr(self, "auto_boot_timer") and self.auto_boot_timer.isActive():
                self.auto_boot_timer.stop()

        self.top_screen_widget.update_frame(top_img)
        if self.touch_drawer.isVisible():
            self.touch_screen_widget.update_frame(bot_img)

    def _toggle_touch_screen(self):
        is_vis = not self.touch_drawer.isVisible()
        self.touch_drawer.setVisible(is_vis)
        self.btn_toggle_touch.setText(t("hud_btn_touch_close") if is_vis else t("hud_btn_touch_open"))

    def _toggle_scanner_drawer(self):
        is_vis = not self.scanner_panel.isVisible()
        self.scanner_panel.setVisible(is_vis)
        if not is_vis:
            self._stop_camera()

    # ----------------- GESTIONE TASTIERA GIOCO -----------------
    def keyPressEvent(self, event: QKeyEvent):
        if self.txt_search.hasFocus():
            super().keyPressEvent(event)
            return

        key = event.key()

        # Tasto primario (A / N): durante il boot, invia sia START (salta loghi/filmati) sia A (conferma)
        if key in self.key_map and self.key_map[key] == 8:
            is_booting = getattr(self, "auto_boot_active", False) and (
                getattr(self.emu_thread, "control_arr", None) is None or self.emu_thread.control_arr[27] != 2
            )
            if is_booting:
                # Se siamo ancora nelle fasi iniziali, manda START per accelerare/saltare il filmato
                self.emu_thread.set_key(3, True) # START
                self.emu_thread.set_key(8, True) # A
                QTimer.singleShot(120, lambda: (
                    self.emu_thread.set_key(3, False),
                    self.emu_thread.set_key(8, False)
                ))
            else:
                # In gioco nell'Overworld, 'N' agisce ESCLUSIVAMENTE come tasto A (interazione / dialogo / sottomenu)
                self.emu_thread.set_key(8, True)
            event.accept()
            return

        if key in self.key_map:
            joypad_id = self.key_map[key]
            self.emu_thread.set_key(joypad_id, True)
            event.accept()
        elif key == Qt.Key.Key_Tab:
            self._toggle_touch_screen()
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if self.txt_search.hasFocus():
            super().keyReleaseEvent(event)
            return

        key = event.key()
        if key in self.key_map:
            joypad_id = self.key_map[key]
            self.emu_thread.set_key(joypad_id, False)
            event.accept()
        else:
            super().keyReleaseEvent(event)

    # ----------------- TCG SCANNER LOGIC -----------------
    def _on_finish_changed(self, idx):
        mapping = {0: "normale", 1: "holo", 2: "reverse holo"}
        self.selected_finish = mapping.get(idx, "normale")
        if self.current_evaluated_card:
            self._evaluate_and_show(self.current_evaluated_card)

    def _on_search_clicked(self):
        query = self.txt_search.text().strip()
        if not query: return
        results = self.tcg_core.search_cards(query, limit=1)
        if not results:
            self.lbl_card_title.setText("Nessun Risultato")
            self.lbl_card_meta.setText(f"Nessuna carta trovata per '{query}'.")
            self.lbl_card_stats.setText("")
            self.btn_inject.setEnabled(False)
            return
        self._evaluate_and_show(results[0])

    def _evaluate_and_show(self, card_item):
        self.current_evaluated_card = card_item
        res = self.tcg_core.evaluate_card(card_item, finish=self.selected_finish, register=False)
        if not res.get("success"):
            self.lbl_card_title.setText("❌ Carta Duplicata")
            self.lbl_card_meta.setText(res.get("message", "Questa carta è già stata registrata!"))
            self.lbl_card_stats.setText("")
            self.btn_inject.setEnabled(False)
            return

        self.last_eval_res = res
        self.lbl_card_title.setText(f"{res['species_name']} — Lv. {res['level']}")
        art_line = f"<b>Illustratore:</b> {res['artist']}<br>" if res.get('artist') else ""
        meta_str = f"<b>Set:</b> {res['set_name']} #{res['card_number']} ({res['release_year']})<br>" \
                   f"{art_line}" \
                   f"<b>Tier:</b> {res['tier_name']}<br>" \
                   f"<b>Sfera:</b> {res['pokeball_name']} ({res['era_name']})"
        self.lbl_card_meta.setText(meta_str)

        ivs = res['ivs']
        def f_iv(v): return f"<b style='color:#ffd700;'>31★</b>" if v == 31 else str(v)
        stats_str = f"<b>IV:</b> PS:{f_iv(ivs['hp'])} | ATK:{f_iv(ivs['atk'])} | DEF:{f_iv(ivs['def'])} | " \
                    f"SPA:{f_iv(ivs['spa'])} | SPD:{f_iv(ivs['spd'])} | SPE:{f_iv(ivs['spe'])}"
        self.lbl_card_stats.setText(stats_str)
        self.btn_inject.setEnabled(True)

    def _on_inject_clicked(self):
        if not hasattr(self, 'last_eval_res') or not self.last_eval_res:
            return

        final_eval = self.tcg_core.evaluate_card(self.current_evaluated_card, finish=self.selected_finish, register=True)
        if not final_eval.get("success"):
            QMessageBox.warning(self, "Attenzione", final_eval.get("message"))
            return

        inject_res = self.injector.inject_pokemon(final_eval, target_save=self.user_save_path)

        if inject_res.get("success"):
            self.last_injected_save_bytes = inject_res.get("save_bytes")
            try:
                from launcher.virtual_box_manager import VirtualBoxManager
                vbox = VirtualBoxManager(self.username)
                vbox.add_card(
                    self.current_evaluated_card,
                    finish=self.selected_finish,
                    status="inviato",
                    injected_target=inject_res.get("target")
                )
            except Exception as e:
                print(f"[VirtualBox] Errore sync da scanner: {e}")
            msg = (
                f"✔ <b>{final_eval['species_name']}</b> (Lv.{final_eval['level']}) iniettato con successo in <b>{inject_res.get('target')}</b>!<br><br>"
                f"⚠️ <b>COME CARICARE IL POKÉMON NEL GIOCO:</b><br>"
                f"• L'emulatore tiene lo stato della partita corrente nella memoria RAM.<br>"
                f"• <b>NON salvare dal menu interno del gioco (SALVA)</b> prima di aver ricaricato.<br><br>"
                f"Vuoi tornare al Launcher adesso per ricaricare subito la partita e trovare il tuo Pokémon in squadra?"
            )
            reply = QMessageBox.question(
                self,
                "Iniezione Completata!",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            self.btn_inject.setEnabled(False)
            self._stop_camera() # Auto-stop fotocamera a riscatto completato
            if reply == QMessageBox.StandardButton.Yes:
                self._on_close_to_launcher()

    def _set_camera_standby_placeholder(self):
        """Imposta il visualizzatore in modalità Standby verticale (2.5 : 3.5)."""
        html = (
            "<div style='text-align: center; color: #64748b; line-height: 1.4;'>"
            "<div style='font-size: 34px; margin-bottom: 6px;'>🎴</div>"
            "<b style='color: #00e5ff; font-size: 13px; letter-spacing: 1px;'>MIRINO CARTA TCG</b><br>"
            "<span style='font-size: 11px; color: #475569;'>Rapporto Verticale 2.5 : 3.5</span><br><br>"
            "<span style='font-size: 12px; color: #94a3b8;'>Telecamera in Standby</span><br>"
            "<span style='font-size: 11px; color: #64748b;'>Premi il pulsante sotto<br>per avviare la scansione</span>"
            "</div>"
        )
        self.lbl_camera.setText(html)
        self.lbl_camera.setStyleSheet(
            "background-color: #070d18; border: 2px dashed #1e293b; border-radius: 12px;"
        )

    def _toggle_camera_feed(self):
        if self.cap is not None and self.cap.isOpened():
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(1)
                if not self.cap or not self.cap.isOpened():
                    QMessageBox.warning(self, "Webcam Non Trovata", "Nessuna fotocamera rilevata o accessibile sul sistema.")
                    self.cap = None
                    return

            self.btn_toggle_camera.setText(t("btn_stop_cam"))
            self.btn_toggle_camera.setStyleSheet(
                "QPushButton { border: 1.5px solid #ef4444; color: #ef4444; font-weight: 700; padding: 10px; border-radius: 8px; background-color: rgba(239, 68, 68, 0.1); }"
                "QPushButton:hover { background-color: rgba(239, 68, 68, 0.25); }"
            )
            self.btn_manual_capture.setEnabled(True)
            self.btn_manual_capture.setText("📸 SCATTA [1/6]")
            self.lbl_camera.setStyleSheet(
                "background-color: #000000; border: 2px solid #00e5ff; border-radius: 12px;"
            )
            self.scan_phase = 1
            self.scan_shots = {}
            self.green_start_time = None
            self.last_green_time = 0.0
            self.phase_cooldown_until = 0.0
            self.phase_transition_msg = ""
            self.is_recognizing = False
            self.flash_counter = 0
            self.camera_timer.start(33) # ~30 FPS
        except Exception as e:
            QMessageBox.critical(self, "Camera Error", f"Unable to start webcam: {e}")
            self._stop_camera()

    def _stop_camera(self):
        if self.camera_timer.isActive():
            self.camera_timer.stop()
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.btn_toggle_camera.setText(t("btn_start_cam"))
        self.btn_toggle_camera.setStyleSheet(
            "QPushButton { border: 1.5px solid #00e5ff; color: #00e5ff; font-weight: 700; padding: 10px; border-radius: 8px; }"
            "QPushButton:hover { background-color: rgba(0, 229, 255, 0.15); }"
        )
        self.btn_manual_capture.setEnabled(False)
        self.btn_manual_capture.setText(t("btn_capture"))
        self.green_start_time = None
        self.scan_phase = 1
        self.phase_cooldown_until = 0.0
        self.phase_transition_msg = ""
        if not self.is_recognizing:
            self._set_camera_standby_placeholder()

    def _detect_card(self, resized_bgr):
        """
        Rileva l'allineamento della carta in base alla fase corrente:
        - Fase 1: Fronte intero (sagoma verticale completa)
        - Fase 2: Retro della carta (dorso blu autentico con Poké Ball)
        - Fase 3: Zoom Nome & PV (parte alta ravvicinata con testo nitido)
        - Fase 4: Zoom Numero & Set (parte in basso ravvicinata)
        """
        gray = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # FASI 1 & 2: CARTA INTERA
        if self.scan_phase in (1, 2):
            edges = cv2.Canny(blurred, 35, 110)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            otsu_edges = cv2.Canny(otsu, 40, 120)
            combined = cv2.bitwise_or(closed, otsu_edges)
            contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            best_cand = None
            best_score = -999999.0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 8500 or area > (260 * 364 * 0.95):
                    continue

                x, y, w, h = cv2.boundingRect(cnt)
                if w <= 0 or h <= 0:
                    continue

                # 1. Filtro di riempimento rettangolare (Rectangular Fill)
                # Una vera carta TCG riempie oltre il 78% del proprio rettangolo contenitore.
                # Un viso umano, testa o corpo riempiono solo il 40-55%: scartati tassativamente!
                rect_fill = area / float(w * h)
                if rect_fill < 0.78:
                    continue

                # 2. Approssimazione geometrica (poligono convesso a 4 lati con angoli retti)
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.035 * peri, True)
                is_convex = cv2.isContourConvex(approx)
                if not is_convex or len(approx) not in (4, 5):
                    continue

                ratio = w / float(h)
                cx = x + w // 2
                cy = y + h // 2
                dist = ((cx - 130) ** 2 + (cy - 182) ** 2) ** 0.5
                area_ratio = float(w * h) / 60736.0

                # Formato carta Pokémon fisica (63x88 mm = ~0.716)
                is_vert = 0.58 <= ratio <= 0.85
                is_horiz = 1.18 <= ratio <= 1.72
                if not is_vert and not is_horiz:
                    continue

                score = (rect_fill * 10000.0) + area - (dist * 350.0)
                if score > best_score:
                    best_score = score
                    best_cand = {
                        'contour': cnt,
                        'bbox': (x, y, w, h),
                        'cx': cx, 'cy': cy,
                        'ratio': ratio,
                        'dist': dist,
                        'area_ratio': area_ratio,
                        'is_vert': is_vert,
                        'is_horiz': is_horiz
                    }

            phase_label = "[1/6] FRONTE" if self.scan_phase == 1 else "[2/6] RETRO"
            sub_default = "Centra la carta nel mirino" if self.scan_phase == 1 else "Mostra il dorso blu con Poké Ball"

            if best_cand is None:
                return "red", f"{phase_label}: INQUADRA", sub_default, None, None

            c = best_cand
            if c['is_horiz']:
                return "orange", f"{phase_label}: RUOTA", "Gira la carta in verticale", c['contour'], c['bbox']

            # CONTROLLO CROMATICO RIGIDO PER FASE 2: DEVE ESSERE IL RETRO BLU E NON IL FRONTE!
            if self.scan_phase == 2:
                bx, by, bw, bh = c['bbox']
                card_roi = resized_bgr[by:by+bh, bx:bx+bw]
                if card_roi.size > 0:
                    # 1. Bordo perimetrale (il dorso Pokémon ha un bordo blu/indaco scuro)
                    rh, rw_roi = card_roi.shape[:2]
                    border_mask = np.zeros((rh, rw_roi), dtype=np.uint8)
                    border_mask[:max(1, int(rh * 0.10)), :] = 255
                    border_mask[max(0, int(rh * 0.90)):, :] = 255
                    border_mask[:, :max(1, int(rw_roi * 0.10))] = 255
                    border_mask[:, max(0, int(rw_roi * 0.90)):] = 255

                    hsv = cv2.cvtColor(card_roi, cv2.COLOR_BGR2HSV)
                    blue_mask = cv2.inRange(hsv, np.array([100, 50, 30]), np.array([130, 255, 220]))
                    border_blue = np.sum((blue_mask > 0) & (border_mask > 0)) / float(max(1, np.sum(border_mask > 0)))

                    # 2. Verifica se è identica al fronte (carta non girata)
                    front_shot = self.scan_shots.get('front')
                    is_same_as_front = False
                    if front_shot is not None and front_shot.size > 0:
                        fh, fw = front_shot.shape[:2]
                        scaled_roi = cv2.resize(card_roi, (fw, fh))
                        diff_mean = np.mean(np.abs(scaled_roi.astype(float) - front_shot.astype(float)))
                        if diff_mean < 35.0:
                            is_same_as_front = True

                    if border_blue < 0.38 or is_same_as_front:
                        return "red", "[2/6] GIRA LA CARTA!", "Mostra il dorso blu con Poké Ball", c['contour'], c['bbox']

            if c['dist'] <= 28 and (0.65 <= c['area_ratio'] <= 1.38) and (0.54 <= c['ratio'] <= 0.88):
                return "green", f"{phase_label}: OTTIMO!", "Tieni fermo per scattare...", c['contour'], c['bbox']

            if c['dist'] > 28 and c['dist'] <= 68:
                return "orange", f"{phase_label}: CENTRA", "Sposta verso il centro", c['contour'], c['bbox']
            elif c['area_ratio'] < 0.65:
                return "orange", f"{phase_label}: AVVICINA", "Avvicina la carta", c['contour'], c['bbox']
            elif c['area_ratio'] > 1.38:
                return "orange", f"{phase_label}: ALLONTANA", "Allontana leggermente", c['contour'], c['bbox']

            return "orange", f"{phase_label}: ALLINEA", "Allinea al riquadro", c['contour'], c['bbox']

        # FASE 3: ZOOM NOME & PV (PARTE ALTA RAVVICINATA)
        elif self.scan_phase == 3:
            return "orange", "[3/6] ZOOM NOME", "Inquadra il Nome e premi [📸 SCATTA]", None, (20, 50, 220, 120)

        # FASE 4: ZOOM NUMERO CARTA (PARTE IN BASSO RAVVICINATA)
        elif self.scan_phase == 4:
            return "orange", "[4/6] ZOOM NUMERO", "Inquadra il Numero (31/147) e premi [📸 SCATTA]", None, (20, 170, 220, 120)

        # FASE 5: ZOOM ANNO CARTA (BORDO IN BASSO COPYRIGHT)
        elif self.scan_phase == 5:
            return "orange", "[5/6] ZOOM ANNO", "Inquadra l'Anno in basso (es. 2017) e premi [📸 SCATTA]", None, (20, 220, 220, 90)

        # FASE 6: ZOOM AUTORE CARTA (BORDO IN BASSO / ILLUSTRATORE)
        elif self.scan_phase == 6:
            return "orange", "[6/6] ZOOM AUTORE", "Inquadra l'Autore (es. Illus. Sugimori) e premi [📸 SCATTA]", None, (20, 200, 220, 100)

        return "red", "INQUADRA", "Posiziona la carta", None, None

    def _update_camera_frame(self):
        if not self.cap or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return

        # Ritaglio centrale con rapporto verticale 2.5 : 3.5
        fh, fw = frame.shape[:2]
        target_ratio = 2.5 / 3.5
        
        crop_h = fh
        crop_w = int(crop_h * target_ratio)
        if crop_w > fw:
            crop_w = fw
            crop_h = int(crop_w / target_ratio)
            
        x1 = max(0, (fw - crop_w) // 2)
        y1 = max(0, (fh - crop_h) // 2)
        cropped = frame[y1:y1 + crop_h, x1:x1 + crop_w]
        self.latest_high_res_frame = cropped

        # Scala alle dimensioni del box verticale 260 x 364
        resized = cv2.resize(cropped, (260, 364), interpolation=cv2.INTER_LINEAR)
        rh, rw = resized.shape[:2]

        now = time.time()

        # Effetto flash bianco allo scatto
        if self.flash_counter > 0:
            white = np.full_like(resized, 255)
            resized = cv2.addWeighted(resized, 0.35, white, 0.65, 0)
            self.flash_counter -= 1
        elif self.is_recognizing:
            scan_y = int((now * 220) % 285) + 36
            cv2.line(resized, (26, scan_y), (234, scan_y), (255, 229, 0), 2)
            cv2.rectangle(resized, (0, 0), (rw, 30), (12, 16, 24), -1)
            cv2.circle(resized, (16, 15), 5, (255, 229, 0), -1)
            cv2.putText(resized, "RICONOSCIMENTO IN CORSO...", (28, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)
            cv2.rectangle(resized, (0, 332), (rw, 364), (12, 16, 24), -1)
            cv2.putText(resized, "Elaborazione delle 6 foto TCG", (32, 350),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200, 210, 220), 1)
        else:
            in_transition = (now < self.phase_cooldown_until)

            if in_transition:
                # Pausa obbligatoria per permettere all'utente di girare o avvicinare la carta
                self.green_start_time = None
                state = "orange"
                bcolor = (10, 160, 245)
                rem = max(0.0, self.phase_cooldown_until - now)
                status_msg = f"PREPARATI FASE [{self.scan_phase}/6]"
                sub_msg = f"{self.phase_transition_msg} ({rem:.1f}s)"
                progress = 0.0
                bbox = None
            else:
                state, status_msg, sub_msg, cnt, bbox = self._detect_card(resized)
                self.card_detection_state = state
                self.latest_bbox = bbox

                if bbox is not None and self.scan_phase in (1, 2):
                    bx, by, bw, bh = bbox
                    scale_y = cropped.shape[0] / 364.0
                    scale_x = cropped.shape[1] / 260.0
                    fx1 = max(0, int(bx * scale_x))
                    fy1 = max(0, int(by * scale_y))
                    fx2 = min(cropped.shape[1], int((bx + bw) * scale_x))
                    fy2 = min(cropped.shape[0], int((by + bh) * scale_y))
                    if fx2 > fx1 and fy2 > fy1:
                        self.latest_card_crop = cropped[fy1:fy2, fx1:fx2].copy()
                    else:
                        self.latest_card_crop = cropped
                else:
                    self.latest_card_crop = cropped

                # Colore Semaforo e Guida
                if state == "green":
                    bcolor = (50, 225, 40)
                    sub_msg = "Carta allineata! Premi [📸 SCATTA]"
                elif state == "orange":
                    bcolor = (10, 160, 245)
                else:
                    bcolor = (55, 55, 235)

            # Disegna mirino specifico in base alla fase
            if self.scan_phase in (1, 2):
                bx1, by1 = 26, 36
                bx2, by2 = 234, 328
            elif self.scan_phase == 3:
                bx1, by1 = 20, 50
                bx2, by2 = 240, 170
            elif self.scan_phase == 4:
                bx1, by1 = 20, 170
                bx2, by2 = 240, 290
            elif self.scan_phase == 5:
                bx1, by1 = 20, 220
                bx2, by2 = 240, 310
            else: # Fase 6: Zoom Autore
                bx1, by1 = 20, 200
                bx2, by2 = 240, 300

            blen = 20
            thick = 3 if state == "green" else 2
            cv2.line(resized, (bx1, by1), (bx1 + blen, by1), bcolor, thick)
            cv2.line(resized, (bx1, by1), (bx1 + blen, by1), bcolor, thick)
            cv2.line(resized, (bx2, by1), (bx2 - blen, by1), bcolor, thick)
            cv2.line(resized, (bx2, by1), (bx2 - blen, by1), bcolor, thick)
            cv2.line(resized, (bx1, by2), (bx1 + blen, by2), bcolor, thick)
            cv2.line(resized, (bx1, by2), (bx1, by2 - blen), bcolor, thick)
            cv2.line(resized, (bx2, by2), (bx2 - blen, by2), bcolor, thick)
            cv2.line(resized, (bx2, by2), (bx2, by2 - blen), bcolor, thick)

            # Barra superiore di stato con 6 indicatori di fase
            cv2.rectangle(resized, (0, 0), (rw, 30), (12, 16, 24), -1)
            for i in range(1, 7):
                dot_x = 10 + (i - 1) * 9
                dot_col = (0, 229, 255) if i <= self.scan_phase else (60, 65, 75)
                cv2.circle(resized, (dot_x, 15), 3, dot_col, -1)

            cv2.putText(resized, status_msg, (68, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.34, (255, 255, 255), 1)

            # Barra inferiore di istruzioni
            cv2.rectangle(resized, (0, 332), (rw, 364), (12, 16, 24), -1)
            cv2.putText(resized, sub_msg, (12, 350),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.33, (200, 210, 220), 1)

        # Conversione e rendering Qt
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, rw, rh, rw * 3, QImage.Format.Format_RGB888)
        self.lbl_camera.setPixmap(QPixmap.fromImage(qimg))

    def _advance_scan_phase(self, high_res_frame):
        """Salva la foto della fase attuale e passa alla successiva con pausa di sicurezza."""
        if self.is_recognizing or high_res_frame is None:
            return

        now = time.time()
        self.flash_counter = 3
        self.green_start_time = None

        fh, fw = high_res_frame.shape[:2]
        scale_y = fh / 364.0
        scale_x = fw / 260.0

        if self.scan_phase == 1:
            self.scan_shots['front'] = high_res_frame.copy()
            self.scan_phase = 2
            self.phase_cooldown_until = now + 2.5
            self.phase_transition_msg = "Gira la carta e mostra il dorso blu"
            self.btn_manual_capture.setText("📸 SCATTA [2/6 RETRO]")
        elif self.scan_phase == 2:
            self.scan_shots['back'] = high_res_frame.copy()
            self.scan_phase = 3
            self.phase_cooldown_until = now + 2.5
            self.phase_transition_msg = "Avvicina la parte alta (Nome e PV)"
            self.btn_manual_capture.setText("📸 SCATTA [3/6 NOME]")
        elif self.scan_phase == 3:
            # Salva crop mirato del nome e frame intero
            crop_box = high_res_frame[max(0, int(50 * scale_y)):min(fh, int(170 * scale_y)), max(0, int(20 * scale_x)):min(fw, int(240 * scale_x))]
            self.scan_shots['header'] = high_res_frame.copy()
            self.scan_shots['header_crop'] = crop_box.copy()
            self.scan_phase = 4
            self.phase_cooldown_until = now + 2.5
            self.phase_transition_msg = "Avvicina il Numero della carta (31/147)"
            self.btn_manual_capture.setText("📸 SCATTA [4/6 NUMERO]")
        elif self.scan_phase == 4:
            # Salva crop mirato del numero e frame intero
            crop_box = high_res_frame[max(0, int(170 * scale_y)):min(fh, int(290 * scale_y)), max(0, int(20 * scale_x)):min(fw, int(240 * scale_x))]
            self.scan_shots['footer'] = high_res_frame.copy()
            self.scan_shots['footer_crop'] = crop_box.copy()
            self.scan_phase = 5
            self.phase_cooldown_until = now + 2.5
            self.phase_transition_msg = "Avvicina l'Anno in basso (es. 2017)"
            self.btn_manual_capture.setText("📸 SCATTA [5/6 ANNO]")
        elif self.scan_phase == 5:
            # Salva crop mirato dell'anno (bordo inferiore) e frame intero
            crop_box = high_res_frame[max(0, int(220 * scale_y)):min(fh, int(310 * scale_y)), max(0, int(20 * scale_x)):min(fw, int(240 * scale_x))]
            self.scan_shots['year'] = high_res_frame.copy()
            self.scan_shots['year_crop'] = crop_box.copy()
            self.scan_phase = 6
            self.phase_cooldown_until = now + 2.5
            self.phase_transition_msg = "Avvicina l'Autore (es. Illus. Sugimori)"
            self.btn_manual_capture.setText("📸 SCATTA [6/6 AUTORE]")
        elif self.scan_phase == 6:
            # Salva crop mirato dell'autore (bordo inferiore) e frame intero
            crop_box = high_res_frame[max(0, int(200 * scale_y)):min(fh, int(300 * scale_y)), max(0, int(20 * scale_x)):min(fw, int(240 * scale_x))]
            self.scan_shots['author'] = high_res_frame.copy()
            self.scan_shots['author_crop'] = crop_box.copy()
            self.scan_phase = 7
            self.phase_cooldown_until = 0.0
            self.phase_transition_msg = ""
            self._finish_and_process_scan()

    def _on_manual_capture_clicked(self):
        """Consente lo scatto manuale istantaneo per la fase corrente."""
        frame_to_use = getattr(self, 'latest_card_crop', self.latest_high_res_frame)
        if frame_to_use is not None and not self.is_recognizing:
            self._advance_scan_phase(frame_to_use)

    def _finish_and_process_scan(self):
        """Ferma la fotocamera e avvia l'analisi intelligente multi-fase."""
        # 1. Ferma subito la webcam per bloccare ogni loop
        if self.camera_timer.isActive():
            self.camera_timer.stop()
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.btn_toggle_camera.setText("📷 AVVIA SCANSIONE")
        self.btn_manual_capture.setEnabled(False)
        self.btn_manual_capture.setText("📸 SCATTA")
        self.is_recognizing = True

        # 2. Mostra schermata di elaborazione
        html = (
            "<div style='text-align: center; color: #00e5ff; line-height: 1.5;'>"
            "<div style='font-size: 38px; margin-bottom: 6px;'>🔍</div>"
            "<b style='color: #00e5ff; font-size: 14px;'>ANALISI MULTI-FASE IN CORSO</b><br>"
            "<span style='font-size: 11px; color: #94a3b8;'>Elaborazione delle 6 foto (Fronte, Retro, Nome, Numero, Anno, Autore)...</span><br><br>"
            "<span style='font-size: 11px; color: #64748b;'>Ricerca nel database Pokémon TCG...</span>"
            "</div>"
        )
        self.lbl_camera.setText(html)
        self.lbl_camera.setStyleSheet(
            "background-color: #070d18; border: 2px solid #00e5ff; border-radius: 12px;"
        )

        # 3. Avvio worker asincrono in background
        self.recognizer_worker = CardRecognizerWorker(self.scan_shots, self.tcg_core)
        self.recognizer_worker.recognition_completed.connect(self._on_recognition_completed)
        self.recognizer_worker.recognition_failed.connect(self._on_recognition_failed)
        self.recognizer_worker.start()

    def _on_recognition_completed(self, card_item):
        self.is_recognizing = False
        self.txt_search.setText(card_item['name'])
        self._evaluate_and_show(card_item)

        art_display = f"<span style='font-size: 11px; color: #38bdf8;'>🎨 {card_item['artist']}</span><br>" if card_item.get('artist') else ""

        # Visualizzatore con vittoria
        html = (
            "<div style='text-align: center; color: #10b981; line-height: 1.5;'>"
            "<div style='font-size: 40px; margin-bottom: 6px;'>🎉</div>"
            "<b style='color: #10b981; font-size: 14px;'>CARTA TROVATA!</b><br>"
            f"<span style='font-size: 13px; color: #ffffff;'><b>{card_item['name']}</b> #{card_item['card_number']}</span><br>"
            f"<span style='font-size: 11px; color: #94a3b8;'>{card_item['set_name']} ({card_item.get('release_year', '')})</span><br>"
            f"{art_display}<br>"
            "<div style='background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 8px; padding: 6px;'>"
            "<span style='color: #00e5ff; font-weight: 700; font-size: 11px;'>Ehi, ce l'abbiamo fatta!</span><br>"
            "<span style='color: #cbd5e1; font-size: 10px;'>Clicca su <b>⚡ INIETTA</b> per inviarla al gioco!</span>"
            "</div>"
            "</div>"
        )
        self.lbl_camera.setText(html)
        self.lbl_camera.setStyleSheet(
            "background-color: #071510; border: 2px solid #10b981; border-radius: 12px;"
        )

        art_msg = f"<b>Autore / Illustratore:</b> {card_item['artist']}<br>" if card_item.get('artist') else ""

        # Notifica esplicita di successo
        QMessageBox.information(
            self,
            "🎉 CARTA IDENTIFICATA CON SUCCESSO!",
            f"<b>Ehi, ce l'abbiamo fatta!</b><br><br>"
            f"<b>Pokémon:</b> {card_item['name']}<br>"
            f"<b>Espansione:</b> {card_item['set_name']} #{card_item['card_number']} ({card_item.get('release_year', '')})<br>"
            f"{art_msg}<br>"
            f"I dati sono stati caricati nella scheda.<br>"
            f"Clicca su <b>⚡ INIETTA NEL GIOCO</b> per riscattarla!"
        )

    def _on_recognition_failed(self, err_msg):
        self.is_recognizing = False
        html = (
            "<div style='text-align: center; color: #ef4444; line-height: 1.5;'>"
            "<div style='font-size: 38px; margin-bottom: 6px;'>⚠️</div>"
            "<b style='color: #ef4444; font-size: 14px;'>SCANSIONE NON RIUSCITA</b><br>"
            f"<span style='font-size: 11px; color: #94a3b8;'>{err_msg}</span><br><br>"
            "<span style='font-size: 11px; color: #64748b;'>Premi <b>📷 AVVIA SCANSIONE</b> per riprovare<br>o cerca il nome nella barra di ricerca</span>"
            "</div>"
        )
        self.lbl_camera.setText(html)
        self.lbl_camera.setStyleSheet(
            "background-color: #15070a; border: 2px solid #ef4444; border-radius: 12px;"
        )

        QMessageBox.warning(
            self,
            "Scansione Incompleta",
            f"Non è stato possibile identificare la carta con certezza.<br><br>"
            f"<i>{err_msg}</i><br><br>"
            f"Puoi cliccare su <b>📷 AVVIA SCANSIONE</b> per riprovare, oppure selezionare la carta tramite la barra di ricerca."
        )

    def _on_close_to_launcher(self):
        unregister_language_listener(self._retranslate_ui)
        self._stop_camera()
        if hasattr(self, 'gamepad_listener') and self.gamepad_listener:
            self.gamepad_listener.stop()
        if hasattr(self, 'emu_thread') and self.emu_thread:
            self.emu_thread.stop()
        try:
            rom_stem = self.rom_path.stem
            user_dir = self.user_save_path.parent
            prof_sav = user_dir / f"{rom_stem}.sav"

            # Se durante questa sessione è stato iniettato un Pokémon, proteggiamo il file
            # affinché la chiusura di melonDS non abbia sovrascritto il salvataggio con la vecchia RAM
            if hasattr(self, 'last_injected_save_bytes') and self.last_injected_save_bytes:
                for p_sav in user_dir.glob("*.sav"):
                    with open(p_sav, "wb") as f:
                        f.write(self.last_injected_save_bytes)
                for gen_sav in [BASE_DIR / "saves" / f"{rom_stem}.sav", BASE_DIR / "saves" / "Pokémon Bianco 2.sav", self.rom_path.parent / f"{rom_stem}.sav"]:
                    with open(gen_sav, "wb") as f:
                        f.write(self.last_injected_save_bytes)
            elif prof_sav.exists():
                for other in user_dir.glob("*.sav"):
                    if other != prof_sav:
                        shutil.copy2(prof_sav, other)
                shutil.copy2(prof_sav, BASE_DIR / "saves" / f"{rom_stem}.sav")
        except Exception as e:
            print(f"Errore sincronizzazione salvataggio: {e}", flush=True)

        self.close()
        if self.launcher_ref:
            self.launcher_ref.show()

    def closeEvent(self, event):
        self._on_close_to_launcher()
        event.accept()

