#!/usr/bin/env python3
"""
Test definitivo: avvia e naviga dall'inizio all'Overworld e interagisce con l'NPC Box.
"""

import os
import sys
import time
import secrets
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

def get_img(shm):
    raw = bytes(shm.buf[:1024 * 384])
    return Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")

def save_img(img, name):
    p = ARTIFACT_DIR / name
    img.save(p)
    print(f"📸 {name}", flush=True)

def press_button(arr, btn, dur=0.25):
    arr[btn] = 1
    time.sleep(dur)
    arr[btn] = 0
    time.sleep(0.3)

def is_in_menu(img):
    # Nel menu Continua, il pixel del box Mauro (x=50, y=250) è scuro (grigio scuro/nero ~ 0x48)
    px = img.getpixel((50, 250))
    # E in alto a (150, 68) c'è la scritta o box CONTINUA
    return px[0] > 40 and px[0] < 100 and px[1] > 40 and px[1] < 100

def main():
    shm_name = f"full_test_{secrets.token_hex(6)}"
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    arr = mp.Array('i', 32)
    proc = mp.Process(target=run_engine_worker, args=(shm_name, arr, ROM_PATH, SAVE_PATH, CORE_LIB), daemon=True)
    proc.start()

    try:
        print("1. Attraversamento Intro / Title Screen...")
        start_time = time.time()
        in_menu = False
        while time.time() - start_time < 25:
            press_button(arr, 3, dur=0.15) # START
            press_button(arr, 8, dur=0.15) # A
            img = get_img(shm)
            if is_in_menu(img):
                in_menu = True
                print("✔ Nel Menu CONTINUA!")
                break
            time.sleep(0.5)

        time.sleep(1.0)
        save_img(get_img(shm), "full_1_menu.png")

        # 2. Premi A su CONTINUA
        print("2. Pressione A su CONTINUA...")
        press_button(arr, 4, dur=0.15) # UP per sicurezza
        press_button(arr, 8, dur=0.25) # A su CONTINUA
        time.sleep(3.0)

        save_img(get_img(shm), "full_2_cgear.png")

        # 3. Rifiuto C-Gear
        print("3. Rifiuto C-Gear...")
        press_button(arr, 5, dur=0.25) # GIÙ
        time.sleep(0.4)
        press_button(arr, 8, dur=0.25) # A
        time.sleep(1.5)
        press_button(arr, 8, dur=0.25) # A conferma procedi
        time.sleep(4.5)

        # 4. In Overworld!
        print("4. Caricamento Overworld...")
        img_ow = get_img(shm)
        save_img(img_ow, "full_3_overworld_npc.png")

        # 5. Parla con l'NPC: Preme A
        print("5. Interazione con l'NPC (Pressione tasto A)...")
        press_button(arr, 8, dur=0.35)
        time.sleep(2.5)

        img_box = get_img(shm)
        save_img(img_box, "full_4_box_open.png")

        time.sleep(1.5)
        save_img(get_img(shm), "full_5_box_final.png")

        print("🎉 TEST COMPLETATO!")

    finally:
        arr[30] = 0
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()

if __name__ == "__main__":
    main()
