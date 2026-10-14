#!/usr/bin/env python3
"""
Modulo Internazionalizzazione (i18n) per il Launcher e il Client di Pokémon TCG Adventure.
Supporta Inglese ('en') e Italiano ('it') con persistenza in config/launcher_config.json
e aggiornamento dinamico dell'interfaccia grafica tramite listener.
"""

import json
from pathlib import Path
from typing import Callable, List

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "launcher_config.json"

_current_lang = "en"
_listeners: List[Callable[[str], None]] = []

TRANSLATIONS = {
    "en": {
        # App & Window Headers
        "app_window_title": "Pokémon TCG Adventure — Game Client",
        "app_header_title": "POKÉMON TCG ADVENTURE",
        "app_header_subtitle": "Welcome, Trainer",
        
        # Tabs
        "tab_login": "Sign In",
        "tab_register": "New Profile",
        
        # Auth form
        "username_placeholder": "Username / Trainer Name",
        "password_placeholder": "Password",
        "remember_account": "Remember account",
        "btn_play": "PLAY",
        "btn_register_play": "CREATE & PLAY",
        "btn_virtual_box": "📦 VIRTUAL POKÉMON BOX",
        
        # Auth status
        "status_enter_credentials": "Please enter both username and password.",
        "status_auth_error": "Authentication error.",
        "status_logging_in": "Sign-in successful! Launching game...",
        "status_load_rom_first": "Please configure the game ROM first.",
        "status_user_empty": "Username cannot be empty.",
        "status_user_min_len": "Username must have at least 3 characters.",
        "status_pwd_min_len": "Password must have at least 4 characters.",
        "status_user_exists": "Username already exists.",
        "status_user_not_found": "User not found.",
        "status_wrong_pwd": "Incorrect password.",
        
        # ROM & Resolution Bar
        "rom_status_loaded": "✔ ROM: {name} (Loaded)",
        "rom_status_missing": "⚠ ROM not configured",
        "btn_change": "Change...",
        "btn_load_rom": "Browse ROM (.nds)",
        "resolution_label": "Resolution:",
        "res_1080p": "1080p (Recommended)",
        "res_720p": "720p",
        "res_1440p": "1440p (2K)",
        "res_fullscreen": "Fullscreen",
        "btn_settings": "⚙ Settings",
        
        # Settings Dialog
        "settings_dialog_title": "Settings & Controls Configuration",
        "settings_header_language": "🌐 Language Settings",
        "settings_label_language": "Interface Language:",
        "settings_header_controls": "⚙ Controls Configuration",
        "settings_hint": "Click an action button and press the key you want to assign:",
        "settings_header_gamepad": "🎮 Gamepad / Controller Support",
        "settings_pad_detected": "Detected ({name})",
        "settings_pad_waiting": "Waiting for connection (Plug & Play active)",
        "settings_pad_desc": "Xbox, PlayStation, and USB controllers are automatically mapped 1:1 with DS buttons.",
        "settings_btn_reset": "🔄 Reset to Defaults",
        "settings_btn_cancel": "Cancel",
        "settings_btn_save": "💾 Save Settings",
        "settings_key_listening": "Press any key...",
        "settings_saved_msg": "Settings saved successfully!",
        
        # In-Game Client HUD
        "client_window_title": "Pokémon TCG Adventure — [Trainer: {username}]",
        "hud_trainer": "👤 Trainer: <b style='color:#00e5ff;'>{username}</b>",
        "hud_status_core": "🟢 melonDS Core Integrated (60 FPS)",
        "hud_btn_touch_open": "📱 TOUCH SCREEN",
        "hud_btn_touch_close": "📱 CLOSE TOUCH",
        "hud_btn_virtual_box": "📦 VIRTUAL BOX",
        "hud_btn_scanner": "📷 TCG SCANNER",
        "hud_btn_settings": "⚙ SETTINGS",
        "hud_btn_exit": "🚪 Exit to Launcher",
        "touch_title": "Touch Screen (Click with mouse):",
        
        # TCG Scanner Drawer
        "scanner_header": "📷 TCG SCANNER HUB",
        "finish_normal": "Normal",
        "finish_holo": "Holo",
        "finish_reverse_holo": "Reverse Holo",
        "search_placeholder": "Card Name (e.g. Charizard)",
        "btn_search": "Search",
        "btn_start_cam": "📷 Start Camera",
        "btn_stop_cam": "⏹ Stop Camera",
        "btn_capture": "📸 Take Photo",
        "btn_inject": "⚡ INJECT INTO GAME",
        "camera_standby": "Standby Camera<br><span style='font-size:11px;color:#64748b;'>Click 'Start Camera'</span>",
        "camera_active": "Align the card inside the frame",
        "scanner_no_results": "No Results",
        "scanner_no_card_found": "No card found for '{query}'.",
        "scanner_duplicate_title": "❌ Duplicate Card",
        "scanner_duplicate_msg": "This card has already been registered!",
        "scanner_confidence": "Confidence",
        "scanner_method": "Method",
        "scanner_artist": "Artist",
        "scanner_set": "Set",
        "scanner_tier": "Tier",
        "scanner_ball": "Ball",
        
        # Virtual Box Dialog
        "vbox_title": "Virtual Pokémon Box — Trainer {username}",
        "vbox_summary": "Storage: {count} cards | In Party: {party}/6",
        "vbox_btn_deposit": "Deposit to Box",
        "vbox_btn_withdraw": "Withdraw to Party",
        "vbox_tab_all": "All Cards",
        "vbox_tab_party": "Current Party (In-Game)",
        "vbox_empty": "No Pokémon currently stored in the Virtual Box.",
        
        # Dialogs & Prompts
        "dialog_exit_title": "Exit Game Session",
        "dialog_exit_prompt": "Do you want to save and return to the main launcher?",
        "dialog_rom_invalid_title": "Invalid ROM",
        "dialog_rom_invalid_msg": "The selected file is not a valid Nintendo DS ROM.",
        
        # Actions definition
        "action_A_name": "A Button",
        "action_A_desc": "Confirm / Interaction",
        "action_B_name": "B Button",
        "action_B_desc": "Cancel / Run",
        "action_X_name": "X Button",
        "action_X_desc": "In-Game Menu",
        "action_Y_name": "Y Button",
        "action_Y_desc": "Register Item / Bicycle",
        "action_UP_name": "D-Pad Up",
        "action_UP_desc": "Movement Up",
        "action_DOWN_name": "D-Pad Down",
        "action_DOWN_desc": "Movement Down",
        "action_LEFT_name": "D-Pad Left",
        "action_LEFT_desc": "Movement Left",
        "action_RIGHT_name": "D-Pad Right",
        "action_RIGHT_desc": "Movement Right",
        "action_L_name": "L Trigger",
        "action_L_desc": "Top-Left Shoulder Button",
        "action_R_name": "R Trigger",
        "action_R_desc": "Top-Right Shoulder Button",
        "action_START_name": "Start Button",
        "action_START_desc": "Start / Main Menu",
        "action_SELECT_name": "Select Button",
        "action_SELECT_desc": "Secondary Selection",
        
        # Key names
        "key_return": "Enter",
        "key_enter": "Keypad Enter",
        "key_shift": "Shift",
        "key_ctrl": "Ctrl",
        "key_alt": "Alt",
        "key_space": "Space",
        "key_tab": "Tab",
        "key_backspace": "Backspace",
        "key_up": "Up Arrow",
        "key_down": "Down Arrow",
        "key_left": "Left Arrow",
        "key_right": "Right Arrow",
    },
    "it": {
        # App & Window Headers
        "app_window_title": "Pokémon TCG Adventure — Game Client",
        "app_header_title": "POKÉMON TCG ADVENTURE",
        "app_header_subtitle": "Benvenuto, Allenatore",
        
        # Tabs
        "tab_login": "Accedi",
        "tab_register": "Nuovo Profilo",
        
        # Auth form
        "username_placeholder": "Nome Utente / Allenatore",
        "password_placeholder": "Password",
        "remember_account": "Ricorda account",
        "btn_play": "GIOCA",
        "btn_register_play": "CREA & GIOCA",
        "btn_virtual_box": "📦 BOX POKÉMON VIRTUALE",
        
        # Auth status
        "status_enter_credentials": "Inserisci sia nome utente che password.",
        "status_auth_error": "Errore di autenticazione.",
        "status_logging_in": "Accesso completato! Avvio in corso...",
        "status_load_rom_first": "Carica prima la ROM di gioco per iniziare.",
        "status_user_empty": "Il nome utente non può essere vuoto.",
        "status_user_min_len": "Il nome utente deve avere almeno 3 caratteri.",
        "status_pwd_min_len": "La password deve avere almeno 4 caratteri.",
        "status_user_exists": "Nome utente già esistente.",
        "status_user_not_found": "Utente non trovato.",
        "status_wrong_pwd": "Password errata.",
        
        # ROM & Resolution Bar
        "rom_status_loaded": "✔ ROM: {name} (Caricata)",
        "rom_status_missing": "⚠ ROM non configurata",
        "btn_change": "Cambia...",
        "btn_load_rom": "Carica ROM (.nds)",
        "resolution_label": "Risoluzione:",
        "res_1080p": "1080p (Consigliata)",
        "res_720p": "720p",
        "res_1440p": "1440p (2K)",
        "res_fullscreen": "Schermo Intero",
        "btn_settings": "⚙ Impostazioni",
        
        # Settings Dialog
        "settings_dialog_title": "Configurazione Comandi & Impostazioni",
        "settings_header_language": "🌐 Impostazioni Lingua",
        "settings_label_language": "Lingua dell'Interfaccia:",
        "settings_header_controls": "⚙ Configurazione Comandi",
        "settings_hint": "Clicca sul pulsante di un'azione e premi il tasto della tastiera che desideri assegnare:",
        "settings_header_gamepad": "🎮 Supporto Controller / Gamepad",
        "settings_pad_detected": "Rilevato ({name})",
        "settings_pad_waiting": "In attesa di collegamento (Plug & Play attivo)",
        "settings_pad_desc": "I controller Xbox / PlayStation / USB sono mappati automaticamente 1:1 con i tasti del DS.",
        "settings_btn_reset": "🔄 Ripristina Predefiniti",
        "settings_btn_cancel": "Annulla",
        "settings_btn_save": "💾 Salva Impostazioni",
        "settings_key_listening": "Premi un tasto...",
        "settings_saved_msg": "Impostazioni salvate con successo!",
        
        # In-Game Client HUD
        "client_window_title": "Pokémon TCG Adventure — [Allenatore: {username}]",
        "hud_trainer": "👤 Allenatore: <b style='color:#00e5ff;'>{username}</b>",
        "hud_status_core": "🟢 Core melonDS Integrato (60 FPS)",
        "hud_btn_touch_open": "📱 SCHERMO TOUCH",
        "hud_btn_touch_close": "📱 CHIUDI TOUCH",
        "hud_btn_virtual_box": "📦 BOX VIRTUALE",
        "hud_btn_scanner": "📷 TCG SCANNER",
        "hud_btn_settings": "⚙ IMPOSTAZIONI",
        "hud_btn_exit": "🚪 Esci al Launcher",
        "touch_title": "Schermo Touch (Clicca con il mouse):",
        
        # TCG Scanner Drawer
        "scanner_header": "📷 TCG SCANNER HUB",
        "finish_normal": "Normale",
        "finish_holo": "Holo",
        "finish_reverse_holo": "Reverse Holo",
        "search_placeholder": "Nome carta (es. Charizard)",
        "btn_search": "Cerca",
        "btn_start_cam": "📷 Avvia Fotocamera",
        "btn_stop_cam": "⏹ Spegni Fotocamera",
        "btn_capture": "📸 Scatta Foto",
        "btn_inject": "⚡ INVIA AL GIOCO",
        "camera_standby": "Telecamera in Standby<br><span style='font-size:11px;color:#64748b;'>Clicca 'Avvia Fotocamera'</span>",
        "camera_active": "Inquadra la carta nel riquadro",
        "scanner_no_results": "Nessun Risultato",
        "scanner_no_card_found": "Nessuna carta trovata per '{query}'.",
        "scanner_duplicate_title": "❌ Carta Duplicata",
        "scanner_duplicate_msg": "Questa carta è già stata registrata!",
        "scanner_confidence": "Affidabilità",
        "scanner_method": "Metodo",
        "scanner_artist": "Illustratore",
        "scanner_set": "Set",
        "scanner_tier": "Tier",
        "scanner_ball": "Sfera",
        
        # Virtual Box Dialog
        "vbox_title": "Box Pokémon Virtuale — Allenatore {username}",
        "vbox_summary": "Deposito: {count} carte | In Squadra: {party}/6",
        "vbox_btn_deposit": "Deposita nel Box",
        "vbox_btn_withdraw": "Ritira in Squadra",
        "vbox_tab_all": "Tutte le Carte",
        "vbox_tab_party": "Squadra Attiva (In Gioco)",
        "vbox_empty": "Nessun Pokémon attualmente conservato nel Box Virtuale.",
        
        # Dialogs & Prompts
        "dialog_exit_title": "Uscita Gioco",
        "dialog_exit_prompt": "Vuoi salvare e tornare al launcher?",
        "dialog_rom_invalid_title": "ROM Non Valida",
        "dialog_rom_invalid_msg": "Il file selezionato non è una ROM Nintendo DS valida.",
        
        # Actions definition
        "action_A_name": "Tasto A",
        "action_A_desc": "Conferma / Interazione",
        "action_B_name": "Tasto B",
        "action_B_desc": "Annulla / Corsa",
        "action_X_name": "Tasto X",
        "action_X_desc": "Menu di Gioco",
        "action_Y_name": "Tasto Y",
        "action_Y_desc": "Registra Oggetto / Bici",
        "action_UP_name": "D-Pad Su",
        "action_UP_desc": "Movimento Verso l'Alto",
        "action_DOWN_name": "D-Pad Giù",
        "action_DOWN_desc": "Movimento Verso il Basso",
        "action_LEFT_name": "D-Pad Sinistra",
        "action_LEFT_desc": "Movimento a Sinistra",
        "action_RIGHT_name": "D-Pad Destra",
        "action_RIGHT_desc": "Movimento a Destra",
        "action_L_name": "Dorsale L",
        "action_L_desc": "Pulsante Superiore Sinistro",
        "action_R_name": "Dorsale R",
        "action_R_desc": "Pulsante Superiore Destro",
        "action_START_name": "Pulsante Start",
        "action_START_desc": "Avvia / Menu Principale",
        "action_SELECT_name": "Pulsante Select",
        "action_SELECT_desc": "Selezione Secondaria",
        
        # Key names
        "key_return": "Invio",
        "key_enter": "Invio Tastierino",
        "key_shift": "Shift",
        "key_ctrl": "Ctrl",
        "key_alt": "Alt",
        "key_space": "Spazio",
        "key_tab": "Tab",
        "key_backspace": "Backspace",
        "key_up": "Freccia Su",
        "key_down": "Freccia Giù",
        "key_left": "Freccia Sinistra",
        "key_right": "Freccia Destra",
    }
}


def _load_persisted_language() -> str:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                lang = data.get("language", "en")
                if lang in TRANSLATIONS:
                    return lang
        except Exception:
            pass
    return "en"


_current_lang = _load_persisted_language()


def get_language() -> str:
    global _current_lang
    return _current_lang


def set_language(lang_code: str) -> bool:
    global _current_lang
    if lang_code not in TRANSLATIONS:
        return False
    _current_lang = lang_code

    # Salva su file di configurazione
    try:
        data = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["language"] = lang_code
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[i18n] Errore salvataggio lingua: {e}", flush=True)

    # Notifica listener
    for cb in list(_listeners):
        try:
            cb(lang_code)
        except Exception:
            pass
    return True


def register_language_listener(callback: Callable[[str], None]):
    if callback not in _listeners:
        _listeners.append(callback)


def unregister_language_listener(callback: Callable[[str], None]):
    if callback in _listeners:
        _listeners.remove(callback)


def t(key: str, **kwargs) -> str:
    lang = get_language()
    table = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = table.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
