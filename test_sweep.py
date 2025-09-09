#!/usr/bin/env python3
"""
Simple test to debug the sweep functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analyzer import ModernAntennaAnalyzer
import time

def test_sweep():
    print("Testing antenna analyzer sweep...")
    
    try:
        # Create analyzer
        analyzer = ModernAntennaAnalyzer()
        
        if not analyzer.hardware_ready:
            print("❌ Hardware not ready!")
            return
        
        print("✅ Hardware ready, starting test sweep...")
        
        # Test a small sweep
        start_freq = 10.0e6  # 10 MHz
        stop_freq = 20.0e6   # 20 MHz
        points = 5
        
        print(f"Testing sweep: {start_freq/1e6:.1f} - {stop_freq/1e6:.1f} MHz, {points} points")
        
        def progress_callback(current, total):
            print(f"Progress: {current}/{total}")
        
        measurements = analyzer.frequency_sweep(start_freq, stop_freq, points, progress_callback)
        
        print(f"✅ Sweep completed! Got {len(measurements)} measurements")
        
        if measurements:
            print("\nFirst few measurements:")
            for i, m in enumerate(measurements[:3]):
                print(f"  {i+1}: {m['frequency']/1e6:.1f} MHz, SWR: {m['swr']:.2f}, Mag: {m['mag_voltage']:.3f}V")
            
            # Test rating
            rating = analyzer.rate_antenna_performance(measurements)
            print(f"\nRating: {rating['rating']} ({rating['score']}/100)")
            print(f"Min SWR: {rating['stats']['min_swr']:.2f}")
            print(f"Avg SWR: {rating['stats']['avg_swr']:.2f}")
        else:
            print("❌ No measurements returned!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sweep()
