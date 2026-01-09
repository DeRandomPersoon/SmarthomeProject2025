"""
Shared base frame that provides the nav bar and a content area used by every page.
Keeps navigation drawing logic in one place so pages only worry about their own widgets.
Extend this class when adding new screens to keep layout consistent.
"""

import tkinter as tk
import math

class BasePage(tk.Frame):
    """Base page with fixed bottom nav bar shared across pages.

    Children should build UI inside `self.content`.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg="#1e1e1e", *args, **kwargs)
        self.parent = parent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # Content container
        self.content = tk.Frame(self, bg="#1e1e1e")
        self.content.grid(row=0, column=0, sticky="nsew")

        # Fixed nav bar at bottom
        self.nav_frame = tk.Frame(self, bg="#1e1e1e")
        self.nav_frame.grid(row=1, column=0, pady=10)
        self.nav_canvases = []
        self.active_nav = 0
        for i in range(4):
            c = tk.Canvas(self.nav_frame, width=70, height=70, bg="#1e1e1e", highlightthickness=0)
            c.grid(row=0, column=i, padx=15)
            c.bind("<Button-1>", lambda e, idx=i: self.on_nav(idx))
            self.nav_canvases.append(c)
        self.draw_nav()

    def hide_nav(self):
        try:
            self.nav_frame.grid_remove()
        except Exception:
            pass

    def show_nav(self):
        try:
            self.nav_frame.grid()
        except Exception:
            pass

    def set_active_nav(self, idx: int):
        self.active_nav = idx
        self.draw_nav()

    def draw_nav(self):
        for i, c in enumerate(self.nav_canvases):
            try:
                c.delete("all")
                if i == self.active_nav:
                    c.create_oval(5, 5, 65, 65, outline="#ff9933", width=4)
                if i == 0:
                    c.create_polygon(18,38, 35,18, 52,38, 52,55, 18,55, fill="", outline="white", width=3)
                    c.create_oval(42,32,48,38, fill="white", outline="")
                    c.create_rectangle(44,22,46,36, fill="white", outline="")
                elif i == 1:
                    c.create_line(18,50,18,22, fill="white", width=2)
                    c.create_line(18,50,52,50, fill="white", width=2)
                    c.create_line(22,44,30,36,38,30,48,22, fill="white", width=3, smooth=False)
                    c.create_oval(20,44,24,48, fill="white", outline="")
                    c.create_oval(28,36,32,40, fill="white", outline="")
                    c.create_oval(36,28,40,32, fill="white", outline="")
                    c.create_oval(46,20,50,24, fill="white", outline="")
                elif i == 2:
                    c.create_oval(18,18,52,52, outline="white", width=3)
                    c.create_line(35,22,35,34, fill="white", width=3)
                elif i == 3:
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
            except Exception:
                pass

    def on_nav(self, idx):
        # Prefer child handler; else bubble to parent if available
        if hasattr(self, 'handle_nav') and callable(getattr(self, 'handle_nav')):
            return self.handle_nav(idx)
        parent_on_nav = getattr(self.parent, 'on_nav', None)
        if callable(parent_on_nav):
            return parent_on_nav(idx)
        # no-op fallback
        return None
