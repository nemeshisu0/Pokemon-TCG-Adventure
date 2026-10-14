#!/usr/bin/env python3
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

def crc16_ccitt(data):
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

def patch_save_exact_gate():
    src_sav = BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav"
    data = bytearray(src_sav.read_bytes())

    # Map 444 (Route 20 Gate threshold), X=143, Y=629, facing North
    map_id = 444
    pos_x = 143
    pos_y = 629
    pos_z = 0

    for (base_offset, chk_block_base) in [(0x19500, 0x25F00), (0x3F500, 0x4BF00)]:
        data[base_offset + 0x04 : base_offset + 0x06] = map_id.to_bytes(2, "little")
        data[base_offset + 0x10 : base_offset + 0x14] = (pos_x * 0x10000 + 0x8000).to_bytes(4, "little")
        data[base_offset + 0x18 : base_offset + 0x1C] = (pos_y * 0x10000 + 0x8000).to_bytes(4, "little")

        data[base_offset + 0x80 : base_offset + 0x84] = map_id.to_bytes(4, "little")
        data[base_offset + 0x86 : base_offset + 0x88] = pos_x.to_bytes(2, "little")
        data[base_offset + 0x8A : base_offset + 0x8C] = pos_z.to_bytes(2, "little")
        data[base_offset + 0x8E : base_offset + 0x90] = pos_y.to_bytes(2, "little")
        data[base_offset + 0x92 : base_offset + 0x94] = (0).to_bytes(2, "little") # North

        block = data[base_offset : base_offset + 0x00A8]
        chk = crc16_ccitt(block)
        data[base_offset + 0xAA : base_offset + 0xAC] = chk.to_bytes(2, "little")
        data[chk_block_base + 0x38 : chk_block_base + 0x3A] = chk.to_bytes(2, "little")

        master_block = data[chk_block_base : chk_block_base + 0x0094]
        chk_master = crc16_ccitt(master_block)
        data[chk_block_base + 0xA2 : chk_block_base + 0xA4] = chk_master.to_bytes(2, "little")

    targets = [
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "Bianco 2.sav",
        BASE_DIR / "saves" / "profiles" / "nemesy2" / "nemesy2_bianco2.sav",
        BASE_DIR / "roms" / "modified" / "Bianco 2.sav",
        BASE_DIR / "saves" / "Pokémon Bianco 2.sav",
        BASE_DIR / "saves" / "Bianco 2.sav"
    ]
    for t in targets:
        with open(t, "wb") as f:
            f.write(data)
    print("✔ Salvataggio impostato a Route 20 (Zone 444, X=143, Y=629, verso Nord).")

def press(ctrl, btn, dur=0.2):
    ctrl[btn] = 1
    time.sleep(dur)
    ctrl[btn] = 0
    time.sleep(0.3)

def capture(shm, fname):
    raw = bytes(shm.buf[:1024 * 384])
    img = Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")
    out = SCRATCH / fname
    img.save(out)
    return out

def get_pos(ram_fd):
    if not ram_fd: return 0, 0, 0
    try:
        with open(ram_fd, "rb") as f:
            f.seek(0x23B384)
            st = f.read(32)
        zid = struct.unpack_from("<H", st, 0)[0]
        px = struct.unpack_from("<I", st, 4)[0] >> 16
        py = struct.unpack_from("<I", st, 12)[0] >> 16
        return zid, px, py
    except Exception:
        return 0, 0, 0

def main():
    patch_save_exact_gate()

    shm_name = "ds_r20_boot_test"
    try:
        shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)
    except FileExistsError:
        s = shared_memory.SharedMemory(name=shm_name)
        s.unlink()
        shm = shared_memory.SharedMemory(name=shm_name, create=True, size=1024 * 384)

    control_arr = mp.Array("i", 32)
    proc = mp.Process(target=run_engine_worker, args=(shm_name, control_arr, ROM_PATH, SAVE_PATH, CORE_LIB), daemon=True)
    proc.start()

    try:
        ram_fd = None
        for _ in range(40):
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

        # Skip intro
        for _ in range(14):
            press(control_arr, 3, dur=0.2)
            time.sleep(0.4)
            press(control_arr, 8, dur=0.2)
            time.sleep(0.4)

        # Continua e C-Gear
        for step in range(8):
            press(control_arr, 4, dur=0.15)
            press(control_arr, 8, dur=0.25)
            time.sleep(0.8)
            press(control_arr, 5, dur=0.15)
            press(control_arr, 8, dur=0.25)
            time.sleep(0.8)
            press(control_arr, 8, dur=0.25)
            time.sleep(1.5)

        time.sleep(1.0)
        capture(shm, "r20_boot_screen.png")
        print("📸 Screenshot catturato: r20_boot_screen.png")

        # Passo UP verso la fattoria
        for _ in range(5):
            press(control_arr, 4, dur=0.3)
            time.sleep(0.2)

        time.sleep(1.0)
        capture(shm, "farm_entered_screen.png")
        print("📸 Screenshot catturato: farm_entered_screen.png")

    finally:
        control_arr[30] = 0
        time.sleep(0.5)
        proc.terminate()
        shm.close()
        shm.unlink()

if __name__ == "__main__":
    main()
