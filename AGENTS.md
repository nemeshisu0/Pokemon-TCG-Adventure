# 🧠 Memoria e Integrazioni di Progetto: NMSYai & Reverse Engineering

Questo file memorizza il contesto permanente del workspace per tutte le sessioni di Antigravity, come richiesto dall'utente.

---

## ⚡ 1. NMSYai (AI Personale per il Coding di Nemesy)
* **Percorso locale:** `/home/nemesy/NMSYai`
* **Natura:** Intelligenza artificiale personale autonoma (100% controllata dall'utente, Budget: 0,00 €), con suite di 54 test unitari (`pytest`), interfaccia Web UI (`http://127.0.0.1:8765`) e CLI da terminale.
* **Memoria Persistente FTS5:** Database SQLite in `/home/nemesy/NMSYai/data/nmsyai.db` contenente oltre 2.140 ricordi e soluzioni tecniche specifiche per questo progetto.
* **Specializzazioni & Skill Verticali (`nmsyai/skills/registry.py`):**
  1. `pokemon_b2w2`: Formato PK5, checksum CRC-16-CCITT per salvataggi `.sav` a 512 KB, calcolo PID, Square Shiny, iniezione carte TCG.
  2. `melonds_cpp`: Basso livello C/C++ su `melonds_core.so`, RAM fisica ARM946E-S, bypass C-Gear (offset `0x21EA25`), memoria condivisa 60 FPS.
  3. `opencv_scanner`: Computer Vision per scanner webcam (`warpPerspective`, ORB/SIFT, rilevamento foil/holo per carte fisiche).
  4. `pokemon_legality`: Validatore matematico anti-cheat per salvataggi Pokémon di 5ª generazione.
  5. `sdat_audio`: Sound engine Nintendo DS `sound_data.sdat`, sequenze SSEQ, banchi SBNK.
  6. `pyqt6_architect`: Architettura interfaccia Launcher con temi scuri QSS e rendering 60 FPS.
  7. `hyprland_ops`: Script di sistema per Arch Linux, Hyprland, ASUS VivoBook (GPU Intel Iris Xe).
  8. `roadmap_planner`: Pianificazione avanzata e checklist operative.
  9. `code_debugger`: Audit e correzione del codice sorgente.
* **Tools di modifica sicura (`nmsyai/agent/tools.py`):** `ProjectAgentManager` con prevenzione path traversal e backup automatici antiritorno in `.nmsyai_backup/`.

---

## 🔬 2. Modulo di Reverse Engineering
* **Percorso locale:** `/home/nemesy/Projects/pokemon-b2w2-project/reverse_engineering`
* **Componenti chiave:**
  1. **ARM9 Decompresso:** `arm9_decompressed.bin` (633 KB, ARMv5TE, base RAM `0x02004000`, entry point `0x02004800`).
  2. **344 Overlays Decompressi:** `overlays9/overlay9_0000.bin` ... `overlay9_0343.bin` con metadati e indirizzi RAM in `arm9_overlays.json`.
  3. **Disassemblatore Python (Capstone):** `run-disasm.sh <indirizzo_ram> [-t] [-n num]` per analizzare istruzioni ARM e Thumb.
  4. **NARC Tool (ndspy):** `run-narc.sh <percorso_narc> [-x cartella_dump]` per ispezionare ed estrarre banchi di dati interni (es. stats Pokémon `a/0/1/6`, script overworld `a/0/5/6`, testi `a/0/0/2`, matrici `a/0/0/8`).
  5. **Integrazione REA (`morluto/rea`):** Binario `~/.local/bin/rea` v6.4.0, configurato come MCP Server in `~/.gemini/config/mcp_config.json`.
  6. **Documentazione di Riferimento:** `MEMORY_MAP.md` e `NARC_CATALOG.md`.

---

## 🎯 Regole Operative per l'Assistente
1. **Uso mirato e on-demand:** NON invocare né eseguire comandi pesanti di reverse engineering o query a NMSYai quando non sono strettamente necessari (evitare spreco di token o operazioni ridondanti per modifiche semplici).
2. **Attivazione quando servono:**
   * Se sorgono problemi complessi su strutture binarie (es. corruzioni di salvataggi, calcoli PK5, crash di memoria nel core C++ di melonDS o configurazioni Wayland/Hyprland), consulta la memoria o i moduli di **NMSYai**.
   * Se serve identificare routine di codice interne alla ROM (es. trigger di script, animazioni, logica delle lotte) o estrarre/modificare archivi interni del gioco, usa gli strumenti di **Reverse Engineering** (`run-narc.sh`, `run-disasm.sh`, binari decompresso ARM9/Overlays).
