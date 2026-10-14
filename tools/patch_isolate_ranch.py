#!/usr/bin/env python3
"""
Isola la Fattoria di Venturia:
1. a/1/2/7 (Table 45): azzera tutti i tassi di incontro selvatico (no erba, no surf, no pesca).
2. a/1/2/6 (File 445 - Fattoria aperta): rimuove tutti gli NPC della storia, tutti i trigger e tutti i warp.
3. a/1/2/6 (File 444 - Casa della fattoria): rimuove tutti i trigger e warp.
"""

import os
import ndspy.rom
import ndspy.narc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_ROM = os.path.join(BASE_DIR, "roms", "original", "Bianco 2.nds")
MODIFIED_ROM = os.path.join(BASE_DIR, "roms", "modified", "Bianco 2.nds")

def main():
    print(f"==> Caricamento ROM da: {ORIGINAL_ROM}...")
    rom = ndspy.rom.NintendoDSRom.fromFile(ORIGINAL_ROM)

    # 1. Modifica incontri selvatici in a/1/2/7 (Table 45 = Fattoria di Venturia)
    enc_id = rom.filenames.idOf("a/1/2/7")
    enc_narc = ndspy.narc.NARC(rom.files[enc_id])
    t45 = bytearray(enc_narc.files[45])
    # Azzeriamo tutti i tassi di incontro (primi 8 byte)
    for i in range(8):
        t45[i] = 0
    enc_narc.files[45] = bytes(t45)
    rom.files[enc_id] = enc_narc.save()
    print("    [OK] Incontri selvatici azzerati al 100% (Table 45)")

    # 2. Modifica overworld entities in a/1/2/6 (File 444 e 445 = Fattoria di Venturia)
    ow_id = rom.filenames.idOf("a/1/2/6")
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])

    # Un overworld file vuoto valido in Gen 5 ha lunghezza 12 byte:
    # 04 00 00 00 (lunghezza 4) + 00 00 00 00 (0 F, 0 N, 0 W, 0 T) + 00 00 00 00 (footer)
    empty_ow = bytes.fromhex("040000000000000000000000")
    
    # File 445 (Fattoria all'aperto)
    ow_narc.files[445] = empty_ow
    # File 444 (Interno casa fattoria)
    ow_narc.files[444] = empty_ow

    rom.files[ow_id] = ow_narc.save()
    print("    [OK] File 445 e 444 ripuliti: 0 NPC, 0 Trigger di trama, 0 Warp d'uscita (Mappa Isolata)")

    print(f"==> Scrittura ROM modificata in: {MODIFIED_ROM}...")
    rom.saveToFile(MODIFIED_ROM)
    print("==> ROM MODIFICATA CON SUCCESSO!")

if __name__ == "__main__":
    main()
