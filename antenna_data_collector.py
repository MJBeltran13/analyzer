#!/usr/bin/env python3
"""
Antenna Data Collector
Collects data with and without antenna for analyzer calibration
"""

import RPi.GPIO as GPIO
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time
import numpy as np
import json
import os
from datetime import datetime
import argparse


class AntennaDataCollector:
    def __init__(self):
        # Hardware configuration (same as analyzer.py)
        self.W_CLK = 12  # violet white is gnd
        self.FQ_UD = 16  # white
        self.DATA = 20   # blue
        self.RESET = 21  # green
        self.ref_voltage = 3.3
        self.adc_resolution = 65536  # 16-bit ADS1115
        self.ads = None
        self.chan0 = None  # Magnitude channel
        self.chan1 = None  # Phase channel
        self.hardware_ready = False
        self.setup_hardware()

    def setup_hardware(self):
        """Initialize GPIO and I2C ADC"""
        try:
            # Initialize ADS1115 I2C ADC FIRST (before GPIO to avoid conflicts)
            print("🔌 Initializing ADS1115 I2C ADC...")
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Scan for I2C devices
            print("🔍 Scanning I2C bus...")
            i2c_devices = []
            for device in i2c.scan():
                i2c_devices.append(hex(device))
            print(f"Found I2C devices: {i2c_devices}")
            
            self.ads = ADS.ADS1115(i2c)
            
            # Configure ADS1115 for optimal performance
            self.ads.gain = 1  # ±4.096V range for better resolution
            self.ads.data_rate = 860  # 860 samples per second for good speed/accuracy balance
            
            self.chan0 = AnalogIn(self.ads, ADS.P0)  # Magnitude
            self.chan1 = AnalogIn(self.ads, ADS.P1)  # Phase
            
            print(f"✅ ADS1115 configured: Gain={self.ads.gain}, Data Rate={self.ads.data_rate} SPS")
            
            # Mark hardware ready before running self-test to avoid false warning
            self.hardware_ready = True

            # Test ADC readings
            self.test_adc_readings()

            # Initialize GPIO AFTER I2C (to avoid conflicts)
            print("🔌 Initializing GPIO for AD9850...")
            GPIO.setmode(GPIO.BCM)
            GPIO.setup([self.W_CLK, self.FQ_UD, self.DATA, self.RESET], GPIO.OUT)
            GPIO.output([self.W_CLK, self.FQ_UD, self.DATA], GPIO.LOW)
            GPIO.output(self.RESET, GPIO.HIGH)

            self.reset_dds()
            print("✅ Real hardware initialized (ADS1115 I2C ADC + AD9850 DDS)")
        except Exception as e:
            print(f"❌ Hardware initialization failed: {e}")
            print("Please check your I2C connections (SDA/SCL) and ensure ADS1115 is properly connected")
            self.hardware_ready = False

    def reset_dds(self):
        GPIO.output(self.RESET, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(self.RESET, GPIO.LOW)
        time.sleep(0.001)
        GPIO.output(self.RESET, GPIO.HIGH)

    def set_frequency(self, freq_hz):
        """Program AD9850 via 3-wire serial: 32-bit FTW + 8-bit control, LSB-first."""
        if not self.hardware_ready:
            return False

        # AD9850 reference clock
        system_clock_hz = 125_000_000.0
        ftw = int((freq_hz * 4294967296.0) / system_clock_hz) & 0xFFFFFFFF

        # AD9850 control byte (0x00 for default operation)
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
        if not self.hardware_ready:
            return 0
        try:
            # Read from ADS1115
            if channel == 0:
                voltage = self.chan0.voltage
                raw_value = self.chan0.value
                return voltage
            elif channel == 1:
                voltage = self.chan1.voltage
                raw_value = self.chan1.value
                return voltage
            else:
                return 0
        except Exception as e:
            print(f"ADC read error on channel {channel}: {e}")
            return 0

    def test_adc_readings(self):
        """Test ADC readings for troubleshooting"""
        if not self.hardware_ready:
            print("❌ Hardware not ready")
            return
        
        print("🔍 Testing ADC readings...")
        mag_readings = []
        phase_readings = []
        
        for i in range(5):
            mag_voltage = self.read_adc(0)
            phase_voltage = self.read_adc(1)
            mag_readings.append(mag_voltage)
            phase_readings.append(phase_voltage)
            print(f"Sample {i+1}: Magnitude={mag_voltage:.3f}V, Phase={phase_voltage:.3f}V")
            time.sleep(0.1)
        
        # Calculate and display statistics
        if mag_readings:
            mag_avg = sum(mag_readings) / len(mag_readings)
            phase_avg = sum(phase_readings) / len(phase_readings)
            print(f"📊 Average readings: Magnitude={mag_avg:.3f}V, Phase={phase_avg:.3f}V")
        
        print("✅ ADC test completed")

    def measure_point(self, freq_hz, samples=5):
        """Measure a single frequency point with multiple samples for averaging"""
        if not self.set_frequency(freq_hz):
            return None
        
        time.sleep(0.01)  # Allow DDS to settle
        
        mag_readings = []
        phase_readings = []
        
        # Take multiple samples for better accuracy
        for _ in range(samples):
            mag_voltage = self.read_adc(0)
            phase_voltage = self.read_adc(1)
            mag_readings.append(mag_voltage)
            phase_readings.append(phase_voltage)
            time.sleep(0.001)  # Small delay between samples
        
        # Calculate averages and standard deviations
        mag_avg = np.mean(mag_readings)
        phase_avg = np.mean(phase_readings)
        mag_std = np.std(mag_readings)
        phase_std = np.std(phase_readings)
        
        return {
            'frequency': freq_hz,
            'mag_voltage': mag_avg,
            'phase_voltage': phase_avg,
            'mag_std': mag_std,
            'phase_std': phase_std,
            'mag_readings': mag_readings,
            'phase_readings': phase_readings,
            'samples': samples
        }

    def collect_data(self, start_freq_mhz, stop_freq_mhz, points=50, antenna_connected=True):
        """Collect data across frequency range"""
        print(f"\n{'='*60}")
        print(f"📡 COLLECTING DATA - {'WITH' if antenna_connected else 'WITHOUT'} ANTENNA")
        print(f"Frequency range: {start_freq_mhz} - {stop_freq_mhz} MHz")
        print(f"Points: {points}")
        print(f"{'='*60}")
        
        if not self.hardware_ready:
            print("❌ Hardware not ready!")
            return None
        
        start_freq_hz = start_freq_mhz * 1e6
        stop_freq_hz = stop_freq_mhz * 1e6
        frequencies = np.linspace(start_freq_hz, stop_freq_hz, points)
        
        measurements = []
        
        for i, freq_hz in enumerate(frequencies):
            freq_mhz = freq_hz / 1e6
            print(f"Measuring {freq_mhz:.2f} MHz ({i+1}/{points})...", end=" ")
            
            measurement = self.measure_point(freq_hz)
            if measurement:
                measurements.append(measurement)
                mag_v = measurement['mag_voltage']
                phase_v = measurement['phase_voltage']
                print(f"Mag={mag_v:.3f}V, Phase={phase_v:.3f}V")
            else:
                print("FAILED")
            
            # Small delay between measurements
            time.sleep(0.01)
        
        print(f"\n✅ Collected {len(measurements)} measurements")
        return measurements

    def save_data(self, measurements, antenna_connected, filename=None):
        """Save collected data to JSON file"""
        if not measurements:
            print("❌ No data to save!")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            antenna_status = "with_antenna" if antenna_connected else "without_antenna"
            filename = f"antenna_data_{antenna_status}_{timestamp}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'antenna_connected': antenna_connected,
            'hardware_info': {
                'ads1115_gain': self.ads.gain if self.ads else None,
                'ads1115_data_rate': self.ads.data_rate if self.ads else None,
                'reference_voltage': self.ref_voltage,
                'adc_resolution': self.adc_resolution
            },
            'measurements': measurements,
            'statistics': self.calculate_statistics(measurements)
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Data saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to save data: {e}")
            return None

    def calculate_statistics(self, measurements):
        """Calculate statistics from measurements"""
        if not measurements:
            return {}
        
        mag_voltages = [m['mag_voltage'] for m in measurements]
        phase_voltages = [m['phase_voltage'] for m in measurements]
        
        stats = {
            'mag_voltage': {
                'min': min(mag_voltages),
                'max': max(mag_voltages),
                'mean': np.mean(mag_voltages),
                'std': np.std(mag_voltages),
                'range': max(mag_voltages) - min(mag_voltages)
            },
            'phase_voltage': {
                'min': min(phase_voltages),
                'max': max(phase_voltages),
                'mean': np.mean(phase_voltages),
                'std': np.std(phase_voltages),
                'range': max(phase_voltages) - min(phase_voltages)
            },
            'total_measurements': len(measurements)
        }
        
        return stats

    def print_statistics(self, measurements, antenna_connected):
        """Print statistics for collected data"""
        if not measurements:
            return
        
        stats = self.calculate_statistics(measurements)
        
        print(f"\n{'='*60}")
        print(f"📊 STATISTICS - {'WITH' if antenna_connected else 'WITHOUT'} ANTENNA")
        print(f"{'='*60}")
        
        print(f"Total measurements: {stats['total_measurements']}")
        print(f"\nMagnitude Voltage:")
        print(f"  Min: {stats['mag_voltage']['min']:.3f}V")
        print(f"  Max: {stats['mag_voltage']['max']:.3f}V")
        print(f"  Mean: {stats['mag_voltage']['mean']:.3f}V")
        print(f"  Std Dev: {stats['mag_voltage']['std']:.3f}V")
        print(f"  Range: {stats['mag_voltage']['range']:.3f}V")
        
        print(f"\nPhase Voltage:")
        print(f"  Min: {stats['phase_voltage']['min']:.3f}V")
        print(f"  Max: {stats['phase_voltage']['max']:.3f}V")
        print(f"  Mean: {stats['phase_voltage']['mean']:.3f}V")
        print(f"  Std Dev: {stats['phase_voltage']['std']:.3f}V")
        print(f"  Range: {stats['phase_voltage']['range']:.3f}V")

    def cleanup(self):
        """Clean up GPIO resources"""
        if self.hardware_ready:
            GPIO.cleanup()
            print("🧹 GPIO cleanup completed")


def main():
    parser = argparse.ArgumentParser(description='Collect antenna data for analyzer calibration')
    parser.add_argument('--start', type=float, default=10.0, help='Start frequency in MHz (default: 10.0)')
    parser.add_argument('--stop', type=float, default=20.0, help='Stop frequency in MHz (default: 20.0)')
    parser.add_argument('--points', type=int, default=50, help='Number of measurement points (default: 50)')
    parser.add_argument('--with-antenna', action='store_true', help='Collect data with antenna connected')
    parser.add_argument('--without-antenna', action='store_true', help='Collect data without antenna connected')
    parser.add_argument('--both', action='store_true', help='Collect data both with and without antenna')
    parser.add_argument('--output', type=str, help='Output filename (optional)')
    
    args = parser.parse_args()
    
    if not any([args.with_antenna, args.without_antenna, args.both]):
        print("❌ Please specify --with-antenna, --without-antenna, or --both")
        return
    
    collector = AntennaDataCollector()
    
    if not collector.hardware_ready:
        print("❌ Hardware initialization failed. Exiting.")
        return
    
    try:
        if args.both or args.with_antenna:
            print("\n🔄 Starting data collection WITH antenna...")
            print("Please connect your antenna and press Enter when ready...")
            input()
            
            measurements_with = collector.collect_data(
                args.start, args.stop, args.points, antenna_connected=True
            )
            
            if measurements_with:
                collector.print_statistics(measurements_with, True)
                collector.save_data(measurements_with, True, 
                                  f"{args.output}_with_antenna.json" if args.output else None)
        
        if args.both or args.without_antenna:
            print("\n🔄 Starting data collection WITHOUT antenna...")
            print("Please disconnect your antenna and press Enter when ready...")
            input()
            
            measurements_without = collector.collect_data(
                args.start, args.stop, args.points, antenna_connected=False
            )
            
            if measurements_without:
                collector.print_statistics(measurements_without, False)
                collector.save_data(measurements_without, False,
                                  f"{args.output}_without_antenna.json" if args.output else None)
        
        print("\n✅ Data collection completed!")
        print("📁 Check the generated JSON files for detailed measurements.")
        print("📊 Use this data to adjust the analyzer.py calibration formulas.")
        
    except KeyboardInterrupt:
        print("\n⚠️ Data collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during data collection: {e}")
    finally:
        collector.cleanup()


if __name__ == '__main__':
    main()
