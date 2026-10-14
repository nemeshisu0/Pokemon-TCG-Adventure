#!/usr/bin/env python3
"""
Deploy Visivo Perfetto per la Fattoria di Venturia (Map 445 / File 306):
1. Ripristina file 305, 444, 445 originali intatti.
2. Ricostruisce File 306 rispettando al 100% la struttura esatta (byte-for-byte verificata):
   - 22 Furnitures (originali intatte)
   - 17 NPCs vanilla intatti (NPC 10 Herdier al Cancello sbloccato con flag=0)
   - + Nuovi NPC/Pokémon posizionati con Flag=0 e Type=2 (Sprite 3D visibili):
       * Mareep (Sprite 363) a X=34, Y=37 (immediatamente a sinistra del giocatore a 35, 37)
       * Mareep (Sprite 363) a X=35, Y=36 (immediatamente a nord/dietro al giocatore a 35, 37)
       * Poké Ball (Sprite 110) a X=34, Y=36 (nel prato aperto visibile subito a nord-ovest del giocatore)
       * Herdier (Sprite 307) a X=47, Y=52 (Cancello Sud - barriera fisica e visiva)
       * Mareep (Sprite 363) a X=46, Y=52 (Cancello Sud lato sinistro)
       * Mareep (Sprite 363) a X=48, Y=52 (Cancello Sud lato destro)
   - 1 Warp (originale intatto)
   - 6 Triggers (originali intatti, 20 byte ciascuno)
   - 16 byte Trailer (Level Scripts originali intatti)
   - payload_len = 1208 + (num_nuovi_npc * 36)
3. Salva la ROM in roms/modified/Bianco 2.nds (allineata a 512 MB).
4. Ripristina Block 34 (Entralink Forest) e azzera la cache Block 41 nei salvataggi, ricalcolando tutti i CRC16.
"""

import os
import sys
import struct
from pathlib import Path
import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
ORIG_ROM_PATH = BASE_DIR / "roms" / "original" / "Bianco 2.nds"
MOD_ROM_PATH = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"

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

def make_npc(npc_id: int, sprite_id: int, x: int, y: int, facing: int = 1, script_id: int = 0) -> bytes:
    """
    Crea un NPC / Pokémon con modello 3D overworld e visibilità permanente (Flag=0, Type=2).
    """
    fields = (
        npc_id,       # 0: ID progressivo
        sprite_id,    # 1: Sprite ID (363 = Mareep, 307 = Herdier, 110 = Poké Ball)
        0,            # 2: Movement (0 = stationary)
        0,            # 3: Motion
        0,            # 4: Flag = 0 (PERMANENTEMENTE VISIBILE)
        script_id,    # 5: Script ID (13 = Mareep cry, 11 = Herdier cry, 0 = Poké Ball)
        facing,       # 6: Facing (0=Nord, 1=Sud, 2=Ovest, 3=Est)
        0, 0, 0,      # 7..9
        0, 0, 0, 0,   # 10..13
        x,            # 14: X Grid Position
        y,            # 15: Y Grid Position
        0,            # 16: Elevation (0 = livello suolo)
        2             # 17: Type = 2 (Interactable 3D Billboard entity)
    )
    return struct.pack('<18H', *fields)

