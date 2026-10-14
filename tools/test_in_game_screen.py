#!/usr/bin/env python3
"""
Navigatore robusto per l'Overworld:
Attende il boot, salta l'intro con START, entra nel menu, seleziona CONTINUA,
rifiuta il C-Gear ed entra in Overworld per catturare lo screenshot degli NPC visibili.
"""

import os
import sys
import time
import secrets
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
SCRATCH_DIR = Path("/home/nemesy/.gemini/antigravity-ide/brain/b8d8417a-cc11-40ef-9c2c-1009c4d46bd9/scratch")
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

def press(control_arr, btn, dur=0.25):
    control_arr[btn] = 1
    time.sleep(dur)
    control_arr[btn] = 0
    time.sleep(0.35)

def capture_screen(shm, filename):
    raw = bytes(shm.buf[:1024 * 384])
    img = Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")
    out = SCRATCH_DIR / filename
    img.save(out)
    return out

def is_gameplay_screen(img):
    # Lo schermo superiore di gameplay in overworld ha colori vivaci (verde degli alberi, erba)
    # L'intro ha spesso bianco/nero o ciano fisso
    top = img.crop((0, 0, 256, 192))
    colors = top.getcolors(maxcolors=10000)
    # Se ci sono molti colori distinti, è gameplay 3D attivo
    return len(colors) > 500

def main():
    print("==> 1. Avvio Worker melonDS Headless...")
    shm_name = f"pokemon_ds_test_{secrets.token_hex(6)}"
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    control_arr = mp.Array('i', 32)
    control_arr[30] = 0 # running

    proc = mp.Process(
        target=run_engine_worker,
        args=(shm_name, control_arr, ROM_PATH, SAVE_PATH, CORE_LIB),
        daemon=True
    )
    proc.start()
    print(f"✔ Worker avviato (PID {proc.pid})")

    try:
        # Trova ram_fd
        ram_fd = None
        for _ in range(20):
            fd_dir = f"/proc/{proc.pid}/fd"
            if os.path.exists(fd_dir):
                for fd in os.listdir(fd_dir):
                    try:
                        tgt = os.readlink(os.path.join(fd_dir, fd))
                        if "melondsfastmem" in tgt:
                            ram_fd = os.path.join(fd_dir, fd)
                            break
                    except Exception:
                        pass
            if ram_fd: break
            time.sleep(0.2)

        print(f"✔ RAM FD trovato: {ram_fd}")

        # Fase A: Salta filmato intro (premere A e START ripetutamente per 10 secondi)
        print("==> 2. Skip filmato iniziale...")
        for i in range(12):
            press(control_arr, 3, dur=0.2) # START
            time.sleep(0.5)
            press(control_arr, 8, dur=0.2) # A
            time.sleep(0.5)
            img = capture_screen(shm, f"boot_{i}.png")

        # Ora siamo al Title Screen o Menu
        print("==> 3. Selezione CONTINUA e gestione C-Gear...")
        for step in range(8):
            press(control_arr, 4, dur=0.15) # UP
            press(control_arr, 8, dur=0.25) # A
            time.sleep(1.0)
            # Rifiuta C-Gear
            press(control_arr, 5, dur=0.15) # DOWN
            press(control_arr, 8, dur=0.25) # A
            time.sleep(0.8)
            press(control_arr, 8, dur=0.25) # A conferma
            time.sleep(2.0)

            # Controlla se siamo in overworld leggendo le coordinate attive del giocatore
            if ram_fd:
                with open(ram_fd, "rb") as f_ram:
                    f_ram.seek(0x23B384)
                    ram_state = f_ram.read(32)
                z_id = struct.unpack_from("<H", ram_state, 0)[0]
                px = struct.unpack_from("<I", ram_state, 4)[0] >> 16
                py = struct.unpack_from("<I", ram_state, 12)[0] >> 16
                print(f"    Step {step}: Zone={z_id}, X={px}, Y={py}")
                if z_id == 445 and px > 0:
                    print(f"🎉 SUCCESSO! GIOCATORE IN OVERWORLD A X={px}, Y={py}!")
                    break

        time.sleep(1.5)
        final_img = capture_screen(shm, "FINAL_IN_GAME_VERIFICATION.png")
        print(f"📸 Screenshot Finale Overworld Salvato: {final_img}")

    finally:
        control_arr[30] = 1
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()
        print("Worker terminato.")

if __name__ == "__main__":
    main()
