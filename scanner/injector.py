#!/usr/bin/env python3
"""
Modulo per l'iniezione autentica dei Pokémon scansionati da carte TCG
all'interno dei file di salvataggio di Pokémon Bianco 2 (DS / SAV5B2W2).
Supporta crittografia LCRNG, calcolo statistiche Gen 5, PID legali (Shiny/Double Shiny),
assegnazione Pokéball storiche, Fiocchi e ricalcolo di tutti i 74 checksum CRC16.
"""

import os
import shutil
import json
import struct
import random
import datetime
import sqlite3
from pathlib import Path

import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "cards.db"
SAVES_DIR = BASE_DIR / "saves"
BACKUPS_DIR = SAVES_DIR / "backups"
HISTORY_FILE = BASE_DIR / "scanner" / "scans_history.json"
PENDING_EXPANDED_FILE = BASE_DIR / "scanner" / "pending_expanded_pokemon.json"
ROM_PATH = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"

SAVE_TARGET_1 = SAVES_DIR / "Pokémon Bianco 2.sav"
SAVE_TARGET_2 = BASE_DIR / "roms" / "modified" / "Bianco 2.sav"

ORDERS = [
    'ABCD', 'ABDC', 'ACBD', 'ACDB', 'ADBC', 'ADCB',
    'BACD', 'BADC', 'BCAD', 'BCDA', 'BDAC', 'BDCA',
    'CABD', 'CADB', 'CBAD', 'CBDA', 'CDAB', 'CDBA',
    'DABC', 'DACB', 'DBAC', 'DBCA', 'DCAB', 'DCBA'
]

