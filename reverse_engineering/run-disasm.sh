#!/bin/bash
# Wrapper rapido per disassemblare codice ARM9 / Overlays con capstone
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$PROJECT_DIR/scanner/.venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$PROJECT_DIR/reverse_engineering/disasm.py" "$@"
