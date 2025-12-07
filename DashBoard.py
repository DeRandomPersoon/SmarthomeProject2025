import tkinter as tk
from tkinter import ttk
import math
import threading
import requests
import time


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Smart Home Dashboard")
        self.geometry("900x600")
        self.minsize(800, 550)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        frame = MainPage(container, self)
        self.frames["MainPage"] = frame
        frame.pack(fill="both", expand=True)

        self.show_frame("MainPage")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()


# -------------------------------------------------------------------------
# MAIN PAGE
# -------------------------------------------------------------------------

class MainPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        self.configure(style="Dark.TFrame")
        self.temp_value = 18
        self.absolute_max = 32
        self.active_index = 0  # bottom nav bar active

        # Styles
        s = ttk.Style()
        s.configure("Dark.TFrame", background="#1e1e1e")

        # Layout → 3 rows
        self.rowconfigure(0, weight=5)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(2, weight=2)
        self.columnconfigure(0, weight=1)

        # ------------------------------
        # TOP AREA → TEMPERATURE GAUGE
        # ------------------------------
        self.gauge_canvas = tk.Canvas(self, bg="#1e1e1e", highlightthickness=0)
        self.gauge_canvas.grid(row=0, column=0, sticky="n", pady=20)


        self.draw_gauge()

        # + and - buttons
        btn_frame = tk.Frame(self, bg="#1e1e1e")
        btn_frame.grid(row=0, column=0, sticky="s", pady=0)

        minus_btn = tk.Button(
            btn_frame, text="-", font=("Arial", 22),
            width=3, command=self.decrease_temp
        )
        minus_btn.grid(row=0, column=0, padx=20)

        plus_btn = tk.Button(
            btn_frame, text="+", font=("Arial", 22),
            width=3, command=self.increase_temp
        )
        plus_btn.grid(row=0, column=1, padx=20)

        # ------------------------------
        # MIDDLE AREA → Weather Block
        # ------------------------------
        self.weather_frame = tk.Frame(self, bg="#2a2a2a")
        self.weather_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=10)
        self.weather_frame.columnconfigure(0, weight=1)
        self.weather_frame.rowconfigure(0, weight=1)

        self.weather_label = tk.Label(
            self.weather_frame,
            text="Loading weather...",
            fg="white", bg="#2a2a2a",
            font=("Arial", 18)
        )
        self.weather_label.pack(expand=True)

        # Start weather thread
        threading.Thread(target=self.refresh_weather, daemon=True).start()

        # ------------------------------
        # BOTTOM AREA → Navigation Bar
        # ------------------------------
        self.nav_frame = tk.Frame(self, bg="#1e1e1e")
        self.nav_frame.grid(row=2, column=0, sticky="nsew")

        self.nav_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.nav_buttons = []
        for i in range(4):
            c = tk.Canvas(self.nav_frame, width=80, height=80,
                          bg="#1e1e1e", highlightthickness=0)
            c.grid(row=0, column=i, padx=20, pady=10)
            self.nav_buttons.append(c)

        self.draw_nav_icons()

    # ---------------------------------------------------------------------
    # DRAW TEMPERATURE GAUGE
    # ---------------------------------------------------------------------

    def draw_gauge(self):
        self.gauge_canvas.delete("all")

        w = self.gauge_canvas.winfo_width() or 900
        h = self.gauge_canvas.winfo_height() or 300

        # GAUGE POSITION AND SIZE
        size = min(w, h) * 0.75
        cx = w / 2
        cy = h / 1.45   # move upward

        r = size / 2

        # FIXED ORIENTATION:
        # Blue (cold) left → Red (hot) right
        # Blank section at bottom (180° - 360°)
        start = -45
        end = 225
        steps = 100

        # Draw gradient arc
        for i in range(steps):
            angle1 = start + (i / steps) * (end - start)
            angle2 = start + ((i + 1) / steps) * (end - start)

            t = i / steps
            color = self.temp_color(t)

            self.gauge_canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=angle1, extent=(angle2 - angle1),
                style="arc", width=25,
                outline=color
            )

        # Needle angle
        needle_angle = start + (self.temp_value / self.absolute_max) * (end - start)
        rad = math.radians(needle_angle)

        nx = cx + math.cos(rad) * (r - 30)
        ny = cy + math.sin(rad) * (r - 30)

        # Needle
        self.gauge_canvas.create_line(
            cx, cy, nx, ny,
            fill="white", width=4
        )

        # Temperature text
        self.gauge_canvas.create_text(
            cx, cy - 30,
            text=str(self.temp_value) + "C",
            fill="white",
            font=("Arial", 34)
        )


    # ---------------------------------------------------------------------

    def temp_color(self, t):
        # blue → cyan → green → yellow → orange → red
        if t < 0.2:   # blue → cyan
            r = 0
            g = int(255 * (t / 0.2))
            b = 255
        elif t < 0.4:  # cyan → green
            r = 0
            g = 255
            b = int(255 - (255 * ((t - 0.2) / 0.2)))
        elif t < 0.6:  # green → yellow
            r = int(255 * ((t - 0.4) / 0.2))
            g = 255
            b = 0
        elif t < 0.8:  # yellow → orange
            r = 255
            g = int(255 - (128 * ((t - 0.6) / 0.2)))
            b = 0
        else:          # orange → red
            r = 255
            g = int(127 - (127 * ((t - 0.8) / 0.2)))
            b = 0

        return "#%02x%02x%02x" % (r, g, b)

    # ---------------------------------------------------------------------
    # TEMPERATURE BUTTON HANDLERS
    # ---------------------------------------------------------------------

    def increase_temp(self):
        print("Increase temperature pressed")

        if self.temp_value >= self.absolute_max:
            self.flash_gauge()
            return

        self.temp_value += 1
        self.draw_gauge()

    def decrease_temp(self):
        print("Decrease temperature pressed")

        if self.temp_value > 0:
            self.temp_value -= 1
            self.draw_gauge()

    def flash_gauge(self):
        for _ in range(2):
            self.gauge_canvas.config(bg="#ff8800")
            self.update()
            time.sleep(0.07)
            self.gauge_canvas.config(bg="#1e1e1e")
            self.update()
            time.sleep(0.07)

    # ---------------------------------------------------------------------
    # WEATHER API
    # ---------------------------------------------------------------------

    def refresh_weather(self):
        while True:
            try:
                url = (
                    "https://api.open-meteo.com/v1/forecast?"
                    "latitude=52.37&longitude=4.89&current_weather=true"
                )
                data = requests.get(url, timeout=5).json()

                temp = data["current_weather"]["temperature"]
                wind = data["current_weather"]["windspeed"]

                text = "Weather\nTemp: {} C\nWind: {} km/h".format(temp, wind)

                self.weather_label.config(text=text)

            except Exception:
                self.weather_label.config(text="Weather unavailable")

            time.sleep(90)

    # ---------------------------------------------------------------------
    # NAV BAR ICONS
    # ---------------------------------------------------------------------

    def draw_nav_icons(self):
        for i, c in enumerate(self.nav_buttons):
            c.delete("all")

            x = 40
            y = 40

            # Highlight if active
            if i == self.active_index:
                c.create_oval(5, 5, 75, 75, outline="#ffaa33", width=4)

            # Very simple placeholder icons:
            if i == 0:  # Fire
                c.create_polygon(
                    40, 15, 55, 45, 40, 70, 25, 45,
                    fill="white"
                )

            elif i == 1:  # Battery
                c.create_rectangle(20, 20, 60, 60, outline="white", width=3)
                c.create_rectangle(60, 32, 70, 48, outline="white", width=3)

            elif i == 2:  # Settings
                c.create_oval(22, 22, 58, 58, outline="white", width=3)
                c.create_line(20, 40, 60, 40, fill="white", width=3)
                c.create_line(40, 20, 40, 60, fill="white", width=3)

            elif i == 3:  # Graph
                c.create_line(20, 60, 20, 20, fill="white", width=3)
                c.create_line(20, 60, 60, 60, fill="white", width=3)
                c.create_line(20, 50, 35, 40, fill="white", width=3)
                c.create_line(35, 40, 55, 30, fill="white", width=3)

            # Click handler
            c.bind("<Button-1>", lambda e, idx=i: self.on_nav_click(idx))

    def on_nav_click(self, idx):
        print("Navigation button clicked:", idx)
        self.active_index = idx
        self.draw_nav_icons()


# -------------------------------------------------------------------------

if __name__ == "__main__":
    app = App()
    app.mainloop()
