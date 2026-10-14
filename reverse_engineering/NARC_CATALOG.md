# 📁 Catalogo ragionato dei NARC: Pokémon Bianco 2

Gli archivi **NARC** (*Nintendo ARChive*) contengono la totalità dei dati di gioco di Pokémon Bianco 2 (testi, script, mappe, modelli 3D, statistiche e audio).

Questo documento serve come guida di riferimento rapida per identificare dove si trovano i dati e come sono strutturati.

---

## 📦 Struttura di un Archivio NARC

Un file NARC è suddiviso in 3 sezioni binarie:
1. **`BTAF`** (File Allocation Table): Tabella degli offset di inizio e fine per ciascun file interno.
2. **`BTNF`** (File Name Table): Tabella opzionale dei nomi dei file interni (spesso assente o vuota nei NARC di Game Freak).
3. **`GMIF`** (Image File): I dati grezzi veri e propri dei file concatenati.

Il tool [`narc_tool.py`](narc_tool.py) gestisce automaticamente queste sezioni per estrarre o ispezionare i file.

---

## 🗂️ Mappa dei NARC Principali di Bianco 2

All'interno del percorso `/a/` della ROM si trovano 308 archivi numerati (`a/X/Y/Z`). I più importanti sono:

### 1. Testi e Dialoghi
| Percorso | Descrizione | Note |
| :--- | :--- | :--- |
| `a/0/0/2` | **Banchi di Messaggi di Testo** (495 file) | Nomi Pokémon, descrizioni strumenti, dialoghi overworld, nomi allenatori, mosse e abilità |
| `a/0/0/3` | Testi di Sistema e UI | Stringhe di configurazione, Wi-Fi e messaggi del sistema |

### 2. Dati dei Pokémon (Gen 5)
| Percorso | Descrizione | Note |
| :--- | :--- | :--- |
| **`a/0/1/6`** | **Statistiche Base dei Pokémon** (710 file) | **76 byte per Pokémon** (tutti i 649 Pokémon + forme alternative di Kyurem, Therian, Deoxys, Rotom, ecc.) |
| `a/0/1/7` | Tabelle di Evoluzione | Condizioni di evoluzione (livello, pietra, felicità, scambio) |
| `a/0/1/8` | Mosse apprese per livello (Learnsets) | Elenco mosse e livelli di apprendimento |
| `a/0/1/9` | Mosse Uovo (Egg Moves) | Mosse ereditabili tramite accoppiamento |
| `a/0/2/0` | Compatibilità MT/MN (Tutor Moves) | Flag a bit per le mosse insegnabili |

#### 🔬 Struttura del Record di Statistiche (76 Byte in `a/0/1/6`):
```text
Offset (Byte) | Dimensione | Campo
0x00          | 1 byte     | HP Base
0x01          | 1 byte     | Attacco Base
0x02          | 1 byte     | Difesa Base
0x03          | 1 byte     | Velocità Base
0x04          | 1 byte     | Attacco Speciale Base
0x05          | 1 byte     | Difesa Speciale Base
0x06          | 1 byte     | Tipo 1 (0=Normale, 1=Lotta, 2=Volante, 3=Veleno...)
0x07          | 1 byte     | Tipo 2
0x08          | 1 byte     | Catch Rate (Tasso di cattura: 3..255)
0x09 - 0x0A   | 2 byte     | Base EXP Yield
0x0B - 0x0C   | 2 byte     | EV Yields (2 bit per statistica)
0x0D - 0x10   | 4 byte     | Strumenti tenuti selvatici (50%, 5%, 1%)
0x11          | 1 byte     | Rapporto di genere (Gender ratio)
0x12          | 1 byte     | Cicli uovo (Egg hatch cycles)
0x13          | 1 byte     | Felicità base (Base Friendship)
0x14          | 1 byte     | Curva di crescita ESP (Fattore crescita)
0x15          | 1 byte     | Gruppo uovo 1
0x16          | 1 byte     | Gruppo uovo 2
0x17          | 1 byte     | Abilità 1
0x18          | 1 byte     | Abilità 2
0x19          | 1 byte     | Abilità Speciale / Nascosta (Dream World)
0x1A          | 1 byte     | Fuga / Parametro Run
0x1B - 0x1E   | 4 byte     | Informazioni di forma e colore Pokédex
...           | ...        | Parametri 3D e altezza/peso
```

### 3. Mappe e Overworld
| Percorso | Descrizione | Note |
| :--- | :--- | :--- |
| `a/0/0/8` | Matrici delle Mappe | Collegamenti dei blocchi per città e percorsi |
| `a/0/1/2` | Header delle Mappe | ID musica, meteo, tipo di mappa, script collegato |
| `a/0/0/6` | Blocchi di Movimento / Permessi | Muri, acqua, erba alta, collisioni |
| `a/0/0/7` | Modelli 3D degli Edifici e Terreni | Geometrie 3D caricate dalla scheda grafica DS |
| `a/0/5/6` | **Script degli Eventi Overworld** | Comandi di gioco eseguiti da NPC, porte, cartelli e trigger |

### 4. Allenatori e Lotte
| Percorso | Descrizione | Note |
| :--- | :--- | :--- |
| `a/0/9/1` | Dati Allenatori | Classe allenatore, IA, oggetti utilizzati, frase di vittoria |
| `a/0/9/2` | Squadre degli Allenatori | Livelli, IV, mosse e Pokémon usati da ogni allenatore |

### 5. Grafica, Icone e Audio
| Percorso | Descrizione | Note |
| :--- | :--- | :--- |
| `a/0/0/4` | Sprite Pokémon animati | Sprite fronte/retro della Gen 5 con frame d'animazione |
| `a/0/6/8` | Icone Pokémon del Box PC | Mini-icone usate nell'interfaccia utente |
| `swan_sound_data.sdat` | Audio Bank Generale (SDAT) | Tutte le colonne sonore, effetti sonori (SFX) e versi dei Pokémon |

---

## 🛠️ Come Utilizzare questi Dati nel Progetto

Per estrarre ed analizzare uno di questi archivi basta usare lo script in dotazione:

```bash
# Esempio: Estrai le statistiche Pokémon in una cartella
./reverse_engineering/run-narc.sh "a/0/1/6" -x ./dati_pokemon

# Esempio: Ispeziona gli script overworld
./reverse_engineering/run-narc.sh "a/0/5/6"
```
