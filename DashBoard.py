"""Main dashboard with gauge, AI, controls, and settings."""

import tkinter as tk
import math
import time
import threading
import requests
import datetime
import csv
from tkinter import filedialog, messagebox
from ControlBoard import ControlBoard
from SettingsPage import SettingsPage
from AIBoard import AIBoard
from BasePage import BasePage

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Home Dashboard")
        self.geometry("900x600")
        self.minsize(800, 550)
        self.configure(bg="#1e1e1e")

        MainPage(self).pack(fill="both", expand=True)


class MainPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent)

        self.temp_value = -20
        self.max_temp = 32

        self.content.rowconfigure(0, weight=4)
        self.content.rowconfigure(1, weight=1)
        self.content.rowconfigure(2, weight=2)
        self.content.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.content, bg="#1e1e1e", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", pady=20)
        self.canvas.bind("<Configure>", self.on_resize)

        self.btn_frame = tk.Frame(self.content, bg="#1e1e1e")
        self.btn_frame.grid(row=1, column=0, sticky='n', pady=(18,0))

        tk.Button(self.btn_frame, text="+", width=4, font=("Arial", 18),
              command=self.increase_temp).grid(row=0, column=0, padx=15)

        tk.Button(self.btn_frame, text="-", width=4, font=("Arial", 18),
              command=self.decrease_temp).grid(row=0, column=1, padx=15)

        self.weather_label = tk.Label(
            self.content, bg="#2a2a2a", fg="white",
            font=("Arial", 16), height=3
        )
        self.weather_label.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)
        self.weather_label.config(cursor="hand2")
        self.weather_label.bind("<Button-1>", lambda e: self.open_weather_details())
        threading.Thread(target=self.load_weather, daemon=True).start()

        self.set_active_nav(0)

        self.control_page = None
        self.settings_page = None
        self.ai_page = None
        self.after(50, self.draw_gauge)

    # =========================================================
    # RESIZE
    # =========================================================
    def on_resize(self, event):
        self.draw_gauge()

    # =========================================================
    # GAUGE (ARC + BALL ON ARC)
    # =========================================================
    def draw_gauge(self):
        self.canvas.delete("all")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50 or h < 50:
            return

        size = min(w, h) * 0.85
        cx = w / 2
        cy = h * 0.85
        r = size / 2
        arc_width = 26

        steps = 140
        for i in range(steps):
            t = i / steps
            start = 180 - (i + 1) * (180 / steps)

            self.canvas.create_arc(
                cx - r, cy - r,
                cx + r, cy + r,
                start=start,
                extent=180 / steps,
                style="arc",
                width=arc_width,
                outline=self.temp_color(t)
            )

        ratio = self.temp_value / self.max_temp
        angle = math.radians(180 - ratio * 180)
        arc_radius = r - arc_width / 2
        bx = cx + math.cos(angle) * arc_radius
        by = cy + math.sin(angle) * arc_radius

        self.canvas.create_oval(
            bx - 6, by - 6,
            bx + 6, by + 6,
            fill="white",
            outline=""
        )

        self.canvas.create_text(
            cx, cy - 45,
            text=str(self.temp_value * -1) + " C",
            fill="white",
            font=("Arial", 32)
        )

    def temp_color(self, t):
        if t < 0.2:
            r, g, b = 0, int(255 * (t / 0.2)), 255
        elif t < 0.4:
            r, g, b = 0, 255, int(255 - 255 * ((t - 0.2) / 0.2))
        elif t < 0.6:
            r, g, b = int(255 * ((t - 0.4) / 0.2)), 255, 0
        elif t < 0.8:
            r, g, b = 255, int(255 - 128 * ((t - 0.6) / 0.2)), 0
        else:
            r, g, b = 255, int(127 - 127 * ((t - 0.8) / 0.2)), 0
        return f"#{r:02x}{g:02x}{b:02x}"

    def increase_temp(self):
        if self.temp_value > (self.max_temp * -1):
            self.temp_value -= 1
            self.draw_gauge()
        else:
            self.flash_gauge()
        
    def decrease_temp(self):
        if self.temp_value < 0:
            self.temp_value += 1
            self.draw_gauge()
        else:
            self.flash_gauge()

    def flash_gauge(self):
        original = self.canvas["bg"]
        self.canvas.config(bg="#ff9933")
        self.update()
        time.sleep(0.08)
        self.canvas.config(bg=original)

    def load_weather(self):
        while True:
            try:
                url = (
                    "https://api.open-meteo.com/v1/forecast?"
                    "latitude=52.37&longitude=4.89&current_weather=true"
                )
                data = requests.get(url, timeout=5).json()
                temp = data["current_weather"]["temperature"]
                wind = data["current_weather"]["windspeed"]
                self.weather_label.config(
                    text=f"Outside: {temp} C   Wind: {wind} km/h"
                )
            except Exception:
                self.weather_label.config(text="Weather unavailable")
            time.sleep(120)

    def open_weather_details(self):
        w = tk.Toplevel(self)
        w.title("Weather details")
        w.geometry("900x650")
        w.configure(bg="#1e1e1e")

        ctrl = tk.Frame(w, bg="#1e1e1e")
        ctrl.pack(side="top", fill="x", padx=10, pady=6)

        tk.Label(ctrl, text="Range:", bg="#1e1e1e", fg="white").pack(side="left", padx=8)
        preset_var = tk.StringVar(value="30 days")
        preset_menu = tk.OptionMenu(ctrl, preset_var, "")
        preset_menu.config(bg="#2a2a2a", fg="white")
        preset_menu.pack(side="left")

        def update_presets(*args):
            menu = preset_menu['menu']
            menu.delete(0, 'end')
            opts = [("2 weeks", "14 days"), ("1 month", "30 days"), ("3 months", "90 days"), ("6 months", "180 days"), ("1 year", "1 years"), ("5 years", "5 years")]
            for label, val in opts:
                menu.add_command(label=label, command=lambda v=val: preset_var.set(v))
            preset_var.set("30 days")

        update_presets()

        refresh_btn = tk.Button(ctrl, text="Refresh", command=lambda: load_and_plot())
        refresh_btn.pack(side="left", padx=6)

        download_btn = tk.Button(ctrl, text="Download CSV", command=lambda: self.download_current_csv())
        download_btn.pack(side="right")

        plot_frame = tk.Frame(w, bg="#1e1e1e")
        plot_frame.pack(fill="both", expand=True, padx=10, pady=6)

        fig = None
        ax = None
        if MATPLOTLIB_AVAILABLE:
            fig = plt.Figure(figsize=(8,5))
            ax = fig.add_subplot(111)
            canvas_widget = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas_widget.get_tk_widget().pack(fill="both", expand=True)
        else:
            canvas_widget = tk.Canvas(plot_frame, bg="#2a2a2a")
            canvas_widget.pack(fill="both", expand=True)

        self._weather_detail_state = {
            "preset_var": preset_var,
            "canvas": canvas_widget,
            "fig": fig,
            "ax": ax,
            "widget_window": w
        }

        def load_and_plot():
            pv = preset_var.get() or "30 days"
            if pv.endswith('days'):
                try:
                    days = int(pv.split()[0]) if ' ' in pv else int(pv.replace('days','').strip())
                except Exception:
                    import re
                    m = re.search(r"(\d+)", pv)
                    days = int(m.group(1)) if m else 30
                mode = 'daily'
                if days > 3650:
                    messagebox.showinfo("Range out of scope","Selected range is too large. Please choose a shorter range (up to 10 years).")
                    self._weather_detail_state['current_data'] = ([], [], [])
                    self._weather_detail_state['mode'] = mode
                    self.render_plot(canvas_widget, [], [], [], self._weather_detail_state)
                    return
                end = datetime.date.today()
                start = end - datetime.timedelta(days=max(1, days)-1)
                dates, tmin, tmax = self.fetch_weather_range(start, end)
            else:
                try:
                    years = int(pv.split()[0]) if ' ' in pv else int(pv.replace('years','').strip())
                except Exception:
                    years = 1
                mode = 'monthly'
                if years > 50:
                    messagebox.showinfo("Range out of scope","Selected range is too large. Please choose a shorter range (up to 50 years).")
                    self._weather_detail_state['current_data'] = ([], [], [])
                    self._weather_detail_state['mode'] = mode
                    self.render_plot(canvas_widget, [], [], [], self._weather_detail_state)
                    return
                end = datetime.date.today()
                start = end - datetime.timedelta(days=years*365)
                dates, tmin, tmax = self.fetch_weather_range(start, end)
                dates, tmin, tmax = self.aggregate_monthly(dates, tmin, tmax)

            if not dates:
                messagebox.showinfo("No data","No data available for the selected range. Try a shorter range or check your network.")
                self._weather_detail_state['current_data'] = ([], [], [])
                self._weather_detail_state['mode'] = mode
                self.render_plot(canvas_widget, [], [], [], self._weather_detail_state)
                return

            self._weather_detail_state['current_data'] = (dates, tmin, tmax)
            self._weather_detail_state['mode'] = mode
            self.render_plot(canvas_widget, dates, tmin, tmax, self._weather_detail_state)

            if MATPLOTLIB_AVAILABLE and fig is not None:
                fig.canvas.draw()

        load_and_plot()

    def fetch_weather_range(self, start_date, end_date):
        s = start_date.isoformat()
        e = end_date.isoformat()
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude=52.37&longitude=4.89&daily=temperature_2m_max,temperature_2m_min"
            f"&start_date={s}&end_date={e}&timezone=Europe%2FAmsterdam"
        )
        try:
            data = requests.get(url, timeout=10).json()
            dates = [datetime.date.fromisoformat(d) for d in data.get("daily", {}).get("time", [])]
            tmin = data.get("daily", {}).get("temperature_2m_min", [])
            tmax = data.get("daily", {}).get("temperature_2m_max", [])
            return dates, tmin, tmax
        except Exception:
            return [], [], []

    def aggregate_monthly(self, dates, tmin, tmax):
        monthly = {}
        for d, mn, mx in zip(dates, tmin, tmax):
            key = (d.year, d.month)
            if key not in monthly:
                monthly[key] = {"tmin": [], "tmax": []}
            monthly[key]["tmin"].append(mn)
            monthly[key]["tmax"].append(mx)
        sorted_items = sorted(monthly.items())
        out_dates = [datetime.date(y, m, 1) for (y, m), _ in sorted_items]
        out_tmin = [sum(v["tmin"]) / len(v["tmin"]) for _, v in sorted_items]
        out_tmax = [sum(v["tmax"]) / len(v["tmax"]) for _, v in sorted_items]
        return out_dates, out_tmin, out_tmax

    def render_plot(self, canvas, dates, tmin, tmax, state):
        if not dates:
            if MATPLOTLIB_AVAILABLE and state.get('fig'):
                ax = state['ax']
                ax.clear()
                ax.text(0.5,0.5,"No data", ha="center")
                state['fig'].canvas.draw()
            else:
                canvas.delete("all")
                canvas.create_text(200,100,text="No data", fill="white")
            return

        mode = state.get('mode', 'daily')

        if MATPLOTLIB_AVAILABLE and state.get('fig'):
            ax = state['ax']
            ax.clear()
            try:
                import matplotlib.dates as mdates
                import matplotlib.ticker as mticker
                x = mdates.date2num(dates)
                ax.plot_date(x, tmin, '-', label="Min")
                ax.plot_date(x, tmax, '-', label="Max")
                ax.fill_between(x, tmin, tmax, alpha=0.2)

                miny = min(min(tmin), 0)
                maxy = max(max(tmax), 0)
                yrange = maxy - miny if maxy != miny else 1
                ax.set_ylim(miny - 0.05*yrange, maxy + 0.05*yrange)
                ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6))
                ax.axhline(0, color='#00ffff', linestyle='--', linewidth=1, alpha=0.9)
                ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=6))
                ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))

                if mode == 'monthly':
                    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            except Exception:
                ax.plot(dates, tmin, label="Min")
                ax.plot(dates, tmax, label="Max")
                ax.fill_between(dates, tmin, tmax, alpha=0.2)
                try:
                    miny = min(tmin)
                    maxy = max(tmax)
                    if miny <= 0 <= maxy:
                        ax.axhline(0, color='#00ffff', linestyle='--', linewidth=1, alpha=0.9)
                except Exception:
                    pass
            ax.legend()
            ax.set_title("Temperature (min/max)")
            ax.set_ylabel("°C")
            state['fig'].autofmt_xdate()
        else:
            canvas.delete("all")
            w = canvas.winfo_width() or 600
            h = canvas.winfo_height() or 300
            pad = 56
            n = len(dates)
            miny = min(tmin)
            maxy = max(tmax)
            yrange = maxy - miny if (maxy - miny) != 0 else 1
            xs = [pad + i*(w-2*pad)/(n-1) for i in range(n)] if n>1 else [w/2]
            ys_min = [h - pad - ((mn - miny)/yrange)*(h-2*pad) for mn in tmin]
            ys_max = [h - pad - ((mx - miny)/yrange)*(h-2*pad) for mx in tmax]
            # axes
            canvas.create_line(pad, pad, pad, h-pad, fill="white")
            canvas.create_line(pad, h-pad, w-pad, h-pad, fill="white")
            # Y axis labels (5 ticks)
            ticks = 5
            for i in range(ticks):
                frac = i/(ticks-1) if ticks>1 else 0
                val = maxy - frac*(maxy - miny)
                y = pad + frac*(h-2*pad)
                canvas.create_text(pad-8, y, text=f"{val:.1f}", fill='white', anchor='e', font=(None,9))
            # draw lines
            for i in range(n-1):
                canvas.create_line(xs[i], ys_min[i], xs[i+1], ys_min[i+1], fill="#00aaff", width=2)
                canvas.create_line(xs[i], ys_max[i], xs[i+1], ys_max[i+1], fill="#ff9933", width=2)
            # fill polygon
            points = []
            for x,y in zip(xs, ys_max):
                points.append((x,y))
            for x,y in reversed(list(zip(xs, ys_min))):
                points.append((x,y))
            flat = [coord for p in points for coord in p]
            if flat:
                canvas.create_polygon(*flat, fill="#888888", stipple="gray25", outline="")
            # zero line if within range
            if miny <= 0 <= maxy:
                y0 = h - pad - ((0 - miny)/yrange)*(h-2*pad)
                canvas.create_line(pad, y0, w-pad, y0, fill="#00ffff", dash=(4,2))
            # X labels: sparse every step
            max_labels = 6
            step = max(1, n//max_labels)
            for i in range(0, n, step):
                d = dates[i]
                lbl = d.strftime('%Y-%m-%d' if mode=='daily' else '%Y-%m')
                canvas.create_text(xs[i], h - pad + 12, text=lbl, fill='white', anchor='n', font=(None,8))


    def download_current_csv(self):
        state = getattr(self, "_weather_detail_state", None)
        if not state or 'current_data' not in state:
            messagebox.showinfo("No data","No data to download")
            return
        dates, tmin, tmax = state['current_data']
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["date","min","max"])
                for d, mn, mx in zip(dates, tmin, tmax):
                    writer.writerow([d.isoformat(), mn, mx])
            messagebox.showinfo("Saved", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_nav(self, idx):
        self.set_active_nav(idx)
        self.show_page(idx)

    def show_page(self, idx):
        if idx == 1:
            try:
                self.canvas.grid_remove()
                self.btn_frame.grid_remove()
                self.weather_label.grid_remove()
            except Exception:
                pass

            if self.control_page:
                self.control_page.destroy()
                self.control_page = None
            if self.settings_page:
                self.settings_page.destroy()
                self.settings_page = None

            if not self.ai_page:
                self.ai_page = AIBoard(self.content)
                self.ai_page.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=40, pady=20)
            return

        if idx == 2:
            try:
                self.canvas.grid_remove()
                self.btn_frame.grid_remove()
                self.weather_label.grid_remove()
            except Exception:
                pass

            if self.settings_page:
                self.settings_page.destroy()
                self.settings_page = None

            if not self.control_page:
                self.control_page = ControlBoard(self.content)
                self.control_page.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=40, pady=20)

        elif idx == 3:
            try:
                self.canvas.grid_remove()
                self.btn_frame.grid_remove()
                self.weather_label.grid_remove()
            except Exception:
                pass

            if self.control_page:
                self.control_page.destroy()
                self.control_page = None

            if not self.settings_page:
                self.settings_page = SettingsPage(self.content)
                self.settings_page.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=40, pady=20)

        else:
            if self.control_page:
                self.control_page.destroy()
                self.control_page = None
            if self.settings_page:
                self.settings_page.destroy()
                self.settings_page = None
            if self.ai_page:
                self.ai_page.destroy()
                self.ai_page = None

            self.canvas.grid(row=0, column=0, sticky="nsew", pady=20)
            self.btn_frame.grid(row=1, column=0)
            self.weather_label.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)
            self.draw_gauge()
            
if __name__ == "__main__":
    App().mainloop()