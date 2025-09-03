# ADS1115 Antenna Analyzer - Hardware Setup

This guide will help you set up the antenna analyzer with a real ADS1115 ADC instead of mock data.

## Hardware Requirements

- **Raspberry Pi** (3B+, 4B, or newer recommended)
- **ADS1115 16-bit ADC** module
- **AD9850 DDS** module for frequency generation
- **Connecting wires** (SDA, SCL, 3.3V, GND)

## ADS1115 Pin Connections

Connect your ADS1115 to the Raspberry Pi as follows:

| ADS1115 Pin | Raspberry Pi Pin | Description |
|-------------|------------------|-------------|
| VDD         | 3.3V            | Power supply |
| GND         | GND             | Ground       |
| SCL         | GPIO 3 (SCL)    | I2C Clock    |
| SDA         | GPIO 2 (SDA)    | I2C Data     |
| ADDR        | GND             | I2C Address (0x48) |

## AD9850 DDS Pin Connections

| AD9850 Pin | Raspberry Pi Pin | Description |
|------------|------------------|-------------|
| VCC        | 3.3V            | Power supply |
| GND        | GND             | Ground       |
| W_CLK      | GPIO 12         | Word clock   |
| FQ_UD      | GPIO 16         | Frequency update |
| DATA       | GPIO 20         | Data line    |
| RESET      | GPIO 21         | Reset        |

## Installation

### 1. Quick Setup (Recommended)

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

# Enable I2C in /boot/config.txt
echo "i2c_arm=on" | sudo tee -a /boot/config.txt
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt

# Create virtual environment
python3 -m venv analyzer_env
source analyzer_env/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements_rpi.txt
```

### 3. Reboot

```bash
sudo reboot
```

## Testing

### 1. Test I2C Bus

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

## Troubleshooting

### No I2C Devices Found

1. **Check connections**: Ensure SDA and SCL are properly connected
2. **Check power**: Verify 3.3V and GND connections
3. **Enable I2C**: Make sure I2C is enabled in `/boot/config.txt`
4. **Reboot**: I2C changes require a reboot

### ADS1115 Not Responding

1. **Check address**: Default address is 0x48
2. **Check pull-up resistors**: I2C needs pull-up resistors (usually on the module)
3. **Check voltage levels**: Ensure 3.3V operation
4. **Check wiring**: Verify no loose connections

### Permission Errors

```bash
# Add user to i2c group
sudo usermod -a -G i2c $USER

# Log out and back in, or reboot
```

## Features

- **Real-time ADC readings** from ADS1115
- **16-bit resolution** for accurate measurements
- **Configurable gain** (±4.096V range)
- **Optimized data rate** (860 SPS)
- **I2C device scanning** for troubleshooting
- **Professional-grade accuracy** for antenna analysis

## Performance

- **ADC Resolution**: 16-bit (65,536 levels)
- **Voltage Range**: ±4.096V (configurable)
- **Data Rate**: 860 samples per second
- **Accuracy**: ±0.01% typical
- **Temperature Drift**: ±0.0005% per °C

## Calibration

The analyzer automatically calibrates based on:
- **Reference voltage**: 3.3V from Raspberry Pi
- **ADC readings**: Real-time voltage measurements
- **SWR calculation**: Based on reflection coefficient

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run `test_ads1115.py` to verify hardware
3. Check I2C bus with `i2cdetect -y 1`
4. Verify all connections and power supply

## License

This project is open source. Feel free to modify and improve it for your needs.
