#!/usr/bin/env bash
# Script per avviare Spiky's DS Map Editor (SDSME) su Linux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDSME_DIR="${SCRIPT_DIR}/SDSME"
EXE_PATH="${SDSME_DIR}/SDSME.exe"

# Directory per prefix dedicato
WINE_PFX="${SDSME_DIR}/.wine_prefix"
mkdir -p "${WINE_PFX}"

if [ ! -f "${EXE_PATH}" ]; then
    echo "❌ Errore: SDSME.exe non trovato in ${SDSME_DIR}"
    exit 1
fi

cd "${SDSME_DIR}" || exit 1

# Percorsi Proton/Wine trovati nel sistema
GE_PROTON_WINE="/home/nemesy/.local/share/Steam/compatibilitytools.d/GE-Proton11-6-x86_64/files/bin/wine"

if [ -x "${GE_PROTON_WINE}" ]; then
    echo "==> Avvio SDSME tramite GE-Proton (Wine 11 + Mono integrato)..."
    WINEPREFIX="${WINE_PFX}" WINEDEBUG=-all exec "${GE_PROTON_WINE}" "${EXE_PATH}" "$@"
elif command -v mono >/dev/null 2>&1; then
    echo "==> Avvio SDSME tramite Mono di sistema..."
    MONO_IOMAP=all exec mono SDSME.exe "$@"
elif command -v wine >/dev/null 2>&1; then
    echo "==> Avvio SDSME tramite Wine di sistema..."
    exec wine SDSME.exe "$@"
else
    echo "❌ Nessun runtime trovato. Installa mono o wine."
    exit 1
fi
