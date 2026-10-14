#!/usr/bin/env python3
"""
Interfaccia Grafica Professionale per il Box Pokémon Virtuale & Gestore Squadra.
Permette all'allenatore di:
1. Gestire il proprio deposito di Pokémon TCG fuori dal gioco e inviarli al salvataggio.
2. Visualizzare in tempo reale i 6 slot della Squadra Pokémon nel gioco.
3. Ritirare qualsiasi Pokémon o Uovo dalla Squadra indietro nel Box Virtuale.
4. Schiudere istantaneamente le Uova misteriose bloccate (es. l'uovo con 199 cicli!).
5. Aprire schede complete con grafici IV/EV, mosse e natura (come matrioska nel gioco).
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QScrollArea, QFrame,
    QMessageBox, QSplitter, QGridLayout, QInputDialog,
    QStackedWidget, QProgressBar
)
from PyQt6.QtGui import QPixmap, QIcon, QFont

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from launcher.ui_theme import STYLE_SHEET
from launcher.virtual_box_manager import VirtualBoxManager
from launcher.pokemon_profile_dialog import PokemonProfileDialog
from launcher.draggable_panel import DraggableInGamePanel

TYPE_COLORS = {
    "Normal": "#94a3b8", "Grass": "#22c55e", "Fire": "#ef4444", "Water": "#3b82f6",
    "Lightning": "#eab308", "Psychic": "#ec4899", "Fighting": "#ea580c", "Darkness": "#475569",
    "Metal": "#64748b", "Dragon": "#8b5cf6", "Fairy": "#f472b6", "Colorless": "#cbd5e1"
}


class PokemonCardWidget(QFrame):
    """Card visiva di un singolo Pokémon nel Box Virtuale."""
    clicked = pyqtSignal(dict)
    double_clicked = pyqtSignal(dict)
    transfer_requested = pyqtSignal(dict)

    def __init__(self, data: dict, mgr: VirtualBoxManager, parent=None):
        super().__init__(parent)
        self.data = data
        self.mgr = mgr
        self.setObjectName("InnerPanel")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Fai doppio clic per aprire la Scheda Completa con Statistiche e Lore")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        is_egg = self.data.get("is_egg", False)
        dex_id = self.data.get("dex_id", 0)
        is_gen_high = dex_id > 649

        # Header card: Dex ID / Badge + Status badge
        header = QHBoxLayout()
        if is_egg:
            dex_lbl = QLabel("🥚 UOVO")
            dex_lbl.setStyleSheet("color: #facc15; font-weight: 800; font-size: 11px;")
        else:
            dex_lbl = QLabel(f"#{dex_id:03d}")
            dex_lbl.setStyleSheet("color: #64748b; font-weight: 800; font-size: 11px;")
        
        status = self.data.get("status", "nel_box")
        if is_gen_high:
            status_lbl = QLabel("📁 GEN 6-9")
            status_lbl.setStyleSheet("background-color: #581c87; color: #e9d5ff; font-size: 10px; font-weight: 800; border-radius: 4px; padding: 2px 6px;")
        elif status == "inviato":
            status_lbl = QLabel("🚀 NEL GIOCO")
            status_lbl.setStyleSheet("background-color: #064e3b; color: #34d399; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 6px;")
        elif is_egg:
            status_lbl = QLabel("🥚 IN INCUBATRICE")
            status_lbl.setStyleSheet("background-color: #713f12; color: #fde047; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 6px;")
        else:
            status_lbl = QLabel("🟢 NEL BOX")
            status_lbl.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-size: 10px; font-weight: 700; border-radius: 4px; padding: 2px 6px;")

        header.addWidget(dex_lbl)
        header.addStretch()
        header.addWidget(status_lbl)
        layout.addLayout(header)

        # Immagine / Sprite del Pokémon
        self.sprite_lbl = QLabel()
        self.sprite_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sprite_lbl.setFixedHeight(80)
        self._load_sprite()
        layout.addWidget(self.sprite_lbl)

        # Nome e Livello
        name_str = self.data.get('species_name', 'Pokémon')
        name_lbl = QLabel(f"<b>{name_str}</b>")
        name_lbl.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: 700;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_lbl)

        if is_egg:
            sub_info = QLabel(f"Cicli: {self.data.get('hatch_cycles', 0)} • In Attesa")
            sub_info.setStyleSheet("color: #fde047; font-size: 11px; font-weight: 600;")
        else:
            sub_info = QLabel(f"Lv. {self.data.get('level', 20)} • {self.data.get('finish', '').upper()}")
            sub_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        sub_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub_info)

        # Badges Tipi
        types_layout = QHBoxLayout()
        types_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        types_layout.setSpacing(4)
        for t in self.data.get("types", [])[:2]:
            t_color = TYPE_COLORS.get(t, "#64748b")
            t_badge = QLabel(t.upper())
            t_badge.setStyleSheet(f"background-color: {t_color}; color: #ffffff; font-size: 9px; font-weight: 800; border-radius: 3px; padding: 1px 5px;")
            types_layout.addWidget(t_badge)
        layout.addLayout(types_layout)

        # Pulsante rapido "Invia al Gioco"
        self.btn_send = QPushButton("🚀 INVIA AL GIOCO")
        self.btn_send.setObjectName("SecondaryButton")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_gen_high:
            self.btn_send.setText("📁 RACCOGLITORE (GEN 6-9)")
            self.btn_send.setStyleSheet("background-color: #3b0764; color: #d8b4fe; font-size: 11px; font-weight: 800; border: 1px solid #9333ea; border-radius: 6px; padding: 6px;")
        elif status == "inviato":
            self.btn_send.setText("✔ GIÀ INVIATO")
            self.btn_send.setStyleSheet("background-color: #064e3b; color: #6ee7b7; font-size: 11px; font-weight: 700; border-radius: 6px; padding: 6px;")
        else:
            btn_text = "🚀 INVIA IN SQUADRA" if is_egg else "🚀 INVIA AL GIOCO"
            self.btn_send.setText(btn_text)
            self.btn_send.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e676, stop:1 #00b0ff); color: #041f0e; font-size: 11px; font-weight: 800; border-radius: 6px; padding: 6px;")
        
        self.btn_send.clicked.connect(lambda: self.transfer_requested.emit(self.data))
        layout.addWidget(self.btn_send)

    def _load_sprite(self):
        dex_id = self.data.get("dex_id", 0)
        is_egg = self.data.get("is_egg", False)
        sprite_path = self.mgr.get_sprite_path(dex_id, is_egg=is_egg)
        if sprite_path and sprite_path.exists():
            pix = QPixmap(str(sprite_path)).scaled(76, 76, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.sprite_lbl.setPixmap(pix)
        else:
            self.sprite_lbl.setText("🥚" if is_egg else "🐾")
            self.sprite_lbl.setStyleSheet("font-size: 32px; color: #475569;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.data)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.data)
        super().mouseDoubleClickEvent(event)


class PartySlotCard(QFrame):
    """Card visiva di uno slot nella Squadra In-Game (1..6)."""
    withdraw_requested = pyqtSignal(int)
    hatch_requested = pyqtSignal(int)
    details_requested = pyqtSignal(dict)
    switch_to_box_requested = pyqtSignal()

    def __init__(self, slot_idx: int, p_data: Optional[dict], mgr: VirtualBoxManager, parent=None):
        super().__init__(parent)
        self.slot_idx = slot_idx
        self.p_data = p_data
        self.mgr = mgr
        self.setObjectName("CardFrame")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header: Slot Number + Status
        header = QHBoxLayout()
        slot_lbl = QLabel(f"SLOT {self.slot_idx + 1} / 6")
        slot_lbl.setStyleSheet("color: #00e5ff; font-weight: 900; font-size: 11px; letter-spacing: 1px;")
        header.addWidget(slot_lbl)
        header.addStretch()

        if not self.p_data:
            # Slot Vuoto
            status_lbl = QLabel("⚪ LIBERO")
            status_lbl.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700;")
            header.addWidget(status_lbl)
            layout.addLayout(header)

            self.setStyleSheet("""
                QFrame#CardFrame {
                    border: 2px dashed #334155;
                    border-radius: 10px;
                    background-color: rgba(15, 23, 42, 0.4);
                }
            """)

            empty_box = QVBoxLayout()
            empty_box.setSpacing(8)
            empty_lbl = QLabel("➕ Slot Disponibile in Squadra")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 700;")

            hint_lbl = QLabel("Puoi inviare un Pokémon o un Uovo dal Box Virtuale a questo slot!")
            hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            hint_lbl.setWordWrap(True)

            btn_choose = QPushButton("📦 SCEGLI DAL BOX VIRTUALE")
            btn_choose.setObjectName("SecondaryButton")
            btn_choose.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_choose.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-weight: 700; border: 1px solid #0284c7; padding: 8px;")
            btn_choose.clicked.connect(self.switch_to_box_requested.emit)

            empty_box.addStretch()
            empty_box.addWidget(empty_lbl)
            empty_box.addWidget(hint_lbl)
            empty_box.addWidget(btn_choose)
            empty_box.addStretch()
            layout.addLayout(empty_box)
            return

        is_egg = bool(self.p_data.get("is_egg", False))
        if is_egg:
            status_lbl = QLabel("🥚 UOVO IN INCUBATORE")
            status_lbl.setStyleSheet("background-color: #713f12; color: #fde047; font-size: 10px; font-weight: 800; border-radius: 4px; padding: 2px 6px;")
        else:
            status_lbl = QLabel("🟢 ATTIVO IN GIOCO")
            status_lbl.setStyleSheet("background-color: #064e3b; color: #34d399; font-size: 10px; font-weight: 800; border-radius: 4px; padding: 2px 6px;")
        header.addWidget(status_lbl)
        layout.addLayout(header)

        # Sprite e Dati Principali
        main_info = QHBoxLayout()
        main_info.setSpacing(12)

        sprite_lbl = QLabel()
        sprite_lbl.setFixedSize(68, 68)
        sprite_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dex_id = self.p_data.get("dex_id") or self.p_data.get("species_id") or 0
        sprite_path = self.mgr.get_sprite_path(dex_id, is_egg=is_egg)
        if sprite_path and sprite_path.exists():
            pix = QPixmap(str(sprite_path)).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            sprite_lbl.setPixmap(pix)
        else:
            sprite_lbl.setText("🥚" if is_egg else "🐾")
            sprite_lbl.setStyleSheet("font-size: 28px;")
        main_info.addWidget(sprite_lbl)

        txt_info = QVBoxLayout()
        txt_info.setSpacing(2)

        if is_egg:
            name_lbl = QLabel(f"<b>UOVO POKÉMON</b>")
            name_lbl.setStyleSheet("color: #fde047; font-size: 15px; font-weight: 800;")
            sub_lbl = QLabel(f"Specie interna: <b>{self.p_data.get('species_name', 'Sconosciuto')}</b> (Lv. {self.p_data.get('level', 5)})")
            sub_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
            cycles = self.p_data.get("hatch_cycles", 0)
            steps = cycles * 256
            cycles_lbl = QLabel(f"🥚 Cicli: <b>{cycles}</b> (~{steps:,} passi rimanenti)")
            cycles_lbl.setStyleSheet("color: #fca5a5; font-size: 11px; font-weight: 700;")
            txt_info.addWidget(name_lbl)
            txt_info.addWidget(sub_lbl)
            txt_info.addWidget(cycles_lbl)
        else:
            name_lbl = QLabel(f"<b>{self.p_data.get('species_name', 'Pokémon')}</b>")
            name_lbl.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 800;")
            sub_lbl = QLabel(f"Livello <b>{self.p_data.get('level', 1)}</b> • {self.p_data.get('nature', 'Ardita')}")
            sub_lbl.setStyleSheet("color: #38bdf8; font-size: 11px;")
            ability_lbl = QLabel(f"Abilità: <i>{self.p_data.get('ability_name', '-')}</i>")
            ability_lbl.setStyleSheet("color: #94a3b8; font-size: 10px;")
            txt_info.addWidget(name_lbl)
            txt_info.addWidget(sub_lbl)
            txt_info.addWidget(ability_lbl)

        main_info.addLayout(txt_info)
        layout.addLayout(main_info)

        # Barra HP o Avviso Uovo
        if is_egg:
            alert_frame = QFrame()
            alert_frame.setStyleSheet("background-color: rgba(239, 68, 68, 0.12); border: 1px solid #ef4444; border-radius: 6px; padding: 4px;")
            al_layout = QVBoxLayout(alert_frame)
            al_layout.setContentsMargins(6, 4, 6, 4)
            al_txt = QLabel("⚠️ Quest'uovo richiede oltre 50.000 passi! Puoi schiuderlo subito con il pulsante verde:")
            al_txt.setStyleSheet("color: #fca5a5; font-size: 10px; font-weight: 600;")
            al_txt.setWordWrap(True)
            al_layout.addWidget(al_txt)
            layout.addWidget(alert_frame)
        else:
            curr_hp = self.p_data.get("current_hp", self.p_data.get("hp_cur", 10))
            max_hp = max(1, self.p_data.get("max_hp", self.p_data.get("hp_max", 10)))
            hp_ratio = curr_hp / max_hp
            hp_frame = QHBoxLayout()
            hp_txt = QLabel(f"PS: <b>{curr_hp} / {max_hp}</b>")
            hp_txt.setStyleSheet("color: #cbd5e1; font-size: 11px;")
            hp_bar = QProgressBar()
            hp_bar.setFixedHeight(8)
            hp_bar.setTextVisible(False)
            hp_bar.setRange(0, max_hp)
            hp_bar.setValue(curr_hp)
            if hp_ratio > 0.5:
                hp_bar.setStyleSheet("QProgressBar::chunk { background-color: #22c55e; border-radius: 3px; } QProgressBar { background: #1e293b; border-radius: 3px; }")
            elif hp_ratio > 0.2:
                hp_bar.setStyleSheet("QProgressBar::chunk { background-color: #eab308; border-radius: 3px; } QProgressBar { background: #1e293b; border-radius: 3px; }")
            else:
                hp_bar.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; border-radius: 3px; } QProgressBar { background: #1e293b; border-radius: 3px; }")
            hp_frame.addWidget(hp_txt)
            hp_frame.addWidget(hp_bar)
            layout.addLayout(hp_frame)

        # Azioni
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        if is_egg:
            btn_hatch = QPushButton("🐣 SCHIUDI ORA")
            btn_hatch.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_hatch.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #06b6d4);
                    color: #041f0e;
                    font-size: 11px;
                    font-weight: 800;
                    border-radius: 6px;
                    padding: 7px;
                }
                QPushButton:hover {
                    filter: brightness(1.15);
                }
            """)
            btn_hatch.clicked.connect(lambda: self.hatch_requested.emit(self.slot_idx))
            btn_layout.addWidget(btn_hatch)
        else:
            btn_details = QPushButton("📜 SCHEDA & IV/EV")
            btn_details.setObjectName("SecondaryButton")
            btn_details.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_details.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-size: 11px; font-weight: 700; border: 1px solid #0284c7; padding: 7px; border-radius: 6px;")
            btn_details.clicked.connect(self._emit_details)
            btn_layout.addWidget(btn_details)

        btn_withdraw = QPushButton("📥 RITIRA NEL BOX")
        btn_withdraw.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_withdraw.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.15);
                border: 1.5px solid #0284c7;
                color: #bae6fd;
                font-weight: 800;
                font-size: 11px;
                border-radius: 6px;
                padding: 7px;
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        btn_withdraw.clicked.connect(lambda: self.withdraw_requested.emit(self.slot_idx))
        btn_layout.addWidget(btn_withdraw)

        layout.addLayout(btn_layout)

    def _emit_details(self):
        if self.p_data:
            self.details_requested.emit(self.p_data)


