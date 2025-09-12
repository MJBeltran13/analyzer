#!/usr/bin/env python3
"""
Antenna Data Analyzer
Analyzes collected antenna data and suggests calibration adjustments for analyzer.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
from datetime import datetime
import glob


class AntennaDataAnalyzer:
    def __init__(self):
        self.data_with_antenna = None
        self.data_without_antenna = None
        self.analysis_results = {}

    def load_data(self, with_antenna_file=None, without_antenna_file=None):
        """Load data from JSON files"""
        if with_antenna_file:
            try:
                with open(with_antenna_file, 'r') as f:
                    self.data_with_antenna = json.load(f)
                print(f"✅ Loaded data WITH antenna from: {with_antenna_file}")
            except Exception as e:
                print(f"❌ Failed to load data WITH antenna: {e}")
                return False

        if without_antenna_file:
            try:
                with open(without_antenna_file, 'r') as f:
                    self.data_without_antenna = json.load(f)
                print(f"✅ Loaded data WITHOUT antenna from: {without_antenna_file}")
            except Exception as e:
                print(f"❌ Failed to load data WITHOUT antenna: {e}")
                return False

        return True

    def auto_find_data_files(self):
        """Automatically find the most recent data files"""
        with_antenna_files = sorted(glob.glob("antenna_data_with_antenna_*.json"), reverse=True)
        without_antenna_files = sorted(glob.glob("antenna_data_without_antenna_*.json"), reverse=True)
        
        if with_antenna_files:
            self.load_data(with_antenna_file=with_antenna_files[0])
        
        if without_antenna_files:
            self.load_data(without_antenna_file=without_antenna_files[0])
        
        return len(with_antenna_files) > 0 or len(without_antenna_files) > 0

    def analyze_voltage_ranges(self):
        """Analyze voltage ranges and suggest calibration points"""
        print("\n" + "="*60)
        print("📊 VOLTAGE RANGE ANALYSIS")
        print("="*60)

        if self.data_with_antenna:
            measurements = self.data_with_antenna['measurements']
            mag_voltages = [m['mag_voltage'] for m in measurements]
            phase_voltages = [m['phase_voltage'] for m in measurements]
            
            print(f"\nWITH ANTENNA:")
            print(f"  Magnitude voltage range: {min(mag_voltages):.3f}V - {max(mag_voltages):.3f}V")
            print(f"  Phase voltage range: {min(phase_voltages):.3f}V - {max(phase_voltages):.3f}V")
            print(f"  Magnitude mean: {np.mean(mag_voltages):.3f}V ± {np.std(mag_voltages):.3f}V")
            print(f"  Phase mean: {np.mean(phase_voltages):.3f}V ± {np.std(phase_voltages):.3f}V")

        if self.data_without_antenna:
            measurements = self.data_without_antenna['measurements']
            mag_voltages = [m['mag_voltage'] for m in measurements]
            phase_voltages = [m['phase_voltage'] for m in measurements]
            
            print(f"\nWITHOUT ANTENNA:")
            print(f"  Magnitude voltage range: {min(mag_voltages):.3f}V - {max(mag_voltages):.3f}V")
            print(f"  Phase voltage range: {min(phase_voltages):.3f}V - {max(phase_voltages):.3f}V")
            print(f"  Magnitude mean: {np.mean(mag_voltages):.3f}V ± {np.std(mag_voltages):.3f}V")
            print(f"  Phase mean: {np.mean(phase_voltages):.3f}V ± {np.std(phase_voltages):.3f}V")

    def suggest_swr_calibration(self):
        """Suggest SWR calibration formula based on collected data"""
        print("\n" + "="*60)
        print("🔧 SWR CALIBRATION SUGGESTIONS")
        print("="*60)

        if not self.data_with_antenna or not self.data_without_antenna:
            print("❌ Need both WITH and WITHOUT antenna data for calibration suggestions")
            return

        with_antenna_mag = [m['mag_voltage'] for m in self.data_with_antenna['measurements']]
        without_antenna_mag = [m['mag_voltage'] for m in self.data_without_antenna['measurements']]

        # Find typical voltage ranges
        with_antenna_min = min(with_antenna_mag)
        with_antenna_max = max(with_antenna_mag)
        without_antenna_min = min(without_antenna_mag)
        without_antenna_max = max(without_antenna_mag)

        print(f"\nVoltage Analysis:")
        print(f"  WITH antenna: {with_antenna_min:.3f}V - {with_antenna_max:.3f}V")
        print(f"  WITHOUT antenna: {without_antenna_min:.3f}V - {without_antenna_max:.3f}V")

        # Calculate voltage difference
        voltage_diff = without_antenna_max - with_antenna_min
        print(f"  Voltage difference: {voltage_diff:.3f}V")

        # Suggest calibration points
        print(f"\nSuggested SWR Calibration Formula:")
        print(f"  # Based on your data analysis")
        print(f"  if mag_voltage <= {with_antenna_min:.3f}:")
        print(f"      swr = 1.0  # Perfect match (best antenna reading)")
        print(f"  elif mag_voltage <= {with_antenna_max:.3f}:")
        print(f"      # Good antenna range: {with_antenna_min:.3f}V - {with_antenna_max:.3f}V")
        print(f"      swr = 1.0 + ((mag_voltage - {with_antenna_min:.3f}) / {with_antenna_max - with_antenna_min:.3f}) * 0.5")
        print(f"  elif mag_voltage <= {without_antenna_min:.3f}:")
        print(f"      # Poor match range: {with_antenna_max:.3f}V - {without_antenna_min:.3f}V")
        print(f"      swr = 1.5 + ((mag_voltage - {with_antenna_max:.3f}) / {without_antenna_min - with_antenna_max:.3f}) * 1.5")
        print(f"  elif mag_voltage <= {without_antenna_max:.3f}:")
        print(f"      # No antenna range: {without_antenna_min:.3f}V - {without_antenna_max:.3f}V")
        print(f"      swr = 3.0 + ((mag_voltage - {without_antenna_min:.3f}) / {without_antenna_max - without_antenna_min:.3f}) * 2.0")
        print(f"  else:")
        print(f"      # Extreme mismatch")
        print(f"      excess_voltage = mag_voltage - {without_antenna_max:.3f}")
        print(f"      swr = 5.0 + excess_voltage * 5.0")

        # Generate the actual Python code
        self.generate_calibration_code(with_antenna_min, with_antenna_max, 
                                     without_antenna_min, without_antenna_max)

    def generate_calibration_code(self, with_min, with_max, without_min, without_max):
        """Generate the actual calibration code for analyzer.py"""
        print(f"\n" + "="*60)
        print("📝 GENERATED CALIBRATION CODE")
        print("="*60)
        print("Replace the SWR calculation in analyzer.py with this code:")
        print()

        code = f'''        # Calculate SWR from real ADC measurements
        # Calibrated based on your antenna data analysis
        # WITH antenna range: {with_min:.3f}V - {with_max:.3f}V
        # WITHOUT antenna range: {without_min:.3f}V - {without_max:.3f}V
        
        if mag_voltage <= {with_min:.3f}:
            # Perfect match (best antenna reading)
            swr = 1.0
        elif mag_voltage <= {with_max:.3f}:
            # Good antenna range: {with_min:.3f}V - {with_max:.3f}V
            swr = 1.0 + ((mag_voltage - {with_min:.3f}) / {with_max - with_min:.3f}) * 0.5
        elif mag_voltage <= {without_min:.3f}:
            # Poor match range: {with_max:.3f}V - {without_min:.3f}V
            swr = 1.5 + ((mag_voltage - {with_max:.3f}) / {without_min - with_max:.3f}) * 1.5
        elif mag_voltage <= {without_max:.3f}:
            # No antenna range: {without_min:.3f}V - {without_max:.3f}V
            swr = 3.0 + ((mag_voltage - {without_min:.3f}) / {without_max - without_min:.3f}) * 2.0
        else:
            # Extreme mismatch
            excess_voltage = mag_voltage - {without_max:.3f}
            swr = 5.0 + excess_voltage * 5.0
        
        # Clamp SWR to reasonable range
        swr = max(1.0, min(swr, 50.0))'''

        print(code)

        # Save to file
        with open('suggested_calibration.py', 'w') as f:
            f.write(code)
        print(f"\n💾 Calibration code saved to: suggested_calibration.py")

    def analyze_antenna_detection(self):
        """Analyze how to detect antenna connection"""
        print("\n" + "="*60)
        print("🔍 ANTENNA DETECTION ANALYSIS")
        print("="*60)

        if not self.data_with_antenna or not self.data_without_antenna:
            print("❌ Need both WITH and WITHOUT antenna data for detection analysis")
            return

        with_antenna_mag = [m['mag_voltage'] for m in self.data_with_antenna['measurements']]
        without_antenna_mag = [m['mag_voltage'] for m in self.data_without_antenna['measurements']]

        with_antenna_mean = np.mean(with_antenna_mag)
        without_antenna_mean = np.mean(without_antenna_mag)
        
        with_antenna_std = np.std(with_antenna_mag)
        without_antenna_std = np.std(without_antenna_mag)

        # Calculate separation
        separation = abs(without_antenna_mean - with_antenna_mean)
        combined_std = np.sqrt(with_antenna_std**2 + without_antenna_std**2)

        print(f"WITH antenna: {with_antenna_mean:.3f}V ± {with_antenna_std:.3f}V")
        print(f"WITHOUT antenna: {without_antenna_mean:.3f}V ± {without_antenna_std:.3f}V")
        print(f"Separation: {separation:.3f}V")
        print(f"Combined std dev: {combined_std:.3f}V")

        if separation > 3 * combined_std:
            print("✅ Good separation - antenna detection should work well")
            threshold = (with_antenna_mean + without_antenna_mean) / 2
            print(f"Suggested threshold: {threshold:.3f}V")
        else:
            print("⚠️ Poor separation - antenna detection may be unreliable")
            print("Consider improving your antenna analyzer circuit")

        # Generate detection code
        print(f"\nSuggested antenna detection code:")
        print(f"def detect_antenna_connection(self, mag_voltage, phase_voltage):")
        print(f"    # Based on your data analysis")
        print(f"    threshold = {threshold:.3f}")
        print(f"    return mag_voltage < threshold")

    def plot_data_comparison(self):
        """Plot comparison of with/without antenna data"""
        if not self.data_with_antenna or not self.data_without_antenna:
            print("❌ Need both datasets for plotting")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Extract data
        with_antenna_freqs = [m['frequency']/1e6 for m in self.data_with_antenna['measurements']]
        with_antenna_mag = [m['mag_voltage'] for m in self.data_with_antenna['measurements']]
        with_antenna_phase = [m['phase_voltage'] for m in self.data_with_antenna['measurements']]

        without_antenna_freqs = [m['frequency']/1e6 for m in self.data_without_antenna['measurements']]
        without_antenna_mag = [m['mag_voltage'] for m in self.data_without_antenna['measurements']]
        without_antenna_phase = [m['phase_voltage'] for m in self.data_without_antenna['measurements']]

        # Plot magnitude
        ax1.plot(with_antenna_freqs, with_antenna_mag, 'b-', label='With Antenna', linewidth=2)
        ax1.plot(without_antenna_freqs, without_antenna_mag, 'r-', label='Without Antenna', linewidth=2)
        ax1.set_xlabel('Frequency (MHz)')
        ax1.set_ylabel('Magnitude Voltage (V)')
        ax1.set_title('Magnitude Voltage Comparison')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot phase
        ax2.plot(with_antenna_freqs, with_antenna_phase, 'b-', label='With Antenna', linewidth=2)
        ax2.plot(without_antenna_freqs, without_antenna_phase, 'r-', label='Without Antenna', linewidth=2)
        ax2.set_xlabel('Frequency (MHz)')
        ax2.set_ylabel('Phase Voltage (V)')
        ax2.set_title('Phase Voltage Comparison')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('antenna_data_comparison.png', dpi=300, bbox_inches='tight')
        print("📊 Plot saved as: antenna_data_comparison.png")
        plt.show()

    def generate_report(self):
        """Generate a comprehensive analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"antenna_analysis_report_{timestamp}.txt"

        with open(report_file, 'w') as f:
            f.write("ANTENNA ANALYZER CALIBRATION REPORT\n")
            f.write("="*50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            if self.data_with_antenna:
                f.write("DATA WITH ANTENNA:\n")
                f.write(f"  File: {self.data_with_antenna.get('timestamp', 'Unknown')}\n")
                f.write(f"  Measurements: {len(self.data_with_antenna['measurements'])}\n")
                stats = self.data_with_antenna['statistics']
                f.write(f"  Magnitude range: {stats['mag_voltage']['min']:.3f}V - {stats['mag_voltage']['max']:.3f}V\n")
                f.write(f"  Phase range: {stats['phase_voltage']['min']:.3f}V - {stats['phase_voltage']['max']:.3f}V\n\n")

            if self.data_without_antenna:
                f.write("DATA WITHOUT ANTENNA:\n")
                f.write(f"  File: {self.data_without_antenna.get('timestamp', 'Unknown')}\n")
                f.write(f"  Measurements: {len(self.data_without_antenna['measurements'])}\n")
                stats = self.data_without_antenna['statistics']
                f.write(f"  Magnitude range: {stats['mag_voltage']['min']:.3f}V - {stats['mag_voltage']['max']:.3f}V\n")
                f.write(f"  Phase range: {stats['phase_voltage']['min']:.3f}V - {stats['phase_voltage']['max']:.3f}V\n\n")

            f.write("RECOMMENDATIONS:\n")
            f.write("1. Use the generated calibration code in analyzer.py\n")
            f.write("2. Test the new calibration with your antenna\n")
            f.write("3. Adjust thresholds if needed based on testing\n")
            f.write("4. Consider improving the antenna analyzer circuit if separation is poor\n")

        print(f"📄 Analysis report saved to: {report_file}")

    def run_full_analysis(self):
        """Run complete analysis"""
        print("🔍 Starting comprehensive antenna data analysis...")
        
        self.analyze_voltage_ranges()
        self.suggest_swr_calibration()
        self.analyze_antenna_detection()
        
        if self.data_with_antenna and self.data_without_antenna:
            self.plot_data_comparison()
        
        self.generate_report()
        
        print("\n✅ Analysis completed!")
        print("📁 Check the generated files:")
        print("  - suggested_calibration.py (calibration code)")
        print("  - antenna_data_comparison.png (plot)")
        print("  - antenna_analysis_report_*.txt (full report)")


def main():
    parser = argparse.ArgumentParser(description='Analyze antenna data for calibration')
    parser.add_argument('--with-antenna', type=str, help='JSON file with antenna data')
    parser.add_argument('--without-antenna', type=str, help='JSON file without antenna data')
    parser.add_argument('--auto', action='store_true', help='Auto-find most recent data files')
    parser.add_argument('--plot', action='store_true', help='Show plots')
    
    args = parser.parse_args()
    
    analyzer = AntennaDataAnalyzer()
    
    # Load data
    if args.auto:
        if not analyzer.auto_find_data_files():
            print("❌ No data files found. Run antenna_data_collector.py first.")
            return
    else:
        if not analyzer.load_data(args.with_antenna, args.without_antenna):
            print("❌ Failed to load data files")
            return
    
    # Run analysis
    analyzer.run_full_analysis()
    
    if args.plot and analyzer.data_with_antenna and analyzer.data_without_antenna:
        analyzer.plot_data_comparison()


if __name__ == '__main__':
    main()
