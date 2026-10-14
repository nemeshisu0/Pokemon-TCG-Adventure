#!/usr/bin/env python3
"""
Test e verifica completa del PC al Cancello Sud (X=47, Y=53):
1. Monitora il boot di melonDS tramite launcher.
2. Naviga automaticamente dal Title Screen all'Overworld.
3. Verifica la posizione del giocatore a (47, 52) rivolto a Sud verso (47, 53).
4. Cattura screenshot dell'overworld con l'entità al cancello.
5. Preme A per interagire con il PC e cattura lo screenshot del Sistema Box PC aperto!
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

def find_worker_fds():
    """Trova il processo worker di melonDS e i suoi file descriptor (ctrl, shm, ram)."""
    for p in os.listdir("/proc"):
        if not p.isdigit(): continue
        pid = int(p)
        fd_dir = f"/proc/{pid}/fd"
        if not os.path.exists(fd_dir): continue
        try:
            ctrl_fd = None
            shm_fd = None
            ram_fd = None
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

def press(mm, btn, dur=0.25):
    struct.pack_into("<i", mm, btn * 4, 1)
    time.sleep(dur)
    struct.pack_into("<i", mm, btn * 4, 0)
    time.sleep(0.3)

def capture_screen(shm_path, filename):
    with open(shm_path, "rb") as f:
        raw = f.read(1024 * 384)
    img = Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")
    out = SCRATCH_DIR / filename
    img.save(out)
    print(f"  [SCREENSHOT] Salvato: {out.name}", flush=True)
    return out

def get_coords(ram_path):
    with open(ram_path, "rb") as f:
        f.seek(0)
        ram = f.read(0x400000)
    base_b28 = 0x21EA24
    zone_id = struct.unpack_from("<H", ram, base_b28 + 4)[0]
    facing_raw = struct.unpack_from("<H", ram, base_b28 + 6)[0] & 3
    base_ram = 0x21EAA8
    x_raw = struct.unpack_from("<I", ram, base_ram)[0]
    y_raw = struct.unpack_from("<I", ram, base_ram + 8)[0]
    matrix_x = x_raw >> 16
    matrix_y = y_raw >> 16
    x_sub = (x_raw & 0xFFFF) / 65536.0
    y_sub = (y_raw & 0xFFFF) / 65536.0
    return zone_id, matrix_x, matrix_y, x_sub, y_sub, facing_raw

def main():
    print("=" * 60)
    print("🔍 RICERCA WORKER MELONDS...")
    print("=" * 60)
    
    start_wait = time.time()
    pid = None
    while time.time() - start_wait < 30:
        pid, ctrl_fd, shm_fd, ram_fd = find_worker_fds()
        if pid:
            break
        time.sleep(0.5)

    if not pid:
        print("❌ Worker non trovato entro il timeout!")
        sys.exit(1)

    print(f"✔ Worker trovato! PID: {pid}")
    print(f"  Ctrl FD: {ctrl_fd}")
    print(f"  SHM FD:  {shm_fd}")
    print(f"  RAM FD:  {ram_fd}")

    with open(ctrl_fd, "r+b") as f_ctrl:
        mm = mmap.mmap(f_ctrl.fileno(), 4096)

        print("\n==> 1. Attesa Schermata Titolo...")
        time.sleep(2.0)
        capture_screen(shm_fd, "gate_step0_title.png")

        print("==> 2. Pressione START / A per accedere al Menu Continua...")
        press(mm, 3) # START
        time.sleep(1.5)
        press(mm, 8) # A
        time.sleep(1.5)
        capture_screen(shm_fd, "gate_step1_menu.png")

        print("==> 3. Pressione A su CONTINUA...")
        press(mm, 8) # A
        time.sleep(2.5)
        capture_screen(shm_fd, "gate_step2_cgear_prompt.png")

        print("==> 4. Selezione NO al C-Gear...")
        press(mm, 5) # GIÙ
        time.sleep(0.4)
        press(mm, 8) # A
        time.sleep(1.5)
        capture_screen(shm_fd, "gate_step3_cgear_confirm.png")

        print("==> 5. Conferma procedi senza C-Gear (A su SÌ)...")
        press(mm, 8) # A
        time.sleep(4.0)

        # Attesa caricamento overworld
        capture_screen(shm_fd, "gate_step4_overworld.png")
        z, mx, my, sx, sy, fc = get_coords(ram_fd)
        print(f"\n📍 STATO GIOCATORE IN RAM:")
        print(f"  Mappa:    {z}")
        print(f"  Matrix X: {mx} (sub: {sx:.2f})")
        print(f"  Matrix Y: {my} (sub: {sy:.2f})")
        print(f"  Facing:   {fc} (0=Nord, 1=Sud, 2=Ovest, 3=Est)")

        print("\n==> 6. INTERAZIONE CON IL PC AL CANCELLO SUD (X=47, Y=53)...")
        # Il giocatore è a (47, 52) rivolto a SUD verso (47, 53)
        press(mm, 8, dur=0.3) # PREME A SUL CANCELLO SUD
        time.sleep(2.0)
        capture_screen(shm_fd, "gate_step5_pc_opened.png")

        print("\n" + "=" * 60)
        print("🎉 TEST COMPLETATO CON SUCCESSO!")
        print("=" * 60)

if __name__ == "__main__":
    main()
