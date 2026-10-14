# 🔬 Pokémon Bianco 2 - Modulo Reverse Engineering & Analisi Binaria

Questo modulo contiene l'analisi completa di basso livello, i binari estratti e gli strumenti di disassemblaggio e ispezione dati per la ROM di **Pokémon Bianco 2 (Nintendo DS)**. È integrato con il toolkit **REA (Reverse Engineer Anything)**.

---

## 📂 Contenuto del Modulo

```text
reverse_engineering/
├── 📄 README.md                <- Questa guida
├── 📄 MEMORY_MAP.md            <- Mappa completa memoria NDS, registri I/O ed entry points
├── 📄 NARC_CATALOG.md          <- Catalogo ragionato dei 308 archivi NARC di Pokémon B2W2
├── 📄 REA_INTEGRATION.md       <- Guida all'uso di REA (CLI e protocollo MCP) con la ROM
│
├── ⚙️ disasm.py                 <- Disassemblatore Python (Capstone) per ARM9, ARM7 e Overlays
├── ⚙️ narc_tool.py              <- Ispezione ed estrazione di archivi NARC del NitroFS
├── 🚀 run-disasm.sh            <- Wrapper shell per disassemblare con 1 comando
├── 🚀 run-narc.sh              <- Wrapper shell per esplorare ed estrarre i NARC
│
├── 📦 arm9.bin                 <- Codice eseguibile ARM9 compresso originale (472 KB)
├── 📦 arm9_decompressed.bin    <- Codice eseguibile ARM9 decompresso (633 KB, ARMv5TE)
├── 📦 arm7.bin                 <- Codice eseguibile ARM7 (167 KB, ARMv4T)
├── 📊 arm9_overlays.json       <- Tabella metadati dei 344 Overlays registrati
├── 📊 filesystem_catalog.json  <- Catalogo di tutti i 662 file del NitroFS
└── 📂 overlays9/               <- I 344 binari degli overlay ARM9 estratti (.bin)
```

---

## 🎮 Specifiche Tecniche della ROM

| Parametro | Valore | Note |
| :--- | :--- | :--- |
| **File ROM** | `roms/original/Bianco 2.nds` | Backup originale (512 MB) |
| **Game Title** | `POKEMON W2` | Titolo registrato nell'header NDS |
| **Game Code** | `IRDI` | Identificativo univoco (Edizione Italiana) |
| **Maker Code** | `01` | Nintendo |
| **ARM9 Base RAM** | `0x02004000` | Indirizzo di caricamento in memoria principale |
| **ARM9 Entry Point** | `0x02004800` | Punto di inizio esecuzione CRT0 |
| **ARM9 Dimensione** | `633.664 byte` | Decompresso da 472.724 byte (BLZ LZSS) |
| **ARM7 Base / Entry** | `0x02380000` | Sub-CPU per I/O, audio e touch screen |
| **Overlays ARM9** | 344 totali | Moduli di codice caricati dinamicamente in RAM |
| **Archivi NARC** | 308 archivi | Contenitori compatti di tutti i dati di gioco |

---

## 🚀 Guida Rapida all'Uso degli Strumenti

### 1. Disassemblare Codice (ARM / Thumb)
Puoi visualizzare le istruzioni Assembly a qualsiasi indirizzo RAM utilizzando lo script wrapper:

```bash
# Disassembla l'entry point (25 istruzioni ARM a 0x02004800)
./reverse_engineering/run-disasm.sh 0x02004800 -n 25

# Disassembla codice Thumb (aggiungi -t)
./reverse_engineering/run-disasm.sh 0x02012000 -t -n 30
```

### 2. Ispezionare ed Estrarre Archivi NARC
Tutti i dati del gioco (testi, sprite, statistiche, script, mappe) risiedono all'interno degli archivi NARC nel percorso `a/`:

```bash
# Ispeziona i file contenuti nelle statistiche Pokémon (a/0/1/6)
./reverse_engineering/run-narc.sh "a/0/1/6"

# Ispeziona i banchi di testo di gioco (a/0/0/2)
./reverse_engineering/run-narc.sh "a/0/0/2"

# Estrai tutti i file interni di un NARC in una cartella
./reverse_engineering/run-narc.sh "a/0/1/6" -x ./dump_stats
```

### 3. Utilizzo di REA (Reverse Engineer Anything)
REA è configurato localmente su `~/.local/bin/rea` e come MCP Server per l'assistente:

```bash
# Ispezione raw-binary con REA
rea inspect reverse_engineering/arm9_decompressed.bin \
  --target-format raw-binary --architecture arm --entry-point 0x02004800
```
Consulta [`REA_INTEGRATION.md`](REA_INTEGRATION.md) per i dettagli di integrazione avanzata.

---

## 📚 Documenti di Approfondimento
- 🗺️ [`MEMORY_MAP.md`](MEMORY_MAP.md) - Mappa dettagliata degli indirizzi di memoria, sezioni ELF/NDS e sequenza di boot.
- 📁 [`NARC_CATALOG.md`](NARC_CATALOG.md) - Guida a tutti i file NARC essenziali per modifiche e modding.
- 🔌 [`REA_INTEGRATION.md`](REA_INTEGRATION.md) - Guida a REA CLI, server MCP e collegamento a decompiler (Ghidra/IDA).
