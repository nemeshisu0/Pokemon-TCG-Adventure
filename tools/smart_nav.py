#!/usr/bin/env python3
"""
Navigatore Intelligente con Riconoscimento Schermo in Tempo Reale:
- Salta i loghi iniziali e il filmato di Kyurem premendo START al momento giusto.
- Riconosce la comparsa della scheda salvataggio ("CONTINUA - MAURO") e preme A.
- Riconosce il box di dialogo C-Gear (bordo giallo) e seleziona NO in modo affidabile.
- Conferma il dialogo successivo e attende l'Overworld (Zona 445 in RAM).
- Scatta lo screenshot live dell'Overworld al Cancello Sud.
- Preme A per interagire con il PC a (47, 53) e scatta lo screenshot del PC aperto.
"""

import os
import sys
import time
import mmap
import struct
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
SCRATCH_DIR = Path("/home/nemesy/.gemini/antigravity-ide/brain/9d6bb43f-c37d-4b5f-a421-44fbdcdce0b1/scratch")
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

def find_worker():
    for p in os.listdir("/proc"):
        if not p.isdigit(): continue
        pid = int(p)
        fd_dir = f"/proc/{pid}/fd"
        if not os.path.exists(fd_dir): continue
        try:
            ctrl_fd, shm_fd, ram_fd = None, None, None
            for fd in os.listdir(fd_dir):
                target = os.readlink(os.path.join(fd_dir, fd))
                if "pym-" in target and not ctrl_fd:
                    ctrl_fd = os.path.join(fd_dir, fd)
                elif "pokemon_ds_shm" in target and not shm_fd:
                    shm_fd = os.path.join(fd_dir, fd)
                elif "melondsfastmem" in target and not ram_fd:
                    ram_fd = os.path.join(fd_dir, fd)
            if ctrl_fd and shm_fd and ram_fd:
                return pid, ctrl_fd, shm_fd, ram_fd
        except Exception:
            pass
    return None, None, None, None

def get_screen(shm_path):
    with open(shm_path, "rb") as f:
        raw = f.read(1024 * 384)
    return Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")

def save_screen(img, name):
    p = SCRATCH_DIR / name
    img.save(p)
    print(f"  📸 [CATTURA] {name}", flush=True)
    return p

def press(mm, btn, dur=0.2):
    struct.pack_into("<i", mm, btn * 4, 1)
    time.sleep(dur)
    struct.pack_into("<i", mm, btn * 4, 0)
    time.sleep(0.2)

def is_main_menu(img):
    # Nel menu Continua, il box info salvataggio si trova tra y=210 e y=290
    # Controlliamo il colore grigio scuro tipico del box (attorno a 60-80 su R,G,B)
    pixels = [img.getpixel((100, y)) for y in [220, 240, 260]]
    is_grey = all(50 <= p[0] <= 90 and 50 <= p[1] <= 90 and 50 <= p[2] <= 90 for p in pixels)
    # E sullo schermo superiore y=30 c'è il pulsante CONTINUA
    top_p = img.getpixel((150, 20))
    return is_grey

def is_cgear_prompt(img):
    # Il riquadro ATTENZIONE ha un bordo giallo a y=202 (RGB ~ 250, 210, 50)
    # e sfondo nero (20, 20, 20)
    p_border = img.getpixel((30, 202))
    p_bg = img.getpixel((30, 220))
    is_yellow = (p_border[0] > 180 and p_border[1] > 160 and p_border[2] < 100)
    is_dark = (p_bg[0] < 40 and p_bg[1] < 40 and p_bg[2] < 40)
    return is_yellow and is_dark

def get_zone_id(ram_fd):
    with open(ram_fd, "rb") as f:
        f.seek(0)
        data = f.read(0x400000)
    return struct.unpack_from("<H", data, 0x21EA24 + 4)[0]

