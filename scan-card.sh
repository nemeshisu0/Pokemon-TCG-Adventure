#!/usr/bin/env bash
# Script rapido per avviare il Card Scanner & Injection Engine di Pokémon TCG

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${PROJECT_DIR}/scanner/.venv/bin/python"
CLI_SCRIPT="${PROJECT_DIR}/scanner/scan_cli.py"

if [ ! -f "${VENV_PYTHON}" ]; then
    echo "❌ Errore: Ambiente virtuale non trovato in ${PROJECT_DIR}/scanner/.venv"
    exit 1
fi

export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# Se viene passato --webcam, avvia lo scanner OCR da videocamera
if [ "$1" == "--webcam" ]; then
    shift
    exec "${VENV_PYTHON}" "${PROJECT_DIR}/scanner/card_scanner.py" "$@"
else
    exec "${VENV_PYTHON}" "${CLI_SCRIPT}" "$@"
fi
