#!/usr/bin/env python3
"""
Script di configurazione automatica della Lobby:
1. Modifica la ROM (roms/modified/Bianco 2.nds) per azzerare gli incontri selvatici
   e pulire gli NPC della storia nella Fattoria di Venturia (Zone 42).
2. Modifica il file di salvataggio (saves/Pokémon Bianco 2.sav) per spawnare il giocatore
   al centro della Fattoria di Venturia (X=15, Y=25, M=42) con checksum perfetti.
3. Configura i collegamenti per melonDS (run-game.sh).
"""

import os
import shutil
import ndspy.rom
import ndspy.narc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_ROM = os.path.join(BASE_DIR, "roms", "original", "Bianco 2.nds")
MODIFIED_DIR = os.path.join(BASE_DIR, "roms", "modified")
MODIFIED_ROM = os.path.join(MODIFIED_DIR, "Bianco 2.nds")
SAVE_FILE = os.path.join(BASE_DIR, "saves", "Pokémon Bianco 2.sav")
MODIFIED_SAV_LINK = os.path.join(MODIFIED_DIR, "Bianco 2.sav")

def crc16_ccitt(data):
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

def patch_save_file():
    print("==> [1/3] Configurazione punto di spawn nel salvataggio...")
    with open(SAVE_FILE, "rb") as f:
        data = bytearray(f.read())

    # Backup del salvataggio
    backup_path = SAVE_FILE + ".bak"
    if not os.path.exists(backup_path):
        shutil.copy2(SAVE_FILE, backup_path)
        print(f"    Creato backup di sicurezza in: {backup_path}")

    # Coordinate per Fattoria di Venturia (Zone 42 = 0x2A)
    # Centro della fattoria: X=15, Y=25
    map_id = 42
    pos_x = 15
    pos_y = 25
    pos_z = 0

    # 1. Coordinate continuous (0x19500)
    # Map ID at 0x19504
    data[0x19504:0x19506] = map_id.to_bytes(2, "little")
    # X continuous (fixed point) at 0x19510
    data[0x19510:0x19514] = (pos_x * 0x10000 + 0x8000).to_bytes(4, "little")
    # Y continuous at 0x19518
    data[0x19518:0x1951C] = (pos_y * 0x10000 + 0x8000).to_bytes(4, "little")

    # 2. Coordinate grid (0x19580)
    # Map ID at 0x19580
    data[0x19580:0x19584] = map_id.to_bytes(4, "little")
    # X at 0x19586
    data[0x19586:0x19588] = pos_x.to_bytes(2, "little")
    # Z at 0x1958A
    data[0x1958A:0x1958C] = pos_z.to_bytes(2, "little")
    # Y at 0x1958E
    data[0x1958E:0x19590] = pos_y.to_bytes(2, "little")

    # 3. Ricalcolo Checksum Block 28 (0x19500, len 0x00A8)
    block_data = data[0x19500 : 0x19500 + 0x00A8]
    chk28 = crc16_ccitt(block_data)
    data[0x195AA:0x195AC] = chk28.to_bytes(2, "little")
    data[0x25F38:0x25F3A] = chk28.to_bytes(2, "little")

    # 4. Ricalcolo Master Checksum Block (0x25F00, len 0x0094)
    master_block = data[0x25F00 : 0x25F00 + 0x0094]
    chk_master = crc16_ccitt(master_block)
    data[0x25FA2:0x25FA4] = chk_master.to_bytes(2, "little")

    # Salva il file modificato
    with open(SAVE_FILE, "wb") as f:
        f.write(data)
    print(f"    Spawn impostato su Mappa {map_id} (Fattoria di Venturia), X={pos_x}, Y={pos_y}")
    print(f"    Checksum aggiornati: Block 28 = {hex(chk28)}, Master = {hex(chk_master)}")

def patch_rom():
    print("==> [2/3] Modifica della ROM (pulizia incontri selvatici e isolamento mappa)...")
    os.makedirs(MODIFIED_DIR, exist_ok=True)
    
    print(f"    Caricamento ROM da: {ORIGINAL_ROM}...")
    rom = ndspy.rom.NintendoDSRom.fromFile(ORIGINAL_ROM)

    # 1. Modifica incontri selvatici in a/1/2/7 (Table 45 = Floccesy Ranch)
    enc_id = rom.filenames.idOf("a/1/2/7")
    enc_narc = ndspy.narc.NARC(rom.files[enc_id])
    t45 = bytearray(enc_narc.files[45])
    # Azzeriamo tutti i tassi di incontro (camminata, surf, pesca, erba scuotente)
    for i in range(8):
        t45[i] = 0
    enc_narc.files[45] = bytes(t45)
    rom.files[enc_id] = enc_narc.save()
    print("    Incontri selvatici nell'erba azzerati (Table 45 rate = 0)")

    # 2. Modifica overworld entities in a/1/2/6 (File 85 = Floccesy Ranch)
    ow_id = rom.filenames.idOf("a/1/2/6")
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])
    f85 = bytearray(ow_narc.files[85])

    # Creiamo un file overworld pulito:
    # 0 NPC di trama, 0 warps per isolare l'area
    # Manteniamo la struttura minima valida di Gen 5:
    clean_ow = bytearray(32)
    clean_ow[0:4] = (20).to_bytes(4, "little") # data length
    clean_ow[4] = 0 # Furniture count
    clean_ow[5] = 0 # NPC count
    clean_ow[6] = 0 # Warp count
    clean_ow[7] = 0 # Trigger count
    # padding / footer
    clean_ow[8:20] = b'\x00' * 12
    ow_narc.files[85] = bytes(clean_ow[:20])
    rom.files[ow_id] = ow_narc.save()
    print("    Overworld ripulito da tutti gli NPC della storia e warps disabilitati")

    print(f"    Salvataggio ROM modificata in: {MODIFIED_ROM}...")
    rom.saveToFile(MODIFIED_ROM)
    print("    ROM modificata salvata con successo!")

def setup_symlinks():
    print("==> [3/3] Configurazione collegamenti salvataggio per melonDS...")
    if os.path.islink(MODIFIED_SAV_LINK) or os.path.exists(MODIFIED_SAV_LINK):
        os.remove(MODIFIED_SAV_LINK)
    os.symlink("../../saves/Pokémon Bianco 2.sav", MODIFIED_SAV_LINK)
    print(f"    Collegamento creato: {MODIFIED_SAV_LINK} -> saves/Pokémon Bianco 2.sav")

if __name__ == "__main__":
    patch_save_file()
    patch_rom()
    setup_symlinks()
    print("\n🎉 SETUP COMPLETATO AL 100%!")
    print("Puoi avviare il gioco con: ./run-game.sh")
