# PUNTO DI RIPRISTINO — Pokemon TCG Adventure Client
**Data:** 2026-10-06 | **Versione:** Checkpoint 6

---

## A che punto siamo

Il progetto e' un **client desktop Python/PyQt6** che integra:
- **Emulatore DS melonDS** (via libretro `.so`) direttamente *in-process*, senza finestre esterne
- **Scanner TCG** con webcam per scansionare carte Pokemon fisiche
- **Sistema di iniezione** dei Pokemon ottenuti dalle carte nel salvataggio del gioco

Il launcher funziona, il gioco si avvia e raggiunge il titolo. Esiste pero' un **bug aperto** nell'overworld.

---

## Cosa e' gia' implementato e funziona

### 1. Architettura Finestra Unica (Sezione 1 della checklist — COMPLETA)
- [x] **Launcher** (`launcher_window.py`) — Login/Registrazione account, selezione ROM, selezione risoluzione
- [x] **Game Client** (`game_client.py`) — Finestra unica con HUD superiore orizzontale
- [x] **Core melonDS in-process** (`core/engine_worker.py` + `core/runner.py`)
  - Il core `.so` gira in un **processo figlio dedicato** separato dal thread Qt
  - Comunicazione tramite **SharedMemory POSIX** a 60 FPS
  - Il frame video viene estratto dalla memoria condivisa e iniettato nei widget QLabel
- [x] **Schermo superiore DS** — scalabile, in alta definizione (256x192 → 1080p)
- [x] **Schermo Touch a scomparsa** — pulsante nell'HUD, appare/scompare su richiesta (Tab o click)
- [x] **Variabili core melonDS** via `RETRO_ENVIRONMENT_GET_VARIABLE`:
  - JIT disabilitato (evita schermata bianca in B2W2)
  - Boot diretto alla cartuccia (evita la schermata nera iniziale)
  - Lingua italiana

### 2. Input e Tasti (COMPLETO)
- [x] **Tastiera** — rimappabile completamente dall'utente
- [x] **Gamepad/Controller** (`gamepad_handler.py`) — rileva automaticamente Xbox/PS/USB via `evdev`
- [x] **Schermo touch** — click del mouse trasmesso come tocco DS (`RETRO_DEVICE_POINTER`)
- [x] **Pulsante "Impostazioni"** nell'HUD superiore
- [x] **SettingsDialog** (`settings_dialog.py`) — dialogo modale per rimappare i 12 tasti DS
- [x] **SettingsManager** (`settings_manager.py`) — salvataggio/caricamento bindings in `config/keybindings.json`

### 3. TCG Core e Iniezione (COMPLETO — gia' testato)
- [x] Regole Tier (1-6), 7 Ere storiche, 7 gradi Pokeball
- [x] Nerf Leggendari, Double Shiny, Anti-Duplicazione
- [x] Iniezione nel salvataggio utente (`saves/profiles/<username>/save.sav`)
- [x] Sincronizzazione salvataggio all'apertura/chiusura sessione

---

## BUG CRITICO APERTO: Crash nell'Overworld

### Sintomo
Dopo circa **5 secondi** dall'ingresso nell'overworld (dopo il titolo e i dialoghi iniziali), il gioco mostra la schermata rossa di sistema DS con il messaggio:
> "Errore di comunicazione. Spegni la console."

### Ipotesi indagate (non ancora risolte)
1. **Firmware non autentico** — Il core melonDS cerca `bios7.bin`, `bios9.bin`, `firmware.bin` nella cartella di sistema. Se usa il FreeBIOS interno, il CRC16 risulta "BAD" e certi moduli del firmware DS crashano.
2. **Protezione Anti-Pirateria (AP) della ROM** — Pokemon Bianco 2 ha check AP che, se scoperti dall'emulatore senza patch, causano crash mirati nell'overworld.
3. **Init C-Gear / Wi-Fi** — Il modulo Wi-Fi/C-Gear del DS prova a inizializzarsi non appena il giocatore entra nel mondo, richiedendo firmware autentico.
4. **Memory Alignment nel buffer SHM** — Problema nel calcolo dell'offset dei frame 256x192 nella SharedMemory (meno probabile, ma escluso solo parzialmente).

### Prossimi passi consigliati
- **Opzione A (Facile):** Posizionare file BIOS autentici (`bios7.bin`, `bios9.bin`, `firmware.bin`) nella cartella `launcher/core/`. Il percorso e' gia' comunicato al core via `RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY`.
- **Opzione B (Tecnica):** Applicare una patch AP alla ROM `roms/modified/Bianco 2.nds` per neutralizzare i check antipirateria.

---

## Cosa manca (Sezioni 2-4 della checklist — NON INIZIATE)

### Sezione 2 — Scanner verticale TCG
- [ ] Box video webcam in formato portrait (rapporto 2.5:3.5, proporzioni carta Pokemon reale)
- [ ] Mirino verticale proporzionato alla carta fisica

