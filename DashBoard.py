# Dashboard.py
"""
Modern TinyHouse Smart Home Dashboard
Dark theme, subtle colored tiles, and preview datapoints (hardcoded for now).
"""

import tkinter as tk
from tkinter import ttk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("TinyHouse Dashboard")
        self.geometry("900x600")
        self.minsize(800, 500)
        self.configure(bg="#1e1e1e")

        container = ttk.Frame(self)
        container.pack(expand=True, fill="both")

        self.frames = {}
        main_page = MainPage(container, self)
        main_page.pack(expand=True, fill="both")
        self.frames["MainPage"] = main_page


class MainPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Dark style
        style = ttk.Style()
        style.configure("Dark.TFrame", background="#1e1e1e")
        self.configure(style="Dark.TFrame")

        # Hardcoded preview values
        self.lights_status = "3 ON"
        self.energy_battery = "Battery: 82%"
        self.water_tank = "Tank: 64%"
        self.smart_thermostat = "Thermostat: 21°C"

        # Layout
        self.columnconfigure((0, 1), weight=1, uniform="col")
        self.rowconfigure((0, 1), weight=1, uniform="row")

        # Tiles
        self._make_tile(
            0, 0, "Lights", self.lights_status, "#3a3f44"
        )
        self._make_tile(
            0, 1, "Energy", self.energy_battery, "#44525c"
        )
        self._make_tile(
            1, 0, "Water", self.water_tank, "#3b4d4f"
        )
        self._make_tile(
            1, 1, "Smart Controls", self.smart_thermostat, "#4a4248"
        )

    def _make_tile(self, r, c, title, preview, color):
        frame = tk.Frame(self, bg=color, highlightbackground="#555", highlightthickness=1)
        frame.grid(row=r, column=c, sticky="nsew", padx=25, pady=25)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        # Main label
        lbl_title = tk.Label(
            frame,
            text=title,
            font=("Arial", 20, "bold"),
            bg=color,
            fg="white"
        )
        lbl_title.place(relx=0.5, rely=0.35, anchor="center")

        # Preview data
        lbl_preview = tk.Label(
            frame,
            text=preview,
            font=("Arial", 12),
            bg=color,
            fg="#cccccc"
        )
        lbl_preview.place(relx=0.5, rely=0.60, anchor="center")

        # Make tile clickable
        frame.bind("<Button-1>", lambda e: print(f"{title} clicked"))
        lbl_title.bind("<Button-1>", lambda e: print(f"{title} clicked"))
        lbl_preview.bind("<Button-1>", lambda e: print(f"{title} clicked"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
