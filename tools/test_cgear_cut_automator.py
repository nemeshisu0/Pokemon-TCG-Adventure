#!/usr/bin/env python3
"""
Test del Motore di Auto-Boot e Taglio Schermata C-Gear:
- Esegue la sequenza automatica a 60 FPS direttamente nel loop del worker.
- Salta i loghi e il filmato.
- Seleziona CONTINUA.
- Taglia completamente la schermata del C-Gear (oscurando il display durante il prompt)
  e iniettando la sequenza sicura: DOWN (NO) -> A (Conferma) -> A (Procedi).
- Sblocca il display appena l Overworld è caricato alla Fattoria (Zona 445).
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
ARTIFACT_DIR = Path("/home/nemesy/.gemini/antigravity-ide/brain/b8d8417a-cc11-40ef-9c2c-1009c4d46bd9")

def get_screen(shm):
    raw = bytes(shm.buf[:1024 * 384])
    return Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")

def save_screen(img, name):
    p = ARTIFACT_DIR / name
    img.save(p)
    print(f"📸 Salvato: {name}", flush=True)
    return p

def main():
    print("==> Avvio test auto-boot e taglio C-Gear...")
    shm_name = f"test_cut_{secrets.token_hex(6)}"
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    arr = mp.Array('i', 32)
    proc = mp.Process(target=run_engine_worker, args=(shm_name, arr, ROM_PATH, SAVE_PATH, CORE_LIB), daemon=True)
    proc.start()

    try:
        # Array di controllo:
        # arr[3] = START
        # arr[4] = UP
        # arr[5] = DOWN
        # arr[8] = A
        time.sleep(3.0)
        
        # 1. Salta intro
        print("  [1/4] Salto introduzione (START)...")
        for _ in range(4):
            arr[3] = 1
            time.sleep(0.15)
            arr[3] = 0
            time.sleep(0.4)

        time.sleep(1.5)
        # 2. Seleziona CONTINUA
        print("  [2/4] Selezione CONTINUA (UP -> A)...")
        arr[4] = 1 # UP
        time.sleep(0.15)
        arr[4] = 0
        time.sleep(0.2)
        arr[8] = 1 # A
        time.sleep(0.2)
        arr[8] = 0
        time.sleep(1.0)

        # 3. Taglio e bypass C-Gear
        print("  [3/4] Taglio schermata C-Gear e bypass sicuro (DOWN -> A -> A)...")
        # Attesa comparsa C-Gear prompt
        time.sleep(1.5)
        arr[5] = 1 # DOWN su NO
        time.sleep(0.2)
        arr[5] = 0
        time.sleep(0.3)
        arr[8] = 1 # A su NO
        time.sleep(0.2)
        arr[8] = 0
        time.sleep(1.2)
        arr[8] = 1 # A conferma Procedi
        time.sleep(0.2)
        arr[8] = 0

        # 4. Attesa Overworld
        print("  [4/4] Attesa arrivo in Overworld...")
        for sec in range(15):
            time.sleep(0.5)
            img = get_screen(shm)
            raw = img.tobytes()
            avg_top = sum(raw[:256*192*3]) / (256*192*3)
            if avg_top > 20:
                print(f"  🎉 OVERWORLD RAGGIUNTO! (avg_top={avg_top:.1f})")
                save_screen(img, "overworld_after_cgear_cut.png")
                break

    finally:
        arr[30] = 0
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()
        print("✔ Test terminato.")

if __name__ == "__main__":
    main()
