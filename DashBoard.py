# Dashboard.py
"""
Clean TinyHouse Smart Home Dashboard
Shows 4 main tiles: Lights, Energy, Water, Smart Controls
"""

import tkinter as tk
from tkinter import ttk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("TinyHouse Dashboard")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Main container
        container = ttk.Frame(self)
        container.pack(expand=True, fill="both")

        # Load only the main page
        self.frames = {}
        main_page = MainPage(container, self)
        main_page.pack(expand=True, fill="both")
        self.frames["MainPage"] = main_page


class MainPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # Grid config for nice centering
        self.columnconfigure((0, 1), weight=1, uniform="col")
        self.rowconfigure((0, 1), weight=1, uniform="row")

        # Create the 4 main tiles
        self._make_tile(0, 0, "Lights", "#F9E79F")
        self._make_tile(0, 1, "Energy", "#AED6F1")
        self._make_tile(1, 0, "Water", "#A9DFBF")
        self._make_tile(1, 1, "Smart Controls", "#F5B7B1")

    def _make_tile(self, r, c, title, color):
        frame = ttk.Frame(self, borderwidth=2, relief="ridge")
        frame.grid(row=r, column=c, sticky="nsew", padx=20, pady=20)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        bg = tk.Label(frame, bg=color)
        bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        lbl = ttk.Label(frame, text=title, font=("Arial", 18, "bold"))
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Make the whole tile clickable
        frame.bind("<Button-1>", lambda e: print(f"{title} clicked"))
        lbl.bind("<Button-1>", lambda e: print(f"{title} clicked"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
