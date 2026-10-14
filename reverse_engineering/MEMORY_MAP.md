# 🗺️ Mappa di Memoria e Architettura Hardware: Pokémon Bianco 2

Questo documento descrive in dettaglio la mappa di memoria della console Nintendo DS, il layout di caricamento di **Pokémon Bianco 2 (IRDI)** e il funzionamento del runtime ARM9/ARM7.

---

## 🏗️ 1. Mappa di Memoria Nintendo DS

L'hardware del Nintendo DS ha un bus di indirizzi a 32 bit con due CPU collegate:

| Intervallo Indirizzi | Dimensione | Descrizione |
| :--- | :--- | :--- |
| `0x00000000 - 0x00003FFF` | 16 KB | ARM9 BIOS / Boot ROM |
| `0x01000000 - 0x01007FFF` | 32 KB | **ARM9 ITCM** (Instruction Tightly-Coupled Memory) - Zero-waitstate |
| `0x02000000 - 0x023FFFFF` | **4 MB** | **Main RAM comune** (Memoria Principale) |
| `0x027E0000 - 0x027E3FFF` | 16 KB | **ARM9 DTCM** (Data Tightly-Coupled Memory) - Stack veloce |
| `0x03000000 - 0x03007FFF` | 32 KB | Shared WRAM (Memoria condivisa ARM9 / ARM7) |
| `0x03800000 - 0x0380FFFF` | 64 KB | ARM7 Dedicated WRAM |
| `0x04000000 - 0x04FFFFFF` | - | **Registri Hardware I/O** (Schermi, DMA, Timer, 2D/3D) |
| `0x05000000 - 0x050007FF` | 2 KB | Standard Palette RAM (BG/OBJ Palette) |
| `0x06000000 - 0x067FFFFF` | 656 KB | VRAM (Video RAM - Banchi A-I rimappabili) |
| `0x07000000 - 0x070007FF` | 2 KB | OAM (Object Attribute Memory - Sprite) |
| `0x08000000 - 0x09FFFFFF` | Fino a 512 MB | **Game Cartridge ROM** (Slot-1 Game Pak) |

---

## 💾 2. Layout di Caricamento di Pokémon Bianco 2

### Header NDS (Primi 512 Byte della Cartuccia):
```text
0x000: "POKEMON W2\0\0" (Game Title - 12 byte)
0x00C: "IRDI"           (Game Code: I=NDS, RD=White 2, I=Italian)
0x010: "01"             (Maker Code: Nintendo)
0x020: 0x00004000       (ARM9 ROM Offset)
0x024: 0x02004800       (ARM9 Entry Point)
0x028: 0x02004000       (ARM9 RAM Load Address)
0x02C: 0x00073694       (ARM9 ROM Size = 472.724 byte compressi)
0x030: 0x0033A400       (ARM7 ROM Offset)
0x034: 0x02380000       (ARM7 Entry Point)
0x038: 0x02380000       (ARM7 RAM Load Address)
0x03C: 0x00028F84       (ARM7 ROM Size = 167.812 byte)
0x040: 0x00363400       (FNT Offset, dimensione 0x4F0)
0x048: 0x00363A00       (FAT Offset, dimensione 0x14B0 - 662 file)
0x050: 0x00077800       (ARM9 Overlay Table Offset, dim 0x2B00 - 344 entries)
```

### Struttura RAM Principale all'Avvio:
```text
0x02000000 ┌────────────────────────────────────────────────────────┐
           │ Riservato di sistema / Nintendo DS Kernel Data         │
0x02004000 ├────────────────────────────────────────────────────────┤
           │ Header ARM9 & Vettori di Eccezione                     │
0x02004800 ├────────────────────────────────────────────────────────┤
           │ Codice Principale (CRT0, Engine, SDK Nintendo)         │
           │ (633 KB fino a circa 0x0209EB80)                       │
0x0209EB80 ├────────────────────────────────────────────────────────┤
           │ Sezione Dati Globali Inizializzati (.data)             │
           │ Sezione Dati Non Inizializzati (.bss - azzerata a boot)│
0x02100000 ├────────────────────────────────────────────────────────┤
           │ AREA DINAMICA OVERLAYS:                                │
           │ Qui il motore carica e scambia gli Overlays (0..343)   │
           │ a seconda della scena (Overworld, Battaglia, Torneo)  │
0x02250000 ├────────────────────────────────────────────────────────┤
           │ Heap Dinamico di Gioco (allocazioni `sys_alloc`)       │
0x02380000 ├────────────────────────────────────────────────────────┤
           │ Spazio di lavoro ARM7 (Audio, WiFi, Touch)             │
0x023FFFFF └────────────────────────────────────────────────────────┘
```

---

## ⚡ 3. Sequenza di Boot CRT0 (Disassembly Dettagliato)

All'indirizzo `0x02004800`, l'hardware salta dopo che il bootloader del BIOS ha copiato l'ARM9 dalla ROM alla RAM:

```arm
; 1. Mascheramento Interrupt Principale
0x02004800  mov   ip, #0x4000000       ; Carica indirizzo base dei registri hardware
0x02004804  str   ip, [ip, #0x208]     ; Scrive su REG_IME (0x04000208) disabilitando interrupt

; 2. Inizializzazione Hardware Low-Level
0x02004808  bl    #0x2004a14           ; Chiama la routine di init del controller memoria

; 3. Azzeramento Sezioni BSS e Buffer di Boot
0x0200480C  mov   r0, #0               ; Valore di riempimento (zero)
0x02004810  ldr   r1, [pc, #0x194]     ; Indirizzo inizio buffer
0x02004814  ldr   r2, [pc, #0x194]     ; Dimensione buffer
0x02004818  bl    #0x2004a00           ; MI_CpuFill (memset)

; 4. Configurazione Tightly-Coupled Memories (ITCM / DTCM)
0x0200482C  ldr   r1, [pc, #0x188]     ; Controllo flag modalità boot
0x02004830  ldrh  r2, [r1]
0x02004834  cmp   r2, #0
0x02004838  moveq r2, #1
0x0200483C  strheq r2, [r1]
```

---

## 🧩 4. Meccanismo degli Overlays

Il Nintendo DS dispone di soli 4 MB di RAM. Pokémon Bianco 2 è un gioco mastodontico (con animazioni complete, centinaia di animazioni di mosse, il torneo mondiale PWT, Pokéstar Studios, ecc.). Per fare spazio:

- I programmatori hanno suddiviso il codice in **344 Overlays**.
- Ogni overlay nella tabella `arm9_overlays.json` possiede:
  - **`ram_address`**: L'indirizzo esatto di RAM a cui viene caricato.
  - **`ram_size`**: Dimensione in byte occupata in memoria.
  - **`bss_size`**: Memoria aggiuntiva azzerata al caricamento.
  - **`file_id`**: L'ID nel filesystem NDS corrispondente.

### Esempi di Overlays Noti in B2W2:
- **Overlay 0 / 1 / 2**: Motore di rendering 3D dell'Overworld e gestione telecamera.
- **Overlay 12 / 14 / 16**: Motore di Battaglia (calcolo danni, intelligenza artificiale avversari, visualizzazione sprite animati).
- **Overlay 78..95**: Minigiochi e funzionalità speciali (Pokéstar Studios, Musical, C-Gear).
- **Overlay 150..210**: Pokémon World Tournament (PWT) e strutture Lotta Speciali.
