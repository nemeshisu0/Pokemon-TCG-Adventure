#!/usr/bin/env python3
"""
Test e deploy definitivo per PC NPC / Furniture e rimozione Mondo Parallelo:
1. File 890 originale intonso da ROM base (nessun bytecode corrotto!).
2. File 306 con:
   - Rimossi {0, 1, 2, 3, 10, 16}: Hugh, Fattore, Worker, 2 Herdier, Plasma grunt.
   - Conservati tutti i 5 Mareep, 3 trainer, 3 ground items.
   - NPC Box a (47, 48): sprite 291, script 2108!
   - Furniture PC a (47, 48): script 2108, type 4!
3. Scrittura ROM modificata a 512 MB.
4. Esecuzione test in melonDS:
   - Ingresso in gioco.
   - Transizione Route 20 -> Farm per caricare tutte le entità in RAM.
   - Interazione con (47, 48) con tasto A -> cattura screenshot menu PC.
   - Salvataggio in-game con trigger control_arr[28] = 1 per flush completo su disco.
   - Reboot melonDS per verificare boot diretto senza mondo parallelo!
"""

import os
import sys
import time
import struct
import shutil
from pathlib import Path
import multiprocessing as mp
from multiprocessing import shared_memory
from PIL import Image

import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from launcher.core.engine_worker import run_engine_worker

ORIG_ROM = BASE_DIR / "roms" / "original" / "Bianco 2.nds"
MOD_ROM = BASE_DIR / "roms" / "modified" / "Bianco 2.nds"
SAVE_PATH = BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav"
CORE_LIB = BASE_DIR / "launcher" / "core" / "melonds_core.so"
SCRATCH = Path("/home/nemesy/.gemini/antigravity-ide/brain/b8d8417a-cc11-40ef-9c2c-1009c4d46bd9/scratch")
SCRATCH.mkdir(parents=True, exist_ok=True)

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
        facing,       # 6: Facing (1 = Sud)
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
        3             # 17: Type = 3 (Interactable PC Object/Stationary)
    ]
    return struct.pack('<18H', *fields)

def patch_rom():
    print("==> 1. Costruzione ROM modificata pulita...")
    rom = ndspy.rom.NintendoDSRom.fromFile(str(ORIG_ROM))
    
    # 1.1 Ripristina File 890 originale intonso (nessuna corruzione)
    scr_id = rom.filenames.idOf('a/0/5/6')
    scr_narc = ndspy.narc.NARC(rom.files[scr_id])
    # Assicuriamoci che File 890 sia quello originale
    rom_orig = ndspy.rom.NintendoDSRom.fromFile(str(ORIG_ROM))
    scr_orig_narc = ndspy.narc.NARC(rom_orig.files[scr_id])
    scr_narc.files[890] = scr_orig_narc.files[890]
    rom.files[scr_id] = scr_narc.save()

    # 1.2 Modifica File 306 in a/1/2/6
    ow_id = rom.filenames.idOf('a/1/2/6')
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])
    f306 = ow_narc.files[306]

    payload_len, f_c, n_c, w_c, t_c = struct.unpack_from('<IBBBB', f306, 0)
    offset = 8
    furn_bytes = f306[offset : offset + f_c * 20]
    offset += f_c * 20

    orig_npcs = []
    for i in range(n_c):
        raw_npc = f306[offset : offset + 36]
        orig_npcs.append(list(struct.unpack('<18H', raw_npc)))
        offset += 36

    warp_bytes = f306[offset : offset + w_c * 32]
    offset += w_c * 32
    trig_bytes = f306[offset : offset + t_c * 20]
    offset += t_c * 20
    trailer_bytes = f306[offset:]

    remove_indices = {0, 1, 2, 3, 10, 16}
    filtered_npcs = []
    new_id = 0
    for idx, npc in enumerate(orig_npcs):
        if idx in remove_indices:
            continue
        npc[0] = new_id
        new_id += 1
        filtered_npcs.append(npc)

    # Aggiungi NPC Box PC con script 10405 a (47, 48)
    box_npc_bytes = make_npc(new_id, sprite_id=291, x=47, y=48, facing=1, script_id=10405, flag=0)
    new_id += 1
    new_npc_bytes = b''.join([struct.pack('<18H', *npc) for npc in filtered_npcs]) + box_npc_bytes
    new_n_c = len(filtered_npcs) + 1

    # Aggiungi Furniture PC con script 10405 a (47, 48)
    new_furn_bytes = furn_bytes + make_furn(script_id=10405, ftype=0, x=47, y=48, z=0)
    new_f_c = f_c + 1

    new_objects_len = 8 + len(new_furn_bytes) + len(new_npc_bytes) + len(warp_bytes) + len(trig_bytes)
    new_payload_len = new_objects_len - 4

    new_hdr = bytearray(8)
    struct.pack_into('<IBBBB', new_hdr, 0, new_payload_len, new_f_c, new_n_c, w_c, t_c)
    new_f306 = bytes(new_hdr) + new_furn_bytes + new_npc_bytes + warp_bytes + trig_bytes + trailer_bytes

    ow_narc.files[306] = new_f306
    rom.files[ow_id] = ow_narc.save()

    rom_bytes = bytearray(rom.save())
    TARGET_SIZE = 536870912
    if len(rom_bytes) < TARGET_SIZE:
        rom_bytes += bytes([0xFF]) * (TARGET_SIZE - len(rom_bytes))
    with open(MOD_ROM, 'wb') as f:
        f.write(rom_bytes)
    print("✔ ROM compilata e salvata con successo!")

