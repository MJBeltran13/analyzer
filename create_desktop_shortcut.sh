#!/bin/bash
# Create desktop shortcut for Modern Antenna Analyzer on Raspberry Pi
# Run with: bash create_desktop_shortcut.sh

echo "🚀 Creating desktop shortcut for Modern Antenna Analyzer"
echo "======================================================"

# Get the current directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$HOME/Desktop"
SHORTCUT_NAME="Antenna Analyzer.desktop"

# Create launcher script
echo "📝 Creating launcher script..."
cat > "$CURRENT_DIR/launch_analyzer.sh" << 'EOF'
#!/bin/bash
# Launcher script for Modern Antenna Analyzer

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the analyzer directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "analyzer_env" ]; then
    echo "🐍 Activating virtual environment..."
    source analyzer_env/bin/activate
else
    echo "⚠️  Virtual environment not found. Using system Python..."
    echo "   Consider running setup_raspberry_pi.sh first"
fi

# Check if analyzer.py exists
if [ ! -f "analyzer.py" ]; then
    echo "❌ Error: analyzer.py not found in $SCRIPT_DIR"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
python3 -c "import RPi.GPIO, board, busio, adafruit_ads1x15, numpy, matplotlib, tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Some dependencies are missing. Installing..."
    if [ -f "requirements_rpi.txt" ]; then
        pip3 install -r requirements_rpi.txt
    else
        echo "❌ requirements_rpi.txt not found"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Run the analyzer
echo "🚀 Starting Modern Antenna Analyzer..."
python3 analyzer.py

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Application exited with an error"
    read -p "Press Enter to exit..."
fi
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
echo "   • The shortcut will automatically activate the virtual environment if it exists"
echo "   • If dependencies are missing, it will try to install them"
echo "   • The terminal will stay open to show any error messages"
echo ""
