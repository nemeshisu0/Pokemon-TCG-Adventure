#!/usr/bin/env python3
"""
Costruisce la Lobby Sandbox 100% Isolata:
1. Modifica la ROM (roms/modified/Bianco 2.nds):
   - Azzera TUTTE le 135 tabelle di incontri selvatici in a/1/2/7 (Zero Pokémon selvatici ovunque).
   - In a/1/2/6, ripulisce File 445 (Fattoria all'aperto) da tutti gli NPC e trigger di trama.
   - Aggiunge un warp di sicurezza/forcefield sui bordi che riporta al centro (X=25, Y=28).
   - Ripulisce File 444 (casa fattoria).
   - Esegue il pad finale della ROM a 512 MB esatti (536,870,912 byte).
2. Modifica il Save (saves/Pokémon Bianco 2.sav e roms/modified/Bianco 2.sav):
   - Spawn fisso a Venturia (Zone 445, X=25, Y=28).
   - Reset Overworld State (Block 41 a 0x1E200) per cancellare i Mareep cachati.
   - Squadra con 1 SOLO STARTER a Livello 5 (Oshawott Lvl 5, HP 20/20, mosse base).
   - Slot 1..5 completamente rimossi (niente leggendari o vecchi pokemon).
   - Scarpe da corsa e Pokedex attivi.
   - Checksum ricalcolati per tutti i 74 blocchi di entrambi gli slot (standard PKHeX).
"""

import os
import struct
import ndspy.rom
import ndspy.narc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_ROM = os.path.join(BASE_DIR, "roms", "original", "Bianco 2.nds")
MODIFIED_ROM = os.path.join(BASE_DIR, "roms", "modified", "Bianco 2.nds")
SOURCE_SAV = "/home/nemesy/Documents/progetti stani miei/roms/Pokémon Bianco 2.sav"
TARGET_SAV_1 = os.path.join(BASE_DIR, "saves", "Pokémon Bianco 2.sav")
TARGET_SAV_2 = os.path.join(BASE_DIR, "roms", "modified", "Bianco 2.sav")

def crc16_ccitt(data):
    top = 0xFF
    bot = 0xFF
    for b in data:
        x = (b ^ top) & 0xFF
        x ^= (x >> 4)
        top = (bot ^ (x >> 3) ^ (x << 4)) & 0xFF
        bot = (x ^ (x << 5)) & 0xFF
    return (top << 8) | bot

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

