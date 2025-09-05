#!/usr/bin/env python3
"""
Debug script for ADS1115 I2C communication issues
"""

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

def debug_ads1115():
    """Debug ADS1115 step by step"""
    try:
        print("🔌 Step 1: Initializing I2C...")
        i2c = busio.I2C(board.SCL, board.SDA)
        print("✅ I2C initialized")
        
        print("🔍 Step 2: Scanning I2C bus...")
        i2c_devices = []
        for device in i2c.scan():
            i2c_devices.append(hex(device))
        print(f"Found I2C devices: {i2c_devices}")
        
        if '0x48' not in i2c_devices:
            print("❌ ADS1115 not found at 0x48")
            return False
            
        print("🔌 Step 3: Creating ADS1115 object...")
        ads = ADS.ADS1115(i2c)
        print("✅ ADS1115 object created")
        
        print("⚙️ Step 4: Configuring ADS1115...")
        ads.gain = 1  # ±4.096V range
        ads.data_rate = 860  # 860 SPS
        print("✅ ADS1115 configured")
        
        print("📊 Step 5: Creating analog input objects...")
        chan0 = AnalogIn(ads, ADS.P0)  # Magnitude
        chan1 = AnalogIn(ads, ADS.P1)  # Phase
        print("✅ Analog input objects created")
        
        print("🔍 Step 6: Testing readings...")
        for i in range(3):
            try:
                mag_voltage = chan0.voltage
                phase_voltage = chan1.voltage
                mag_raw = chan0.value
                phase_raw = chan1.value
                print(f"Sample {i+1}: Mag={mag_voltage:.3f}V ({mag_raw}), Phase={phase_voltage:.3f}V ({phase_raw})")
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Reading error on sample {i+1}: {e}")
                return False
        
        print("✅ ADS1115 debug completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Debug failed at step: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("ADS1115 Debug Script")
    print("=" * 50)
    debug_ads1115()
