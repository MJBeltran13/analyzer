#!/usr/bin/env python3
"""
Simple test script for ADS1115 ADC
Use this to verify your ADS1115 is working correctly
"""

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

def test_ads1115():
    """Test ADS1115 basic functionality"""
    try:
        print("🔌 Initializing ADS1115...")
        
        # Initialize I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Scan for I2C devices
        print("🔍 Scanning I2C bus...")
        i2c_devices = []
        for device in i2c.scan():
            i2c_devices.append(hex(device))
        print(f"Found I2C devices: {i2c_devices}")
        
        if not i2c_devices:
            print("❌ No I2C devices found. Check your connections!")
            return False
        
        # Initialize ADS1115
        ads = ADS.ADS1115(i2c)
        
        # Configure for optimal performance
        ads.gain = 1  # ±4.096V range
        ads.data_rate = 860  # 860 SPS
        
        print(f"✅ ADS1115 initialized: Gain={ads.gain}, Data Rate={ads.data_rate} SPS")
        
        # Create analog input objects
        chan0 = AnalogIn(ads, ADS.P0)  # Magnitude
        chan1 = AnalogIn(ads, ADS.P1)  # Phase
        
        print("🔍 Testing ADC readings...")
        print("Channel 0 (Magnitude) | Channel 1 (Phase)")
        print("-" * 40)
        
        for i in range(10):
            mag_voltage = chan0.voltage
            phase_voltage = chan1.voltage
            mag_raw = chan0.value
            phase_raw = chan1.value
            
            print(f"Sample {i+1:2d}: {mag_voltage:6.3f}V ({mag_raw:6d}) | {phase_voltage:6.3f}V ({phase_raw:6d})")
            time.sleep(0.5)
        
        print("✅ ADS1115 test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ ADS1115 test failed: {e}")
        return False

if __name__ == "__main__":
    print("ADS1115 Test Script")
    print("=" * 50)
    print("Make sure your ADS1115 is connected to SDA and SCL pins")
    print("and powered with 3.3V and GND")
    print()
    
    success = test_ads1115()
    
    if success:
        print("\n🎉 ADS1115 is working correctly!")
        print("You can now run the main analyzer.py script")
    else:
        print("\n💥 ADS1115 test failed!")
        print("Please check:")
        print("1. Power connections (3.3V and GND)")
        print("2. I2C connections (SDA and SCL)")
        print("3. I2C pull-up resistors (if needed)")
        print("4. ADS1115 address (default should work)")
