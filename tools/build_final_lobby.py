#!/usr/bin/env python3
import os
import struct
import ndspy.rom
import ndspy.narc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_ROM = os.path.join(BASE_DIR, 'roms', 'original', 'Bianco 2.nds')
MODIFIED_ROM = os.path.join(BASE_DIR, 'roms', 'modified', 'Bianco 2.nds')
SOURCE_SAV = '/home/nemesy/Documents/progetti stani miei/roms/Pokémon Bianco 2.sav'
TARGET_SAV_1 = os.path.join(BASE_DIR, 'saves', 'Pokémon Bianco 2.sav')
TARGET_SAV_2 = os.path.join(BASE_DIR, 'roms', 'modified', 'Bianco 2.sav')

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

def make_barrier_npc(npc_id, sprite_id, raw_x, raw_y, facing=0):
    npc = bytearray(36)
    struct.pack_into('<H', npc, 0, npc_id)
    struct.pack_into('<H', npc, 2, sprite_id)
    struct.pack_into('<H', npc, 4, 0)
    struct.pack_into('<H', npc, 6, 0)
    struct.pack_into('<H', npc, 8, 0)
    struct.pack_into('<H', npc, 10, 0)
    struct.pack_into('<H', npc, 12, facing)
    struct.pack_into('<H', npc, 14, 0)
    struct.pack_into('<H', npc, 28, raw_x)
    struct.pack_into('<H', npc, 30, raw_y)
    struct.pack_into('<H', npc, 32, 0)
    struct.pack_into('<H', npc, 34, 1)
    return npc

