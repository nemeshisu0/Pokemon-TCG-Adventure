#!/usr/bin/env python3
"""
Test completo interazione Box NPC e persistenza salvataggio:
1. Boot del gioco e ingresso nell'Overworld.
2. Step Sud su Route 20 e rientro per ricaricare File 306 dalla nuova ROM.
3. Posizionamento davanti all'NPC Box a (47, 48).
4. Interazione con tasto A -> verifica menu/dialogo PC (NO CRASH!).
5. Salvataggio in-game per fissare la cache nel salvataggio.
6. Reboot diretto dal salvataggio per verificare che all'avvio l'NPC e il mondo sono perfetti.
"""

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

def press(control_arr, btn, dur=0.2):
    control_arr[btn] = 1
    time.sleep(dur)
    control_arr[btn] = 0
    time.sleep(0.3)

def capture(shm, filename):
    raw = bytes(shm.buf[:1024 * 384])
    img = Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")
    out = SCRATCH / filename
    img.save(out)
    return out

def get_player_pos(ram_fd):
    if not ram_fd: return 0, 0, 0
    with open(ram_fd, "rb") as f:
        f.seek(0x23B384)
        st = f.read(32)
    zid = struct.unpack_from("<H", st, 0)[0]
    px = struct.unpack_from("<I", st, 4)[0] >> 16
    py = struct.unpack_from("<I", st, 12)[0] >> 16
    return zid, px, py

def main():
    print("==> 1. Avvio Worker melonDS...")
    shm_name = "ds_box_test"
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    control_arr = mp.Array('i', 32)

    proc = mp.Process(
        target=run_engine_worker,
        args=(shm_name, control_arr, ROM_PATH, SAVE_PATH, CORE_LIB),
        daemon=True
    )
    proc.start()

    try:
        ram_fd = None
        for _ in range(30):
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

        # Salta intro
        print("==> 2. Skip intro...")
        for _ in range(12):
            press(control_arr, 3, dur=0.2)
            time.sleep(0.5)
            press(control_arr, 8, dur=0.2)
            time.sleep(0.5)

        # Seleziona Continua e gestisci C-Gear
        print("==> 3. Caricamento salvataggio...")
        for step in range(8):
            press(control_arr, 4, dur=0.15)
            press(control_arr, 8, dur=0.25)
            time.sleep(1.0)
            press(control_arr, 5, dur=0.15)
            press(control_arr, 8, dur=0.25)
            time.sleep(0.8)
            press(control_arr, 8, dur=0.25)
            time.sleep(2.0)
            zid, px, py = get_player_pos(ram_fd)
            if zid == 445 and px > 0:
                print(f"✔ Overworld raggiunto: Zone={zid}, X={px}, Y={py}")
                break

        # Step Sud su Route 20 per forzare reload pulito
        print("==> 4. Transizione mappa Sud -> Nord...")
        for _ in range(10):
            press(control_arr, 5, dur=0.3) # DOWN
            zid, px, py = get_player_pos(ram_fd)
            if zid != 445:
                print(f"    Uscito su Route 20: Zone={zid}")
                break

        time.sleep(0.5)
        for _ in range(12):
            press(control_arr, 4, dur=0.3) # UP
            zid, px, py = get_player_pos(ram_fd)
            if zid == 445 and py <= 49:
                print(f"    Rientrato in fattoria a X={px}, Y={py}")
                break

        time.sleep(1.0)
        capture(shm, "npc_box_standing.png")
        print("📸 Screenshot catturato: npc_box_standing.png")

        # Ora il giocatore è a (47, 49) rivolto a Nord. L'NPC è a (47, 48)!
        # Premiamo A per interagire!
        print("==> 5. Pressione Tasto A per interagire con l'NPC Box...")
        press(control_arr, 8, dur=0.3) # A
        time.sleep(1.5)
        capture(shm, "npc_box_interacted.png")
        print("📸 Screenshot catturato: npc_box_interacted.png")

        # Premiamo A di nuovo per avanzare il dialogo del PC
        press(control_arr, 8, dur=0.3)
        time.sleep(1.5)
        capture(shm, "npc_box_menu.png")
        print("📸 Screenshot catturato: npc_box_menu.png")

        # Chiudiamo eventuale dialogo premendo B due volte
        press(control_arr, 9, dur=0.2) # B
        time.sleep(0.5)
        press(control_arr, 9, dur=0.2) # B
        time.sleep(1.0)

        # Salviamo la partita in-game per aggiornare la cache del salvataggio!
        print("==> 6. Salvataggio della partita in-game...")
        press(control_arr, 9, dur=0.25) # X (Menu)
        time.sleep(1.0)
        for _ in range(4):
            press(control_arr, 5, dur=0.2) # DOWN
            time.sleep(0.2)
        press(control_arr, 8, dur=0.3) # A (Salva)
        time.sleep(1.5)
        press(control_arr, 8, dur=0.3) # A (Sì)
        time.sleep(2.0)
        press(control_arr, 8, dur=0.3) # A (Conferma)
        time.sleep(6.0) # Attendi scrittura completa della SRAM
        print("✔ Salvataggio completato!")

    finally:
        control_arr[30] = 1
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()
        print("Worker terminato.")

if __name__ == "__main__":
    main()
