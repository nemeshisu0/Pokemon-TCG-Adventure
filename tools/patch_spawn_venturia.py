#!/usr/bin/env python3
"""
Imposta lo spawn in ENTRAMBI i blocchi di salvataggio (Slot 1 e Slot 2)
su Mappa 444 (Fattoria di Venturia) alle coordinate X=15, Y=25.
"""

import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_SAV = os.path.join(BASE_DIR, "saves", "archive", "Pokemon_Bianco_2_100percent.sav")
TARGET_SAV = os.path.join(BASE_DIR, "saves", "Pokémon Bianco 2.sav")
MODIFIED_SAV = os.path.join(BASE_DIR, "roms", "modified", "Bianco 2.sav")

def crc16_ccitt(data):
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

def patch_slot(data, base_offset, chk_block_base):
    # Map ID 444 (0x01BC) = Fattoria di Venturia
    map_id = 444
    pos_x = 15
    pos_y = 25
    pos_z = 0

    # 1. Continuous coordinates
    data[base_offset + 0x04 : base_offset + 0x06] = map_id.to_bytes(2, "little")
    data[base_offset + 0x10 : base_offset + 0x14] = (pos_x * 0x10000 + 0x8000).to_bytes(4, "little")
    data[base_offset + 0x18 : base_offset + 0x1C] = (pos_y * 0x10000 + 0x8000).to_bytes(4, "little")

    # 2. Grid coordinates (offset 0x80)
    data[base_offset + 0x80 : base_offset + 0x84] = map_id.to_bytes(4, "little")
    data[base_offset + 0x86 : base_offset + 0x88] = pos_x.to_bytes(2, "little")
    data[base_offset + 0x8A : base_offset + 0x8C] = pos_z.to_bytes(2, "little")
    data[base_offset + 0x8E : base_offset + 0x90] = pos_y.to_bytes(2, "little")

    # 3. Checksum blocco Trainer Position (len 0x00A8)
    block = data[base_offset : base_offset + 0x00A8]
    chk = crc16_ccitt(block)
    data[base_offset + 0xAA : base_offset + 0xAC] = chk.to_bytes(2, "little")
    data[chk_block_base + 0x38 : chk_block_base + 0x3A] = chk.to_bytes(2, "little")

    # 4. Master Checksum (len 0x0094)
    master_block = data[chk_block_base : chk_block_base + 0x0094]
    chk_master = crc16_ccitt(master_block)
    data[chk_block_base + 0xA2 : chk_block_base + 0xA4] = chk_master.to_bytes(2, "little")

    return chk, chk_master

def main():
    print(f"==> Caricamento salvataggio base da: {ARCHIVE_SAV}...")
    with open(ARCHIVE_SAV, "rb") as f:
        data = bytearray(f.read())

    # Patch Slot 1 (0x19500, checksum table a 0x25F00)
    chk1, m1 = patch_slot(data, 0x19500, 0x25F00)
    print(f"    Slot 1 aggiornato: Map 444, X=15, Y=25 (Block CRC={hex(chk1)}, Master={hex(m1)})")

    # Patch Slot 2 (0x3F500, checksum table a 0x4BF00)
    chk2, m2 = patch_slot(data, 0x3F500, 0x4BF00)
    print(f"    Slot 2 aggiornato: Map 444, X=15, Y=25 (Block CRC={hex(chk2)}, Master={hex(m2)})")

    # Salva il nuovo file di salvataggio
    with open(TARGET_SAV, "wb") as f:
        f.write(data)
    print(f"==> Salvataggio scritto in: {TARGET_SAV}")

    # Aggiorna il collegamento simbolico in roms/modified/Bianco 2.sav
    if os.path.islink(MODIFIED_SAV) or os.path.exists(MODIFIED_SAV):
        os.remove(MODIFIED_SAV)
    os.symlink("../../saves/Pokémon Bianco 2.sav", MODIFIED_SAV)
    print(f"==> Collegamento creato: {MODIFIED_SAV} -> {TARGET_SAV}")

if __name__ == "__main__":
    main()
