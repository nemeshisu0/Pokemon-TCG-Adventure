#!/usr/bin/env python3
"""
Finestra Principale del Launcher Desktop per Pokémon TCG Adventure.
Presenta interfaccia in stile PokeMMO con gestione account, verifica ROM,
configurazione grafica e pulsante di avvio 'GIOCA'.
"""

import sys
import os
import shutil
from pathlib import Path

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QFileDialog,
    QFrame, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QIcon, QFont, QPixmap

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from launcher.ui_theme import STYLE_SHEET
from launcher.account_manager import AccountManager
from launcher.rom_manager import ROMManager


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pokémon TCG Adventure — Game Client")
        self.setFixedSize(920, 580)
        self.setStyleSheet(STYLE_SHEET)

        self.account_mgr = AccountManager()
        self.rom_mgr = ROMManager()
        self.is_register_mode = False

        self._build_ui()
        self._load_saved_preferences()

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

        title = QLabel("POKÉMON TCG ADVENTURE")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Benvenuto, Allenatore")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
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
        self.btn_tab_login = QPushButton("Accedi")
        self.btn_tab_login.setObjectName("TabButtonActive")
        self.btn_tab_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_login.clicked.connect(self._set_login_mode)

        self.btn_tab_register = QPushButton("Nuovo Profilo")
        self.btn_tab_register.setObjectName("TabButtonInactive")
        self.btn_tab_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_register.clicked.connect(self._set_register_mode)

        tab_layout.addWidget(self.btn_tab_login)
        tab_layout.addWidget(self.btn_tab_register)
        card_layout.addLayout(tab_layout)

        # Campi input
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Nome Utente / Allenatore")
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Password")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.returnPressed.connect(self._on_play_clicked)

        card_layout.addWidget(self.txt_username)
        card_layout.addWidget(self.txt_password)

        # Opzioni extra
        opts_layout = QHBoxLayout()
        self.chk_remember = QCheckBox("Ricorda account")
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
        self.btn_play = QPushButton("GIOCA")
        self.btn_play.setObjectName("PlayButton")
        self.btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play.clicked.connect(self._on_play_clicked)
        card_layout.addWidget(self.btn_play)

        center_container.addWidget(self.card_frame)
        main_layout.addLayout(center_container)
        main_layout.addStretch()

        # ----------------- BOTTOM BAR -----------------
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Box ROM a sinistra
        self.rom_badge = QFrame()
        rom_layout = QHBoxLayout(self.rom_badge)
        rom_layout.setContentsMargins(12, 8, 12, 8)
        rom_layout.setSpacing(10)

        self.lbl_rom_status = QLabel("")
        self.lbl_rom_status.setStyleSheet("font-size: 13px; font-weight: 600;")
        
        self.btn_rom_select = QPushButton("Cambia")
        self.btn_rom_select.setObjectName("SecondaryButton")
        self.btn_rom_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rom_select.clicked.connect(self._select_rom_file)

        rom_layout.addWidget(self.lbl_rom_status)
        rom_layout.addWidget(self.btn_rom_select)
        bottom_layout.addWidget(self.rom_badge)

        bottom_layout.addStretch()

        # Selettore Risoluzione a destra
        res_layout = QHBoxLayout()
        lbl_res = QLabel("Risoluzione:")
        lbl_res.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600;")
        
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1080p (Consigliata)", "720p", "1440p (2K)", "Schermo Intero"])
        self.combo_res.currentTextChanged.connect(self._on_resolution_changed)

        res_layout.addWidget(lbl_res)
        res_layout.addWidget(self.combo_res)
        bottom_layout.addLayout(res_layout)

        main_layout.addLayout(bottom_layout)

        self._refresh_rom_ui()

    def _set_login_mode(self):
        self.is_register_mode = False
        self.btn_tab_login.setObjectName("TabButtonActive")
        self.btn_tab_register.setObjectName("TabButtonInactive")
        self.btn_tab_login.setStyle(self.btn_tab_login.style())
        self.btn_tab_register.setStyle(self.btn_tab_register.style())
        self.btn_play.setText("GIOCA")
        self.lbl_status.setText("")

    def _set_register_mode(self):
        self.is_register_mode = True
        self.btn_tab_login.setObjectName("TabButtonInactive")
        self.btn_tab_register.setObjectName("TabButtonActive")
        self.btn_tab_login.setStyle(self.btn_tab_login.style())
        self.btn_tab_register.setStyle(self.btn_tab_register.style())
        self.btn_play.setText("CREA & GIOCA")
        self.lbl_status.setText("")

    def _load_saved_preferences(self):
        last_user = self.rom_mgr.get_last_user()
        if last_user:
            self.txt_username.setText(last_user)
            self.txt_password.setFocus()
        else:
            self.txt_username.setFocus()

    def _refresh_rom_ui(self):
        is_ready = self.rom_mgr.is_rom_ready()
        if is_ready:
            rom_name = Path(self.rom_mgr.get_rom_path()).stem
            self.rom_badge.setObjectName("RomBadgeActive")
            self.lbl_rom_status.setText(f"✔ ROM: {rom_name} (Caricata)")
            self.lbl_rom_status.setStyleSheet("color: #10b981; font-weight: 700;")
            self.btn_rom_select.setText("Sfoglia...")
        else:
            self.rom_badge.setObjectName("RomBadgeMissing")
            self.lbl_rom_status.setText("⚠ ROM non configurata")
            self.lbl_rom_status.setStyleSheet("color: #ef4444; font-weight: 700;")
            self.btn_rom_select.setText("Carica ROM (.nds)")

        self.rom_badge.setStyle(self.rom_badge.style())

    def _select_rom_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona ROM di Pokémon Bianco 2",
            str(BASE_DIR),
            "Nintendo DS ROMs (*.nds)"
        )
        if file_path:
            if self.rom_mgr.set_rom_path(file_path):
                self._refresh_rom_ui()
                self.lbl_status.setText("")
            else:
                QMessageBox.warning(self, "ROM Non Valida", "Il file selezionato non è una ROM valida.")

    def _on_resolution_changed(self, text: str):
        self.rom_mgr.set_resolution(text.split()[0])

    def _on_play_clicked(self):
        if not self.rom_mgr.is_rom_ready():
            self.lbl_status.setText("Carica prima la ROM di gioco per iniziare.")
            return

        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()

        if not username or not password:
            self.lbl_status.setText("Inserisci sia nome utente che password.")
            return

        if self.is_register_mode:
            res = self.account_mgr.register(username, password)
        else:
            res = self.account_mgr.login(username, password)

        if not res.get("success"):
            self.lbl_status.setText(res.get("error", "Errore di autenticazione."))
            return

        # Salva ultimo utente se selezionato
        if self.chk_remember.isChecked():
            self.rom_mgr.set_last_user(username)

        self.lbl_status.setStyleSheet("color: #10b981; font-size: 13px; font-weight: 700;")
        self.lbl_status.setText("Accesso completato! Avvio in corso...")

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


def main():
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
