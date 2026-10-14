#!/usr/bin/env python3
"""
Modulo di Gestione del Box Pokémon Virtuale (Storage Fuori Gioco).
Consente di:
1. Archiviare tutte le carte scansionate nel Box Virtuale del profilo allenatore.
2. Visualizzare statistiche, rarità, IV, mosse e ball assegnate.
3. Trasferire chirurgicamente qualsiasi Pokémon dal Box Virtuale al salvataggio del gioco
   (Squadra o Box PC 1..24) tramite PokemonInjector.
"""

import os
import json
import sqlite3
import datetime
import urllib.request
from pathlib import Path
from typing import List, Dict, Optional, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "cards.db"
SCANNED_CARDS_FILE = BASE_DIR / "scanner" / "scanned_cards.json"
SPRITES_DIR = BASE_DIR / "assets" / "sprites"
SPRITES_DIR.mkdir(parents=True, exist_ok=True)

from scanner.tcg_core import TCGCore
from scanner.injector import PokemonInjector


class VirtualBoxManager:
    def __init__(self, username: str = "nemesy2"):
        self.username = username
        self.user_dir = BASE_DIR / "saves" / "profiles" / username
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.box_file = self.user_dir / "virtual_box.json"

        self.tcg_core = TCGCore()
        self.injector = PokemonInjector()
        self.items: List[Dict[str, Any]] = []

        self.load_box()

    def load_box(self):
        """Carica il Box Virtuale o lo popola dalle carte scannerizzate esistenti."""
        if self.box_file.exists():
            try:
                with open(self.box_file, "r", encoding="utf-8") as f:
                    self.items = json.load(f)
                return
            except Exception as e:
                print(f"[VirtualBox] Errore lettura {self.box_file}: {e}")
                self.items = []

        # Se non esiste ancora, auto-migra le carte già scansionate
        self.items = []
        if SCANNED_CARDS_FILE.exists():
            try:
                with open(SCANNED_CARDS_FILE, "r", encoding="utf-8") as f:
                    scanned = json.load(f)
                for key, data in scanned.items():
                    self._import_scanned_entry(key, data)
                self.save_box()
            except Exception as e:
                print(f"[VirtualBox] Errore migrazione scanned_cards: {e}")

    def save_box(self):
        """Salva lo stato corrente del Box Virtuale su disco."""
        try:
            with open(self.box_file, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[VirtualBox] Errore salvataggio {self.box_file}: {e}")

    def _import_scanned_entry(self, key: str, data: dict):
        dex_id = data.get("dex_id", 0)
        species = data.get("species", "Pokémon")
        finish = data.get("finish", "normale")
        set_name = data.get("set", "")
        card_num = str(data.get("number", ""))

        # Cerca dati completi nel database SQLite
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT card_id, release_year, types, hp, rarity FROM cards WHERE dex_id = ? AND card_number = ? LIMIT 1",
            (dex_id, card_num)
        )
        row = cur.fetchone()
        conn.close()

        card_id = row[0] if row else f"custom_{dex_id}_{card_num}"
        release_year = row[1] if row and row[1] else 2020
        types = json.loads(row[2]) if row and row[2] else ["Normal"]
        hp = row[3] if row and row[3] else 60
        rarity = row[4] if row and row[4] else "Common"

        # Genera valutazione TCG
        eval_data = self.tcg_core.evaluate_card(card_id, finish=finish, register=False, bypass_uniqueness=True)
        level = eval_data.get("level", 20) if eval_data.get("success") else 20
        pokeball = eval_data.get("pokeball_name", "Poké Ball") if eval_data.get("success") else "Poké Ball"

        entry = {
            "id": key,
            "card_id": card_id,
            "dex_id": dex_id,
            "species_name": species,
            "level": level,
            "finish": finish,
            "set_name": set_name,
            "card_number": card_num,
            "release_year": release_year,
            "types": types,
            "hp": hp,
            "rarity": rarity,
            "is_shiny": data.get("is_shiny", False),
            "pokeball": pokeball,
            "status": "nel_box",
            "injected_target": None,
            "injected_at": None,
            "date_added": data.get("date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "eval_cache": eval_data if eval_data.get("success") else None
        }
        self.items.append(entry)

    def add_card(self, card_id_or_dict: Any, finish: str = "normale", status: str = "nel_box", injected_target: Optional[str] = None) -> dict:
        """Aggiunge una nuova carta/Pokémon al Box Virtuale."""
        eval_res = self.tcg_core.evaluate_card(card_id_or_dict, finish=finish, register=True, bypass_uniqueness=False)
        if not eval_res.get("success"):
            return eval_res

        dex_id = eval_res["species_id"]
        unique_key = eval_res.get("unique_key") or f"{dex_id}_{finish}_{len(self.items)}"

        entry = {
            "id": unique_key,
            "card_id": eval_res.get("card_id", ""),
            "dex_id": dex_id,
            "species_name": eval_res["species_name"],
            "level": eval_res["level"],
            "finish": finish,
            "set_name": eval_res.get("set_name", ""),
            "card_number": eval_res.get("card_number", ""),
            "release_year": eval_res.get("release_year", 2020),
            "types": eval_res.get("types", ["Normal"]),
            "hp": eval_res.get("hp", 60),
            "rarity": eval_res.get("rarity", "Common"),
            "is_shiny": eval_res.get("is_shiny", False),
            "is_double_shiny": eval_res.get("is_double_shiny", False),
            "pokeball": eval_res.get("pokeball_name", "Poké Ball"),
            "tier": eval_res.get("tier"),
            "tier_name": eval_res.get("tier_name"),
            "era": eval_res.get("era"),
            "era_name": eval_res.get("era_name"),
            "particles": eval_res.get("particles"),
            "title": eval_res.get("title"),
            "ribbon": eval_res.get("ribbon"),
            "ivs": eval_res.get("ivs"),
            "artist": eval_res.get("artist"),
            "met_location": eval_res.get("met_location"),
            "status": status,
            "injected_target": injected_target,
            "injected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == "inviato" else None,
            "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "eval_cache": eval_res
        }
        self.items.insert(0, entry)
        self.save_box()
        return {"success": True, "item": entry}

    def transfer_to_game(self, item_id: str, target_save_path: Optional[str] = None) -> dict:
        """Trasferisce un Pokémon dal Box Virtuale al salvataggio attivo del gioco."""
        target_item = None
        for it in self.items:
            if it["id"] == item_id:
                target_item = it
                break

        if not target_item:
            return {"success": False, "error": "NOT_FOUND", "message": "Pokémon non trovato nel Box Virtuale."}

        dex_id = target_item.get("dex_id", 0)
        if dex_id > 649:
            return {
                "success": False,
                "error": "GEN_6_9_NOT_SUPPORTED",
                "message": (
                    f"<b>{target_item['species_name']}</b> appartiene alla Generazione 6-9 (#{dex_id}).<br><br>"
                    "La ROM di Pokémon Bianco 2 supporta nativamente fino alla 5ª Generazione (Dex #1-#649).<br>"
                    "Sarà trasferibile direttamente nella ROM quando completeremo l'espansione con SDSME (Strada A).<br><br>"
                    "Nel frattempo è custodito nel tuo Box Virtuale!"
                )
            }

        # Ricostruisci o recupera l'eval_res per l'injector
        eval_res = target_item.get("eval_cache")
        if not eval_res or not eval_res.get("success"):
            eval_res = self.tcg_core.evaluate_card(
                target_item.get("card_id"),
                finish=target_item.get("finish", "normale"),
                register=False,
                bypass_uniqueness=True
            )

        if not eval_res or not eval_res.get("success"):
            return {"success": False, "error": "EVAL_FAILED", "message": "Impossibile valutare i dati del Pokémon."}

        # Esegui iniezione
        save_path = Path(target_save_path) if target_save_path else (self.user_dir / "Bianco 2.sav")
        if not save_path.exists():
            save_path = BASE_DIR / "saves" / "Pokémon Bianco 2.sav"

        inject_res = self.injector.inject_pokemon(eval_res, target_save=save_path)
        if inject_res.get("success"):
            target_item["status"] = "inviato"
            target_item["injected_target"] = inject_res.get("target")
            target_item["injected_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_box()

            return {
                "success": True,
                "target": inject_res.get("target"),
                "species_name": target_item["species_name"],
                "level": target_item["level"],
                "message": f"✔ {target_item['species_name']} (Lv.{target_item['level']}) trasferito in {inject_res.get('target')}!"
            }
        else:
            return inject_res

    def delete_item(self, item_id: str) -> bool:
        """Rimuove un Pokémon dal Box Virtuale."""
        for i, it in enumerate(self.items):
            if it["id"] == item_id:
                del self.items[i]
                self.save_box()
                return True
        return False

    def get_party(self, target_save_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recupera l'elenco dei Pokémon attualmente nella squadra (Party) dal salvataggio di gioco."""
        save_path = Path(target_save_path) if target_save_path else (self.user_dir / "Bianco 2.sav")
        if not save_path.exists():
            save_path = BASE_DIR / "saves" / "Pokémon Bianco 2.sav"
        return self.injector.get_party(target_save=save_path)

    def withdraw_from_party_to_box(self, slot_index: int, target_save_path: Optional[str] = None) -> dict:
        """
        Preleva un Pokémon o Uovo dalla squadra in-game e lo deposita nel Box Virtuale,
        aggiornando i restanti slot e ricalcolando tutti i 74 checksum del salvataggio.
        """
        save_path = Path(target_save_path) if target_save_path else (self.user_dir / "Bianco 2.sav")
        if not save_path.exists():
            save_path = BASE_DIR / "saves" / "Pokémon Bianco 2.sav"

        res = self.injector.withdraw_from_party(slot_index, target_save=save_path)
        if not res.get("success"):
            return res

        p = res["pokemon"]
        is_egg = p.get("is_egg", False)
        dex_id = p.get("dex_id", p.get("species_id", 0))
        species_name_raw = p.get("species_name", "Pokémon")
        unique_key = f"withdrawn_{dex_id}_{int(datetime.datetime.now().timestamp())}_{slot_index}"

        # Se è un uovo, usiamo una nomenclatura e grafica ad hoc
        species_name = "Uovo Pokémon" if is_egg else species_name_raw
        item_title = f"Uovo ({species_name_raw})" if is_egg else species_name_raw

        # Costruisci l'entry per il Virtual Box
        entry = {
            "id": unique_key,
            "card_id": f"party_{dex_id}",
            "dex_id": dex_id,
            "species_name": item_title,
            "real_species_name": species_name_raw,
            "nickname": p.get("nickname", species_name_raw),
            "level": p.get("level", 5),
            "finish": "uovo" if is_egg else "squadra",
            "set_name": "Squadra di Gioco",
            "card_number": str(dex_id),
            "release_year": 2012,
            "types": p.get("types", ["Normal"]),
            "hp": p.get("hp_max", 20),
            "rarity": "Speciale" if is_egg else "Squadra",
            "is_shiny": p.get("is_shiny", False),
            "is_egg": is_egg,
            "hatch_cycles": p.get("hatch_cycles", 0),
            "pokeball": "Poké Ball",
            "status": "nel_box",
            "ivs": p.get("ivs"),
            "evs": p.get("evs", {"hp": 0, "atk": 0, "def": 0, "spe": 0, "spa": 0, "spd": 0}),
            "nature": p.get("nature"),
            "nature_id": p.get("nature_id"),
            "ability_name": p.get("ability_name"),
            "ability_id": p.get("ability_id"),
            "moves": p.get("moves"),
            "injected_target": None,
            "injected_at": None,
            "date_added": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "eval_cache": {
                "success": True,
                "species_id": dex_id,
                "species_name": species_name_raw,
                "level": p.get("level", 5),
                "is_shiny": p.get("is_shiny", False),
                "is_egg": is_egg,
                "hatch_cycles": p.get("hatch_cycles", 0),
                "ivs": p.get("ivs", {"hp": 15, "atk": 15, "def": 15, "spe": 15, "spa": 15, "spd": 15}),
                "moves": p.get("moves", []),
                "nature_id": p.get("nature_id"),
                "tier_name": "Uovo Misterioso" if is_egg else "Veterano della Squadra",
                "era_name": "Regione di Unima",
                "pokeball_name": "Poké Ball",
                "pokeball_id": p.get("pokeball_id", 4)
            }
        }
        self.items.insert(0, entry)
        self.save_box()
        return {
            "success": True,
            "item": entry,
            "message": f"✔ {entry['species_name']} (Slot {slot_index + 1}) trasferito nel Box Virtuale con successo!"
        }

    def hatch_egg_in_party(self, slot_index: int, target_save_path: Optional[str] = None) -> dict:
        """Schiude istantaneamente un uovo presente nella squadra del giocatore."""
        save_path = Path(target_save_path) if target_save_path else (self.user_dir / "Bianco 2.sav")
        if not save_path.exists():
            save_path = BASE_DIR / "saves" / "Pokémon Bianco 2.sav"
        return self.injector.hatch_egg_in_party(slot_index, target_save=save_path)

    def get_sprite_path(self, dex_id: int, is_egg: bool = False) -> Optional[Path]:
        """Restituisce il path locale dello sprite, scaricandolo se mancante."""
        if is_egg:
            egg_path = SPRITES_DIR / "egg.png"
            if egg_path.exists():
                return egg_path

        if not dex_id or dex_id <= 0:
            return None

        sprite_path = SPRITES_DIR / f"{dex_id}.png"
        if sprite_path.exists():
            return sprite_path

        try:
            url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{dex_id}.png"
            urllib.request.urlretrieve(url, sprite_path)
            if sprite_path.exists() and sprite_path.stat().st_size > 0:
                return sprite_path
        except Exception:
            pass
        return None

    def get_card_image_path(self, card_id: Optional[str] = None, dex_id: int = 0) -> Optional[Path]:
        """Restituisce il path dell'artwork HD della carta TCG originale (con cache locale)."""
        card_cache_dir = BASE_DIR / "assets" / "card_cache"
        card_cache_dir.mkdir(parents=True, exist_ok=True)

        target_cache_key = None
        image_url = None

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # 1. Prova ricerca per card_id specifico (se non è un id generico)
        if card_id and not str(card_id).startswith(("in_game_", "party_", "custom_")):
            clean_id = str(card_id).replace("/", "_").replace("\\", "_")
            dest = card_cache_dir / f"{clean_id}.png"
            if dest.exists() and dest.stat().st_size > 0:
                conn.close()
                return dest
            cur.execute("SELECT image_url, card_id FROM cards WHERE card_id = ? LIMIT 1", (str(card_id),))
            row = cur.fetchone()
            if row and row[0]:
                image_url = row[0]
                target_cache_key = row[1].replace("/", "_").replace("\\", "_")

        # 2. Se non trovata o id generico di squadra, cerca la migliore carta TCG per dex_id
        if not image_url and dex_id > 0:
            dest_dex = card_cache_dir / f"dex_{dex_id}.png"
            if dest_dex.exists() and dest_dex.stat().st_size > 0:
                conn.close()
                return dest_dex
            cur.execute(
                "SELECT image_url, card_id FROM cards WHERE dex_id = ? AND image_url IS NOT NULL AND image_url != '' ORDER BY release_year DESC LIMIT 1",
                (dex_id,)
            )
            row = cur.fetchone()
            if row and row[0]:
                image_url = row[0]
                target_cache_key = f"dex_{dex_id}"

        conn.close()

        # 3. Scarica se trovata l'URL
        if image_url and target_cache_key:
            dest = card_cache_dir / f"{target_cache_key}.png"
            try:
                req = urllib.request.Request(
                    image_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=6) as resp, open(dest, "wb") as f:
                    f.write(resp.read())
                if dest.exists() and dest.stat().st_size > 0:
                    return dest
            except Exception as e:
                print(f"[VirtualBox] Errore download carta {target_cache_key}: {e}")
        return None

    def ensure_full_eval_data(self, entry: dict) -> dict:
        """Assicura che la card abbia tutti i dettagli calcolati da TCGCore."""
        eval_cache = entry.get("eval_cache") or {}
        if not eval_cache.get("tier_name") or not eval_cache.get("era_name") or not eval_cache.get("ivs"):
            res = self.tcg_core.evaluate_card(
                entry.get("card_id"),
                finish=entry.get("finish", "normale"),
                register=False,
                bypass_uniqueness=True
            )
            if res.get("success"):
                entry["eval_cache"] = res
                eval_cache = res

        if eval_cache:
            modified = False
            fields_to_copy = [
                ("tier", "tier"),
                ("tier_name", "tier_name"),
                ("era", "era"),
                ("era_name", "era_name"),
                ("particles", "particles"),
                ("title", "title"),
                ("ribbon", "ribbon"),
                ("ivs", "ivs"),
                ("artist", "artist"),
                ("met_location", "met_location"),
                ("is_double_shiny", "is_double_shiny"),
            ]
            for key_in_entry, key_in_cache in fields_to_copy:
                if key_in_cache in eval_cache and (key_in_entry not in entry or entry[key_in_entry] is None):
                    entry[key_in_entry] = eval_cache[key_in_cache]
                    modified = True

            if "pokeball_name" in eval_cache and not entry.get("pokeball"):
                entry["pokeball"] = eval_cache["pokeball_name"]
                modified = True

            if modified:
                self.save_box()

        return entry

    def get_stats(self) -> dict:
        total = len(self.items)
        in_box = sum(1 for it in self.items if it.get("status") == "nel_box")
        sent = sum(1 for it in self.items if it.get("status") == "inviato")
        shinies = sum(1 for it in self.items if it.get("is_shiny"))
        return {
            "total": total,
            "in_box": in_box,
            "sent": sent,
            "shinies": shinies
        }
