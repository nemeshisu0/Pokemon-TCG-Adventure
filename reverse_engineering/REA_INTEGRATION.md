# 🔌 Integrazione REA (Reverse Engineer Anything)

Questa guida illustra come **REA** (`morluto/rea`) è installato e configurato nel sistema, come utilizzarlo sia da riga di comando che attraverso l'assistente AI (tramite protocollo MCP), e come sfruttarlo per l'analisi dei binari di Pokémon Bianco 2.

---

## 📌 1. Installazione e Percorsi nel Sistema

- **Repository Sorgente**: `/home/nemesy/rea` (compilata localmente da TypeScript con `turbo`).
- **Binario Eseguibile**: `/home/nemesy/.local/bin/rea` (incluso nel `$PATH` utente).
- **Versione Attuale**: `6.4.0` (con supporto raw-binary, ARM e 6502).
- **Configurazione MCP**: `/home/nemesy/.gemini/config/mcp_config.json`.

---

## 🤖 2. Funzionamento con l'Assistente AI (Protocollo MCP)

REA è registrato come **MCP Server** (*Model Context Protocol*). Questo significa che l'assistente AI ha accesso diretto ai seguenti strumenti avanzati:
- `inspect_native_load_image`: Verifica mappatura in memoria, entry point e sezioni.
- `inspect_native_instruction`: Decodifica delle singole istruzioni assembly e operandi.
- `inspect_native_api`: Ricostruzione delle firme delle funzioni e convenzioni di chiamata.
- `search`: Ricerca di stringhe o simboli analizzati nel binario.
- `trace`: Tracciamento dei riferimenti incrociati di un valore o funzione (XREFs).

---

## 💻 3. Comandi CLI Pronti all'Uso

### A. Ispezione Raw Binary dell'ARM9
Dato che il Nintendo DS esegue codice nativo ARM (ARMv5TE) caricato direttamente in RAM, possiamo eseguire l'ispezione fornendo l'architettura e l'entry point:

```bash
rea inspect reverse_engineering/arm9_decompressed.bin \
  --target-format raw-binary \
  --architecture arm \
  --entry-point 0x02004800
```

### B. Ispezione delle Istruzioni Assembly
```bash
rea instructions reverse_engineering/arm9_decompressed.bin \
  --target-format raw-binary \
  --architecture arm \
  --entry-point 0x02004800
```

### C. Verifica Stato e Diagnostica REA
Per verificare lo stato di salute dei provider collegati a REA:
```bash
rea doctor
```

---

## 🧠 4. Configurazione Decompiler Avanzato (Ghidra / IDA)

REA delega la decompilazione in pseudocodice C a motori locali di reverse engineering, principalmente **Ghidra**:

Per abilitare la decompilazione automatica C in REA:
1. Installa Ghidra (versione 12.1.x) e un JDK 21/17:
   ```bash
   sudo pacman -S jdk-openjdk ghidra
   ```
2. Imposta la variabile d'ambiente nel tuo `.bashrc` o nella sessione:
   ```bash
   export GHIDRA_INSTALL_DIR=/percorso/di/ghidra
   ```
3. A quel punto i comandi `rea decompile` e `rea function` produrranno pseudocodice C completo per qualsiasi routine ARM del gioco.
