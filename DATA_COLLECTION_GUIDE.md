# Antenna Data Collection Guide

This guide will help you collect data with and without an antenna to calibrate your analyzer.

## Overview

The data collection process involves:
1. **Collecting data WITH antenna connected** - to establish good performance baseline
2. **Collecting data WITHOUT antenna connected** - to establish poor performance baseline  
3. **Analyzing the data** - to generate calibration formulas
4. **Updating analyzer.py** - with the new calibration

## Step 1: Collect Data

### Basic Usage

```bash
# Collect data with antenna connected
python3 antenna_data_collector.py --with-antenna --start 10.0 --stop 20.0 --points 50

# Collect data without antenna connected  
python3 antenna_data_collector.py --without-antenna --start 10.0 --stop 20.0 --points 50

# Collect both datasets in sequence
python3 antenna_data_collector.py --both --start 10.0 --stop 20.0 --points 50
```

### Parameters

- `--start`: Start frequency in MHz (default: 10.0)
- `--stop`: Stop frequency in MHz (default: 20.0)  
- `--points`: Number of measurement points (default: 50)
- `--with-antenna`: Collect data with antenna connected
- `--without-antenna`: Collect data without antenna connected
- `--both`: Collect both datasets
- `--output`: Custom output filename (optional)

### Example Commands

```bash
# Quick test with fewer points
python3 antenna_data_collector.py --both --start 14.0 --stop 14.5 --points 25

# Full range test with more points
python3 antenna_data_collector.py --both --start 1.0 --stop 30.0 --points 100

# Custom output filename
python3 antenna_data_collector.py --both --output my_antenna_test
```

## Step 2: Analyze Data

### Automatic Analysis

```bash
# Auto-find and analyze the most recent data files
python3 analyze_antenna_data.py --auto

# Show plots during analysis
python3 analyze_antenna_data.py --auto --plot
```

### Manual Analysis

```bash
# Analyze specific files
python3 analyze_antenna_data.py --with-antenna antenna_data_with_antenna_20240101_120000.json --without-antenna antenna_data_without_antenna_20240101_120500.json
```

## Step 3: Update Analyzer

The analysis will generate several files:

1. **`suggested_calibration.py`** - New calibration code for analyzer.py
2. **`antenna_data_comparison.png`** - Plot showing data comparison
3. **`antenna_analysis_report_*.txt`** - Detailed analysis report

### Updating analyzer.py

1. Open `suggested_calibration.py` 
2. Copy the calibration code
3. Replace the SWR calculation section in `analyzer.py` (around line 270-300)
4. Test the updated analyzer

## Data Collection Tips

### Before Starting

1. **Ensure hardware is working**: Run `python3 test_ads1115.py` first
2. **Check connections**: Verify all wiring is secure
3. **Stable environment**: Avoid moving cables during collection
4. **Good antenna**: Use a known good antenna for baseline

### During Collection

1. **Follow prompts**: The script will ask you to connect/disconnect antenna
2. **Wait for settling**: Allow a few seconds after connecting antenna
3. **Don't touch**: Avoid moving cables during measurement
4. **Note conditions**: Record any unusual conditions

### Frequency Range Selection

- **Narrow range**: Use 1-2 MHz around antenna resonance for detailed analysis
- **Wide range**: Use full antenna bandwidth for general calibration
- **Multiple ranges**: Collect data for different frequency bands if needed

## Understanding the Results

### Voltage Ranges

The analysis will show typical voltage ranges:
- **WITH antenna**: Lower voltages (better match)
- **WITHOUT antenna**: Higher voltages (poor match)

### Calibration Quality

Good calibration requires:
- **Clear separation**: Different voltage ranges for with/without antenna
- **Consistent readings**: Low standard deviation
- **Reasonable range**: Voltages within 0-3.3V range

### SWR Mapping

The generated calibration maps voltage ranges to SWR values:
- **Low voltage** → Low SWR (good match)
- **High voltage** → High SWR (poor match)

## Troubleshooting

### No Data Files Found

```bash
# Check if files exist
ls antenna_data_*.json

# Run data collection first
python3 antenna_data_collector.py --both
```

### Hardware Errors

```bash
# Test hardware first
python3 test_ads1115.py

# Check I2C devices
i2cdetect -y 1
```

### Poor Separation

If voltage ranges are too similar:
1. Check antenna connection
2. Verify antenna analyzer circuit
3. Try different frequency range
4. Check for loose connections

### Analysis Errors

```bash
# Check file format
python3 -c "import json; print(json.load(open('your_file.json')))"

# Verify data structure
python3 analyze_antenna_data.py --with-antenna your_file.json
```

## Example Workflow

```bash
# 1. Collect data
python3 antenna_data_collector.py --both --start 14.0 --stop 14.5 --points 50

# 2. Analyze data  
python3 analyze_antenna_data.py --auto --plot

# 3. Check results
cat suggested_calibration.py
open antenna_data_comparison.png

# 4. Update analyzer.py with new calibration code

# 5. Test updated analyzer
python3 analyzer.py
```

## Files Generated

### Data Collection
- `antenna_data_with_antenna_YYYYMMDD_HHMMSS.json`
- `antenna_data_without_antenna_YYYYMMDD_HHMMSS.json`

### Analysis
- `suggested_calibration.py` - New calibration code
- `antenna_data_comparison.png` - Data comparison plot
- `antenna_analysis_report_YYYYMMDD_HHMMSS.txt` - Full report

## Next Steps

After updating analyzer.py:
1. Test with known good antenna
2. Test with known poor antenna  
3. Verify SWR readings make sense
4. Fine-tune calibration if needed
5. Document your calibration settings

## Support

If you encounter issues:
1. Check hardware connections
2. Verify I2C communication
3. Review error messages
4. Test with demo analyzer first
5. Check generated log files
