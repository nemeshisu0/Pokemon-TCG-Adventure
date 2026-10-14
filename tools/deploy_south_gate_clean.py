#!/usr/bin/env python3
"""
Deploy and verify PC at South Gate (X=47, Y=53) on Floccesy Farm (Map 445):
- ROM:
  * OW file 306: Furnitures at (47, 53) and (47, 52).
                 NPC 10 (Poké Ball terminal 110) at (47, 53).
                 NPC 3 (Herdier 307) at (47, 53).
                 NPC 11 (Mareep 363) at (48, 52).
                 NPC 1 (Hugh 34) at (46, 52).
                 All with Script 7, Flag 0.
  * Script file 890: Script 7, 11, 12 with CallPC(0, 101) (opcode 0x0146).
- Save:
  * Based on recently saved nemesy2 profile (with Geonet already dismissed and saved).
  * Position player at Map 445, (47, 52), Facing 1 (SUD, directly facing 47, 53).
  * Recalculates all CRC16 CCITT checksums across both slots.
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
    print(f"==> 1. Caricamento ROM Originale...")
    orig_rom = ndspy.rom.NintendoDSRom.fromFile(str(ORIGINAL_ROM))
    
    # 1. Overworld entities in a/1/2/6 file 306
    ow_id = orig_rom.filenames.idOf("a/1/2/6")
    orig_ow_narc = ndspy.narc.NARC(orig_rom.files[ow_id])
    f306 = bytearray(orig_ow_narc.files[306])

    print("==> 2. Configurazione Furniture e NPCs al Cancello Sud...")
    # Furnitures a (47, 53)
    struct.pack_into("<IIIII", f306, 8, 7, 6, 47, 53, 32)   # Furn 0: Script 7 Omnidirectional
    struct.pack_into("<IIIII", f306, 28, 7, 3, 47, 53, 32)  # Furn 1: Script 7 Facing South
    struct.pack_into("<IIIII", f306, 48, 7, 4, 47, 53, 32)  # Furn 2: Script 7 Desk
    struct.pack_into("<IIIII", f306, 68, 7, 0, 47, 53, 32)  # Furn 3: Script 7 Facing North
    
    # Furnitures a (47, 52)
    struct.pack_into("<IIIII", f306, 88, 7, 6, 47, 52, 32)  # Furn 4: Script 7 Omnidirectional
    struct.pack_into("<IIIII", f306, 108, 7, 3, 47, 52, 32) # Furn 5: Script 7 Facing South

    # NPCs: base offset 448
    # NPC 10 (Poké Ball terminal 110) al cancello a (47, 53)
    ball_npc10 = struct.pack("<18H", 10, 110, 0, 0, 0, 7, 1, 0, 0, 0, 0, 0, 0, 0, 47, 53, 0, 2)
    f306[448 + 10 * 36 : 448 + 11 * 36] = ball_npc10

    # NPC 3 (Herdier 307) al cancello a (47, 53)
    herdier_npc3 = struct.pack("<18H", 3, 307, 0, 0, 0, 7, 1, 0, 0, 0, 0, 0, 0, 0, 47, 53, 0, 2)
    f306[448 + 3 * 36 : 448 + 4 * 36] = herdier_npc3

    # NPC 11 (Mareep 363) accanto a (48, 52)
    mareep_npc11 = struct.pack("<18H", 11, 363, 0, 0, 0, 7, 1, 0, 0, 0, 0, 0, 0, 0, 48, 52, 0, 2)
    f306[448 + 11 * 36 : 448 + 12 * 36] = mareep_npc11

    # NPC 1 (Hugh 34) a (46, 52)
    hugh_npc1 = struct.pack("<18H", 1, 34, 0, 0, 0, 7, 1, 0, 0, 0, 0, 0, 0, 0, 46, 52, 0, 2)
    f306[448 + 1 * 36 : 448 + 2 * 36] = hugh_npc1

    # Inietta SOLO su file 306
    orig_ow_narc.files[306] = bytes(f306)
    orig_rom.files[ow_id] = orig_ow_narc.save()

    # 2. Scripts: a/0/5/6 file 890
    scr_id = orig_rom.filenames.idOf("a/0/5/6")
    orig_scr_narc = ndspy.narc.NARC(orig_rom.files[scr_id])
    f890 = bytearray(orig_scr_narc.files[890])

    # Bytecode CallPC: Lock, FacePlayer, CallPC(0, 101) [0x0146], Release, Unlock, Halt
    # 2e 00 (Lock)
    # 74 00 (FacePlayer)
    # 46 01 00 00 65 00 (CallPC(0, 101) - Box storage!)
    # 30 00 (Release)
    # 2f 00 (Unlock)
    # 02 00 (Halt)
    pc_bytecode = bytes.fromhex("2e00740046010000650030002f000200")

    # Script 7 (offset 2780)
    s7_off = 2780
    f890[s7_off : s7_off + len(pc_bytecode)] = pc_bytecode
    f890[s7_off + len(pc_bytecode) : 2961] = b'\x00' * (2961 - (s7_off + len(pc_bytecode)))

    # Script 11 (offset 3457)
    s11_off = 3457
    f890[s11_off : s11_off + len(pc_bytecode)] = pc_bytecode

    # Script 12 (offset 3542)
    s12_off = 3542
    f890[s12_off : s12_off + len(pc_bytecode)] = pc_bytecode

    orig_scr_narc.files[890] = bytes(f890)
    orig_rom.files[scr_id] = orig_scr_narc.save()

    orig_rom.saveToFile(str(MODIFIED_ROM))
    print(f"    [OK] ROM creata pulita con CallPC(0, 101): {MODIFIED_ROM}")

def patch_saves():
    print("\n==> 3. Aggiornamento posizione salvataggio al Cancello Sud...")
    src_sav = BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav"
    data = bytearray(src_sav.read_bytes())

    pos_x = 35
    pos_y = 35
    matrix_x = 47
    matrix_y = 52
    facing = 1 # SUD (verso il cancello a 47, 53)

    for slot in [0x00000, 0x26000]:
        # Pulisci cache overworld per ricaricare entità da file 306
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

    dest_paths = [
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav",
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav",
        BASE_DIR / "saves" / "Pokémon Bianco 2.sav",
        BASE_DIR / "saves" / "Bianco 2.sav",
        BASE_DIR / "roms" / "modified" / "Bianco 2.sav",
    ]

    for p in dest_paths:
        p.write_bytes(data)
        print(f"    [OK] Salvataggio aggiornato: {p}")

if __name__ == "__main__":
    patch_rom()
    patch_saves()
    print("\n🎉 DEPLOY CANCELLO SUD COMPLETATO!")
