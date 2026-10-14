#!/usr/bin/env python3
"""
Gestore delle Impostazioni e Mappatura Comandi per Pokémon TCG Adventure.
Memorizza le configurazioni in config/keybindings.json e fornisce
il mapping per la tastiera e per il gamepad/controller.
"""

import json
from pathlib import Path
from PyQt6.QtCore import Qt

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
KEYBINDINGS_FILE = CONFIG_DIR / "keybindings.json"

# Libretro Joypad Button IDs
RETRO_DEVICE_ID_JOYPAD_B = 0
RETRO_DEVICE_ID_JOYPAD_Y = 1
RETRO_DEVICE_ID_JOYPAD_SELECT = 2
RETRO_DEVICE_ID_JOYPAD_START = 3
RETRO_DEVICE_ID_JOYPAD_UP = 4
RETRO_DEVICE_ID_JOYPAD_DOWN = 5
RETRO_DEVICE_ID_JOYPAD_LEFT = 6
RETRO_DEVICE_ID_JOYPAD_RIGHT = 7
RETRO_DEVICE_ID_JOYPAD_A = 8
RETRO_DEVICE_ID_JOYPAD_X = 9
RETRO_DEVICE_ID_JOYPAD_L = 10
RETRO_DEVICE_ID_JOYPAD_R = 11

ACTIONS_DEF = [
    {"id": "A", "name": "Tasto A", "desc": "Conferma / Interazione", "retro_id": RETRO_DEVICE_ID_JOYPAD_A, "default_key": int(Qt.Key.Key_Z), "default_name": "Z", "alt_key": int(Qt.Key.Key_J)},
    {"id": "B", "name": "Tasto B", "desc": "Annulla / Corsa", "retro_id": RETRO_DEVICE_ID_JOYPAD_B, "default_key": int(Qt.Key.Key_X), "default_name": "X", "alt_key": int(Qt.Key.Key_K)},
    {"id": "X", "name": "Tasto X", "desc": "Menu di Gioco", "retro_id": RETRO_DEVICE_ID_JOYPAD_X, "default_key": int(Qt.Key.Key_A), "default_name": "A", "alt_key": int(Qt.Key.Key_U)},
    {"id": "Y", "name": "Tasto Y", "desc": "Registra Oggetto / Bici", "retro_id": RETRO_DEVICE_ID_JOYPAD_Y, "default_key": int(Qt.Key.Key_S), "default_name": "S", "alt_key": int(Qt.Key.Key_I)},
    {"id": "UP", "name": "D-Pad Su", "desc": "Movimento Verso l'Alto", "retro_id": RETRO_DEVICE_ID_JOYPAD_UP, "default_key": int(Qt.Key.Key_Up), "default_name": "Freccia Su", "alt_key": None},
    {"id": "DOWN", "name": "D-Pad Giù", "desc": "Movimento Verso il Basso", "retro_id": RETRO_DEVICE_ID_JOYPAD_DOWN, "default_key": int(Qt.Key.Key_Down), "default_name": "Freccia Giù", "alt_key": None},
    {"id": "LEFT", "name": "D-Pad Sinistra", "desc": "Movimento a Sinistra", "retro_id": RETRO_DEVICE_ID_JOYPAD_LEFT, "default_key": int(Qt.Key.Key_Left), "default_name": "Freccia Sinistra", "alt_key": None},
    {"id": "RIGHT", "name": "D-Pad Destra", "desc": "Movimento a Destra", "retro_id": RETRO_DEVICE_ID_JOYPAD_RIGHT, "default_key": int(Qt.Key.Key_Right), "default_name": "Freccia Destra", "alt_key": None},
    {"id": "L", "name": "Dorsale L", "desc": "Pulsante Superiore Sinistro", "retro_id": RETRO_DEVICE_ID_JOYPAD_L, "default_key": int(Qt.Key.Key_Q), "default_name": "Q", "alt_key": None},
    {"id": "R", "name": "Dorsale R", "desc": "Pulsante Superiore Destro", "retro_id": RETRO_DEVICE_ID_JOYPAD_R, "default_key": int(Qt.Key.Key_E), "default_name": "E", "alt_key": None},
    {"id": "START", "name": "Pulsante Start", "desc": "Avvia / Menu Principale", "retro_id": RETRO_DEVICE_ID_JOYPAD_START, "default_key": int(Qt.Key.Key_Return), "default_name": "Invio", "alt_key": int(Qt.Key.Key_Enter)},
    {"id": "SELECT", "name": "Pulsante Select", "desc": "Selezione Secondaria", "retro_id": RETRO_DEVICE_ID_JOYPAD_SELECT, "default_key": int(Qt.Key.Key_Shift), "default_name": "Shift", "alt_key": int(Qt.Key.Key_Backspace)},
]

KEY_NAMES_IT = {
    int(Qt.Key.Key_Return): "Invio",
    int(Qt.Key.Key_Enter): "Invio Tastierino",
    int(Qt.Key.Key_Shift): "Shift",
    int(Qt.Key.Key_Control): "Ctrl",
    int(Qt.Key.Key_Alt): "Alt",
    int(Qt.Key.Key_Space): "Spazio",
    int(Qt.Key.Key_Tab): "Tab",
    int(Qt.Key.Key_Backspace): "Backspace",
    int(Qt.Key.Key_Up): "Freccia Su",
    int(Qt.Key.Key_Down): "Freccia Giù",
    int(Qt.Key.Key_Left): "Freccia Sinistra",
    int(Qt.Key.Key_Right): "Freccia Destra",
}


def key_to_string(qt_key_int: int) -> str:
    if qt_key_int in KEY_NAMES_IT:
        return KEY_NAMES_IT[qt_key_int]
    try:
        from PyQt6.QtGui import QKeySequence
        txt = QKeySequence(qt_key_int).toString()
        if txt:
            return txt
    except Exception:
        pass
    return f"Key_{qt_key_int}"


class SettingsManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.bindings = self.load_bindings()

    def get_default_bindings(self) -> dict:
        defaults = {}
        for item in ACTIONS_DEF:
            defaults[item["id"]] = {
                "key": item["default_key"],
                "name": item["default_name"],
                "alt_key": item.get("alt_key")
            }
        return defaults

    def load_bindings(self) -> dict:
        defaults = self.get_default_bindings()
        if not KEYBINDINGS_FILE.exists():
            self.save_bindings(defaults)
            return defaults

        try:
            with open(KEYBINDINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Assicura che ci siano tutte le chiavi
                for k, v in defaults.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return defaults

    def save_bindings(self, bindings: dict):
        self.bindings = bindings
        with open(KEYBINDINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(bindings, f, indent=2, ensure_ascii=False)

    def get_qt_key_map(self) -> dict[int, int]:
        """
        Ritorna la mappa: Qt.Key -> RETRO_DEVICE_ID_JOYPAD_*
        Include sia i tasti primari impostati dall'utente che i fallback alternativi.
        """
        key_map = {}
        action_retro_lookup = {item["id"]: item["retro_id"] for item in ACTIONS_DEF}

        for action_id, bind_info in self.bindings.items():
            retro_id = action_retro_lookup.get(action_id)
            if retro_id is None:
                continue

            primary_k = bind_info.get("key")
            if primary_k:
                key_map[primary_k] = retro_id

            alt_k = bind_info.get("alt_key")
            if alt_k:
                key_map[alt_k] = retro_id

        return key_map

