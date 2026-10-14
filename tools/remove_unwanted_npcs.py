#!/usr/bin/env python3
"""
Rimuove gli NPC davanti alla fattoria (Hugh, Fattore, Worker, Herdier davanti)
e i cani/NPC dietro (Herdier smarrito a 51, 20 e Plasma grunt a 52, 20):
1. Carica File 306 originale.
2. Filtra la lista degli NPC mantenendo solo i Mareep, gli allenatori del recinto e gli strumenti.
3. Ricalcola gli ID progressivi (0..N-1), n_c e payload_len secondo lo standard FrostsGen5Editor.
4. Salva la ROM in roms/modified/Bianco 2.nds.
5. Sincronizza i salvataggi.
"""

import struct
from pathlib import Path
import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
ORIG_ROM_PATH = BASE_DIR / "roms" / "original" / "Bianco 2.nds"
MOD_ROM_PATH = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"

def main():
    print("==> 1. Caricamento ROM originale...")
    rom = ndspy.rom.NintendoDSRom.fromFile(str(ORIG_ROM_PATH))
    ow_id = rom.filenames.idOf('a/1/2/6')
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])
    f306 = ow_narc.files[306]

    payload_len, f_c, n_c, w_c, t_c = struct.unpack_from('<IBBBB', f306, 0)
    print(f"Originale: Furn={f_c}, NPCs={n_c}, Warps={w_c}, Triggers={t_c}")

    offset = 8
    furn_bytes = f306[offset : offset + f_c * 20]
    offset += f_c * 20

    # Leggi tutti gli NPC
    npcs = []
    for i in range(n_c):
        raw_npc = f306[offset : offset + 36]
        fields = list(struct.unpack('<18H', raw_npc))
        npcs.append(fields)
        offset += 36

    warp_bytes = f306[offset : offset + w_c * 32]
    offset += w_c * 32

    trig_bytes = f306[offset : offset + t_c * 20] # 20 bytes per trigger!
    offset += t_c * 20

    trailer_bytes = f306[offset:]

    # NPC da rimuovere:
    # Davanti alla fattoria:
    # - NPC 0: Worker a (25, 44) davanti alla casa
    # - NPC 1: Hugh a (46, 52) davanti sul sentiero
    # - NPC 2: Fattore a (46, 52) davanti sul sentiero
    # - NPC 10: Herdier a (47, 52) davanti al cancello
    # Cani / NPC dietro:
    # - NPC 3: Herdier a (51, 20) cane dietro nel bosco
    # - NPC 16: Plasma a (52, 20) dietro nel bosco
    remove_indices = {0, 1, 2, 3, 10, 16}

    filtered_npcs = []
    new_id = 0
    for idx, npc in enumerate(npcs):
        if idx in remove_indices:
            print(f"  [RIMOSSO] NPC {idx}: sprite={npc[1]}, X={npc[14]}, Y={npc[15]}")
            continue
        # Riassegna ID progressivo
        npc[0] = new_id
        new_id += 1
        filtered_npcs.append(npc)
        print(f"  [CONSERVATO] ID={npc[0]} (ex-{idx}): sprite={npc[1]}, X={npc[14]}, Y={npc[15]}")

    new_n_c = len(filtered_npcs)
    new_npc_bytes = b''.join([struct.pack('<18H', *npc) for npc in filtered_npcs])

    # Calcolo esatto header
    new_objects_len = 8 + len(furn_bytes) + len(new_npc_bytes) + len(warp_bytes) + len(trig_bytes)
    new_payload_len = new_objects_len - 4

    new_hdr = bytearray(8)
    struct.pack_into('<IBBBB', new_hdr, 0, new_payload_len, f_c, new_n_c, w_c, t_c)

    new_f306 = bytes(new_hdr) + furn_bytes + new_npc_bytes + warp_bytes + trig_bytes + trailer_bytes
    print(f"Nuovo File 306: NPCs={new_n_c}, payload_len={new_payload_len}, total_len={len(new_f306)}")

    ow_narc.files[306] = new_f306
    rom.files[ow_id] = ow_narc.save()

    print(f"==> 2. Scrittura ROM modificata: {MOD_ROM_PATH}...")
    rom_bytes = bytearray(rom.save())
    TARGET_SIZE = 536870912
    if len(rom_bytes) < TARGET_SIZE:
        rom_bytes += bytes([0xFF]) * (TARGET_SIZE - len(rom_bytes))
    with open(MOD_ROM_PATH, 'wb') as f:
        f.write(rom_bytes)
    print("✔ ROM scritta con successo (512 MB)!")

if __name__ == "__main__":
    main()
