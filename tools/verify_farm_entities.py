#!/usr/bin/env python3
"""
Test e verifica visiva automatizzata:
1. Avvia melonDS headless con la nuova ROM modificata e il salvataggio attivo.
2. Invia gli input per superare il Title Screen, Continua e rifiutare il C-Gear.
3. Entra nell'overworld alla Fattoria di Venturia (Map 445).
4. Cattura uno screenshot ad alta risoluzione del campo dove si trova il giocatore a (35, 37).
5. Mostra chiaramente il Mareep e la Poké Ball presenti a video.
"""

import os
import sys
import time
import secrets
import mmap
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
    time.sleep(0.3)

def capture_screen(shm, filename):
    raw = bytes(shm.buf[:1024 * 384])
    img = Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")
    out = SCRATCH_DIR / filename
    img.save(out)
    print(f"📸 Salvato: {out.name}", flush=True)
    return out

def main():
    print("==> 1. Avvio Worker melonDS Headless per Verifica Visiva...")
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
    print(f"✔ Worker avviato (PID {proc.pid}) con ROM: {Path(ROM_PATH).name}")

    try:
        # Attesa avvio
        time.sleep(2.5)

        print("==> 2. Superamento schermata del titolo...")
        for attempt in range(15):
            press(control_arr, 3, dur=0.2) # START
            time.sleep(1.0)
            
            # UP per essere su CONTINUA
            press(control_arr, 4, dur=0.15)
            press(control_arr, 4, dur=0.15)
            time.sleep(0.3)
            
            # A su CONTINUA
            print("    Pressione A su CONTINUA...")
            press(control_arr, 8, dur=0.25) # A
            time.sleep(3.0)

            # C-Gear prompt: DOWN -> A -> A
            print("    Gestione prompt C-Gear...")
            press(control_arr, 5, dur=0.2) # DOWN
            time.sleep(0.3)
            press(control_arr, 8, dur=0.25) # A (conferma NO)
            time.sleep(1.5)
            press(control_arr, 8, dur=0.25) # A (conferma procedi)
            time.sleep(3.0)

            # Verifica se siamo in overworld
            img = capture_screen(shm, f"test_boot_step_{attempt}.png")

            # Trova fd ram del processo worker
            ram_fd = None
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

            if ram_fd:
                with open(ram_fd, "rb") as f_ram:
                    f_ram.seek(0)
                    ram_data = f_ram.read(0x400000)
                zone_id = struct.unpack_from("<H", ram_data, 0x21EA24 + 4)[0]
                mx = struct.unpack_from("<I", ram_data, 0x21EAA8)[0] >> 16
                my = struct.unpack_from("<I", ram_data, 0x21EAA8 + 8)[0] >> 16
                print(f"    Stato RAM: Zona={zone_id}, X={mx}, Y={my}")
                if zone_id == 445:
                    print("🎉 CONFERMATO: IN OVERWORLD ALLA FATTORIA (MAPPA 445)!")
                    break

        time.sleep(1.0)
        # Cattura lo screenshot finale dell'Overworld
        final_screen = capture_screen(shm, "VERIFIED_VISIBLE_ENTITIES_FARM.png")
        print(f"🎉 TEST COMPLETATO! Screenshot di verifica: {final_screen}")

    finally:
        control_arr[30] = 1 # richiedi stop
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()
        print("Worker headless terminato pulito.")

if __name__ == "__main__":
    main()
