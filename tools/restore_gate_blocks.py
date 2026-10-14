#!/usr/bin/env python3
"""
Ripristina i blocchi di sbarramento davanti al cancello sud e i blocchi originali:
1. Carica la ROM con le impostazioni sandbox complete (da roms/modified/Bianco 2.nds.bak).
2. Aggiunge i blocchi fisici (NPC Poliziotto/Guardia sprite 52 e 57) esattamente davanti al cancello:
   - X=46, Y=53
   - X=47, Y=53
   - X=48, Y=53
   - X=46, Y=54
   - X=47, Y=54
   - X=48, Y=54
   Mantenendo tutti i blocchi preesistenti (32 guardie) di build_final_lobby.py.
3. Salva la ROM in roms/modified/Bianco 2.nds (512 MB esatti).
4. Resetta la cache overworld (Block 41 a 0x1E200) nei salvataggi del profilo per caricare subito i blocchi a video.
"""

import os
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

def crc16_ccitt(data):
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
    struct.pack_into('<H', npc, 8, 0)
    struct.pack_into('<H', npc, 10, 0)
    struct.pack_into('<H', npc, 12, facing)
    struct.pack_into('<H', npc, 14, 0)
    struct.pack_into('<H', npc, 28, raw_x)
    struct.pack_into('<H', npc, 30, raw_y)
    struct.pack_into('<H', npc, 32, 0)
    struct.pack_into('<H', npc, 34, 1) # Solid NPC barrier
    return bytes(npc)

def main():
    print(f"==> Caricamento base sicura da: {BAK_ROM}...")
    rom = ndspy.rom.NintendoDSRom.fromFile(str(BAK_ROM))

    ow_id = rom.filenames.idOf('a/1/2/6')
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])

    # Creazione della lista completa dei blocchi NPC
    barrier_npcs = []
    idx = 0

    # 1. I blocchi storici di build_final_lobby.py
    # A) World Coords (per outdoor matrix engine)
    for wy, spr in [(437, 57), (438, 52), (439, 57), (440, 52)]:
        for wx in [407, 408, 409, 410]:
            barrier_npcs.append(make_barrier_npc(idx, spr, wx, wy, facing=0))
            idx += 1

    # B) Local Coords (area capanno / porta)
    for ly, spr in [(21, 52), (22, 57), (23, 52), (24, 57)]:
        for lx in [23, 24, 25, 26]:
            barrier_npcs.append(make_barrier_npc(idx, spr, lx, ly, facing=0))
            idx += 1

    # 2. I blocchi davanti al Cancello Sud (uscita mappa verso Percorso 20)
    # Coprono l'intero passaggio del cancello (X=46, 47, 48 a Y=53 e Y=54)
    gate_coords = [
        (46, 53, 52, 0), # Poliziotto a X=46, Y=53
        (47, 53, 57, 0), # Guardia a X=47, Y=53
        (48, 53, 52, 0), # Poliziotto a X=48, Y=53
        (46, 54, 57, 0), # Guardia a X=46, Y=54
        (47, 54, 52, 0), # Poliziotto a X=47, Y=54
        (48, 54, 57, 0), # Guardia a X=48, Y=54
    ]
    for gx, gy, gspr, gfacing in gate_coords:
        barrier_npcs.append(make_barrier_npc(idx, gspr, gx, gy, facing=gfacing))
        idx += 1

    num_npcs = len(barrier_npcs)
    print(f"    Totale NPC di sbarramento configurati: {num_npcs}")

    ow_barrier = bytearray()
    ow_data_len = num_npcs * 36 + 4
    ow_barrier += ow_data_len.to_bytes(4, 'little')
    ow_barrier += bytes([0, num_npcs, 0, 0]) # 0 F, num_npcs N, 0 W, 0 T
    for b_npc in barrier_npcs:
        ow_barrier += b_npc
    ow_barrier += b'\x00\x00\x00\x00' # Footer 4 byte

    for f_idx in [305, 306, 444, 445]:
        ow_narc.files[f_idx] = bytes(ow_barrier)

    rom.files[ow_id] = ow_narc.save()

    print(f"==> Salvataggio ROM in: {OUT_ROM}...")
    rom_bytes = bytearray(rom.save())
    TARGET_SIZE = 536870912
    if len(rom_bytes) < TARGET_SIZE:
        print(f"    Padding a 512 MB ({TARGET_SIZE} bytes)...")
        rom_bytes += bytes([0xFF]) * (TARGET_SIZE - len(rom_bytes))

    with open(OUT_ROM, 'wb') as f:
        f.write(rom_bytes)
    print("    [OK] ROM Bianco 2.nds salvata e allineata!")

    # 3. Reset Overworld Cache (Block 41) nei salvataggi
    save_files = [
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav",
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav",
        BASE_DIR / "saves" / "Pokémon Bianco 2.sav",
        BASE_DIR / "saves" / "Bianco 2.sav",
        BASE_DIR / "roms" / "modified" / "Bianco 2.sav",
    ]

    for sp in save_files:
        if not sp.exists():
            continue
        try:
            with open(sp, 'rb') as f:
                data = bytearray(f.read())
            if len(data) != 524288:
                continue

            for slot_offset in [0x00000, 0x26000]:
                # Reset Block 41 (Overworld state / entity cache)
                ow_base = slot_offset + 0x1E200
                data[ow_base : ow_base + 0x1400] = b'\x00' * 0x1400

                # Ricalcolo checksums
                for off, length, chk_off, chk_mir in BLOCKS:
                    chk = crc16_ccitt(data[slot_offset + off : slot_offset + off + length])
                    data[slot_offset + chk_off : slot_offset + chk_off + 2] = chk.to_bytes(2, 'little')
                    data[slot_offset + chk_mir : slot_offset + chk_mir + 2] = chk.to_bytes(2, 'little')

            with open(sp, 'wb') as f:
                f.write(data)
            print(f"    [OK] Cache overworld azzerata e checksum validati per: {sp.name}")
        except Exception as e:
            print(f"    [ERRORE] su {sp.name}: {e}")

    print("\n✅ BLOCCHI DAVANTI AL CANCELLO E ALLA MAPPA RIPRISTINATI AL 100%!")

if __name__ == "__main__":
    main()
