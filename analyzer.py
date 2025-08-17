#!/usr/bin/env python3
"""
Modern Antenna Analyzer - shadcn-inspired Design
Beautiful, modern UI for antenna testing with dark/light themes
"""

# Import mock hardware for Windows development
try:
    import RPi.GPIO as GPIO
    import spidev
    MOCK_MODE = False
except ImportError:
    print("Running in mock mode for Windows development...")
    from mock_hardware import MockGPIO as GPIO, MockSpiDevModule
    spidev = MockSpiDevModule
    MOCK_MODE = True

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
import random

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
        """Initialize GPIO and SPI"""
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
                print("✅ Mock hardware initialized (Demo Mode)")
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
        """Simulate realistic antenna response"""
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


class ModernAntennaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Antenna Analyzer" + (" - Demo Mode" if MOCK_MODE else ""))
        self.root.geometry("800x480")
        self.root.resizable(False, False)  # Fixed size, not resizable
        self.root.minsize(800, 480)
        self.root.maxsize(800, 480)
        
        # Theme management
        self.is_dark_mode = True
        self.current_theme = ModernTheme.DARK
        
        # Configure root styling
        self.setup_modern_styling()
        
        self.analyzer = ModernAntennaAnalyzer()
        self.measurements = []
        
        self.setup_modern_gui()
    
    def setup_modern_styling(self):
        """Setup modern styling for the application"""
        self.root.configure(bg=self.current_theme['bg_primary'])
        
        # Configure ttk styles
        self.style = ttk.Style()
        
        # Configure modern button style
        self.style.configure('Modern.TButton',
                           background=self.current_theme['accent'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           font=('Segoe UI', 10, 'bold'))
        self.style.map('Modern.TButton',
                      background=[('active', self.current_theme['accent_hover'])])
        
        # Configure card frame style
        self.style.configure('Card.TFrame',
                           background=self.current_theme['bg_card'],
                           borderwidth=1,
                           relief='solid')
        
        # Configure modern entry style
        self.style.configure('Modern.TEntry',
                           borderwidth=1,
                           relief='solid',
                           fieldbackground=self.current_theme['bg_muted'],
                           foreground=self.current_theme['text_primary'])
    
    def create_modern_card(self, parent, title="", padding=10):
        """Create a modern card-style frame"""
        card = tk.Frame(parent, 
                       bg=self.current_theme['bg_card'],
                       relief='solid',
                       bd=1)
        
        if title:
            title_frame = tk.Frame(card, bg=self.current_theme['bg_card'])
            title_frame.pack(fill='x', padx=padding, pady=(padding, 5))
            
            title_label = tk.Label(title_frame,
                                 text=title,
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
        
        btn = tk.Button(parent,
                       text=text,
                       command=command,
                       bg=bg_color,
                       fg=fg_color,
                       border=0,
                       relief='flat',
                       font=('Segoe UI', 10, 'bold'),
                       cursor='hand2',
                       pady=12,
                       padx=24)
        
        if width:
            btn.configure(width=width)
        
        # Hover effects
        def on_enter(e):
            btn.configure(bg=hover_color)
        def on_leave(e):
            btn.configure(bg=bg_color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def show_demo_info(self):
        """Show modern demo info dialog"""
        demo_window = tk.Toplevel(self.root)
        demo_window.title("Demo Mode")
        demo_window.geometry("500x400")
        demo_window.configure(bg=self.current_theme['bg_primary'])
        demo_window.resizable(False, False)
        
        # Center the window
        demo_window.transient(self.root)
        demo_window.grab_set()
        
        # Header
        header_frame = tk.Frame(demo_window, bg=self.current_theme['bg_primary'])
        header_frame.pack(fill='x', padx=30, pady=(30, 20))
        
        icon_label = tk.Label(header_frame, text="🖥️", font=('Segoe UI', 32),
                            bg=self.current_theme['bg_primary'])
        icon_label.pack()
        
        # Content
        content_frame = tk.Frame(demo_window, bg=self.current_theme['bg_primary'])
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        info_text = """You're running the antenna analyzer in demonstration mode!

This version simulates:
• A realistic antenna response (dipole @ 14.2 MHz)
• Hardware measurements and SWR calculations  
• Complete modern GUI functionality

To run on actual Raspberry Pi hardware:
1. Copy files to Raspberry Pi
2. Install: pip install -r requirements-rpi.txt
3. Run: python3 antenna_tester.py

Try the one-click sweep to see how it works!"""
        
        text_label = tk.Label(content_frame, text=info_text,
                            font=('Segoe UI', 10),
                            bg=self.current_theme['bg_primary'],
                            fg=self.current_theme['text_secondary'],
                            justify='left')
        text_label.pack(anchor='w')
        
        # Button
        btn_frame = tk.Frame(demo_window, bg=self.current_theme['bg_primary'])
        btn_frame.pack(fill='x', padx=30, pady=(0, 30))
        
        ok_btn = self.create_modern_button(btn_frame, "Got it!", demo_window.destroy)
        ok_btn.pack(anchor='e')
    
    def setup_modern_gui(self):
        """Setup the modern GUI interface optimized for 800x480 screen"""
        # Main container - minimal padding for maximum space usage
        main_container = tk.Frame(self.root, bg=self.current_theme['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=3, pady=3)
        
        # Header - more compact
        self.create_header(main_container)
        
        # Content area
        content_area = tk.Frame(main_container, bg=self.current_theme['bg_primary'])
        content_area.pack(fill='both', expand=True, pady=(3, 0))
        
        # Left panel - narrower to give more space to plot
        left_panel = tk.Frame(content_area, bg=self.current_theme['bg_primary'])
        left_panel.pack(side='left', fill='y', padx=(0, 3))
        
        # Right panel (plot) - gets more space
        right_panel = tk.Frame(content_area, bg=self.current_theme['bg_primary'])
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Setup panels
        self.setup_control_panel(left_panel)
        self.setup_results_panel(left_panel)
        self.setup_plot_panel(right_panel)
    
    def create_header(self, parent):
        """Create modern header with buttons at the top"""
        header = tk.Frame(parent, bg=self.current_theme['bg_primary'])
        header.pack(fill='x', pady=(0, 3))
        
        # Top row - Title and action buttons
        top_row = tk.Frame(header, bg=self.current_theme['bg_primary'])
        top_row.pack(fill='x', pady=(0, 5))
        
        # Title section
        title_frame = tk.Frame(top_row, bg=self.current_theme['bg_primary'])
        title_frame.pack(side='left')
        
        title_label = tk.Label(title_frame, text="Antenna Analyzer",
                              font=('Segoe UI', 14, 'bold'),
                              bg=self.current_theme['bg_primary'],
                              fg=self.current_theme['text_primary'])
        title_label.pack(anchor='w')
        
        subtitle_text = "RF Testing Suite"
        if MOCK_MODE:
            subtitle_text += " • Demo"
            
        subtitle_label = tk.Label(title_frame, text=subtitle_text,
                                font=('Segoe UI', 7),
                                bg=self.current_theme['bg_primary'],
                                fg=self.current_theme['text_secondary'])
        subtitle_label.pack(anchor='w')
        
        # Action buttons on the right
        button_frame = tk.Frame(top_row, bg=self.current_theme['bg_primary'])
        button_frame.pack(side='right')
        
        # Create action buttons
        self.create_modern_button(button_frame, "💾 Save", self.save_results, "secondary").pack(side='left', padx=(0, 3))
        self.create_modern_button(button_frame, "📂 History", self.show_history, "secondary").pack(side='left', padx=(0, 3))
        self.create_modern_button(button_frame, "🗑️ Clear", self.clear_results, "secondary").pack(side='left', padx=(0, 3))
        
        # Sweep button row
        sweep_row = tk.Frame(header, bg=self.current_theme['bg_primary'])
        sweep_row.pack(fill='x', pady=(0, 3))
        
        # Sweep button - centered
        self.sweep_button = self.create_modern_button(sweep_row, 
                                                    "🚀 SWEEP",
                                                    self.one_click_sweep,
                                                    "primary")
        self.sweep_button.pack(anchor='center')
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_frame = tk.Frame(sweep_row, bg=self.current_theme['bg_primary'])
        progress_frame.pack(fill='x', pady=(3, 0))
        
        progress_canvas = tk.Canvas(progress_frame, height=6, 
                                  bg=self.current_theme['bg_muted'],
                                  highlightthickness=0, relief='flat')
        progress_canvas.pack(fill='x')
        self.progress_canvas = progress_canvas
        
        # Status
        self.status_var = tk.StringVar(value="Ready to test" + (" - Demo Mode" if MOCK_MODE else ""))
        status_label = tk.Label(sweep_row, textvariable=self.status_var,
                              font=('Segoe UI', 8),
                              bg=self.current_theme['bg_primary'],
                              fg=self.current_theme['text_secondary'])
        status_label.pack(anchor='w', pady=(3, 0))
    
    def setup_control_panel(self, parent):
        """Setup modern control panel optimized for small screen"""
        control_card, control_content = self.create_modern_card(parent, "Test Parameters")
        control_card.pack(fill='x', pady=(0, 3))
        control_card.configure(width=260)
        
        # Demo mode indicator
        if MOCK_MODE:
            demo_frame = tk.Frame(control_content, bg=self.current_theme['bg_muted'],
                                relief='solid', bd=1)
            demo_frame.pack(fill='x', pady=(0, 5))
            
            demo_label = tk.Label(demo_frame, text="🖥️ DEMO",
                                font=('Segoe UI', 7, 'bold'),
                                bg=self.current_theme['bg_muted'],
                                fg=self.current_theme['accent'],
                                pady=2)
            demo_label.pack()
        
        # Frequency inputs - more compact
        freq_frame = tk.Frame(control_content, bg=self.current_theme['bg_card'])
        freq_frame.pack(fill='x', pady=(0, 5))
        
        # Start frequency
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
        
        # Stop frequency
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
        
        # Points
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
        results_card.configure(width=260)
        
        # Initialize pagination variables
        self.current_page = 0
        self.results_pages = []
        
        # Rating display
        rating_frame = tk.Frame(results_content, bg=self.current_theme['bg_card'])
        rating_frame.pack(fill='x', pady=(0, 8))
        
        # Rating badge - smaller
        self.rating_var = tk.StringVar(value="--")
        rating_badge = tk.Label(rating_frame, textvariable=self.rating_var,
                              font=('Segoe UI', 18, 'bold'),
                              bg=self.current_theme['success'],
                              fg='white',
                              width=3, height=1)
        rating_badge.pack(side='left', padx=(0, 6))
        self.rating_badge = rating_badge
        
        # Score info
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
        
        # Results text area - compact for pagination
        results_frame = tk.Frame(results_content, bg=self.current_theme['bg_muted'],
                               relief='solid', bd=1)
        results_frame.pack(fill='both', expand=True, pady=(0, 3))
        
        self.results_text = tk.Text(results_frame,
                                  bg=self.current_theme['bg_muted'],
                                  fg=self.current_theme['text_primary'],
                                  font=('Consolas', 7),
                                  relief='flat', bd=1,
                                  wrap='word',
                                  padx=6, pady=3,
                                  height=8,  # Smaller height for better fit
                                  state='normal')
        self.results_text.pack(fill='both', expand=True)
        
        # Pagination controls
        pagination_frame = tk.Frame(results_content, bg=self.current_theme['bg_card'])
        pagination_frame.pack(fill='x', pady=(0, 3))
        
        # Page info
        self.page_info_var = tk.StringVar(value="Page 1 of 1")
        page_info_label = tk.Label(pagination_frame, textvariable=self.page_info_var,
                                 font=('Segoe UI', 7),
                                 bg=self.current_theme['bg_card'],
                                 fg=self.current_theme['text_secondary'])
        page_info_label.pack(side='left')
        
                # Navigation buttons
        button_frame = tk.Frame(pagination_frame, bg=self.current_theme['bg_card'])
        button_frame.pack(side='right')
        
        self.prev_button = self.create_modern_button(button_frame, "◀", 
                                                    self.previous_page, "secondary")
        self.prev_button.pack(side='left', padx=(0, 2))
        
        self.next_button = self.create_modern_button(button_frame, "Next ▶", 
                                                    self.next_page, "primary")
        self.next_button.pack(side='left', padx=(0, 2))
        
        # View button for detailed results
        self.view_button = self.create_modern_button(button_frame, "👁️ View", 
                                                    self.view_detailed_results, "success")
        self.view_button.pack(side='left')
        
        # Test button for quick test
        self.test_button = self.create_modern_button(button_frame, "🧪 Test", 
                                                    self.quick_test, "primary")
        self.test_button.pack(side='left', padx=(2, 0))
        
        # Initially disable navigation buttons
        self.prev_button.configure(state='disabled')
        self.next_button.configure(state='disabled')
        self.view_button.configure(state='disabled')
        
        # Add initial content
        self.results_text.insert(tk.END, "Ready for test results...\n")
        self.results_text.see(tk.END)
    
    def setup_plot_panel(self, parent):
        """Setup modern plot panel optimized for small screen"""
        plot_card, plot_content = self.create_modern_card(parent, "SWR Analysis")
        plot_card.pack(fill='both', expand=True)
        
        # Modern matplotlib styling
        plt.style.use('dark_background' if self.is_dark_mode else 'default')
        
        # Optimized figure size for 800x480
        self.fig = Figure(figsize=(6.5, 4), facecolor=self.current_theme['bg_card'])
        self.ax = self.fig.add_subplot(111)
        
        # Style the plot
        self.ax.set_facecolor(self.current_theme['bg_muted'])
        self.ax.grid(True, alpha=0.2, color=self.current_theme['text_muted'])
        self.ax.set_xlabel('Frequency (MHz)', color=self.current_theme['text_primary'], fontsize=9)
        self.ax.set_ylabel('SWR', color=self.current_theme['text_primary'], fontsize=9)
        self.ax.set_title('Antenna SWR vs Frequency', 
                         color=self.current_theme['text_primary'], fontsize=10, fontweight='bold')
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, plot_content)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.is_dark_mode = not self.is_dark_mode
        self.current_theme = ModernTheme.DARK if self.is_dark_mode else ModernTheme.LIGHT
        # In a full implementation, you would refresh all styling here
        # For now, just update the button text
        pass
    
    def setup_touch_scrolling(self, widget):
        """Setup enhanced touch scrolling like a phone for the given widget"""
        # Variables to track touch state
        widget.touch_start_y = None
        widget.touch_start_scroll = None
        widget.scroll_sensitivity = 2.0  # More responsive for better scrolling
        
        def on_touch_start(event):
            """Handle touch start (mouse button 1)"""
            widget.touch_start_y = event.y
            widget.touch_start_scroll = widget.yview()[0]
            widget.config(cursor="fleur")  # Show scroll cursor
            
            # Visual feedback - change background slightly
            original_bg = widget.cget("bg")
            widget.config(bg=self.current_theme['bg_secondary'])
            
            # Store original background to restore later
            widget.original_bg = original_bg
            
            # Prevent text selection during scrolling
            return "break"
        
        def on_touch_move(event):
            """Handle touch move (drag)"""
            if widget.touch_start_y is not None:
                # Calculate scroll delta
                delta_y = (widget.touch_start_y - event.y) * widget.scroll_sensitivity
                
                # Get current scroll position
                current_scroll = widget.touch_start_scroll + (delta_y / widget.winfo_height())
                
                # Clamp to valid range
                current_scroll = max(0.0, min(1.0, current_scroll))
                
                # Apply scroll
                widget.yview_moveto(current_scroll)
                
                # Update scrollbar position
                widget.update_idletasks()
            
            # Prevent text selection during scrolling
            return "break"
        
        def on_touch_end(event):
            """Handle touch end"""
            widget.touch_start_y = None
            widget.touch_start_scroll = None
            widget.config(cursor="")  # Reset cursor
            
            # Restore original background
            if hasattr(widget, 'original_bg'):
                widget.config(bg=widget.original_bg)
        
        def on_mouse_wheel(event):
            """Handle mouse wheel for desktop compatibility"""
            # Scroll by 3 lines per wheel unit for better scrolling
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def on_key_scroll(event):
            """Handle keyboard scrolling (arrow keys, page up/down)"""
            if event.keysym == 'Up':
                widget.yview_scroll(-1, "units")
            elif event.keysym == 'Down':
                widget.yview_scroll(1, "units")
            elif event.keysym == 'Prior':  # Page Up
                widget.yview_scroll(-1, "pages")
            elif event.keysym == 'Next':   # Page Down
                widget.yview_scroll(1, "pages")
            elif event.keysym == 'Home':
                widget.yview_moveto(0.0)
            elif event.keysym == 'End':
                widget.yview_moveto(1.0)
        
        # Bind touch events with higher priority
        widget.bind("<Button-1>", on_touch_start, add="+")
        widget.bind("<B1-Motion>", on_touch_move, add="+")
        widget.bind("<ButtonRelease-1>", on_touch_end, add="+")
        
        # Bind mouse wheel for desktop
        widget.bind("<MouseWheel>", on_mouse_wheel, add="+")
        
        # Bind keyboard events for accessibility
        widget.bind("<Key>", on_key_scroll, add="+")
        
        # Make widget focusable for keyboard navigation
        widget.config(takefocus=1)
        
        # Disable text selection on drag to prevent conflicts
        widget.bind("<B1-Motion>", lambda e: "break", add="+")
    
    def update_progress(self, current, total):
        """Update modern progress bar"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        
        # Update canvas progress bar
        self.progress_canvas.delete("all")
        canvas_width = self.progress_canvas.winfo_width()
        if canvas_width > 1:
            progress_width = (progress / 100) * canvas_width
            self.progress_canvas.create_rectangle(0, 0, progress_width, 6,
                                                fill=self.current_theme['accent'],
                                                outline="")
        
        self.status_var.set(f"Measuring point {current}/{total}" + (" (Demo)" if MOCK_MODE else ""))
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
            
            # Disable button and start sweep
            self.sweep_button.configure(state='disabled', text="🔄 Sweeping...")
            self.progress_var.set(0)
            self.status_var.set("Starting sweep..." + (" (Demo)" if MOCK_MODE else ""))
            
            start_time = time.time()
            self.measurements = self.analyzer.frequency_sweep(
                start_freq, stop_freq, points, self.update_progress
            )
            sweep_time = time.time() - start_time
            
            self.status_var.set("Analyzing results..." + (" (Demo)" if MOCK_MODE else ""))
            rating_result = self.analyzer.rate_antenna_performance(self.measurements)
            
            self.update_modern_results_display(rating_result, sweep_time)
            self.plot_modern_results()
            
            self.status_var.set(f"✅ Sweep completed in {sweep_time:.1f}s - Rating: {rating_result['rating']}" + 
                              (" (Demo)" if MOCK_MODE else ""))
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Sweep failed: {e}")
        finally:
            self.sweep_button.configure(state='normal', text="🚀 ONE-CLICK SWEEP & RATE")
            self.progress_var.set(0)
            self.progress_canvas.delete("all")
    
    def update_modern_results_display(self, rating_result, sweep_time):
        """Update results with pagination system"""
        # Update rating badge
        self.rating_var.set(rating_result['rating'])
        self.score_var.set(f"{rating_result['score']:.0f}/100")
        
        # Update badge color based on score
        score = rating_result['score']
        if score >= 80:
            self.rating_badge.configure(bg=self.current_theme['success'])
        elif score >= 60:
            self.rating_badge.configure(bg=self.current_theme['warning'])
        else:
            self.rating_badge.configure(bg=self.current_theme['error'])
        
        # Create paginated content
        self.create_results_pages(rating_result, sweep_time)
        
        # Display first page
        self.current_page = 0
        self.display_current_page()
        
        # Update navigation buttons
        self.update_navigation_buttons()
    
    def create_results_pages(self, rating_result, sweep_time):
        """Create paginated content for results"""
        self.results_pages = []
        
        # Page 1: Overview and Summary
        page1 = f"ANTENNA PERFORMANCE ANALYSIS\n"
        if MOCK_MODE:
            page1 += f"🖥️ DEMO MODE - Simulated Results\n"
        page1 += f"{'='*40}\n\n"
        page1 += f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        page1 += f"Sweep time: {sweep_time:.1f} seconds\n"
        page1 += f"Frequency range: {float(self.start_freq_var.get()):.1f} - {float(self.stop_freq_var.get()):.1f} MHz\n"
        page1 += f"Measurement points: {len(self.measurements)}\n"
        if MOCK_MODE:
            page1 += f"Simulated antenna: Dipole (resonant at ~14.2 MHz)\n"
        page1 += f"\nOVERALL RATING: {rating_result['rating']} ({rating_result['score']:.0f}/100)\n\n"
        page1 += "SUMMARY:\n"
        page1 += f"• Minimum SWR: {rating_result['stats']['min_swr']:.2f}\n"
        page1 += f"• Average SWR: {rating_result['stats']['avg_swr']:.2f}\n"
        page1 += f"• Maximum SWR: {rating_result['stats']['max_swr']:.2f}\n"
        page1 += f"• Excellent points (≤1.5): {rating_result['stats']['excellent_ratio']:.1%}\n"
        page1 += f"• Good points (≤2.0): {rating_result['stats']['good_ratio']:.1%}\n"
        page1 += f"• Acceptable points (≤3.0): {rating_result['stats']['acceptable_ratio']:.1%}\n"
        
        self.results_pages.append(page1)
        
        # Page 2: Detailed Analysis
        page2 = f"DETAILED ANALYSIS\n"
        page2 += f"{'='*40}\n\n"
        page2 += rating_result['analysis'] + "\n\n"
        
        # Add recommendations based on score
        score = rating_result['score']
        stats = rating_result['stats']
        
        page2 += "RECOMMENDATIONS:\n"
        page2 += f"{'-'*30}\n"
        
        if score >= 85:
            page2 += "✅ Excellent antenna performance! No adjustments needed.\n"
        elif score >= 70:
            page2 += "✅ Good antenna performance. Minor tuning could improve bandwidth.\n"
        elif score >= 50:
            page2 += "⚠️ Acceptable performance. Consider adjusting antenna length or matching network.\n"
        else:
            page2 += "❌ Poor performance. Antenna requires significant adjustment or redesign.\n"
        
        if stats['min_swr'] > 2.0:
            page2 += "• Check antenna resonance - may need length adjustment\n"
        
        if stats['good_ratio'] < 0.5:
            page2 += "• Consider adding matching network to improve bandwidth\n"
        
        if stats['avg_swr'] > 3.0:
            page2 += "• Check all connections and ensure proper grounding\n"
        
        self.results_pages.append(page2)
        
        # Page 3: Technical Details and Demo Info
        page3 = f"TECHNICAL DETAILS\n"
        page3 += f"{'='*40}\n\n"
        
        # Add frequency analysis
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
        
        if MOCK_MODE:
            page3 += f"DEMO MODE INFORMATION:\n"
            page3 += f"{'-'*30}\n"
            page3 += "• This simulates a realistic dipole antenna\n"
            page3 += "• Try different frequency ranges to see varying results\n"
            page3 += "• The 10-20 MHz range shows good performance\n"
            page3 += "• Real hardware will show actual antenna measurements\n"
            page3 += "• Simulated resonance at ~14.2 MHz\n"
        
        self.results_pages.append(page3)
    
    def display_current_page(self):
        """Display the current page of results"""
        if not self.results_pages:
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, self.results_pages[self.current_page])
        self.results_text.see("1.0")  # Scroll to top
        
        # Update page info
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
            self.test_button.configure(state='normal')  # Test button always enabled
            return
        
        # Enable/disable previous button
        if self.current_page > 0:
            self.prev_button.configure(state='normal')
        else:
            self.prev_button.configure(state='disabled')
        
        # Enable/disable next button
        if self.current_page < len(self.results_pages) - 1:
            self.next_button.configure(state='normal')
        else:
            self.next_button.configure(state='disabled')
        
        # Enable/disable view button (always enabled when there are results)
        self.view_button.configure(state='normal')
        
        # Test button is always enabled
        self.test_button.configure(state='normal')
    
    def plot_modern_results(self):
        """Plot results with modern styling optimized for small screen"""
        if not self.measurements:
            return
        
        frequencies = [m['frequency'] / 1e6 for m in self.measurements]
        swr_values = [m['swr'] for m in self.measurements]
        
        self.ax.clear()
        
        # Modern plot styling
        self.ax.set_facecolor(self.current_theme['bg_muted'])
        
        # Main SWR line with modern styling - thinner for small screen
        self.ax.plot(frequencies, swr_values, color=self.current_theme['accent'], 
                    linewidth=2, label='SWR', alpha=0.9)
        
        # Reference lines with modern colors - shorter labels
        self.ax.axhline(y=1.5, color=self.current_theme['success'], 
                       linestyle='--', alpha=0.7, linewidth=1.5, label='1.5')
        self.ax.axhline(y=2.0, color=self.current_theme['warning'], 
                       linestyle='--', alpha=0.7, linewidth=1.5, label='2.0')
        self.ax.axhline(y=3.0, color=self.current_theme['error'], 
                       linestyle='--', alpha=0.7, linewidth=1.5, label='3.0')
        
        # Highlight minimum SWR point - smaller marker
        min_swr_idx = np.argmin(swr_values)
        self.ax.plot(frequencies[min_swr_idx], swr_values[min_swr_idx], 
                    'o', color=self.current_theme['success'], markersize=8, 
                    label=f'Min: {swr_values[min_swr_idx]:.2f}')
        
        # Styling - smaller fonts
        self.ax.set_xlabel('Frequency (MHz)', color=self.current_theme['text_primary'], fontsize=10)
        self.ax.set_ylabel('SWR', color=self.current_theme['text_primary'], fontsize=10)
        title = 'Antenna SWR vs Frequency'
        if MOCK_MODE:
            title += ' (Demo)'
        self.ax.set_title(title, color=self.current_theme['text_primary'], 
                         fontsize=11, fontweight='bold')
        
        self.ax.grid(True, alpha=0.2, color=self.current_theme['text_muted'])
        self.ax.legend(facecolor=self.current_theme['bg_card'], 
                      edgecolor=self.current_theme['border'],
                      labelcolor=self.current_theme['text_primary'],
                      fontsize=8, loc='upper right')
        
        # Set limits
        self.ax.set_ylim(1, min(max(swr_values) * 1.1, 10))
        
        # Style spines
        for spine in self.ax.spines.values():
            spine.set_color(self.current_theme['border'])
        self.ax.tick_params(colors=self.current_theme['text_secondary'], labelsize=8)
        
        self.canvas.draw()
    
    def quick_test(self):
        """Perform a quick test with default parameters"""
        try:
            # Set default parameters for quick test
            self.start_freq_var.set("10.0")
            self.stop_freq_var.set("20.0")
            self.points_var.set("25")
            
            # Perform the sweep
            self.one_click_sweep()
            
        except Exception as e:
            messagebox.showerror("Error", f"Quick test failed: {e}")
    
    def view_detailed_results(self):
        """Show detailed results in a larger window"""
        if not self.results_pages:
            messagebox.showwarning("Warning", "No results to view")
            return
        
        # Create detailed results window
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Detailed Test Results")
        detail_window.geometry("700x500")
        detail_window.configure(bg=self.current_theme['bg_primary'])
        detail_window.resizable(True, True)
        detail_window.transient(self.root)
        detail_window.grab_set()
        
        # Header
        header_frame = tk.Frame(detail_window, bg=self.current_theme['bg_primary'])
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = tk.Label(header_frame, text="📊 Detailed Test Results",
                             font=('Segoe UI', 16, 'bold'),
                             bg=self.current_theme['bg_primary'],
                             fg=self.current_theme['text_primary'])
        title_label.pack(anchor='w')
        
        # Rating display
        rating_frame = tk.Frame(header_frame, bg=self.current_theme['bg_primary'])
        rating_frame.pack(anchor='w', pady=(10, 0))
        
        rating_badge = tk.Label(rating_frame, text=self.rating_var.get(),
                              font=('Segoe UI', 24, 'bold'),
                              bg=self.rating_badge.cget('bg'),
                              fg='white',
                              width=4, height=1)
        rating_badge.pack(side='left', padx=(0, 15))
        
        score_label = tk.Label(rating_frame, text=f"Score: {self.score_var.get()}",
                             font=('Segoe UI', 14, 'bold'),
                             bg=self.current_theme['bg_primary'],
                             fg=self.current_theme['text_primary'])
        score_label.pack(side='left')
        
        # Content area with scrollbar
        content_frame = tk.Frame(detail_window, bg=self.current_theme['bg_primary'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create scrollable text area
        text_frame = tk.Frame(content_frame, bg=self.current_theme['bg_muted'], relief='solid', bd=1)
        text_frame.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame,
                               width=20,
                               troughcolor=self.current_theme['bg_muted'],
                               bg=self.current_theme['accent'],
                               activebackground=self.current_theme['accent_hover'],
                               relief='flat',
                               bd=0)
        scrollbar.pack(side='right', fill='y')
        
        # Detailed text widget
        detail_text = tk.Text(text_frame,
                            bg=self.current_theme['bg_muted'],
                            fg=self.current_theme['text_primary'],
                            font=('Consolas', 10),
                            relief='flat', bd=0,
                            wrap='word',
                            padx=15, pady=15,
                            yscrollcommand=scrollbar.set)
        detail_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=detail_text.yview)
        
        # Combine all pages into one detailed view
        all_content = "DETAILED ANTENNA ANALYSIS REPORT\n"
        all_content += "=" * 60 + "\n\n"
        
        for i, page in enumerate(self.results_pages):
            all_content += f"PAGE {i+1}:\n"
            all_content += "-" * 40 + "\n"
            all_content += page + "\n\n"
        
        # Add additional detailed information
        if self.measurements:
            all_content += "RAW MEASUREMENT DATA:\n"
            all_content += "-" * 40 + "\n"
            all_content += f"Total measurements: {len(self.measurements)}\n"
            all_content += f"Frequency range: {self.measurements[0]['frequency']/1e6:.2f} - {self.measurements[-1]['frequency']/1e6:.2f} MHz\n\n"
            
            # Show first 10 and last 10 measurements
            all_content += "First 10 measurements:\n"
            for i, m in enumerate(self.measurements[:10]):
                all_content += f"  {i+1:2d}. {m['frequency']/1e6:6.2f} MHz: SWR = {m['swr']:.3f}\n"
            
            if len(self.measurements) > 20:
                all_content += f"  ... ({len(self.measurements)-20} more measurements) ...\n"
            
            all_content += "\nLast 10 measurements:\n"
            for i, m in enumerate(self.measurements[-10:]):
                all_content += f"  {len(self.measurements)-9+i:2d}. {m['frequency']/1e6:6.2f} MHz: SWR = {m['swr']:.3f}\n"
        
        detail_text.insert(tk.END, all_content)
        detail_text.config(state='disabled')  # Make read-only
        
        # Buttons
        button_frame = tk.Frame(detail_window, bg=self.current_theme['bg_primary'])
        button_frame.pack(fill='x', padx=20, pady=(10, 20))
        
        # Copy button
        copy_btn = self.create_modern_button(button_frame, "📋 Copy", 
                                           lambda: self.copy_to_clipboard(all_content))
        copy_btn.pack(side='left', padx=(0, 10))
        
        # Print button
        print_btn = self.create_modern_button(button_frame, "🖨️ Print", 
                                            lambda: self.print_results(detail_window))
        print_btn.pack(side='left', padx=(0, 10))
        
        # Close button
        close_btn = self.create_modern_button(button_frame, "✖️ Close", 
                                            detail_window.destroy, "secondary")
        close_btn.pack(side='right')
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Success", "Results copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
    
    def print_results(self, parent_window):
        """Print results (simulated)"""
        messagebox.showinfo("Print", "Print functionality would open system print dialog.\n\nIn a real implementation, this would format the results for printing.")
    
    def save_results(self):
        """Save results with modern feedback"""
        if not self.measurements:
            messagebox.showwarning("Warning", "No measurements to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"antenna_test_{timestamp}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'demo_mode': MOCK_MODE,
            'parameters': {
                'start_freq_mhz': float(self.start_freq_var.get()),
                'stop_freq_mhz': float(self.stop_freq_var.get()),
                'points': int(self.points_var.get())
            },
            'measurements': self.measurements,
            'rating': self.analyzer.rate_antenna_performance(self.measurements)
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Success", f"Results saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {e}")
    
    def show_history(self):
        """Show history of saved test results"""
        # Find all antenna test JSON files
        import glob
        json_files = glob.glob("antenna_test_*.json")
        
        if not json_files:
            messagebox.showinfo("History", "No previous test results found.")
            return
        
        # Sort files by modification time (newest first)
        json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Create history window - smaller for 800x480
        history_window = tk.Toplevel(self.root)
        history_window.title("Test History")
        history_window.geometry("600x400")
        history_window.configure(bg=self.current_theme['bg_primary'])
        history_window.transient(self.root)
        history_window.grab_set()
        
        # Header - smaller fonts
        header_frame = tk.Frame(history_window, bg=self.current_theme['bg_primary'])
        header_frame.pack(fill='x', padx=15, pady=(15, 8))
        
        title_label = tk.Label(header_frame, text="📂 Test History",
                             font=('Segoe UI', 14, 'bold'),
                             bg=self.current_theme['bg_primary'],
                             fg=self.current_theme['text_primary'])
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(header_frame, text=f"Found {len(json_files)} previous test(s)",
                                font=('Segoe UI', 9),
                                bg=self.current_theme['bg_primary'],
                                fg=self.current_theme['text_secondary'])
        subtitle_label.pack(anchor='w')
        
        # Main content frame
        content_frame = tk.Frame(history_window, bg=self.current_theme['bg_primary'])
        content_frame.pack(fill='both', expand=True, padx=15, pady=8)
        
        # Create scrollable list
        list_frame = tk.Frame(content_frame, bg=self.current_theme['bg_card'], relief='solid', bd=1)
        list_frame.pack(fill='both', expand=True)
        
        # Touch-friendly scrollbar
        scrollbar = tk.Scrollbar(list_frame,
                               width=20,  # Wider for touch
                               troughcolor=self.current_theme['bg_card'],
                               bg=self.current_theme['border'],
                               activebackground=self.current_theme['accent'],
                               relief='flat',
                               bd=0)
        scrollbar.pack(side='right', fill='y')
        
        # Listbox with custom styling - smaller font
        self.history_listbox = tk.Listbox(list_frame,
                                        bg=self.current_theme['bg_card'],
                                        fg=self.current_theme['text_primary'],
                                        selectbackground=self.current_theme['accent'],
                                        selectforeground='white',
                                        font=('Consolas', 8),
                                        relief='flat',
                                        yscrollcommand=scrollbar.set)
        self.history_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.history_listbox.yview)
        
        # Add touch scrolling support
        self.setup_touch_scrolling(self.history_listbox)
        
        # Populate list with test summaries
        self.history_files = []
        for filename in json_files:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                # Extract key information
                timestamp = data.get('timestamp', 'Unknown')
                if timestamp != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        date_str = timestamp[:19]  # Take first 19 chars
                else:
                    date_str = 'Unknown'
                
                params = data.get('parameters', {})
                rating_info = data.get('rating', {})
                
                start_freq = params.get('start_freq_mhz', 'N/A')
                stop_freq = params.get('stop_freq_mhz', 'N/A')
                rating = rating_info.get('rating', 'N/A')
                score = rating_info.get('score', 0)
                
                demo_mode = data.get('demo_mode', False)
                demo_text = " [DEMO]" if demo_mode else ""
                
                # Format list entry
                entry_text = f"{date_str} | {start_freq}-{stop_freq} MHz | Rating: {rating} ({score:.0f}/100){demo_text}"
                self.history_listbox.insert(tk.END, entry_text)
                self.history_files.append(filename)
                
            except Exception as e:
                # If file is corrupted, show basic info
                mod_time = datetime.fromtimestamp(os.path.getmtime(filename))
                date_str = mod_time.strftime('%Y-%m-%d %H:%M:%S')
                entry_text = f"{date_str} | {filename} | [ERROR: Cannot read file]"
                self.history_listbox.insert(tk.END, entry_text)
                self.history_files.append(filename)
        
        # Buttons frame
        button_frame = tk.Frame(history_window, bg=self.current_theme['bg_primary'])
        button_frame.pack(fill='x', padx=15, pady=(8, 15))
        
        # Load button - shorter text
        load_btn = self.create_modern_button(button_frame, "📖 Load", 
                                           lambda: self.load_history_file(history_window))
        load_btn.pack(side='left', padx=(0, 5))
        
        # Delete button - shorter text
        delete_btn = self.create_modern_button(button_frame, "🗑️ Delete", 
                                             lambda: self.delete_history_file(history_window), "secondary")
        delete_btn.pack(side='left', padx=(0, 5))
        
        # Close button
        close_btn = self.create_modern_button(button_frame, "✖️ Close", history_window.destroy, "secondary")
        close_btn.pack(side='right')
        
        # Double-click to load
        self.history_listbox.bind('<Double-1>', lambda e: self.load_history_file(history_window))
    
    def load_history_file(self, history_window):
        """Load selected history file"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a test to load.")
            return
        
        filename = self.history_files[selection[0]]
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Load measurements
            self.measurements = data.get('measurements', [])
            
            # Update parameters
            params = data.get('parameters', {})
            self.start_freq_var.set(str(params.get('start_freq_mhz', '1.0')))
            self.stop_freq_var.set(str(params.get('stop_freq_mhz', '30.0')))
            self.points_var.set(str(params.get('points', '100')))
            
            # Update display
            rating_result = data.get('rating', {})
            if rating_result:
                # Calculate sweep time (approximate)
                sweep_time = len(self.measurements) * 0.01
                self.update_modern_results_display(rating_result, sweep_time)
                self.plot_modern_results()
                
                # Update status
                timestamp = data.get('timestamp', 'Unknown')
                if timestamp != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        date_str = timestamp[:16]
                else:
                    date_str = 'Unknown'
                
                self.status_var.set(f"📂 Loaded test from {date_str} - Rating: {rating_result.get('rating', 'N/A')}")
            
            history_window.destroy()
            messagebox.showinfo("Success", f"Loaded test results from {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file {filename}:\n{e}")
    
    def delete_history_file(self, history_window):
        """Delete selected history file"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a test to delete.")
            return
        
        filename = self.history_files[selection[0]]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {filename}?"):
            try:
                os.remove(filename)
                messagebox.showinfo("Success", f"Deleted {filename}")
                history_window.destroy()
                # Refresh history window
                self.show_history()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {filename}:\n{e}")
    
    def clear_results(self):
        """Clear results with modern styling"""
        self.measurements = []
        self.rating_var.set("--")
        self.score_var.set("--")
        self.rating_badge.configure(bg=self.current_theme['bg_muted'])
        
        # Clear pagination
        self.results_pages = []
        self.current_page = 0
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Ready for test results...\n")
        self.page_info_var.set("Page 1 of 1")
        
        # Disable navigation buttons
        self.prev_button.configure(state='disabled')
        self.next_button.configure(state='disabled')
        self.view_button.configure(state='disabled')
        self.test_button.configure(state='normal')  # Test button always enabled
        
        self.ax.clear()
        self.ax.set_facecolor(self.current_theme['bg_muted'])
        self.ax.set_xlabel('Frequency (MHz)', color=self.current_theme['text_primary'], fontsize=10)
        self.ax.set_ylabel('SWR', color=self.current_theme['text_primary'], fontsize=10)
        title = 'Antenna SWR vs Frequency'
        if MOCK_MODE:
            title += ' (Demo)'
        self.ax.set_title(title, color=self.current_theme['text_primary'], fontsize=11, fontweight='bold')
        self.ax.grid(True, alpha=0.2, color=self.current_theme['text_muted'])
        self.ax.set_ylim(1, 10)
        
        for spine in self.ax.spines.values():
            spine.set_color(self.current_theme['border'])
        self.ax.tick_params(colors=self.current_theme['text_secondary'], labelsize=8)
        
        self.canvas.draw()
        self.status_var.set("Ready to test" + (" - Demo Mode" if MOCK_MODE else ""))
    
    def on_closing(self):
        """Handle application closing"""
        self.analyzer.cleanup()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ModernAntennaGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main() 