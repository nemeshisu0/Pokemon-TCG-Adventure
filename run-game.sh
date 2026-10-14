#!/usr/bin/env bash
# Script rapido per avviare Pokémon Bianco 2 con melonDS su PC

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Se esiste una versione modificata, avvia quella, altrimenti quella originale
if [ -f "${PROJECT_DIR}/roms/modified/Bianco 2.nds" ]; then
    ROM_PATH="${PROJECT_DIR}/roms/modified/Bianco 2.nds"
    echo "==> [melonDS] Avvio versione MODIFICATA: ${ROM_PATH}"
else
    ROM_PATH="${PROJECT_DIR}/roms/original/Bianco 2.nds"
    echo "==> [melonDS] Avvio versione ORIGINALE: ${ROM_PATH}"
fi

exec /usr/bin/melonDS "${ROM_PATH}" "$@"
