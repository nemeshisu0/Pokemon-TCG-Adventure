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
import shutil
from pathlib import Path

import cv2
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QComboBox, QMessageBox, QSplitter
)
from PyQt6.QtGui import QImage, QPixmap, QPainter, QKeyEvent, QMouseEvent

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

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
from launcher.settings_manager import SettingsManager
from launcher.gamepad_handler import GamepadListener

CORE_LIB_PATH = BASE_DIR / "launcher" / "core" / "melonds_core.so"


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

        # Gestore Comandi e Mappatura Tasti Personalizzabili
        self.settings_mgr = SettingsManager()
        self.key_map = self.settings_mgr.get_qt_key_map()
        self.gamepad_listener = None

        self._build_ui()
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

        lbl_player = QLabel(f"👤 Allenatore: <b style='color:#00e5ff;'>{self.username}</b>")
        lbl_player.setStyleSheet("font-size: 15px;")
        
        lbl_status = QLabel("🟢 Core melonDS Integrato (60 FPS)")
        lbl_status.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px;")

        top_layout.addWidget(lbl_player)
        top_layout.addWidget(lbl_status)
        top_layout.addStretch()

        # Bottoni Azione HUD
        self.btn_toggle_touch = QPushButton("📱 SCHERMO TOUCH")
        self.btn_toggle_touch.setObjectName("SecondaryButton")
        self.btn_toggle_touch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_touch.clicked.connect(self._toggle_touch_screen)

        self.btn_settings = QPushButton("⚙ IMPOSTAZIONI")
        self.btn_settings.setObjectName("SecondaryButton")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self._open_settings_dialog)

        self.btn_toggle_scanner = QPushButton("📷 TCG SCANNER")
        self.btn_toggle_scanner.setObjectName("SecondaryButton")
        self.btn_toggle_scanner.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_scanner.clicked.connect(self._toggle_scanner_drawer)

        self.btn_back_launcher = QPushButton("🚪 Esci al Launcher")
        self.btn_back_launcher.setObjectName("SecondaryButton")
        self.btn_back_launcher.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_launcher.clicked.connect(self._on_close_to_launcher)

        top_layout.addWidget(self.btn_toggle_touch)
        top_layout.addWidget(self.btn_settings)
        top_layout.addWidget(self.btn_toggle_scanner)
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
        
        lbl_touch_title = QLabel("Schermo Touch (Clicca con il mouse):")
        lbl_touch_title.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        touch_layout.addWidget(lbl_touch_title)
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

        hdr_scanner = QLabel("📷 TCG SCANNER HUB")
        hdr_scanner.setObjectName("HeaderLabel")
        scanner_layout.addWidget(hdr_scanner)

        # Riquadro telecamera (In attesa dei punti 2,3,4)
        self.lbl_camera = QLabel("📷 Telecamera Standby\n(Premi 'Attiva' per avviare)")
        self.lbl_camera.setFixedSize(400, 200)
        self.lbl_camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camera.setStyleSheet("background-color: #070d18; border: 1.5px dashed #1e293b; border-radius: 10px; color: #64748b;")
        scanner_layout.addWidget(self.lbl_camera)

        # Ricerca rapida carta
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Cerca carta (es. Charizard, Lucario)...")
        self.txt_search.returnPressed.connect(self._on_search_clicked)
        
        self.btn_search = QPushButton("Cerca")
        self.btn_search.setObjectName("SecondaryButton")
        self.btn_search.clicked.connect(self._on_search_clicked)
        
        search_layout.addWidget(self.txt_search)
        search_layout.addWidget(self.btn_search)
        scanner_layout.addLayout(search_layout)

        # Selezione finitura
        fin_layout = QHBoxLayout()
        lbl_fin = QLabel("Finitura:")
        lbl_fin.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.combo_finish = QComboBox()
        self.combo_finish.addItems(["Normale (Standard)", "Holo (Olografica)", "Reverse Holo"])
        self.combo_finish.currentIndexChanged.connect(self._on_finish_changed)
        fin_layout.addWidget(lbl_fin)
        fin_layout.addWidget(self.combo_finish)
        scanner_layout.addLayout(fin_layout)

        # Scheda Dettagli
        self.details_box = QFrame()
        self.details_box.setObjectName("InnerPanel")
        self.details_layout = QVBoxLayout(self.details_box)
        self.details_layout.setContentsMargins(12, 10, 12, 10)
        self.details_layout.setSpacing(6)

        self.lbl_card_title = QLabel("Nessuna carta selezionata")
        self.lbl_card_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #00e5ff;")
        self.lbl_card_meta = QLabel("Cerca una carta o inquadrala per visualizzare i dettagli.")
        self.lbl_card_meta.setStyleSheet("font-size: 12px; color: #94a3b8;")
        self.lbl_card_meta.setWordWrap(True)
        self.lbl_card_stats = QLabel("")
        self.lbl_card_stats.setStyleSheet("font-size: 12px; color: #cbd5e1;")

        self.details_layout.addWidget(self.lbl_card_title)
        self.details_layout.addWidget(self.lbl_card_meta)
        self.details_layout.addWidget(self.lbl_card_stats)
        scanner_layout.addWidget(self.details_box)

        # Bottone Iniezione
        self.btn_inject = QPushButton("⚡ INIETTA NEL GIOCO")
        self.btn_inject.setObjectName("PlayButton")
        self.btn_inject.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_inject.setEnabled(False)
        self.btn_inject.clicked.connect(self._on_inject_clicked)
        scanner_layout.addWidget(self.btn_inject)

        scanner_layout.addStretch()
        self.splitter.addWidget(self.scanner_panel)
        main_layout.addWidget(self.splitter, 1)

    def _start_inprocess_emulator(self):
        """Avvia il thread del core melonDS collegando i frame video direttamente ai widget."""
        self.emu_thread.frame_ready.connect(self._on_frame_ready)
        self.emu_thread.start()

        # Avvio ascolto Gamepad / Controller USB & Bluetooth
        self.gamepad_listener = GamepadListener(self.emu_thread)
        self.gamepad_listener.start()

    def _open_settings_dialog(self):
        from launcher.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.keybindings_changed.connect(self._reload_keybindings)
        dlg.exec()

    def _reload_keybindings(self):
        self.key_map = self.settings_mgr.get_qt_key_map()

    def _on_frame_ready(self, top_img: QImage, bot_img: QImage):
        self.top_screen_widget.update_frame(top_img)
        if self.touch_drawer.isVisible():
            self.touch_screen_widget.update_frame(bot_img)

    def _toggle_touch_screen(self):
        is_vis = not self.touch_drawer.isVisible()
        self.touch_drawer.setVisible(is_vis)
        self.btn_toggle_touch.setText("📱 CHIUDI TOUCH" if is_vis else "📱 SCHERMO TOUCH")

    def _toggle_scanner_drawer(self):
        self.scanner_panel.setVisible(not self.scanner_panel.isVisible())

    # ----------------- GESTIONE TASTIERA GIOCO -----------------
    def keyPressEvent(self, event: QKeyEvent):
        if self.txt_search.hasFocus():
            super().keyPressEvent(event)
            return

        key = event.key()
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
        meta_str = f"<b>Set:</b> {res['set_name']} #{res['card_number']} ({res['release_year']})<br>" \
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

        inject_res = self.injector.inject_pokemon(final_eval)
        if self.user_save_path.exists() and (BASE_DIR / "saves" / "Pokémon Bianco 2.sav").exists():
            shutil.copy2(BASE_DIR / "saves" / "Pokémon Bianco 2.sav", self.user_save_path)

        if inject_res.get("success"):
            msg = f"✔ {final_eval['species_name']} (Lv.{final_eval['level']}) iniettato con successo in {inject_res.get('target')}!"
            QMessageBox.information(self, "Iniezione Completata!", msg)
            self.btn_inject.setEnabled(False)

    def _update_camera_frame(self):
        pass # Verrà implementato nei Punti 2, 3 e 4!

    def _on_close_to_launcher(self):
        if hasattr(self, 'gamepad_listener') and self.gamepad_listener:
            self.gamepad_listener.stop()
        if hasattr(self, 'emu_thread') and self.emu_thread:
            self.emu_thread.stop()
        try:
            rom_stem = self.rom_path.stem
            user_dir = self.user_save_path.parent
            prof_sav = user_dir / f"{rom_stem}.sav"
            if prof_sav.exists():
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