class VirtualBoxDialog(DraggableInGamePanel):
    """Pannello interno sovrapposto (matrioska) del Box Pokémon Virtuale e Gestore Squadra."""
    def __init__(self, username: str, user_save_path: Optional[str] = None, parent=None, emu_thread=None):
        super().__init__(parent, header_height=64)
        self.username = username
        self.user_save_path = user_save_path
        self.emu_thread = emu_thread
        self.mgr = VirtualBoxManager(username)
        self.selected_item = None
        self.open_profile_windows = {}

        if parent:
            w = min(1120, max(800, parent.width() - 40))
            h = min(740, max(560, parent.height() - 60))
            x = max(10, (parent.width() - w) // 2)
            y = max(35, (parent.height() - h) // 2)
            self.setGeometry(x, y, w, h)
        else:
            self.resize(1120, 740)

        self.setStyleSheet(STYLE_SHEET)
        self._build_ui()
        self._refresh_list()

    def _pre_modify_save(self):
        """Assicura che la save RAM dell'emulatore melonDS venga riversata su file prima dell'iniezione."""
        if self.emu_thread and hasattr(self.emu_thread, "flush_save_to_disk"):
            try:
                self.emu_thread.flush_save_to_disk()
            except Exception as e:
                print(f"[VirtualBox] Errore pre-modify flush: {e}")

    def _post_modify_save(self):
        """Ricarica il salvataggio modificato al volo dentro la memoria RAM di melonDS attivo."""
        if self.emu_thread and hasattr(self.emu_thread, "reload_save_from_disk"):
            try:
                self.emu_thread.reload_save_from_disk()
            except Exception as e:
                print(f"[VirtualBox] Errore post-modify reload: {e}")

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # ----------------- HEADER & STATS -----------------
        header_frame = QFrame()
        header_frame.setObjectName("CardFrame")
        header_frame.setFixedHeight(64)
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(18, 6, 18, 6)

        title_box = QVBoxLayout()
        lbl_title = QLabel("📦 BOX VIRTUALE & GESTORE SQUADRA")
        lbl_title.setObjectName("HeaderLabel")
        lbl_title.setStyleSheet("font-size: 18px; color: #00e5ff;")
        
        lbl_sub = QLabel(f"Centro Pokémon Fuori Gioco • Profilo: <b>{self.username}</b>")
        lbl_sub.setStyleSheet("color: #94a3b8; font-size: 12px;")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        # Stat badges
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("font-size: 13px; color: #cbd5e1; font-weight: 600;")
        h_layout.addWidget(self.lbl_stats)

        # Pulsante Aggiungi Carta da Database
        btn_add = QPushButton("➕ Aggiungi Carta (Test)")
        btn_add.setObjectName("SecondaryButton")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._add_card_dialog)
        h_layout.addWidget(btn_add)

        # Pulsante Chiudi Box
        btn_close_box = QPushButton("✕ CHIUDI")
        btn_close_box.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close_box.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                border: 1.5px solid #ef4444;
                color: #fca5a5;
                font-weight: 800;
                font-size: 11px;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        btn_close_box.clicked.connect(self.close)
        h_layout.addWidget(btn_close_box)

        main_layout.addWidget(header_frame)

        # ----------------- NAVIGAZIONE A TAB (BOX vs SQUADRA) -----------------
        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)

        self.btn_tab_box = QPushButton("📦 BOX VIRTUALE (Deposito Esterno)")
        self.btn_tab_box.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_box.setFixedHeight(38)
        self.btn_tab_box.clicked.connect(lambda: self._switch_tab(0))

        self.btn_tab_party = QPushButton("👥 SQUADRA NEL GIOCO (6 Slot Attivi)")
        self.btn_tab_party.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_party.setFixedHeight(38)
        self.btn_tab_party.clicked.connect(lambda: self._switch_tab(1))

        nav_layout.addWidget(self.btn_tab_box, 1)
        nav_layout.addWidget(self.btn_tab_party, 1)
        main_layout.addWidget(nav_frame)

        # ----------------- STACKED WIDGET (PAGINE) -----------------
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)

        # PAGE 0: VISTA BOX VIRTUALE
        self._build_box_page()

        # PAGE 1: VISTA SQUADRA IN-GAME
        self._build_party_page()

        self._switch_tab(0)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btn_tab_box.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #06b6d4);
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 13px;
                    border: none;
                    border-radius: 8px;
                }
            """)
            self.btn_tab_party.setStyleSheet("""
                QPushButton {
                    background-color: #0f172a;
                    color: #94a3b8;
                    font-weight: 700;
                    font-size: 13px;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #1e293b;
                    color: #cbd5e1;
                }
            """)
            self._refresh_list()
        else:
            self.btn_tab_party.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #0284c7);
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 13px;
                    border: none;
                    border-radius: 8px;
                }
            """)
            self.btn_tab_box.setStyleSheet("""
                QPushButton {
                    background-color: #0f172a;
                    color: #94a3b8;
                    font-weight: 700;
                    font-size: 13px;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #1e293b;
                    color: #cbd5e1;
                }
            """)
            self._refresh_party_view()

    def _build_box_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)

        # Barra Filtri
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Cerca per nome (es. Lucario, Charizard, Oshawott)...")
        self.txt_search.textChanged.connect(self._refresh_list)
        filter_bar.addWidget(self.txt_search, 2)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Tutti gli Stati", "🟢 Nel Box (Disponibili)", "🚀 Già Inviati al Gioco"])
        self.combo_status.currentTextChanged.connect(self._refresh_list)
        filter_bar.addWidget(self.combo_status, 1)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["Tutti i Tipi"] + list(TYPE_COLORS.keys()))
        self.combo_type.currentTextChanged.connect(self._refresh_list)
        filter_bar.addWidget(self.combo_type, 1)

        page_layout.addLayout(filter_bar)

        # Splitter Griglia + Dettagli
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #1e293b; width: 3px; }")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 4, 12, 4)
        self.grid_layout.setSpacing(12)
        self.scroll_area.setWidget(self.grid_container)

        splitter.addWidget(self.scroll_area)

        # Destra: Pannello Dettaglio
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("CardFrame")
        self.detail_frame.setFixedWidth(360)
        self._build_detail_panel()
        splitter.addWidget(self.detail_frame)

        splitter.setSizes([720, 360])
        page_layout.addWidget(splitter, 1)

        self.stack.addWidget(page)

    def _build_detail_panel(self):
        d_layout = QVBoxLayout(self.detail_frame)
        d_layout.setContentsMargins(18, 18, 18, 18)
        d_layout.setSpacing(12)

        title = QLabel("SCHEDA POKÉMON")
        title.setObjectName("HeaderLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_layout.addWidget(title)

        self.d_sprite = QLabel()
        self.d_sprite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.d_sprite.setFixedHeight(120)
        d_layout.addWidget(self.d_sprite)

        self.d_name = QLabel("Seleziona un Pokémon")
        self.d_name.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")
        self.d_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_layout.addWidget(self.d_name)

        self.d_sub = QLabel("")
        self.d_sub.setStyleSheet("font-size: 13px; color: #00e5ff; font-weight: 600;")
        self.d_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_layout.addWidget(self.d_sub)

        # Info Box con statistiche
        self.d_info_box = QFrame()
        self.d_info_box.setObjectName("InnerPanel")
        info_layout = QVBoxLayout(self.d_info_box)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(6)

        self.d_set = QLabel("Set: -")
        self.d_rarity = QLabel("Rarità: -")
        self.d_hp = QLabel("Punti Salute (HP): -")
        self.d_ball = QLabel("Pokéball Assegnata: -")
        self.d_status = QLabel("Stato: -")

        for lbl in [self.d_set, self.d_rarity, self.d_hp, self.d_ball, self.d_status]:
            lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            info_layout.addWidget(lbl)

        d_layout.addWidget(self.d_info_box)
        d_layout.addStretch()

        # Pulsante Scheda Dettagli & Lore TCG
        self.d_btn_profile = QPushButton("📜 SCHEDA DETTAGLI & LORE TCG")
        self.d_btn_profile.setObjectName("SecondaryButton")
        self.d_btn_profile.setCursor(Qt.CursorShape.PointingHandCursor)
        self.d_btn_profile.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; font-weight: 800; font-size: 12px; "
            "border: 1.5px solid #0284c7; border-radius: 8px; padding: 10px;"
        )
        self.d_btn_profile.clicked.connect(self._open_profile_dialog)
        self.d_btn_profile.setEnabled(False)
        d_layout.addWidget(self.d_btn_profile)

        # Pulsantone Grande Trasferimento
        self.d_btn_transfer = QPushButton("🚀 INVIA AL GIOCO")
        self.d_btn_transfer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.d_btn_transfer.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e676, stop:1 #00c853);
                color: #041f0e;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.5px;
                border: none;
                border-radius: 8px;
                padding: 10px 14px;
                min-height: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #69f0ae, stop:1 #00e676);
            }
            QPushButton:pressed {
                background-color: #00b248;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
        """)
        self.d_btn_transfer.clicked.connect(self._transfer_selected)
        self.d_btn_transfer.setEnabled(False)
        d_layout.addWidget(self.d_btn_transfer)

        # Pulsante Elimina dal Box
        self.d_btn_delete = QPushButton("🗑 Rimuovi dal Box")
        self.d_btn_delete.setObjectName("SecondaryButton")
        self.d_btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.d_btn_delete.clicked.connect(self._delete_selected)
        self.d_btn_delete.setEnabled(False)
        d_layout.addWidget(self.d_btn_delete)

    def _build_party_page(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)

        # Barra superiore gestione squadra
        top_bar = QFrame()
        top_bar.setObjectName("InnerPanel")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(14, 8, 14, 8)

        lbl_party_info = QLabel("👥 <b>SQUADRA ATTIVA NEL GIOCO</b> • Fino a 6 Pokémon/Uova contemporaneamente")
        lbl_party_info.setStyleSheet("color: #e2e8f0; font-size: 13px;")
        top_layout.addWidget(lbl_party_info)
        top_layout.addStretch()

        self.btn_refresh_party = QPushButton("🔄 Ricarica dal Salvataggio")
        self.btn_refresh_party.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_party.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-weight: 700; border: 1px solid #0284c7; padding: 6px 14px; border-radius: 6px;")
        self.btn_refresh_party.clicked.connect(self._on_refresh_save_clicked)
        top_layout.addWidget(self.btn_refresh_party)

        page_layout.addWidget(top_bar)

        # Banner informativo per sincronizzazione con il gioco in-game
        info_banner = QFrame()
        info_banner.setStyleSheet("background-color: rgba(14, 165, 233, 0.08); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 6px; padding: 5px 12px;")
        ib_layout = QHBoxLayout(info_banner)
        ib_layout.setContentsMargins(8, 4, 8, 4)
        lbl_hint = QLabel("💡 <b>Hai preso o depositato Pokémon nel gioco?</b> Ricordati di <b>salvare la partita dal menu del gioco (X ➔ SALVA)</b> e poi clicca su <b>🔄 Ricarica dal Salvataggio</b>.")
        lbl_hint.setStyleSheet("color: #bae6fd; font-size: 11px;")
        lbl_hint.setWordWrap(True)
        ib_layout.addWidget(lbl_hint)
        page_layout.addWidget(info_banner)

        # Area scrollabile per i 6 slot
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        self.party_container = QWidget()
        self.party_grid = QGridLayout(self.party_container)
        self.party_grid.setContentsMargins(4, 4, 12, 4)
        self.party_grid.setSpacing(14)
        scroll.setWidget(self.party_container)

        page_layout.addWidget(scroll, 1)

        self.stack.addWidget(page)

    def _on_refresh_save_clicked(self):
        """Sincronizza attivamente la Save RAM di melonDS e ricarica squadra e box."""
        self._pre_modify_save()
        self._refresh_party_view()
        self._refresh_list()

        party = self.mgr.get_party(self.user_save_path)
        p_count = len(party)
        self.btn_refresh_party.setText(f"✔ Aggiornato! ({p_count}/6 in Squadra)")
        self.btn_refresh_party.setStyleSheet("background-color: #064e3b; color: #34d399; font-weight: 800; border: 1px solid #059669; padding: 6px 14px; border-radius: 6px;")
        QTimer.singleShot(2500, self._reset_refresh_party_button)

    def _reset_refresh_party_button(self):
        if hasattr(self, 'btn_refresh_party') and self.btn_refresh_party:
            self.btn_refresh_party.setText("🔄 Ricarica dal Salvataggio")
            self.btn_refresh_party.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-weight: 700; border: 1px solid #0284c7; padding: 6px 14px; border-radius: 6px;")

    def _refresh_party_view(self):
        """Carica i dati della squadra direttamente dal file di salvataggio attivo."""
        while self.party_grid.count():
            item = self.party_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        party = self.mgr.get_party(self.user_save_path)
        party_count = len(party)

        for slot_idx in range(6):
            p_data = party[slot_idx] if slot_idx < party_count else None
            card = PartySlotCard(slot_idx, p_data, self.mgr)
            card.withdraw_requested.connect(self._withdraw_from_party)
            card.hatch_requested.connect(self._hatch_egg)
            card.details_requested.connect(self._open_party_member_profile)
            card.switch_to_box_requested.connect(lambda: self._switch_tab(0))

            row = slot_idx // 3
            col = slot_idx % 3
            self.party_grid.addWidget(card, row, col)

    def _withdraw_from_party(self, slot_idx: int):
        self._pre_modify_save()
        party = self.mgr.get_party(self.user_save_path)
        if slot_idx >= len(party):
            return

        p = party[slot_idx]
        is_egg = p.get("is_egg", False)
        item_name = f"l'Uovo di {p.get('species_name')}" if is_egg else p.get("species_name")

        reply = QMessageBox.question(
            self,
            "Conferma Ritiro nel Box",
            f"Vuoi ritirare <b>{item_name}</b> dalla squadra di gioco e depositarlo nel tuo <b>Box Virtuale</b>?<br><br>"
            f"Lo slot nella squadra verrà liberato e i dati saranno salvati in sicurezza nel launcher.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        res = self.mgr.withdraw_from_party_to_box(slot_idx, target_save_path=self.user_save_path)
        self._post_modify_save()

        if res.get("success"):
            QMessageBox.information(
                self,
                "Ritiro Completato! 📥",
                f"✔ <b>{item_name}</b> è stato trasferito con successo nel Box Virtuale!<br><br>"
                f"I restanti Pokémon della squadra sono stati ricompattati e il salvataggio è aggiornato."
            )
            self._refresh_party_view()
            self._refresh_list()
        else:
            QMessageBox.critical(self, "Errore Ritiro", f"Impossibile ritirare il Pokémon:<br>{res.get('message', 'Errore sconosciuto')}")

    def _hatch_egg(self, slot_idx: int):
        self._pre_modify_save()
        party = self.mgr.get_party(self.user_save_path)
        if slot_idx >= len(party):
            return

        p = party[slot_idx]
        species_name = p.get("species_name", "Pokémon")

        reply = QMessageBox.question(
            self,
            "Conferma Schiusa Immediata",
            f"Vuoi schiudere istantaneamente quest'uovo nella tua squadra?<br><br>"
            f"Nascerà un autentico <b>{species_name}</b> (Lv. {p.get('level', 5)}) pronto a lottare!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        res = self.mgr.hatch_egg_in_party(slot_idx, target_save_path=self.user_save_path)
        self._post_modify_save()

        if res.get("success"):
            QMessageBox.information(
                self,
                "Uovo Schiuso con Successo! 🐣",
                f"✨ Complimenti! L'uovo si è schiuso in <b>{species_name}</b> (Lv. {p.get('level', 5)})!<br><br>"
                f"Ora è un membro attivo della tua squadra di Pokémon Bianco 2!"
            )
            self._refresh_party_view()
        else:
            QMessageBox.critical(self, "Errore Schiusa", f"Impossibile schiudere l'uovo:<br>{res.get('message', 'Errore sconosciuto')}")

    def _open_party_member_profile(self, p_data: dict):
        dex_id = p_data.get("dex_id") or p_data.get("species_id") or 0
        entry = {
            "id": f"party_view_{dex_id}_{p_data.get('level', 1)}",
            "card_id": f"in_game_{dex_id}",
            "dex_id": dex_id,
            "species_name": p_data.get("species_name", "Pokémon"),
            "nickname": p_data.get("nickname", p_data.get("species_name")),
            "level": p_data.get("level", 20),
            "finish": "squadra",
            "set_name": "Squadra Attiva nel Gioco",
            "card_number": str(dex_id),
            "release_year": 2012,
            "types": p_data.get("types", ["Normal"]),
            "hp": p_data.get("max_hp", p_data.get("hp_max", 50)),
            "rarity": "Squadra",
            "is_shiny": p_data.get("is_shiny", False),
            "is_egg": bool(p_data.get("is_egg", False)),
            "hatch_cycles": p_data.get("hatch_cycles", 0),
            "pokeball": p_data.get("ball_name", "Poké Ball"),
            "status": "inviato",
            "ivs": p_data.get("ivs"),
            "evs": p_data.get("evs"),
            "nature": p_data.get("nature"),
            "nature_id": p_data.get("nature_id"),
            "ability_name": p_data.get("ability_name"),
            "moves": p_data.get("moves"),
            "injected_target": "Squadra",
            "eval_cache": {
                "success": True,
                "species_id": dex_id,
                "species_name": p_data.get("species_name"),
                "level": p_data.get("level"),
                "is_shiny": p_data.get("is_shiny", False),
                "is_egg": bool(p_data.get("is_egg", False)),
                "hatch_cycles": p_data.get("hatch_cycles", 0),
                "ivs": p_data.get("ivs"),
                "moves": [m if isinstance(m, int) else m.get("move_id", 0) for m in p_data.get("moves", [])],
                "nature_id": p_data.get("nature_id"),
                "tier_name": "Veterano della Squadra",
                "era_name": "Unima In-Game",
                "pokeball_name": p_data.get("ball_name", "Poké Ball")
            }
        }
        self._open_profile_dialog(entry)

    def _refresh_list(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        search = self.txt_search.text().strip().lower()
        status_filter = self.combo_status.currentText()
        type_filter = self.combo_type.currentText()

        stats = self.mgr.get_stats()
        self.lbl_stats.setText(
            f"📦 Totale: <b>{stats['total']}</b> | "
            f"🟢 Nel Box: <b style='color:#38bdf8;'>{stats['in_box']}</b> | "
            f"🚀 Inviati: <b style='color:#34d399;'>{stats['sent']}</b>"
        )

        row, col = 0, 0
        COL_COUNT = 3

        filtered_items = []
        for it in self.mgr.items:
            # Filtro ricerca
            if search and search not in it.get("species_name", "").lower() and search not in str(it.get("dex_id", "")):
                continue
            # Filtro stato
            if "Nel Box" in status_filter and it.get("status") != "nel_box":
                continue
            if "Inviati" in status_filter and it.get("status") != "inviato":
                continue
            # Filtro tipo
            if type_filter != "Tutti i Tipi" and type_filter not in it.get("types", []):
                continue
            filtered_items.append(it)

        for it in filtered_items:
            card = PokemonCardWidget(it, self.mgr)
            card.clicked.connect(self._show_detail)
            card.double_clicked.connect(self._open_profile_dialog)
            card.transfer_requested.connect(self._on_card_transfer_requested)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= COL_COUNT:
                col = 0
                row += 1

        if filtered_items and not self.selected_item:
            self._show_detail(filtered_items[0])

    def _show_detail(self, data: dict):
        self.selected_item = data
        is_egg = data.get("is_egg", False)

        name_str = data.get("species_name", "Pokémon")
        self.d_name.setText(name_str)
        if is_egg:
            self.d_sub.setText(f"Uovo Pokémon • Cicli: {data.get('hatch_cycles', 0)}")
            self.d_rarity.setText("Rarità: <b>Speciale (Uovo)</b>")
            self.d_set.setText("Origine: <b>Incubatore Esterno</b>")
            self.d_hp.setText(f"Punti Salute: <b>{data.get('hp', 20)} HP</b>")
        else:
            self.d_sub.setText(f"Lv. {data.get('level', 20)} • {data.get('finish', '').upper()}")
            self.d_set.setText(f"Set: <b>{data.get('set_name', '')}</b> (#{data.get('card_number', '')})")
            self.d_rarity.setText(f"Rarità: <b>{data.get('rarity', 'Common')}</b> (Anno {data.get('release_year', 2020)})")
            self.d_hp.setText(f"Punti Salute: <b>{data.get('hp', 60)} HP</b>")

        self.d_ball.setText(f"Pokéball: <b>{data.get('pokeball', 'Poké Ball')}</b>")
        
        status = data.get("status", "nel_box")
        if status == "inviato":
            self.d_status.setText(f"Stato: <b style='color:#34d399;'>INVIATO</b> in <i>{data.get('injected_target')}</i>")
            self.d_btn_transfer.setText("✔ GIÀ INVIATO (RE-INVIA)")
        else:
            self.d_status.setText("Stato: <b style='color:#38bdf8;'>DISPONIBILE NEL BOX</b>")
            self.d_btn_transfer.setText("🚀 INVIA IN SQUADRA" if is_egg else "🚀 INVIA AL GIOCO")

        self.d_btn_transfer.setEnabled(True)
        self.d_btn_profile.setEnabled(True)
        self.d_btn_delete.setEnabled(True)

        sprite_path = self.mgr.get_sprite_path(data.get("dex_id", 0), is_egg=is_egg)
        if sprite_path and sprite_path.exists():
            pix = QPixmap(str(sprite_path)).scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.d_sprite.setPixmap(pix)
        else:
            self.d_sprite.setText("🥚" if is_egg else "🐾")

    def _open_profile_dialog(self, item=None):
        target_item = item if isinstance(item, dict) else self.selected_item
        if not target_item:
            return
        item_id = target_item["id"]
        if item_id in self.open_profile_windows:
            win = self.open_profile_windows[item_id]
            win.show()
            win.raise_()
            return

        parent_host = self.parentWidget() or self
        dlg = PokemonProfileDialog(target_item, self.mgr, user_save_path=self.user_save_path, parent=parent_host, emu_thread=self.emu_thread)
        new_x = min(self.x() + 30, max(0, parent_host.width() - dlg.width()))
        new_y = min(self.y() + 25, max(0, parent_host.height() - dlg.height()))
        dlg.move(new_x, new_y)

        self.open_profile_windows[item_id] = dlg
        dlg.closed.connect(lambda closed_id: self.open_profile_windows.pop(closed_id, None))
        dlg.transferred.connect(self._on_profile_transferred)
        dlg.show()
        dlg.raise_()

    def close(self):
        for win in list(self.open_profile_windows.values()):
            win.close()
        self.hide()
        return True

    def closeEvent(self, event):
        for win in list(self.open_profile_windows.values()):
            win.close()
        self.hide()
        event.accept()

    def _on_profile_transferred(self, item):
        self._refresh_list()
        self._refresh_party_view()
        if self.selected_item and self.selected_item.get("id") == item.get("id"):
            for it in self.mgr.items:
                if it["id"] == item["id"]:
                    self._show_detail(it)
                    break

    def _transfer_selected(self):
        if not self.selected_item:
            return
        self._on_card_transfer_requested(self.selected_item)

    def _on_card_transfer_requested(self, data: dict):
        pkm_name = data.get("species_name", "questo Pokémon")
        is_egg = data.get("is_egg", False)
        dex_id = data.get("dex_id", 0)

        # 1. Controllo Generazione 6-9
        if dex_id > 649:
            QMessageBox.information(
                self,
                "Pokémon di Generazione 6-9 📁",
                f"<b>{pkm_name}</b> (#{dex_id}) appartiene a una Generazione successiva alla 5ª.<br><br>"
                "La cartuccia originale di Pokémon Bianco 2 supporta fino a 649 specie (Gen 1-5).<br>"
                "I Pokémon di Gen 6-9 rimangono custoditi nel tuo <b>Raccoglitore Virtuale</b> e saranno trasferibili nel gioco non appena completeremo l'espansione della ROM (Strada A con SDSME)!"
            )
            return

        # 2. Controllo spazio in Squadra per messaggio esplicito
        party = self.mgr.get_party(self.user_save_path)
        party_count = len(party)

        if party_count < 6:
            prompt_txt = (
                f"Vuoi trasferire <b>{pkm_name}</b> direttamente nella tua <b>Squadra Pokémon</b>?<br><br>"
                f"📍 Destinazione esatta: <b>Squadra (Slot {party_count + 1}/6)</b>.<br>"
                f"Sarà subito visibile tra i tuoi 6 Pokémon attivi!"
            )
        else:
            prompt_txt = (
                f"La tua <b>Squadra è attualmente al completo (6/6 Pokémon)</b>.<br><br>"
                f"Vuoi depositare <b>{pkm_name}</b> nel computer del Centro Pokémon?<br>"
                f"📍 Destinazione esatta: <b>PC Box 1 (Deposito Pokémon)</b>.<br><br>"
                f"<i>Suggerimento: Se preferisci averlo in Squadra, puoi prima liberare uno slot ritirando un Pokémon dalla scheda 'Squadra nel Gioco'.</i>"
            )

        reply = QMessageBox.question(
            self,
            "Conferma Trasferimento",
            prompt_txt,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Sincronizza memoria live melonDS prima e dopo l'iniezione
        self._pre_modify_save()
        res = self.mgr.transfer_to_game(data["id"], target_save_path=self.user_save_path)
        self._post_modify_save()

        if res.get("success"):
            target_str = res.get("target", "Gioco")
            QMessageBox.information(
                self,
                "Trasferimento Riuscito! 🚀",
                f"✔ <b>{pkm_name}</b> è stato posizionato con successo in:<br>"
                f"<b>{target_str}</b>!<br><br>"
                f"I dati sono sincronizzati istantaneamente con il gioco!"
            )
            self._refresh_list()
            self._refresh_party_view()
            self._show_detail(data)
        else:
            QMessageBox.critical(self, "Errore Trasferimento", f"Impossibile trasferire il Pokémon:<br>{res.get('message')}")

    def _delete_selected(self):
        if not self.selected_item:
            return
        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            f"Sei sicuro di voler rimuovere <b>{self.selected_item.get('species_name')}</b> dal Box Virtuale?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.mgr.delete_item(self.selected_item["id"])
            self.selected_item = None
            self._refresh_list()

    def _add_card_dialog(self):
        query, ok = QInputDialog.getText(
            self,
            "Aggiungi Pokémon di Prova",
            "Inserisci il nome del Pokémon da cercare (es. Pikachu, Mewtwo, Gengar):"
        )
        if not ok or not query.strip():
            return

        results = self.mgr.tcg_core.search_cards(query.strip(), limit=5)
        if not results:
            QMessageBox.warning(self, "Non Trovato", f"Nessuna carta trovata per '{query}'.")
            return

        card_id = results[0]["card_id"]
        res = self.mgr.add_card(card_id, finish="normale")
        if res.get("success"):
            QMessageBox.information(
                self,
                "Carta Aggiunta!",
                f"✔ <b>{res['item']['species_name']}</b> (#{res['item']['dex_id']}) aggiunto al tuo Box Virtuale!"
            )
            self._refresh_list()
            self._show_detail(res["item"])
        else:
            QMessageBox.warning(self, "Attenzione", res.get("message", "Errore aggiunta."))