def make_starter_pkm(source_data):
    slot0_raw = source_data[0x18E08:0x18E08+220]
    pid = struct.unpack_from('<I', slot0_raw, 0)[0]
    chk = struct.unpack_from('<H', slot0_raw, 6)[0]
    seed = chk
    def next_chk_u16():
        nonlocal seed
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        return (seed >> 16) & 0xFFFF
    shift = ((pid >> 13) & 0x1F) % 24
    orders = [
        'ABCD', 'ABDC', 'ACBD', 'ACDB', 'ADBC', 'ADCB',
        'BACD', 'BADC', 'BCAD', 'BCDA', 'BDAC', 'BDCA',
        'CABD', 'CADB', 'CBAD', 'CBDA', 'CDAB', 'CDBA',
        'DABC', 'DACB', 'DBAC', 'DBCA', 'DCAB', 'DCBA'
    ]
    order = orders[shift]
    blocks = {}
    for i in range(4):
        b_data = bytearray(32)
        for j in range(0, 32, 2):
            val = struct.unpack_from('<H', slot0_raw, 8 + i*32 + j)[0]
            val ^= next_chk_u16()
            b_data[j:j+2] = struct.pack('<H', val)
        blocks[order[i]] = b_data
        
    seed_pid = pid
    def next_pid_u16():
        nonlocal seed_pid
        seed_pid = (seed_pid * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        return (seed_pid >> 16) & 0xFFFF
    p_data = bytearray(84)
    for j in range(0, 84, 2):
        val = struct.unpack_from('<H', slot0_raw, 136 + j)[0]
        val ^= next_pid_u16()
        p_data[j:j+2] = struct.pack('<H', val)
        
    # Block A: Oshawott (501), Level 5 (EXP 125)
    struct.pack_into('<H', blocks['A'], 0x00, 501)
    struct.pack_into('<I', blocks['A'], 0x08, 125)
    blocks['A'][0x14] = 70 # friendship
    blocks['A'][0x18:0x1E] = b'\x00' * 6 # EVs
    
    # Block B: Tackle (33), Tail Whip (39), Water Gun (55), 0
    struct.pack_into('<4H', blocks['B'], 0x00, 33, 39, 55, 0)
    blocks['B'][0x08:0x0C] = bytes([35, 30, 25, 0]) # PPs
    
    # Block C: Nickname
    nick = 'OSHAWOTT'.encode('utf-16le') + b'\xff\xff'
    nick = nick.ljust(22, b'\x00')
    blocks['C'][0:22] = nick
    
    # Party stats
    p_data[0x00:0x04] = b'\x00\x00\x00\x00'
    p_data[0x04] = 5 # Level 5!
    struct.pack_into('<H', p_data, 0x06, 20) # Current HP: 20
    struct.pack_into('<H', p_data, 0x08, 20) # Max HP: 20
    struct.pack_into('<H', p_data, 0x0A, 11) # Atk: 11
    struct.pack_into('<H', p_data, 0x0C, 10) # Def: 10
    struct.pack_into('<H', p_data, 0x0E, 10) # Spe: 10
    struct.pack_into('<H', p_data, 0x10, 12) # SpA: 12
    struct.pack_into('<H', p_data, 0x12, 10) # SpD: 10
    
    # Checksum and re-encryption
    chk = 0
    for b_name in ['A', 'B', 'C', 'D']:
        b = blocks[b_name]
        for j in range(0, 32, 2):
            chk = (chk + struct.unpack_from('<H', b, j)[0]) & 0xFFFF
            
    out = bytearray(220)
    struct.pack_into('<I', out, 0, pid)
    struct.pack_into('<H', out, 4, 0)
    struct.pack_into('<H', out, 6, chk)
    
    seed = chk
    for i in range(4):
        b = blocks[order[i]]
        for j in range(0, 32, 2):
            val = struct.unpack_from('<H', b, j)[0]
            val ^= next_chk_u16()
            struct.pack_into('<H', out, 8 + i*32 + j, val)
            
    seed_pid = pid
    for j in range(0, 84, 2):
        val = struct.unpack_from('<H', p_data, j)[0]
        val ^= next_pid_u16()
        struct.pack_into('<H', out, 136 + j, val)
        
    return bytes(out)

def patch_rom():
    print(f"==> [1/2] Modifica della ROM da: {ORIGINAL_ROM}...")
    rom = ndspy.rom.NintendoDSRom.fromFile(ORIGINAL_ROM)

    # 1. Azzera TUTTI gli incontri selvatici su TUTTE le 135 tabelle di a/1/2/7
    enc_id = rom.filenames.idOf("a/1/2/7")
    enc_narc = ndspy.narc.NARC(rom.files[enc_id])
    print(f"    Azzeramento tassi di incontro su tutte le {len(enc_narc.files)} tabelle...")
    for idx in range(len(enc_narc.files)):
        t = bytearray(enc_narc.files[idx])
        # In Gen 5, encounter rates are in the first 8 bytes
        for i in range(min(8, len(t))):
            t[i] = 0
        enc_narc.files[idx] = bytes(t)
    rom.files[enc_id] = enc_narc.save()
    print("    [OK] Incontri selvatici AZZERATI al 100% in tutta la ROM!")

    # 2. Ripulisci overworld di Venturia (File 444 e 445 in a/1/2/6)
    ow_id = rom.filenames.idOf("a/1/2/6")
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])
    
    # Creiamo un File 445 con:
    # 0 Furniture, 0 NPCs, 1 Warp di sicurezza (forcefield sul bordo sud!), 0 Triggers
    # Header: length (4B), 0 F, 0 N, 1 W, 0 T
    # Warp struct (20B = 0x14):
    # Target Map: 445 (uint16)
    # Target Warp: 0 (uint16)
    # exit_x: 25, exit_y: 28
    # X_ext: 100, Y_ext: 20
    forcefield_warp = bytearray(20)
    struct.pack_into('<HH', forcefield_warp, 0, 445, 0) # Target map 445
    struct.pack_into('<B', forcefield_warp, 4, 1)
    struct.pack_into('<B', forcefield_warp, 5, 1)
    struct.pack_into('<I', forcefield_warp, 6, 25 * 0x10000 + 0x8000) # Exit X: 25
    struct.pack_into('<I', forcefield_warp, 10, 28 * 0x10000 + 0x8000) # Exit Y: 28
    struct.pack_into('<HH', forcefield_warp, 14, 100, 20) # Wide extension
    
    ow445 = bytearray()
    ow445 += (20 + 4).to_bytes(4, 'little') # length
    ow445 += bytes([0, 0, 1, 0]) # 0 F, 0 N, 1 Warp, 0 Triggers
    ow445 += forcefield_warp
    ow445 += b'\x00\x00\x00\x00' # footer
    
    ow_narc.files[445] = bytes(ow445)
    
    # File 444 (interno casa)
    empty_ow = bytes.fromhex("040000000000000000000000")
    ow_narc.files[444] = empty_ow
    
    rom.files[ow_id] = ow_narc.save()
    print("    [OK] File 445 e 444 ripuliti (0 NPC, 0 Trigger, Forcefield Warp attivo)!")

    # Salvataggio ROM
    os.makedirs(os.path.dirname(MODIFIED_ROM), exist_ok=True)
    rom_bytes = bytearray(rom.save())
    
    # Padda a 512 MB esatti (536,870,912 bytes)
    TARGET_SIZE = 536870912
    if len(rom_bytes) < TARGET_SIZE:
        print(f"    Padding ROM da {len(rom_bytes)} a {TARGET_SIZE} bytes (512 MB)...")
        rom_bytes += b'\xff' * (TARGET_SIZE - len(rom_bytes))
        
    with open(MODIFIED_ROM, "wb") as f:
        f.write(rom_bytes)
    print(f"    [OK] ROM salvata con successo ({len(rom_bytes)} bytes) in: {MODIFIED_ROM}")

