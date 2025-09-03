#!/bin/bash
# Setup script for Raspberry Pi with ADS1115
# Run with: bash setup_raspberry_pi.sh

echo "🚀 Setting up Raspberry Pi for ADS1115 Antenna Analyzer"
echo "=================================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "🔧 Installing required system packages..."
sudo apt install -y python3-pip python3-dev python3-venv
sudo apt install -y i2c-tools python3-smbus

# Enable I2C
echo "🔌 Enabling I2C interface..."
if ! grep -q "i2c_arm=on" /boot/config.txt; then
    echo "i2c_arm=on" | sudo tee -a /boot/config.txt
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
    echo "I2C enabled in /boot/config.txt"
else
    echo "I2C already enabled"
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv analyzer_env
source analyzer_env/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements_rpi.txt

# Test I2C
echo "🔍 Testing I2C bus..."
i2cdetect -y 1

echo ""
echo "✅ Setup completed!"
echo ""
echo "To run the analyzer:"
echo "1. Activate environment: source analyzer_env/bin/activate"
echo "2. Test ADS1115: python3 test_ads1115.py"
echo "3. Run analyzer: python3 analyzer.py"
echo ""
echo "Note: You may need to reboot for I2C changes to take effect"
