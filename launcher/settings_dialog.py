#!/usr/bin/env python3
"""
Finestra di Dialogo per la Configurazione dei Comandi (Tastiera & Gamepad) e Lingua.
Supporta selezione dinamica della lingua (Inglese / Italiano) con aggiornamento istantaneo
e rimappatura interattiva dei tasti del Nintendo DS.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QComboBox, QMessageBox
)
from PyQt6.QtGui import QKeyEvent

from launcher.i18n import (
    t, get_language, set_language,
    register_language_listener, unregister_language_listener
)
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
QLabel#SectionTitle {
    font-size: 14px;
    font-weight: 800;
    color: #38bdf8;
}
QLabel#ActionTitle {
    font-size: 13px;
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
QComboBox#LangCombo {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1.5px solid #0284c7;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 700;
    font-size: 13px;
    min-width: 130px;
}
QComboBox#LangCombo:hover {
    border-color: #00e5ff;
}
QComboBox#LangCombo QAbstractItemView {
    background-color: #131d33;
    color: #f8fafc;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    border: 1px solid #334155;
}
"""


class SettingsDialog(QDialog):
    keybindings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 620)
        self.setStyleSheet(DIALOG_STYLE)

        self.mgr = SettingsManager()
        self.current_bindings = dict(self.mgr.bindings)
        self.active_listening_action = None
        self.key_buttons = {}
        self.action_labels = {}

        self._build_ui()
        self._retranslate_ui()
        register_language_listener(self._retranslate_ui)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Intestazione Dialogo
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("DialogTitle")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # ----------------- SEZIONE LINGUA -----------------
        lang_card = QFrame()
        lang_card.setObjectName("SectionCard")
        lang_layout = QHBoxLayout(lang_card)
        lang_layout.setContentsMargins(16, 12, 16, 12)

        lang_text_layout = QVBoxLayout()
        lang_text_layout.setSpacing(2)
        self.lbl_lang_section = QLabel()
        self.lbl_lang_section.setObjectName("SectionTitle")
        self.lbl_lang_desc = QLabel()
        self.lbl_lang_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        lang_text_layout.addWidget(self.lbl_lang_section)
        lang_text_layout.addWidget(self.lbl_lang_desc)

        self.combo_lang = QComboBox()
        self.combo_lang.setObjectName("LangCombo")
        self.combo_lang.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo_lang.addItem("English (EN)", "en")
        self.combo_lang.addItem("Italiano (IT)", "it")

        # Seleziona la lingua attualmente attiva
        active_lang = get_language()
        for idx in range(self.combo_lang.count()):
            if self.combo_lang.itemData(idx) == active_lang:
                self.combo_lang.setCurrentIndex(idx)
                break

        self.combo_lang.currentIndexChanged.connect(self._on_language_selection_changed)

        lang_layout.addLayout(lang_text_layout)
        lang_layout.addStretch()
        lang_layout.addWidget(self.combo_lang)
        main_layout.addWidget(lang_card)

        # ----------------- SEZIONE COMANDI -----------------
        self.lbl_hint = QLabel()
        self.lbl_hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
        main_layout.addWidget(self.lbl_hint)

        # Griglia comandi (due colonne: Tasti Azione a sinistra, D-Pad/Menu a destra)
        card = QFrame()
        card.setObjectName("SectionCard")
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)

        for idx, item in enumerate(ACTIONS_DEF):
            act_id = item["id"]
            col_base = 0 if idx < 6 else 3
            row = idx if idx < 6 else idx - 6

            # Label azione
            lbl_act = QLabel()
            lbl_act.setObjectName("ActionTitle")
            lbl_desc = QLabel()
            lbl_desc.setObjectName("ActionDesc")

            self.action_labels[act_id] = (lbl_act, lbl_desc)

            vbox = QVBoxLayout()
            vbox.setSpacing(1)
            vbox.addWidget(lbl_act)
            vbox.addWidget(lbl_desc)

            # Pulsante Tasto
            btn = QPushButton()
            btn.setObjectName("KeyButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, a=act_id: self._start_listening(a))
            self.key_buttons[act_id] = btn

            card_layout.addLayout(vbox, row, col_base)
            card_layout.addWidget(btn, row, col_base + 1)

            if col_base == 0 and row == 0:
                card_layout.setColumnMinimumWidth(2, 20)

        main_layout.addWidget(card)

        # ----------------- SEZIONE GAMEPAD -----------------
        pad_card = QFrame()
        pad_card.setObjectName("SectionCard")
        pad_layout = QHBoxLayout(pad_card)
        pad_layout.setContentsMargins(16, 10, 16, 10)

        lbl_pad_icon = QLabel("🎮")
        lbl_pad_icon.setStyleSheet("font-size: 22px;")

        self.lbl_pad_text = QLabel()
        self.lbl_pad_text.setTextFormat(Qt.TextFormat.RichText)

        pad_layout.addWidget(lbl_pad_icon)
        pad_layout.addWidget(self.lbl_pad_text)
        pad_layout.addStretch()
        main_layout.addWidget(pad_card)

        # ----------------- BARRA PULSANTI INFERIORE -----------------
        btn_bar = QHBoxLayout()
        self.btn_reset = QPushButton()
        self.btn_reset.setObjectName("SecondaryButton")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.clicked.connect(self._reset_defaults)

        self.btn_cancel = QPushButton()
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton()
        self.btn_save.setObjectName("PrimarySaveButton")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_and_close)

        btn_bar.addWidget(self.btn_reset)
        btn_bar.addStretch()
        btn_bar.addWidget(self.btn_cancel)
        btn_bar.addWidget(self.btn_save)
        main_layout.addLayout(btn_bar)

    def _retranslate_ui(self, lang_code=None):
        """Aggiorna tutti i testi dell'interfaccia nella lingua selezionata."""
        self.setWindowTitle(t("settings_dialog_title"))
        self.lbl_title.setText(f"⚙ {t('settings_dialog_title')}")
        self.lbl_lang_section.setText(t("settings_header_language"))
        self.lbl_lang_desc.setText(t("settings_label_language"))
        self.lbl_hint.setText(t("settings_hint"))

        # Aggiorna label delle azioni e pulsanti
        for act_id, (lbl_act, lbl_desc) in self.action_labels.items():
            lbl_act.setText(t(f"action_{act_id}_name"))
            lbl_desc.setText(t(f"action_{act_id}_desc"))

            if act_id != self.active_listening_action:
                info = self.current_bindings.get(act_id, {})
                key_code = info.get("key")
                if key_code is not None:
                    name = key_to_string(key_code)
                    self.key_buttons[act_id].setText(f"[ {name} ]")

        # Gamepad status
        gamepad_status = self._detect_gamepad_status()
        self.lbl_pad_text.setText(
            f"<b>{t('settings_header_gamepad')}:</b> {gamepad_status}<br>"
            f"<span style='color:#64748b; font-size:11px;'>{t('settings_pad_desc')}</span>"
        )

        # Pulsanti inferiori
        self.btn_reset.setText(t("settings_btn_reset"))
        self.btn_cancel.setText(t("settings_btn_cancel"))
        self.btn_save.setText(t("settings_btn_save"))

    def _on_language_selection_changed(self, index: int):
        lang_code = self.combo_lang.itemData(index)
        if lang_code and lang_code != get_language():
            set_language(lang_code)

    def _detect_gamepad_status(self) -> str:
        try:
            import evdev
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            pads = [d.name for d in devices if any(k in d.name.lower() for k in ["controller", "gamepad", "joystick", "xbox", "playstation", "wireless gamepad"])]
            if pads:
                return f"<span style='color:#10b981;'>{t('settings_pad_detected', name=pads[0])}</span>"
        except Exception:
            pass
        return f"<span style='color:#94a3b8;'>{t('settings_pad_waiting')}</span>"

    def _start_listening(self, action_id: str):
        if self.active_listening_action and self.active_listening_action in self.key_buttons:
            old_act = self.active_listening_action
            old_key = self.current_bindings[old_act].get("key")
            old_name = key_to_string(old_key) if old_key else self.current_bindings[old_act].get("name", "")
            self.key_buttons[old_act].setText(f"[ {old_name} ]")
            self.key_buttons[old_act].setObjectName("KeyButton")
            self.key_buttons[old_act].setStyle(self.key_buttons[old_act].style())

        self.active_listening_action = action_id
        btn = self.key_buttons[action_id]
        btn.setText(t("settings_key_listening"))
        btn.setObjectName("KeyButtonListening")
        btn.setStyle(btn.style())
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.active_listening_action:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_Escape:
            action_id = self.active_listening_action
            old_key = self.current_bindings[action_id].get("key")
            key_name = key_to_string(old_key) if old_key else self.current_bindings[action_id].get("name", "")
            btn = self.key_buttons[action_id]
            btn.setText(f"[ {key_name} ]")
            btn.setObjectName("KeyButton")
            btn.setStyle(btn.style())
            self.active_listening_action = None
            event.accept()
            return

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
                key_code = info.get("key")
                name = key_to_string(key_code) if key_code else info.get("name", "")
                self.key_buttons[act_id].setText(f"[ {name} ]")
                self.key_buttons[act_id].setObjectName("KeyButton")
                self.key_buttons[act_id].setStyle(self.key_buttons[act_id].style())

    def _save_and_close(self):
        lang_code = self.combo_lang.currentData()
        if lang_code:
            set_language(lang_code)

        self.mgr.save_bindings(self.current_bindings)
        self.keybindings_changed.emit()
        self.accept()

    def closeEvent(self, event):
        unregister_language_listener(self._retranslate_ui)
        super().closeEvent(event)

    def reject(self):
        unregister_language_listener(self._retranslate_ui)
        super().reject()

    def accept(self):
        unregister_language_listener(self._retranslate_ui)
        super().accept()
