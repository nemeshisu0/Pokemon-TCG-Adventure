#!/usr/bin/env python3
import os
import sys
import time
import struct
import multiprocessing as mp
from multiprocessing import shared_memory
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from launcher.core.engine_worker import run_engine_worker

ROM_PATH = str(BASE_DIR / "roms" / "modified" / "Bianco 2.nds")
SAVE_PATH = str(BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav")
CORE_LIB = str(BASE_DIR / "launcher" / "core" / "melonds_core.so")
SCRATCH = Path("/home/nemesy/.gemini/antigravity-ide/brain/b8d8417a-cc11-40ef-9c2c-1009c4d46bd9/scratch")
SCRATCH.mkdir(parents=True, exist_ok=True)

def press(ctrl, btn, dur=0.2):
    ctrl[btn] = 1
    time.sleep(dur)
    ctrl[btn] = 0
    time.sleep(0.3)

def capture(shm, fname):
    raw = bytes(shm.buf[:1024 * 384])
    img = Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")
    out = SCRATCH / fname
    img.save(out)
    return out

def get_pos(ram_fd):
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

def main():
    shm_name = "ds_live_npc_test"
    try:
        shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    except FileExistsError:
        s = shared_memory.SharedMemory(name=shm_name)
        s.unlink()
        shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)

    control_arr = mp.Array("i", 32)
    proc = mp.Process(target=run_engine_worker, args=(shm_name, control_arr, ROM_PATH, SAVE_PATH, CORE_LIB), daemon=True)
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

        print("==> 1. Skip intro...")
        for _ in range(14):
            press(control_arr, 3, dur=0.2)
            time.sleep(0.4)
            press(control_arr, 8, dur=0.2)
            time.sleep(0.4)

        print("==> 2. Continua e C-Gear...")
        in_game = False
        for step in range(10):
            press(control_arr, 4, dur=0.15)
            press(control_arr, 8, dur=0.25)
            time.sleep(0.8)
            press(control_arr, 5, dur=0.15)
            press(control_arr, 8, dur=0.25)
            time.sleep(0.8)
            press(control_arr, 8, dur=0.25)
            time.sleep(1.5)
            zid, px, py = get_pos(ram_fd)
            if zid in [444, 445] and px > 0:
                print(f"✔ Overworld raggiunto: Zone={zid}, X={px}, Y={py}")
                in_game = True
                break

        if not in_game:
            capture(shm, "failed_boot.png")
            print("❌ Impossibile entrare in-game!")
            return

        # Cattura schermata di boot immediato
        capture(shm, "boot_immediate.png")
        print("📸 Screenshot catturato: boot_immediate.png")

        # Step Sud su Route 20 e rientro per ricaricare la mappa pulita
        print("==> 3. Transizione mappa...")
        for _ in range(10):
            press(control_arr, 5, dur=0.3) # DOWN
            zid, px, py = get_pos(ram_fd)
            if zid != 445:
                print(f"    Uscito su Route 20: Zone={zid}")
                break
        time.sleep(0.5)

        for _ in range(12):
            press(control_arr, 4, dur=0.3) # UP
            zid, px, py = get_pos(ram_fd)
            if zid == 445 and py <= 49:
                print(f"    Rientrato in fattoria a X={px}, Y={py}")
                break
        time.sleep(1.0)

        capture(shm, "ranch_entered.png")
        print("📸 Screenshot catturato: ranch_entered.png")

        # Ora il giocatore è a (47, 49) rivolto a Nord verso l'NPC Box a (47, 48)
        print("==> 4. Interazione con l'NPC Box (Tasto A)...")
        press(control_arr, 8, dur=0.3)
        time.sleep(1.5)
        capture(shm, "npc_interact_1.png")
        print("📸 Screenshot catturato: npc_interact_1.png")

        press(control_arr, 8, dur=0.3)
        time.sleep(1.5)
        capture(shm, "npc_interact_2.png")
        print("📸 Screenshot catturato: npc_interact_2.png")

        # Premiamo A ancora per vedere se apre il PC o menu opzioni
        press(control_arr, 8, dur=0.3)
        time.sleep(1.5)
        capture(shm, "npc_interact_3.png")
        print("📸 Screenshot catturato: npc_interact_3.png")

    finally:
        control_arr[30] = 0
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()
        print("Test completato.")

if __name__ == "__main__":
    main()
