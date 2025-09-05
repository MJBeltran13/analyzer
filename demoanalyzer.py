#!/usr/bin/env python3
"""
Antenna Analyzer

Generates random measurements across 10–40 MHz for demonstration
purposes. No hardware required.
"""

import random
import time
import json
from datetime import datetime
from typing import List, Dict

# Optional GUI/plot imports will be attempted later to allow headless usage


def generate_frequency_points(start_mhz: float, stop_mhz: float, points: int) -> List[float]:
    if points < 2:
        return [start_mhz, stop_mhz]
    step = (stop_mhz - start_mhz) / (points - 1)
    return [start_mhz + i * step for i in range(points)]


class Analyzer:
    def __init__(self, start_mhz: float = 10.0, stop_mhz: float = 40.0, points: int = 100):
        self.start_mhz = float(start_mhz)
        self.stop_mhz = float(stop_mhz)
        self.points = int(points)
        if self.start_mhz >= self.stop_mhz:
            raise ValueError("start_mhz must be less than stop_mhz")
        if self.points < 10 or self.points > 2000:
            raise ValueError("points must be between 10 and 2000")

        # Create one or two "resonance" dips across the band for realism
        self.num_resonances = 1 if random.random() < 0.6 else 2
        self.resonance_centers = [
            random.uniform(self.start_mhz + 2, self.stop_mhz - 2)
            for _ in range(self.num_resonances)
        ]
        self.resonance_widths = [random.uniform(0.8, 3.0) for _ in range(self.num_resonances)]

    def _voltage_pair(self, freq_mhz: float) -> Dict[str, float]:
        # Produce pseudo-random but smooth-ish voltages in 0.0–3.3 V
        base = 1.6 + 0.2 * random.uniform(-1, 1)
        mag = max(0.0, min(3.3, base + 0.5 * random.uniform(-1, 1)))
        phase = max(0.0, min(3.3, base + 0.5 * random.uniform(-1, 1)))
        return {"mag_voltage": mag, "phase_voltage": phase}

    def _swr(self, freq_mhz: float) -> float:
        # Build an SWR curve with one or two dips
        swr = 3.5  # baseline
        for center, width in zip(self.resonance_centers, self.resonance_widths):
            # Gaussian-like dip
            dx = (freq_mhz - center) / max(0.001, width)
            dip = 2.8 * (2.71828 ** (-(dx * dx)))  # up to ~2.8 reduction
            swr = max(1.05, swr - dip)
        # Add a small noise component
        swr += random.uniform(-0.05, 0.05)
        return max(1.0, min(10.0, swr))

    def run_sweep(self) -> List[Dict[str, float]]:
        freqs_mhz = generate_frequency_points(self.start_mhz, self.stop_mhz, self.points)
        results: List[Dict[str, float]] = []
        for f_mhz in freqs_mhz:
            v = self._voltage_pair(f_mhz)
            swr = self._swr(f_mhz)
            results.append(
                {
                    "frequency": f_mhz * 1e6,
                    "swr": swr,
                    "mag_voltage": v["mag_voltage"],
                    "phase_voltage": v["phase_voltage"],
                }
            )
            # Light delay to simulate work
            time.sleep(0.002)
        return results

    @staticmethod
    def rate_antenna_performance(measurements: List[Dict[str, float]]) -> Dict:
        print(f"DEBUG: rate_antenna_performance called with {len(measurements)} measurements")
        if not measurements:
            print("DEBUG: No measurements, returning default")
            return {"rating": "F", "score": 0, "min_swr": 0.0, "avg_swr": 0.0}
        
        print("DEBUG: Extracting SWR values...")
        swrs = [m["swr"] for m in measurements]
        print(f"DEBUG: SWR values: {swrs[:5]}... (showing first 5)")
        print(f"DEBUG: SWR types: {[type(s) for s in swrs[:5]]}")
        
        min_swr = min(swrs)
        avg_swr = sum(swrs) / len(swrs)
        good_ratio = sum(1 for x in swrs if x <= 2.0) / len(swrs)
        print(f"DEBUG: min_swr: {min_swr}, avg_swr: {avg_swr}, good_ratio: {good_ratio}")
        
        score = 0
        if min_swr <= 1.3:
            score += 35
        elif min_swr <= 1.7:
            score += 25
        elif min_swr <= 2.0:
            score += 15
        score += int(max(0, (2.5 - avg_swr) * 15))
        score += int(good_ratio * 40)
        score = max(0, min(100, score))
        print(f"DEBUG: Calculated score: {score}")
        
        if score >= 90:
            rating = "A+"
        elif score >= 80:
            rating = "A"
        elif score >= 70:
            rating = "B"
        elif score >= 60:
            rating = "C"
        elif score >= 50:
            rating = "D"
        else:
            rating = "F"
        
        result = {"rating": rating, "score": float(score), "min_swr": float(min_swr), "avg_swr": float(avg_swr)}
        print(f"DEBUG: Returning result: {result}")
        return result


