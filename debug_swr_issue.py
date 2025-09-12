#!/usr/bin/env python3
"""
Debug tool to identify why SWR readings are always 1.00
This script will help diagnose the antenna analyzer measurement issue
"""

import time
import numpy as np
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO

class SWRDebugger:
    def __init__(self):
        # Hardware configuration
        self.W_CLK = 12  # violet white is gnd
        self.FQ_UD = 16  # white
        self.DATA = 20   # blue
        self.RESET = 21  # green
        self.ads = None
        self.chan0 = None  # Magnitude channel
        self.chan1 = None  # Phase channel
        self.hardware_ready = False
        self.setup_hardware()

    def setup_hardware(self):
        """Initialize hardware for debugging"""
        try:
            print("🔌 Initializing hardware for debugging...")
            
            # Initialize ADS1115 I2C ADC
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Scan for I2C devices
            print("🔍 Scanning I2C bus...")
            i2c_devices = []
            for device in i2c.scan():
                i2c_devices.append(hex(device))
            print(f"Found I2C devices: {i2c_devices}")
            
            if not i2c_devices:
                print("❌ No I2C devices found!")
                return
            
            self.ads = ADS.ADS1115(i2c)
            self.ads.gain = 1  # ±4.096V range
            self.ads.data_rate = 860  # 860 SPS
            
            self.chan0 = AnalogIn(self.ads, ADS.P0)  # Magnitude
            self.chan1 = AnalogIn(self.ads, ADS.P1)  # Phase
            
            print("✅ ADS1115 initialized")
            
            # Initialize GPIO for AD9850
            GPIO.setmode(GPIO.BCM)
            GPIO.setup([self.W_CLK, self.FQ_UD, self.DATA, self.RESET], GPIO.OUT)
            GPIO.output([self.W_CLK, self.FQ_UD, self.DATA], GPIO.LOW)
            GPIO.output(self.RESET, GPIO.HIGH)
            
            self.reset_dds()
            self.hardware_ready = True
            print("✅ Hardware ready for debugging")
            
        except Exception as e:
            print(f"❌ Hardware setup failed: {e}")
            self.hardware_ready = False

    def reset_dds(self):
        """Reset the AD9850 DDS"""
        GPIO.output(self.RESET, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(self.RESET, GPIO.LOW)
        time.sleep(0.001)
        GPIO.output(self.RESET, GPIO.HIGH)

    def set_frequency(self, freq_hz):
        """Set DDS frequency"""
        if not self.hardware_ready:
            return False
        
        system_clock_hz = 125_000_000.0
        ftw = int((freq_hz * 4294967296.0) / system_clock_hz) & 0xFFFFFFFF
        control_byte = 0x00
        
        # Load 32-bit FTW, LSB-first
        for bit_index in range(32):
            bit = (ftw >> bit_index) & 0x1
            GPIO.output(self.DATA, GPIO.HIGH if bit else GPIO.LOW)
            GPIO.output(self.W_CLK, GPIO.HIGH)
            GPIO.output(self.W_CLK, GPIO.LOW)
        
        # Load 8-bit control byte, LSB-first
        for bit_index in range(8):
            bit = (control_byte >> bit_index) & 0x1
            GPIO.output(self.DATA, GPIO.HIGH if bit else GPIO.LOW)
            GPIO.output(self.W_CLK, GPIO.HIGH)
            GPIO.output(self.W_CLK, GPIO.LOW)
        
        # Latch the 40-bit word
        GPIO.output(self.FQ_UD, GPIO.HIGH)
        GPIO.output(self.FQ_UD, GPIO.LOW)
        return True

    def read_adc(self, channel):
        """Read ADC voltage"""
        if not self.hardware_ready:
            return 0
        try:
            if channel == 0:
                return self.chan0.voltage
            elif channel == 1:
                return self.chan1.voltage
            else:
                return 0
        except Exception as e:
            print(f"ADC read error on channel {channel}: {e}")
            return 0

    def calculate_swr_original(self, mag_voltage):
        """Original SWR calculation from analyzer.py"""
        if mag_voltage <= 1.0:
            swr = 1.0  # Perfect match
        elif mag_voltage <= 1.1:
            # Linear interpolation between 1.0V (SWR=1.0) and 1.1V (SWR=3.0)
            swr = 1.0 + ((mag_voltage - 1.0) / 0.1) * 2.0
        else:
            # For higher voltages, use exponential curve
            excess_voltage = mag_voltage - 1.1
            swr = 3.0 + excess_voltage * 10.0
        
        # Clamp SWR to reasonable range
        swr = max(1.0, min(swr, 50.0))
        return swr

    def calculate_swr_improved(self, mag_voltage):
        """Improved SWR calculation that handles actual voltage ranges"""
        # Map voltage to SWR with better scaling
        # Assume 0V = perfect match (SWR 1.0), higher voltages = worse match
        
        if mag_voltage <= 0.1:
            swr = 1.0  # Very low voltage = perfect match
        elif mag_voltage <= 1.0:
            # Linear interpolation: 0.1V = SWR 1.0, 1.0V = SWR 2.0
            swr = 1.0 + ((mag_voltage - 0.1) / 0.9) * 1.0
        elif mag_voltage <= 2.0:
            # Linear interpolation: 1.0V = SWR 2.0, 2.0V = SWR 5.0
            swr = 2.0 + ((mag_voltage - 1.0) / 1.0) * 3.0
        else:
            # Exponential for higher voltages
            excess_voltage = mag_voltage - 2.0
            swr = 5.0 + excess_voltage * 5.0
        
        # Clamp SWR to reasonable range
        swr = max(1.0, min(swr, 50.0))
        return swr

    def debug_measurement(self, freq_hz):
        """Debug a single measurement point"""
        print(f"\n🔍 Debugging measurement at {freq_hz/1e6:.1f} MHz")
        
        # Set frequency
        if not self.set_frequency(freq_hz):
            print("❌ Failed to set frequency")
            return None
        
        time.sleep(0.01)  # Wait for DDS to settle
        
        # Read ADC values multiple times
        mag_readings = []
        phase_readings = []
        
        for i in range(5):
            mag_voltage = self.read_adc(0)
            phase_voltage = self.read_adc(1)
            mag_readings.append(mag_voltage)
            phase_readings.append(phase_voltage)
            time.sleep(0.001)
        
        # Calculate statistics
        mag_avg = np.mean(mag_readings)
        mag_std = np.std(mag_readings)
        phase_avg = np.mean(phase_readings)
        phase_std = np.std(phase_readings)
        
        # Calculate SWR with both methods
        swr_original = self.calculate_swr_original(mag_avg)
        swr_improved = self.calculate_swr_improved(mag_avg)
        
        print(f"📊 ADC Readings:")
        print(f"   Magnitude: {mag_avg:.3f}V ± {mag_std:.3f}V (range: {min(mag_readings):.3f}V - {max(mag_readings):.3f}V)")
        print(f"   Phase: {phase_avg:.3f}V ± {phase_std:.3f}V (range: {min(phase_readings):.3f}V - {max(phase_readings):.3f}V)")
        print(f"📈 SWR Calculations:")
        print(f"   Original method: {swr_original:.2f}")
        print(f"   Improved method: {swr_improved:.2f}")
        
        # Analysis
        print(f"🔍 Analysis:")
        if mag_avg <= 0.1:
            print("   ⚠️  Very low magnitude voltage - possible issues:")
            print("      - No antenna connected")
            print("      - ADC not receiving signal")
            print("      - Hardware connection problem")
        elif mag_avg <= 1.0:
            print("   ✅ Low magnitude voltage - normal for good antenna match")
        elif mag_avg <= 2.0:
            print("   ⚠️  Medium magnitude voltage - moderate antenna mismatch")
        else:
            print("   ❌ High magnitude voltage - poor antenna match or hardware issue")
        
        return {
            'frequency': freq_hz,
            'mag_voltage': mag_avg,
            'phase_voltage': phase_avg,
            'swr_original': swr_original,
            'swr_improved': swr_improved,
            'mag_readings': mag_readings,
            'phase_readings': phase_readings
        }

    def run_diagnostic(self):
        """Run comprehensive diagnostic"""
        print("🔧 ANTENNA ANALYZER DIAGNOSTIC TOOL")
        print("=" * 50)
        
        if not self.hardware_ready:
            print("❌ Hardware not ready. Cannot run diagnostic.")
            return
        
        # Test different frequencies
        test_frequencies = [10e6, 14.2e6, 21.3e6, 28.5e6]  # Common ham bands
        
        print(f"\n🧪 Testing {len(test_frequencies)} frequencies...")
        
        results = []
        for freq in test_frequencies:
            result = self.debug_measurement(freq)
            if result:
                results.append(result)
        
        # Summary
        print(f"\n📋 DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        if results:
            mag_voltages = [r['mag_voltage'] for r in results]
            phase_voltages = [r['phase_voltage'] for r in results]
            swr_original = [r['swr_original'] for r in results]
            swr_improved = [r['swr_improved'] for r in results]
            
            print(f"📊 Voltage Statistics:")
            print(f"   Magnitude: {min(mag_voltages):.3f}V - {max(mag_voltages):.3f}V (avg: {np.mean(mag_voltages):.3f}V)")
            print(f"   Phase: {min(phase_voltages):.3f}V - {max(phase_voltages):.3f}V (avg: {np.mean(phase_voltages):.3f}V)")
            
            print(f"📈 SWR Statistics:")
            print(f"   Original method: {min(swr_original):.2f} - {max(swr_original):.2f} (avg: {np.mean(swr_original):.2f})")
            print(f"   Improved method: {min(swr_improved):.2f} - {max(swr_improved):.2f} (avg: {np.mean(swr_improved):.2f})")
            
            # Identify the issue
            print(f"\n🔍 ISSUE IDENTIFICATION:")
            if all(swr == 1.0 for swr in swr_original):
                print("   ❌ PROBLEM FOUND: All SWR values are 1.00")
                print("   🔧 CAUSE: Original SWR calculation expects voltages 1.0V-1.1V")
                print(f"   📊 ACTUAL: Your voltages are {min(mag_voltages):.3f}V - {max(mag_voltages):.3f}V")
                print("   💡 SOLUTION: Use improved SWR calculation or adjust voltage mapping")
            else:
                print("   ✅ SWR calculation is working correctly")
            
            if np.mean(mag_voltages) < 0.5:
                print("   ⚠️  WARNING: Very low magnitude voltages detected")
                print("   🔧 POSSIBLE CAUSES:")
                print("      - No antenna connected to the analyzer")
                print("      - Antenna analyzer circuit not properly built")
                print("      - ADC not receiving the magnitude signal")
                print("      - Wrong voltage range in SWR calculation")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print("   1. Check that an antenna is connected to your analyzer")
        print("   2. Verify the antenna analyzer circuit is properly built")
        print("   3. Use the improved SWR calculation method")
        print("   4. Consider adding voltage offset calibration")

    def cleanup(self):
        """Clean up hardware"""
        if self.hardware_ready:
            GPIO.cleanup()

if __name__ == "__main__":
    debugger = SWRDebugger()
    try:
        debugger.run_diagnostic()
    finally:
        debugger.cleanup()
