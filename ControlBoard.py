import tkinter as tk
import threading
import json
import os

try:
    from Micro import MicroController
except Exception:
    MicroController = None

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


class ControlBoard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e1e")
        self.parent = parent

        # Top bar with Open Settings button
        top = tk.Frame(self, bg="#1e1e1e")
        top.pack(fill="x", padx=10, pady=(10, 0))
        settings_btn = tk.Button(top, text="Open Settings", command=lambda: self.parent.on_nav(3))
        settings_btn.pack(side="right")

        # Vertical buttons
        self.btn_frame = tk.Frame(self, bg="#1e1e1e")
        self.btn_frame.pack(expand=True, pady=20)

        self.light_buttons = []
        for i in range(4):
            b = tk.Button(
                self.btn_frame,
                text=f"Light {i+1}",
                width=20,
                height=2,
                font=("Arial", 16),
                command=lambda n=i: self.toggle_light(n),
            )
            b.pack(pady=8)
            self.light_buttons.append(b)

        self.status = tk.Label(self, text="Micro: not connected", bg="#1e1e1e", fg="white", font=("Arial", 12))
        self.status.pack(pady=8)

        self.micro = None
        self.selected_port = None

        # Try auto-connect using saved settings (if available)
        if MicroController:
            try:
                if os.path.exists(SETTINGS_FILE):
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        s = json.load(f)
                        port = s.get("serial_port") or ""
                        baud = s.get("baud", 115200)
                        if port:
                            threading.Thread(target=self._connect_worker, args=(port, baud), daemon=True).start()
            except Exception:
                pass

    def _connect_worker(self, port, baud):
        try:
            mc = MicroController()
            ok = mc.connect(port, baud)  # pass baud through
            if ok:
                self.micro = mc
                self.selected_port = port
                self.status.config(text=f"Micro: connected ({port})")
            else:
                self.status.config(text="Micro: connect failed")
        except Exception:
            self.status.config(text="Micro: error")

    def toggle_light(self, idx):
        if not self.micro or not self.micro.is_connected:
            self.status.config(text="Micro not connected")
            return

        self.status.config(text=f"Sending toggle {idx+1}...")
        def worker():
            ok = self.micro.toggle_led(idx + 1)
            self.status.config(text=(f"Toggled {idx+1}" if ok else "Send failed"))
        threading.Thread(target=worker, daemon=True).start()