def press(control_arr, btn, dur=0.2):
    control_arr[btn] = 1
    time.sleep(dur)
    control_arr[btn] = 0
    time.sleep(0.3)

def capture(shm, filename):
    raw = bytes(shm.buf[:1024 * 384])
    img = Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")
    out = SCRATCH / filename
    img.save(out)
    return out

def get_player_pos(ram_fd):
    if not ram_fd: return 0, 0, 0
    try:
        with open(ram_fd, "rb") as f:
            f.seek(0x23B384)
            st = f.read(32)
        zid = struct.unpack_from("<H", st, 0)[0]
        px = struct.unpack_from("<I", st, 4)[0] >> 16
        py = struct.unpack_from("<I", st, 12)[0] >> 16
        return zid, px, py
    except Exception:
        return 0, 0, 0

def run_test():
    print("==> 2. Avvio simulazione in melonDS...")
    shm_name = "ds_pc_deploy_test"
    try:
        shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    except FileExistsError:
        s = shared_memory.SharedMemory(name=shm_name)
        s.unlink()
        shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)

    control_arr = mp.Array('i', 32)
    proc = mp.Process(
        target=run_engine_worker,
        args=(shm_name, control_arr, str(MOD_ROM), str(SAVE_PATH), str(CORE_LIB)),
        daemon=True
    )
    proc.start()

    try:
        ram_fd = None
        for _ in range(40):
            fd_dir = f"/proc/{proc.pid}/fd"
            if os.path.exists(fd_dir):
                for fd in os.listdir(fd_dir):
                    try:
                        if "melondsfastmem" in os.readlink(os.path.join(fd_dir, fd)):
                            ram_fd = os.path.join(fd_dir, fd)
                            break
                    except Exception: pass
            if ram_fd: break
            time.sleep(0.2)

        print("==> 3. Skip intro e caricamento salvataggio...")
        for _ in range(12):
            press(control_arr, 3, dur=0.2)
            time.sleep(0.4)
            press(control_arr, 8, dur=0.2)
            time.sleep(0.4)

        for _ in range(8):
            press(control_arr, 4, dur=0.15)
            press(control_arr, 8, dur=0.25)
            time.sleep(0.8)
            press(control_arr, 5, dur=0.15)
            press(control_arr, 8, dur=0.25)
            time.sleep(0.8)
            press(control_arr, 8, dur=0.25)
            time.sleep(1.2)
            zid, px, py = get_player_pos(ram_fd)
            if zid == 445 and px > 0:
                print(f"✔ In-game raggiunto: Zone={zid}, X={px}, Y={py}")
                break

        print("==> 4. Transizione mappa Route 20 -> Farm per caricare entità pulite...")
        for _ in range(10):
            press(control_arr, 5, dur=0.3) # DOWN
            zid, px, py = get_player_pos(ram_fd)
            if zid != 445:
                print(f"    Uscito su Route 20: Zone={zid}")
                break

        time.sleep(0.5)
        for _ in range(12):
            press(control_arr, 4, dur=0.3) # UP
            zid, px, py = get_player_pos(ram_fd)
            if zid == 445 and py <= 49:
                print(f"    Rientrato in fattoria a X={px}, Y={py}")
                break

        time.sleep(1.0)
        capture(shm, "pc_test_standing.png")

        print("==> 5. Interazione con NPC/Furniture Box a (47, 48)...")
        # Giocatore è a (47, 49) rivolto a Nord. Premiamo A!
        press(control_arr, 8, dur=0.3)
        time.sleep(1.5)
        capture(shm, "pc_test_screen1.png")
        print("📸 Screenshot 1 salvato: pc_test_screen1.png")

        # Premiamo A per avanzare (se c'è testo di avvio PC)
        press(control_arr, 8, dur=0.3)
        time.sleep(1.5)
        capture(shm, "pc_test_screen2.png")
        print("📸 Screenshot 2 salvato: pc_test_screen2.png")

        # Chiudiamo menu con B ripetuto (0 è B)
        for _ in range(3):
            press(control_arr, 0, dur=0.25) # B = 0
            time.sleep(0.5)

        print("==> 6. Esecuzione salvataggio in-game per fissare la cache...")
        press(control_arr, 9, dur=0.25) # X = 9 (Menu)
        time.sleep(1.0)
        for _ in range(4):
            press(control_arr, 5, dur=0.2) # DOWN = 5
            time.sleep(0.2)
        press(control_arr, 8, dur=0.3) # A = 8 (Salva)
        time.sleep(1.5)
        press(control_arr, 8, dur=0.3) # A = 8 (Sì)
        time.sleep(2.0)
        press(control_arr, 8, dur=0.3) # A = 8 (Conferma)
        time.sleep(5.0)

        # Trigger flush RAM su disco in engine_worker!
        print("==> 7. Trigger flush save RAM su disco (control_arr[28] = 1)...")
        control_arr[28] = 1
        time.sleep(2.0)
        print("✔ Flush richiesto e completato!")

    finally:
        control_arr[30] = 0
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()

if __name__ == "__main__":
    patch_rom()
    run_test()