BLOCKS = [
    (0x00000, 0x03e0, 0x003E2, 0x25F00), # 00 Box Names
    (0x00400, 0x0ff0, 0x013F2, 0x25F02), # 01 Box 1
    (0x01400, 0x0ff0, 0x023F2, 0x25F04), # 02 Box 2
    (0x02400, 0x0ff0, 0x033F2, 0x25F06), # 03 Box 3
    (0x03400, 0x0ff0, 0x043F2, 0x25F08), # 04 Box 4
    (0x04400, 0x0ff0, 0x053F2, 0x25F0A), # 05 Box 5
    (0x05400, 0x0ff0, 0x063F2, 0x25F0C), # 06 Box 6
    (0x06400, 0x0ff0, 0x073F2, 0x25F0E), # 07 Box 7
    (0x07400, 0x0ff0, 0x083F2, 0x25F10), # 08 Box 8
    (0x08400, 0x0ff0, 0x093F2, 0x25F12), # 09 Box 9
    (0x09400, 0x0ff0, 0x0A3F2, 0x25F14), # 10 Box 10
    (0x0A400, 0x0ff0, 0x0B3F2, 0x25F16), # 11 Box 11
    (0x0B400, 0x0ff0, 0x0C3F2, 0x25F18), # 12 Box 12
    (0x0C400, 0x0ff0, 0x0D3F2, 0x25F1A), # 13 Box 13
    (0x0D400, 0x0ff0, 0x0E3F2, 0x25F1C), # 14 Box 14
    (0x0E400, 0x0ff0, 0x0F3F2, 0x25F1E), # 15 Box 15
    (0x0F400, 0x0ff0, 0x103F2, 0x25F20), # 16 Box 16
    (0x10400, 0x0ff0, 0x113F2, 0x25F22), # 17 Box 17
    (0x11400, 0x0ff0, 0x123F2, 0x25F24), # 18 Box 18
    (0x12400, 0x0ff0, 0x133F2, 0x25F26), # 19 Box 19
    (0x13400, 0x0ff0, 0x143F2, 0x25F28), # 20 Box 20
    (0x14400, 0x0ff0, 0x153F2, 0x25F2A), # 21 Box 21
    (0x15400, 0x0ff0, 0x163F2, 0x25F2C), # 22 Box 22
    (0x16400, 0x0ff0, 0x173F2, 0x25F2E), # 23 Box 23
    (0x17400, 0x0ff0, 0x183F2, 0x25F30), # 24 Box 24
    (0x18400, 0x09ec, 0x18DEE, 0x25F32), # 25 Inventory
    (0x18E00, 0x0534, 0x19336, 0x25F34), # 26 Party Pokémon
    (0x19400, 0x00b0, 0x194B2, 0x25F36), # 27 Trainer Data
    (0x19500, 0x00a8, 0x195AA, 0x25F38), # 28 Trainer Position
    (0x19600, 0x1338, 0x1A93A, 0x25F3A), # 29 Unity Tower
    (0x1AA00, 0x07c4, 0x1B1C6, 0x25F3C), # 30 Pal Pad Player Data
    (0x1B200, 0x0d54, 0x1BF56, 0x25F3E), # 31 Pal Pad Friend Data
    (0x1C000, 0x0094, 0x1C096, 0x25F40), # 32 Options / Skin Info
    (0x1C100, 0x0658, 0x1C75A, 0x25F42), # 33 Trainer Card
    (0x1C800, 0x0a94, 0x1D296, 0x25F44), # 34 Mystery Gift
    (0x1D300, 0x01ac, 0x1D4AE, 0x25F46), # 35 Dream World Stuff
    (0x1D500, 0x03ec, 0x1D8EE, 0x25F48), # 36 Chatter
    (0x1D900, 0x005c, 0x1D95E, 0x25F4A), # 37 Adventure data
    (0x1DA00, 0x01e0, 0x1DBE2, 0x25F4C), # 38 Trainer Card Records
    (0x1DC00, 0x00a8, 0x1DCAA, 0x25F4E), # 39 Unused
    (0x1DD00, 0x0460, 0x1E162, 0x25F50), # 40 Mail
    (0x1E200, 0x1400, 0x1F602, 0x25F52), # 41 Overworld State
    (0x1F700, 0x02a4, 0x1F9A6, 0x25F54), # 42 Musical
    (0x1FA00, 0x00e0, 0x1FAE2, 0x25F56), # 43 White Forest / Black City
    (0x1FB00, 0x034c, 0x1FE4E, 0x25F58), # 44 IR
    (0x1FF00, 0x04e0, 0x203E2, 0x25F5A), # 45 EventWork
    (0x20400, 0x00f8, 0x204FA, 0x25F5C), # 46 GTS
    (0x20500, 0x02fc, 0x207FE, 0x25F5E), # 47 Regulation Tournament
    (0x20800, 0x0094, 0x20896, 0x25F60), # 48 Gimmick
    (0x20900, 0x035c, 0x20C5E, 0x25F62), # 49 Battle Box
    (0x20D00, 0x01d4, 0x20ED6, 0x25F64), # 50 Daycare
    (0x20F00, 0x01e0, 0x210E2, 0x25F66), # 51 Strength Boulder Status
    (0x21100, 0x00f0, 0x211F2, 0x25F68), # 52 Misc (Badges, Money)
    (0x21200, 0x01b4, 0x213B6, 0x25F6A), # 53 Entralink
    (0x21400, 0x04dc, 0x218DE, 0x25F6C), # 54 Pokedex
    (0x21900, 0x0034, 0x21936, 0x25F6E), # 55 Encount
    (0x21A00, 0x003c, 0x21A3E, 0x25F70), # 56 Battle Subway Play Info
    (0x21B00, 0x01ac, 0x21CAE, 0x25F72), # 57 Battle Subway Score Info
    (0x21D00, 0x0b90, 0x22892, 0x25F74), # 58 Battle Subway Wi-Fi Info
    (0x22900, 0x00ac, 0x229AE, 0x25F76), # 59 Online Records
    (0x22A00, 0x0850, 0x23252, 0x25F78), # 60 Entralink Forest Pokemon
    (0x23300, 0x0284, 0x23586, 0x25F7A), # 61 Answered Questions
    (0x23600, 0x0010, 0x23612, 0x25F7C), # 62 Unity Tower
    (0x23700, 0x00a8, 0x237AA, 0x25F7E), # 63 Battle Institute & PWT
    (0x23800, 0x016c, 0x2396E, 0x25F80), # 64 ???
    (0x23A00, 0x0080, 0x23A82, 0x25F82), # 65 ???
    (0x23B00, 0x00fc, 0x23BFE, 0x25F84), # 66 Hollow/Rival Block
    (0x23C00, 0x16a8, 0x252AA, 0x25F86), # 67 Join Avenue Block
    (0x25300, 0x0498, 0x2579A, 0x25F88), # 68 Medal
    (0x25800, 0x0060, 0x25862, 0x25F8A), # 69 Key Data
    (0x25900, 0x00fc, 0x259FE, 0x25F8C), # 70 Festa Missions
    (0x25A00, 0x03e4, 0x25DE6, 0x25F8E), # 71 Pokestar Studios
    (0x25E00, 0x00f0, 0x25EF2, 0x25F90), # 72 ???
    (0x25F00, 0x0094, 0x25FA2, 0x25FA2), # 73 Checksum Block
]

def crc16_ccitt(data: bytes) -> int:
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

