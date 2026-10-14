#!/usr/bin/env python3
"""
Disassembler helper for Pokémon Bianco 2 (NDS).
Supports ARM9 (base 0x02004000), ARM7 (base 0x02380000), and all 344 Overlays.
"""

import sys
import json
import argparse
from pathlib import Path
import capstone

RE_DIR = Path(__file__).resolve().parent
ARM9_PATH = RE_DIR / "arm9_decompressed.bin"
ARM7_PATH = RE_DIR / "arm7.bin"
OVERLAYS_DIR = RE_DIR / "overlays9"
OVERLAYS_JSON = RE_DIR / "arm9_overlays.json"

ARM9_BASE = 0x02004000
ARM7_BASE = 0x02380000

def load_overlay_table():
    if OVERLAYS_JSON.exists():
        try:
            with open(OVERLAYS_JSON, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def disasm_block(title: str, binary_path: Path, base_addr: int, target_addr: int, count: int = 25, thumb: bool = False):
    if not binary_path.exists():
        print(f"Errore: File binario non trovato: {binary_path}")
        return False

    with open(binary_path, "rb") as f:
        data = f.read()

    offset = target_addr - base_addr
    if offset < 0 or offset >= len(data):
        print(f"Indirizzo 0x{target_addr:08X} fuori range per {title} (Range: 0x{base_addr:08X} - 0x{base_addr + len(data):08X})")
        return False

    read_bytes = count * (2 if thumb else 4)
    code = data[offset : offset + read_bytes]

    mode = capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM
    md = capstone.Cs(capstone.CS_ARCH_ARM, mode)
    print(f"=== Disassembly: {title} (Modo: {'THUMB' if thumb else 'ARM'}) ===")
    disasms = list(md.disasm(code, target_addr))
    if not disasms:
        print("  (Nessuna istruzione valida decodificata a questo indirizzo)")
    for i in disasms:
        bytes_hex = " ".join(f"{b:02x}" for b in i.bytes)
        print(f"0x{i.address:08X}  [{bytes_hex:<11}]  {i.mnemonic:<8} {i.op_str}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Disassemblatore per Pokémon Bianco 2 (ARM9, ARM7, Overlays)")
    parser.add_argument("address", nargs="?", default=None, help="Indirizzo RAM esadecimale (es. 0x02004800)")
    parser.add_argument("-o", "--overlay", type=int, default=None, help="ID dell'Overlay (0..343)")
    parser.add_argument("-7", "--arm7", action="store_true", help="Forza disassemblaggio da ARM7")
    parser.add_argument("-n", "--count", type=int, default=25, help="Numero di istruzioni da disassemblare")
    parser.add_argument("-t", "--thumb", action="store_true", help="Disassembla in modalità Thumb (16-bit)")
    args = parser.parse_args()

    overlays = load_overlay_table()

    # Modalità esplicita: --overlay ID
    if args.overlay is not None:
        ov_id = args.overlay
        if ov_id < 0 or ov_id >= len(overlays):
            print(f"Errore: Overlay ID {ov_id} non valido (disponibili: 0..{len(overlays)-1})")
            return
        meta = overlays[ov_id]
        ov_base = int(meta["ram_address"], 16)
        ov_file = OVERLAYS_DIR / f"overlay9_{ov_id:04d}.bin"
        target_addr = int(args.address, 16) if args.address else ov_base
        disasm_block(f"Overlay {ov_id} ({ov_file.name})", ov_file, ov_base, target_addr, args.count, args.thumb)
        return

    # Modalità esplicita: --arm7
    if args.arm7:
        target_addr = int(args.address, 16) if args.address else ARM7_BASE
        disasm_block("ARM7 Sub-CPU", ARM7_PATH, ARM7_BASE, target_addr, args.count, args.thumb)
        return

    if not args.address:
        parser.print_help()
        return

    target_addr = int(args.address, 16)

    # 1. Verifica se ricade in ARM7
    if ARM7_BASE <= target_addr < (ARM7_BASE + 0x40000):
        disasm_block("ARM7 Sub-CPU", ARM7_PATH, ARM7_BASE, target_addr, args.count, args.thumb)
        return

    # 2. Verifica se ricade in ARM9 Main Code
    if ARM9_PATH.exists() and ARM9_BASE <= target_addr < (ARM9_BASE + ARM9_PATH.stat().st_size):
        disasm_block("ARM9 Main Code", ARM9_PATH, ARM9_BASE, target_addr, args.count, args.thumb)
        return

    # 3. Autodetect Overlays per indirizzo
    for meta in overlays:
        ov_base = int(meta["ram_address"], 16)
        ov_size = int(meta["ram_size"], 16)
        if ov_base <= target_addr < (ov_base + ov_size):
            ov_id = meta["id"]
            ov_file = OVERLAYS_DIR / f"overlay9_{ov_id:04d}.bin"
            disasm_block(f"Overlay {ov_id} (Rilevato da RAM 0x{ov_base:08X})", ov_file, ov_base, target_addr, args.count, args.thumb)
            return

    # Se non trovato in nessuno
    print(f"Indirizzo 0x{target_addr:08X} non corrisponde a nessun modulo ARM9, ARM7 o Overlay noto.")

if __name__ == "__main__":
    main()