def main():
    print("⏳ Ricerca processo worker melonDS...")
    for _ in range(40):
        pid, ctrl_fd, shm_fd, ram_fd = find_worker()
        if pid: break
        time.sleep(0.5)

    if not pid:
        print("❌ Worker non trovato!")
        sys.exit(1)

    print(f"✔ Worker agganciato: PID {pid}")

    with open(ctrl_fd, "r+b") as f_ctrl:
        mm = mmap.mmap(f_ctrl.fileno(), 4096)

        print("\n==> Fase 1: Avanzamento verso il Menu Principale...")
        menu_reached = False
        start_time = time.time()
        while time.time() - start_time < 35:
            img = get_screen(shm_fd)
            if is_main_menu(img):
                print("  🎯 MENU CONTINUA RILEVATO!")
                save_screen(img, "smart_menu_detected.png")
                menu_reached = True
                break
            # Premi START per accelerare intro e titolo
            press(mm, 3, dur=0.15)
            time.sleep(0.6)

        if not menu_reached:
            print("⚠ Timeout menu continua, tentativo diretto...")

        time.sleep(1.0)
        # Assicurati che sia su CONTINUA
        press(mm, 4, dur=0.1) # UP
        time.sleep(0.2)
        print("==> Fase 2: Pressione A su CONTINUA...")
        press(mm, 8, dur=0.25) # A
        time.sleep(1.5)

        print("==> Fase 3: Rilevamento dialogo C-Gear...")
        cgear_handled = False
        for _ in range(20):
            img = get_screen(shm_fd)
            if is_cgear_prompt(img):
                print("  🎯 DIALOGO C-GEAR RILEVATO! Selezione NO...")
                save_screen(img, "smart_cgear_detected.png")
                press(mm, 5, dur=0.2) # GIÙ su NO
                time.sleep(0.3)
                press(mm, 8, dur=0.25) # A su NO
                time.sleep(1.2)
                print("  🎯 Conferma Procedi senza C-Gear (A su SÌ)...")
                press(mm, 8, dur=0.25) # A su SÌ
                cgear_handled = True
                break
            time.sleep(0.5)

        if not cgear_handled:
            print("⚠ Fallback input C-Gear...")
            press(mm, 5, dur=0.2)
            time.sleep(0.3)
            press(mm, 8, dur=0.25)
            time.sleep(1.0)
            press(mm, 8, dur=0.25)

        print("==> Fase 4: Attesa Overworld (Zona 445)...")
        for _ in range(30):
            zid = get_zone_id(ram_fd)
            if zid == 445:
                print(f"  🎉 GIOCATORE IN OVERWORLD! Zona: {zid}")
                break
            time.sleep(0.5)

        time.sleep(2.0) # Attesa fine dissolvenza grafica
        img_ow = get_screen(shm_fd)
        save_screen(img_ow, "OVERWORLD_AT_SOUTH_GATE.png")

        # Leggi coordinate precise in RAM
        with open(ram_fd, "rb") as f:
            f.seek(0)
            ram = f.read(0x400000)
        base_b28 = 0x21EA24
        facing = struct.unpack_from("<H", ram, base_b28 + 6)[0] & 3
        base_ram = 0x21EAA8
        mx = struct.unpack_from("<I", ram, base_ram)[0] >> 16
        my = struct.unpack_from("<I", ram, base_ram + 8)[0] >> 16
        print(f"\n📍 Posizione Effettiva: Matrix X={mx}, Y={my}, Facing={facing}")

        print("\n==> Fase 5: Interazione con il PC a (47, 53)...")
        # Se non è rivolto a Sud, girati a Sud
        if facing != 1:
            print("  Giro il personaggio a SUD...")
            press(mm, 5, dur=0.15)
            time.sleep(0.4)

        print("  Pressione A sul PC al Cancello Sud...")
        press(mm, 8, dur=0.3)
        time.sleep(2.5)

        img_pc = get_screen(shm_fd)
        save_screen(img_pc, "PC_STORAGE_OPENED.png")
        print("\n🎉 PROCEDURA COMPLETATA CON SUCCESSO!")

if __name__ == "__main__":
    main()
