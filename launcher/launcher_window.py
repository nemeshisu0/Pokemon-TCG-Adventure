#!/usr/bin/env python3
"""
Finestra Principale del Launcher Desktop per Pokémon TCG Adventure.
Presenta interfaccia in stile PokeMMO con gestione account, verifica ROM,
configurazione grafica, selezione lingua (EN/IT) e pulsante di avvio 'PLAY'.
"""

import sys
import os
import shutil
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QFileDialog,
    QFrame, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QKeyEvent

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from launcher.ui_theme import STYLE_SHEET
from launcher.account_manager import AccountManager
from launcher.rom_manager import ROMManager
from launcher.settings_dialog import SettingsDialog
from launcher.i18n import (
    t, get_language, register_language_listener, unregister_language_listener
)


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(920, 580)
        self.setStyleSheet(STYLE_SHEET)

        self.account_mgr = AccountManager()
        self.rom_mgr = ROMManager()
        self.is_register_mode = False

        self._build_ui()
        self._load_saved_preferences()
        self._retranslate_ui()
        register_language_listener(self._retranslate_ui)

    def _build_ui(self):
        central = QWidget(self)
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(35, 30, 35, 25)
        main_layout.setSpacing(20)

        # ----------------- HEADER -----------------
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(4)

        self.lbl_title = QLabel("POKÉMON TCG ADVENTURE")
        self.lbl_title.setObjectName("TitleLabel")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_subtitle = QLabel()
        self.lbl_subtitle.setObjectName("SubtitleLabel")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.lbl_title)
        header_layout.addWidget(self.lbl_subtitle)
        main_layout.addLayout(header_layout)

        # ----------------- CENTER CARD -----------------
        center_container = QHBoxLayout()
        center_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card_frame = QFrame()
        self.card_frame.setObjectName("CardFrame")
        self.card_frame.setFixedWidth(420)
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(15)

        # Tabs Accedi / Registrati
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(8)
        self.btn_tab_login = QPushButton()
        self.btn_tab_login.setObjectName("TabButtonActive")
        self.btn_tab_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_login.clicked.connect(self._set_login_mode)

        self.btn_tab_register = QPushButton()
        self.btn_tab_register.setObjectName("TabButtonInactive")
        self.btn_tab_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_register.clicked.connect(self._set_register_mode)

        tab_layout.addWidget(self.btn_tab_login)
        tab_layout.addWidget(self.btn_tab_register)
        card_layout.addLayout(tab_layout)

        # Campi input
        self.txt_username = QLineEdit()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.returnPressed.connect(self._on_play_clicked)

        card_layout.addWidget(self.txt_username)
        card_layout.addWidget(self.txt_password)

        # Opzioni extra
        opts_layout = QHBoxLayout()
        self.chk_remember = QCheckBox()
        self.chk_remember.setChecked(True)
        opts_layout.addWidget(self.chk_remember)
        opts_layout.addStretch()
        card_layout.addLayout(opts_layout)

        # Feedback messaggio
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: 600;")
        card_layout.addWidget(self.lbl_status)

        # Pulsantone GIOCA
        self.btn_play = QPushButton()
        self.btn_play.setObjectName("PlayButton")
        self.btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play.clicked.connect(self._on_play_clicked)
        card_layout.addWidget(self.btn_play)

        # Pulsante Box Pokémon Virtuale
        self.btn_box = QPushButton()
        self.btn_box.setObjectName("SecondaryButton")
        self.btn_box.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_box.setStyleSheet("background-color: #17253d; border: 1.5px solid #00e5ff; color: #00e5ff; font-weight: 700; font-size: 14px; padding: 10px; border-radius: 8px;")
        self.btn_box.clicked.connect(self._open_virtual_box)
        card_layout.addWidget(self.btn_box)

        center_container.addWidget(self.card_frame)
        main_layout.addLayout(center_container)
        main_layout.addStretch()

        # ----------------- BOTTOM BAR -----------------
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(12)

        # Box ROM a sinistra
        self.rom_badge = QFrame()
        rom_layout = QHBoxLayout(self.rom_badge)
        rom_layout.setContentsMargins(12, 8, 12, 8)
        rom_layout.setSpacing(10)

        self.lbl_rom_status = QLabel("")
        self.lbl_rom_status.setStyleSheet("font-size: 13px; font-weight: 600;")
        
        self.btn_rom_select = QPushButton()
        self.btn_rom_select.setObjectName("SecondaryButton")
        self.btn_rom_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rom_select.clicked.connect(self._select_rom_file)

        rom_layout.addWidget(self.lbl_rom_status)
        rom_layout.addWidget(self.btn_rom_select)
        bottom_layout.addWidget(self.rom_badge)

        bottom_layout.addStretch()

        # Pulsante Impostazioni & Lingua
        self.btn_settings = QPushButton()
        self.btn_settings.setObjectName("SecondaryButton")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setStyleSheet(
            "QPushButton { background-color: #1e293b; color: #38bdf8; border: 1px solid #334155; border-radius: 8px; padding: 8px 14px; font-weight: 700; font-size: 13px; }"
            "QPushButton:hover { background-color: #334155; border-color: #38bdf8; color: #ffffff; }"
        )
        self.btn_settings.clicked.connect(self._open_settings_dialog)
        bottom_layout.addWidget(self.btn_settings)

        # Selettore Risoluzione a destra
        res_layout = QHBoxLayout()
        self.lbl_res = QLabel()
        self.lbl_res.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600;")
        
        self.combo_res = QComboBox()
        self.combo_res.currentTextChanged.connect(self._on_resolution_changed)

        res_layout.addWidget(self.lbl_res)
        res_layout.addWidget(self.combo_res)
        bottom_layout.addLayout(res_layout)

        main_layout.addLayout(bottom_layout)

    def _retranslate_ui(self, lang_code=None):
        """Aggiorna tutti i testi dell'interfaccia nella lingua selezionata (EN/IT)."""
        self.setWindowTitle(t("app_window_title"))
        self.lbl_title.setText(t("app_header_title"))
        self.lbl_subtitle.setText(t("app_header_subtitle"))

        self.btn_tab_login.setText(t("tab_login"))
        self.btn_tab_register.setText(t("tab_register"))
        self.txt_username.setPlaceholderText(t("username_placeholder"))
        self.txt_password.setPlaceholderText(t("password_placeholder"))
        self.chk_remember.setText(t("remember_account"))

        if self.is_register_mode:
            self.btn_play.setText(t("btn_register_play"))
        else:
            self.btn_play.setText(t("btn_play"))

        self.btn_box.setText(t("btn_virtual_box"))
        self.btn_settings.setText(t("btn_settings"))
        self.lbl_res.setText(t("resolution_label"))

        # Aggiorna opzioni risoluzione
        curr_res = self.combo_res.currentData() or "1080p"
        self.combo_res.blockSignals(True)
        self.combo_res.clear()
        res_items = [
            (t("res_1080p"), "1080p"),
            (t("res_720p"), "720p"),
            (t("res_1440p"), "1440p"),
            (t("res_fullscreen"), "fullscreen"),
        ]
        target_idx = 0
        for idx, (label, val) in enumerate(res_items):
            self.combo_res.addItem(label, val)
            if val == curr_res:
                target_idx = idx
        self.combo_res.setCurrentIndex(target_idx)
        self.combo_res.blockSignals(False)

        self._refresh_rom_ui()

    def _set_login_mode(self):
        self.is_register_mode = False
        self.btn_tab_login.setObjectName("TabButtonActive")
        self.btn_tab_register.setObjectName("TabButtonInactive")
        self.btn_tab_login.setStyle(self.btn_tab_login.style())
        self.btn_tab_register.setStyle(self.btn_tab_register.style())
        self.btn_play.setText(t("btn_play"))
        self.lbl_status.setText("")

    def _set_register_mode(self):
        self.is_register_mode = True
        self.btn_tab_login.setObjectName("TabButtonInactive")
        self.btn_tab_register.setObjectName("TabButtonActive")
        self.btn_tab_login.setStyle(self.btn_tab_login.style())
        self.btn_tab_register.setStyle(self.btn_tab_register.style())
        self.btn_play.setText(t("btn_register_play"))
        self.lbl_status.setText("")

    def _load_saved_preferences(self):
        last_user = self.rom_mgr.get_last_user()
        if last_user:
            self.txt_username.setText(last_user)
            if last_user.lower() == "nemesy2":
                self.txt_password.setText("1234")
                self.btn_play.setFocus()
            else:
                self.txt_password.setFocus()
        else:
            self.txt_username.setFocus()

    def _refresh_rom_ui(self):
        is_ready = self.rom_mgr.is_rom_ready()
        if is_ready:
            rom_name = Path(self.rom_mgr.get_rom_path()).stem
            self.rom_badge.setObjectName("RomBadgeActive")
            self.lbl_rom_status.setText(t("rom_status_loaded", name=rom_name))
            self.lbl_rom_status.setStyleSheet("color: #10b981; font-weight: 700;")
            self.btn_rom_select.setText(t("btn_change"))
        else:
            self.rom_badge.setObjectName("RomBadgeMissing")
            self.lbl_rom_status.setText(t("rom_status_missing"))
            self.lbl_rom_status.setStyleSheet("color: #ef4444; font-weight: 700;")
            self.btn_rom_select.setText(t("btn_load_rom"))

        self.rom_badge.setStyle(self.rom_badge.style())

    def _select_rom_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("btn_load_rom"),
            str(BASE_DIR),
            "Nintendo DS ROMs (*.nds)"
        )
        if file_path:
            if self.rom_mgr.set_rom_path(file_path):
                self._refresh_rom_ui()
                self.lbl_status.setText("")
            else:
                QMessageBox.warning(self, t("dialog_rom_invalid_title"), t("dialog_rom_invalid_msg"))

    def _open_settings_dialog(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def _on_resolution_changed(self, text: str):
        val = self.combo_res.currentData()
        if val:
            self.rom_mgr.set_resolution(val)
        else:
            self.rom_mgr.set_resolution(text.split()[0])

    def _on_play_clicked(self):
        if not self.rom_mgr.is_rom_ready():
            self.lbl_status.setText(t("status_load_rom_first"))
            return

        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()

        if not username or not password:
            self.lbl_status.setText(t("status_enter_credentials"))
            return

        if self.is_register_mode:
            res = self.account_mgr.register(username, password)
        else:
            res = self.account_mgr.login(username, password)

        if not res.get("success"):
            err_code = res.get("error_code")
            if err_code:
                err_text = t(err_code)
            else:
                err_text = res.get("error", t("status_auth_error"))
            self.lbl_status.setText(err_text)
            return

        # Salva ultimo utente se selezionato
        if self.chk_remember.isChecked():
            self.rom_mgr.set_last_user(username)

        self.lbl_status.setStyleSheet("color: #10b981; font-size: 13px; font-weight: 700;")
        self.lbl_status.setText(t("status_logging_in"))

        # Procedi con l'avvio della sessione di gioco
        self._launch_game_session(res["username"], res["save_file"])

    def _launch_game_session(self, username: str, user_save_path: str):
        """
        Sincronizza il salvataggio personale del profilo e avvia
        il Client di Gioco Unificato con HUD laterale per lo scanner.
        """
        rom_path = self.rom_mgr.get_rom_path()
        rom_stem = Path(rom_path).stem
        user_dir = Path(user_save_path).parent

        # Il file di salvataggio atteso dal core melonDS nella cartella del profilo
        profile_rom_sav = user_dir / f"{rom_stem}.sav"
        if not profile_rom_sav.exists() and Path(user_save_path).exists():
            shutil.copy2(user_save_path, profile_rom_sav)
        elif profile_rom_sav.exists() and not Path(user_save_path).exists():
            shutil.copy2(profile_rom_sav, user_save_path)

        # Copia il salvataggio personale del profilo come salvataggio attivo della ROM
        rom_dir = Path(rom_path).parent
        active_sav_1 = rom_dir / f"{rom_stem}.sav"
        active_sav_2 = BASE_DIR / "saves" / "Pokémon Bianco 2.sav"

        source_sav = profile_rom_sav if profile_rom_sav.exists() else Path(user_save_path)
        if source_sav.exists():
            shutil.copy2(source_sav, active_sav_1)
            shutil.copy2(source_sav, active_sav_2)

        # Nascondi il launcher e apri il Client di Gioco In-Game
        from launcher.game_client import GameClientWindow
        self.game_client = GameClientWindow(
            username=username,
            user_save_path=str(source_sav),
            rom_path=rom_path,
            launcher_ref=self
        )
        self.hide()
        self.game_client.show()

    def _open_virtual_box(self):
        """Apre il Box Pokémon Virtuale direttamente dal Launcher."""
        username = self.txt_username.text().strip() or "nemesy2"
        user_dir = BASE_DIR / "saves" / "profiles" / username
        user_dir.mkdir(parents=True, exist_ok=True)
        
        rom_stem = Path(self.rom_mgr.get_rom_path()).stem
        save_file = user_dir / f"{rom_stem}.sav"
        if not save_file.exists():
            save_file = user_dir / f"{username}_bianco2.sav"
        if not save_file.exists():
            save_file = BASE_DIR / "saves" / "Pokémon Bianco 2.sav"

        from launcher.virtual_box_dialog import VirtualBoxDialog
        host = self.centralWidget() or self
        if hasattr(self, 'vbox_dialog') and self.vbox_dialog:
            self.vbox_dialog.show()
            self.vbox_dialog.raise_()
            return
        self.vbox_dialog = VirtualBoxDialog(username=username, user_save_path=str(save_file), parent=host)
        self.vbox_dialog.show()
        self.vbox_dialog.raise_()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_N, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not (self.txt_username.hasFocus() or self.txt_password.hasFocus()):
                self._on_play_clicked()
                event.accept()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        unregister_language_listener(self._retranslate_ui)
        super().closeEvent(event)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--auto-play", action="store_true")
    args, unknown = parser.parse_known_args()

    app = QApplication(sys.argv[:1] + unknown)
    window = LauncherWindow()
    window.show()

    if args.username:
        window.txt_username.setText(args.username)
    if args.password:
        window.txt_password.setText(args.password)
    if args.auto_play:
        QTimer.singleShot(300, window._on_play_clicked)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
