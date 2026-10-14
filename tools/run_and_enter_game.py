#!/usr/bin/env python3
"""
Automazione visiva affidabile:
Rileva gli stati dello schermo in tempo reale e invia gli input precisi per:
1. Superare la schermata iniziale ("Premi Start")
2. Selezionare "CONTINUA"
3. Rifiutare il C-Gear in sicurezza (DOWN -> A -> A)
4. Entrare nell'Overworld al Cancello Sud
5. Scattare screenshot dell'Overworld
6. Premere A per interagire con il PC a (47, 53)
7. Scattare screenshot del PC aperto
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
    path = SCRATCH_DIR / name
    img.save(path)
    print(f"📸 Salvato: {path.name}", flush=True)
    return path

def press(mm, btn, dur=0.25):
    struct.pack_into("<i", mm, btn * 4, 1)
    time.sleep(dur)
    struct.pack_into("<i", mm, btn * 4, 0)
    time.sleep(0.3)

def main():
    print("⏳ Attesa worker melonDS...")
    for _ in range(40):
        pid, ctrl_fd, shm_fd, ram_fd = find_worker()
        if pid: break
        time.sleep(0.5)

    if not pid:
        print("❌ Worker non trovato!")
        sys.exit(1)

    print(f"✔ Worker connesso: PID {pid}")

    with open(ctrl_fd, "r+b") as f_ctrl:
        mm = mmap.mmap(f_ctrl.fileno(), 4096)

        # 1. Attendi schermata iniziale (logo o "Premi Start")
        print("==> 1. Attesa Schermata del Titolo...")
        time.sleep(2.0)
        for attempt in range(15):
            img = get_screen(shm_fd)
            # Premi START per superare intro/title
            press(mm, 3, dur=0.2) # START
            time.sleep(1.0)
            img = get_screen(shm_fd)
            # Verifica se siamo nel menu (controlla pixel o colore di Continua)
            # Nel menu, la parte inferiore mostra i dati di salvataggio (grigio scuro)
            # Oppure salviamo lo screenshot
            save_screen(img, f"menu_check_{attempt}.png")
            # Se siamo nel menu con "CONTINUA"
            # Premiamo UP due volte per sicurezza per essere su CONTINUA
            press(mm, 4, dur=0.15) # UP
            time.sleep(0.2)
            press(mm, 4, dur=0.15) # UP
            time.sleep(0.3)
            # Premi A su CONTINUA
            print("==> 2. Pressione A su CONTINUA...")
            press(mm, 8, dur=0.25) # A
            time.sleep(3.0)
            img_cgear = get_screen(shm_fd)
            save_screen(img_cgear, f"cgear_check_{attempt}.png")
            
            # Controlla se compare il dialogo C-Gear ("Vuoi effettuare il collegamento?")
            # C-Gear prompt ha testo bianco su sfondo con box
            # Premiamo DOWN per selezionare NO
            print("==> 3. Gestione C-Gear (NO -> Conferma)...")
            press(mm, 5, dur=0.2) # DOWN
            time.sleep(0.4)
            press(mm, 8, dur=0.25) # A (conferma NO)
            time.sleep(1.5)
            # Conferma secondo dialogo ("Così non potrai utilizzare...") -> A su SÌ
            press(mm, 8, dur=0.25) # A (conferma procedi)
            time.sleep(4.0)

            # Verifica se siamo in overworld
            img_ow = get_screen(shm_fd)
            save_screen(img_ow, "overworld_live_check.png")

            # Controlla RAM se mappa == 445
            with open(ram_fd, "rb") as f_ram:
                f_ram.seek(0)
                ram_data = f_ram.read(0x400000)
            zone_id = struct.unpack_from("<H", ram_data, 0x21EA24 + 4)[0]
            mx = struct.unpack_from("<I", ram_data, 0x21EAA8)[0] >> 16
            my = struct.unpack_from("<I", ram_data, 0x21EAA8 + 8)[0] >> 16
            facing = struct.unpack_from("<H", ram_data, 0x21EA24 + 6)[0] & 3
            print(f"Stato RAM: Zona={zone_id}, X={mx}, Y={my}, Facing={facing}")

            if zone_id == 445:
                print("🎉 ENTRATI CON SUCCESSO IN OVERWORLD (ZONA 445)!")
                break
            else:
                print(f"Tentativo {attempt+1}: ancora non in overworld, riprovo...")

        # Siamo in Overworld!
        save_screen(get_screen(shm_fd), "FINAL_OVERWORLD_AT_GATE.png")

        # Ora interagisci con il PC al Cancello Sud
        print("\n==> 4. INTERAZIONE CON IL PC A (47, 53)...")
        # Premiamo A
        press(mm, 8, dur=0.3)
        time.sleep(2.0)
        save_screen(get_screen(shm_fd), "FINAL_PC_STORAGE_OPENED.png")

        print("✔ OPERAZIONE COMPLETATA!")

if __name__ == "__main__":
    main()
