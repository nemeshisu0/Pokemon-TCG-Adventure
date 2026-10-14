#!/usr/bin/env python3
"""
Test di iniezione di entità fisiche visibili in Pokémon Bianco 2:
- Ripristina file 305, 444, 445 originali da roms/original/Bianco 2.nds.
- Modifica File 306 (Overworld di Zone 445 - Fattoria di Venturia):
  Aggiunge 2 entità fisiche visibili direttamente davanti al giocatore (fermo a X=35, Y=35, Verso SUD):
  1. Poké Ball a terra (Sprite 110) a (X=35, Y=36) -> 1 casella frontale!
  2. Lavoratore della Fattoria (Sprite 291) a (X=36, Y=35) -> 1 casella a destra del giocatore!
  Entrambi con Flag=0 (mai nascosti) e Script=0 (nessuna funzione/inermi).
  Mantiene il 100% di Furnitures, Warps, Triggers e Level Scripts originali!
- Reset della cache Overworld (Block 41) e ricalcolo di tutti i CRC nei salvataggi.
"""

import os
import sys
import struct
import shutil
from pathlib import Path
import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
ORIG_ROM_PATH = BASE_DIR / "roms" / "original" / "Bianco 2.nds"
MOD_ROM_PATH = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"

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
    (0x1C000, 0x0094, 0x1C096, 0x25F40), # 32 Mystery Gift
    (0x1C100, 0x0658, 0x1C75A, 0x25F42), # 33 Trainer Card
    (0x1C800, 0x0a94, 0x1D296, 0x25F44), # 34 Congratulation
    (0x1D300, 0x01ac, 0x1D4AE, 0x25F46), # 35 Game Sync
    (0x1D500, 0x03ec, 0x1D8EE, 0x25F48), # 36 Musical
    (0x1D900, 0x005c, 0x1D95E, 0x25F4A), # 37 Geonet
    (0x1DA00, 0x01e0, 0x1DBE2, 0x25F4C), # 38 Battle Subway Info
    (0x1DC00, 0x00a8, 0x1DCAA, 0x25F4E), # 39 Global Terminal
    (0x1DD00, 0x0460, 0x1E162, 0x25F50), # 40 Wi-Fi Configuration
    (0x1E200, 0x1400, 0x1F602, 0x25F52), # 41 Overworld State (Cache)
    (0x1F700, 0x02a4, 0x1F9A6, 0x25F54), # 42 Game Stats
    (0x1FA00, 0x00e0, 0x1FAE2, 0x25F56), # 43 Daycare
    (0x1FB00, 0x034c, 0x1FE4E, 0x25F58), # 44 Link Battle Data
    (0x1FF00, 0x04e0, 0x203E2, 0x25F5A), # 45 GTS Data
    (0x20400, 0x00f8, 0x204FA, 0x25F5C), # 46 Mailbox
    (0x20500, 0x02fc, 0x207FE, 0x25F5E), # 47 Battle Video
    (0x20800, 0x0094, 0x20896, 0x25F60), # 48 CGear Skin
    (0x20900, 0x035c, 0x20C5E, 0x25F62), # 49 Entralink State
    (0x20D00, 0x01d4, 0x20ED6, 0x25F64), # 50 Feeling Check
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

def crc16_ccitt(data):
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

def make_npc_bytes(npc_id, sprite_id, x, y, facing=0, z=2, script_id=0, flag=0):
    """
    Struttura autentica a 36 byte (18 short little-endian) per NPC in Gen 5:
    [0]: id
    [1]: sprite
    [2]: movementPermissions (0 = fermo)
    [3]: permissions2 (0)
    [4]: flag (0 = sempre visibile)
    [5]: scriptUsed (0 = inerte)
    [6]: defaultDirection (0=Nord, 1=Sud, 2=Ovest, 3=Est)
    [7..13]: sightRange, unk1, unk2, leashH, leashV, unk3, unk4
    [14]: xPosition
    [15]: yPosition
    [16]: unknown5 (0)
    [17]: zPosition (2 = ground elevation)
    """
    n = bytearray(36)
    struct.pack_into('<H', n, 0, npc_id)
    struct.pack_into('<H', n, 2, sprite_id)
    struct.pack_into('<H', n, 4, 0)
    struct.pack_into('<H', n, 6, 0)
    struct.pack_into('<H', n, 8, flag)
    struct.pack_into('<H', n, 10, script_id)
    struct.pack_into('<H', n, 12, facing)
    # 14..26 are 0
    struct.pack_into('<H', n, 28, x)
    struct.pack_into('<H', n, 30, y)
    struct.pack_into('<H', n, 32, 0)
    struct.pack_into('<H', n, 34, z)
    return bytes(n)

