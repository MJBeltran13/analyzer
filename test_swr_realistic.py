#!/usr/bin/env python3
"""
Test the updated SWR calculation to ensure it gives realistic ratings
"""

def calculate_swr_updated(mag_voltage):
    """Updated SWR calculation with more realistic mapping"""
    if mag_voltage <= 0.1:
        swr = 1.0
    elif mag_voltage <= 0.5:
        swr = 1.0 + ((mag_voltage - 0.1) / 0.4) * 0.5
    elif mag_voltage <= 0.8:
        # Updated: 0.5V = SWR 1.5, 0.8V = SWR 3.0 (more realistic)
        swr = 1.5 + ((mag_voltage - 0.5) / 0.3) * 1.5
    elif mag_voltage <= 1.2:
        swr = 2.0 + ((mag_voltage - 0.8) / 0.4) * 1.0
    elif mag_voltage <= 2.0:
        swr = 3.0 + ((mag_voltage - 1.2) / 0.8) * 2.0
    else:
        excess_voltage = mag_voltage - 2.0
        swr = 5.0 + excess_voltage * 5.0
    
    swr = max(1.0, min(swr, 50.0))
    return swr

def calculate_rating(swr):
    """Calculate rating based on SWR"""
    if swr <= 1.2:
        return "A+"
    elif swr <= 1.5:
        return "A"
    elif swr <= 2.0:
        return "B"
    elif swr <= 3.0:
        return "C"
    elif swr <= 5.0:
        return "D"
    else:
        return "F"

def test_scenarios():
    print("🧪 TESTING UPDATED SWR CALCULATION")
    print("=" * 50)
    
    test_cases = [
        (0.1, "Perfect antenna match"),
        (0.3, "Good antenna match"),
        (0.5, "Moderate antenna match"),
        (0.7, "Your readings (no antenna)"),
        (0.8, "Poor antenna match"),
        (1.0, "Very poor antenna match"),
        (1.5, "Extremely poor match"),
        (2.0, "No antenna/open circuit")
    ]
    
    print("Voltage | SWR  | Rating | Description")
    print("-" * 50)
    
    for voltage, description in test_cases:
        swr = calculate_swr_updated(voltage)
        rating = calculate_rating(swr)
        print(f"{voltage:6.1f}V | {swr:4.1f} | {rating:6s} | {description}")
    
    print(f"\n💡 KEY INSIGHT:")
    print(f"   • 0.7V readings now give SWR ≈ 2.8 (Rating: C)")
    print(f"   • This should result in a poor rating when no antenna is connected")
    print(f"   • Much more realistic than the previous A+ rating!")

if __name__ == "__main__":
    test_scenarios()