def make_starter_pkm(source_data):
    slot0_raw = source_data[0x18E08:0x18E08+220]
    pid = struct.unpack_from('<I', slot0_raw, 0)[0]
    chk = struct.unpack_from('<H', slot0_raw, 6)[0]
    blocks = {}
    for i, b_name in enumerate(['A', 'B', 'C', 'D']):
        blocks[b_name] = bytearray(slot0_raw[8 + i*32 : 8 + (i+1)*32])
    p_data = bytearray(slot0_raw[136:220])
    
    struct.pack_into('<H', blocks['A'], 0x00, 501)
    struct.pack_into('<I', blocks['A'], 0x08, 125)
    struct.pack_into('<4H', blocks['B'], 0x00, 33, 39, 55, 0)
    struct.pack_into('<4B', blocks['B'], 0x08, 35, 30, 25, 0)
    struct.pack_into('<4B', blocks['B'], 0x0C, 35, 30, 25, 0)
    struct.pack_into('<B', p_data, 0x04, 5)
    struct.pack_into('<H', p_data, 0x06, 20)
    struct.pack_into('<H', p_data, 0x08, 20)
    struct.pack_into('<H', p_data, 0x0A, 11)
    struct.pack_into('<H', p_data, 0x0C, 10)
    struct.pack_into('<H', p_data, 0x0E, 10)
    struct.pack_into('<H', p_data, 0x10, 12)
    struct.pack_into('<H', p_data, 0x12, 10)
    
    new_chk = 0
    for b_name in ['A', 'B', 'C', 'D']:
        for j in range(0, 32, 2):
            new_chk = (new_chk + struct.unpack_from('<H', blocks[b_name], j)[0]) & 0xFFFF
            
    out = bytearray(220)
    struct.pack_into('<I', out, 0, pid)
    struct.pack_into('<H', out, 4, 0)
    struct.pack_into('<H', out, 6, new_chk)
    
    shift = ((pid >> 13) & 31) % 24
    PERMUTATIONS = [
        ['A', 'B', 'C', 'D'], ['A', 'B', 'D', 'C'], ['A', 'C', 'B', 'D'], ['A', 'C', 'D', 'B'],
        ['A', 'D', 'B', 'C'], ['A', 'D', 'C', 'B'], ['B', 'A', 'C', 'D'], ['B', 'A', 'D', 'C'],
        ['B', 'C', 'A', 'D'], ['B', 'C', 'D', 'A'], ['B', 'D', 'A', 'C'], ['B', 'D', 'C', 'A'],
        ['C', 'A', 'B', 'D'], ['C', 'A', 'D', 'B'], ['C', 'B', 'A', 'D'], ['C', 'B', 'D', 'A'],
        ['C', 'D', 'A', 'B'], ['C', 'D', 'B', 'A'], ['D', 'A', 'B', 'C'], ['D', 'A', 'C', 'B'],
        ['D', 'B', 'A', 'C'], ['D', 'B', 'C', 'A'], ['D', 'C', 'A', 'B'], ['D', 'C', 'B', 'A']
    ]
    order = PERMUTATIONS[shift]
    
    seed_chk = new_chk
    def next_chk_u16():
        nonlocal seed_chk
        seed_chk = (seed_chk * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        return (seed_chk >> 16) & 0xFFFF
        
    seed_pid = pid
    def next_pid_u16():
        nonlocal seed_pid
        seed_pid = (seed_pid * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        return (seed_pid >> 16) & 0xFFFF
        
    for i, b_name in enumerate(order):
        b = blocks[b_name]
        for j in range(0, 32, 2):
            val = struct.unpack_from('<H', b, j)[0]
            val ^= next_chk_u16()
            struct.pack_into('<H', out, 8 + i*32 + j, val)
            
    for j in range(0, 84, 2):
        val = struct.unpack_from('<H', p_data, j)[0]
        val ^= next_pid_u16()
        struct.pack_into('<H', out, 136 + j, val)
        
    return bytes(out)

def patch_rom():
    rom = ndspy.rom.NintendoDSRom.fromFile(ORIGINAL_ROM)

    # 1. Incontri selvatici a zero
    enc_id = rom.filenames.idOf('a/1/2/7')
    enc_narc = ndspy.narc.NARC(rom.files[enc_id])
    for idx in range(len(enc_narc.files)):
        t = bytearray(enc_narc.files[idx])
        for i in range(min(8, len(t))):
            t[i] = 0
        enc_narc.files[idx] = bytes(t)
    rom.files[enc_id] = enc_narc.save()

    # 2. Percorso 20 = VUOTO
    maps_id = rom.filenames.idOf('a/0/0/8')
    maps_narc = ndspy.narc.NARC(rom.files[maps_id])
    dummy_map = maps_narc.files[1053]
    maps_narc.files[446] = dummy_map
    maps_narc.files[447] = dummy_map

    # 3. Griglia di collisione: muro solido a sud (da Y=21 in poi) su tutte le mappe coinvolte
    for m_idx in [444, 445, 1006]:
        if m_idx < len(maps_narc.files):
            fm = bytearray(maps_narc.files[m_idx])
            bmd_end = struct.unpack_from('<I', fm, 8)[0]
            for y in range(21, 32):
                for x in range(32):
                    tile_off = bmd_end + 4 + (y * 32 + x) * 8
                    if tile_off + 8 <= len(fm):
                        struct.pack_into('<4H', fm, tile_off, 0, 3, 27, 64)
            maps_narc.files[m_idx] = bytes(fm)
    rom.files[maps_id] = maps_narc.save()

    # 4. Map Matrix
    mm_id = rom.filenames.idOf('a/0/0/9')
    mm_narc = ndspy.narc.NARC(rom.files[mm_id])
    f0 = bytearray(mm_narc.files[0])
    w = 29
    off_2_24 = 8 + (24 * w + 2) * 8
    struct.pack_into('<4H', f0, off_2_24, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
    mm_narc.files[0] = bytes(f0)
    rom.files[mm_id] = mm_narc.save()

    # 5. PERSONAGGI DI BLOCCO DAVANTI ALLA PORTA (World + Local Coords)
    barrier_npcs = []
    idx = 0

    # A) World Coords (per outdoor engine di Unima)
    for wy, spr in [(437, 57), (438, 52), (439, 57), (440, 52)]:
        for wx in [407, 408, 409, 410]:
            barrier_npcs.append(make_barrier_npc(idx, spr, wx, wy, facing=0))
            idx += 1

    # B) Local Coords (per local grid engine)
    for ly, spr in [(21, 52), (22, 57), (23, 52), (24, 57)]:
        for lx in [23, 24, 25, 26]:
            barrier_npcs.append(make_barrier_npc(idx, spr, lx, ly, facing=0))
            idx += 1

    num_npcs = len(barrier_npcs)
    ow_barrier = bytearray()
    ow_data_len = num_npcs * 36 + 4
    ow_barrier += ow_data_len.to_bytes(4, 'little')
    ow_barrier += bytes([0, num_npcs, 0, 0])
    for b_npc in barrier_npcs:
        ow_barrier += b_npc
    ow_barrier += b'    '

    ow_id = rom.filenames.idOf('a/1/2/6')
    ow_narc = ndspy.narc.NARC(rom.files[ow_id])
    for f_idx in [305, 306, 444, 445]:
        ow_narc.files[f_idx] = bytes(ow_barrier)
    rom.files[ow_id] = ow_narc.save()

    # 6. Init scripts disabilitati
    scr_id = rom.filenames.idOf('a/0/5/6')
    scr_narc = ndspy.narc.NARC(rom.files[scr_id])
    for s_idx in [891, 315, 888, 889, 890]:
        scr_narc.files[s_idx] = b'    '
    rom.files[scr_id] = scr_narc.save()

    # Padding a 512 MB
    rom_bytes = bytearray(rom.save())
    TARGET_SIZE = 536870912
    if len(rom_bytes) < TARGET_SIZE:
        rom_bytes += bytes([0xFF]) * (TARGET_SIZE - len(rom_bytes))

    with open(MODIFIED_ROM, 'wb') as f:
        f.write(rom_bytes)
    print(f'[OK] ROM salvata con {num_npcs} personaggi di sbarramento (World + Local)!')

def patch_save():
    with open(SOURCE_SAV, 'rb') as f:
        data = bytearray(f.read())

    starter_pkm = make_starter_pkm(data)

    def apply_slot(slot_offset):
        pos_base = slot_offset + 0x19500
        map_id = 445
        x, y, z = 25, 20, 0
        data[pos_base + 0x04 : pos_base + 0x08] = map_id.to_bytes(4, 'little')
        data[pos_base + 0x10 : pos_base + 0x14] = (x * 0x10000 + 0x8000).to_bytes(4, 'little')
        data[pos_base + 0x18 : pos_base + 0x1C] = (y * 0x10000 + 0x8000).to_bytes(4, 'little')
        data[pos_base + 0x80 : pos_base + 0x84] = map_id.to_bytes(4, 'little')
        data[pos_base + 0x84 : pos_base + 0x88] = (x * 0x10000 + 0x8000).to_bytes(4, 'little')
        data[pos_base + 0x88 : pos_base + 0x8C] = (z * 0x10000).to_bytes(4, 'little')
        data[pos_base + 0x8C : pos_base + 0x90] = (y * 0x10000 + 0x8000).to_bytes(4, 'little')
        
        t_base = slot_offset + 0x19400
        data[t_base + 0x24 : t_base + 0x28] = b'    '
        misc_base = slot_offset + 0x21100
        data[misc_base + 0x04] = 0
        dex_base = slot_offset + 0x21400
        data[dex_base : dex_base + 0x04DC] = b' ' * 0x04DC
        ow_base = slot_offset + 0x1E200
        data[ow_base : ow_base + 0x1400] = b' ' * 0x1400
        party_base = slot_offset + 0x18E00
        data[party_base + 4] = 1
        data[party_base + 8 : party_base + 8 + 220] = starter_pkm
        data[party_base + 8 + 220 : party_base + 8 + 220*6] = b' ' * (220 * 5)

    def update_all_checksums(slot_offset):
        for off, length, chk_off, chk_mir in BLOCKS:
            chk = crc16_ccitt(data[slot_offset+off : slot_offset+off+length])
            data[slot_offset+chk_off : slot_offset+chk_off+2] = chk.to_bytes(2, 'little')
            data[slot_offset+chk_mir : slot_offset+chk_mir+2] = chk.to_bytes(2, 'little')

    apply_slot(0x00000)
    apply_slot(0x26000)
    update_all_checksums(0x00000)
    update_all_checksums(0x26000)

    with open(TARGET_SAV_1, 'wb') as f:
        f.write(data)
    with open(TARGET_SAV_2, 'wb') as f:
        f.write(data)
    print('[OK] Salvataggio scritto con successo!')

if __name__ == '__main__':
    patch_rom()
    patch_save()
    print('BUILD COMPLETATA!')
