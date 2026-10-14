#!/usr/bin/env python3
"""
Gestore Account e Profili Locali in stile PokeMMO.
Gestisce autenticazione sicura (PBKDF2/SHA256) e associazione a salvataggi
personali isolati per ciascun giocatore (saves/profiles/<username>/save.sav).
"""

import os
import json
import hashlib
import secrets
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
PROFILES_DIR = BASE_DIR / "saves" / "profiles"
ACCOUNTS_FILE = CONFIG_DIR / "accounts.json"
TEMPLATE_SAV = BASE_DIR / "saves" / "Pokémon Bianco 2.sav"


class AccountManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        self.accounts = self._load_accounts()

    def _load_accounts(self) -> dict:
        if not ACCOUNTS_FILE.exists():
            return {}
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_accounts(self):
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.accounts, f, indent=2, ensure_ascii=False)

    def _hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        if salt is None:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()
        return pwd_hash, salt

    def register(self, username: str, password: str) -> dict:
        username = username.strip()
        if not username:
            return {"success": False, "error_code": "status_user_empty", "error": "Il nome utente non può essere vuoto."}
        if len(username) < 3:
            return {"success": False, "error_code": "status_user_min_len", "error": "Il nome utente deve avere almeno 3 caratteri."}
        if len(password) < 4:
            return {"success": False, "error_code": "status_pwd_min_len", "error": "La password deve avere almeno 4 caratteri."}

        key = username.lower()
        if key in self.accounts:
            return {"success": False, "error_code": "status_user_exists", "error": "Nome utente già esistente."}

        pwd_hash, salt = self._hash_password(password)
        
        # Prepara la cartella del profilo e il salvataggio personale
        user_dir = PROFILES_DIR / key
        user_dir.mkdir(parents=True, exist_ok=True)
        user_sav = user_dir / f"{key}_bianco2.sav"
        
        if not user_sav.exists() and TEMPLATE_SAV.exists():
            shutil.copy2(TEMPLATE_SAV, user_sav)

        self.accounts[key] = {
            "display_name": username,
            "hash": pwd_hash,
            "salt": salt,
            "created_at": str(Path(__file__).stat().st_mtime),
            "save_file": str(user_sav)
        }
        self._save_accounts()

        return {
            "success": True,
            "username": username,
            "save_file": str(user_sav)
        }

    def login(self, username: str, password: str) -> dict:
        username = username.strip()
        key = username.lower()
        if key not in self.accounts:
            return {"success": False, "error_code": "status_user_not_found", "error": "Utente non trovato."}

        user_data = self.accounts[key]
        expected_hash, _ = self._hash_password(password, user_data["salt"])
        if expected_hash != user_data["hash"]:
            return {"success": False, "error_code": "status_wrong_pwd", "error": "Password errata."}

        user_sav = Path(user_data.get("save_file", PROFILES_DIR / key / f"{key}_bianco2.sav"))
        if not user_sav.exists() and TEMPLATE_SAV.exists():
            user_sav.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(TEMPLATE_SAV, user_sav)

        return {
            "success": True,
            "username": user_data.get("display_name", username),
            "save_file": str(user_sav)
        }

    def list_accounts(self) -> list:
        return [acc["display_name"] for acc in self.accounts.values()]

