#!/usr/bin/env python3
"""
Test di verifica per l'internazionalizzazione (i18n) e il cambio lingua nel Launcher.
Verifica:
1. Caricamento e traduzione chiavi in Inglese ed Italiano.
2. Persistenza della lingua in config/launcher_config.json.
3. Funzionamento di SettingsDialog e selettore lingua (QComboBox).
4. Aggiornamento in tempo reale di LauncherWindow tramite listener.
"""

import sys
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Imposta piattaforma offscreen per test headless
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from launcher import i18n
from launcher.settings_manager import SettingsManager, key_to_string, get_action_name, get_action_desc
from launcher.settings_dialog import SettingsDialog
from launcher.launcher_window import LauncherWindow


def test_i18n():
    print("[1/5] Test del modulo base i18n...")
    # Imposta lingua inglese
    i18n.set_language("en")
    assert i18n.get_language() == "en", "Lingua attiva dovrebbe essere 'en'"
    assert i18n.t("tab_login") == "Sign In", f"Atteso 'Sign In', ottenuto '{i18n.t('tab_login')}'"
    assert i18n.t("btn_play") == "PLAY", f"Atteso 'PLAY', ottenuto '{i18n.t('btn_play')}'"
    assert i18n.t("btn_settings") == "⚙ Settings", f"Atteso '⚙ Settings', ottenuto '{i18n.t('btn_settings')}'"

    # Imposta lingua italiana
    i18n.set_language("it")
    assert i18n.get_language() == "it", "Lingua attiva dovrebbe essere 'it'"
    assert i18n.t("tab_login") == "Accedi", f"Atteso 'Accedi', ottenuto '{i18n.t('tab_login')}'"
    assert i18n.t("btn_play") == "GIOCA", f"Atteso 'GIOCA', ottenuto '{i18n.t('btn_play')}'"
    assert i18n.t("btn_settings") == "⚙ Impostazioni", f"Atteso '⚙ Impostazioni', ottenuto '{i18n.t('btn_settings')}'"

    # Reimposta inglese
    i18n.set_language("en")
    print("  ✔ Modulo base i18n: SUPERATO")


def test_settings_manager_localization():
    print("[2/5] Test localizzazione nomi azioni e tasti...")
    i18n.set_language("en")
    assert get_action_name("A") == "A Button"
    assert get_action_desc("A") == "Confirm / Interaction"

    from PyQt6.QtCore import Qt
    assert key_to_string(int(Qt.Key.Key_Return)) == "Enter"
    assert key_to_string(int(Qt.Key.Key_Up)) == "Up Arrow"

    i18n.set_language("it")
    assert get_action_name("A") == "Tasto A"
    assert get_action_desc("A") == "Conferma / Interazione"
    assert key_to_string(int(Qt.Key.Key_Return)) == "Invio"
    assert key_to_string(int(Qt.Key.Key_Up)) == "Freccia Su"

    i18n.set_language("en")
    print("  ✔ Localizzazione SettingsManager: SUPERATO")


def test_gui_integration():
    print("[3/5] Test interfaccia grafica e selettore lingua in SettingsDialog...")
    app = QApplication.instance() or QApplication(sys.argv[:1])

    # Assicuriamo che parta in inglese
    i18n.set_language("en")
    window = LauncherWindow()

    # Verifica testi LauncherWindow in Inglese
    assert window.btn_tab_login.text() == "Sign In", f"Got {window.btn_tab_login.text()}"
    assert window.btn_tab_register.text() == "New Profile", f"Got {window.btn_tab_register.text()}"
    assert window.btn_play.text() == "PLAY", f"Got {window.btn_play.text()}"
    assert window.btn_box.text() == "📦 VIRTUAL POKÉMON BOX", f"Got {window.btn_box.text()}"
    assert window.btn_settings.text() == "⚙ Settings", f"Got {window.btn_settings.text()}"
    assert window.chk_remember.text() == "Remember account", f"Got {window.chk_remember.text()}"
    assert window.lbl_subtitle.text() == "Welcome, Trainer", f"Got {window.lbl_subtitle.text()}"
    print("  ✔ LauncherWindow in Inglese: SUPERATO")

    # Apri SettingsDialog
    dlg = SettingsDialog(window)
    assert dlg.windowTitle() == "Settings & Controls Configuration"
    assert dlg.combo_lang.currentData() == "en"
    assert dlg.btn_save.text() == "💾 Save Settings"
    assert dlg.btn_cancel.text() == "Cancel"
    assert dlg.btn_reset.text() == "🔄 Reset to Defaults"
    print("  ✔ SettingsDialog in Inglese: SUPERATO")

    # Cambia lingua a Italiano dal combo box
    it_index = -1
    for i in range(dlg.combo_lang.count()):
        if dlg.combo_lang.itemData(i) == "it":
            it_index = i
            break
    assert it_index != -1, "Opzione 'it' non trovata nel combo box"

    print("[4/5] Cambio dinamico a 'it' dal combo box...")
    dlg.combo_lang.setCurrentIndex(it_index)

    # Verifica che la finestra delle impostazioni si sia aggiornata istantaneamente
    assert dlg.windowTitle() == "Configurazione Comandi & Impostazioni"
    assert dlg.btn_save.text() == "💾 Salva Impostazioni"
    assert dlg.btn_cancel.text() == "Annulla"
    assert dlg.btn_reset.text() == "🔄 Ripristina Predefiniti"

    # Verifica che ANCHE la finestra principale LauncherWindow si sia aggiornata istantaneamente!
    assert window.btn_tab_login.text() == "Accedi", f"Got {window.btn_tab_login.text()}"
    assert window.btn_tab_register.text() == "Nuovo Profilo", f"Got {window.btn_tab_register.text()}"
    assert window.btn_play.text() == "GIOCA", f"Got {window.btn_play.text()}"
    assert window.btn_box.text() == "📦 BOX POKÉMON VIRTUALE", f"Got {window.btn_box.text()}"
    assert window.btn_settings.text() == "⚙ Impostazioni", f"Got {window.btn_settings.text()}"
    assert window.chk_remember.text() == "Ricorda account", f"Got {window.chk_remember.text()}"
    assert window.lbl_subtitle.text() == "Benvenuto, Allenatore", f"Got {window.lbl_subtitle.text()}"
    print("  ✔ Aggiornamento dinamico a Italiano: SUPERATO")

    # Cambia di nuovo a Inglese e salva
    en_index = -1
    for i in range(dlg.combo_lang.count()):
        if dlg.combo_lang.itemData(i) == "en":
            en_index = i
            break
    dlg.combo_lang.setCurrentIndex(en_index)
    dlg._save_and_close()

    print("[5/5] Verifica persistenza configurazione...")
    cfg_file = BASE_DIR / "config" / "launcher_config.json"
    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg.get("language") == "en", f"Lingua salvata errata: {cfg.get('language')}"
    assert window.btn_play.text() == "PLAY", f"Got {window.btn_play.text()}"
    assert window.btn_settings.text() == "⚙ Settings", f"Got {window.btn_settings.text()}"
    print("  ✔ Persistenza configurazione in config/launcher_config.json: SUPERATO")

    dlg.close()
    window.close()


if __name__ == "__main__":
    test_i18n()
    test_settings_manager_localization()
    test_gui_integration()
    print("\n==========================================")
    print("🎉 TUTTI I TEST i18n & CAMBIO LINGUA SUPERATI!")
    print("==========================================")
