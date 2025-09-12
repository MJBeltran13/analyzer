#!/bin/bash
# Create desktop shortcut for Modern Antenna Analyzer on Raspberry Pi
# Run with: bash create_desktop_shortcut.sh

echo "🚀 Creating desktop shortcut for Modern Antenna Analyzer"
echo "======================================================"

# Get the current directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Resolve the Desktop directory using xdg-user-dir if available (handles localized desktops)
if command -v xdg-user-dir >/dev/null 2>&1; then
    DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
else
    DESKTOP_DIR="$HOME/Desktop"
fi
mkdir -p "$DESKTOP_DIR"
SHORTCUT_NAME="Antenna Analyzer.desktop"

# Create launcher script
echo "📝 Creating launcher script..."
cat > "$CURRENT_DIR/launch_analyzer.sh" << 'EOF'
#!/bin/bash
# Launcher script for Modern Antenna Analyzer
set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/analyzer_env"

echo "🐍 Ensuring Python virtual environment..."
# If currently inside another venv, deactivate to avoid confusion
if [ -n "${VIRTUAL_ENV:-}" ]; then
    deactivate 2>/dev/null || true
fi
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR"
    # Ensure venv module is available; try to install if not
    if ! python3 - <<'PY'
import sys
import importlib
sys.exit(0 if importlib.util.find_spec('venv') else 1)
PY
    then
        echo "python3 venv module missing. Attempting to install python3-venv (sudo required)."
        if command -v sudo >/dev/null 2>&1; then
            sudo apt update || true
            sudo apt install -y python3-venv || true
        fi
    fi
    python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    python3 -m venv "$VENV_DIR" || { echo "Failed to create venv at $VENV_DIR."; echo "Install with: sudo apt install -y python3-venv"; read -p "Press Enter to exit..."; exit 1; }
fi

# If the venv looks broken, recreate it
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Venv activation script missing at $VENV_DIR/bin/activate. Recreating venv..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR" || { echo "Failed to recreate venv at $VENV_DIR."; echo "Install with: sudo apt install -y python3-venv"; read -p "Press Enter to exit..."; exit 1; }
fi
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true

echo "🔍 Checking Python dependencies..."
python - <<'PY' || DEP_ERR=$?
import importlib
modules = [
    ("board", "adafruit-blinka"),
    ("adafruit_ads1x15", "adafruit-circuitpython-ads1x15"),
    ("smbus2", "smbus2"),
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib"),
]
missing = []
for mod, pkg in modules:
    try:
        importlib.import_module(mod)
    except Exception:
        missing.append(pkg)
if missing:
    print("Installing:", missing)
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
PY
if [ "${DEP_ERR:-0}" -ne 0 ]; then
    echo "⚠️  Dependency check failed. Attempting installation from requirements files if available..."
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip install -r "$SCRIPT_DIR/requirements.txt" || true
    fi
    if [ -f "$SCRIPT_DIR/requirements_rpi.txt" ]; then
        pip install -r "$SCRIPT_DIR/requirements_rpi.txt" || true
    fi
fi

if [ ! -f "$SCRIPT_DIR/analyzer.py" ]; then
    echo "❌ Error: analyzer.py not found in $SCRIPT_DIR"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "🚀 Starting Modern Antenna Analyzer..."
exec python "$SCRIPT_DIR/analyzer.py"
EOF

# Make launcher script executable
chmod +x "$CURRENT_DIR/launch_analyzer.sh"

# Create desktop shortcut
echo "🖥️  Creating desktop shortcut..."
cat > "$DESKTOP_DIR/$SHORTCUT_NAME" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Antenna Analyzer
Comment=Modern Antenna Analyzer with ADS1115
Exec=$CURRENT_DIR/launch_analyzer.sh
Path=$CURRENT_DIR
Icon=applications-electronics
Terminal=true
StartupNotify=true
Categories=Electronics;Engineering;Science;
Keywords=antenna;analyzer;ham;radio;electronics;
EOF

# Make desktop file executable
chmod +x "$DESKTOP_DIR/$SHORTCUT_NAME"

echo ""
echo "✅ Desktop shortcut created successfully!"
echo "📍 Location: $DESKTOP_DIR/$SHORTCUT_NAME"
echo ""
echo "🎯 You can now:"
echo "   • Double-click the 'Antenna Analyzer' icon on your desktop"
echo "   • Or run: $CURRENT_DIR/launch_analyzer.sh"
echo ""
echo "📋 Notes:"
echo "   • The launcher now creates/uses a local virtual environment automatically"
echo "   • Dependencies install inside the venv to avoid PEP 668 issues"
echo "   • The terminal will stay open to show any error messages"
echo ""
