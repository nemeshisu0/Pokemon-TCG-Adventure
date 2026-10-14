#!/usr/bin/env python3
"""
Costruisce la ROM definitiva con:
1. File 890 originale intonso (nessuna corruzione di bytecode!).
2. File 306 pulito:
   - Rimossi: Hugh (#1, 34), Fattore (#2, 35), Worker (#0, 291), Herdier cancello (#10, 307),
              Herdier bosco (#3, 307), Plasma grunt (#16, 293).
   - Conservati: tutti i 5 Mareep, i 3 allenatori del recinto, i 3 strumenti a terra.
   - Aggiunto: NPC Box PC (Sprite 15 / Allenatore o 291 / Assistente) a (47, 48) rivolto a Sud (1) con script 2108 (Script nativo PC di sistema!).
   - Aggiunto: Furniture PC a (47, 48) con script 2108 e tipo 4.
   - Trigger a 20 byte ciascuno, trailer preservato, header corretto.
3. Salvataggio ROM a 512 MB in roms/modified/Bianco 2.nds.
"""

import struct
from pathlib import Path
import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
ORIG_ROM_PATH = BASE_DIR / "roms" / "original" / "Bianco 2.nds"
MOD_ROM_PATH = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"

def make_furn(script_id, ftype, x, y, z=0):
    f = bytearray(20)
    struct.pack_into('<IIIII', f, 0, script_id, ftype, x, y, z)
    return bytes(f)

def make_npc(npc_id, sprite_id, x, y, facing=1, script_id=2108, flag=0):
    fields = [
        npc_id,       # 0: ID
        sprite_id,    # 1: Sprite (291 = Assistente)
        0,            # 2: Movement
        0,            # 3: Motion
        flag,         # 4: Flag (0 = Sempre visibile)
        script_id,    # 5: Script ID (2108 = Routine nativa Box PC!)
        facing,       # 6: Facing (1 = Sud, guarda verso il giocatore a 47, 49)
        0,            # 7: Line of sight
        0,            # 8: Unk8
        0,            # 9: Unk9
        0,            # 10: X Range
        0,            # 11: Y Range
        0,            # 12: Unk12
        0,            # 13: Unk13
        x,            # 14: X Tile (47)
        y,            # 15: Y Tile (48)
        0,            # 16: Z Elevation
        2             # 17: Type = 2 (Interactable NPC)
    ]
    return struct.pack('<18H', *fields)

def main():
    print("==> 1. Caricamento ROM originale intonsa...")
    rom = ndspy.rom.NintendoDSRom.fromFile(str(ORIG_ROM_PATH))
    ow_id = rom.filenames.idOf('a/1/2/6')
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])
    f306 = ow_narc.files[306]

    payload_len, f_c, n_c, w_c, t_c = struct.unpack_from('<IBBBB', f306, 0)
    print(f"Originale File 306: Furn={f_c}, NPCs={n_c}, Warps={w_c}, Triggers={t_c}")

    offset = 8
    furn_bytes = f306[offset : offset + f_c * 20]
    offset += f_c * 20

    # Leggi tutti i 17 NPC originali
    orig_npcs = []
    for i in range(n_c):
        raw_npc = f306[offset : offset + 36]
        fields = list(struct.unpack('<18H', raw_npc))
        orig_npcs.append(fields)
        offset += 36

    warp_bytes = f306[offset : offset + w_c * 32]
    offset += w_c * 32

    trig_bytes = f306[offset : offset + t_c * 20] # 20 byte per trigger!
    offset += t_c * 20

    trailer_bytes = f306[offset:]

    # Filtra gli NPC indesiderati
    # - NPC 0: Worker a (25, 44)
    # - NPC 1: Hugh a (46, 52)
    # - NPC 2: Farmer a (46, 52)
    # - NPC 3: Herdier cane bosco a (51, 20)
    # - NPC 10: Herdier cancello a (47, 52)
    # - NPC 16: Plasma grunt a (52, 20)
    remove_indices = {0, 1, 2, 3, 10, 16}

    filtered_npcs = []
    new_id = 0
    for idx, npc in enumerate(orig_npcs):
        if idx in remove_indices:
            print(f"  [RIMOSSO] NPC {idx}: sprite={npc[1]}, X={npc[14]}, Y={npc[15]}")
            continue
        npc[0] = new_id
        new_id += 1
        filtered_npcs.append(npc)
        print(f"  [CONSERVATO] ID={npc[0]} (ex-{idx}): sprite={npc[1]}, X={npc[14]}, Y={npc[15]}")

    # Aggiungi NPC Box PC a X=47, Y=48 rivolto a Sud (1)
    # Sprite 291 (Assistente) con Script 10105 (PC nativo!)
    box_npc_bytes = make_npc(new_id, sprite_id=291, x=47, y=48, facing=1, script_id=10105, flag=0)
    new_id += 1
    print(f"  [AGGIUNTO] NPC Box PC ID={new_id-1}: sprite=291 a (47, 48), script=10105")

    new_npc_bytes = b''.join([struct.pack('<18H', *npc) for npc in filtered_npcs]) + box_npc_bytes
    new_n_c = len(filtered_npcs) + 1

    # Aggiungi anche Furniture PC a (47, 48) con script 10105
    new_furn_bytes = furn_bytes + make_furn(script_id=10105, ftype=4, x=47, y=48, z=0)
    new_f_c = f_c + 1

    # Ricalcolo Header
    new_objects_len = 8 + len(new_furn_bytes) + len(new_npc_bytes) + len(warp_bytes) + len(trig_bytes)
    new_payload_len = new_objects_len - 4

    new_hdr = bytearray(8)
    struct.pack_into('<IBBBB', new_hdr, 0, new_payload_len, new_f_c, new_n_c, w_c, t_c)

    new_f306 = bytes(new_hdr) + new_furn_bytes + new_npc_bytes + warp_bytes + trig_bytes + trailer_bytes
    print(f"Nuovo File 306: Furn={new_f_c}, NPCs={new_n_c}, payload_len={new_payload_len}, total_len={len(new_f306)}")

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
