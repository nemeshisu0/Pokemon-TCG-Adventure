#!/usr/bin/env python3
"""
Deploy PC al Cancello Sud (X=47, Y=53) basato sul file Overworld VANILLA 306:
- Mantiene intatta al 100% la struttura interna (22 Furnitures, 17 NPCs, 1 Warp, 6 Triggers, footer).
- Modifica NPC 0, 1, 2 e 10 con Flag=0 (sempre visibili), Type=0 (NPC standard), Script=7.
- Modifica Script 7 in file 890 per eseguire RTCallGlobal(2108) (Sistema Box PC Pokémon).
- Configura Furniture con Script=2108 a (47, 53) e (47, 52).
- Pulisce cache Block 41 nei salvataggi e ricalcola tutti i checksum CRC16.
"""

import os
import sys
import struct
from pathlib import Path
import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_ROM = BASE_DIR / "roms" / "original" / "Bianco 2.nds"
MODIFIED_ROM = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"

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

def patch_rom():
    print(f"==> 1. Caricamento ROM Originale per estrarre f306 e f890 autentici...")
    orig_rom = ndspy.rom.NintendoDSRom.fromFile(str(ORIGINAL_ROM))
    
    # 1. Overworld entities in a/1/2/6 file 306
    ow_id = orig_rom.filenames.idOf("a/1/2/6")
    orig_ow_narc = ndspy.narc.NARC(orig_rom.files[ow_id])
    f306 = bytearray(orig_ow_narc.files[306])

    print("==> 2. Modifica entità in f306 (struttura vanilla 1228 byte)...")
    # Furn 0: PC a (47, 53) - type 4
    struct.pack_into("<IIIII", f306, 8, 2108, 4, 47, 53, 32)
    # Furn 1: PC a (47, 53) - type 0 (interazione libera da ogni direzione)
    struct.pack_into("<IIIII", f306, 28, 2108, 0, 47, 53, 32)
    # Furn 2: PC a (47, 52) - type 4
    struct.pack_into("<IIIII", f306, 48, 2108, 4, 47, 52, 32)
    # Furn 3: PC a (47, 52) - type 0
    struct.pack_into("<IIIII", f306, 68, 2108, 0, 47, 52, 32)

    # Base NPCs: offset 448 (dopo 22 furnitures * 20 = 440 + header 8)
    # NPC 3 (Herdier Vanilla) spostato al Cancello Sud (47, 53) rivolto a Nord verso la strada:
    herdier_npc3 = struct.pack("<18H", 3, 307, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 47, 53, 0, 2)
    f306[448 + 3 * 36 : 448 + 4 * 36] = herdier_npc3

    # NPC 11 (Mareep Vanilla) spostato a (47, 52) rivolto a Ovest direttamente di fronte al giocatore:
    mareep_npc11 = struct.pack("<18H", 11, 363, 0, 0, 0, 7, 2, 0, 0, 0, 0, 0, 0, 0, 47, 52, 0, 2)
    f306[448 + 11 * 36 : 448 + 12 * 36] = mareep_npc11

    # Backup su NPC 10 (Herdier) e NPC 1 (Mareep)
    herdier_struct = struct.pack("<18H", 10, 307, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 47, 53, 0, 2)
    f306[448 + 10 * 36 : 448 + 11 * 36] = herdier_struct

    mareep_struct = struct.pack("<18H", 1, 363, 0, 0, 0, 7, 2, 0, 0, 0, 0, 0, 0, 0, 47, 52, 0, 2)
    f306[448 + 1 * 36 : 448 + 2 * 36] = mareep_struct

    print(f"    [OK] File 306 modificato (NPC 3 Herdier a 47,53 | NPC 11 Mareep a 47,52)!")

    # Inietta nella ROM modificata
    mod_rom = ndspy.rom.NintendoDSRom.fromFile(str(MODIFIED_ROM))
    mod_ow_narc = ndspy.narc.NARC(mod_rom.files[ow_id])
    for idx in [305, 306, 444, 445]:
        mod_ow_narc.files[idx] = bytes(f306)
    mod_rom.files[ow_id] = mod_ow_narc.save()

    # Script 7 in a/0/5/6 file 890 - Estratto fresco da ORIGINAL_ROM (3924 byte!)
    scr_id = orig_rom.filenames.idOf("a/0/5/6")
    orig_scr_narc = ndspy.narc.NARC(orig_rom.files[scr_id])
    f890 = bytearray(orig_scr_narc.files[890])

    # Bytecode Script 7: Lock, EyeToEye, RTCallGlobal(2108), Release, Unlock, Halt
    pc_bytecode = bytes.fromhex("2e0074001c003c0830002f000200")
    s7_off = 2780
    f890[s7_off : s7_off + len(pc_bytecode)] = pc_bytecode
    f890[s7_off + len(pc_bytecode) : 2961] = b'\x00' * (2961 - (s7_off + len(pc_bytecode)))

    mod_scr_narc = ndspy.narc.NARC(mod_rom.files[scr_id])
    mod_scr_narc.files[890] = bytes(f890)
    mod_rom.files[scr_id] = mod_scr_narc.save()
    print(f"    [OK] Script 7 in file 890 programmato con RTCallGlobal(2108)! (Dimensione: {len(f890)} byte)")

    mod_rom.saveToFile(str(MODIFIED_ROM))
    print(f"    [OK] ROM salvata con successo: {MODIFIED_ROM}")

