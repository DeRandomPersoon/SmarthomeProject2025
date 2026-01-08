import tkinter as tk
import math
import time
import threading
import requests
from ControlBoard import ControlBoard
from SettingsPage import SettingsPage
from AIBoard import AIBoard


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Home Dashboard")
        self.geometry("900x600")
        self.minsize(800, 550)
        self.configure(bg="#1e1e1e")

        MainPage(self).pack(fill="both", expand=True)


class MainPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e1e")

        self.temp_value = -20
        self.max_temp = 32

        # Layout
        self.rowconfigure(0, weight=4)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=2)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)

        # =========================
        # GAUGE CANVAS
        # =========================
        self.canvas = tk.Canvas(self, bg="#1e1e1e", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", pady=20)
        self.canvas.bind("<Configure>", self.on_resize)

        # =========================
        # + / - BUTTONS
        # =========================
        self.btn_frame = tk.Frame(self, bg="#1e1e1e")
        self.btn_frame.grid(row=1, column=0)

        tk.Button(self.btn_frame, text="+", width=4, font=("Arial", 18),
              command=self.increase_temp).grid(row=0, column=0, padx=15)

        tk.Button(self.btn_frame, text="-", width=4, font=("Arial", 18),
              command=self.decrease_temp).grid(row=0, column=1, padx=15)

        # =========================
        # WEATHER
        # =========================
        self.weather_label = tk.Label(
            self, bg="#2a2a2a", fg="white",
            font=("Arial", 16), height=3
        )
        self.weather_label.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)
        threading.Thread(target=self.load_weather, daemon=True).start()

        # =========================
        # NAV BAR
        # =========================
        nav = tk.Frame(self, bg="#1e1e1e")
        nav.grid(row=3, column=0, pady=10)

        self.nav_canvases = []
        self.active_nav = 0
        for i in range(4):
            c = tk.Canvas(nav, width=70, height=70, bg="#1e1e1e", highlightthickness=0)
            c.grid(row=0, column=i, padx=15)
            self.nav_canvases.append(c)

        self.draw_nav()
        # Placeholder for pages created on nav presses
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

        # ---------- ARC
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

        # ---------- BALL ON ARC (NO NEEDLE)
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

        # ---------- TEXT
        self.canvas.create_text(
            cx, cy - 45,
            text=str(self.temp_value * -1) + " C",
            fill="white",
            font=("Arial", 32)
        )

    # =========================================================
    # COLOR GRADIENT (UNCHANGED)
    # =========================================================
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

    # =========================================================
    # BUTTON LOGIC
    # =========================================================
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

    # =========================================================
    # WEATHER
    # =========================================================
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

    # =========================================================
    # NAV BAR
    # =========================================================
    def draw_nav(self):
        for i, c in enumerate(self.nav_canvases):
            c.delete("all")

            if i == self.active_nav:
                c.create_oval(5, 5, 65, 65, outline="#ff9933", width=4)

            if i == 0:
                # house with simple thermometer inside
                c.create_polygon(18,38, 35,18, 52,38, 52,55, 18,55, fill="", outline="white", width=3)
                # thermometer (bulb + tube)
                c.create_oval(42,32,48,38, fill="white", outline="")
                c.create_rectangle(44,22,46,36, fill="white", outline="")
            elif i == 1:
                # rising line graph: axes + polyline
                c.create_line(18,50,18,22, fill="white", width=2)  # y axis
                c.create_line(18,50,52,50, fill="white", width=2)  # x axis
                c.create_line(22,44,30,36,38,30,48,22, fill="white", width=3, smooth=False)
                c.create_oval(20,44,24,48, fill="white", outline="")
                c.create_oval(28,36,32,40, fill="white", outline="")
                c.create_oval(36,28,40,32, fill="white", outline="")
                c.create_oval(46,20,50,24, fill="white", outline="")
            elif i == 2:
                # power (on/off) symbol
                c.create_oval(18,18,52,52, outline="white", width=3)
                c.create_line(35,22,35,34, fill="white", width=3)
            elif i == 3:
                # gear icon (approximate)
                cx, cy = 35, 35
                r = 10
                c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="white", width=3)
                teeth = 8
                for j in range(teeth):
                    a = 2 * math.pi * j / teeth
                    x1 = cx + math.cos(a) * (r + 4)
                    y1 = cy + math.sin(a) * (r + 4)
                    x2 = cx + math.cos(a) * (r + 8)
                    y2 = cy + math.sin(a) * (r + 8)
                    c.create_line(x1, y1, x2, y2, fill="white", width=2)

            c.bind("<Button-1>", lambda e, idx=i: self.on_nav(idx))

    def on_nav(self, idx):
        print("Nav pressed:", idx)
        self.active_nav = idx
        self.draw_nav()
        self.show_page(idx)

    def show_page(self, idx):
        # AI page (index 1)
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
                self.ai_page = AIBoard(self)
                self.ai_page.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=40, pady=20)
            return

        # If third nav (index 2) selected, replace main content with ControlBoard
        if idx == 2:
            # hide main widgets
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
                self.control_page = ControlBoard(self)
                self.control_page.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=40, pady=20)

        elif idx == 3:
            # Settings page
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
                self.settings_page = SettingsPage(self)
                self.settings_page.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=40, pady=20)

        else:
            # restore main widgets if they were hidden
            if self.control_page:
                self.control_page.destroy()
                self.control_page = None
            if self.settings_page:
                self.settings_page.destroy()
                self.settings_page = None
            if self.ai_page:
                self.ai_page.destroy()
                self.ai_page = None

            # re-grid original widgets
            self.canvas.grid(row=0, column=0, sticky="nsew", pady=20)
            self.btn_frame.grid(row=1, column=0)
            self.weather_label.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)
            self.draw_gauge()


if __name__ == "__main__":
    App().mainloop()

###test