#!/usr/bin/env python3
"""
Gestore della ROM per il Client.
Verifica la presenza del file .nds, ne valida l'integrità e memorizza
il percorso configurato dall'utente senza includere ROM protette nel software.
"""

import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "launcher_config.json"
DEFAULT_MODIFIED_ROM = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"


class ROMManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if not CONFIG_FILE.exists():
            default_cfg = {
                "rom_path": str(DEFAULT_MODIFIED_ROM) if DEFAULT_MODIFIED_ROM.exists() else "",
                "resolution": "1080p",
                "fullscreen": False,
                "remember_user": True,
                "last_username": ""
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_cfg, f, indent=2)
            return default_cfg

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"rom_path": "", "resolution": "1080p"}

    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def get_rom_path(self) -> str:
        path = self.config.get("rom_path", "")
        if path and Path(path).exists():
            return path
        # Fallback automatico su quella modificata di progetto se presente
        if DEFAULT_MODIFIED_ROM.exists():
            self.set_rom_path(str(DEFAULT_MODIFIED_ROM))
            return str(DEFAULT_MODIFIED_ROM)
        return ""

    def set_rom_path(self, path_str: str) -> bool:
        p = Path(path_str)
        if p.exists() and p.suffix.lower() == ".nds":
            self.config["rom_path"] = str(p.resolve())
            self._save_config()
            return True
        return False

    def is_rom_ready(self) -> bool:
        r_path = self.get_rom_path()
        return bool(r_path and Path(r_path).exists() and Path(r_path).stat().st_size > 10 * 1024 * 1024)

    def get_resolution(self) -> str:
        return self.config.get("resolution", "1080p")

    def set_resolution(self, res: str):
        self.config["resolution"] = res
        self._save_config()

    def set_last_user(self, username: str):
        self.config["last_username"] = username
        self._save_config()

    def get_last_user(self) -> str:
        return self.config.get("last_username", "")