def patch_saves():
    print("\n==> 3. Reset Overworld Cache e coordinate salvataggi...")
    save_files = [
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav",
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav",
        BASE_DIR / "saves" / "Pokémon Bianco 2.sav",
        BASE_DIR / "saves" / "Bianco 2.sav",
        BASE_DIR / "roms" / "modified" / "Bianco 2.sav",
    ]

    pos_x = 35
    pos_y = 35
    matrix_x = 47
    matrix_y = 52
    facing = 1 # SUD (verso il Cancello Sud a 47, 53)

    for s_path in save_files:
        if not s_path.exists(): continue
        data = bytearray(s_path.read_bytes())
        for slot in [0x00000, 0x26000]:
            # Pulisci cache overworld
            data[slot + 0x1E200 : slot + 0x1E200 + 0x1400] = b'\x00' * 0x1400

            b28 = slot + 0x19500
            data[b28 + 0x04 : b28 + 0x06] = (445).to_bytes(2, "little")
            data[b28 + 0x06 : b28 + 0x08] = facing.to_bytes(2, "little")
            data[b28 + 0x10 : b28 + 0x14] = (pos_x * 0x10000 + 0x8000).to_bytes(4, "little")
            data[b28 + 0x18 : b28 + 0x1C] = (pos_y * 0x10000 + 0x8000).to_bytes(4, "little")

            data[b28 + 0x80 : b28 + 0x84] = (445).to_bytes(4, "little")
            data[b28 + 0x86 : b28 + 0x88] = matrix_x.to_bytes(2, "little")
            data[b28 + 0x8A : b28 + 0x8C] = (0).to_bytes(2, "little")
            data[b28 + 0x8E : b28 + 0x90] = matrix_y.to_bytes(2, "little")
            data[b28 + 0x92 : b28 + 0x94] = facing.to_bytes(2, "little")

            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot + off
                actual_chk_off = slot + chk_off
                actual_chk_mir = slot + chk_mir
                chk = crc16_ccitt(data[actual_off : actual_off + length])
                data[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, 'little')
                data[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, 'little')

        s_path.write_bytes(data)
        print(f"    [OK] Aggiornato salvataggio: {s_path.name}")

    print("\n🎉 MODIFICA COMPLETATA!")

if __name__ == "__main__":
    patch_rom()
    patch_saves()