def patch_rom():
    print(f"==> 1. Lettura file originali da: {ORIG_ROM_PATH}")
    orig_rom = ndspy.rom.NintendoDSRom.fromFile(str(ORIG_ROM_PATH))
    orig_ow_narc = ndspy.narc.NARC(orig_rom.files[orig_rom.filenames.idOf('a/1/2/6')])

    print(f"==> 2. Caricamento ROM modificata: {MOD_ROM_PATH}")
    mod_rom = ndspy.rom.NintendoDSRom.fromFile(str(MOD_ROM_PATH))
    ow_id = mod_rom.filenames.idOf('a/1/2/6')
    mod_ow_narc = ndspy.narc.NARC(mod_rom.files[ow_id])

    # Ripristina 305, 444, 445 originali
    for f_idx in [305, 444, 445]:
        mod_ow_narc.files[f_idx] = orig_ow_narc.files[f_idx]
    print("    [OK] File 305, 444, 445 ripristinati da ROM originale!")

    # Prendi File 306 originale (Zone 445 - Fattoria di Venturia)
    orig_306 = orig_ow_narc.files[306]
    hdr_len, f_c, n_c, w_c, t_c = struct.unpack_from('<IBBBB', orig_306, 0)
    print(f"    File 306 originale: Furnitures={f_c}, NPCs={n_c}, Warps={w_c}, Triggers={t_c}, Total={len(orig_306)}B")

    # Splitta le sezioni originali:
    furn_end = 8 + f_c * 20
    npc_end = furn_end + n_c * 36
    warp_end = npc_end + w_c * 20
    trig_end = warp_end + t_c * 22

    furn_bytes = orig_306[8 : furn_end]
    npc_bytes = orig_306[furn_end : npc_end]
    warp_bytes = orig_306[npc_end : warp_end]
    trig_bytes = orig_306[warp_end : trig_end]
    trailer_bytes = orig_306[trig_end :] # Level scripts statici e dinamici

    # Creiamo 2 nuove entità di test:
    # 1. Poké Ball (Sprite 110) a X=35, Y=36 (subito davanti al giocatore rivolto a Sud)
    new_npc1 = make_npc_bytes(npc_id=n_c, sprite_id=110, x=35, y=36, facing=0, z=2, script_id=0, flag=0)
    # 2. Lavoratore (Sprite 291) a X=36, Y=35 (1 casella a destra del giocatore)
    new_npc2 = make_npc_bytes(npc_id=n_c + 1, sprite_id=291, x=36, y=35, facing=2, z=2, script_id=0, flag=0)

    all_npc_bytes = npc_bytes + new_npc1 + new_npc2
    new_n_c = n_c + 2

    # Calcolo nuovo header
    # payload_len = 4 + len(furn) + len(npcs) + len(warps) + len(trigs)
    new_payload_len = 4 + len(furn_bytes) + len(all_npc_bytes) + len(warp_bytes) + len(trig_bytes)
    new_header = bytearray(8)
    struct.pack_into('<IBBBB', new_header, 0, new_payload_len, f_c, new_n_c, w_c, t_c)

    new_file_306 = bytes(new_header) + furn_bytes + all_npc_bytes + warp_bytes + trig_bytes + trailer_bytes
    print(f"    File 306 modificato: Furnitures={f_c}, NPCs={new_n_c}, Warps={w_c}, Triggers={t_c}, Total={len(new_file_306)}B")

    mod_ow_narc.files[306] = new_file_306
    mod_rom.files[ow_id] = mod_ow_narc.save()

    print(f"==> 3. Salvataggio ROM modificata: {MOD_ROM_PATH}...")
    rom_bytes = bytearray(mod_rom.save())
    TARGET_SIZE = 536870912
    if len(rom_bytes) < TARGET_SIZE:
        print(f"    Padding a 512 MB...")
        rom_bytes += bytes([0xFF]) * (TARGET_SIZE - len(rom_bytes))
    with open(MOD_ROM_PATH, "wb") as f:
        f.write(rom_bytes)
    print("    [OK] ROM modificata e allineata con successo!")

def patch_saves():
    print("\n==> 4. Allineamento Salvataggi (Reset Cache Overworld Block 41)...")
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
            # 1. Assicuriamo spawn a Mappa 445, X=35, Y=35, Facing=1 (Sud)
            pos_base = slot + 0x19500
            map_id = 445
            x = 35
            y = 35
            z = 0
            facing = 1 # Sud

            # Continuous coords
            data[pos_base + 0x04 : pos_base + 0x06] = map_id.to_bytes(2, "little")
            data[pos_base + 0x06 : pos_base + 0x08] = facing.to_bytes(2, "little")
            data[pos_base + 0x10 : pos_base + 0x14] = (x * 0x10000 + 0x8000).to_bytes(4, "little")
            data[pos_base + 0x18 : pos_base + 0x1C] = (y * 0x10000 + 0x8000).to_bytes(4, "little")
            data[pos_base + 0x12 : pos_base + 0x14] = x.to_bytes(2, "little")
            data[pos_base + 0x1A : pos_base + 0x1C] = y.to_bytes(2, "little")

            # Grid coords (0x80)
            data[pos_base + 0x80 : pos_base + 0x84] = map_id.to_bytes(4, "little")
            data[pos_base + 0x84 : pos_base + 0x88] = (x * 0x10000 + 0x8000).to_bytes(4, "little")
            data[pos_base + 0x88 : pos_base + 0x8C] = (z * 0x10000).to_bytes(4, "little")
            data[pos_base + 0x8C : pos_base + 0x90] = (y * 0x10000 + 0x8000).to_bytes(4, "little")

            # 2. Reset Overworld Cache (Block 41) a 0x1E200
            data[slot + 0x1E200 : slot + 0x1E200 + 0x1400] = b'\x00' * 0x1400

            # 3. Ricalcolo Checksum di tutti i 74 blocchi
            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot + off
                actual_chk_off = slot + chk_off
                actual_chk_mir = slot + chk_mir
                chk = crc16_ccitt(data[actual_off : actual_off + length])
                data[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, "little")
                data[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, "little")

            # 4. Master Checksum Block 73
            chk_master = crc16_ccitt(data[slot + 0x25F00 : slot + 0x25F00 + 0x0094])
            data[slot + 0x25F00 + 0xA2 : slot + 0x25F00 + 0xA4] = chk_master.to_bytes(2, "little")

        with open(s_path, "wb") as f:
            f.write(data)
        print(f"    [OK] Salvataggio aggiornato e validato al 100%: {s_path.name}")

if __name__ == "__main__":
    patch_rom()
    patch_saves()
    print("\n✅ TUTTO COMPLETATO CON SUCCESSO!")