### Sezione 3 — Helper intelligente e feedback scansione
- [ ] Animazione laser/linea di scansione mentre analizza la carta
- [ ] Rilevamento dimensioni e posizione carta in tempo reale con OpenCV
  - [ ] Messaggi: "Avvicina la carta", "Allontana la carta", "Centra la carta"
  - [ ] Cambio colore mirino in verde fluorescente quando la posizione e' perfetta

### Sezione 4 — Gestione telecamera on-demand
- [ ] Telecamera spenta all'avvio (privacy + risparmio risorse)
- [ ] Schermata di standby con pulsante "Avvia Scansione Pokemon"
- [ ] Accensione hardware su richiesta (click pulsante)
- [ ] Pulsante "Ferma Scansione" e auto-stop al riscatto carta

---

## Struttura del progetto

```
pokemon-b2w2-project/
|
+-- launcher/
|   +-- core/
|   |   +-- melonds_core.so        <- Core libretro melonDS compilato
|   |   +-- engine_worker.py       <- Worker processo figlio (loop retro_run)
|   |   +-- runner.py              <- Thread Qt: SharedMemory + polling frame
|   |
|   +-- game_client.py             <- Finestra principale di gioco (HUD + schermo DS + scanner)
|   +-- launcher_window.py         <- Launcher: login, selezione ROM, avvio sessione
|   +-- settings_manager.py        <- Gestione configurazione tasti (JSON)
|   +-- settings_dialog.py         <- Dialogo modale rimapping tasti
|   +-- gamepad_handler.py         <- Listener controller USB/BT (evdev)
|   +-- account_manager.py         <- Gestione account utenti
|   +-- rom_manager.py             <- Gestione percorso ROM e configurazione
|   +-- ui_theme.py                <- Tema visivo PyQt6
|
+-- roms/
|   +-- original/                  <- ROM originale (non toccare)
|   +-- modified/                  <- ROM con patch (Bianco 2.nds)
|
+-- saves/
|   +-- profiles/<username>/       <- Salvataggio per profilo utente
|   +-- Pokemon Bianco 2.sav       <- Salvataggio attivo sincronizzato
|
+-- config/
|   +-- accounts.json              <- Database account
|   +-- keybindings.json           <- Configurazione tasti salvata
|   +-- launcher_config.json       <- Config launcher (ROM path, risoluzione...)
|   +-- rules.json                 <- Regole TCG
|
+-- scanner/                       <- Modulo scanner TCG (webcam + riconoscimento)
|   +-- .venv/                     <- Ambiente virtuale Python
|
+-- rollback/                      <- QUESTA CARTELLA (punto di ripristino)
|   +-- STATO_ATTUALE.md           <- Questo file
|   +-- files/                     <- Copie dei file sorgente critici
|
+-- run-client.sh                  <- Script di avvio principale
+-- PROJECT_CHECKLIST.md           <- Checklist ufficiale del progetto
+-- README.md
```

---

## Come avviare il progetto

```bash
cd /home/nemesy/Projects/pokemon-b2w2-project
./run-client.sh
```

L'ambiente virtuale si trova in `scanner/.venv/`. Lo script lo usa automaticamente.

**Dipendenze Python principali:**
- `PyQt6` — UI grafica
- `evdev` — Supporto gamepad Linux
- `ctypes` — Interfaccia con melonds_core.so

---

## Come usare questo rollback

Se le modifiche successive rompono qualcosa, per ripristinare i file critici:

```bash
cd /home/nemesy/Projects/pokemon-b2w2-project

# Ripristina tutti i file critici
cp rollback/files/game_client.py      launcher/game_client.py
cp rollback/files/launcher_window.py  launcher/launcher_window.py
cp rollback/files/engine_worker.py    launcher/core/engine_worker.py
cp rollback/files/runner.py           launcher/core/runner.py
cp rollback/files/settings_manager.py launcher/settings_manager.py
cp rollback/files/settings_dialog.py  launcher/settings_dialog.py
cp rollback/files/gamepad_handler.py  launcher/gamepad_handler.py
```

---

## Note tecniche importanti

| Dettaglio | Valore |
|---|---|
| Cartella sistema melonDS | `launcher/core/` (stessa del `.so`) |
| Formato frame video | XRGB32 (4 byte/pixel) |
| Risoluzione DS | 256 x 192 pixel per schermo |
| Buffer SharedMemory | 1024 x 384 byte (pitch=1024, due schermi sovrapposti) |
| Tasto Tab | Toggle schermo touch |
| Porta gamepad | Solo port=0 (giocatore 1) |
| Script avvio | run-client.sh -> scanner/.venv/bin/python launcher/launcher_window.py |
| Indice 30 control_arr | Running flag (1=running, 0=stop) |
| Indice 31 control_arr | Frame counter (incrementato ad ogni nuovo frame) |
| Indici 0-15 control_arr | Stato tasti joypad DS (RETRO_DEVICE_ID_JOYPAD_*) |
| Indici 16-18 control_arr | Touch screen (16=pressed, 17=x, 18=y) |
