"""
Settings page for configuring how the desktop app talks to the Pico.
Holds serial port options, WiFi connection testing, and persists selections to disk.
Keep all connection-related testing here so the other pages stay focused on controls.
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import threading
from BasePage import BasePage

try:
    from Micro import MicroController
except Exception:
    MicroController = None

try:
    from WiFiController import WiFiController
except Exception:
    WiFiController = None

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


class SettingsPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        # Hide this page's nav; MainPage provides the visible one
        self.hide_nav()
        self.micro = None

        # Load persisted settings
        self.settings = self.load_settings()

        top = tk.Frame(self.content, bg="#1e1e1e")
        top.pack(fill="x", padx=8, pady=8)
        tk.Label(top, text="Device settings", bg="#1e1e1e", fg="white", font=("Arial", 16)).pack(side="left")

        form = tk.Frame(self.content, bg="#1e1e1e")
        form.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(form, text="Serial port:", bg="#1e1e1e", fg="white").grid(row=0, column=0, sticky="w")
        self.port_var = tk.StringVar(value=self.settings.get("serial_port", ""))
        self.port_combo = ttk.Combobox(form, textvariable=self.port_var, values=self._list_ports(), state="readonly", width=40)
        self.port_combo.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        tk.Label(form, text="Baud:", bg="#1e1e1e", fg="white").grid(row=1, column=0, sticky="w")
        self.baud_var = tk.IntVar(value=self.settings.get("baud", 115200))
        self.baud_entry = tk.Entry(form, textvariable=self.baud_var, width=12)
        self.baud_entry.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        btn_row = tk.Frame(form, bg="#1e1e1e")
        btn_row.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 10))
        tk.Button(btn_row, text="Refresh ports", command=self.refresh_ports).pack(side="left", padx=6)
        tk.Button(btn_row, text="Auto-detect", command=self.auto_detect).pack(side="left", padx=6)
        tk.Button(btn_row, text="Test connect", command=self.test_connect).pack(side="left", padx=6)
        tk.Button(btn_row, text="Save", command=self.save_settings).pack(side="left", padx=6)
        tk.Button(btn_row, text="Close", command=lambda: self.on_nav(0)).pack(side="left", padx=6)

        # WiFi testing under the serial controls
        tk.Label(form, text="Pico IP:", bg="#1e1e1e", fg="white").grid(row=3, column=0, sticky="w")
        self.ip_var = tk.StringVar(value=self.settings.get("pico_ip", ""))
        self.ip_entry = tk.Entry(form, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=3, column=1, sticky="w", padx=6, pady=6)

        wifi_row = tk.Frame(form, bg="#1e1e1e")
        wifi_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=(2, 10))
        tk.Button(wifi_row, text="Test WiFi connect", command=self.test_wifi_connect).pack(side="left", padx=6)

        self.info_label = tk.Label(form, text="", bg="#1e1e1e", fg="white")
        self.info_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=4)

    def _list_ports(self):
        if MicroController:
            try:
                return MicroController.list_ports()
            except Exception:
                return []
        return []

    def refresh_ports(self):
        self.port_combo["values"] = self._list_ports()
        self.info_label.config(text="Ports refreshed")

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"serial_port": "", "baud": 115200, "pico_ip": ""}

    def save_settings(self):
        self.settings["serial_port"] = self.port_var.get()
        self.settings["baud"] = int(self.baud_var.get())
        self.settings["pico_ip"] = self.ip_var.get().strip()
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
            self.info_label.config(text="Settings saved")
        except Exception as e:
            self.info_label.config(text=f"Save failed: {e}")

    def auto_detect(self):
        self.info_label.config(text="Auto-detecting...")
        def worker():
            try:
                p = MicroController.auto_detect() if MicroController else None
            except Exception:
                p = None
            self.port_var.set(p or "")
            self.info_label.config(text=f"Detected: {p}" if p else "No device found")
        threading.Thread(target=worker, daemon=True).start()

    def test_connect(self):
        port = self.port_var.get()
        baud = int(self.baud_var.get())
        if not port:
            self.info_label.config(text="Select a port first")
            return
        if not MicroController:
            self.info_label.config(text="pyserial not installed")
            return

        self.info_label.config(text="Testing connection...")
        def worker():
            try:
                mc = MicroController()
                ok = mc.connect(port)
                if ok:
                    mc.disconnect()
                self.info_label.config(text=f"Connected to {port}" if ok else "Connection failed")
            except Exception as e:
                self.info_label.config(text=f"Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def test_wifi_connect(self):
        ip = self.ip_var.get().strip()
        if not ip:
            self.info_label.config(text="Enter Pico IP first")
            return
        if not WiFiController:
            self.info_label.config(text="requests not installed")
            return

        self.info_label.config(text="Testing WiFi...")

        def worker():
            try:
                wc = WiFiController(host=ip, port=80, timeout=2.0)
                ok = wc.connect(ip, 80)
                msg = f"WiFi OK: {ip}" if ok else "WiFi connect failed"
            except Exception as e:
                msg = f"WiFi error: {e}"
            self.info_label.after(0, lambda: self.info_label.config(text=msg))

        threading.Thread(target=worker, daemon=True).start()