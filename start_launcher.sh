#!/usr/bin/env bash
# ==============================================================================
# Pokémon TCG Adventure — Linux Launcher Script
# Compatible with: Arch Linux, Hyprland, Ubuntu, Debian, Fedora, openSUSE
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "⚡ Starting Pokémon TCG Adventure — Linux Launcher"
echo "=================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed on your system."
    echo "👉 Install Python 3 using your package manager (e.g., sudo pacman -S python or sudo apt install python3 python3-venv)"
    exit 1
fi

# Detect or create virtual environment
VENV_PATH="$SCRIPT_DIR/scanner/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "📦 Creating virtual environment in $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
    "$VENV_PATH/bin/pip" install --upgrade pip
    echo "📥 Installing required dependencies from requirements.txt..."
    "$VENV_PATH/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Launch application
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
"$VENV_PATH/bin/python3" "$SCRIPT_DIR/launcher/launcher_window.py" "$@"
