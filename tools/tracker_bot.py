#!/usr/bin/env python3
"""
Bot di Tracciamento in Tempo Reale delle Coordinate del Giocatore (Pokémon Bianco 2).
Legge direttamente la memoria RAM (fastmem) dell'emulatore melonDS in tempo reale:
- Lettura Blocco 28 (0x21EA24): coordinate locali della mappa e direzione dello sguardo autentica.
- Lettura Overworld Matrix (0x21EAA8): coordinate di rendering matriciale e subpixel.
- Rileva dinamicamente riavvii e nuove sessioni dell'emulatore.
- Scrive il foglio Markdown 'tools/foglio_coordinate.md' e lo storico 'tools/coords.log'.
"""

import os
import sys
import time
import struct
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "tools" / "coords.log"
POS_FILE = BASE_DIR / "tools" / "live_position.txt"
SHEET_FILE = BASE_DIR / "tools" / "foglio_coordinate.md"

FACING_NAMES = {
    0: "NORD (⬆ Su - Verso il Capanno)",
    1: "SUD (⬇ Giù - Verso il Prato)",
    2: "OVEST (⬅ Sinistra - Verso i Fiori)",
    3: "EST (➡ Destra - Verso la Casa)",
}

ZONE_NAMES = {
    444: "Fattoria di Venturia (Esterno)",
    445: "Fattoria di Venturia (Area Capanno / Fattoria)",
    315: "Centro Pokémon di Alisopoli",
    316: "Centro Pokémon di Venturia",
    317: "Centro Pokémon di Zinzellopoli",
}

def find_melonds_fastmem():
    """Scansiona i processi attivi per trovare l'FD di fastmem di melonDS più recente."""
    candidates = []
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        pid = int(p)
        fd_dir = f"/proc/{pid}/fd"
        if not os.path.exists(fd_dir):
            continue
        try:
            for fd in os.listdir(fd_dir):
                try:
                    target = os.readlink(os.path.join(fd_dir, fd))
                    if "melondsfastmem" in target:
                        candidates.append((pid, os.path.join(fd_dir, fd), os.path.getmtime(f"/proc/{pid}")))
                except Exception:
                    pass
        except Exception:
            pass
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates[0][0], candidates[0][1]

def update_sheet(zone_id, grid_x, grid_y, front_x, front_y, matrix_x, matrix_y, x_sub, y_sub, facing_raw, status_str, stop_duration=0.0):
    """Aggiorna il foglio di coordinate in formato Markdown chiaro e pronto da consultare."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    dir_str = FACING_NAMES.get(facing_raw, f"Dir {facing_raw}")
    zone_label = ZONE_NAMES.get(zone_id, f"Zona {zone_id}")

    dur_str = f"da {stop_duration:.1f} secondi" if stop_duration > 0 else "in movimento"

    content = f"""# 📍 FOGLIO COORDINATE LIVE — POKÉMON BIANCO 2

> **Ultimo Aggiornamento:** `{ts}`  
> **Stato Giocatore:** `{status_str}` ({dur_str})

---

### 🎯 Posizione Ufficiale nel Salvataggio e Mappa (Grid):
| Parametro | Valore | Note |
|---|---|---|
| **Mappa / Stanza** | **{zone_id}** | `{zone_label}` |
| **Casella X (Grid)** | **{grid_x}** | Coordinata locale del salvataggio / entità |
| **Casella Y (Grid)** | **{grid_y}** | Coordinata locale del salvataggio / entità |
| **Direzione Sguardo** | **{dir_str}** | Dove punta il tuo personaggio |
| **Casella Frontale (+1)** | **X={front_x}, Y={front_y}** | Punto esatto dell'interazione frontale |

---

### 📐 Dati Tecnici Motore Grafico (Matrix RAM):
| Parametro | Valore | Note |
|---|---|---|
| **Matrix X** | `{matrix_x}` | Subpixel: `{x_sub:.2f}` |
| **Matrix Y** | `{matrix_y}` | Subpixel: `{y_sub:.2f}` |

