#!/usr/bin/env python3
"""
Test e verifica visiva interazione NPC Box PC con tempistiche esatte.
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
ARTIFACT_DIR = Path("/home/nemesy/.gemini/antigravity-ide/brain/923d14a9-5bb5-447d-9861-60ab47ad32cd")

def press(control_arr, btn, dur=0.25):
    control_arr[btn] = 1
    time.sleep(dur)
    control_arr[btn] = 0
    time.sleep(0.3)

def capture_screen(shm, filename):
    raw = bytes(shm.buf[:1024 * 384])
    img = Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")
    out = ARTIFACT_DIR / filename
    img.save(out)
    print(f"📸 Screenshot salvato: {out.name}", flush=True)
    return out

def main():
    print("==> 1. Avvio melonDS Headless per Test NPC Box...")
    shm_name = f"pokemon_pc_test_{secrets.token_hex(6)}"
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    control_arr = mp.Array('i', 32)
    control_arr[30] = 0

    proc = mp.Process(
        target=run_engine_worker,
        args=(shm_name, control_arr, ROM_PATH, SAVE_PATH, CORE_LIB),
        daemon=True
    )
    proc.start()
    print(f"✔ Worker avviato (PID {proc.pid})")

    try:
        # 1. Attesa Schermata Titolo
        time.sleep(3.0)
        capture_screen(shm, "step0_title.png")

        # 2. START per saltare intro
        print("==> Pressione START...")
        press(control_arr, 3, dur=0.25)
        time.sleep(1.5)
        capture_screen(shm, "step1_press_start.png")

        # 3. A per entrare nel menu
        print("==> Pressione A per Menu...")
        press(control_arr, 8, dur=0.25)
        time.sleep(2.0)
        capture_screen(shm, "step2_menu.png")

        # 4. A su CONTINUA
        print("==> Pressione A su CONTINUA...")
        press(control_arr, 8, dur=0.25)
        time.sleep(3.0)
        capture_screen(shm, "step3_cgear_prompt.png")

        # 5. NO al C-Gear: GIÙ -> A
        print("==> Rifiuto C-Gear (DOWN -> A)...")
        press(control_arr, 5, dur=0.25)
        time.sleep(0.4)
        press(control_arr, 8, dur=0.25)
        time.sleep(1.5)
        capture_screen(shm, "step4_cgear_confirm.png")

        # 6. Conferma procedi: A
        print("==> Conferma avvio senza C-Gear (A)...")
        press(control_arr, 8, dur=0.25)
        time.sleep(4.5)

        # 7. Cattura Overworld
        capture_screen(shm, "step5_overworld.png")

        # 8. Interazione con l'NPC: Preme A
        print("==> 7. INTERAZIONE CON L'NPC (Premendo A)...")
        press(control_arr, 8, dur=0.35)
        time.sleep(2.5)

        # 9. Cattura Schermata Box PC
        capture_screen(shm, "step6_box_storage.png")

        print("🎉 TEST COMPLETATO CON SUCCESSO!")

    finally:
        control_arr[30] = 1
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()
        print("Worker terminato.")

if __name__ == "__main__":
    main()
