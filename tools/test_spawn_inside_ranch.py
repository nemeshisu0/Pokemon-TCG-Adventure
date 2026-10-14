#!/usr/bin/env python3
"""
Test e verifica visiva dello spawn DENTRO il Ranch (Floccesy Farm, Map 445):
- Imposta coordinate x=35, y=35 (dentro la fattoria davanti al recinto/casa).
- Avvia worker headless melonDS.
- Naviga automaticamente rilevando i fotogrammi a video:
  * Supera Title Screen
  * Seleziona CONTINUA
  * Rifiuta C-Gear
  * Entra nell Overworld
- Scatta lo screenshot definitivo dell Overworld.
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

BLOCKS = [
    (0x00000, 0x03e0, 0x003E2, 0x25F00),
    (0x00400, 0x0ff0, 0x013F2, 0x25F02),
    (0x01400, 0x0ff0, 0x023F2, 0x25F04),
    (0x02400, 0x0ff0, 0x033F2, 0x25F06),
    (0x03400, 0x0ff0, 0x043F2, 0x25F08),
    (0x04400, 0x0ff0, 0x053F2, 0x25F0A),
    (0x05400, 0x0ff0, 0x063F2, 0x25F0C),
    (0x06400, 0x0ff0, 0x073F2, 0x25F0E),
    (0x07400, 0x0ff0, 0x083F2, 0x25F10),
    (0x08400, 0x0ff0, 0x093F2, 0x25F12),
    (0x09400, 0x0ff0, 0x0A3F2, 0x25F14),
    (0x0A400, 0x0ff0, 0x0B3F2, 0x25F16),
    (0x0B400, 0x0ff0, 0x0C3F2, 0x25F18),
    (0x0C400, 0x0ff0, 0x0D3F2, 0x25F1A),
    (0x0D400, 0x0ff0, 0x0E3F2, 0x25F1C),
    (0x0E400, 0x0ff0, 0x0F3F2, 0x25F1E),
    (0x0F400, 0x0ff0, 0x103F2, 0x25F20),
    (0x10400, 0x0ff0, 0x113F2, 0x25F22),
    (0x11400, 0x0ff0, 0x123F2, 0x25F24),
    (0x12400, 0x0ff0, 0x133F2, 0x25F26),
    (0x13400, 0x0ff0, 0x143F2, 0x25F28),
    (0x14400, 0x0ff0, 0x153F2, 0x25F2A),
    (0x15400, 0x0ff0, 0x163F2, 0x25F2C),
    (0x16400, 0x0ff0, 0x173F2, 0x25F2E),
    (0x17400, 0x0ff0, 0x183F2, 0x25F30),
    (0x18400, 0x09ec, 0x18DEE, 0x25F32),
    (0x18E00, 0x0534, 0x19336, 0x25F34),
    (0x19400, 0x00b0, 0x194B2, 0x25F36),
    (0x19500, 0x00a8, 0x195AA, 0x25F38),
    (0x19600, 0x1338, 0x1A93A, 0x25F3A),
    (0x1AA00, 0x07c4, 0x1B1C6, 0x25F3C),
    (0x1B200, 0x0d54, 0x1BF56, 0x25F3E),
    (0x1C000, 0x0094, 0x1C096, 0x25F40),
    (0x1C100, 0x0658, 0x1C75A, 0x25F42),
    (0x1C800, 0x0a94, 0x1D296, 0x25F44),
    (0x1D300, 0x01ac, 0x1D4AE, 0x25F46),
    (0x1D500, 0x03ec, 0x1D8EE, 0x25F48),
    (0x1D900, 0x005c, 0x1D95E, 0x25F4A),
    (0x1DA00, 0x01e0, 0x1DBE2, 0x25F4C),
    (0x1DC00, 0x00a8, 0x1DCAA, 0x25F4E),
    (0x1DD00, 0x0460, 0x1E162, 0x25F50),
    (0x1E200, 0x1400, 0x1F602, 0x25F52),
    (0x1F700, 0x02a4, 0x1F9A6, 0x25F54),
    (0x1FA00, 0x00e0, 0x1FAE2, 0x25F56),
    (0x1FB00, 0x034c, 0x1FE4E, 0x25F58),
    (0x1FF00, 0x04e0, 0x203E2, 0x25F5A),
    (0x20400, 0x00f8, 0x204FA, 0x25F5C),
    (0x20500, 0x02fc, 0x207FE, 0x25F5E),
    (0x20800, 0x0094, 0x20896, 0x25F60),
    (0x20900, 0x035c, 0x20C5E, 0x25F62),
    (0x20D00, 0x01d4, 0x20ED6, 0x25F64),
    (0x20F00, 0x01e0, 0x210E2, 0x25F66),
    (0x21100, 0x00f0, 0x211F2, 0x25F68),
    (0x21200, 0x01b4, 0x213B6, 0x25F6A),
    (0x21400, 0x04dc, 0x218DE, 0x25F6C),
    (0x21900, 0x0034, 0x21936, 0x25F6E),
    (0x21A00, 0x003c, 0x21A3E, 0x25F70),
    (0x21B00, 0x01ac, 0x21CAE, 0x25F72),
    (0x21D00, 0x0b90, 0x22892, 0x25F74),
    (0x22900, 0x00ac, 0x229AE, 0x25F76),
    (0x22A00, 0x0850, 0x23252, 0x25F78),
    (0x23300, 0x0284, 0x23586, 0x25F7A),
    (0x23600, 0x0010, 0x23612, 0x25F7C),
    (0x23700, 0x00a8, 0x237AA, 0x25F7E),
    (0x23800, 0x016c, 0x2396E, 0x25F80),
    (0x23A00, 0x0080, 0x23A82, 0x25F82),
    (0x23B00, 0x00fc, 0x23BFE, 0x25F84),
    (0x23C00, 0x16a8, 0x252AA, 0x25F86),
    (0x25300, 0x0498, 0x2579A, 0x25F88),
    (0x25800, 0x0060, 0x25862, 0x25F8A),
    (0x25900, 0x00fc, 0x259FE, 0x25F8C),
    (0x25A00, 0x03e4, 0x25DE6, 0x25F8E),
    (0x25E00, 0x00f0, 0x25EF2, 0x25F90),
    (0x25F00, 0x0094, 0x25FA2, 0x25FA2),
]

def crc16_ccitt(data):
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

def patch_save_inside_farm(pos_x=35, pos_y=35, facing=1):
    src_sav = BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav"
    data = bytearray(src_sav.read_bytes())
    map_id = 445 # Fattoria di Venturia (Floccesy Farm)
    pos_z = 0

    for slot in [0x00000, 0x26000]:
        data[slot + 0x1E200 : slot + 0x1E200 + 0x1400] = b'\x00' * 0x1400

        b28 = slot + 0x19500
        data[b28 + 0x04 : b28 + 0x06] = map_id.to_bytes(2, "little")
        data[b28 + 0x06 : b28 + 0x08] = facing.to_bytes(2, "little")
        data[b28 + 0x10 : b28 + 0x14] = (pos_x * 0x10000 + 0x8000).to_bytes(4, "little")
        data[b28 + 0x18 : b28 + 0x1C] = (pos_y * 0x10000 + 0x8000).to_bytes(4, "little")

        data[b28 + 0x80 : b28 + 0x84] = map_id.to_bytes(4, "little")
        data[b28 + 0x86 : b28 + 0x88] = pos_x.to_bytes(2, "little")
        data[b28 + 0x8A : b28 + 0x8C] = pos_z.to_bytes(2, "little")
        data[b28 + 0x8E : b28 + 0x90] = pos_y.to_bytes(2, "little")
        data[b28 + 0x92 : b28 + 0x94] = facing.to_bytes(2, "little")

        for off, length, chk_off, chk_mir in BLOCKS:
            actual_off = slot + off
            actual_chk_off = slot + chk_off
            actual_chk_mir = slot + chk_mir
            chk = crc16_ccitt(data[actual_off : actual_off + length])
            data[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, 'little')
            data[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, 'little')

    dest_paths = [
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav",
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav",
        BASE_DIR / "saves" / "Pokémon Bianco 2.sav",
        BASE_DIR / "saves" / "Bianco 2.sav",
        BASE_DIR / "roms" / "modified" / "Bianco 2.sav",
    ]
    for p in dest_paths:
        p.write_bytes(data)
    print(f"✔ Salvataggi aggiornati a Map {map_id}, X={pos_x}, Y={pos_y}, Verso={facing}!")

def press_btn(arr, btn, dur=0.25):
    arr[btn] = 1
    time.sleep(dur)
    arr[btn] = 0
    time.sleep(0.3)

def get_screen(shm):
    raw = bytes(shm.buf[:1024 * 384])
    return Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")

def save_screen(img, name):
    p = ARTIFACT_DIR / name
    img.save(p)
    print(f"📸 Salvato: {name}", flush=True)
    return p

def is_main_menu(img):
    try:
        pixels = [img.getpixel((100, y)) for y in [220, 240, 260]]
        return all(50 <= p[0] <= 90 and 50 <= p[1] <= 90 and 50 <= p[2] <= 90 for p in pixels)
    except Exception:
        return False

def is_cgear_prompt(img):
    try:
        p_border = img.getpixel((30, 202))
        p_bg = img.getpixel((30, 220))
        is_yellow = (p_border[0] > 180 and p_border[1] > 160 and p_border[2] < 100)
        is_dark = (p_bg[0] < 40 and p_bg[1] < 40 and p_bg[2] < 40)
        return is_yellow and is_dark
    except Exception:
        return False

def main():
    patch_save_inside_farm(pos_x=35, pos_y=35, facing=1)

    print("\n==> Avvio worker melonDS...")
    shm_name = f"test_ranch_{secrets.token_hex(6)}"
    shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    arr = mp.Array('i', 32)
    proc = mp.Process(target=run_engine_worker, args=(shm_name, arr, ROM_PATH, SAVE_PATH, CORE_LIB), daemon=True)
    proc.start()

    try:
        print("==> Salto schermate iniziali verso il menu Continua...")
        menu_reached = False
        start_t = time.time()
        while time.time() - start_t < 25:
            img = get_screen(shm)
            if is_main_menu(img):
                print("  🎯 MENU CONTINUA RILEVATO!")
                menu_reached = True
                break
            press_btn(arr, 3, dur=0.15) # START
            time.sleep(0.4)

        if not menu_reached:
            print("⚠ Fallback: UP + A...")
        time.sleep(0.5)

        # Assicurati di essere su CONTINUA
        press_btn(arr, 4, dur=0.15) # UP
        time.sleep(0.2)
        print("==> Pressione A su CONTINUA...")
        press_btn(arr, 8, dur=0.25) # A
        time.sleep(1.0)

        # Rileva e gestisci C-Gear
        print("==> Gestione dialogo C-Gear...")
        cgear_done = False
        start_cg = time.time()
        while time.time() - start_cg < 12:
            img = get_screen(shm)
            if is_cgear_prompt(img):
                print("  🎯 DIALOGO C-GEAR RILEVATO! DOWN -> A (NO) -> A (Procedi)...")
                press_btn(arr, 5, dur=0.2) # DOWN su NO
                time.sleep(0.3)
                press_btn(arr, 8, dur=0.25) # A conferma NO
                time.sleep(1.0)
                press_btn(arr, 8, dur=0.25) # A conferma Procedi
                cgear_done = True
                break
            time.sleep(0.3)

        if not cgear_done:
            print("⚠ Fallback C-Gear: DOWN -> A -> A...")
            press_btn(arr, 5, dur=0.2)
            time.sleep(0.3)
            press_btn(arr, 8, dur=0.25)
            time.sleep(1.0)
            press_btn(arr, 8, dur=0.25)

        # Attesa fine dissolvenza Overworld (attendi che lo schermo non sia nero)
        print("==> Attesa fine dissolvenza Overworld...")
        time.sleep(2.0)
        for _ in range(30):
            img = get_screen(shm)
            raw = img.tobytes()
            avg_top = sum(raw[:256*192*3]) / (256*192*3)
            avg_bot = sum(raw[256*192*3:]) / (256*192*3)
            if avg_top > 15:
                print(f"  🎉 OVERWORLD RENDERIZZATO (avg_top={avg_top:.1f})!")
                break
            time.sleep(0.5)

        time.sleep(1.0)
        img_ow = get_screen(shm)
        save_screen(img_ow, "ranch_inside_spawn_verified.png")

        # Trova RAM del worker per controllare coordinate
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
            print(f"📍 Posizione RAM live: Zona={zone_id}, X={mx}, Y={my}")

    finally:
        arr[30] = 0
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()
        print("✔ Test completato e worker spento.")

if __name__ == "__main__":
    main()
