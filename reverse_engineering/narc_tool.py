#!/usr/bin/env python3
"""
NARC archive extractor & inspector for Pokémon Bianco 2.
Allows viewing contents or dumping files from any NARC inside the ROM NitroFS.
"""

import os
import sys
import argparse
from pathlib import Path
import ndspy.rom
import ndspy.narc

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_ROM = BASE_DIR.parent / "roms" / "original" / "Bianco 2.nds"

def inspect_narc(rom_path: Path, narc_path: str, extract_to: str = None):
    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))
    file_bytes = rom.getFileByName(narc_path)
    if not file_bytes:
        print(f"File not found in ROM: {narc_path}")
        return

    narc = ndspy.narc.NARC(file_bytes)
    print(f"=== NARC: {narc_path} ===")
    print(f"Total internal files: {len(narc.files)}")
    
    total_size = sum(len(f) for f in narc.files)
    print(f"Uncompressed payload size: {total_size} bytes ({total_size / 1024:.2f} KB)")

    for i in range(min(15, len(narc.files))):
        f = narc.files[i]
        magic = f[:4].decode('ascii', errors='replace') if len(f) >= 4 else ''
        print(f"  [{i:04d}] Size: {len(f):6d} bytes | Header: {magic}")
    if len(narc.files) > 15:
        print(f"  ... (+ {len(narc.files) - 15} more files)")

    if extract_to:
        out_dir = Path(extract_to)
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(narc.files):
            out_file = out_dir / f"file_{i:04d}.bin"
            with open(out_file, "wb") as out_f:
                out_f.write(f)
        print(f"Extracted all {len(narc.files)} files to {out_dir}")

def main():
    parser = argparse.ArgumentParser(description="Inspect or extract NARC from Pokémon Bianco 2")
    parser.add_argument("narc_path", help="Path inside NitroFS (e.g. 'a/0/0/2' or 'a/0/1/6')")
    parser.add_argument("-x", "--extract", metavar="DIR", help="Extract internal files to directory")
    parser.add_argument("--rom", default=str(DEFAULT_ROM), help="Path to NDS ROM")
    args = parser.parse_args()

    inspect_narc(Path(args.rom), args.narc_path, args.extract)

if __name__ == "__main__":
    main()
