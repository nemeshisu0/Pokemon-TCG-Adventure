#!/usr/bin/env python3
import os
import sys
import time
import mmap
import struct
from pathlib import Path
from PIL import Image

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

def press(mm, btn, dur=0.25):
    struct.pack_into("<i", mm, btn * 4, 1)
    time.sleep(dur)
    struct.pack_into("<i", mm, btn * 4, 0)
    time.sleep(0.3)

def get_screen(shm_path):
    with open(shm_path, "rb") as f:
        raw = f.read(1024 * 384)
    return Image.frombytes("RGB", (256, 384), raw, "raw", "BGRX")

def main():
    print("Connecting to worker...")
    for _ in range(30):
        pid, ctrl_fd, shm_fd, ram_fd = find_worker()
        if pid: break
        time.sleep(0.5)
    if not pid:
        print("Worker not found!")
        sys.exit(1)
    print(f"Worker PID: {pid}")

    with open(ctrl_fd, "r+b") as f_ctrl:
        mm = mmap.mmap(f_ctrl.fileno(), 4096)

        # Title -> Continua -> Overworld
        for step in range(12):
            press(mm, 3, dur=0.2) # START
            time.sleep(0.8)
            press(mm, 4, dur=0.15) # UP
            press(mm, 8, dur=0.2) # A
            time.sleep(1.5)
            # C-Gear prompt: DOWN then A then A
            press(mm, 5, dur=0.2) # DOWN
            time.sleep(0.3)
            press(mm, 8, dur=0.2) # A
            time.sleep(1.0)
            press(mm, 8, dur=0.2) # A
            time.sleep(2.5)

            # Check RAM zone
            with open(ram_fd, "rb") as f_ram:
                f_ram.seek(0)
                ram_data = f_ram.read(0x400000)
            zone_id = struct.unpack_from("<H", ram_data, 0x21EA24 + 4)[0]
            mx = struct.unpack_from("<I", ram_data, 0x21EAA8)[0] >> 16
            my = struct.unpack_from("<I", ram_data, 0x21EAA8 + 8)[0] >> 16
            print(f"Step {step}: Zone={zone_id}, X={mx}, Y={my}")
            if zone_id == 445:
                print("In Overworld!")
                break

        time.sleep(2.0)
        img = get_screen(shm_fd)
        out_path = "/home/nemesy/.gemini/antigravity-ide/brain/9d6bb43f-c37d-4b5f-a421-44fbdcdce0b1/gate_blocks_screen.png"
        img.save(out_path)
        print(f"Screenshot saved to: {out_path}")

if __name__ == "__main__":
    main()
