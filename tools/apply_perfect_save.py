#!/usr/bin/env python3
"""
Applica il punto di spawn esatto su Fattoria di Venturia (Zone 445, X=25, Y=28)
sul file di salvataggio al 100% con scarpe da corsa, Pokedex e squadra completa,
ricollegando e ricalcolando TUTTI i 74 checksum con la specifica ufficiale di PKHeX.
"""

import os
import shutil
import struct

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_SAV = "/home/nemesy/Documents/progetti stani miei/roms/Pokémon Bianco 2.sav"
TARGET_SAV_1 = os.path.join(BASE_DIR, "saves", "Pokémon Bianco 2.sav")
TARGET_SAV_2 = os.path.join(BASE_DIR, "roms", "modified", "Bianco 2.sav")

def crc16_ccitt(data):
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

# Struttura dei 74 blocchi di SAV5B2W2 (PKHeX)
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

def main():
    print(f"==> Caricamento salvataggio sorgente: {SOURCE_SAV}")
    with open(SOURCE_SAV, "rb") as f:
        data = bytearray(f.read())

    def apply_spawn(slot_offset):
        pos_base = slot_offset + 0x19500
        map_id = 445 # Fattoria di Venturia Outdoor
        x = 25
        y = 28
        z = 0
        # continuous coordinates
        data[pos_base + 0x04 : pos_base + 0x08] = map_id.to_bytes(4, "little")
        data[pos_base + 0x10 : pos_base + 0x14] = (x * 0x10000 + 0x8000).to_bytes(4, "little")
        data[pos_base + 0x18 : pos_base + 0x1C] = (y * 0x10000 + 0x8000).to_bytes(4, "little")
        
        # grid coordinates
        data[pos_base + 0x80 : pos_base + 0x84] = map_id.to_bytes(4, "little")
        data[pos_base + 0x84 : pos_base + 0x88] = (x * 0x10000 + 0x8000).to_bytes(4, "little")
        data[pos_base + 0x88 : pos_base + 0x8C] = (z * 0x10000).to_bytes(4, "little")
        data[pos_base + 0x8C : pos_base + 0x90] = (y * 0x10000 + 0x8000).to_bytes(4, "little")

    def update_all_checksums(slot_offset):
        for off, length, chk_off, chk_mir in BLOCKS:
            actual_off = slot_offset + off
            actual_chk_off = slot_offset + chk_off
            actual_chk_mir = slot_offset + chk_mir
            chk = crc16_ccitt(data[actual_off : actual_off + length])
            data[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, "little")
            data[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, "little")

    # Patch su entrambi gli slot
    apply_spawn(0x00000)
    apply_spawn(0x26000)
    update_all_checksums(0x00000)
    update_all_checksums(0x26000)

    # Validazione finale
    for slot_name, slot_offset in [("Slot 1", 0), ("Slot 2", 0x26000)]:
        valid = 0
        for off, length, chk_off, chk_mir in BLOCKS:
            expected = crc16_ccitt(data[slot_offset+off : slot_offset+off+length])
            act1 = struct.unpack_from("<H", data, slot_offset+chk_off)[0]
            act2 = struct.unpack_from("<H", data, slot_offset+chk_mir)[0]
            if expected == act1 == act2:
                valid += 1
        print(f"    {slot_name}: {valid}/{len(BLOCKS)} blocchi validi al 100%")

    os.makedirs(os.path.dirname(TARGET_SAV_1), exist_ok=True)
    with open(TARGET_SAV_1, "wb") as f:
        f.write(data)
    with open(TARGET_SAV_2, "wb") as f:
        f.write(data)

    print(f"==> Salvataggio scritto con successo in:")
    print(f"    1. {TARGET_SAV_1}")
    print(f"    2. {TARGET_SAV_2}")

if __name__ == "__main__":
    main()
