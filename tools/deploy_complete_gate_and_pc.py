#!/usr/bin/env python3
"""
Deploy DEFINITIVO di Blocchi Cancello Sud + PC Box Completo:
1. Sbarramento Cancello Sud:
   - Poliziotti (Sprite 52) e Guardie (Sprite 57) a (X=46,47,48 Y=53,54) che bloccano completamente l'uscita dalla fattoria.
   - Tutti i 32 blocchi di sicurezza dell'area lobby/fattoria da Bianco 2.nds.bak.
2. PC Box Interagibile funzionante:
   - Al Cancello Sud (X=47, Y=52 e X=48, Y=52):
     * Poké Ball PC (Sprite 110) a (47, 52) con Script 2108 (Box System)
     * Assistente PC (Sprite 291) a (48, 52) con Script 2108 (Box System)
     * Furniture interattiva a (47, 52) e (48, 52) con Script 2108
   - Al Centro Fattoria (X=35, Y=36 e X=36, Y=35):
     * Poké Ball PC (Sprite 110) a (35, 36) con Script 2108
     * Assistente PC (Sprite 291) a (36, 35) con Script 2108
     * Furniture interattiva a (35, 36) e (36, 35) con Script 2108
3. Iniezione sincronizzata in TUTTI i file Overworld della zona: 305, 306, 444, 445.
4. Script File 890 configurato con routine CallPC.
5. Allineamento e pulizia cache overworld (Block 41) in tutti i salvataggi attivi.
"""

import os
import sys
import struct
from pathlib import Path
import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
BAK_ROM = BASE_DIR / "roms" / "modified" / "Bianco 2.nds.bak"
OUT_ROM = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"

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

def crc16_ccitt(data: bytes) -> int:
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

def make_barrier_npc(npc_id, sprite_id, raw_x, raw_y, facing=0):
    npc = bytearray(36)
    struct.pack_into('<H', npc, 0, npc_id)
    struct.pack_into('<H', npc, 2, sprite_id)
    struct.pack_into('<H', npc, 4, 0)
    struct.pack_into('<H', npc, 6, 0)
    struct.pack_into('<H', npc, 8, 0) # Flag 0 = sempre visibile
    struct.pack_into('<H', npc, 10, 0)
    struct.pack_into('<H', npc, 12, facing)
    struct.pack_into('<H', npc, 14, 0)
    struct.pack_into('<H', npc, 28, raw_x)
    struct.pack_into('<H', npc, 30, raw_y)
    struct.pack_into('<H', npc, 32, 0)
    struct.pack_into('<H', npc, 34, 1) # Solid NPC barrier
    return bytes(npc)

def make_pc_npc(npc_id, sprite_id, raw_x, raw_y, facing=1, script_id=2108):
    npc = bytearray(36)
    struct.pack_into('<H', npc, 0, npc_id)
    struct.pack_into('<H', npc, 2, sprite_id) # 110 = Poké Ball, 291 = Assistente
    struct.pack_into('<H', npc, 4, 0)
    struct.pack_into('<H', npc, 6, 0)
    struct.pack_into('<H', npc, 8, 0)          # Flag 0 = sempre visibile
    struct.pack_into('<H', npc, 10, script_id)  # Script 2108 = Box PC System
    struct.pack_into('<H', npc, 12, facing)
    struct.pack_into('<H', npc, 14, 0)
    struct.pack_into('<H', npc, 28, raw_x)
    struct.pack_into('<H', npc, 30, raw_y)
    struct.pack_into('<H', npc, 32, 0)
    struct.pack_into('<H', npc, 34, 2)          # Type 2 = interactable NPC
    return bytes(npc)

def make_furn(script_id, ftype, x, y, z=0):
    f = bytearray(20)
    struct.pack_into('<IIIII', f, 0, script_id, ftype, x, y, z)
    return bytes(f)