---
*Questo foglio si aggiorna automaticamente a intervalli di 100ms mentre giochi.*
"""
    try:
        with open(SHEET_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

def log_event(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        with open(POS_FILE, "w", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def main():
    print("====================================================")
    print("🛰️ BOT TRACKER COORDINATE LIVE POTENZIATO AVVIATO!")
    print(f"📄 Foglio Live: {SHEET_FILE}")
    print(f"📜 Storico Log: {LOG_FILE}")
    print("====================================================")
    sys.stdout.flush()

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n=== NUOVA SESSIONE TRACKER: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    except Exception:
        pass

    last_record = None
    stop_start_time = time.time()
    last_log_time = 0

    while True:
        pid, ram_path = find_melonds_fastmem()
        if not pid or not ram_path:
            time.sleep(0.5)
            continue

        try:
            with open(ram_path, "rb") as f:
                while True:
                    if not os.path.exists(f"/proc/{pid}"):
                        print(f"Processo {pid} terminato, cerco nuova istanza...")
                        break

                    f.seek(0)
                    ram = f.read(0x400000)
                    if len(ram) < 0x400000:
                        time.sleep(0.2)
                        continue

                    # 1. Lettura Blocco 28 (Salvataggio & Grid Mappa)
                    base_b28 = 0x21EA24
                    zone_id = struct.unpack_from("<H", ram, base_b28 + 4)[0]
                    facing_raw = struct.unpack_from("<H", ram, base_b28 + 6)[0] & 3
                    grid_x = struct.unpack_from("<H", ram, base_b28 + 0x12)[0]
                    grid_y = struct.unpack_from("<H", ram, base_b28 + 0x1a)[0]

                    # 2. Lettura Overworld Matrix RAM
                    base_ram = 0x21EAA8
                    x_raw = struct.unpack_from("<I", ram, base_ram)[0]
                    y_raw = struct.unpack_from("<I", ram, base_ram + 8)[0]
                    matrix_x = x_raw >> 16
                    matrix_y = y_raw >> 16
                    x_sub = (x_raw & 0xFFFF) / 65536.0
                    y_sub = (y_raw & 0xFFFF) / 65536.0

                    if grid_x == 0 and grid_y == 0:
                        time.sleep(0.15)
                        continue

                    # 3. Calcolo casella frontale precisa
                    # 0: Nord (dy = -1), 1: Sud (dy = +1), 2: Ovest (dx = -1), 3: Est (dx = +1)
                    dx = 0 if facing_raw in (0, 1) else (1 if facing_raw == 3 else -1)
                    dy = -1 if facing_raw == 0 else (1 if facing_raw == 1 else 0)
                    front_x = grid_x + dx
                    front_y = grid_y + dy

                    now = time.time()
                    current_record = (zone_id, grid_x, grid_y, facing_raw)

                    if current_record != last_record:
                        stop_start_time = now
                        dir_str = FACING_NAMES.get(facing_raw, f"Dir {facing_raw}")
                        log_event(f"🏃 IN MOVIMENTO -> Grid X={grid_x:2d}, Y={grid_y:2d} | Verso={dir_str} | Frontale=({front_x}, {front_y}) | Mappa={zone_id}")
                        update_sheet(zone_id, grid_x, grid_y, front_x, front_y, matrix_x, matrix_y, x_sub, y_sub, facing_raw, "IN MOVIMENTO", 0.0)
                        last_record = current_record
                        last_log_time = now
                    else:
                        stop_dur = now - stop_start_time
                        if now - last_log_time >= 3.0:
                            dir_str = FACING_NAMES.get(facing_raw, f"Dir {facing_raw}")
                            log_event(f"🛑 FERMO A     -> Grid X={grid_x:2d}, Y={grid_y:2d} | Verso={dir_str} | Frontale=({front_x}, {front_y}) | Mappa={zone_id} (da {stop_dur:.1f}s)")
                            last_log_time = now
                        update_sheet(zone_id, grid_x, grid_y, front_x, front_y, matrix_x, matrix_y, x_sub, y_sub, facing_raw, "FERMO", stop_dur)

                    time.sleep(0.1)
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)

if __name__ == "__main__":
    main()
