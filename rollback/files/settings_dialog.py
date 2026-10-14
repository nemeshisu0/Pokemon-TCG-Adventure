#!/usr/bin/env python3
"""
Finestra di Dialogo per la Configurazione dei Comandi (Tastiera & Gamepad).
Interfaccia moderna e interattiva: permette di cliccare su ciascun tasto
del Nintendo DS e rimapparlo all'istante premendo il pulsante desiderato.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtGui import QKeyEvent

from launcher.settings_manager import (
    SettingsManager, ACTIONS_DEF, key_to_string
)

DIALOG_STYLE = """
QDialog {
    background-color: #0b1120;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 12px;
}
QFrame#SectionCard {
    background-color: #131d33;
    border: 1px solid #1e293b;
    border-radius: 10px;
}
QLabel {
    color: #cbd5e1;
    font-size: 13px;
}
QLabel#DialogTitle {
    font-size: 18px;
    font-weight: 800;
    color: #00e5ff;
}
QLabel#ActionTitle {
    font-size: 14px;
    font-weight: 700;
    color: #f1f5f9;
}
QLabel#ActionDesc {
    font-size: 11px;
    color: #64748b;
}
QPushButton#KeyButton {
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 700;
    font-size: 13px;
    min-width: 120px;
}
QPushButton#KeyButton:hover {
    background-color: #334155;
    border-color: #38bdf8;
}
QPushButton#KeyButtonListening {
    background-color: #0284c7;
    color: #ffffff;
    border: 2px solid #00e5ff;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 800;
    font-size: 13px;
    min-width: 120px;
}
QPushButton#PrimarySaveButton {
    background-color: #10b981;
    color: #ffffff;
    font-weight: 800;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
}
QPushButton#PrimarySaveButton:hover {
    background-color: #059669;
}
QPushButton#SecondaryButton {
    background-color: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton#SecondaryButton:hover {
    background-color: #334155;
    color: #f8fafc;
}
"""


class SettingsDialog(QDialog):
    keybindings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurazione Comandi & Impostazioni")
        self.setMinimumSize(680, 560)
        self.setStyleSheet(DIALOG_STYLE)

        self.mgr = SettingsManager()
        self.current_bindings = dict(self.mgr.bindings)
        self.active_listening_action = None
        self.key_buttons = {}

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Intestazione
        header_layout = QHBoxLayout()
        lbl_title = QLabel("⚙ Configurazione Comandi")
        lbl_title.setObjectName("DialogTitle")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        lbl_hint = QLabel("Clicca sul pulsante di un'azione e premi il tasto della tastiera che desideri assegnare:")
        lbl_hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
        main_layout.addWidget(lbl_hint)

        # Griglia comandi (due colonne: Tasti Azione a sinistra, D-Pad/Menu a destra)
        card = QFrame()
        card.setObjectName("SectionCard")
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        # Dividiamo i 12 comandi in due colonne (6 ciascuna)
        for idx, item in enumerate(ACTIONS_DEF):
            act_id = item["id"]
            col_base = 0 if idx < 6 else 3
            row = idx if idx < 6 else idx - 6

            # Label azione
            lbl_act = QLabel(item["name"])
            lbl_act.setObjectName("ActionTitle")
            lbl_desc = QLabel(item["desc"])
            lbl_desc.setObjectName("ActionDesc")

            vbox = QVBoxLayout()
            vbox.setSpacing(2)
            vbox.addWidget(lbl_act)
            vbox.addWidget(lbl_desc)

            # Pulsante Tasto
            btn = QPushButton()
            btn.setObjectName("KeyButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            cur_key_info = self.current_bindings.get(act_id, {})
            key_name = cur_key_info.get("name", item["default_name"])
            btn.setText(f"[ {key_name} ]")
            btn.clicked.connect(lambda checked, a=act_id: self._start_listening(a))

            self.key_buttons[act_id] = btn

            card_layout.addLayout(vbox, row, col_base)
            card_layout.addWidget(btn, row, col_base + 1)

            if col_base == 0 and row == 0:
                # Spazio tra le due colonne
                card_layout.setColumnMinimumWidth(2, 24)

        main_layout.addWidget(card)

        # Scheda Gamepad informativo
        pad_card = QFrame()
        pad_card.setObjectName("SectionCard")
        pad_layout = QHBoxLayout(pad_card)
        pad_layout.setContentsMargins(16, 12, 16, 12)

        gamepad_status = self._detect_gamepad_status()
        lbl_pad_icon = QLabel("🎮")
        lbl_pad_icon.setStyleSheet("font-size: 20px;")
        lbl_pad_text = QLabel(f"<b>Supporto Controller:</b> {gamepad_status}<br>"
                              "<span style='color:#64748b; font-size:11px;'>I controller Xbox / PlayStation / USB sono mappati automaticamente 1:1 con i tasti del DS.</span>")
        lbl_pad_text.setTextFormat(Qt.TextFormat.RichText)

        pad_layout.addWidget(lbl_pad_icon)
        pad_layout.addWidget(lbl_pad_text)
        pad_layout.addStretch()
        main_layout.addWidget(pad_card)

        # Barra Pulsanti Inferiore
        btn_bar = QHBoxLayout()
        btn_reset = QPushButton("🔄 Ripristina Predefiniti")
        btn_reset.setObjectName("SecondaryButton")
        btn_reset.clicked.connect(self._reset_defaults)

        btn_cancel = QPushButton("Annulla")
        btn_cancel.setObjectName("SecondaryButton")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Salva Comandi")
        btn_save.setObjectName("PrimarySaveButton")
        btn_save.clicked.connect(self._save_and_close)

        btn_bar.addWidget(btn_reset)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        main_layout.addLayout(btn_bar)

    def _detect_gamepad_status(self) -> str:
        try:
            import evdev
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            pads = [d.name for d in devices if any(k in d.name.lower() for k in ["controller", "gamepad", "joystick", "xbox", "playstation", "wireless gamepad"])]
            if pads:
                return f"<span style='color:#10b981;'>Rilevato ({pads[0]})</span>"
        except Exception:
            pass
        return "<span style='color:#94a3b8;'>In attesa di collegamento (Plug & Play attivo)</span>"

    def _start_listening(self, action_id: str):
        # Se c'era già un'azione in ascolto, ripristinala
        if self.active_listening_action and self.active_listening_action in self.key_buttons:
            old_act = self.active_listening_action
            old_name = self.current_bindings[old_act]["name"]
            self.key_buttons[old_act].setText(f"[ {old_name} ]")
            self.key_buttons[old_act].setObjectName("KeyButton")
            self.key_buttons[old_act].setStyle(self.key_buttons[old_act].style())

        self.active_listening_action = action_id
        btn = self.key_buttons[action_id]
        btn.setText("Premi un tasto...")
        btn.setObjectName("KeyButtonListening")
        btn.setStyle(btn.style())
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.active_listening_action:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_Escape:
            # Annulla ascolto tasto
            action_id = self.active_listening_action
            key_name = self.current_bindings[action_id]["name"]
            btn = self.key_buttons[action_id]
            btn.setText(f"[ {key_name} ]")
            btn.setObjectName("KeyButton")
            btn.setStyle(btn.style())
            self.active_listening_action = None
            event.accept()
            return

        # Assegna il nuovo tasto
        action_id = self.active_listening_action
        readable_name = key_to_string(key)

        self.current_bindings[action_id] = {
            "key": int(key),
            "name": readable_name,
            "alt_key": None
        }

        btn = self.key_buttons[action_id]
        btn.setText(f"[ {readable_name} ]")
        btn.setObjectName("KeyButton")
        btn.setStyle(btn.style())

        self.active_listening_action = None
        event.accept()

    def _reset_defaults(self):
        defaults = self.mgr.get_default_bindings()
        self.current_bindings = defaults
        for act_id, info in defaults.items():
            if act_id in self.key_buttons:
                self.key_buttons[act_id].setText(f"[ {info['name']} ]")
                self.key_buttons[act_id].setObjectName("KeyButton")
                self.key_buttons[act_id].setStyle(self.key_buttons[act_id].style())

    def _save_and_close(self):
        self.mgr.save_bindings(self.current_bindings)
        self.keybindings_changed.emit()
        self.accept()

