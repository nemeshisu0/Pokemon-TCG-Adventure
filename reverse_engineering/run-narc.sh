#!/bin/bash
# Wrapper rapido per ispezionare ed estrarre archivi NARC dalla ROM
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$PROJECT_DIR/scanner/.venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$PROJECT_DIR/reverse_engineering/narc_tool.py" "$@"