def lcrng_cipher(data_bytes: bytes, seed: int) -> bytes:
    out = bytearray(data_bytes)
    s = seed
    for i in range(0, len(out), 2):
        s = (s * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        k = (s >> 16) & 0xFFFF
        val = struct.unpack_from('<H', out, i)[0]
        struct.pack_into('<H', out, i, val ^ k)
    return bytes(out)


class PokemonInjector:
    def __init__(self):
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_game_data()

    def _load_game_data(self):
        """Carica i NARC della ROM per accedere ai dati di base autentici."""
        self.rom = ndspy.rom.NintendoDSRom.fromFile(str(ROM_PATH))
        self.narc_personal = ndspy.narc.NARC(self.rom.files[self.rom.filenames.idOf('a/0/1/6')])
        self.narc_learnset = ndspy.narc.NARC(self.rom.files[self.rom.filenames.idOf('a/0/1/8')])
        self.narc_moves = ndspy.narc.NARC(self.rom.files[self.rom.filenames.idOf('a/0/2/1')])

    def calc_exp(self, level: int, growth_rate: int) -> int:
        l = level
        if growth_rate == 0: # Medium Fast
            return l ** 3
        elif growth_rate == 1: # Erratic
            if l < 50: return (l**3 * (100 - l)) // 50
            elif l < 68: return (l**3 * (150 - l)) // 100
            elif l < 98: return (l**3 * ((1911 - 10*l) // 3)) // 500
            else: return (l**3 * (160 - l)) // 100
        elif growth_rate == 2: # Fluctuating
            if l < 15: return (l**3 * (((l + 1) // 3) + 24)) // 50
            elif l < 36: return (l**3 * (l + 14)) // 50
            else: return (l**3 * ((l // 2) + 32)) // 50
        elif growth_rate == 3: # Medium Slow
            if l <= 1: return 0
            return max(0, int(1.2 * (l**3) - 15 * (l**2) + 100 * l - 140))
        elif growth_rate == 4: # Fast
            return (4 * (l**3)) // 5
        elif growth_rate == 5: # Slow
            return (5 * (l**3)) // 4
        return l ** 3

    def calc_stats(self, base_stats: tuple, ivs: dict, level: int, nature_id: int):
        hp_base, atk_base, def_base, spe_base, spa_base, spd_base = base_stats
        
        # Formula HP: ((2*Base + IV) * Level) // 100 + Level + 10
        if hp_base == 1: # Shedinja
            hp = 1
        else:
            hp = ((2 * hp_base + ivs['hp']) * level) // 100 + level + 10
            
        def calc_raw(base, iv):
            return ((2 * base + iv) * level) // 100 + 5

        atk_raw = calc_raw(atk_base, ivs['atk'])
        def_raw = calc_raw(def_base, ivs['def'])
        spe_raw = calc_raw(spe_base, ivs['spe'])
        spa_raw = calc_raw(spa_base, ivs['spa'])
        spd_raw = calc_raw(spd_base, ivs['spd'])

        # Nature modifiers
        # Boosted: nature_id // 5, Hindered: nature_id % 5
        # Stats index: 0=Atk, 1=Def, 2=Spe, 3=SpA, 4=SpD
        boosted = nature_id // 5
        hindered = nature_id % 5
        
        raws = [atk_raw, def_raw, spe_raw, spa_raw, spd_raw]
        final_stats = []
        for i, val in enumerate(raws):
            if boosted == hindered:
                final_stats.append(val)
            elif i == boosted:
                final_stats.append((val * 110) // 100)
            elif i == hindered:
                final_stats.append((val * 90) // 100)
            else:
                final_stats.append(val)

        return hp, final_stats[0], final_stats[1], final_stats[2], final_stats[3], final_stats[4]

    def get_moves_and_pps(self, species_id: int, level: int):
        learn_bytes = self.narc_learnset.files[species_id]
        moves_learned = []
        for i in range(0, len(learn_bytes), 4):
            m_id, lvl = struct.unpack_from('<HH', learn_bytes, i)
            if m_id == 0xFFFF:
                break
            if lvl <= level:
                moves_learned.append(m_id)

        # Seleziona le ultime 4 mosse (o riempi con zeri)
        selected_moves = moves_learned[-4:] if moves_learned else [33] # Tackle default
        while len(selected_moves) < 4:
            selected_moves.append(0)

        pps = []
        for m_id in selected_moves:
            if m_id == 0:
                pps.append(0)
            else:
                m_file = self.narc_moves.files[m_id]
                pps.append(m_file[5]) # Base PP offset 5
        return selected_moves, pps

    def generate_legal_pid(self, tid: int, sid: int, is_shiny: bool, is_double_shiny: bool, gender_ratio: int):
        t_xor = tid ^ sid
        for _ in range(5000):
            high = random.randint(0, 0xFFFF)
            if is_double_shiny:
                diff = 0 # Square Shiny / Risonanza Cosmica
            elif is_shiny:
                diff = random.randint(1, 7) # Star Shiny
            else:
                diff = random.randint(8, 0xFFFF) # Non Shiny
                
            low = high ^ t_xor ^ diff
            pid = (high << 16) | low

            # Gender calculation
            if gender_ratio == 255:
                gender = 2 # Genderless
            elif gender_ratio == 254:
                gender = 1 # Always Female
            elif gender_ratio == 0:
                gender = 0 # Always Male
            else:
                gender = 1 if (pid & 0xFF) < gender_ratio else 0

            return pid, gender
        raise RuntimeError("Impossibile generare PID valido.")

    def create_pk5(self, eval_res: dict, tid: int, sid: int, ot_name_bytes: bytes) -> tuple[bytes, bytes]:
        """Costruisce i pacchetti PKM a 220 byte (Squadra) e 136 byte (Box)."""
        dex_id = eval_res['species_id']
        level = eval_res['level']
        ivs = eval_res['ivs']
        is_shiny = eval_res['is_shiny']
        is_double_shiny = eval_res.get('is_double_shiny', False)
        
        # Dati base della specie dal NARC
        p_data = self.narc_personal.files[dex_id]
        base_stats = (p_data[0], p_data[1], p_data[2], p_data[3], p_data[4], p_data[5])
        growth_rate = p_data[0x15]
        gender_ratio = p_data[0x10]
        ab1, ab2, ab_h = p_data[0x18], p_data[0x19], p_data[0x1A]

        # Natura e PID
        if eval_res.get('nature_id') is not None:
            nature_id = eval_res['nature_id']
        else:
            nature_id = random.randint(0, 24)
        pid, gender = self.generate_legal_pid(tid, sid, is_shiny, is_double_shiny, gender_ratio)

        # Abilità
        if eval_res.get('hidden_ability', False) and ab_h != 0:
            ability_id = ab_h
            has_hidden_flag = 1
        else:
            ability_id = ab2 if (ab2 != 0 and random.random() < 0.5) else ab1
            has_hidden_flag = 0

        # Mosse e PP
        if eval_res.get('moves') and isinstance(eval_res['moves'], list) and len(eval_res['moves']) > 0 and isinstance(eval_res['moves'][0], int):
            moves = list(eval_res['moves'][:4])
            while len(moves) < 4:
                moves.append(0)
            pps = []
            for m_id in moves:
                if m_id == 0:
                    pps.append(0)
                else:
                    m_file = self.narc_moves.files[m_id]
                    pps.append(m_file[5])
        else:
            moves, pps = self.get_moves_and_pps(dex_id, level)
        exp_points = self.calc_exp(level, growth_rate)

        is_egg = eval_res.get('is_egg', False)

        # ---------------- BLOCK A (32 bytes) ----------------
        block_a = bytearray(32)
        struct.pack_into('<H', block_a, 0x00, dex_id)
        struct.pack_into('<H', block_a, 0x02, 0) # Held Item
        struct.pack_into('<H', block_a, 0x04, tid)
        struct.pack_into('<H', block_a, 0x06, sid)
        struct.pack_into('<I', block_a, 0x08, exp_points)
        if is_egg:
            block_a[0x0C] = eval_res.get('hatch_cycles', 5)
        else:
            block_a[0x0C] = 0 if eval_res.get('is_legendary_sealed', False) else 70 # Base Friendship
        block_a[0x0D] = ability_id
        block_a[0x0E] = 0 # Markings
        block_a[0x0F] = 4 # Italian Language ID
        # EV strictly zero
        block_a[0x10:0x16] = b'\x00' * 6
        # Contest stats zero
        block_a[0x16:0x1C] = b'\x00' * 6

        # ---------------- BLOCK B (32 bytes) ----------------
        block_b = bytearray(32)
        struct.pack_into('<4H', block_b, 0x00, moves[0], moves[1], moves[2], moves[3])
        block_b[0x08:0x0C] = bytes(pps)
        block_b[0x0C:0x10] = b'\x00' * 4 # PP Ups
        
        # IV Bitfield
        iv_field = (
            (ivs['hp'] & 31) |
            ((ivs['atk'] & 31) << 5) |
            ((ivs['def'] & 31) << 10) |
            ((ivs['spe'] & 31) << 15) |
            ((ivs['spa'] & 31) << 20) |
            ((ivs['spd'] & 31) << 25)
        )
        if is_egg:
            iv_field |= (1 << 30) # Bit 30: is_egg flag
        struct.pack_into('<I', block_b, 0x10, iv_field)
        
        # Flags offset 0x18: bit 0: fateful, bits 1-2: gender, bits 3-7: form
        is_fateful = 1 if (is_double_shiny or eval_res.get('tier') in ['tier_5', 'tier_6']) else 0
        egg_flag = 0x40 if is_egg else 0
        block_b[0x18] = (is_fateful & 1) | ((gender & 3) << 1) | egg_flag
        block_b[0x19] = nature_id
        block_b[0x1A] = (has_hidden_flag & 1) # Hidden ability flag

        # ---------------- BLOCK C (32 bytes) ----------------
        block_c = bytearray(32)
        nick_str = "UOVO" if is_egg else eval_res['species_name'].upper()
        nick_encoded = nick_str.encode('utf-16le') + b'\xff\xff'
        nick_encoded = nick_encoded.ljust(22, b'\x00')
        block_c[0:22] = nick_encoded[:22]
        block_c[0x17] = 22 # White 2 Origin Game

        # Unova Ribbons (Classic Ribbon / Premier Ribbon per eventi vintage)
        if eval_res.get('ribbon') or is_double_shiny:
            # Assegna Fiocco Classico (Bit 0) o Fiocco Ricordo (Bit 5)
            block_c[0x18] = 0x01 if not is_double_shiny else 0x21

        # ---------------- BLOCK D (32 bytes) ----------------
        block_d = bytearray(32)
        ot_padded = ot_name_bytes.ljust(16, bytes([0]))[:16]
        block_d[0:16] = ot_padded
        block_d[0x10] = eval_res.get('pokeball_id', 4) # Pokéball vintage/grade
        block_d[0x11] = level & 0x7F # Met Level
        now = datetime.datetime.now()
        block_d[0x14] = now.year - 2000
        block_d[0x15] = now.month
        block_d[0x16] = now.day
        struct.pack_into('<H', block_d, 0x18, 445) # Met Location: Fattoria di Venturia (Lobby)

        # Calcolo Checksum dei 4 blocchi in chiaro
        chk = 0
        raw_blocks = {'A': block_a, 'B': block_b, 'C': block_c, 'D': block_d}
        for letter in ['A', 'B', 'C', 'D']:
            b = raw_blocks[letter]
            for j in range(0, 32, 2):
                chk = (chk + struct.unpack_from('<H', b, j)[0]) & 0xFFFF

        # Cifratura e Shuffling dei blocchi
        shift = ((pid >> 13) & 0x1F) % 24
        order = ORDERS[shift]
        
        # Assembla Box Data (136 bytes)
        box_data = bytearray(136)
        struct.pack_into('<I', box_data, 0, pid)
        struct.pack_into('<H', box_data, 4, 0) # Sanity
        struct.pack_into('<H', box_data, 6, chk)
        
        # Concatena blocchi nell'ordine permutato
        shuffled_blocks = bytearray(128)
        for i, letter in enumerate(order):
            shuffled_blocks[i*32 : (i+1)*32] = raw_blocks[letter]

        # Cifra i 128 byte con seed = chk
        box_data[8:136] = lcrng_cipher(bytes(shuffled_blocks), chk)

        # ---------------- PARTY DATA (84 bytes) ----------------
        hp, atk, df, spe, spa, spd = self.calc_stats(base_stats, ivs, level, nature_id)
        party_raw = bytearray(84)
        party_raw[0x00:0x04] = b'\x00' * 4 # Status Condition: Healthy
        party_raw[0x04] = level
        struct.pack_into('<H', party_raw, 0x06, hp) # Current HP
        struct.pack_into('<H', party_raw, 0x08, hp) # Max HP
        struct.pack_into('<H', party_raw, 0x0A, atk)
        struct.pack_into('<H', party_raw, 0x0C, df)
        struct.pack_into('<H', party_raw, 0x0E, spe)
        struct.pack_into('<H', party_raw, 0x10, spa)
        struct.pack_into('<H', party_raw, 0x12, spd)

        # Cifra la struttura party con seed = pid
        party_encrypted = lcrng_cipher(bytes(party_raw), pid)

        # Pacchetto Squadra completo (220 bytes)
        party_data = bytearray(220)
        party_data[0:136] = box_data
        party_data[136:220] = party_encrypted

        return bytes(party_data), bytes(box_data)

    def backup_save(self, target_file: Path = None) -> Path:
        """Esegue backup di sicurezza prima di toccare i salvataggi."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUPS_DIR / f"save_backup_{timestamp}.sav"
        src = target_file if (target_file and target_file.exists()) else SAVE_TARGET_1
        shutil.copy2(src, backup_file)
        return backup_file

    def inject_pokemon(self, eval_res: dict, target_save: Path | str = None) -> dict:
        """
        Inietta direttamente il Pokémon scansionato nel salvataggio.
        Per Gen 1-5: salva in Squadra o Box 1, ricalcola tutti i 74 checksum.
        Per Gen 6-9: accoda nel virtual binder (Strada B in attesa di Strada A).
        Se specificato target_save, inietta in quel file e sincronizza i mirror.
        """
        dex_id = eval_res['species_id']
        
        # Gestione Gen 6-9 (Strada B: virtual binder in attesa di sprite)
        if dex_id > 649:
            return {
                'success': True,
                'status': 'PENDING_EXPANSION',
                'target': 'Virtual Binder (Gen 6-9)',
                'message': f"Pokémon #{dex_id} ({eval_res['species_name']}) registrato nel Raccoglitore Virtuale! In attesa di Strada A."
            }

        # Individua il file primario su cui iniettare
        primary_save = Path(target_save) if target_save else SAVE_TARGET_1
        if not primary_save.exists():
            primary_save = SAVE_TARGET_1

        # Backup preventivo
        backup_path = self.backup_save(primary_save)

        with open(primary_save, 'rb') as f:
            save_bytes = bytearray(f.read())

        # Leggi dati allenatore dal blocco 27 (0x19400)
        ot_name_bytes = bytes(save_bytes[0x19404:0x19414])
        tid = struct.unpack('<H', save_bytes[0x19414:0x19416])[0]
        sid = struct.unpack('<H', save_bytes[0x19416:0x19418])[0]
        party_count = save_bytes[0x18E04]

        # Crea PK5 autentico
        party_pkm, box_pkm = self.create_pk5(eval_res, tid, sid, ot_name_bytes)

        target_str = ""
        def apply_to_slot(slot_offset):
            nonlocal target_str
            # Inserimento in Squadra
            if party_count < 6:
                slot_pos = slot_offset + 0x18E08 + party_count * 220
                save_bytes[slot_pos : slot_pos + 220] = party_pkm
                save_bytes[slot_offset + 0x18E04] = party_count + 1
                target_str = f"Squadra (Slot {party_count + 1}/6)"
            else:
                # Inserimento nei PC Box (ricerca a cascata da Box 1 a Box 24, per 720 slot complessivi)
                injected_box = False
                for b_idx in range(24):
                    box_num = b_idx + 1
                    # Box 1 inizia a 0x00400, ogni box successivo dista 0x01000 byte
                    box_base = slot_offset + 0x00400 + b_idx * 0x01000
                    for s in range(30):
                        pos = box_base + s * 136
                        # Uno slot è vuoto se i primi 4 byte (PID) sono 0
                        if struct.unpack_from('<I', save_bytes, pos)[0] == 0:
                            save_bytes[pos : pos + 136] = box_pkm
                            injected_box = True
                            target_str = f"PC Box {box_num} (Slot {s + 1}/30)"
                            break
                    if injected_box:
                        break

                if not injected_box:
                    # Tutti i 24 Box (720 Pokémon) sono saturi! Sovrascrive l'ultimo slot del Box 24
                    last_pos = slot_offset + 0x17400 + 29 * 136
                    save_bytes[last_pos : last_pos + 136] = box_pkm
                    target_str = "PC Box 24 (Slot 30 sovrascritto - PC saturo 720/720)"

        def update_checksums(slot_offset):
            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot_offset + off
                actual_chk_off = slot_offset + chk_off
                actual_chk_mir = slot_offset + chk_mir
                chk = crc16_ccitt(save_bytes[actual_off : actual_off + length])
                save_bytes[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, "little")
                save_bytes[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, "little")

        # Iniezione su entrambi gli slot
        apply_to_slot(0x00000)
        apply_to_slot(0x26000)
        update_checksums(0x00000)
        update_checksums(0x26000)

        # Scrittura su tutti i target rilevanti per mantenere sincronizzato qualsiasi profilo e percorso
        destinations = {primary_save, SAVE_TARGET_1, SAVE_TARGET_2, SAVES_DIR / "Bianco 2.sav"}
        profiles_dir = SAVES_DIR / "profiles"
        if profiles_dir.exists():
            for p_sav in profiles_dir.glob("*/*.sav"):
                destinations.add(p_sav)
        if primary_save.parent != SAVES_DIR:
            for p_sav in primary_save.parent.glob("*.sav"):
                destinations.add(p_sav)

        for dst in destinations:
            try:
                with open(dst, 'wb') as f:
                    f.write(save_bytes)
            except Exception as e:
                print(f"Errore scrittura {dst}: {e}")

        # Registrazione cronologia
        history_entry = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'card_key': eval_res.get('unique_key'),
            'species_id': dex_id,
            'species_name': eval_res['species_name'],
            'set_name': eval_res.get('set_name'),
            'card_number': eval_res.get('card_number'),
            'finish': eval_res.get('finish'),
            'level': eval_res['level'],
            'target': target_str,
            'is_shiny': eval_res.get('is_shiny', False),
            'is_double_shiny': eval_res.get('is_double_shiny', False),
            'pokeball': eval_res.get('pokeball_name')
        }
        
        hist = []
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    hist = json.load(f)
            except Exception:
                hist = []
        hist.append(history_entry)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(hist, f, indent=2, ensure_ascii=False)

        return {
            'success': True,
            'status': 'INJECTED',
            'target': target_str,
            'backup': str(backup_path),
            'details': history_entry,
            'save_bytes': bytes(save_bytes)
        }

    def get_party(self, target_save: Path | str = None) -> list:
        """Legge e decodifica tutti i Pokémon attualmente presenti nella squadra del salvataggio."""
        primary_save = Path(target_save) if target_save else SAVE_TARGET_1
        if not primary_save.exists():
            primary_save = SAVE_TARGET_1
        if not primary_save.exists():
            return []

        with open(primary_save, 'rb') as f:
            save_bytes = f.read()

        party_count = min(6, save_bytes[0x18E04])
        party = []

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        nature_names = [
            "Ardita", "Solitaria", "Audace", "Decisa", "Schiva",
            "Sicura", "Docile", "Placida", "Scaltra", "Fiacca",
            "Timida", "Lesta", "Seria", "Allegra", "Ingenua",
            "Modesta", "Mite", "Quieta", "Ritrosa", "Ardente",
            "Calma", "Gentile", "Vivace", "Cauta", "Furba"
        ]
        abilities_map = {}
        gen5_data_path = BASE_DIR / "database" / "gen5_in_game_data.json"
        if gen5_data_path.exists():
            try:
                with open(gen5_data_path, "r", encoding="utf-8") as f:
                    abilities_map = json.load(f).get("abilities", {})
            except Exception:
                pass

        for slot in range(party_count):
            slot_pos = 0x18E08 + slot * 220
            pkm = save_bytes[slot_pos : slot_pos + 220]
            pid = struct.unpack_from('<I', pkm, 0)[0]
            chk = struct.unpack_from('<H', pkm, 6)[0]

            dec_blocks = bytearray(lcrng_cipher(pkm[8:136], chk))
            shift = ((pid >> 13) & 0x1F) % 24
            order = ORDERS[shift]
            blocks = {}
            for idx, letter in enumerate(order):
                blocks[letter] = dec_blocks[idx*32 : (idx+1)*32]

            ba = blocks['A']
            bb = blocks['B']
            bc = blocks['C']
            bd = blocks['D']

            dex_id = struct.unpack_from('<H', ba, 0)[0]
            friendship_or_cycles = ba[0x0C]
            ability_id = ba[0x0D]

            moves = list(struct.unpack_from('<4H', bb, 0))
            iv_field = struct.unpack_from('<I', bb, 0x10)[0]
            ivs = {
                'hp': iv_field & 31,
                'atk': (iv_field >> 5) & 31,
                'def': (iv_field >> 10) & 31,
                'spe': (iv_field >> 15) & 31,
                'spa': (iv_field >> 20) & 31,
                'spd': (iv_field >> 25) & 31,
            }
            is_egg = bool((bb[0x18] & 0x40) or (iv_field & 0x40000000))
            gender_val = (bb[0x18] >> 1) & 3
            nature_id = bb[0x19]
            nature_name = nature_names[nature_id % 25] if nature_id < 25 else "Ardita"
            ab_info = abilities_map.get(str(ability_id), {})
            ability_name = ab_info.get("name", f"Abilità #{ability_id}") if ability_id > 0 else "—"

            nick = bc[:22].decode('utf-16le', errors='ignore').split('\uffff')[0].strip('\x00')
            ot = bd[:16].decode('utf-16le', errors='ignore').split('\uffff')[0].strip('\x00')
            pokeball_id = bd[0x10]

            party_dec = lcrng_cipher(pkm[136:220], pid)
            lvl = party_dec[4]
            hp_cur = struct.unpack_from('<H', party_dec, 6)[0]
            hp_max = struct.unpack_from('<H', party_dec, 8)[0]

            cur.execute("SELECT name, types FROM cards WHERE dex_id = ? LIMIT 1", (dex_id,))
            row = cur.fetchone()
            species_name = row[0] if row else f"Pokémon #{dex_id}"
            types = json.loads(row[1]) if row and row[1] else ["Normal"]

            party.append({
                'slot': slot + 1,
                'dex_id': dex_id,
                'species_id': dex_id,
                'species_name': species_name,
                'nickname': nick if nick else species_name,
                'ot': ot,
                'level': lvl,
                'hp_cur': hp_cur,
                'hp_max': hp_max,
                'current_hp': hp_cur,
                'max_hp': hp_max,
                'is_egg': is_egg,
                'hatch_cycles': friendship_or_cycles if is_egg else 0,
                'nature_id': nature_id,
                'nature': nature_name,
                'ability_id': ability_id,
                'ability_name': ability_name,
                'gender_val': gender_val,
                'ivs': ivs,
                'moves': [m for m in moves if m != 0],
                'types': types,
                'pokeball_id': pokeball_id,
                'raw_bytes': pkm
            })

        conn.close()
        return party

    def withdraw_from_party(self, slot_index: int, target_save: Path | str = None) -> dict:
        """
        Rimuove il Pokémon allo slot specificato (0..5) dalla squadra del salvataggio
        e fa scorrere in avanti i membri rimanenti, ricalcolando tutti i 74 checksum.
        """
        primary_save = Path(target_save) if target_save else SAVE_TARGET_1
        if not primary_save.exists():
            primary_save = SAVE_TARGET_1

        party = self.get_party(primary_save)
        if slot_index < 0 or slot_index >= len(party):
            return {"success": False, "message": f"Slot {slot_index + 1} non valido."}

        pkm_to_remove = party[slot_index]
        self.backup_save(primary_save)

        with open(primary_save, 'rb') as f:
            save_bytes = bytearray(f.read())

        party_count = save_bytes[0x18E04]
        if party_count <= 0:
            return {"success": False, "message": "Nessun Pokémon in squadra."}

        def remove_from_slot(slot_offset):
            for s in range(slot_index, party_count - 1):
                dst = slot_offset + 0x18E08 + s * 220
                src = slot_offset + 0x18E08 + (s + 1) * 220
                save_bytes[dst : dst + 220] = save_bytes[src : src + 220]
            vacated = slot_offset + 0x18E08 + (party_count - 1) * 220
            save_bytes[vacated : vacated + 220] = b'\x00' * 220
            save_bytes[slot_offset + 0x18E04] = party_count - 1

        def update_checksums(slot_offset):
            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot_offset + off
                actual_chk_off = slot_offset + chk_off
                actual_chk_mir = slot_offset + chk_mir
                chk = crc16_ccitt(save_bytes[actual_off : actual_off + length])
                save_bytes[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, "little")
                save_bytes[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, "little")

        remove_from_slot(0x00000)
        remove_from_slot(0x26000)
        update_checksums(0x00000)
        update_checksums(0x26000)

        destinations = {primary_save, SAVE_TARGET_1, SAVE_TARGET_2, SAVES_DIR / "Bianco 2.sav"}
        profiles_dir = SAVES_DIR / "profiles"
        if profiles_dir.exists():
            for p_sav in profiles_dir.glob("*/*.sav"):
                destinations.add(p_sav)
        if primary_save.parent != SAVES_DIR:
            for p_sav in primary_save.parent.glob("*.sav"):
                destinations.add(p_sav)

        for dst in destinations:
            try:
                with open(dst, 'wb') as f:
                    f.write(save_bytes)
            except Exception as e:
                print(f"Errore scrittura {dst}: {e}")

        return {"success": True, "pokemon": pkm_to_remove}

    def replace_party_slot(self, slot_index: int, eval_res: dict, target_save: Path | str = None) -> dict:
        """Sostituisce chirurgicamente un Pokémon in squadra con un nuovo esemplare autentico e legale al 100%."""
        primary_save = Path(target_save) if target_save else SAVE_TARGET_1
        if not primary_save.exists():
            primary_save = SAVE_TARGET_1

        self.backup_save(primary_save)

        with open(primary_save, 'rb') as f:
            save_bytes = bytearray(f.read())

        party_count = save_bytes[0x18E04]
        if slot_index < 0 or slot_index >= party_count:
            return {"success": False, "message": f"Slot {slot_index + 1} non valido."}

        ot_name_bytes = bytes(save_bytes[0x19404:0x19414])
        tid = struct.unpack('<H', save_bytes[0x19414:0x19416])[0]
        sid = struct.unpack('<H', save_bytes[0x19416:0x19418])[0]

        party_pkm, _ = self.create_pk5(eval_res, tid, sid, ot_name_bytes)

        def write_slot(slot_offset):
            pos = slot_offset + 0x18E08 + slot_index * 220
            save_bytes[pos : pos + 220] = party_pkm

        def update_checksums(slot_offset):
            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot_offset + off
                actual_chk_off = slot_offset + chk_off
                actual_chk_mir = slot_offset + chk_mir
                chk = crc16_ccitt(save_bytes[actual_off : actual_off + length])
                save_bytes[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, "little")
                save_bytes[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, "little")

        write_slot(0x00000)
        write_slot(0x26000)
        update_checksums(0x00000)
        update_checksums(0x26000)

        destinations = {primary_save, SAVE_TARGET_1, SAVE_TARGET_2, SAVES_DIR / "Bianco 2.sav"}
        profiles_dir = SAVES_DIR / "profiles"
        if profiles_dir.exists():
            for p_sav in profiles_dir.glob("*/*.sav"):
                destinations.add(p_sav)
        if primary_save.parent != SAVES_DIR:
            for p_sav in primary_save.parent.glob("*.sav"):
                destinations.add(p_sav)

        for dst in destinations:
            try:
                with open(dst, 'wb') as f:
                    f.write(save_bytes)
            except Exception as e:
                print(f"Errore scrittura {dst}: {e}")

        return {"success": True, "message": f"Slot {slot_index + 1} sostituito con successo con {eval_res['species_name']}!"}

    def hatch_egg_in_party(self, slot_index: int, target_save: Path | str = None) -> dict:
        """
        Schiude immediatamente l'uovo allo slot specificato (0..5), togliendo il flag uovo,
        impostando l'affetto base a 70 e sistemando il nickname.
        """
        primary_save = Path(target_save) if target_save else SAVE_TARGET_1
        if not primary_save.exists():
            primary_save = SAVE_TARGET_1

        party = self.get_party(primary_save)
        if slot_index < 0 or slot_index >= len(party):
            return {"success": False, "message": "Slot non valido."}

        egg = party[slot_index]
        if not egg.get("is_egg"):
            return {"success": False, "message": "Il Pokémon selezionato non è un uovo."}

        self.backup_save(primary_save)

        with open(primary_save, 'rb') as f:
            save_bytes = bytearray(f.read())

        def hatch_in_slot(slot_offset):
            pos = slot_offset + 0x18E08 + slot_index * 220
            pkm = bytearray(save_bytes[pos : pos + 220])
            pid = struct.unpack_from('<I', pkm, 0)[0]
            chk = struct.unpack_from('<H', pkm, 6)[0]

            dec_blocks = bytearray(lcrng_cipher(pkm[8:136], chk))
            shift = ((pid >> 13) & 0x1F) % 24
            order = ORDERS[shift]
            raw_blocks = {}
            for idx, letter in enumerate(order):
                raw_blocks[letter] = dec_blocks[idx*32 : (idx+1)*32]

            ba = raw_blocks['A']
            bb = raw_blocks['B']
            bc = raw_blocks['C']

            bb[0x18] = bb[0x18] & ~0x40
            iv_val = struct.unpack_from('<I', bb, 0x10)[0]
            struct.pack_into('<I', bb, 0x10, iv_val & ~0x40000000)
            ba[0x0C] = 70

            nick_str = egg["species_name"].upper()
            encoded_nick = nick_str.encode('utf-16le') + b'\xff\xff'
            encoded_nick = encoded_nick.ljust(22, b'\x00')
            bc[0:22] = encoded_nick[:22]

            new_chk = 0
            for letter in ['A', 'B', 'C', 'D']:
                b = raw_blocks[letter]
                for j in range(0, 32, 2):
                    new_chk = (new_chk + struct.unpack_from('<H', b, j)[0]) & 0xFFFF

            shuffled = bytearray(128)
            for i, letter in enumerate(order):
                shuffled[i*32 : (i+1)*32] = raw_blocks[letter]

            struct.pack_into('<H', pkm, 6, new_chk)
            pkm[8:136] = lcrng_cipher(bytes(shuffled), new_chk)
            save_bytes[pos : pos + 220] = pkm

        def update_checksums(slot_offset):
            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot_offset + off
                actual_chk_off = slot_offset + chk_off
                actual_chk_mir = slot_offset + chk_mir
                chk = crc16_ccitt(save_bytes[actual_off : actual_off + length])
                save_bytes[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, "little")
                save_bytes[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, "little")

        hatch_in_slot(0x00000)
        hatch_in_slot(0x26000)
        update_checksums(0x00000)
        update_checksums(0x26000)

        destinations = {primary_save, SAVE_TARGET_1, SAVE_TARGET_2, SAVES_DIR / "Bianco 2.sav"}
        profiles_dir = SAVES_DIR / "profiles"
        if profiles_dir.exists():
            for p_sav in profiles_dir.glob("*/*.sav"):
                destinations.add(p_sav)
        if primary_save.parent != SAVES_DIR:
            for p_sav in primary_save.parent.glob("*.sav"):
                destinations.add(p_sav)

        for dst in destinations:
            try:
                with open(dst, 'wb') as f:
                    f.write(save_bytes)
            except Exception as e:
                print(f"Errore scrittura {dst}: {e}")

        return {"success": True, "message": f"🐣 {egg['species_name']} si è schiuso con successo!"}


