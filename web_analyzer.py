#!/usr/bin/env python3
"""
Web-based Antenna Analyzer
Modern web interface for antenna testing with real-time updates
"""

from flask import Flask, render_template, request, jsonify
import time
import numpy as np
import json
import os
from datetime import datetime
import random
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Import mock hardware for web development
try:
    import RPi.GPIO as GPIO
    import spidev
    MOCK_MODE = False
except ImportError:
    print("Running in mock mode for web development...")
    from mock_hardware import MockGPIO as GPIO, MockSpiDevModule
    spidev = MockSpiDevModule
    MOCK_MODE = True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

class WebAntennaAnalyzer:
    def __init__(self):
        self.W_CLK = 18
        self.FQ_UD = 24
        self.DATA = 23
        self.RESET = 25
        self.ref_voltage = 3.3
        self.adc_resolution = 1024
        self.spi = None
        self.hardware_ready = False
        self.mock_mode = MOCK_MODE
        self.setup_hardware()
    
    def setup_hardware(self):
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup([self.W_CLK, self.FQ_UD, self.DATA, self.RESET], GPIO.OUT)
            GPIO.output([self.W_CLK, self.FQ_UD, self.DATA], GPIO.LOW)
            GPIO.output(self.RESET, GPIO.HIGH)
            
            self.spi = spidev.SpiDev()
            self.spi.open(0, 0)
            self.spi.max_speed_hz = 1000000
            
            self.reset_dds()
            self.hardware_ready = True
            
            if self.mock_mode:
                print("✅ Mock hardware initialized (Web Demo Mode)")
            else:
                print("✅ Real hardware initialized")
        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            self.hardware_ready = False
    
    def reset_dds(self):
        GPIO.output(self.RESET, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(self.RESET, GPIO.LOW)
        time.sleep(0.001)
        GPIO.output(self.RESET, GPIO.HIGH)
    
    def set_frequency(self, freq_hz):
        if not self.hardware_ready:
            return False
        freq_word = int((freq_hz * 4294967296.0) / 125000000.0)
        for i in range(32):
            GPIO.output(self.DATA, (freq_word >> (31-i)) & 1)
            GPIO.output(self.W_CLK, GPIO.HIGH)
            GPIO.output(self.W_CLK, GPIO.LOW)
        for i in range(8):
            GPIO.output(self.DATA, GPIO.LOW)
            GPIO.output(self.W_CLK, GPIO.HIGH)
            GPIO.output(self.W_CLK, GPIO.LOW)
        GPIO.output(self.FQ_UD, GPIO.HIGH)
        GPIO.output(self.FQ_UD, GPIO.LOW)
        return True
    
    def read_adc(self, channel):
        if not self.hardware_ready:
            return 0
        try:
            adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
            data = ((adc[1] & 3) << 8) + adc[2]
            voltage = (data * self.ref_voltage) / self.adc_resolution
            return voltage
        except:
            return 0
    
    def simulate_antenna_response(self, freq_hz):
        resonant_freq = 14.2e6
        bandwidth = 2.0e6
        freq_offset = abs(freq_hz - resonant_freq)
        normalized_offset = freq_offset / bandwidth
        base_swr = 1.1 + 2.0 * (normalized_offset ** 2)
        harmonic_effect = 0.3 * np.sin(freq_hz / 1e6 * 0.5)
        random_variation = random.uniform(-0.1, 0.1)
        swr = base_swr + harmonic_effect + random_variation
        return max(1.0, min(10.0, swr))
    
    def measure_point(self, freq_hz):
        if not self.set_frequency(freq_hz):
            return None
        time.sleep(0.01)
        mag_voltage = self.read_adc(0)
        phase_voltage = self.read_adc(1)
        
        if self.mock_mode:
            swr = self.simulate_antenna_response(freq_hz)
            reflection_coeff = (swr - 1) / (swr + 1)
            mag_db = 20 * np.log10(reflection_coeff + 0.01)
            mag_voltage = 0.9 + mag_db * 0.03
            mag_voltage = max(0.5, min(2.5, mag_voltage))
        else:
            mag_db = (mag_voltage - 0.9) / 0.03
            reflection_coeff = 10 ** (mag_db / 20.0)
            reflection_coeff = min(reflection_coeff, 0.99)
            if reflection_coeff >= 1.0:
                swr = 999
            else:
                swr = (1 + reflection_coeff) / (1 - reflection_coeff)
                swr = min(swr, 50)
        
        return {
            'frequency': freq_hz,
            'swr': swr,
            'mag_voltage': mag_voltage,
            'phase_voltage': phase_voltage
        }
    
    def frequency_sweep(self, start_freq, stop_freq, points=100):
        frequencies = np.linspace(start_freq, stop_freq, points)
        measurements = []
        for i, freq in enumerate(frequencies):
            measurement = self.measure_point(freq)
            if measurement:
                measurements.append(measurement)
            if i % 10 == 0:
                time.sleep(0.001)
        return measurements
    
    def rate_antenna_performance(self, measurements):
        if not measurements:
            return {"rating": "F", "score": 0, "analysis": "No measurements available"}
        
        swr_values = [m['swr'] for m in measurements]
        min_swr = min(swr_values)
        avg_swr = np.mean(swr_values)
        max_swr = max(swr_values)
        
        excellent_points = sum(1 for swr in swr_values if swr <= 1.5)
        good_points = sum(1 for swr in swr_values if swr <= 2.0)
        acceptable_points = sum(1 for swr in swr_values if swr <= 3.0)
        
        total_points = len(swr_values)
        excellent_ratio = excellent_points / total_points
        good_ratio = good_points / total_points
        acceptable_ratio = acceptable_points / total_points
        
        score = 0
        if excellent_ratio >= 0.8:
            score = 90 + (excellent_ratio - 0.8) * 50
        elif good_ratio >= 0.6:
            score = 70 + (good_ratio - 0.6) * 50
        elif acceptable_ratio >= 0.4:
            score = 50 + (acceptable_ratio - 0.4) * 50
        else:
            score = acceptable_ratio * 125
            
        if min_swr <= 1.2:
            score += 5
        elif min_swr <= 1.5:
            score += 2
        if good_ratio >= 0.7:
            score += 3
            
        score = min(100, max(0, score))
        
        if score >= 90: rating = "A+"
        elif score >= 85: rating = "A"
        elif score >= 80: rating = "A-"
        elif score >= 75: rating = "B+"
        elif score >= 70: rating = "B"
        elif score >= 65: rating = "B-"
        elif score >= 60: rating = "C+"
        elif score >= 55: rating = "C"
        elif score >= 50: rating = "C-"
        elif score >= 40: rating = "D"
        else: rating = "F"
        
        analysis = []
        analysis.append(f"Minimum SWR: {min_swr:.2f}")
        analysis.append(f"Average SWR: {avg_swr:.2f}")
        analysis.append(f"Maximum SWR: {max_swr:.2f}")
        analysis.append(f"Excellent (≤1.5): {excellent_points}/{total_points} ({excellent_ratio:.1%})")
        analysis.append(f"Good (≤2.0): {good_points}/{total_points} ({good_ratio:.1%})")
        analysis.append(f"Acceptable (≤3.0): {acceptable_points}/{total_points} ({acceptable_ratio:.1%})")
        
        return {
            "rating": rating,
            "score": score,
            "analysis": "\n".join(analysis),
            "stats": {
                "min_swr": min_swr,
                "avg_swr": avg_swr,
                "max_swr": max_swr,
                "excellent_ratio": excellent_ratio,
                "good_ratio": good_ratio,
                "acceptable_ratio": acceptable_ratio
            }
        }
    
    def cleanup(self):
        if self.hardware_ready:
            GPIO.cleanup()

# Global analyzer instance
analyzer = WebAntennaAnalyzer()

@app.route('/')
def index():
    return render_template('index.html', mock_mode=MOCK_MODE)

@app.route('/api/sweep', methods=['POST'])
def perform_sweep():
    try:
        data = request.get_json()
        start_freq = float(data['start_freq']) * 1e6
        stop_freq = float(data['stop_freq']) * 1e6
        points = int(data['points'])
        
        if start_freq >= stop_freq:
            return jsonify({'error': 'Start frequency must be less than stop frequency'}), 400
        
        if points < 10 or points > 1000:
            return jsonify({'error': 'Points must be between 10 and 1000'}), 400
        
        if not analyzer.hardware_ready:
            return jsonify({'error': 'Hardware not ready. Check connections.'}), 500
        
        start_time = time.time()
        measurements = analyzer.frequency_sweep(start_freq, stop_freq, points)
        sweep_time = time.time() - start_time
        
        rating_result = analyzer.rate_antenna_performance(measurements)
        plot_data = generate_plot(measurements)
        
        return jsonify({
            'success': True,
            'measurements': measurements,
            'rating': rating_result,
            'sweep_time': sweep_time,
            'plot_data': plot_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quick-test', methods=['POST'])
def quick_test():
    try:
        start_freq = 10.0 * 1e6
        stop_freq = 20.0 * 1e6
        points = 25
        
        if not analyzer.hardware_ready:
            return jsonify({'error': 'Hardware not ready. Check connections.'}), 500
        
        start_time = time.time()
        measurements = analyzer.frequency_sweep(start_freq, stop_freq, points)
        sweep_time = time.time() - start_time
        
        rating_result = analyzer.rate_antenna_performance(measurements)
        plot_data = generate_plot(measurements)
        
        return jsonify({
            'success': True,
            'measurements': measurements,
            'rating': rating_result,
            'sweep_time': sweep_time,
            'plot_data': plot_data,
            'parameters': {
                'start_freq': 10.0,
                'stop_freq': 20.0,
                'points': 25
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save', methods=['POST'])
def save_results():
    try:
        data = request.get_json()
        measurements = data['measurements']
        rating = data['rating']
        parameters = data['parameters']
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"antenna_test_{timestamp}.json"
        
        save_data = {
            'timestamp': datetime.now().isoformat(),
            'demo_mode': MOCK_MODE,
            'parameters': parameters,
            'measurements': measurements,
            'rating': rating
        }
        
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    try:
        import glob
        json_files = glob.glob("antenna_test_*.json")
        
        history = []
        for filename in json_files:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                timestamp = data.get('timestamp', 'Unknown')
                if timestamp != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        date_str = timestamp[:19]
                else:
                    date_str = 'Unknown'
                
                params = data.get('parameters', {})
                rating_info = data.get('rating', {})
                
                history.append({
                    'filename': filename,
                    'timestamp': date_str,
                    'start_freq': params.get('start_freq', 'N/A'),
                    'stop_freq': params.get('stop_freq', 'N/A'),
                    'rating': rating_info.get('rating', 'N/A'),
                    'score': rating_info.get('score', 0),
                    'demo_mode': data.get('demo_mode', False)
                })
                
            except Exception as e:
                mod_time = datetime.fromtimestamp(os.path.getmtime(filename))
                date_str = mod_time.strftime('%Y-%m-%d %H:%M:%S')
                history.append({
                    'filename': filename,
                    'timestamp': date_str,
                    'start_freq': 'N/A',
                    'stop_freq': 'N/A',
                    'rating': 'N/A',
                    'score': 0,
                    'demo_mode': False,
                    'error': 'Cannot read file'
                })
        
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load/<filename>')
def load_results(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        measurements = data.get('measurements', [])
        plot_data = generate_plot(measurements) if measurements else None
        
        return jsonify({
            'success': True,
            'data': data,
            'plot_data': plot_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<filename>')
def delete_results(filename):
    try:
        os.remove(filename)
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_plot(measurements):
    if not measurements:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#2a2a2a')
    
    frequencies = [m['frequency'] / 1e6 for m in measurements]
    swr_values = [m['swr'] for m in measurements]
    
    ax.plot(frequencies, swr_values, color='#3b82f6', linewidth=2, label='SWR', alpha=0.9)
    
    ax.axhline(y=1.5, color='#22c55e', linestyle='--', alpha=0.7, linewidth=1.5, label='1.5')
    ax.axhline(y=2.0, color='#f59e0b', linestyle='--', alpha=0.7, linewidth=1.5, label='2.0')
    ax.axhline(y=3.0, color='#ef4444', linestyle='--', alpha=0.7, linewidth=1.5, label='3.0')
    
    min_swr_idx = np.argmin(swr_values)
    ax.plot(frequencies[min_swr_idx], swr_values[min_swr_idx], 
            'o', color='#22c55e', markersize=10, 
            label=f'Min: {swr_values[min_swr_idx]:.2f}')
    
    ax.set_xlabel('Frequency (MHz)', color='#ffffff', fontsize=12)
    ax.set_ylabel('SWR', color='#ffffff', fontsize=12)
    title = 'Antenna SWR vs Frequency'
    if MOCK_MODE:
        title += ' (Demo)'
    ax.set_title(title, color='#ffffff', fontsize=14, fontweight='bold')
    
    ax.grid(True, alpha=0.2, color='#666666')
    ax.legend(facecolor='#1a1a1a', edgecolor='#444444',
              labelcolor='#ffffff', fontsize=10, loc='upper right')
    
    ax.set_ylim(1, min(max(swr_values) * 1.1, 10))
    
    for spine in ax.spines.values():
        spine.set_color('#444444')
    ax.tick_params(colors='#cccccc', labelsize=10)
    
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight', 
                facecolor='#1a1a1a', edgecolor='none')
    img_buffer.seek(0)
    img_data = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close(fig)
    
    return img_data

if __name__ == '__main__':
    print("🌐 Starting Web Antenna Analyzer...")
    print(f"📡 Mode: {'Demo' if MOCK_MODE else 'Hardware'}")
    print("🌍 Server will be available at: http://localhost:5000")
    print("📱 Open in your browser to access the web interface")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        analyzer.cleanup()
    except Exception as e:
        print(f"❌ Error: {e}")
        analyzer.cleanup()