def save_results(measurements: List[Dict[str, float]], meta: Dict[str, str]) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"antenna_test_{timestamp}.json"
    payload = {
        "timestamp": datetime.now().isoformat(),
        "mode": "DEMO",
        "parameters": meta,
        "measurements": measurements,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return filename


def maybe_plot(measurements: List[Dict[str, float]]):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return
    if not measurements:
        return
    freqs = [m["frequency"] / 1e6 for m in measurements]
    swrs = [m["swr"] for m in measurements]
    plt.figure(figsize=(8, 4))
    plt.plot(freqs, swrs, label="SWR", color="#3b82f6")
    plt.axhline(1.5, linestyle="--", color="#22c55e", alpha=0.7, label="1.5")
    plt.axhline(2.0, linestyle="--", color="#f59e0b", alpha=0.7, label="2.0")
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("SWR")
    plt.title("SWR vs Frequency")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.show()


def main():
    # If Tkinter is available, launch GUI by default
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
    except Exception:
        # Fallback to a non-GUI run with defaults
        start, stop, points = 10.0, 40.0, 200
        analyzer = Analyzer(start, stop, points)
        print(f"Running sweep {start:.1f}–{stop:.1f} MHz, {points} points...")
        t0 = time.time()
        measurements = analyzer.run_sweep()
        dt = time.time() - t0
        rating = analyzer.rate_antenna_performance(measurements)
        print(f"Completed in {dt:.2f}s | Rating: {rating['rating']} | Score: {rating['score']}")
        print(f"Min SWR: {rating['min_swr']:.2f} | Avg SWR: {rating['avg_swr']:.2f}")
        meta = {"start_mhz": start, "stop_mhz": stop, "points": points}
        out = save_results(measurements, meta)
        print(f"Saved results to {out}")
        maybe_plot(measurements)
        return

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

    class ModernGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("Modern Antenna Analyzer")
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

            subtitle_text = "RF Testing Suite"
            subtitle_label = tk.Label(title_frame, text=subtitle_text,
                                      font=('Segoe UI', 8),
                                      bg=self.current_theme['bg_primary'],
                                      fg=self.current_theme['text_secondary'])
            subtitle_label.pack(anchor='w')

            button_frame = tk.Frame(top_row, bg=self.current_theme['bg_primary'])
            button_frame.pack(side='right')
            b1 = self.create_modern_button(button_frame, "Save", self.save_results, "secondary")
            b2 = self.create_modern_button(button_frame, "Clear", self.clear_results, "secondary")
            b3 = self.create_modern_button(button_frame, "Summary", self.view_summary, "secondary")
            b1.pack(side='left', padx=(0, 3))
            b2.pack(side='left', padx=(0, 3))
            b3.pack(side='left', padx=(0, 3))
            self._compact_buttons += [b1, b2, b3]

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

            self.status_var = tk.StringVar(value="Ready to test")
            status_label = tk.Label(sweep_row, textvariable=self.status_var,
                                    font=('Segoe UI', 8),
                                    bg=self.current_theme['bg_primary'],
                                    fg=self.current_theme['text_secondary'])
            status_label.pack(anchor='w', pady=(3, 0))

        def setup_control_panel(self, parent):
            """Setup modern control panel optimized for small screen"""
            control_card, control_content = self.create_modern_card(parent, "Test Parameters")
            control_card.pack(fill='x', pady=(0, 3))

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
            self.stop_freq_var = tk.StringVar(value="40.0")
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
            self.points_var = tk.StringVar(value="200")
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

        def on_window_resize(self, event):
            try:
                if self.is_small_screen():
                    self.apply_small_screen_scaling()
            except Exception:
                pass

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
                print("DEBUG: Starting sweep...")
                start_freq = float(self.start_freq_var.get()) * 1e6
                stop_freq = float(self.stop_freq_var.get()) * 1e6
                points = int(self.points_var.get())
                print(f"DEBUG: Parameters - Start: {start_freq}, Stop: {stop_freq}, Points: {points}")

                if start_freq >= stop_freq:
                    messagebox.showerror("Error", "Start frequency must be less than stop frequency")
                    return
                if points < 10 or points > 1000:
                    messagebox.showerror("Error", "Points must be between 10 and 1000")
                    return

                self.sweep_button.configure(state='disabled', text="Sweeping...")
                self.progress_var.set(0)
                self.status_var.set("Starting sweep...")

                start_time = time.time()
                print("DEBUG: Creating Analyzer...")
                analyzer = Analyzer(float(self.start_freq_var.get()), float(self.stop_freq_var.get()), points)
                self.measurements = []
                freqs = generate_frequency_points(float(self.start_freq_var.get()), float(self.stop_freq_var.get()), points)
                print(f"DEBUG: Generated {len(freqs)} frequency points")
                
                for i, f_mhz in enumerate(freqs, start=1):
                    v = analyzer._voltage_pair(f_mhz)
                    swr = analyzer._swr(f_mhz)
                    self.measurements.append({
                        "frequency": f_mhz * 1e6,
                        "swr": swr,
                        "mag_voltage": v["mag_voltage"],
                        "phase_voltage": v["phase_voltage"],
                    })
                    self.update_progress(i, points)
                    time.sleep(0.002)

                sweep_time = time.time() - start_time
                print(f"DEBUG: Sweep completed, {len(self.measurements)} measurements")

                self.status_var.set("Analyzing results...")
                print("DEBUG: Calling rate_antenna_performance...")
                rating_result = analyzer.rate_antenna_performance(self.measurements)
                print(f"DEBUG: Rating result: {rating_result}")
                print(f"DEBUG: Rating result type: {type(rating_result)}")
                print(f"DEBUG: Score type: {type(rating_result.get('score'))}")

                print("DEBUG: Updating results display...")
                self.update_modern_results_display(rating_result, sweep_time)
                print("DEBUG: Plotting results...")
                self.plot_modern_results()

                self.status_var.set(f"✅ Sweep completed in {sweep_time:.1f}s - Rating: {rating_result['rating']}")
                print("DEBUG: Sweep completed successfully!")

            except ValueError as e:
                print(f"DEBUG: ValueError: {e}")
                messagebox.showerror("Error", f"Invalid input: {e}")
            except Exception as e:
                print(f"DEBUG: Exception: {e}")
                print(f"DEBUG: Exception type: {type(e)}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Sweep failed: {e}")
            finally:
                self.sweep_button.configure(state='normal', text="SWEEP")
                self.progress_var.set(0)
                self.progress_canvas.delete("all")

        def update_modern_results_display(self, rating_result, sweep_time):
            """Update results with modern display"""
            print(f"DEBUG: update_modern_results_display called with rating_result: {rating_result}")
            print(f"DEBUG: rating_result type: {type(rating_result)}")
            print(f"DEBUG: rating_result keys: {rating_result.keys() if isinstance(rating_result, dict) else 'Not a dict'}")
            
            self.rating_var.set(rating_result['rating'])
            print(f"DEBUG: Set rating to: {rating_result['rating']}")
            
            score_value = rating_result['score']
            print(f"DEBUG: Score value: {score_value}, type: {type(score_value)}")
            self.score_var.set(f"{score_value:.0f}/100")
            print(f"DEBUG: Set score display to: {score_value:.0f}/100")

            score = float(score_value)  # Ensure score is a float
            print(f"DEBUG: Score as float: {score}")
            if score >= 80:
                self.rating_badge.configure(bg=self.current_theme['success'])
            elif score >= 60:
                self.rating_badge.configure(bg=self.current_theme['warning'])
            else:
                self.rating_badge.configure(bg=self.current_theme['error'])

            self.results_text.delete(1.0, tk.END)
            results_text = f"ANALYZER\n"
            results_text += f"{'='*40}\n\n"
            results_text += f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            results_text += f"Sweep time: {sweep_time:.1f} seconds\n"
            results_text += f"Frequency range: {float(self.start_freq_var.get()):.1f} - {float(self.stop_freq_var.get()):.1f} MHz\n"
            results_text += f"Measurement points: {len(self.measurements)}\n"
            results_text += f"Mode: Test Data\n"
            results_text += f"\nOVERALL RATING: {rating_result['rating']} ({rating_result['score']:.0f}/100)\n\n"
            results_text += "SUMMARY:\n"
            results_text += f"• Minimum SWR: {rating_result['min_swr']:.2f}\n"
            results_text += f"• Average SWR: {rating_result['avg_swr']:.2f}\n"
            results_text += f"• Points measured: {len(self.measurements)}\n"
            
            self.results_text.insert(1.0, results_text)
            self.results_text.see("1.0")

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
            title = 'Antenna SWR vs Frequency'
            self.ax.set_title(title, color=self.current_theme['text_primary'], fontsize=12, fontweight='bold')
            self.ax.grid(True, alpha=0.25, color=self.current_theme['text_muted'], linewidth=0.8)
            self.ax.set_ylim(1, min(max(swr_values) * 1.1, 10))
            for spine in self.ax.spines.values():
                spine.set_color(self.current_theme['border'])
            self.ax.tick_params(colors=self.current_theme['text_secondary'], labelsize=10)

            self.canvas.draw_idle()

        def clear_results(self):
            try:
                self.measurements = []
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "Ready for test results...\n")
                self.rating_var.set("--")
                self.score_var.set("--")
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
                    'hardware_mode': 'DEMO_DATA',
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

        def view_summary(self):
            """Show a summary dialog with key test results"""
            try:
                if not self.measurements:
                    messagebox.showinfo("Summary", "No test results available. Please run a sweep first.")
                    return
                
                # Calculate summary statistics
                swrs = [m['swr'] for m in self.measurements]
                min_swr = min(swrs)
                max_swr = max(swrs)
                avg_swr = sum(swrs) / len(swrs)
                good_points = sum(1 for swr in swrs if swr <= 2.0)
                excellent_points = sum(1 for swr in swrs if swr <= 1.5)
                
                # Find frequency at minimum SWR
                min_swr_idx = swrs.index(min_swr)
                min_swr_freq = self.measurements[min_swr_idx]['frequency'] / 1e6
                
                summary_text = f"""ANTENNA TEST SUMMARY
{'='*50}

Test Parameters:
• Frequency Range: {float(self.start_freq_var.get()):.1f} - {float(self.stop_freq_var.get()):.1f} MHz
• Measurement Points: {len(self.measurements)}
• Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SWR Analysis:
• Minimum SWR: {min_swr:.2f} at {min_swr_freq:.1f} MHz
• Maximum SWR: {max_swr:.2f}
• Average SWR: {avg_swr:.2f}

Performance Rating:
• Overall Grade: {self.rating_var.get()}
• Score: {self.score_var.get()}
• Excellent Points (≤1.5): {excellent_points}/{len(self.measurements)} ({excellent_points/len(self.measurements)*100:.1f}%)
• Good Points (≤2.0): {good_points}/{len(self.measurements)} ({good_points/len(self.measurements)*100:.1f}%)

Recommendations:
• Best operating frequency: {min_swr_freq:.1f} MHz
• SWR performance: {'Excellent' if min_swr <= 1.5 else 'Good' if min_swr <= 2.0 else 'Fair' if min_swr <= 3.0 else 'Poor'}
"""
                
                # Create summary window
                summary_window = tk.Toplevel(self.root)
                summary_window.title("Test Summary")
                summary_window.geometry("500x600")
                summary_window.configure(bg=self.current_theme['bg_primary'])
                summary_window.resizable(True, True)
                
                # Make it modal
                summary_window.transient(self.root)
                summary_window.grab_set()
                
                # Create text widget with scrollbar
                text_frame = tk.Frame(summary_window, bg=self.current_theme['bg_primary'])
                text_frame.pack(fill='both', expand=True, padx=10, pady=10)
                
                text_widget = tk.Text(text_frame, 
                                    bg=self.current_theme['bg_muted'],
                                    fg=self.current_theme['text_primary'],
                                    font=('Consolas', 10),
                                    wrap='word',
                                    padx=10, pady=10)
                
                scrollbar = tk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)
                
                text_widget.pack(side='left', fill='both', expand=True)
                scrollbar.pack(side='right', fill='y')
                
                text_widget.insert('1.0', summary_text)
                text_widget.configure(state='disabled')
                
                # Close button
                button_frame = tk.Frame(summary_window, bg=self.current_theme['bg_primary'])
                button_frame.pack(fill='x', padx=10, pady=(0, 10))
                
                close_button = self.create_modern_button(button_frame, "Close", summary_window.destroy, "primary")
                close_button.pack(anchor='center')
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to show summary: {e}")

    root = tk.Tk()
    app = ModernGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


