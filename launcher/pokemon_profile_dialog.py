#!/usr/bin/env python3
"""
Finestra Grafica Avanzata — Profilo Completo Pokémon, Dati In-Game Gen 5 & Eredità TCG.
Riproduce al 100% tutti i parametri della schermata "Info Pokémon" di Pokémon Bianco 2:
- Statistiche di Lotta reali calcolate a livello corrente (formula ufficiale Nintendo)
- 4 Mosse con Tipo, Categoria (Fisico/Speciale/Stato), Potenza, Precisione, PP e Descrizione
- Natura (con bonus +10% e malus -10%), Caratteristica di personalità, Abilità completa
- Dati Allenatore Originale (AO), ID, Punti Esperienza, Note d'Incontro e Luogo
- Scheda Eredità TCG con Artwork HD, Era Storica, Titoli Onorari, Fiocchi e Tier di Rarità
- Supporto Multi-Finestra indipendente fluttuante (stile PokéMMO) e pulsanti di chiusura espliciti
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar, QMessageBox, QScrollArea,
    QTabWidget, QGridLayout, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QColor

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from launcher.ui_theme import STYLE_SHEET
from launcher.virtual_box_manager import VirtualBoxManager
from launcher.pokemon_game_data import PokemonGameDataManager, TYPE_INFO
from launcher.draggable_panel import DraggableInGamePanel

TYPE_COLORS = {
    "Normal": "#94a3b8", "Grass": "#22c55e", "Fire": "#ef4444", "Water": "#3b82f6",
    "Lightning": "#eab308", "Psychic": "#ec4899", "Fighting": "#ea580c", "Darkness": "#475569",
    "Metal": "#64748b", "Dragon": "#8b5cf6", "Fairy": "#f472b6", "Colorless": "#cbd5e1"
}


class PokemonProfileDialog(DraggableInGamePanel):
    """
    Pannello interno sovrapposto (matrioska) del Profilo Pokémon, Dati In-Game e TCG.
    Vive interamente dentro alla finestra del gioco/launcher (stile PokéMMO).
    """
    closed = pyqtSignal(str) # item_id
    transferred = pyqtSignal(dict)

    def __init__(self, item_data: dict, mgr: VirtualBoxManager, user_save_path: Optional[str] = None, parent=None, emu_thread=None):
        super().__init__(parent, header_height=58)
        self.item = mgr.ensure_full_eval_data(item_data)
        self.mgr = mgr
        self.user_save_path = user_save_path
        self.emu_thread = emu_thread
        self.game_data_mgr = PokemonGameDataManager()
        self.game_summary = self.game_data_mgr.get_game_summary(self.item, username=self.mgr.username)

        pkm_name = self.item.get("species_name", "Pokémon")
        lvl = self.item.get("level", 20)

        if parent:
            w = min(1040, max(750, parent.width() - 40))
            h = min(720, max(540, parent.height() - 60))
            self.resize(w, h)
        else:
            self.resize(1040, 720)

        self.setStyleSheet(STYLE_SHEET)
        self._build_ui()

    def _pre_modify_save(self):
        """Assicura che la RAM live dell'emulatore melonDS venga sincronizzata prima di modifiche/letture."""
        if self.emu_thread and hasattr(self.emu_thread, "flush_save_to_disk"):
            try:
                self.emu_thread.flush_save_to_disk()
            except Exception as e:
                print(f"[ProfileDialog] Errore pre-modify flush: {e}")

    def _post_modify_save(self):
        """Ricarica al volo il salvataggio modificato nella RAM dell'emulatore melonDS."""
        if self.emu_thread and hasattr(self.emu_thread, "reload_save_from_disk"):
            try:
                self.emu_thread.reload_save_from_disk()
            except Exception as e:
                print(f"[ProfileDialog] Errore post-modify reload: {e}")

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 12, 16, 14)
        root_layout.setSpacing(10)

        # ----------------- TOP HEADER BAR (CON PULSANTE CHIUSURA ESPLICITO) -----------------
        header_bar = QFrame()
        header_bar.setObjectName("CardFrame")
        header_bar.setFixedHeight(58)
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(14, 6, 14, 6)
        hb_layout.setSpacing(12)

        # Mini Sprite + Nome & Livello
        self.top_sprite = QLabel()
        self.top_sprite.setFixedSize(44, 44)
        self.top_sprite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_mini_sprite()
        hb_layout.addWidget(self.top_sprite)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        is_egg = self.item.get("is_egg", False)
        if is_egg:
            lbl_head_title = QLabel(f"<b>🥚 UOVO POKÉMON ({self.item.get('species_name', '').upper()})</b>")
            lbl_head_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #fde047;")
            cycles = self.item.get('hatch_cycles', 0)
            lbl_head_sub = QLabel(f"In Incubazione • <b>{cycles}</b> Cicli di schiusa (~{cycles * 256:,} passi)")
            lbl_head_sub.setStyleSheet("font-size: 11px; color: #fca5a5;")
        else:
            lbl_head_title = QLabel(f"<b>#{self.item.get('dex_id', 0):03d} {self.item.get('species_name', '').upper()}</b>")
            lbl_head_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
            lbl_head_sub = QLabel(f"Livello {self.item.get('level', 20)} {self.game_summary.get('gender_symbol', '')} • AO: <b style='color:#38bdf8;'>{self.game_summary.get('ot_name', '')}</b> (ID: {self.game_summary.get('tid', '')})")
            lbl_head_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_box.addWidget(lbl_head_title)
        title_box.addWidget(lbl_head_sub)
        hb_layout.addLayout(title_box)

        # Badges di stato / tipo
        hb_layout.addSpacing(10)
        for t in self.item.get("types", [])[:2]:
            t_col = TYPE_COLORS.get(t, "#64748b")
            t_badge = QLabel(t.upper())
            t_badge.setStyleSheet(f"background-color: {t_col}; color: #ffffff; font-size: 9px; font-weight: 800; border-radius: 4px; padding: 2px 8px;")
            hb_layout.addWidget(t_badge)

        if self.item.get("is_double_shiny"):
            d_badge = QLabel("🌌 DOUBLE SHINY")
            d_badge.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9333ea, stop:1 #ec4899); color: #ffffff; font-size: 9px; font-weight: 800; border-radius: 4px; padding: 2px 8px;")
            hb_layout.addWidget(d_badge)
        elif self.item.get("is_shiny"):
            s_badge = QLabel("⭐ SHINY")
            s_badge.setStyleSheet("background-color: #b45309; color: #fef08a; font-size: 9px; font-weight: 800; border-radius: 4px; padding: 2px 8px;")
            hb_layout.addWidget(s_badge)

        hb_layout.addStretch()

        # Pulsante di Chiusura Esplicito
        self.btn_header_close = QPushButton("✕ CHIUDI")
        self.btn_header_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_header_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                border: 1.5px solid #ef4444;
                color: #fca5a5;
                font-weight: 800;
                font-size: 12px;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.btn_header_close.clicked.connect(self.close)
        hb_layout.addWidget(self.btn_header_close)

        root_layout.addWidget(header_bar)

        # ----------------- CORPO CENTRALE A DUE COLONNE -----------------
        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)

        # =========================================================================
        # COLONNA SINISTRA (320px): Artwork Carta TCG HD & Azioni Rapide
        # =========================================================================
        left_frame = QFrame()
        left_frame.setObjectName("CardFrame")
        left_frame.setFixedWidth(320)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(8)

        card_title = QLabel("CARTA TCG ORIGINALE")
        card_title.setObjectName("HeaderLabel")
        card_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_title.setStyleSheet("color: #00e5ff; font-size: 11px; font-weight: 800; letter-spacing: 1px;")
        left_layout.addWidget(card_title)

        # Immagine Carta HD
        self.lbl_card_img = QLabel()
        self.lbl_card_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_card_img.setFixedHeight(290)
        self.lbl_card_img.setStyleSheet("background-color: #070d18; border-radius: 10px; border: 1px solid #1e293b;")
        self._load_card_image()
        left_layout.addWidget(self.lbl_card_img)

        # Info Rapide della Carta
        meta_frame = QFrame()
        meta_frame.setObjectName("InnerPanel")
        meta_layout = QVBoxLayout(meta_frame)
        meta_layout.setContentsMargins(10, 8, 10, 8)
        meta_layout.setSpacing(3)

        set_name = self.item.get("set_name", "Set Sconosciuto")
        card_num = self.item.get("card_number", "?")
        year = self.item.get("release_year", 2020)
        artist = self.item.get("artist") or "Illustratore Ufficiale"
        finish = self.item.get("finish", "Normale").upper()

        lbl_s = QLabel(f"📦 <b>Set:</b> {set_name} (#{card_num})")
        lbl_y = QLabel(f"📅 <b>Anno:</b> {year} • {finish}")
        lbl_a = QLabel(f"🎨 <b>Artista:</b> {artist}")
        for l in [lbl_s, lbl_y, lbl_a]:
            l.setStyleSheet("color: #cbd5e1; font-size: 11px;")
            meta_layout.addWidget(l)

        left_layout.addWidget(meta_frame)
        left_layout.addStretch()

        # Box Stato & Pulsante Trasferisci
        self.status_box = QFrame()
        self.status_box.setObjectName("InnerPanel")
        sb_layout = QVBoxLayout(self.status_box)
        sb_layout.setContentsMargins(10, 8, 10, 8)
        sb_layout.setSpacing(6)

        status = self.item.get("status", "nel_box")
        if status == "inviato":
            self.lbl_status = QLabel(f"🚀 <b>NEL GIOCO</b> ({self.item.get('injected_target')})")
            self.lbl_status.setStyleSheet("color: #34d399; font-size: 11px; font-weight: 700;")
        else:
            self.lbl_status = QLabel("🟢 <b>NEL BOX VIRTUALE</b>")
            self.lbl_status.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 700;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(self.lbl_status)

        self.btn_transfer = QPushButton("🚀 INVIA AL GIOCO")
        self.btn_transfer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_transfer.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e676, stop:1 #00c853);
                color: #041f0e;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.5px;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                min-height: 38px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #69f0ae, stop:1 #00e676);
            }
            QPushButton:pressed {
                background-color: #00b248;
            }
        """)
        if status == "inviato":
            self.btn_transfer.setText("✔ RE-INVIA COPIA")
        self.btn_transfer.clicked.connect(self._transfer_to_game)
        sb_layout.addWidget(self.btn_transfer)

        # Pulsante Chiudi Inferiore
        btn_bot_close = QPushButton("✕ Chiudi Scheda")
        btn_bot_close.setObjectName("SecondaryButton")
        btn_bot_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_bot_close.clicked.connect(self.close)
        sb_layout.addWidget(btn_bot_close)

        left_layout.addWidget(self.status_box)
        body_layout.addWidget(left_frame)

        # =========================================================================
        # COLONNA DESTRA: Tab Widget (1: Dati In-Game Gen 5 | 2: Eredità TCG & Lore)
        # =========================================================================
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1e293b;
                border-radius: 12px;
                background-color: rgba(19, 27, 46, 0.85);
            }
            QTabBar::tab {
                background-color: #0d1424;
                color: #94a3b8;
                font-weight: 700;
                font-size: 12px;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1e293b;
                color: #00e5ff;
                border-bottom: 2px solid #00e5ff;
            }
            QTabBar::tab:hover:!selected {
                color: #f1f5f9;
                background-color: #131b2e;
            }
        """)

        # Tab 1: ⚔️ Dati In-Game (Info Pokémon)
        tab_game = QWidget()
        self._build_tab_in_game(tab_game)
        self.tabs.addTab(tab_game, "⚔️ Dati di Lotta & In-Gioco (Info Pokémon)")

        # Tab 2: 🃏 Eredità TCG & Lore Temporale
        tab_tcg = QWidget()
        self._build_tab_tcg_lore(tab_tcg)
        self.tabs.addTab(tab_tcg, "🃏 Eredità TCG, Rarità & Lore Temporale")

        body_layout.addWidget(self.tabs, 1)
        root_layout.addLayout(body_layout, 1)

    # -------------------------------------------------------------------------
    # TAB 1: DATI IN-GAME GEN 5 (IDENTICO AD "INFO POKÉMON" DI B2W2)
    # -------------------------------------------------------------------------
    def _build_tab_in_game(self, container: QWidget):
        scroll = QScrollArea(container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        c_widget = QWidget()
        layout = QVBoxLayout(c_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        scroll.setWidget(c_widget)

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        # --- SEZIONE 1: IDENTITÀ & CRESCITA ---
        id_frame = QFrame()
        id_frame.setObjectName("InnerPanel")
        idf_layout = QVBoxLayout(id_frame)
        idf_layout.setContentsMargins(14, 10, 14, 10)
        idf_layout.setSpacing(8)

        id_head = QLabel("📋 DATI ALLENATORE & CRESCITA ESPERIENZA")
        id_head.setObjectName("HeaderLabel")
        id_head.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 800;")
        idf_layout.addWidget(id_head)

        id_grid = QGridLayout()
        id_grid.setHorizontalSpacing(16)
        id_grid.setVerticalSpacing(4)

        id_grid.addWidget(QLabel("<b>Allenatore Originale (AO):</b>"), 0, 0)
        id_grid.addWidget(QLabel(f"<span style='color:#ffffff;'>{self.game_summary['ot_name']}</span>"), 0, 1)

        id_grid.addWidget(QLabel("<b>ID Allenatore:</b>"), 0, 2)
        id_grid.addWidget(QLabel(f"<span style='color:#ffffff;'>{self.game_summary['tid']}</span>"), 0, 3)

        id_grid.addWidget(QLabel("<b>Strumento Tenuto:</b>"), 1, 0)
        id_grid.addWidget(QLabel(f"<span style='color:#94a3b8;'>{self.game_summary['held_item']}</span>"), 1, 1)

        id_grid.addWidget(QLabel("<b>Gruppo Esperienza:</b>"), 1, 2)
        id_grid.addWidget(QLabel(f"<span style='color:#cbd5e1;'>{self.game_summary['growth_rate_name']}</span>"), 1, 3)

        idf_layout.addLayout(id_grid)

        # Barra Esperienza
        exp_row = QHBoxLayout()
        exp_lbl = QLabel(f"Exp. Attuale: <b>{self.game_summary['current_exp']}</b> • Punti per il prossimo livello: <b style='color:#00e5ff;'>{self.game_summary['exp_to_next']}</b>")
        exp_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        exp_row.addWidget(exp_lbl)
        idf_layout.addLayout(exp_row)
        layout.addWidget(id_frame)

        # --- SEZIONE 2: NATURA, CARATTERISTICA & ABILITÀ ---
        nat_frame = QFrame()
        nat_frame.setObjectName("InnerPanel")
        nf_layout = QVBoxLayout(nat_frame)
        nf_layout.setContentsMargins(14, 10, 14, 10)
        nf_layout.setSpacing(8)

        nat_head = QLabel("🧠 NATURA, CARATTERE & ABILITÀ")
        nat_head.setObjectName("HeaderLabel")
        nat_head.setStyleSheet("color: #facc15; font-size: 12px; font-weight: 800;")
        nf_layout.addWidget(nat_head)

        # Natura & Modificatori
        nat_str = f"Natura <b>{self.game_summary['nature_name']}</b>"
        if self.game_summary['nature_boosted']:
            nat_str += f" (<span style='color:#22c55e;'>+{self.game_summary['nature_boosted']}</span>, <span style='color:#ef4444;'>-{self.game_summary['nature_hindered']}</span>)"
        else:
            nat_str += " (<i>Neutra</i>)"

        lbl_nat = QLabel(f"• <b>Natura:</b> {nat_str}<br>• <b>Caratteristica:</b> <span style='color:#ffffff;'>\"{self.game_summary['characteristic']}.\"</span>")
        lbl_nat.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        nf_layout.addWidget(lbl_nat)

        # Abilità Box
        ab = self.game_summary["ability"]
        ha_tag = " <span style='background-color:#9333ea; color:#ffffff; font-size:9px; font-weight:800; border-radius:3px; padding:1px 5px;'>SPECIAL / ABILITÀ NASCOSTA</span>" if ab.get("is_hidden") else ""
        lbl_ab = QLabel(f"• <b>Abilità:</b> <b style='color:#00e5ff; font-size:13px;'>{ab['name']}</b>{ha_tag}<br><i style='color:#94a3b8;'>\"{ab['desc']}\"</i>")
        lbl_ab.setStyleSheet("font-size: 12px;")
        lbl_ab.setWordWrap(True)
        nf_layout.addWidget(lbl_ab)
        layout.addWidget(nat_frame)

        # --- SEZIONE 3: STATISTICHE REALI DI LOTTA GEN 5 ---
        stat_frame = QFrame()
        stat_frame.setObjectName("InnerPanel")
        sf_layout = QVBoxLayout(stat_frame)
        sf_layout.setContentsMargins(14, 10, 14, 10)
        sf_layout.setSpacing(8)

        stat_head = QLabel("📊 STATISTICHE DI LOTTA EFFETTIVE (FORMULA UFFICIALE DI GEN 5)")
        stat_head.setObjectName("HeaderLabel")
        stat_head.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 800;")
        sf_layout.addWidget(stat_head)

        stats_dict = self.game_summary["battle_stats"]
        stat_order = [
            ("hp", "#ef4444"),
            ("atk", "#f97316"),
            ("def", "#eab308"),
            ("spa", "#3b82f6"),
            ("spd", "#10b981"),
            ("spe", "#a855f7")
        ]

        for s_key, s_col in stat_order:
            s_data = stats_dict[s_key]

            row_frame = QFrame()
            row_frame.setStyleSheet("background-color: #0b1220; border: 1px solid #1e293b; border-radius: 8px;")
            rf_layout = QVBoxLayout(row_frame)
            rf_layout.setContentsMargins(10, 6, 10, 6)
            rf_layout.setSpacing(4)

            # Riga Superiore: Nome stat, Base Stat e Valore Reale Calcolato
            top_h = QHBoxLayout()
            top_h.setSpacing(8)
            lbl_stat_name = QLabel(f"<b style='color:{s_col}; font-size:13px;'>●</b> <b>{s_data['label']}</b> <span style='color:#64748b; font-size:11px;'>(Base: {s_data['base']})</span>")
            top_h.addWidget(lbl_stat_name)
            top_h.addStretch()

            if s_key == "hp":
                val_text = f"<b style='font-size:14px; color:#ffffff;'>PS {s_data['current']}</b><span style='color:#64748b; font-size:11px;'> / {s_data['max']}</span>"
            else:
                nat_sym = s_data.get("nature", "")
                nat_color = "#22c55e" if nat_sym == "+" else ("#ef4444" if nat_sym == "-" else "#ffffff")
                val_text = f"<b style='font-size:14px; color:{nat_color};'>{s_data['val']}</b> <b style='color:{nat_color}; font-size:12px;'>{nat_sym}</b>"
            lbl_val = QLabel(val_text)
            top_h.addWidget(lbl_val)
            rf_layout.addLayout(top_h)

            # Riga Barre Grafiche: Barra IV + Barra EV affiancate
            bars_layout = QHBoxLayout()
            bars_layout.setSpacing(14)

            # 1. Barra Grafica IV (0-31)
            iv_box = QHBoxLayout()
            iv_box.setSpacing(6)
            lbl_iv_tag = QLabel("<b>IV:</b>")
            lbl_iv_tag.setStyleSheet("color: #94a3b8; font-size: 10px;")
            iv_box.addWidget(lbl_iv_tag)

            bar_iv = QProgressBar()
            bar_iv.setRange(0, 31)
            bar_iv.setValue(s_data["iv"])
            bar_iv.setTextVisible(False)
            bar_iv.setFixedHeight(8)
            if s_data["iv"] == 31:
                bar_iv.setStyleSheet("QProgressBar { background-color: #0f172a; border-radius: 4px; } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffd700, stop:1 #fbbf24); border-radius: 4px; }")
            else:
                bar_iv.setStyleSheet(f"QProgressBar {{ background-color: #0f172a; border-radius: 4px; }} QProgressBar::chunk {{ background-color: {s_col}; border-radius: 4px; }}")
            iv_box.addWidget(bar_iv, 1)

            iv_val_lbl = QLabel("<b style='color:#ffd700;'>31 ★ MAX</b>" if s_data["iv"] == 31 else f"<b>{s_data['iv']}</b>/31")
            iv_val_lbl.setStyleSheet("font-size: 10px; color: #cbd5e1;")
            iv_val_lbl.setFixedWidth(56)
            iv_val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            iv_box.addWidget(iv_val_lbl)
            bars_layout.addLayout(iv_box, 1)

            # 2. Barra Grafica EV (0-252)
            ev_box = QHBoxLayout()
            ev_box.setSpacing(6)
            lbl_ev_tag = QLabel("<b>EV:</b>")
            lbl_ev_tag.setStyleSheet("color: #64748b; font-size: 10px;")
            ev_box.addWidget(lbl_ev_tag)

            bar_ev = QProgressBar()
            bar_ev.setRange(0, 252)
            bar_ev.setValue(s_data["ev"])
            bar_ev.setTextVisible(False)
            bar_ev.setFixedHeight(8)
            bar_ev.setStyleSheet("QProgressBar { background-color: #0f172a; border-radius: 4px; } QProgressBar::chunk { background-color: #06b6d4; border-radius: 4px; }")
            ev_box.addWidget(bar_ev, 1)

            ev_val_lbl = QLabel(f"<b>{s_data['ev']}</b>/252")
            ev_val_lbl.setStyleSheet("font-size: 10px; color: #64748b;")
            ev_val_lbl.setFixedWidth(46)
            ev_val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            ev_box.addWidget(ev_val_lbl)
            bars_layout.addLayout(ev_box, 1)

            rf_layout.addLayout(bars_layout)
            sf_layout.addWidget(row_frame)

        layout.addWidget(stat_frame)

        # --- SEZIONE 4: MOSSE CONOSCIUTE (MOVESET) ---
        moves_frame = QFrame()
        moves_frame.setObjectName("InnerPanel")
        mf_layout = QVBoxLayout(moves_frame)
        mf_layout.setContentsMargins(14, 10, 14, 10)
        mf_layout.setSpacing(8)

        moves_head = QLabel("⚔️ MOSSE CONOSCIUTE")
        moves_head.setObjectName("HeaderLabel")
        moves_head.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 800;")
        mf_layout.addWidget(moves_head)

        moves_grid = QGridLayout()
        moves_grid.setHorizontalSpacing(10)
        moves_grid.setVerticalSpacing(10)

        moves = self.game_summary.get("moves", [])
        for idx, m in enumerate(moves[:4]):
            m_card = QFrame()
            m_card.setStyleSheet("background-color: #0b1220; border: 1px solid #1e293b; border-radius: 8px; padding: 6px;")
            mc_layout = QVBoxLayout(m_card)
            mc_layout.setContentsMargins(8, 6, 8, 6)
            mc_layout.setSpacing(3)

            # Header mossa
            m_top = QHBoxLayout()
            m_name_lbl = QLabel(f"<b>{m['name']}</b>")
            m_name_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 800;")
            m_top.addWidget(m_name_lbl)
            m_top.addStretch()

            # Tipo
            m_type_lbl = QLabel(m['type_name'].upper())
            m_type_lbl.setStyleSheet(f"background-color: {m['type_color']}; color: #ffffff; font-size: 9px; font-weight: 800; border-radius: 3px; padding: 1px 5px;")
            m_top.addWidget(m_type_lbl)

            # Categoria
            m_cat_lbl = QLabel(f"{m['category_icon']} {m['category']}")
            m_cat_lbl.setStyleSheet(f"background-color: #1e293b; color: {m['category_color']}; font-size: 9px; font-weight: 800; border-radius: 3px; padding: 1px 5px;")
            m_top.addWidget(m_cat_lbl)
            mc_layout.addLayout(m_top)

            # Parametri
            m_stats_lbl = QLabel(f"Potenza: <b>{m['power']}</b> • Precisione: <b>{m['accuracy']}</b> • PP: <b style='color:#38bdf8;'>{m['pp']}</b>")
            m_stats_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
            mc_layout.addWidget(m_stats_lbl)

            # Descrizione
            m_desc_lbl = QLabel(f"<i style='color:#94a3b8;'>{m['desc']}</i>")
            m_desc_lbl.setStyleSheet("font-size: 10px;")
            m_desc_lbl.setWordWrap(True)
            mc_layout.addWidget(m_desc_lbl)

            row = idx // 2
            col = idx % 2
            moves_grid.addWidget(m_card, row, col)

        mf_layout.addLayout(moves_grid)
        layout.addWidget(moves_frame)

        # --- SEZIONE 5: NOTE D'INCONTRO & MEMORIE ---
        enc_frame = QFrame()
        enc_frame.setObjectName("InnerPanel")
        ef_layout = QVBoxLayout(enc_frame)
        ef_layout.setContentsMargins(14, 10, 14, 10)
        ef_layout.setSpacing(4)

        enc_head = QLabel("📍 NOTE D'INCONTRO & PROVENIENZA")
        enc_head.setObjectName("HeaderLabel")
        enc_head.setStyleSheet("color: #a855f7; font-size: 12px; font-weight: 800;")
        ef_layout.addWidget(enc_head)

        lbl_enc = QLabel(
            f"• <b>Data di arrivo:</b> {self.game_summary['met_date']}<br>"
            f"• <b>Luogo d'incontro:</b> <span style='color:#38bdf8;'>{self.game_summary['met_location']}</span> (al Liv. {self.game_summary['met_level']})<br>"
            f"• <b>Sfera cattura:</b> {self.game_summary['pokeball']}<br>"
            f"• <b>Nota di memoria:</b> <i>\"Sembra un incontro predestinato tramite Risonanza TCG.\"</i>"
        )
        lbl_enc.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        ef_layout.addWidget(lbl_enc)
        layout.addWidget(enc_frame)

    # -------------------------------------------------------------------------
    # TAB 2: EREDITÀ TCG, RARITÀ & LORE TEMPORALE
    # -------------------------------------------------------------------------
    def _build_tab_tcg_lore(self, container: QWidget):
        scroll = QScrollArea(container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        c_widget = QWidget()
        layout = QVBoxLayout(c_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        scroll.setWidget(c_widget)

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        # --- 1. EREDITÀ TEMPORALE DELL'ERA ---
        era_frame = QFrame()
        era_frame.setObjectName("InnerPanel")
        era_layout = QVBoxLayout(era_frame)
        era_layout.setContentsMargins(16, 12, 16, 12)
        era_layout.setSpacing(8)

        era_head = QHBoxLayout()
        era_head_lbl = QLabel("🏛️ EREDITÀ TEMPORALE DELL'ERA STORICA")
        era_head_lbl.setObjectName("HeaderLabel")
        era_head_lbl.setStyleSheet("color: #ffd700; font-size: 13px; font-weight: 800;")
        era_head.addWidget(era_head_lbl)
        era_head.addStretch()

        title_badge = QLabel(f"👑 {self.item.get('title') or 'Il Viaggiatore'}")
        title_badge.setStyleSheet("background-color: rgba(234, 179, 8, 0.15); border: 1px solid #eab308; color: #fde047; font-size: 12px; font-weight: 800; border-radius: 6px; padding: 3px 10px;")
        era_head.addWidget(title_badge)
        era_layout.addLayout(era_head)

        era_grid = QHBoxLayout()
        era_grid.setSpacing(12)

        # Sfera
        box_ball = QFrame()
        box_ball.setStyleSheet("background-color: #0b1220; border: 1px solid #1e293b; border-radius: 8px; padding: 8px;")
        b_layout = QVBoxLayout(box_ball)
        b_layout.setContentsMargins(6, 4, 6, 4)
        b_lbl1 = QLabel("SFERA ASSEGNATA")
        b_lbl1.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 700;")
        b_lbl2 = QLabel(f"🔴 <b>{self.item.get('pokeball', 'Poké Ball')}</b>")
        b_lbl2.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 700;")
        b_layout.addWidget(b_lbl1)
        b_layout.addWidget(b_lbl2)
        era_grid.addWidget(box_ball)

        # Fiocco
        box_rib = QFrame()
        box_rib.setStyleSheet("background-color: #0b1220; border: 1px solid #1e293b; border-radius: 8px; padding: 8px;")
        r_layout = QVBoxLayout(box_rib)
        r_layout.setContentsMargins(6, 4, 6, 4)
        r_lbl1 = QLabel("MEDAGLIA / FIOCCO ONORARIO")
        r_lbl1.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: 700;")
        r_lbl2 = QLabel(f"🏅 <b>{self.item.get('ribbon') or 'Nessun Fiocco Epocale'}</b>")
        r_lbl2.setStyleSheet("color: #fde047; font-size: 13px; font-weight: 700;")
        r_layout.addWidget(r_lbl1)
        r_layout.addWidget(r_lbl2)
        era_grid.addWidget(box_rib)

        era_layout.addLayout(era_grid)

        # Particelle
        era_desc = QLabel(
            f"• <b>Periodo Storico:</b> {self.item.get('era_name', 'Era Contemporanea')}<br>"
            f"• <b>Effetto Particellare:</b> <span style='color:#38bdf8;'>{self.item.get('particles', 'Standard')}</span>"
        )
        era_desc.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        era_layout.addWidget(era_desc)
        layout.addWidget(era_frame)

        # --- 2. GERARCHIA DI RARITÀ TCG ---
        tier_frame = QFrame()
        tier_frame.setObjectName("InnerPanel")
        tier_layout = QVBoxLayout(tier_frame)
        tier_layout.setContentsMargins(16, 12, 16, 12)
        tier_layout.setSpacing(8)

        tier_head = QHBoxLayout()
        tier_head_lbl = QLabel("⚡ GERARCHIA DI RARITÀ TCG")
        tier_head_lbl.setObjectName("HeaderLabel")
        tier_head_lbl.setStyleSheet("color: #00e5ff; font-size: 13px; font-weight: 800;")
        tier_head.addWidget(tier_head_lbl)
        tier_head.addStretch()

        tier_badge = QLabel(f"💎 {self.item.get('tier_name', 'Standard')}")
        tier_badge.setStyleSheet("background-color: rgba(0, 229, 255, 0.15); border: 1px solid #00e5ff; color: #38bdf8; font-size: 11px; font-weight: 800; border-radius: 6px; padding: 3px 10px;")
        tier_head.addWidget(tier_badge)
        tier_layout.addLayout(tier_head)

        tier_info = QLabel(
            f"• <b>Finitura Rilevata:</b> {self.item.get('finish', '').upper()}<br>"
            f"• <b>Scala Livello:</b> Livello {self.item.get('level', 20)} calcolato sulla rarità del set.<br>"
            f"• <b>Abilità Nascosta:</b> Sbloccata in base al prestigio della carta nel binder."
        )
        tier_info.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        tier_layout.addWidget(tier_info)
        layout.addWidget(tier_frame)

        # --- 3. BARRE GRAFICHE IV (0-31) ---
        iv_frame = QFrame()
        iv_frame.setObjectName("InnerPanel")
        iv_layout = QVBoxLayout(iv_frame)
        iv_layout.setContentsMargins(16, 12, 16, 12)
        iv_layout.setSpacing(8)

        iv_head = QLabel("📊 VALORI INDIVIDUALI (IV DI GEN 5)")
        iv_head.setObjectName("HeaderLabel")
        iv_head.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 800;")
        iv_layout.addWidget(iv_head)

        ivs = self.item.get("ivs") or {"hp": 15, "atk": 15, "def": 15, "spa": 15, "spd": 15, "spe": 15}
        iv_names = [
            ("Punti Salute (PS)", ivs.get("hp", 15), "#ef4444"),
            ("Attacco", ivs.get("atk", 15), "#f97316"),
            ("Difesa", ivs.get("def", 15), "#eab308"),
            ("Attacco Sp.", ivs.get("spa", 15), "#3b82f6"),
            ("Difesa Sp.", ivs.get("spd", 15), "#10b981"),
            ("Velocità", ivs.get("spe", 15), "#a855f7"),
        ]

        for label_text, val, color in iv_names:
            iv_row = QHBoxLayout()
            iv_row.setSpacing(10)

            lbl_n = QLabel(label_text)
            lbl_n.setFixedWidth(130)
            lbl_n.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
            iv_row.addWidget(lbl_n)

            bar = QProgressBar()
            bar.setRange(0, 31)
            bar.setValue(val)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            if val == 31:
                bar.setStyleSheet("QProgressBar { background-color: #0f172a; border-radius: 5px; } QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffd700, stop:1 #fbbf24); border-radius: 5px; }")
            else:
                bar.setStyleSheet(f"QProgressBar {{ background-color: #0f172a; border-radius: 5px; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 5px; }}")
            iv_row.addWidget(bar)

            if val == 31:
                lbl_val = QLabel("31 ★ MAX")
                lbl_val.setStyleSheet("color: #ffd700; font-weight: 900; font-size: 11px;")
            else:
                lbl_val = QLabel(f"{val}/31")
                lbl_val.setStyleSheet("color: #cbd5e1; font-weight: 700; font-size: 11px;")
            lbl_val.setFixedWidth(65)
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight)
            iv_row.addWidget(lbl_val)

            iv_layout.addLayout(iv_row)

        layout.addWidget(iv_frame)

    # -------------------------------------------------------------------------
    # HELPERS CARICAMENTO IMMAGINI & SPRITE
    # -------------------------------------------------------------------------
    def _load_card_image(self):
        card_id = self.item.get("card_id")
        dex_id = self.item.get("dex_id") or self.item.get("species_id") or 0
        img_path = self.mgr.get_card_image_path(card_id, dex_id=dex_id)
        if img_path and img_path.exists():
            pix = QPixmap(str(img_path)).scaled(270, 285, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_card_img.setPixmap(pix)
        else:
            self.lbl_card_img.setText("🃏\nArtwork Carta TCG")
            self.lbl_card_img.setStyleSheet("color: #475569; font-size: 14px; font-weight: 700;")

    def _load_mini_sprite(self):
        dex_id = self.item.get("dex_id", 0)
        is_egg = self.item.get("is_egg", False)
        sprite_path = self.mgr.get_sprite_path(dex_id, is_egg=is_egg)
        if sprite_path and sprite_path.exists():
            pix = QPixmap(str(sprite_path)).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.top_sprite.setPixmap(pix)
        else:
            self.top_sprite.setText("🥚" if is_egg else "🐾")

    def _transfer_to_game(self):
        pkm_name = self.item.get("species_name", "questo Pokémon")
        reply = QMessageBox.question(
            self,
            "Conferma Trasferimento nel Gioco",
            f"Vuoi trasferire <b>{pkm_name}</b> (Lv.{self.item.get('level')}) direttamente nella tua partita di Pokémon Bianco 2?<br><br>"
            f"Verrà posizionato nel primo slot libero (in <b>Squadra</b> o nel <b>Box PC 1</b>).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._pre_modify_save()
        res = self.mgr.transfer_to_game(self.item["id"], target_save_path=self.user_save_path)
        self._post_modify_save()
        if res.get("success"):
            self.item["status"] = "inviato"
            self.item["injected_target"] = res.get("target")
            self.lbl_status.setText(f"🚀 <b>NEL GIOCO</b> ({res.get('target')})")
            self.lbl_status.setStyleSheet("color: #34d399; font-size: 11px; font-weight: 700;")
            self.btn_transfer.setText("✔ GIÀ TRASFERITO")
            self.transferred.emit(self.item)

            QMessageBox.information(
                self,
                "Trasferimento Riuscito! 🚀",
                f"✔ <b>{self.item['species_name']}</b> è stato trasferito con successo in:<br>"
                f"<b>{res.get('target')}</b>!<br><br>"
                f"Lo troverai subito pronto al prossimo avvio del gioco!"
            )
        else:
            QMessageBox.critical(self, "Errore Trasferimento", f"Impossibile trasferire il Pokémon:<br>{res.get('message')}")

    def close(self):
        self.closed.emit(self.item.get("id", ""))
        self.hide()
        return True

    def closeEvent(self, event):
        self.closed.emit(self.item.get("id", ""))
        self.hide()
        event.accept()
