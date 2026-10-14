# CHECKLIST UFFICIALE: POKÉMON TCG ADVENTURE CLIENT

### 1. Architettura a Finestra Unica (Emulatore Incorporato)
- [x] **Eliminazione finestra esterna staccata**: niente finestra separata di melonDS sul desktop o affiancata da Hyprland.
- [x] **Embedding diretto**: il core C++ di melonDS (`melonds_core.so`) gira direttamente in-process dentro la nostra applicazione PyQt6.
- [x] **Layout a schermo singolo**: visualizzazione primaria dello schermo superiore DS in alta definizione scalabile.
- [x] **Schermo Touch a scomparsa**: pulsante interattivo nell'HUD per far apparire lo schermo touch inferiore solo quando serve interagire con i menu di gioco (mouse cliccabile).

---

### 2. Orientamento Telecamera Verticale (Formato Carta TCG)
- [x] **Box video verticale (Portrait)**: visualizzatore della webcam ridisegnato con rapporto verticale (circa 2.5 : 3.5, proporzioni reali delle carte Pokémon).
- [x] **Sagoma di mira verticale**: mirino interno proporzionato esattamente al rettangolo di una carta fisica reale.

---

### 3. Helper Intelligente e Feedback di Scansione
- [x] **Indicatore di attività visivo e Fasi Guidate**: sequenza a 6 fasi ([1/6] Fronte -> [2/6] Retro -> [3/6] Zoom Nome -> [4/6] Zoom Numero -> [5/6] Zoom Anno -> [6/6] Zoom Autore).
- [x] **Rilevamento dimensioni e posizione in tempo reale** (OpenCV):
  - [x] Messaggio: *«Avvicina la carta»* (se la carta è troppo lontana o piccola).
  - [x] Messaggio: *«Allontana la carta»* (se la carta è troppo vicina o esce dal mirino).
  - [x] Messaggio: *«Centra la carta»* / *«Allinea al riquadro»* / *«Gira la carta»*.
  - [x] Messaggio: *«OTTIMO!»* con mirino verde fluorescente solo quando allineata stabilmente.
  - [x] Controllo cromatico rigido anti-falso-verde: verifica del bordo blu perimetrale e verifica che la carta sia stata fisicamente voltata.
- [x] **Knowledge Engine Distribuito & Apprendimento Attivo** (`database/card_knowledge.json`):
  - [x] **Motore Visuale Ibrido stile Google Lens (SIFT Feature Matching)**: confronto fotografico invariante per scala/rotazione/luminosità dell'artwork contro il catalogo ufficiale (150+ match chiave).
  - [x] Supporto multilingua completo (PS italiano, PV francese, KP tedesco, HP inglese) e gestione tollerante delle abbreviazioni degli autori (`Ill.`, `Illus.`).
  - [x] Bot di matching visivo e OCR multi-filtro con archiviazione persistente delle foto in `scanner/captures/`.
  - [x] Memoria condivisa distribuibile nel gioco per il riconoscimento istantaneo da parte di tutti i giocatori.

---

### 4. Gestione Telecamera On-Demand (Standby di Default)
- [x] **Telecamera spenta all'avvio**: nessun flusso video attivo in background per privacy e risparmio risorse.
- [x] **Schermata di Standby**: visualizzatore spento con icona e pulsante: *«Avvia Fotocamera»*.
- [x] **Accensione hardware su richiesta**: la telecamera si attiva solo quando l'utente clicca il pulsante.
- [x] **Pulsante di spegnimento e auto-stop**: possibilità di spegnere la telecamera manualmente con *«Ferma Fotocamera»* o spegnimento automatico al riscatto della carta.

---

### 5. Regole TCG e Gestione Salvataggi (Già collaudati e protetti)
- [x] **Salvataggio sul profilo dell'account**: iniezione nel file personale (`saves/profiles/<username>/save.sav`).
- [x] **Regole Tier (1–6)**: scala IV al 31 (0 per Tier 1–2, 1 per Tier 3 e Baby Shiny, 2 per Tier 4, 3 per Tier 5, 4 per Tier 6).
- [x] **7 Ere Storiche & 7 Gradi Pokéball**: sfere esclusive dal 1999 al 2026.
- [x] **Nerf Leggendari**: Lv. 5 sigillato, crescita lenta.
- [x] **Double Shiny**: Square Shiny (XOR = 0) + Fiocco + IV extra.
- [x] **Anti-Duplicazione**: chiave univoca `Specie + Set + Numero + Finitura`.
- [x] **Gen 1–5 in Squadra/PC, Gen 6–9 nel Raccoglitore Virtuale**.
