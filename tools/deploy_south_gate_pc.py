#!/usr/bin/env python3
"""
Deploy definitivo del PC al Cancello Sud (X=47, Y=53) e al Capanno (X=39, Y=37).
- Genera entità Furniture (Script 2108, Tipo 4)
- Genera entità NPC autentiche (Sprite 110 Poké Ball + Sprite 291 Assistente)
  con Script 2108, Flag 0 (sempre visibili, no despawn), Byte 34 = 2 (standard Gen 5).
- Inietta nei file Overworld 305, 306, 444, 445 in a/1/2/6.
- Resetta la cache overworld nei salvataggi (Blocco 41) per forzare il ricaricamento.
"""

import os
import sys
import struct
from pathlib import Path
import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
ROM_PATH = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"

BLOCKS = [
    (0x00000, 0x03e0, 0x003E2, 0x25F00),
    (0x00400, 0x0ff0, 0x013F2, 0x25F02),
    (0x01400, 0x0ff0, 0x023F2, 0x25F04),
    (0x02400, 0x0ff0, 0x033F2, 0x25F06),
    (0x03400, 0x0ff0, 0x043F2, 0x25F08),
    (0x04400, 0x0ff0, 0x053F2, 0x25F0A),
    (0x05400, 0x0ff0, 0x063F2, 0x25F0C),
    (0x06400, 0x0ff0, 0x073F2, 0x25F0E),
    (0x07400, 0x0ff0, 0x083F2, 0x25F10),
    (0x08400, 0x0ff0, 0x093F2, 0x25F12),
    (0x09400, 0x0ff0, 0x0A3F2, 0x25F14),
    (0x0A400, 0x0ff0, 0x0B3F2, 0x25F16),
    (0x0B400, 0x0ff0, 0x0C3F2, 0x25F18),
    (0x0C400, 0x0ff0, 0x0D3F2, 0x25F1A),
    (0x0D400, 0x0ff0, 0x0E3F2, 0x25F1C),
    (0x0E400, 0x0ff0, 0x0F3F2, 0x25F1E),
    (0x0F400, 0x0ff0, 0x103F2, 0x25F20),
    (0x10400, 0x0ff0, 0x113F2, 0x25F22),
    (0x11400, 0x0ff0, 0x123F2, 0x25F24),
    (0x12400, 0x0ff0, 0x133F2, 0x25F26),
    (0x13400, 0x0ff0, 0x143F2, 0x25F28),
    (0x14400, 0x0ff0, 0x153F2, 0x25F2A),
    (0x15400, 0x0ff0, 0x163F2, 0x25F2C),
    (0x16400, 0x0ff0, 0x173F2, 0x25F2E),
    (0x17400, 0x0ff0, 0x183F2, 0x25F30),
    (0x18400, 0x09ec, 0x18DEE, 0x25F32),
    (0x18E00, 0x0534, 0x19336, 0x25F34),
    (0x19400, 0x00b0, 0x194B2, 0x25F36),
    (0x19500, 0x00a8, 0x195AA, 0x25F38),
    (0x19600, 0x1338, 0x1A93A, 0x25F3A),
    (0x1AA00, 0x07c4, 0x1B1C6, 0x25F3C),
    (0x1B200, 0x0d54, 0x1BF56, 0x25F3E),
    (0x1C000, 0x0094, 0x1C096, 0x25F40),
    (0x1C100, 0x0658, 0x1C75A, 0x25F42),
    (0x1C800, 0x0a94, 0x1D296, 0x25F44),
    (0x1D300, 0x01ac, 0x1D4AE, 0x25F46),
    (0x1D500, 0x03ec, 0x1D8EE, 0x25F48),
    (0x1D900, 0x005c, 0x1D95E, 0x25F4A),
    (0x1DA00, 0x01e0, 0x1DBE2, 0x25F4C),
    (0x1DC00, 0x00a8, 0x1DCAA, 0x25F4E),
    (0x1DD00, 0x0460, 0x1E162, 0x25F50),
    (0x1E200, 0x1400, 0x1F602, 0x25F52),
    (0x1F700, 0x02a4, 0x1F9A6, 0x25F54),
    (0x1FA00, 0x00e0, 0x1FAE2, 0x25F56),
    (0x1FB00, 0x034c, 0x1FE4E, 0x25F58),
    (0x1FF00, 0x04e0, 0x203E2, 0x25F5A),
    (0x20400, 0x00f8, 0x204FA, 0x25F5C),
    (0x20500, 0x02fc, 0x207FE, 0x25F5E),
    (0x20800, 0x0094, 0x20896, 0x25F60),
    (0x20900, 0x035c, 0x20C5E, 0x25F62),
    (0x20D00, 0x01d4, 0x20ED6, 0x25F64),
    (0x20F00, 0x01e0, 0x210E2, 0x25F66),
    (0x21100, 0x00f0, 0x211F2, 0x25F68),
    (0x21200, 0x01b4, 0x213B6, 0x25F6A),
    (0x21400, 0x04dc, 0x218DE, 0x25F6C),
    (0x21900, 0x0034, 0x21936, 0x25F6E),
    (0x21A00, 0x003c, 0x21A3E, 0x25F70),
    (0x21B00, 0x01ac, 0x21CAE, 0x25F72),
    (0x21D00, 0x0b90, 0x22892, 0x25F74),
    (0x22900, 0x00ac, 0x229AE, 0x25F76),
    (0x22A00, 0x0850, 0x23252, 0x25F78),
    (0x23300, 0x0284, 0x23586, 0x25F7A),
    (0x23600, 0x0010, 0x23612, 0x25F7C),
    (0x23700, 0x00a8, 0x237AA, 0x25F7E),
    (0x23800, 0x016c, 0x2396E, 0x25F80),
    (0x23A00, 0x0080, 0x23A82, 0x25F82),
    (0x23B00, 0x00fc, 0x23BFE, 0x25F84),
    (0x23C00, 0x16a8, 0x252AA, 0x25F86),
    (0x25300, 0x0498, 0x2579A, 0x25F88),
    (0x25800, 0x0060, 0x25862, 0x25F8A),
    (0x25900, 0x00fc, 0x259FE, 0x25F8C),
    (0x25A00, 0x03e4, 0x25DE6, 0x25F8E),
    (0x25E00, 0x00f0, 0x25EF2, 0x25F90),
    (0x25F00, 0x0094, 0x25FA2, 0x25FA2),
]