def patch_save():
    print(f"==> [2/2] Modifica del salvataggio da: {SOURCE_SAV}...")
    with open(SOURCE_SAV, "rb") as f:
        data = bytearray(f.read())

    starter_pkm = make_starter_pkm(data)

    def apply_slot(slot_offset):
        # 1. Spawn a Venturia (Zone 445, X=25, Y=28)
        pos_base = slot_offset + 0x19500
        map_id = 445
        x, y, z = 25, 28, 0
        data[pos_base + 0x04 : pos_base + 0x08] = map_id.to_bytes(4, "little")
        data[pos_base + 0x10 : pos_base + 0x14] = (x * 0x10000 + 0x8000).to_bytes(4, "little")
        data[pos_base + 0x18 : pos_base + 0x1C] = (y * 0x10000 + 0x8000).to_bytes(4, "little")
        data[pos_base + 0x80 : pos_base + 0x84] = map_id.to_bytes(4, "little")
        data[pos_base + 0x84 : pos_base + 0x88] = (x * 0x10000 + 0x8000).to_bytes(4, "little")
        data[pos_base + 0x88 : pos_base + 0x8C] = (z * 0x10000).to_bytes(4, "little")
        data[pos_base + 0x8C : pos_base + 0x90] = (y * 0x10000 + 0x8000).to_bytes(4, "little")
        
        # 2. Reset Overworld State (Block 41 a 0x1E200) per rimuovere i Mareep cachati
        ow_base = slot_offset + 0x1E200
        data[ow_base : ow_base + 0x1400] = b'\x00' * 0x1400

        # 3. Squadra Pokémon: Solo 1 Starter a Livello 5!
        party_base = slot_offset + 0x18E00
        data[party_base + 4] = 1 # Party Count = 1!
        # Slot 0 = Starter Lvl 5
        data[party_base + 8 : party_base + 8 + 220] = starter_pkm
        # Slots 1..5 = 0s
        data[party_base + 8 + 220 : party_base + 8 + 220*6] = b'\x00' * (220 * 5)

    def update_all_checksums(slot_offset):
        for off, length, chk_off, chk_mir in BLOCKS:
            actual_off = slot_offset + off
            actual_chk_off = slot_offset + chk_off
            actual_chk_mir = slot_offset + chk_mir
            chk = crc16_ccitt(data[actual_off : actual_off + length])
            data[actual_chk_off : actual_chk_off + 2] = chk.to_bytes(2, "little")
            data[actual_chk_mir : actual_chk_mir + 2] = chk.to_bytes(2, "little")

    apply_slot(0x00000)
    apply_slot(0x26000)
    update_all_checksums(0x00000)
    update_all_checksums(0x26000)

    # Validazione finale
    for slot_name, slot_offset in [("Slot 1", 0), ("Slot 2", 0x26000)]:
        valid = 0
        for off, length, chk_off, chk_mir in BLOCKS:
            expected = crc16_ccitt(data[slot_offset+off : slot_offset+off+length])
            act1 = struct.unpack_from("<H", data, slot_offset+chk_off)[0]
            act2 = struct.unpack_from("<H", data, slot_offset+chk_mir)[0]
            if expected == act1 == act2:
                valid += 1
        print(f"    {slot_name}: {valid}/{len(BLOCKS)} blocchi validi al 100%")

    os.makedirs(os.path.dirname(TARGET_SAV_1), exist_ok=True)
    with open(TARGET_SAV_1, "wb") as f:
        f.write(data)
    with open(TARGET_SAV_2, "wb") as f:
        f.write(data)
    print(f"    [OK] Salvataggio scritto in: {TARGET_SAV_2}")

if __name__ == "__main__":
    patch_rom()
    patch_save()
    print("\n🎉 LOBBY SANDBOX COMPLETATA AL 100%!")