def main():
    print(f"==> 1. Caricamento ROM originale: {ORIG_ROM_PATH}...")
    rom = ndspy.rom.NintendoDSRom.fromFile(str(ORIG_ROM_PATH))
    ow_id = rom.filenames.idOf('a/1/2/6')
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])

    # Ripristina files 305, 444, 445 originali
    orig_ow_narc = ndspy.narc.NARC(ndspy.rom.NintendoDSRom.fromFile(str(ORIG_ROM_PATH)).files[ow_id])
    ow_narc.files[305] = orig_ow_narc.files[305]
    ow_narc.files[444] = orig_ow_narc.files[444]
    ow_narc.files[445] = orig_ow_narc.files[445]

    # Analisi File 306 originale
    f306_orig = orig_ow_narc.files[306]
    orig_payload_len, f_c, n_c, w_c, t_c = struct.unpack_from('<IBBBB', f306_orig, 0)
    print(f"    File 306 originale: Furn={f_c}, NPCs={n_c}, Warps={w_c}, Triggers={t_c}, Len={len(f306_orig)}")

    offset = 8
    furn_bytes = f306_orig[offset : offset + f_c * 20]
    offset += f_c * 20

    npc_list = []
    for i in range(n_c):
        npc_data = bytearray(f306_orig[offset : offset + 36])
        # Sblocca NPC 10 (Herdier originale al cancello a 47, 52) impostando Flag=0
        if i == 10:
            struct.pack_into('<H', npc_data, 8, 0)
            print("    [OK] Herdier originale NPC 10 (47, 52) impostato Flag=0!")
        npc_list.append(bytes(npc_data))
        offset += 36

    warp_bytes = f306_orig[offset : offset + w_c * 32]
    offset += w_c * 32

    trig_bytes = f306_orig[offset : offset + t_c * 20] # 20 bytes per trigger!
    offset += t_c * 20

    trailer_bytes = f306_orig[offset:] # 16 byte Level Scripts trailer
    print(f"    Offset oggetti: {offset}, Trailer: {len(trailer_bytes)} bytes")

    # Nuovi NPC da aggiungere:
    # Il giocatore è fermo a X=35, Y=37!
    # 1. Mareep a X=34, Y=37 (direttamente alla sua sinistra, campo aperto!)
    # 2. Mareep a X=35, Y=36 (direttamente sopra/dietro di lui!)
    # 3. Poké Ball a X=34, Y=36 (in diagonale nel prato visibile!)
    # 4. Herdier barriera Cancello Sud a X=47, Y=52
    # 5. Mareep barriera Cancello Sud a X=46, Y=52
    # 6. Mareep barriera Cancello Sud a X=48, Y=52
    new_npcs = [
        make_npc(len(npc_list),     363, 34, 37, facing=3, script_id=13), # Mareep guarda verso il giocatore a Est
        make_npc(len(npc_list) + 1, 363, 35, 36, facing=1, script_id=13), # Mareep guarda verso il giocatore a Sud
        make_npc(len(npc_list) + 2, 110, 34, 36, facing=1, script_id=0),  # Poké Ball Item nel prato aperto
        make_npc(len(npc_list) + 3, 307, 47, 52, facing=1, script_id=11), # Barriera Herdier cancello
        make_npc(len(npc_list) + 4, 363, 46, 52, facing=1, script_id=13), # Barriera Mareep cancello SX
        make_npc(len(npc_list) + 5, 363, 48, 52, facing=1, script_id=13), # Barriera Mareep cancello DX
    ]

    for npc in new_npcs:
        npc_list.append(npc)

    new_n_c = len(npc_list)
    new_npc_bytes = b''.join(npc_list)

    # Calcolo esatto del nuovo payload_len
    # payload_len = dimensione da byte 4 alla fine degli oggetti (escluso il trailer di 16 byte e i primi 4 byte)
    new_objects_len = 8 + len(furn_bytes) + len(new_npc_bytes) + len(warp_bytes) + len(trig_bytes)
    new_payload_len = new_objects_len - 4

    new_hdr = bytearray(8)
    struct.pack_into('<IBBBB', new_hdr, 0, new_payload_len, f_c, new_n_c, w_c, t_c)

    new_f306 = bytes(new_hdr) + furn_bytes + new_npc_bytes + warp_bytes + trig_bytes + trailer_bytes
    print(f"    [OK] Nuovo File 306 creato: {new_n_c} NPCs totali, len={len(new_f306)}, payload_len={new_payload_len}")

    ow_narc.files[306] = new_f306
    rom.files[ow_id] = ow_narc.save()

    # Scrittura ROM
    print(f"==> 2. Scrittura ROM modificata: {MOD_ROM_PATH}...")
    rom_bytes = bytearray(rom.save())
    TARGET_SIZE = 536870912
    if len(rom_bytes) < TARGET_SIZE:
        rom_bytes += bytes([0xFF]) * (TARGET_SIZE - len(rom_bytes))
    with open(MOD_ROM_PATH, 'wb') as f:
        f.write(rom_bytes)
    print("    [OK] ROM scritta con successo (512 MB)!")

    # Aggiornamento salvataggi
    print("\n==> 3. Sincronizzazione Salvataggi...")
    # Ripristina Block 34 (Entralink Forest) dal backup pulito
    clean_backup = BASE_DIR / "saves" / "backups" / "save_backup_20261010_200851.sav"
    clean_b34 = clean_backup.read_bytes()[0x22A00 : 0x22A00 + 0x850] if clean_backup.exists() else None

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
            # Ripristina Block 34
            if clean_b34:
                data[slot + 0x22A00 : slot + 0x22A00 + 0x850] = clean_b34
            # Pulisce Block 41 Overworld Cache
            data[slot + 0x1E200 : slot + 0x1E200 + 0x1400] = b'\x00' * 0x1400
            for off, length, chk_off, chk_mir in BLOCKS:
                actual_off = slot + off
                actual_chk_off = slot + chk_off
                actual_chk_mir = slot + chk_mir
                chk = crc16_ccitt(data[actual_off : actual_off + length])
                data[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, 'little')
                data[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, 'little')
        s_path.write_bytes(data)
        print(f"    [OK] Salvataggio aggiornato e CRC calcolati: {s_path.name}")

if __name__ == "__main__":
    main()
