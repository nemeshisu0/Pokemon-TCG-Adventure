#!/usr/bin/env python3
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
    time.sleep(0.4)

def is_black(img):
    # Check bottom screen (192..384)
    data = img.tobytes()
    return sum(data[256*192*3:]) / (256*192*3) < 5

def main():
    shm_name = f"robust_test_{secrets.token_hex(6)}"
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    arr = mp.Array('i', 32)
    proc = mp.Process(target=run_engine_worker, args=(shm_name, arr, ROM_PATH, SAVE_PATH, CORE_LIB), daemon=True)
    proc.start()

    try:
        # 1. Attendi che compaia "Premi Start"
        print("Attesa Title Screen...")
        time.sleep(3.5)
        save_img(get_img(shm), "rob_0_title.png")

        # 2. Premi START più volte fino a che non siamo nel menu
        print("Premi START...")
        for _ in range(3):
            press_button(arr, 3, dur=0.2)
            time.sleep(0.5)

        time.sleep(2.0)
        save_img(get_img(shm), "rob_1_menu.png")

        # 3. Assicurati di essere su CONTINUA (UP) e premi A
        print("Premi UP e poi A su Continua...")
        press_button(arr, 4, dur=0.15)
        press_button(arr, 8, dur=0.25)

        # Attendi dialogo C-Gear
        time.sleep(3.0)
        save_img(get_img(shm), "rob_2_cgear.png")

        # 4. Rifiuta C-Gear: DOWN -> A -> A
        print("Rifiuto C-Gear...")
        press_button(arr, 5, dur=0.25)
        time.sleep(0.5)
        press_button(arr, 8, dur=0.25)
        time.sleep(1.5)
        press_button(arr, 8, dur=0.25)

        # 5. Attendi Overworld
        print("Attesa Overworld...")
        time.sleep(4.0)
        img_ow = get_img(shm)
        save_img(img_ow, "rob_3_overworld.png")

        # 6. Interazione NPC Box (Preme A)
        print("Interazione con NPC Box (preme A)...")
        press_button(arr, 8, dur=0.3)
        time.sleep(2.5)
        save_img(get_img(shm), "rob_4_box_storage.png")

        # Ancora un secondo per vedere se c'è animazione
        time.sleep(1.5)
        save_img(get_img(shm), "rob_5_box_opened.png")

    finally:
        arr[30] = 0
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()
        print("Fatto!")

if __name__ == "__main__":
    main()
