#!/usr/bin/env python3
"""
Demo Antenna Analyzer (Mock Data)

Generates random mock measurements across 10–40 MHz for demonstration
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


class DemoAnalyzer:
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

    def _mock_voltage_pair(self, freq_mhz: float) -> Dict[str, float]:
        # Produce pseudo-random but smooth-ish voltages in 0.0–3.3 V
        base = 1.6 + 0.2 * random.uniform(-1, 1)
        mag = max(0.0, min(3.3, base + 0.5 * random.uniform(-1, 1)))
        phase = max(0.0, min(3.3, base + 0.5 * random.uniform(-1, 1)))
        return {"mag_voltage": mag, "phase_voltage": phase}

    def _mock_swr(self, freq_mhz: float) -> float:
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
            v = self._mock_voltage_pair(f_mhz)
            swr = self._mock_swr(f_mhz)
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
    def rate_antenna_performance(measurements: List[Dict[str, float]]) -> Dict[str, float]:
        if not measurements:
            return {"rating": "F", "score": 0}
        swrs = [m["swr"] for m in measurements]
        min_swr = min(swrs)
        avg_swr = sum(swrs) / len(swrs)
        good_ratio = sum(1 for x in swrs if x <= 2.0) / len(swrs)
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
        return {"rating": rating, "score": score, "min_swr": min_swr, "avg_swr": avg_swr}


def save_results(measurements: List[Dict[str, float]], meta: Dict[str, str]) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"demo_antenna_test_{timestamp}.json"
    payload = {
        "timestamp": datetime.now().isoformat(),
        "mode": "DEMO_MOCK",
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
    plt.title("Demo SWR vs Frequency (Mock Data)")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.show()


def main():
    # If Tkinter is available, launch GUI by default
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
    except Exception:
        # Fallback to a non-GUI demo run with defaults
        start, stop, points = 10.0, 40.0, 200
        analyzer = DemoAnalyzer(start, stop, points)
        print(f"Running demo sweep {start:.1f}–{stop:.1f} MHz, {points} points...")
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

    class DemoAnalyzerGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("Demo Antenna Analyzer (Mock 10–40 MHz)")
            self.root.geometry("900x520")

            self.start_var = tk.StringVar(value="10.0")
            self.stop_var = tk.StringVar(value="40.0")
            self.points_var = tk.StringVar(value="200")

            self.measurements: List[Dict[str, float]] = []

            main = tk.Frame(self.root)
            main.pack(fill="both", expand=True, padx=8, pady=8)

            controls = tk.Frame(main)
            controls.pack(fill="x", pady=(0, 8))

            def add_labeled_entry(parent, label_text, var, width=8):
                frame = tk.Frame(parent)
                frame.pack(side="left", padx=6)
                tk.Label(frame, text=label_text).pack(anchor="w")
                e = tk.Entry(frame, textvariable=var, width=width)
                e.pack()
                return e

            add_labeled_entry(controls, "Start (MHz)", self.start_var)
            add_labeled_entry(controls, "Stop (MHz)", self.stop_var)
            add_labeled_entry(controls, "Points", self.points_var)

            self.run_btn = tk.Button(controls, text="SWEEP", command=self.run_sweep, padx=12, pady=6)
            self.run_btn.pack(side="left", padx=8)

            self.save_btn = tk.Button(controls, text="Save", command=self.save_results, padx=10, pady=6, state="disabled")
            self.save_btn.pack(side="left", padx=4)

            # Progress/status row
            self.progress_var = tk.DoubleVar(value=0)
            progress_frame = tk.Frame(main)
            progress_frame.pack(fill="x", pady=(0, 6))
            self.progress_canvas = tk.Canvas(progress_frame, height=6, bg="#e5e7eb", highlightthickness=0, relief='flat')
            self.progress_canvas.pack(fill="x")
            # Replace previous plain status label placement
            status_row = tk.Frame(main)
            status_row.pack(fill="x")
            self.status_var = tk.StringVar(value="Ready")
            tk.Label(status_row, textvariable=self.status_var, fg="#6b7280").pack(anchor="w")

            content = tk.Frame(main)
            content.pack(fill="both", expand=True)
            left = tk.Frame(content)
            right = tk.Frame(content)
            left.pack(side="left", fill="both", expand=False, padx=(0, 8))
            right.pack(side="left", fill="both", expand=True)

            # Results text panel
            res_card = tk.Frame(left, relief="solid", bd=1)
            res_card.pack(fill="both", expand=True)
            tk.Label(res_card, text="Results").pack(anchor="w", padx=6, pady=4)
            self.results_text = tk.Text(res_card, width=36, height=24)
            self.results_text.pack(fill="both", expand=True, padx=6, pady=(0, 6))

            # Plot panel
            plot_card = tk.Frame(right, relief="solid", bd=1)
            plot_card.pack(fill="both", expand=True)
            tk.Label(plot_card, text="SWR vs Frequency").pack(anchor="w", padx=6, pady=4)
            self.fig = Figure(figsize=(6, 4))
            self.ax = self.fig.add_subplot(111)
            self.ax.set_xlabel("Frequency (MHz)")
            self.ax.set_ylabel("SWR")
            self.ax.grid(True, alpha=0.25)
            self.canvas = FigureCanvasTkAgg(self.fig, plot_card)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)

        def run_sweep(self):
            try:
                start = float(self.start_var.get())
                stop = float(self.stop_var.get())
                points = int(self.points_var.get())
                if start >= stop:
                    messagebox.showerror("Error", "Start must be less than Stop")
                    return
                if points < 10 or points > 2000:
                    messagebox.showerror("Error", "Points must be between 10 and 2000")
                    return
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
                return

            self.run_btn.configure(state="disabled", text="Sweeping...")
            self.progress_var.set(0)
            self.progress_canvas.delete("all")
            self.status_var.set("Starting sweep...")
            self.root.update_idletasks()

            analyzer = DemoAnalyzer(start, stop, points)
            t0 = time.time()
            self.measurements = []
            freqs = generate_frequency_points(start, stop, points)
            for i, f_mhz in enumerate(freqs, start=1):
                v = analyzer._mock_voltage_pair(f_mhz)
                swr = analyzer._mock_swr(f_mhz)
                self.measurements.append({
                    "frequency": f_mhz * 1e6,
                    "swr": swr,
                    "mag_voltage": v["mag_voltage"],
                    "phase_voltage": v["phase_voltage"],
                })
                # Update progress bar
                progress = (i / points) * 100
                self.progress_var.set(progress)
                self.progress_canvas.delete("all")
                width = self.progress_canvas.winfo_width()
                if width > 1:
                    self.progress_canvas.create_rectangle(0, 0, (progress / 100) * width, 6, fill="#3b82f6", outline="")
                self.status_var.set(f"Measuring point {i}/{points}")
                if i % max(1, points // 50) == 0:
                    self.root.update_idletasks()
                time.sleep(0.002)

            elapsed = time.time() - t0
            rating = analyzer.rate_antenna_performance(self.measurements)

            self.populate_results(rating, elapsed)
            self.plot_results()

            self.status_var.set(f"Done in {elapsed:.2f}s | Rating {rating['rating']} ({rating['score']})")
            self.run_btn.configure(state="normal", text="SWEEP")
            self.progress_var.set(0)
            self.progress_canvas.delete("all")
            self.save_btn.configure(state="normal")

        def populate_results(self, rating: Dict[str, float], elapsed: float):
            self.results_text.delete("1.0", "end")
            lines = []
            lines.append("DEMO ANALYZER (MOCK DATA)")
            lines.append("=" * 32)
            lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Sweep: {self.start_var.get()}–{self.stop_var.get()} MHz  |  Points: {self.points_var.get()}")
            lines.append(f"Elapsed: {elapsed:.2f} s")
            lines.append("")
            lines.append(f"Rating: {rating['rating']}  |  Score: {rating['score']}")
            lines.append(f"Min SWR: {rating['min_swr']:.2f}  |  Avg SWR: {rating['avg_swr']:.2f}")
            self.results_text.insert("1.0", "\n".join(lines))

        def plot_results(self):
            if not self.measurements:
                return
            freqs = [m["frequency"] / 1e6 for m in self.measurements]
            swrs = [m["swr"] for m in self.measurements]
            self.ax.clear()
            self.ax.plot(freqs, swrs, color="#3b82f6", linewidth=2)
            self.ax.axhline(1.5, linestyle="--", color="#22c55e", alpha=0.8)
            self.ax.axhline(2.0, linestyle="--", color="#f59e0b", alpha=0.8)
            self.ax.set_xlabel("Frequency (MHz)")
            self.ax.set_ylabel("SWR")
            self.ax.set_title("Demo SWR vs Frequency")
            self.ax.grid(True, alpha=0.25)
            self.ax.set_ylim(1.0, max(3.2, min(10.0, max(swrs) * 1.1)))
            self.canvas.draw_idle()

        def save_results(self):
            if not self.measurements:
                messagebox.showinfo("Save", "No results to save.")
                return
            meta = {
                "start_mhz": float(self.start_var.get()),
                "stop_mhz": float(self.stop_var.get()),
                "points": int(self.points_var.get()),
            }
            out = save_results(self.measurements, meta)
            messagebox.showinfo("Save", f"Saved to {out}")

    root = tk.Tk()
    app = DemoAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