def crc16_ccitt(data):
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

def make_furn(script_id, ftype, x, y, z=0):
    f = bytearray(20)
    struct.pack_into('<IIIII', f, 0, script_id, ftype, x, y, z)
    return f

def make_npc(npc_id, sprite_id, x, y, script_id=2108, facing=1, z=0):
    n = bytearray(36)
    struct.pack_into('<H', n, 0, npc_id)       # ID progressivo
    struct.pack_into('<H', n, 2, sprite_id)   # Sprite (110 = Poké Ball, 291 = Worker)
    struct.pack_into('<H', n, 4, 0)           # Movimento stazionario
    struct.pack_into('<H', n, 6, 0)           # Parametro movimento
    struct.pack_into('<H', n, 8, script_id)   # SCRIPT ID = 2108 (PC Pokémon!)
    struct.pack_into('<H', n, 10, 0)          # SPAWN FLAG = 0 (SEMPRE VISIBILE!)
    struct.pack_into('<H', n, 12, facing)     # Direzione (1=Sud, 2=Ovest, 3=Est)
    struct.pack_into('<H', n, 14, 0)
    # Byte 16..27 restano a 0
    struct.pack_into('<H', n, 28, x)          # X Tile
    struct.pack_into('<H', n, 30, y)          # Y Tile
    struct.pack_into('<H', n, 32, z)          # Z Elevation
    struct.pack_into('<H', n, 34, 2)          # Type = 2 (standard B2W2)
    return n

def main():
    print(f"==> Caricamento ROM da: {ROM_PATH}...")
    rom = ndspy.rom.NintendoDSRom.fromFile(str(ROM_PATH))

    ow_id = rom.filenames.idOf("a/1/2/6")
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])

    # 1. Definiamo le entità:
    # A) Al CANCELLO SUD (X=47, Y=53):
    # - Furniture trigger a (47, 53)
    # - NPC Poké Ball (110) esattamente a (47, 53)
    # - NPC Assistente (291) a (48, 53) rivolto a Ovest verso il terminale
    # B) Al CAPANNO (X=39, Y=37):
    # - Furniture trigger a (39, 37)
    # - NPC Poké Ball (110) a (39, 37)
    # - NPC Assistente (291) a (38, 37) rivolto a Est verso il terminale
    furns = [
        make_furn(2108, 4, 47, 53, z=0),
        make_furn(2108, 4, 39, 37, z=0),
    ]

    npcs = [
        make_npc(0, 110, 47, 53, script_id=2108, facing=1), # Poké Ball PC Cancello Sud
        make_npc(1, 291, 48, 53, script_id=2108, facing=2), # Assistente Cancello Sud
        make_npc(2, 110, 39, 37, script_id=2108, facing=1), # Poké Ball PC Capanno
        make_npc(3, 291, 38, 37, script_id=2108, facing=3), # Assistente Capanno
    ]

    all_furn_bytes = b''.join(furns)
    all_npc_bytes = b''.join(npcs)

    header = bytearray(8)
    payload_len = len(all_furn_bytes) + len(all_npc_bytes)
    struct.pack_into('<IBBBB', header, 0, payload_len, len(furns), len(npcs), 0, 0)

    ow_file_bytes = bytes(header + all_furn_bytes + all_npc_bytes)

    for f_idx in [305, 306, 444, 445]:
        ow_narc.files[f_idx] = ow_file_bytes

    rom.files[ow_id] = ow_narc.save()
    rom.saveToFile(str(ROM_PATH))
    print(f"    [OK] File Overworld aggiornati in ROM: {len(furns)} Furnitures e {len(npcs)} NPCs!")

    # 2. Reset Overworld Cache in tutti i salvataggi
    save_files = [
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav",
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav",
        BASE_DIR / "saves" / "Pokémon Bianco 2.sav",
        BASE_DIR / "saves" / "Bianco 2.sav",
        BASE_DIR / "roms" / "modified" / "Bianco 2.sav",
    ]

    for s_path in save_files:
        if not s_path.exists(): continue
        data = bytearray(s_path.read_bytes())
        for slot in [0x00000, 0x26000]:
            # Reset Blocco 41 (Overworld cache)
            data[slot + 0x1E200 : slot + 0x1E200 + 0x1400] = b'\x00' * 0x1400
            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot + off
                actual_chk_off = slot + chk_off
                actual_chk_mir = slot + chk_mir
                chk = crc16_ccitt(data[actual_off : actual_off + length])
                data[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, 'little')
                data[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, 'little')
        s_path.write_bytes(data)
        print(f"    [OK] Cache resettata e checksum aggiornato per: {s_path.name}")

    print("\n🎉 Patch PC completata con successo al Cancello Sud (X=47, Y=53) e Capanno!")

if __name__ == "__main__":
    main()
