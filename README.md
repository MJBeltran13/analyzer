# Modern Antenna Analyzer - ADS1115 Hardware

A professional-grade antenna analyzer with real ADS1115 16-bit ADC hardware support, featuring a beautiful modern UI inspired by shadcn design principles.

## 🚀 Features

- **🔌 Real Hardware**: ADS1115 16-bit I2C ADC for accurate measurements
- **📡 Professional Analysis**: Real-time SWR calculations and antenna performance rating
- **🎨 Modern UI**: Beautiful dark/light theme with responsive design
- **📊 Interactive Plots**: Real-time SWR vs frequency visualization
- **💾 Data Management**: Save, load, and analyze test results
- **📱 Responsive Design**: Optimized for both desktop and small screens
- **🔍 Hardware Diagnostics**: Built-in I2C scanning and ADC testing

## 🛠️ Hardware Requirements

- **Raspberry Pi** (3B+, 4B, or newer recommended)
- **ADS1115 16-bit ADC** module (I2C interface)
- **AD9850 DDS** module for frequency generation
- **Connecting wires** (SDA, SCL, 3.3V, GND)

## 🔌 Pin Connections

### ADS1115 (I2C ADC)
| ADS1115 Pin | Raspberry Pi Pin | Description |
|-------------|------------------|-------------|
| VDD         | 3.3V            | Power supply |
| GND         | GND             | Ground       |
| SCL         | GPIO 3 (SCL)    | I2C Clock    |
| SDA         | GPIO 2 (SDA)    | I2C Data     |
| ADDR        | GND             | I2C Address (0x48) |

### AD9850 (DDS)
| AD9850 Pin | Raspberry Pi Pin | Description |
|------------|------------------|-------------|
| VCC        | 3.3V            | Power supply |
| GND        | GND             | Ground       |
| W_CLK      | GPIO 12         | Word clock   |
| FQ_UD      | GPIO 16         | Frequency update |
| DATA       | GPIO 20         | Data line    |
| RESET      | GPIO 21         | Reset        |

## 🚀 Quick Start

### 1. Automated Setup (Recommended)

```bash
# Make setup script executable
chmod +x setup_raspberry_pi.sh

# Run setup script
bash setup_raspberry_pi.sh
```

### 2. Manual Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-dev python3-venv i2c-tools python3-smbus

# Enable I2C
echo "i2c_arm=on" | sudo tee -a /boot/config.txt
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt

# Create virtual environment
python3 -m venv analyzer_env
source analyzer_env/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements_rpi.txt

# Reboot for I2C changes
sudo reboot
```

## 🧪 Testing

### 1. Verify I2C Bus

```bash
# Check if I2C is enabled
i2cdetect -y 1
```

You should see your ADS1115 at address 0x48.

### 2. Test ADS1115

```bash
# Activate environment
source analyzer_env/bin/activate

# Test ADS1115 functionality
python3 test_ads1115.py
```

### 3. Run Analyzer

```bash
# Activate environment
source analyzer_env/bin/activate

# Run main analyzer
python3 analyzer.py
```

## 📊 Performance Specifications

- **ADC Resolution**: 16-bit (65,536 levels)
- **Voltage Range**: ±4.096V (configurable)
- **Data Rate**: 860 samples per second
- **Accuracy**: ±0.01% typical
- **Temperature Drift**: ±0.0005% per °C
- **Frequency Range**: 1 Hz - 40 MHz (AD9850 dependent)

## 🎯 Usage

### Basic Testing

1. **Set Parameters**:
   - Start Frequency (MHz): Beginning of frequency range
   - Stop Frequency (MHz): End of frequency range
   - Measurement Points: Number of measurements (10-1000)

2. **Run Tests**:
   - **SWEEP**: Run custom frequency sweep
   - **Quick Test**: Run predefined test (10-20 MHz, 25 points)

3. **View Results**:
   - Real-time SWR measurements
   - Performance rating (A+ to F)
   - Detailed analysis and recommendations
   - Interactive SWR plot

### Advanced Features

- **Real-time Monitoring**: Live voltage readings from ADS1115
- **Data Export**: Save results to JSON format
- **History Management**: Load and compare previous tests
- **Hardware Diagnostics**: Built-in troubleshooting tools

## 🔧 Troubleshooting

### No I2C Devices Found

1. **Check connections**: Ensure SDA and SCL are properly connected
2. **Check power**: Verify 3.3V and GND connections
3. **Enable I2C**: Make sure I2C is enabled in `/boot/config.txt`
4. **Reboot**: I2C changes require a reboot

### ADS1115 Not Responding

1. **Check address**: Default address is 0x48
2. **Check pull-up resistors**: I2C needs pull-up resistors
3. **Check voltage levels**: Ensure 3.3V operation
4. **Check wiring**: Verify no loose connections

### Permission Errors

```bash
# Add user to i2c group
sudo usermod -a -G i2c $USER

# Log out and back in, or reboot
```

## 📁 File Structure

```
analyzer/
├── analyzer.py              # Main analyzer application
├── test_ads1115.py         # ADS1115 test script
├── requirements_rpi.txt     # Raspberry Pi dependencies
├── setup_raspberry_pi.sh   # Automated setup script
├── README_ADS1115.md       # Detailed hardware guide
├── static/                 # UI assets
├── templates/              # HTML templates
└── web_analyzer.py         # Web interface (optional)
```

## 🌐 Web Interface

For web-based access, see `README_WEB.md` for the web interface setup.

## 📚 Dependencies

- **Hardware**: RPi.GPIO, adafruit-circuitpython-ads1x15
- **Data Processing**: numpy, matplotlib
- **GUI**: tkinter (built-in on Raspberry Pi)
- **Optional**: smbus2 for enhanced I2C performance

## 🤝 Contributing

This project is open source. Feel free to:
- Report bugs
- Suggest improvements
- Submit pull requests
- Share your modifications

## 📄 License

This project is open source. Use it for educational, personal, or commercial purposes.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run `test_ads1115.py` to verify hardware
3. Check I2C bus with `i2cdetect -y 1`
4. Verify all connections and power supply
5. Check the detailed guide in `README_ADS1115.md`

---

**Happy Antenna Testing! 🎯📡**
