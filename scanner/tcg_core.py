#!/usr/bin/env python3
import os
import json
import random
import sqlite3
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / 'config' / 'rules.json'
DB_PATH = BASE_DIR / 'database' / 'cards.db'
SCANNED_CARDS_FILE = BASE_DIR / 'scanner' / 'scanned_cards.json'
PENDING_EXPANDED_FILE = BASE_DIR / 'scanner' / 'pending_expanded_pokemon.json'

class TCGCore:
    def __init__(self):
        self.rules = self._load_rules()
        self.scanned_cards = self._load_scanned_cards()

    def _load_rules(self):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_scanned_cards(self):
        if not SCANNED_CARDS_FILE.exists():
            return {}
        try:
            with open(SCANNED_CARDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_scanned_cards(self):
        with open(SCANNED_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.scanned_cards, f, indent=2, ensure_ascii=False)

    def get_card_by_id(self, card_id: str):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT card_id, name, dex_id, set_id, set_name, card_number, total_set_cards, release_year, rarity, supertype, subtypes, types, hp, artist FROM cards WHERE card_id = ?', (card_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'card_id': row[0],
            'name': row[1],
            'dex_id': row[2],
            'set_id': row[3],
            'set_name': row[4],
            'card_number': row[5],
            'total_set_cards': row[6],
            'release_year': row[7],
            'rarity': row[8],
            'supertype': row[9],
            'subtypes': json.loads(row[10]) if row[10] else [],
            'types': json.loads(row[11]) if row[11] else [],
            'hp': row[12],
            'artist': row[13] if len(row) > 13 else None
        }

    def search_cards(self, query: str, limit: int = 10):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        clean = ''.join(c for c in query.lower() if c.isalnum())
        cur.execute('SELECT card_id, name, set_name, card_number, release_year, rarity, dex_id, artist FROM cards WHERE clean_name LIKE ? AND supertype = "Pokémon" ORDER BY release_year ASC LIMIT ?', (f'%{clean}%', limit))
        rows = cur.fetchall()
        conn.close()
        return [
            {'card_id': r[0], 'name': r[1], 'set_name': r[2], 'card_number': r[3], 'release_year': r[4], 'rarity': r[5], 'dex_id': r[6], 'artist': r[7]}
            for r in rows
        ]

    def check_uniqueness(self, dex_id: int, set_id: str, card_number: str, finish: str):
        key = f'{dex_id}_{set_id}_{card_number}_{finish.lower().replace(" ", "_")}'
        return key not in self.scanned_cards, key

    def determine_card_tier(self, card_data: dict, finish: str):
        rarity = card_data.get('rarity', 'Common') or 'Common'
        subtypes = card_data.get('subtypes', []) or []
        
        if finish.lower() in ['reverse holo', 'reverse']:
            return 'tier_2', self.rules['card_rarity_tiers']['tier_2']

        if any(w in rarity for w in ['Secret', 'Gold', 'Special Illustration', 'Hyper']) or 'Gold Star' in card_data['name']:
            return 'tier_6', self.rules['card_rarity_tiers']['tier_6']

        if any(w in subtypes for w in ['MEGA', 'VMAX', 'VSTAR', 'TAG TEAM']) or 'Full Art' in rarity or 'Illustration Rare' in rarity:
            return 'tier_5', self.rules['card_rarity_tiers']['tier_5']

        if any(w in subtypes for w in ['EX', 'GX', 'V', 'ex']):
            return 'tier_4', self.rules['card_rarity_tiers']['tier_4']

        if 'Shiny' in rarity or 'Vault' in card_data.get('set_name', ''):
            return 'tier_3_5', self.rules['card_rarity_tiers']['tier_3_5']

        if any(w in subtypes for w in ['BREAK', 'LV.X', 'Prime', 'LEGEND']) or 'Radiant' in card_data['name'] or 'Amazing' in rarity:
            return 'tier_3', self.rules['card_rarity_tiers']['tier_3']

        if 'Holo' in rarity:
            return 'tier_2', self.rules['card_rarity_tiers']['tier_2']

        return 'tier_1', self.rules['card_rarity_tiers']['tier_1']

    def determine_historical_era(self, release_year: int):
        eras = self.rules['historical_eras']
        for era_key, era_info in sorted(eras.items(), key=lambda x: x[1]['years'][0], reverse=True):
            y_min, y_max = era_info['years']
            if y_min <= release_year <= y_max:
                return era_key, era_info
        return 'tier_1', eras['tier_1']

    def evaluate_card(self, card_data, finish: str = 'normale', register: bool = True, bypass_uniqueness: bool = False) -> dict:
        if isinstance(card_data, str):
            card_data = self.get_card_by_id(card_data)
        elif isinstance(card_data, dict) and 'subtypes' not in card_data:
            card_data = self.get_card_by_id(card_data['card_id'])
            
        if not card_data:
            return {'success': False, 'error': 'CARD_NOT_FOUND', 'message': 'Carta non trovata nel database TCG.'}

        dex_id = card_data['dex_id']
        set_id = card_data['set_id']
        card_num = card_data['card_number']
        release_year = card_data['release_year'] or 2020
        
        if not bypass_uniqueness:
            is_unique, unique_key = self.check_uniqueness(dex_id, set_id, card_num, finish)
            if not is_unique:
                prev = self.scanned_cards[unique_key]
                return {
                    'success': False,
                    'error': 'DUPLICATE',
                    'message': f'Carta [{card_data["name"]} #{card_num} - {finish.upper()}] gia riscattata il {prev.get("date", "in passato")}!'
                }
        else:
            _, unique_key = self.check_uniqueness(dex_id, set_id, card_num, finish)

        tier_key, tier_info = self.determine_card_tier(card_data, finish)
        era_key, era_info = self.determine_historical_era(release_year)

        is_legendary = dex_id in self.rules['legendary_nerf']['legendary_ids']
        if is_legendary and self.rules['legendary_nerf']['enabled']:
            level = self.rules['legendary_nerf']['sealed_level']
            sealed_desc = 'TUTTI I POTERI ASSOPITI (Livello Sigillato a Lv. 5, crescita lenta)'
        else:
            level = random.randint(tier_info['min_level'], tier_info['max_level'])
            sealed_desc = None

        ivs = [random.randint(0, 31) for _ in range(6)]
        guaranteed_31_count = tier_info['guaranteed_iv_31']

        is_card_shiny = tier_info.get('is_card_shiny', False) or ('Shining' in card_data['name'])
        lucky_shiny_roll = random.random() < self.rules['shiny_mechanics']['base_random_shiny_chance']
        
        is_shiny = is_card_shiny or lucky_shiny_roll
        is_double_shiny = False
        double_shiny_data = None

        if is_card_shiny and lucky_shiny_roll:
            is_double_shiny = True
            double_shiny_cfg = self.rules['shiny_mechanics']['double_shiny']
            guaranteed_31_count += double_shiny_cfg['bonus_guaranteed_iv_31']
            double_shiny_data = {
                'achievement': double_shiny_cfg['achievement_name'],
                'particle': double_shiny_cfg['particle_effect'],
                'ribbon': double_shiny_cfg['ribbon']
            }

        chosen_indices = random.sample(range(6), min(6, guaranteed_31_count))
        for idx in chosen_indices:
            ivs[idx] = 31

        has_hidden_ability = random.random() < tier_info['hidden_ability_chance']

        result = {
            'success': True,
            'unique_key': unique_key,
            'species_id': dex_id,
            'species_name': card_data['name'],
            'set_name': card_data['set_name'],
            'card_number': card_num,
            'release_year': release_year,
            'artist': card_data.get('artist'),
            'finish': finish.capitalize(),
            'tier': tier_key,
            'tier_name': tier_info['name'],
            'era': era_key,
            'era_name': era_info['era_name'],
            
            'level': level,
            'ivs': {
                'hp': ivs[0], 'atk': ivs[1], 'def': ivs[2],
                'spa': ivs[3], 'spd': ivs[4], 'spe': ivs[5]
            },
            'hidden_ability': has_hidden_ability,
            'is_shiny': is_shiny,
            'is_double_shiny': is_double_shiny,
            'double_shiny_details': double_shiny_data,
            'is_legendary_sealed': is_legendary,
            'legendary_notes': sealed_desc,

            'pokeball_name': era_info['pokeball_name'],
            'pokeball_id': era_info['pokeball_id'],
            'particles': era_info['particles'],
            'title': era_info['title'],
            'ribbon': era_info['ribbon'],
            'met_location': f'Eredita del {release_year} — {card_data["set_name"]} #{card_num}',
            
            'is_gen_1_5': dex_id <= 649,
            'date_scanned': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if register:
            self.scanned_cards[unique_key] = {
                'species': card_data['name'],
                'dex_id': dex_id,
                'set': card_data['set_name'],
                'number': card_num,
                'finish': finish,
                'date': result['date_scanned'],
                'is_shiny': is_shiny
            }
            self._save_scanned_cards()

            if dex_id > 649:
                self._save_pending_expanded(result)

        return result

    def _save_pending_expanded(self, pokemon_res):
        pending = []
        if PENDING_EXPANDED_FILE.exists():
            try:
                with open(PENDING_EXPANDED_FILE, 'r', encoding='utf-8') as f:
                    pending = json.load(f)
            except Exception:
                pending = []
        pending.append(pokemon_res)
        with open(PENDING_EXPANDED_FILE, 'w', encoding='utf-8') as f:
            json.dump(pending, f, indent=2, ensure_ascii=False)
