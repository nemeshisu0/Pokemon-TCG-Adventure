<div align="center">

# 🎴 POKÉMON TCG ADVENTURE 🎮
### *The Next-Gen Bridge Between Physical Pokémon Cards & Gen 5 DS Adventures*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6%20Dark%20Glass-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![melonDS](https://img.shields.io/badge/Core-melonDS%20In--Process%2060FPS-FF3E00?style=for-the-badge&logo=nintendo-gamecube&logoColor=white)](http://melonds.kuribo64.net/)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV%20%2B%20OCR-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%2010%20%26%2011-0078D6?style=for-the-badge&logo=linux&logoColor=white)](#-installation--setup)
[![Language](https://img.shields.io/badge/i18n-English%20%7C%20Italiano-FFD700?style=for-the-badge)](file:///README.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

<br/>

**`#Pokemon`** &nbsp; **`#PokemonTCG`** &nbsp; **`#melonDS`** &nbsp; **`#PokeMMO`** &nbsp; **`#ComputerVision`** &nbsp; **`#PyQt6`** &nbsp; **`#ReverseEngineering`** &nbsp; **`#NintendoDS`** &nbsp; **`#ArchLinux`** &nbsp; **`#Windows`** &nbsp; **`#OpenCV`**

<br/>

**[🇬🇧 English Documentation](#-english-guide)** • **[🇮🇹 Guida in Italiano](#-guida-in-italiano)**

---

</div>

<br/>

# 🇬🇧 ENGLISH GUIDE

## 🌟 Overview
**Pokémon TCG Adventure** transforms real-life physical Pokémon trading cards into living, battle-ready in-game Pokémon inside **Pokémon White Version 2**. Featuring a modern, PokeMMO-inspired launcher, hardware-accelerated 60 FPS in-process DS emulation, and an interactive 6-stage Computer Vision scanner hub, this software bridges physical collecting and classic handheld gaming.

---

## ✨ Key Features
- ⚡ **Embedded 60 FPS melonDS Core**: Runs natively within the Qt6 window via ultra-low latency shared memory (`SharedMemory`) — no clunky external windows or popups.
- ✂️ **Seamless C-Gear Skip & Fast Boot**: Bypasses the Gen 5 C-Gear connection prompt and intro titles at memory level for instant gameplay.
- 📷 **Real-Time Optical TCG Scanner**: Automated 6-stage Computer Vision pipeline (Front, Back, Name, Number, Year, Artist) powered by OpenCV and Tesseract OCR.
- 🌈 **Holo & Finish Evaluation**: Accurately calculates IVs, Shininess, Nature, and movesets based on physical card edition (Standard, Holo, Reverse Holo).
- 📦 **Virtual Pokémon Box**: Offline desktop vault allowing trainers to deposit, withdraw, and inspect cards without losing save legality.
- 🌐 **Dynamic Multilingual Launcher**: English (Default) and Italian with instantaneous runtime language switching and settings persistence.
- 🎮 **Universal Controller & Remapping**: Native support for Xbox, PlayStation, generic USB gamepads, and full keyboard key-rebinding.

---

## 💻 Cross-Platform Installation

### 🐧 Linux (Arch Linux / Hyprland / Ubuntu / Debian / Fedora)

#### 1. System Requirements
- **Arch Linux**:
  ```bash
  sudo pacman -S python python-pip tesseract tesseract-data-eng tesseract-data-ita
  ```
- **Ubuntu / Debian**:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip python3-venv tesseract-ocr tesseract-ocr-eng tesseract-ocr-ita libgl1-mesa-glx
  ```
- **Fedora**:
  ```bash
  sudo dnf install python3 python3-pip tesseract tesseract-langpack-eng tesseract-langpack-ita mesa-libGL
  ```

#### 2. Quick Start
Clone the repository and run the automated launcher script:
```bash
git clone https://github.com/nemeshisu0/Pokemon-TCG-Adventure.git
cd Pokemon-TCG-Adventure
chmod +x start_launcher.sh
./start_launcher.sh
```
*The script will automatically configure your Python virtual environment and install all dependencies.*

---

### 🪟 Windows (Windows 10 & Windows 11 64-bit)

#### 1. System Requirements
- Install **Python 3.10+** from [python.org](https://www.python.org/) *(Make sure to check "Add Python to PATH" during installation)*.
- *(Optional for camera scanning)*: Install [Tesseract-OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki).

#### 2. Quick Start
1. Download or clone this repository:
   ```cmd
   git clone https://github.com/nemeshisu0/Pokemon-TCG-Adventure.git
   cd Pokemon-TCG-Adventure
   ```
2. Double-click **`start_launcher.bat`** (or run it in CMD/PowerShell):
   ```cmd
   start_launcher.bat
   ```
*The batch script initializes the Python virtual environment, installs the required packages, and boots the launcher.*

---

## 🕹️ Controls Configuration

| DS Action | Default Keyboard Key | Controller Button | Description |
|---|---|---|---|
| **A Button** | `N` or `Z` | Button A / ✕ | Confirm / Interaction |
| **B Button** | `B` or `X` | Button B / ◯ | Cancel / Running Shoes |
| **X Button** | `V` or `A` | Button X / ▢ | In-Game Menu |
| **Y Button** | `M` or `S` | Button Y / △ | Key Item / Bicycle |
| **D-Pad Up** | `Up Arrow` or `I` | D-Pad Up | Move Up |
| **D-Pad Down** | `Down Arrow` or `K` | D-Pad Down | Move Down |
| **D-Pad Left** | `Left Arrow` or `J` | D-Pad Left | Move Left |
| **D-Pad Right** | `Right Arrow` or `L` | D-Pad Right | Move Right |
| **Start** | `Enter` | Start / Options | Main Menu |
| **Select** | `Shift` | Select / Back | Secondary Action |
| **L Trigger** | `Q` | L1 / LB | Top Left Shoulder |
| **R Trigger** | `E` | R1 / RB | Top Right Shoulder |

*All controls can be customized inside the **`⚙ Settings`** menu.*

---

<br/>

---

# 🇮🇹 GUIDA IN ITALIANO

## 🌟 Panoramica
**Pokémon TCG Adventure** è un'infrastruttura completa che unisce il collezionismo delle carte fisiche Pokémon al mondo di gioco di **Pokémon Versione Bianca 2**. Con un'architettura grafica in stile PokeMMO, l'integrazione nativa del core melonDS a 60 FPS senza finestre esterne e uno scanner ottico intelligente in Computer Vision, puoi trasformare le tue carte reali in Pokémon da schierare in squadra.

---

## ✨ Funzionalità Principali
- ⚡ **Core melonDS Integrato a 60 FPS**: Renderizzato direttamente nella finestra Qt6 tramite memoria condivisa a bassissima latenza (`SharedMemory`), con stabilità assoluta.
- ✂️ **Taglio C-Gear & Salto Intro**: Avvio istantaneo con bypass del collegamento C-Gear e salto automatico delle schermate iniziali a livello di memoria RAM.
- 📷 **Scanner TCG Ottico Multistadio**: Pipeline guidata a 6 fasi (Fronte, Retro, Zoom Nome, Numero, Anno e Autore) con OCR e riconoscimento intelligente dei set.
- 🌈 **Valutazione Finiture & Holo**: Calcolo matematico di IV, natura, mosse e shiny rate in base alla rarità e alla finitura (Normale, Olografica, Reverse Holo).
- 📦 **Box Pokémon Virtuale**: Deposito desktop per gestire, archiviare e ritirare carte dalla squadra di gioco, con schiusa immediata delle uova.
- 🌐 **Interfaccia Bilingue Dinamica**: Cambio lingua immediato tra Inglese e Italiano dal menu Impostazioni con aggiornamento live dei testi.
- 🎮 **Supporto Controller Plug & Play**: Compatibilità nativa con controller Xbox, PlayStation, joypad generici USB e rimappatura tastiera.

---

## 💻 Installazione Multi-Piattaforma

### 🐧 Linux (Arch Linux / Hyprland / Ubuntu / Debian / Fedora)

#### 1. Dipendenze di Sistema
- **Arch Linux**:
  ```bash
  sudo pacman -S python python-pip tesseract tesseract-data-eng tesseract-data-ita
  ```
- **Ubuntu / Debian**:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip python3-venv tesseract-ocr tesseract-ocr-eng tesseract-ocr-ita libgl1-mesa-glx
  ```
- **Fedora**:
  ```bash
  sudo dnf install python3 python3-pip tesseract tesseract-langpack-eng tesseract-langpack-ita mesa-libGL
  ```

#### 2. Avvio Rapido
Clona il repository ed avvia lo script automatico:
```bash
git clone https://github.com/nemeshisu0/Pokemon-TCG-Adventure.git
cd Pokemon-TCG-Adventure
chmod +x start_launcher.sh
./start_launcher.sh
```
*Lo script configurerà automaticamente l'ambiente virtuale Python e installerà tutte le librerie.*

---

### 🪟 Windows (Windows 10 & Windows 11 a 64 bit)

#### 1. Requisiti di Sistema
- Installa **Python 3.10+** da [python.org](https://www.python.org/) *(assicurati di spuntare "Add Python to PATH" durante l'installazione)*.
- *(Opzionale per scansioni da webcam)*: Installa [Tesseract-OCR per Windows](https://github.com/UB-Mannheim/tesseract/wiki).

#### 2. Avvio Rapido
1. Scarica o clona il repository:
   ```cmd
   git clone https://github.com/nemeshisu0/Pokemon-TCG-Adventure.git
   cd Pokemon-TCG-Adventure
   ```
2. Fai doppio clic su **`start_launcher.bat`** (o avvialo da terminale CMD/PowerShell):
   ```cmd
   start_launcher.bat
   ```
*Lo script batch creerà l'ambiente virtuale, installerà i requisiti e avvierà il Launcher.*

---

## 📂 Struttura del Progetto

```
Pokemon-TCG-Adventure/
├── launcher/                  # Interfaccia grafica Desktop (PyQt6)
│   ├── core/                  # Core melonDS nativo & IPC Shared Memory
│   ├── i18n.py                # Sistema di localizzazione bilingue (EN / IT)
│   ├── launcher_window.py     # Finestra principale del launcher
│   ├── game_client.py         # Client di gioco HUD & TCG Scanner
│   ├── settings_dialog.py     # Gestione impostazioni, comandi e lingua
│   └── virtual_box_dialog.py  # Box Pokémon Virtuale desktop
├── scanner/                   # Motore Computer Vision & TCG Core
│   ├── card_scanner.py        # Pipeline di scansione con OpenCV
│   ├── injector.py            # Calcolo PK5 e iniezione nel salvataggio
│   └── knowledge_engine.py    # Database e riconoscimento carte
├── reverse_engineering/       # Mappature binarie ARM9 & Overlays
├── tools/                     # Utility di patch e automazione
├── start_launcher.sh          # Script di avvio per Linux
├── start_launcher.bat         # Script di avvio per Windows
└── requirements.txt           # Dipendenze Python multipiattaforma
```

---

## 📄 Note Legali / Legal Notice
*Pokémon, Pokémon TCG and Nintendo DS are trademarks of Nintendo, Creatures Inc., and GAME FREAK inc.*  
*This software is an open-source research and educational project. No copyrighted Nintendo ROM files are provided with this repository. Users must supply their own legitimate dump of Pokémon White 2.*

<div align="center">
  <sub>Crafted with passion for the Pokémon community.</sub>
</div>
