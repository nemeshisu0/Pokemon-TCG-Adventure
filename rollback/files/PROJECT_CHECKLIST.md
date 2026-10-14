# CHECKLIST UFFICIALE: POKÉMON TCG ADVENTURE CLIENT

### 1. Architettura a Finestra Unica (Emulatore Incorporato)
- [x] **Eliminazione finestra esterna staccata**: niente finestra separata di melonDS sul desktop o affiancata da Hyprland.
- [x] **Embedding diretto**: il core C++ di melonDS (`melonds_core.so`) gira direttamente in-process dentro la nostra applicazione PyQt6.
- [x] **Layout a schermo singolo**: visualizzazione primaria dello schermo superiore DS in alta definizione scalabile.
- [x] **Schermo Touch a scomparsa**: pulsante interattivo nell'HUD per far apparire lo schermo touch inferiore solo quando serve interagire con i menu di gioco (mouse cliccabile).

---

### 2. Orientamento Telecamera Verticale (Formato Carta TCG)
- [ ] **Box video verticale (Portrait)**: visualizzatore della webcam ridisegnato con rapporto verticale (circa 2.5 : 3.5, proporzioni reali delle carte Pokémon).
- [ ] **Sagoma di mira verticale**: mirino interno proporzionato esattamente al rettangolo di una carta fisica reale.

---

### 3. Helper Intelligente e Feedback di Scansione
- [ ] **Indicatore di attività visivo**: animazione laser/linea di scansione che scorre sulla carta per mostrare che l'analisi è in corso.
- [ ] **Rilevamento dimensioni e posizione in tempo reale** (OpenCV):
  - [ ] Messaggio: *«Avvicina la carta»* (se la carta è troppo lontana o piccola).
  - [ ] Messaggio: *«Allontana la carta»* (se la carta è troppo vicina o esce dal mirino).
  - [ ] Messaggio: *«Sposta a destra»* / *«Sposta a sinistra»* / *«Centra la carta»* (se è disallineata).
  - [ ] Messaggio: *«Carta agganciata! Lettura in corso...»* con cambio colore mirino in verde fluorescente quando la posizione è perfetta.

---

### 4. Gestione Telecamera On-Demand (Standby di Default)
- [ ] **Telecamera spenta all'avvio**: nessun flusso video attivo in background per privacy e risparmio risorse.
- [ ] **Schermata di Standby**: visualizzatore spento con icona e pulsante centrale: *«Avvia Scansione Pokémon»*.
- [ ] **Accensione hardware su richiesta**: la telecamera si attiva solo quando l'utente clicca il pulsante.
- [ ] **Pulsante di spegnimento e auto-stop**: possibilità di spegnere la telecamera manualmente con *«Ferma Scansione»* o spegnimento automatico al riscatto della carta.

---

### 5. Regole TCG e Gestione Salvataggi (Già collaudati e protetti)
- [x] **Salvataggio sul profilo dell'account**: iniezione nel file personale (`saves/profiles/<username>/save.sav`).
- [x] **Regole Tier (1–6)**: scala IV al 31 (0 per Tier 1–2, 1 per Tier 3 e Baby Shiny, 2 per Tier 4, 3 per Tier 5, 4 per Tier 6).
- [x] **7 Ere Storiche & 7 Gradi Pokéball**: sfere esclusive dal 1999 al 2026.
- [x] **Nerf Leggendari**: Lv. 5 sigillato, crescita lenta.
- [x] **Double Shiny**: Square Shiny (XOR = 0) + Fiocco + IV extra.
- [x] **Anti-Duplicazione**: chiave univoca `Specie + Set + Numero + Finitura`.
- [x] **Gen 1–5 in Squadra/PC, Gen 6–9 nel Raccoglitore Virtuale**.
