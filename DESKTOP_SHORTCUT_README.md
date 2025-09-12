# Desktop Shortcut Setup for Raspberry Pi

This guide explains how to create a desktop shortcut for the Modern Antenna Analyzer on Raspberry Pi.

## Quick Setup

1. **Run the setup script:**
   ```bash
   bash create_desktop_shortcut.sh
   ```

2. **That's it!** You'll now have a "Antenna Analyzer" icon on your desktop.

## What the Script Does

The `create_desktop_shortcut.sh` script:

1. **Creates a launcher script** (`launch_analyzer.sh`) that:
   - Automatically activates the virtual environment (if it exists)
   - Checks for missing dependencies and installs them
   - Runs the analyzer with proper error handling
   - Keeps the terminal open if there are errors

2. **Creates a desktop shortcut** (`.desktop` file) that:
   - Appears as "Antenna Analyzer" on your desktop
   - Uses an electronics icon
   - Opens in a terminal window
   - Is categorized under Electronics/Engineering

## Manual Setup (Alternative)

If you prefer to create the shortcut manually:

### Step 1: Create the launcher script
```bash
# Create launch_analyzer.sh with the content from the script above
chmod +x launch_analyzer.sh
```

### Step 2: Create the desktop file
```bash
# Create ~/Desktop/Antenna Analyzer.desktop
cat > ~/Desktop/Antenna\ Analyzer.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Antenna Analyzer
Comment=Modern Antenna Analyzer with ADS1115
Exec=/path/to/your/analyzer/launch_analyzer.sh
Icon=applications-electronics
Terminal=true
StartupNotify=true
Categories=Electronics;Engineering;Science;
Keywords=antenna;analyzer;ham;radio;electronics;
EOF

chmod +x ~/Desktop/Antenna\ Analyzer.desktop
```

## Troubleshooting

### Shortcut doesn't appear on desktop
- Make sure the `.desktop` file is executable: `chmod +x ~/Desktop/Antenna\ Analyzer.desktop`
- Check if your desktop environment supports `.desktop` files
- Try refreshing the desktop or logging out/in

### Application won't start
- Make sure you've run `setup_raspberry_pi.sh` first
- Check that the virtual environment exists: `ls -la analyzer_env/`
- Verify Python dependencies: `python3 -c "import RPi.GPIO, board, busio"`

### Permission errors
- Make sure the launcher script is executable: `chmod +x launch_analyzer.sh`
- Check file ownership: `ls -la launch_analyzer.sh`

## File Structure After Setup

```
analyzer/
├── analyzer.py                    # Main application
├── create_desktop_shortcut.sh     # Setup script
├── launch_analyzer.sh            # Launcher script (created by setup)
├── setup_raspberry_pi.sh         # Initial Pi setup
├── requirements_rpi.txt          # Python dependencies
└── analyzer_env/                 # Virtual environment (if created)

~/Desktop/
└── Antenna Analyzer.desktop      # Desktop shortcut (created by setup)
```

## Usage

Once set up, simply double-click the "Antenna Analyzer" icon on your desktop to run the application. The launcher will handle all the setup automatically.
