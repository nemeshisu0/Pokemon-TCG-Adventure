#!/usr/bin/env bash
# Avvio del Launcher Desktop Ufficiale per Pokémon TCG Adventure

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${PROJECT_DIR}/scanner/.venv/bin/python"
LAUNCHER_SCRIPT="${PROJECT_DIR}/launcher/launcher_window.py"

if [ ! -f "${VENV_PYTHON}" ]; then
    echo "❌ Errore: Ambiente virtuale non trovato in ${PROJECT_DIR}/scanner/.venv"
    exit 1
fi

export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

exec "${VENV_PYTHON}" "${LAUNCHER_SCRIPT}" "$@"
