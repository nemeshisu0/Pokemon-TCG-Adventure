#!/usr/bin/env python3
"""
Script di movimento in tempo reale per dimostrare e tracciare le coordinate esatte.
Muove il personaggio live nell'overworld mentre la finestra di gioco è aperta
davanti all'utente nello split screen di Hyprland.
"""

import os
import sys
import time
import mmap
import struct
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "tools" / "coords.log"
SHEET_FILE = BASE_DIR / "tools" / "foglio_coordinate.md"

# Button mappings in libretro / melonDS shared memory
BTN_B = 0
BTN_Y = 1
BTN_SELECT = 2
BTN_START = 3
BTN_UP = 4
BTN_DOWN = 5
BTN_LEFT = 6
BTN_RIGHT = 7
BTN_A = 8
BTN_X = 9

DIR_NAMES = {
    0: "NORD (⬆ Su)",
    1: "SUD (⬇ Giù)",
    2: "OVEST (⬅ Sinistra)",
    3: "EST (➡ Destra)",
}

def get_live_state(ram_f):
    ram_f.seek(0x23b384)
    data = ram_f.read(32)
    map_id = struct.unpack_from("<H", data, 0)[0]
    raw_x = struct.unpack_from("<I", data, 4)[0]
    raw_y = struct.unpack_from("<I", data, 12)[0]
    facing = struct.unpack_from("<H", data, 20)[0] & 3
    
    x = raw_x >> 16
    y = raw_y >> 16
    sub_x = (raw_x & 0xFFFF) / 65536.0
    sub_y = (raw_y & 0xFFFF) / 65536.0
    
    return map_id, x, y, sub_x, sub_y, facing

def log_pos(msg, map_id, x, y, facing):
    ts = time.strftime("%H:%M:%S")
    dir_str = DIR_NAMES.get(facing, f"Dir {facing}")
    line = f"[{ts}] {msg:<18} -> X={x:2d}, Y={y:2d} | Verso={dir_str} | Mappa={map_id}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        
    sheet_content = f"""# 📍 FOGLIO COORDINATE IN DIRETTA (LIVE OVERWORLD)

> **Ultimo Movimento:** `{ts}`  
> **Azione:** `{msg}`

---

### 🎯 Posizione Attuale del Giocatore:
| Parametro | Valore | Descrizione |
|---|---|---|
| **Mappa Attiva** | **{map_id}** | Fattoria di Venturia (Area Capanno) |
| **Coordinata X** | **{x}** | Posizione orizzontale sulla mappa |
| **Coordinata Y** | **{y}** | Posizione verticale sulla mappa |
| **Direzione** | **{dir_str}** | Direzione verso cui guarda il personaggio |

---
*Aggiornato in tempo reale durante il movimento controllato dall'assistente.*
"""
    with open(SHEET_FILE, "w", encoding="utf-8") as f:
        f.write(sheet_content)

def main():
    print("=" * 60)
    print("🎮 AVVIO CONTROLLO MOVIMENTO LIVE IN TEMPO REALE")
    print("=" * 60)
    
    ctrl_path = "/proc/92163/fd/5"
    ram_path = "/proc/92163/fd/9"
    
    with open(ctrl_path, "r+b") as f_ctrl, open(ram_path, "rb") as f_ram:
        mm = mmap.mmap(f_ctrl.fileno(), 4096)
        
        def press(btn_id, dur=0.35):
            struct.pack_into("<i", mm, btn_id * 4, 1)
            time.sleep(dur)
            struct.pack_into("<i", mm, btn_id * 4, 0)
            time.sleep(0.2)
            
        m, x, y, sx, sy, fc = get_live_state(f_ram)
        log_pos("PUNTO DI PARTENZA", m, x, y, fc)
        time.sleep(1.0)
        
        # Movimenti dimostrativi
        steps = [
            ("PASSO SU (NORD)", BTN_UP),
            ("PASSO SU (NORD)", BTN_UP),
            ("PASSO A SINISTRA (OVEST)", BTN_LEFT),
            ("PASSO A SINISTRA (OVEST)", BTN_LEFT),
            ("PASSO GIÙ (SUD)", BTN_DOWN),
            ("PASSO GIÙ (SUD)", BTN_DOWN),
            ("PASSO A DESTRA (EST)", BTN_RIGHT),
            ("PASSO A DESTRA (EST)", BTN_RIGHT),
        ]
        
        for name, btn in steps:
            press(btn, dur=0.35)
            m, x, y, sx, sy, fc = get_live_state(f_ram)
            log_pos(name, m, x, y, fc)
            time.sleep(0.6)
            
        print("=" * 60)
        print("✅ MOVIMENTO COMPLETATO CON SUCCESSO!")
        print("=" * 60)

if __name__ == "__main__":
    main()
