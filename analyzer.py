#!/usr/bin/env python3
"""
Modern Antenna Analyzer - shadcn-inspired Design
Beautiful, modern UI for antenna testing with dark/light themes
"""

# Import real hardware libraries
import RPi.GPIO as GPIO
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os


# Modern color scheme (shadcn-inspired)
class ModernTheme:
    # Dark theme colors
    DARK = {
        'bg_primary': '#09090b',
        'bg_secondary': '#18181b',
        'bg_muted': '#27272a',
        'bg_card': '#0c0c0f',
        'border': '#3f3f46',
        'text_primary': '#fafafa',
        'text_secondary': '#a1a1aa',
        'text_muted': '#71717a',
        'accent': '#3b82f6',
        'accent_hover': '#2563eb',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'gradient_start': '#3b82f6',
        'gradient_end': '#8b5cf6'
    }
    # Light theme colors
    LIGHT = {
        'bg_primary': '#ffffff',
        'bg_secondary': '#f8fafc',
        'bg_muted': '#f1f5f9',
        'bg_card': '#ffffff',
        'border': '#e2e8f0',
        'text_primary': '#0f172a',
        'text_secondary': '#475569',
        'text_muted': '#64748b',
        'accent': '#3b82f6',
        'accent_hover': '#2563eb',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'gradient_start': '#3b82f6',
        'gradient_end': '#8b5cf6'
    }


class ModernAntennaAnalyzer:
    def __init__(self):
        # Hardware configuration (same as before)
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
            GPIO.setmode(GPIO.BCM)
            GPIO.setup([self.W_CLK, self.FQ_UD, self.DATA, self.RESET], GPIO.OUT)
            GPIO.output([self.W_CLK, self.FQ_UD, self.DATA], GPIO.LOW)
            GPIO.output(self.RESET, GPIO.HIGH)

            # Initialize ADS1115 I2C ADC
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

            self.reset_dds()
            print("✅ Real hardware initialized (ADS1115 I2C ADC)")
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
        """Program AD9850 via 3-wire serial: 32-bit FTW + 8-bit control, LSB-first.
        Uses 125 MHz reference clock (no PLL) as in provided Arduino example.
        """
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
        for i in range(5):
            mag_voltage = self.read_adc(0)
            phase_voltage = self.read_adc(1)
            print(f"Sample {i+1}: Magnitude={mag_voltage:.3f}V, Phase={phase_voltage:.3f}V")
            time.sleep(0.1)
        
        print("✅ ADC test completed")



    def measure_point(self, freq_hz):
        if not self.set_frequency(freq_hz):
            return None
        time.sleep(0.01)
        mag_voltage = self.read_adc(0)
        phase_voltage = self.read_adc(1)

        # Calculate SWR from real ADC measurements
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

    def frequency_sweep(self, start_freq, stop_freq, points=100, progress_callback=None):
        frequencies = np.linspace(start_freq, stop_freq, points)
        measurements = []
        for i, freq in enumerate(frequencies):
            measurement = self.measure_point(freq)
            if measurement:
                measurements.append(measurement)
            if progress_callback:
                progress_callback(i + 1, points)
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

        if score >= 90:
            rating = "A+"
        elif score >= 85:
            rating = "A"
        elif score >= 80:
            rating = "A-"
        elif score >= 75:
            rating = "B+"
        elif score >= 70:
            rating = "B"
        elif score >= 65:
            rating = "B-"
        elif score >= 60:
            rating = "C+"
        elif score >= 55:
            rating = "C"
        elif score >= 50:
            rating = "C-"
        elif score >= 40:
            rating = "D"
        else:
            rating = "F"

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


class ModernAntennaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Antenna Analyzer - ADS1115 Hardware")
        self.root.geometry("800x480")   # Target screen
        self.root.resizable(True, True)
        self.root.minsize(640, 400)     # Allow smaller if needed
        try:
            # Slightly reduce Tk scaling for compactness on small screens
            self.root.tk.call('tk', 'scaling', 0.9)
        except Exception:
            pass

        # Theme management
        self.is_dark_mode = True
        self.current_theme = ModernTheme.DARK

        # Configure root styling
        self.setup_modern_styling()

        self.analyzer = ModernAntennaAnalyzer()
        self.measurements = []
        self._compact_buttons = []

        self.setup_modern_gui()

    # ---- Small-screen helpers ----
    def is_small_screen(self):
        try:
            w = self.root.winfo_width()
            h = self.root.winfo_height()
        except Exception:
            w, h = 800, 480
        return (w <= 820 and h <= 500)

    def apply_small_screen_scaling(self):
        # Adjust sweep button padding
        try:
            self.sweep_button.configure(pady=8, padx=16, text="SWEEP")
        except Exception:
            pass

        # Results text compact
        try:
            self.results_text.configure(font=('Consolas', 8), height=6, padx=6, pady=4)
        except Exception:
            pass

        # Rating badge smaller
        try:
            self.rating_badge.configure(font=('Segoe UI', 14, 'bold'), width=3, height=1)
        except Exception:
            pass

        # Slim progress bar
        try:
            self.progress_canvas.config(height=4)
        except Exception:
            pass

        # Slim pagination row button paddings if they exist
        for btn in getattr(self, '_compact_buttons', []):
            try:
                btn.configure(pady=6, padx=10)
            except Exception:
                pass

    # ---- Styling & components ----
    def setup_modern_styling(self):
        """Setup modern styling for the application"""
        self.root.configure(bg=self.current_theme['bg_primary'])
        self.style = ttk.Style()
        self.style.configure('Modern.TButton',
                             background=self.current_theme['accent'],
                             foreground='white',
                             borderwidth=0,
                             focuscolor='none',
                             font=('Segoe UI', 10, 'bold'))
        self.style.map('Modern.TButton',
                       background=[('active', self.current_theme['accent_hover'])])
        self.style.configure('Card.TFrame',
                             background=self.current_theme['bg_card'],
                             borderwidth=1,
                             relief='solid')
        self.style.configure('Modern.TEntry',
                             borderwidth=1,
                             relief='solid',
                             fieldbackground=self.current_theme['bg_muted'],
                             foreground=self.current_theme['text_primary'])

    def create_modern_card(self, parent, title="", padding=10):
        """Create a modern card-style frame"""
        if self.is_small_screen():
            padding = 6
        card = tk.Frame(parent, bg=self.current_theme['bg_card'], relief='solid', bd=1)
        if title:
            title_frame = tk.Frame(card, bg=self.current_theme['bg_card'])
            title_frame.pack(fill='x', padx=padding, pady=(padding, 4))
            title_label = tk.Label(title_frame, text=title,
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=self.current_theme['bg_card'],
                                   fg=self.current_theme['text_primary'])
            title_label.pack(anchor='w')
        content_frame = tk.Frame(card, bg=self.current_theme['bg_card'])
        content_frame.pack(fill='both', expand=True, padx=padding, pady=(0, padding))
        return card, content_frame

    def create_modern_button(self, parent, text, command, style="primary", width=None):
        """Create a modern styled button"""
        if style == "primary":
            bg_color = self.current_theme['accent']
            fg_color = 'white'
            hover_color = self.current_theme['accent_hover']
        elif style == "success":
            bg_color = self.current_theme['success']
            fg_color = 'white'
            hover_color = '#16a34a'
        elif style == "secondary":
            bg_color = self.current_theme['bg_muted']
            fg_color = self.current_theme['text_primary']
            hover_color = self.current_theme['border']
        else:
            bg_color = self.current_theme['accent']
            fg_color = 'white'
            hover_color = self.current_theme['accent_hover']

        btn = tk.Button(parent, text=text, command=command,
                        bg=bg_color, fg=fg_color, border=0, relief='flat',
                        font=('Segoe UI', 10, 'bold'), cursor='hand2', pady=12, padx=24)
        if width:
            btn.configure(width=width)

        def on_enter(e): btn.configure(bg=hover_color)
        def on_leave(e): btn.configure(bg=bg_color)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn



    def setup_modern_gui(self):
        """Setup the modern GUI interface with flexible sizing"""
        main_container = tk.Frame(self.root, bg=self.current_theme['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=3, pady=3)

        self.create_header(main_container)

        # Content area (use grid for tight control on small screens)
        content_area = tk.Frame(main_container, bg=self.current_theme['bg_primary'])
        content_area.pack(fill='both', expand=True, pady=(3, 0))
        content_area.grid_columnconfigure(0, weight=0, minsize=280)  # fixed left column
        content_area.grid_columnconfigure(1, weight=1)               # flexible right column
        content_area.grid_rowconfigure(0, weight=1)

        left_panel = tk.Frame(content_area, bg=self.current_theme['bg_primary'], width=280)
        right_panel = tk.Frame(content_area, bg=self.current_theme['bg_primary'])
        left_panel.grid(row=0, column=0, sticky='ns', padx=(0, 3))
        right_panel.grid(row=0, column=1, sticky='nsew')

        # Setup panels
        self.setup_control_panel(left_panel)
        self.setup_results_panel(left_panel)
        self.setup_plot_panel(right_panel)

        # Navigation buttons that we may compact later
        self._compact_buttons = []

        # Bind resize and apply initial compact scaling if needed
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.after(50, lambda: self.apply_small_screen_scaling() if self.is_small_screen() else None)

    def create_header(self, parent):
        """Create modern header with buttons at the top"""
        header = tk.Frame(parent, bg=self.current_theme['bg_primary'])
        header.pack(fill='x', pady=(0, 2))

        top_row = tk.Frame(header, bg=self.current_theme['bg_primary'])
        top_row.pack(fill='x', pady=(0, 2))

        title_frame = tk.Frame(top_row, bg=self.current_theme['bg_primary'])
        title_frame.pack(side='left')
        title_label = tk.Label(title_frame, text="Antenna Analyzer",
                               font=('Segoe UI', 14, 'bold'),
                               bg=self.current_theme['bg_primary'],
                               fg=self.current_theme['text_primary'])
        title_label.pack(anchor='w')

        subtitle_text = "RF Testing Suite • ADS1115 Hardware"
        subtitle_label = tk.Label(title_frame, text=subtitle_text,
                                  font=('Segoe UI', 8),
                                  bg=self.current_theme['bg_primary'],
                                  fg=self.current_theme['text_secondary'])
        subtitle_label.pack(anchor='w')

        button_frame = tk.Frame(top_row, bg=self.current_theme['bg_primary'])
        button_frame.pack(side='right')
        b1 = self.create_modern_button(button_frame, "Save", self.save_results, "secondary")
        b2 = self.create_modern_button(button_frame, "History", self.show_history, "secondary")
        b3 = self.create_modern_button(button_frame, "Clear", self.clear_results, "secondary")
        b4 = self.create_modern_button(button_frame, "◀ Previous", self.previous_page, "primary")
        b5 = self.create_modern_button(button_frame, "Next ▶", self.next_page, "primary")
        b6 = self.create_modern_button(button_frame, "View", self.view_detailed_results, "success")
        b1.pack(side='left', padx=(0, 3))
        b2.pack(side='left', padx=(0, 3))
        b3.pack(side='left', padx=(0, 3))
        b4.pack(side='left', padx=(0, 3))
        b5.pack(side='left', padx=(0, 3))
        b6.pack(side='left', padx=(0, 3))
        self._compact_buttons += [b1, b2, b3, b4, b5, b6]
        
        # Store references to navigation buttons
        self.prev_button = b4
        self.next_button = b5
        self.view_button = b6

        sweep_row = tk.Frame(header, bg=self.current_theme['bg_primary'])
        sweep_row.pack(fill='x', pady=(0, 2))
        self.sweep_button = self.create_modern_button(sweep_row, "SWEEP", self.one_click_sweep, "primary")
        self.sweep_button.pack(anchor='center')

        self.progress_var = tk.DoubleVar()
        progress_frame = tk.Frame(sweep_row, bg=self.current_theme['bg_primary'])
        progress_frame.pack(fill='x', pady=(3, 0))
        progress_canvas = tk.Canvas(progress_frame, height=6,
                                    bg=self.current_theme['bg_muted'],
                                    highlightthickness=0, relief='flat')
        progress_canvas.pack(fill='x')
        self.progress_canvas = progress_canvas

        self.status_var = tk.StringVar(value="Ready to test - ADS1115 Hardware")
        status_label = tk.Label(sweep_row, textvariable=self.status_var,
                                font=('Segoe UI', 8),
                                bg=self.current_theme['bg_primary'],
                                fg=self.current_theme['text_secondary'])
        status_label.pack(anchor='w', pady=(3, 0))

    def setup_control_panel(self, parent):
        """Setup modern control panel optimized for small screen"""
        control_card, control_content = self.create_modern_card(parent, "Test Parameters")
        control_card.pack(fill='x', pady=(0, 3))

        # Hardware status frame
        hw_frame = tk.Frame(control_content, bg=self.current_theme['bg_muted'], relief='solid', bd=1)
        hw_frame.pack(fill='x', pady=(0, 5))
        hw_label = tk.Label(hw_frame, text="ADS1115 I2C ADC",
                                  font=('Segoe UI', 8, 'bold'),
                                  bg=self.current_theme['bg_muted'],
                                  fg=self.current_theme['success'],
                                  pady=2)
        hw_label.pack()

        freq_frame = tk.Frame(control_content, bg=self.current_theme['bg_card'])
        freq_frame.pack(fill='x', pady=(0, 5))

        start_frame = tk.Frame(freq_frame, bg=self.current_theme['bg_card'])
        start_frame.pack(fill='x', pady=(0, 3))
        tk.Label(start_frame, text="Start (MHz)",
                 font=('Segoe UI', 8, 'bold'),
                 bg=self.current_theme['bg_card'],
                 fg=self.current_theme['text_primary']).pack(anchor='w')
        self.start_freq_var = tk.StringVar(value="10.0")
        start_entry = tk.Entry(start_frame, textvariable=self.start_freq_var,
                               font=('Segoe UI', 9),
                               bg=self.current_theme['bg_muted'],
                               fg=self.current_theme['text_primary'],
                               relief='solid', bd=1)
        start_entry.pack(fill='x', pady=(1, 0))

        stop_frame = tk.Frame(freq_frame, bg=self.current_theme['bg_card'])
        stop_frame.pack(fill='x', pady=(0, 3))
        tk.Label(stop_frame, text="Stop (MHz)",
                 font=('Segoe UI', 8, 'bold'),
                 bg=self.current_theme['bg_card'],
                 fg=self.current_theme['text_primary']).pack(anchor='w')
        self.stop_freq_var = tk.StringVar(value="20.0")
        stop_entry = tk.Entry(stop_frame, textvariable=self.stop_freq_var,
                              font=('Segoe UI', 9),
                              bg=self.current_theme['bg_muted'],
                              fg=self.current_theme['text_primary'],
                              relief='solid', bd=1)
        stop_entry.pack(fill='x', pady=(1, 0))

        points_frame = tk.Frame(freq_frame, bg=self.current_theme['bg_card'])
        points_frame.pack(fill='x')
        tk.Label(points_frame, text="Points",
                 font=('Segoe UI', 8, 'bold'),
                 bg=self.current_theme['bg_card'],
                 fg=self.current_theme['text_primary']).pack(anchor='w')
        self.points_var = tk.StringVar(value="50")
        points_entry = tk.Entry(points_frame, textvariable=self.points_var,
                                font=('Segoe UI', 9),
                                bg=self.current_theme['bg_muted'],
                                fg=self.current_theme['text_primary'],
                                relief='solid', bd=1)
        points_entry.pack(fill='x', pady=(1, 0))

    def setup_results_panel(self, parent):
        """Setup modern results panel with pagination system"""
        results_card, results_content = self.create_modern_card(parent, "Test Results")
        results_card.pack(fill='both', expand=True)

        self.current_page = 0
        self.results_pages = []

        rating_frame = tk.Frame(results_content, bg=self.current_theme['bg_card'])
        rating_frame.pack(fill='x', pady=(0, 8))

        self.rating_var = tk.StringVar(value="--")
        rating_badge = tk.Label(rating_frame, textvariable=self.rating_var,
                                font=('Segoe UI', 18, 'bold'),
                                bg=self.current_theme['success'],
                                fg='white',
                                width=3, height=1)
        rating_badge.pack(side='left', padx=(0, 6))
        self.rating_badge = rating_badge

        score_frame = tk.Frame(rating_frame, bg=self.current_theme['bg_card'])
        score_frame.pack(side='left', fill='x', expand=True)
        self.score_var = tk.StringVar(value="--")
        score_label = tk.Label(score_frame, textvariable=self.score_var,
                               font=('Segoe UI', 11, 'bold'),
                               bg=self.current_theme['bg_card'],
                               fg=self.current_theme['text_primary'])
        score_label.pack(anchor='w')
        score_desc = tk.Label(score_frame, text="Score",
                              font=('Segoe UI', 7),
                              bg=self.current_theme['bg_card'],
                              fg=self.current_theme['text_secondary'])
        score_desc.pack(anchor='w')

        results_frame = tk.Frame(results_content, bg=self.current_theme['bg_muted'], relief='solid', bd=1)
        results_frame.pack(fill='both', expand=True, pady=(0, 3))
        self.results_text = tk.Text(results_frame,
                                    bg=self.current_theme['bg_muted'],
                                    fg=self.current_theme['text_primary'],
                                    font=('Consolas', 8),
                                    relief='flat', bd=1,
                                    wrap='word',
                                    padx=6, pady=3,
                                    height=8,
                                    state='normal')
        self.results_text.pack(fill='both', expand=True)

        pagination_frame = tk.Frame(results_content, bg=self.current_theme['bg_card'])
        pagination_frame.pack(fill='x', pady=(0, 2))

        self.page_info_var = tk.StringVar(value="Page 1 of 1")
        page_info_label = tk.Label(pagination_frame, textvariable=self.page_info_var,
                                   font=('Segoe UI', 7),
                                   bg=self.current_theme['bg_card'],
                                   fg=self.current_theme['text_secondary'])
        page_info_label.pack(side='left')

        button_frame = tk.Frame(pagination_frame, bg=self.current_theme['bg_card'])
        button_frame.pack(side='right')

        self.test_button = self.create_modern_button(button_frame, "Test", self.quick_test, "primary")

        # Keep references for compacting on small screens
        self.test_button.pack(side='left', padx=(0, 2))
        self._compact_buttons += [self.test_button]

        self.results_text.insert(tk.END, "Ready for test results...\n")
        self.results_text.see(tk.END)

    def setup_plot_panel(self, parent):
        """Setup modern plot panel optimized for small screen"""
        plot_card, plot_content = self.create_modern_card(parent, "SWR Analysis")
        plot_card.pack(fill='both', expand=True)

        plt.style.use('dark_background' if self.is_dark_mode else 'default')
        self.fig = Figure(figsize=(8, 6), facecolor=self.current_theme['bg_card'])
        self.ax = self.fig.add_subplot(111)

        # Tight layout for short screens
        self.fig.set_tight_layout(True)
        self.fig.subplots_adjust(top=0.88, bottom=0.18, left=0.12, right=0.97)

        self.ax.set_facecolor(self.current_theme['bg_muted'])
        self.ax.grid(True, alpha=0.2, color=self.current_theme['text_muted'])
        self.ax.set_xlabel('Frequency (MHz)', color=self.current_theme['text_primary'], fontsize=9)
        self.ax.set_ylabel('SWR', color=self.current_theme['text_primary'], fontsize=9)
        self.ax.set_title('Antenna SWR vs Frequency',
                          color=self.current_theme['text_primary'], fontsize=10, fontweight='bold')

        self.canvas = FigureCanvasTkAgg(self.fig, plot_content)
        canvas_widget = self.canvas.get_tk_widget()
        try:
            canvas_widget.configure(bg=self.current_theme['bg_card'], highlightthickness=0, borderwidth=0)
        except Exception:
            pass
        try:
            # Some TkAgg builds expose the underlying tk canvas here
            self.canvas._tkcanvas.configure(bg=self.current_theme['bg_card'], highlightthickness=0, borderwidth=0)
        except Exception:
            pass
        canvas_widget.pack(fill='both', expand=True)
        # Resize plot to fill the card when the widget size changes
        canvas_widget.bind('<Configure>', self._on_plot_resize)

    def _on_plot_resize(self, event=None):
        try:
            widget = self.canvas.get_tk_widget()
            width = max(100, widget.winfo_width())
            height = max(100, widget.winfo_height())
            dpi = self.fig.get_dpi() or 100
            self.fig.set_size_inches(width / dpi, height / dpi, forward=True)
            # Tighten margins to use more space
            self.fig.subplots_adjust(top=0.94, bottom=0.12, left=0.10, right=0.98)
            self.canvas.draw_idle()
        except Exception:
            pass

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.is_dark_mode = not self.is_dark_mode
        self.current_theme = ModernTheme.DARK if self.is_dark_mode else ModernTheme.LIGHT

    def setup_touch_scrolling(self, widget):
        """Setup enhanced touch scrolling like a phone for the given widget"""
        widget.touch_start_y = None
        widget.touch_start_scroll = None
        widget.scroll_sensitivity = 2.0

        def on_touch_start(event):
            widget.touch_start_y = event.y
            widget.touch_start_scroll = widget.yview()[0]
            widget.config(cursor="fleur")
            original_bg = widget.cget("bg")
            widget.config(bg=self.current_theme['bg_secondary'])
            widget.original_bg = original_bg
            return "break"

        def on_touch_move(event):
            if widget.touch_start_y is not None:
                delta_y = (widget.touch_start_y - event.y) * widget.scroll_sensitivity
                current_scroll = widget.touch_start_scroll + (delta_y / widget.winfo_height())
                current_scroll = max(0.0, min(1.0, current_scroll))
                widget.yview_moveto(current_scroll)
                widget.update_idletasks()
            return "break"

        def on_touch_end(event):
            widget.touch_start_y = None
            widget.touch_start_scroll = None
            widget.config(cursor="")
            if hasattr(widget, 'original_bg'):
                widget.config(bg=widget.original_bg)

        def on_mouse_wheel(event):
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_key_scroll(event):
            if event.keysym == 'Up':
                widget.yview_scroll(-1, "units")
            elif event.keysym == 'Down':
                widget.yview_scroll(1, "units")
            elif event.keysym == 'Prior':
                widget.yview_scroll(-1, "pages")
            elif event.keysym == 'Next':
                widget.yview_scroll(1, "pages")
            elif event.keysym == 'Home':
                widget.yview_moveto(0.0)
            elif event.keysym == 'End':
                widget.yview_moveto(1.0)

        widget.bind("<Button-1>", on_touch_start, add="+")
        widget.bind("<B1-Motion>", on_touch_move, add="+")
        widget.bind("<ButtonRelease-1>", on_touch_end, add="+")
        widget.bind("<MouseWheel>", on_mouse_wheel, add="+")
        widget.bind("<Key>", on_key_scroll, add="+")
        widget.config(takefocus=1)
        widget.bind("<B1-Motion>", lambda e: "break", add="+")

    def update_progress(self, current, total):
        """Update modern progress bar"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.progress_canvas.delete("all")
        canvas_width = self.progress_canvas.winfo_width()
        if canvas_width > 1:
            progress_width = (progress / 100) * canvas_width
            self.progress_canvas.create_rectangle(0, 0, progress_width, 6,
                                                  fill=self.current_theme['accent'],
                                                  outline="")
        self.status_var.set(f"Measuring point {current}/{total}")
        self.root.update_idletasks()

    def one_click_sweep(self):
        """Perform complete sweep with modern UI feedback"""
        try:
            start_freq = float(self.start_freq_var.get()) * 1e6
            stop_freq = float(self.stop_freq_var.get()) * 1e6
            points = int(self.points_var.get())

            if start_freq >= stop_freq:
                messagebox.showerror("Error", "Start frequency must be less than stop frequency")
                return
            if points < 10 or points > 1000:
                messagebox.showerror("Error", "Points must be between 10 and 1000")
                return
            if not self.analyzer.hardware_ready:
                messagebox.showerror("Error", "Hardware not ready. Check connections.")
                return

            self.sweep_button.configure(state='disabled', text="Sweeping...")
            self.progress_var.set(0)
            self.status_var.set("Starting sweep...")

            start_time = time.time()
            self.measurements = self.analyzer.frequency_sweep(
                start_freq, stop_freq, points, self.update_progress
            )
            sweep_time = time.time() - start_time

            self.status_var.set("Analyzing results...")
            rating_result = self.analyzer.rate_antenna_performance(self.measurements)

            self.update_modern_results_display(rating_result, sweep_time)
            self.plot_modern_results()

            self.status_var.set(f"✅ Sweep completed in {sweep_time:.1f}s - Rating: {rating_result['rating']}")

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Sweep failed: {e}")
        finally:
            self.sweep_button.configure(state='normal', text="SWEEP")
            self.progress_var.set(0)
            self.progress_canvas.delete("all")

    def update_modern_results_display(self, rating_result, sweep_time):
        """Update results with pagination system"""
        self.rating_var.set(rating_result['rating'])
        self.score_var.set(f"{rating_result['score']:.0f}/100")

        score = rating_result['score']
        if score >= 80:
            self.rating_badge.configure(bg=self.current_theme['success'])
        elif score >= 60:
            self.rating_badge.configure(bg=self.current_theme['warning'])
        else:
            self.rating_badge.configure(bg=self.current_theme['error'])

        self.create_results_pages(rating_result, sweep_time)
        self.current_page = 0
        self.display_current_page()
        self.update_navigation_buttons()

    def create_results_pages(self, rating_result, sweep_time):
        """Create paginated content for results"""
        self.results_pages = []

        page1 = f"ANTENNA PERFORMANCE ANALYSIS\n"
        page1 += f"ADS1115 HARDWARE MODE\n"
        page1 += f"{'='*40}\n\n"
        page1 += f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        page1 += f"Sweep time: {sweep_time:.1f} seconds\n"
        page1 += f"Frequency range: {float(self.start_freq_var.get()):.1f} - {float(self.stop_freq_var.get()):.1f} MHz\n"
        page1 += f"Measurement points: {len(self.measurements)}\n"
        page1 += f"Hardware: ADS1115 I2C ADC\n"
        page1 += f"\nOVERALL RATING: {rating_result['rating']} ({rating_result['score']:.0f}/100)\n\n"
        page1 += "SUMMARY:\n"
        page1 += f"• Minimum SWR: {rating_result['stats']['min_swr']:.2f}\n"
        page1 += f"• Average SWR: {rating_result['stats']['avg_swr']:.2f}\n"
        page1 += f"• Maximum SWR: {rating_result['stats']['max_swr']:.2f}\n"
        page1 += f"• Excellent points (≤1.5): {rating_result['stats']['excellent_ratio']:.1%}\n"
        page1 += f"• Good points (≤2.0): {rating_result['stats']['good_ratio']:.1%}\n"
        page1 += f"• Acceptable points (≤3.0): {rating_result['stats']['acceptable_ratio']:.1%}\n"
        self.results_pages.append(page1)

        page2 = f"DETAILED ANALYSIS\n"
        page2 += f"{'='*40}\n\n"
        page2 += rating_result['analysis'] + "\n\n"
        score = rating_result['score']
        stats = rating_result['stats']
        page2 += "RECOMMENDATIONS:\n"
        page2 += f"{'-'*30}\n"
        if score >= 85:
            page2 += "Excellent antenna performance! No adjustments needed.\n"
        elif score >= 70:
            page2 += "Good antenna performance. Minor tuning could improve bandwidth.\n"
        elif score >= 50:
            page2 += "Acceptable performance. Consider adjusting antenna length or matching network.\n"
        else:
            page2 += "Poor performance. Antenna requires significant adjustment or redesign.\n"
        if stats['min_swr'] > 2.0:
            page2 += "• Check antenna resonance - may need length adjustment\n"
        if stats['good_ratio'] < 0.5:
            page2 += "• Consider adding matching network to improve bandwidth\n"
        if stats['avg_swr'] > 3.0:
            page2 += "• Check all connections and ensure proper grounding\n"
        self.results_pages.append(page2)

        page3 = f"TECHNICAL DETAILS\n"
        page3 += f"{'='*40}\n\n"
        if self.measurements:
            frequencies = [m['frequency'] / 1e6 for m in self.measurements]
            swr_values = [m['swr'] for m in self.measurements]
            min_swr_idx = swr_values.index(min(swr_values))
            min_freq = frequencies[min_swr_idx]
            min_swr = swr_values[min_swr_idx]
            page3 += f"RESONANCE ANALYSIS:\n"
            page3 += f"• Best frequency: {min_freq:.2f} MHz\n"
            page3 += f"• Minimum SWR at resonance: {min_swr:.2f}\n"
            page3 += f"• Frequency range tested: {frequencies[0]:.1f} - {frequencies[-1]:.1f} MHz\n"
            page3 += f"• Total bandwidth tested: {frequencies[-1] - frequencies[0]:.1f} MHz\n\n"
        page3 += f"HARDWARE INFORMATION:\n"
        page3 += f"{'-'*30}\n"
        page3 += "• Using ADS1115 16-bit I2C ADC\n"
        page3 += "• Connected via SDA/SCL pins\n"
        page3 += "• Real-time voltage measurements\n"
        page3 += "• Actual antenna response data\n"
        page3 += "• Professional-grade accuracy\n"
        self.results_pages.append(page3)

    def display_current_page(self):
        """Display the current page of results"""
        if not self.results_pages:
            return
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, self.results_pages[self.current_page])
        self.results_text.see("1.0")
        self.page_info_var.set(f"Page {self.current_page + 1} of {len(self.results_pages)}")

    def next_page(self):
        """Go to next page"""
        if self.current_page < len(self.results_pages) - 1:
            self.current_page += 1
            self.display_current_page()
            self.update_navigation_buttons()

    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Update navigation button states"""
        if not self.results_pages:
            self.prev_button.configure(state='disabled')
            self.next_button.configure(state='disabled')
            self.view_button.configure(state='disabled')
            self.test_button.configure(state='normal')
            return

        self.prev_button.configure(state='normal' if self.current_page > 0 else 'disabled')
        self.next_button.configure(state='normal' if self.current_page < len(self.results_pages) - 1 else 'disabled')
        self.view_button.configure(state='normal')
        self.test_button.configure(state='normal')

    def plot_modern_results(self):
        """Plot results with modern styling optimized for small screen"""
        if not self.measurements:
            return
        frequencies = [m['frequency'] / 1e6 for m in self.measurements]
        swr_values = [m['swr'] for m in self.measurements]

        self.ax.clear()
        self.ax.set_facecolor(self.current_theme['bg_muted'])

        # Make more prominent
        self.fig.subplots_adjust(top=0.96, bottom=0.12, left=0.08, right=0.995)

        # Line
        self.ax.plot(frequencies, swr_values, color=self.current_theme['accent'], linewidth=2.8)
        # Threshold lines
        self.ax.axhline(y=1.5, color=self.current_theme['success'], linestyle='--', alpha=0.8, linewidth=1.6)
        self.ax.axhline(y=2.0, color=self.current_theme['warning'], linestyle='--', alpha=0.8, linewidth=1.6)
        self.ax.axhline(y=3.0, color=self.current_theme['error'], linestyle='--', alpha=0.8, linewidth=1.6)

        # Min point
        try:
            min_idx = swr_values.index(min(swr_values))
            self.ax.plot(frequencies[min_idx], swr_values[min_idx], 'o', color=self.current_theme['success'], markersize=9)
        except Exception:
            pass

        self.ax.set_xlabel('Frequency (MHz)', color=self.current_theme['text_primary'], fontsize=11)
        self.ax.set_ylabel('SWR', color=self.current_theme['text_primary'], fontsize=11)
        title = 'Antenna SWR vs Frequency - ADS1115 Hardware'
        self.ax.set_title(title, color=self.current_theme['text_primary'], fontsize=12, fontweight='bold')
        self.ax.grid(True, alpha=0.25, color=self.current_theme['text_muted'], linewidth=0.8)
        self.ax.set_ylim(1, min(max(swr_values) * 1.1, 10))
        for spine in self.ax.spines.values():
            spine.set_color(self.current_theme['border'])
        self.ax.tick_params(colors=self.current_theme['text_secondary'], labelsize=10)

        self.canvas.draw_idle()

    def on_window_resize(self, event):
        try:
            if self.is_small_screen():
                self.apply_small_screen_scaling()
        except Exception:
            pass

    def clear_results(self):
        try:
            self.measurements = []
            self.results_pages = []
            self.current_page = 0
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Ready for test results...\n")
            self.rating_var.set("--")
            self.score_var.set("--")
            self.update_navigation_buttons()
            self.ax.clear()
            self.canvas.draw_idle()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear: {e}")

    def save_results(self):
        try:
            if not self.measurements:
                messagebox.showinfo("Save", "No results to save.")
                return
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"antenna_test_{timestamp}.json"
            data = {
                'timestamp': datetime.now().isoformat(),
                'hardware_mode': 'ADS1115_I2C_ADC',
                'parameters': {
                    'start_freq': float(self.start_freq_var.get()),
                    'stop_freq': float(self.stop_freq_var.get()),
                    'points': int(self.points_var.get())
                },
                'measurements': self.measurements,
                'rating': {
                    'rating': self.rating_var.get(),
                    'score': int(self.score_var.get().split('/')[0]) if self.score_var.get() != "--" else 0
                }
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Save", f"Saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

    def show_history(self):
        try:
            import glob
            files = sorted(glob.glob("antenna_test_*.json"), reverse=True)
            if not files:
                messagebox.showinfo("History", "No saved results found.")
                return
            hist = tk.Toplevel(self.root)
            hist.title("History")
            hist.geometry("420x320")
            listbox = tk.Listbox(hist)
            listbox.pack(fill='both', expand=True)
            for fn in files:
                listbox.insert(tk.END, fn)
        except Exception as e:
            messagebox.showerror("Error", f"History failed: {e}")

    def view_detailed_results(self):
        try:
            if not self.results_pages:
                messagebox.showinfo("Details", "No results to view.")
                return
            win = tk.Toplevel(self.root)
            win.title("Detailed Results")
            win.geometry("600x400")
            txt = tk.Text(win)
            txt.pack(fill='both', expand=True)
            txt.insert(1.0, "\n\n".join(self.results_pages))
            txt.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Error", f"View failed: {e}")

    def quick_test(self):
        try:
            self.start_freq_var.set("10.0")
            self.stop_freq_var.set("20.0")
            self.points_var.set("25")
            self.one_click_sweep()
        except Exception as e:
            messagebox.showerror("Error", f"Quick test failed: {e}")

if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = ModernAntennaGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Failed to launch GUI: {e}")