def deploy():
    print(f"==> 1. Caricamento ROM da base sicura: {BAK_ROM}...")
    rom = ndspy.rom.NintendoDSRom.fromFile(str(BAK_ROM))

    ow_id = rom.filenames.idOf('a/1/2/6')
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])

    # Costruiamo la lista completa degli NPC:
    npcs = []
    idx = 0

    # A) Blocchi storici di lobby (32 guardie)
    for wy, spr in [(437, 57), (438, 52), (439, 57), (440, 52)]:
        for wx in [407, 408, 409, 410]:
            npcs.append(make_barrier_npc(idx, spr, wx, wy, facing=0))
            idx += 1

    for ly, spr in [(21, 52), (22, 57), (23, 52), (24, 57)]:
        for lx in [23, 24, 25, 26]:
            npcs.append(make_barrier_npc(idx, spr, lx, ly, facing=0))
            idx += 1

    # B) Blocchi del Cancello Sud (uscita dalla fattoria verso Percorso 20)
    gate_barriers = [
        (46, 53, 52, 0), # Poliziotto
        (47, 53, 57, 0), # Guardia
        (48, 53, 52, 0), # Poliziotto
        (46, 54, 57, 0), # Guardia
        (47, 54, 52, 0), # Poliziotto
        (48, 54, 57, 0), # Guardia
    ]
    for gx, gy, gspr, gfacing in gate_barriers:
        npcs.append(make_barrier_npc(idx, gspr, gx, gy, facing=gfacing))
        idx += 1

    # C) NPC PC INTERAGIBILI:
    # 1. Al Cancello Sud (subito davanti alle guardie):
    npcs.append(make_pc_npc(idx, 110, 47, 52, facing=1, script_id=2108)) # Poké Ball PC a (47, 52)
    idx += 1
    npcs.append(make_pc_npc(idx, 291, 48, 52, facing=2, script_id=2108)) # Assistente PC a (48, 52)
    idx += 1

    # 2. Al Centro della Fattoria (vicino al punto di spawn del giocatore):
    npcs.append(make_pc_npc(idx, 110, 35, 36, facing=1, script_id=2108)) # Poké Ball PC a (35, 36)
    idx += 1
    npcs.append(make_pc_npc(idx, 291, 36, 35, facing=2, script_id=2108)) # Assistente PC a (36, 35)
    idx += 1
    npcs.append(make_pc_npc(idx, 110, 34, 35, facing=3, script_id=2108)) # Poké Ball PC a (34, 35)
    idx += 1

    # D) FURNITURES (Computer / Terminali fisici invisibili su cui premere A):
    furns = [
        # Cancello Sud:
        make_furn(2108, 0, 47, 52, z=0),
        make_furn(2108, 4, 47, 52, z=0),
        make_furn(2108, 0, 48, 52, z=0),
        # Centro Fattoria:
        make_furn(2108, 0, 35, 36, z=0),
        make_furn(2108, 4, 35, 36, z=0),
        make_furn(2108, 0, 36, 35, z=0),
        make_furn(2108, 0, 34, 35, z=0),
    ]

    num_npcs = len(npcs)
    num_furns = len(furns)
    print(f"    Configurati {num_furns} Furnitures PC e {num_npcs} NPCs (Barriere + PC)!")

    ow_body = b''.join(furns) + b''.join(npcs)
    ow_footer = b'\x00\x00\x00\x00'
    payload_len = len(ow_body) + len(ow_footer)
    header = bytearray(8)
    struct.pack_into('<IBBBB', header, 0, payload_len, num_furns, num_npcs, 0, 0)
    ow_file_bytes = bytes(header) + ow_body + ow_footer

    for f_idx in [305, 306, 444, 445]:
        ow_narc.files[f_idx] = ow_file_bytes

    rom.files[ow_id] = ow_narc.save()

    # E) Programmazione Script 7 in file 890 (Script di Mappa 445)
    scr_id = rom.filenames.idOf('a/0/5/6')
    scr_narc = ndspy.narc.NARC(rom.files[scr_id])
    f890 = bytearray(scr_narc.files[890])
    pc_code = bytes.fromhex("2e00a600470574003d00000400000000000032003e0030002f000200")
    s7_off = 2780
    f890[s7_off : s7_off + len(pc_code)] = pc_code
    scr_narc.files[890] = bytes(f890)
    rom.files[scr_id] = scr_narc.save()
    print("    [OK] Script 7 configurato con routine CallPC universale!")

    # F) Salvataggio ROM
    print(f"==> 2. Scrittura ROM modificata: {OUT_ROM}...")
    rom_bytes = bytearray(rom.save())
    TARGET_SIZE = 536870912
    if len(rom_bytes) < TARGET_SIZE:
        rom_bytes += bytes([0xFF]) * (TARGET_SIZE - len(rom_bytes))
    with open(OUT_ROM, 'wb') as f:
        f.write(rom_bytes)
    print("    [OK] ROM modificata completata e allineata a 512 MB!")

    # G) Pulizia Cache Overworld (Block 41) nei salvataggi
    print("\n==> 3. Allineamento Salvataggi (Reset Cache Overworld Block 41)...")
    save_files = [
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav",
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav",
        BASE_DIR / "saves" / "Bianco 2.sav",
        BASE_DIR / "saves" / "Pokémon Bianco 2.sav",
    ]

    for s_path in save_files:
        if not s_path.exists(): continue
        data = bytearray(s_path.read_bytes())
        for slot in [0x00000, 0x26000]:
            data[slot + 0x1E200 : slot + 0x1E200 + 0x1400] = b'\x00' * 0x1400
            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot + off
                actual_chk_off = slot + chk_off
                actual_chk_mir = slot + chk_mir
                chk = crc16_ccitt(data[actual_off : actual_off + length])
                data[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, 'little')
                data[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, 'little')
        s_path.write_bytes(data)
        print(f"    [OK] Aggiornato salvataggio: {s_path.name}")

if __name__ == "__main__":
    deploy()
    print("\n🎉 BLOCCHI CANCELLO SUD E PC DEPLOYATI CON SUCCESSO!")
