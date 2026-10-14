#!/usr/bin/env bash
# Script per avviare Frost's Gen 5 Editor su Linux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EDITOR_DIR="${SCRIPT_DIR}/FrostsGen5Editor"
EXE_PATH="${EDITOR_DIR}/FrostsGen5Editor.exe"

# Directory per prefix dedicato per l'editor
WINE_PFX="${EDITOR_DIR}/.wine_prefix"
mkdir -p "${WINE_PFX}"

if [ ! -f "${EXE_PATH}" ]; then
    echo "❌ Errore: FrostsGen5Editor.exe non trovato in ${EDITOR_DIR}"
    exit 1
fi

cd "${EDITOR_DIR}" || exit 1

# Percorsi Proton/Wine trovati nel sistema
GE_PROTON_WINE="/home/nemesy/.local/share/Steam/compatibilitytools.d/GE-Proton11-6-x86_64/files/bin/wine"

if [ -x "${GE_PROTON_WINE}" ]; then
    echo "==> Avvio Frost's Gen 5 Editor tramite GE-Proton (Wine 11 + Mono integrato)..."
    WINEPREFIX="${WINE_PFX}" WINEDEBUG=-all exec "${GE_PROTON_WINE}" "${EXE_PATH}" "$@"
elif command -v mono >/dev/null 2>&1; then
    echo "==> Avvio Frost's Gen 5 Editor tramite Mono di sistema..."
    MONO_IOMAP=all exec mono FrostsGen5Editor.exe "$@"
elif command -v wine >/dev/null 2>&1; then
    echo "==> Avvio Frost's Gen 5 Editor tramite Wine di sistema..."
    exec wine FrostsGen5Editor.exe "$@"
else
    echo "❌ Nessun runtime trovato. Installa mono con: sudo pacman -S mono"
    exit 1
fi
