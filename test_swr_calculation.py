#!/usr/bin/env python3
"""
Test script to verify the improved SWR calculation
This script tests the new SWR calculation logic with various voltage inputs
"""

def calculate_swr_original(mag_voltage):
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

def calculate_swr_improved(mag_voltage):
    """Improved SWR calculation that handles actual voltage ranges"""
    if mag_voltage <= 0.1:
        # Very low voltage = perfect match (or no signal)
        swr = 1.0
    elif mag_voltage <= 1.0:
        # Low voltage range: 0.1V = SWR 1.0, 1.0V = SWR 2.0
        swr = 1.0 + ((mag_voltage - 0.1) / 0.9) * 1.0
    elif mag_voltage <= 2.0:
        # Medium voltage range: 1.0V = SWR 2.0, 2.0V = SWR 5.0
        swr = 2.0 + ((mag_voltage - 1.0) / 1.0) * 3.0
    elif mag_voltage <= 3.0:
        # High voltage range: 2.0V = SWR 5.0, 3.0V = SWR 10.0
        swr = 5.0 + ((mag_voltage - 2.0) / 1.0) * 5.0
    else:
        # Very high voltage = extreme mismatch
        excess_voltage = mag_voltage - 3.0
        swr = 10.0 + excess_voltage * 5.0
    
    # Clamp SWR to reasonable range
    swr = max(1.0, min(swr, 50.0))
    return swr

def test_swr_calculations():
    """Test both SWR calculation methods with various voltage inputs"""
    print("🧪 SWR CALCULATION TEST")
    print("=" * 60)
    print(f"{'Voltage (V)':<12} {'Original SWR':<12} {'Improved SWR':<12} {'Difference':<12}")
    print("-" * 60)
    
    test_voltages = [0.0, 0.05, 0.1, 0.2, 0.5, 0.8, 1.0, 1.1, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    
    for voltage in test_voltages:
        swr_orig = calculate_swr_original(voltage)
        swr_improved = calculate_swr_improved(voltage)
        difference = swr_improved - swr_orig
        
        print(f"{voltage:<12.2f} {swr_orig:<12.2f} {swr_improved:<12.2f} {difference:<12.2f}")
    
    print("\n📊 ANALYSIS:")
    print("=" * 60)
    
    # Test with typical low voltage readings (what you're probably seeing)
    low_voltages = [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
    print("Low voltage readings (typical for no antenna or poor connection):")
    for voltage in low_voltages:
        swr_orig = calculate_swr_original(voltage)
        swr_improved = calculate_swr_improved(voltage)
        print(f"  {voltage:.2f}V: Original={swr_orig:.2f}, Improved={swr_improved:.2f}")
    
    print("\n💡 EXPLANATION:")
    print("=" * 60)
    print("• Original method expects voltages 1.0V-1.1V for meaningful SWR readings")
    print("• If your ADC reads <1.0V, original method always returns SWR=1.0")
    print("• Improved method maps 0.1V-3.0V range to SWR 1.0-10.0")
    print("• This provides realistic SWR variation for actual antenna measurements")
    
    print("\n🔧 RECOMMENDATIONS:")
    print("=" * 60)
    print("1. Use the improved SWR calculation (already implemented in analyzer.py)")
    print("2. Check your antenna analyzer circuit connections")
    print("3. Verify an antenna is connected to the analyzer")
    print("4. Use the debug mode to see actual voltage readings during sweeps")

if __name__ == "__main__":
    test_swr_calculations()
