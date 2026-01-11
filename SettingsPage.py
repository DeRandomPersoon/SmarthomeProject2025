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
    import psycopg2
except Exception:
    psycopg2 = None

try:
    from Micro import MicroController
except Exception:
    MicroController = None

try:
    from WiFiController import WiFiController
except Exception:
    WiFiController = None

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.txt")

# Database configuration
DB_HOST = "4.233.209.202"
DB_NAME = "TinyHomeTeam"
DB_USER = "postgres"
DB_PASSWORD = "730879"
DB_PORT = "5432"


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

        # Database section
        tk.Label(form, text="", bg="#1e1e1e").grid(row=5, column=0)  # spacer
        tk.Label(form, text="Database Controls:", bg="#1e1e1e", fg="white", font=("Arial", 12, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 5))
        
        db_row = tk.Frame(form, bg="#1e1e1e")
        db_row.grid(row=7, column=0, columnspan=2, sticky="w", pady=(2, 10))
        tk.Button(db_row, text="Test DB Connection", command=self.test_db_connection, bg="#444444", fg="white").pack(side="left", padx=6)
        tk.Button(db_row, text="Push Data Now", command=self.push_data_now, bg="#444444", fg="white").pack(side="left", padx=6)
        tk.Button(db_row, text="View Database", command=self.view_database, bg="#444444", fg="white").pack(side="left", padx=6)

        self.info_label = tk.Label(form, text="", bg="#1e1e1e", fg="white")
        self.info_label.grid(row=8, column=0, columnspan=2, sticky="w", pady=4)

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

    def test_db_connection(self):
        """Test database connection."""
        if not psycopg2:
            self.info_label.config(text="psycopg2 not installed", fg="red")
            return
        
        self.info_label.config(text="Testing database...", fg="yellow")
        
        def worker():
            try:
                connection = psycopg2.connect(
                    host=DB_HOST,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    port=DB_PORT
                )
                connection.close()
                self.info_label.config(text="✓ Database connection successful!", fg="green")
            except Exception as e:
                self.info_label.config(text=f"✗ Database failed: {e}", fg="red")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def push_data_now(self):
        """Immediately push buffered data to database."""
        if not psycopg2:
            self.info_label.config(text="psycopg2 not installed", fg="red")
            return
        
        self.info_label.config(text="Pushing data...", fg="yellow")
        
        def worker():
            try:
                self._upload_buffered_data()
                self.info_label.config(text="✓ Data pushed successfully!", fg="green")
            except Exception as e:
                self.info_label.config(text=f"✗ Push failed: {e}", fg="red")
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _upload_buffered_data(self):
        """Upload all buffered data from data.txt to database and clear file."""
        if not os.path.exists(DATA_FILE):
            return
        
        try:
            with open(DATA_FILE, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Could not read data file: {e}")
            return
        
        if len(lines) == 0:
            return
        
        try:
            connection = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )
            
            cursor = connection.cursor()
            
            for line in lines:
                line = line.strip()
                
                try:
                    parts = line.split(',')
                    
                    if len(parts) == 2:
                        sensor_name = parts[0].strip()[:50]  # Truncate to 50 chars max
                        value = float(parts[1].strip())
                        
                        sql = "INSERT INTO sensor_metingen (sensor_naam, meting_waarde) VALUES (%s, %s)"
                        cursor.execute(sql, (sensor_name, value))
                        print(f"Uploaded to DB: {sensor_name} -> {value}")
                
                except ValueError:
                    print(f"Invalid data line: {line}")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Clear the file after successful upload
            with open(DATA_FILE, 'w') as f:
                pass
        
        except Exception as e:
            print(f"Database error: {e}")
            raise
    
    def view_database(self):
        """Open popup to view pending and uploaded data."""
        if not psycopg2:
            self.info_label.config(text="psycopg2 not installed", fg="red")
            return
        
        popup = tk.Toplevel(self)
        popup.title("Database Viewer")
        popup.geometry("700x500")
        popup.configure(bg="#2a2a2a")
        
        tk.Label(popup, text="Database Status", bg="#2a2a2a", fg="white", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Create text widget with scrollbar
        frame = tk.Frame(popup, bg="#2a2a2a")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        text = tk.Text(frame, bg="#1e1e1e", fg="white", font=("Courier", 10), yscrollcommand=scrollbar.set)
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)
        
        # Status label
        status_label = tk.Label(popup, text="", bg="#2a2a2a", fg="yellow", font=("Arial", 10))
        status_label.pack(pady=5)
        
        def refresh():
            """Show pending data.txt and database entries."""
            text.delete(1.0, 'end')
            text.insert('end', "Loading...\n")
            status_label.config(text="Loading...", fg="yellow")
            
            def worker():
                try:
                    pending_count = 0
                    
                    # Show pending data from data.txt
                    if os.path.exists(DATA_FILE):
                        try:
                            with open(DATA_FILE, 'r') as f:
                                pending_lines = f.readlines()
                            
                            if pending_lines:
                                text.delete(1.0, 'end')
                                text.insert('end', "=== PENDING (waiting for upload) ===\n")
                                text.insert('end', f"{'Sensor/Device':<25} {'Value':<10}\n")
                                text.insert('end', "-" * 40 + "\n")
                                
                                for line in pending_lines:
                                    line = line.strip()
                                    if line:
                                        try:
                                            parts = line.split(',')
                                            if len(parts) == 2:
                                                sensor = parts[0].strip()
                                                value = parts[1].strip()
                                                value_str = "ON" if value == "1" else ("OFF" if value == "0" else value)
                                                text.insert('end', f"{sensor:<25} {value_str:<10}\n")
                                                pending_count += 1
                                        except Exception:
                                            pass
                                
                                text.insert('end', "\n")
                        except Exception as e:
                            text.delete(1.0, 'end')
                            text.insert('end', f"Could not read data.txt: {e}\n\n")
                    
                    # Show database entries
                    entries = self._get_recent_database_entries(10)
                    
                    if not pending_count and not entries:
                        text.delete(1.0, 'end')
                        text.insert('end', "No pending data and no database entries found\n")
                        status_label.config(text="No data found", fg="orange")
                        return
                    
                    if entries:
                        text.insert('end', "=== DATABASE (uploaded) ===\n")
                        text.insert('end', f"{'Sensor/Device':<25} {'Value':<10} {'Info'}\n")
                        text.insert('end', "-" * 70 + "\n")
                        
                        for entry in entries:
                            sensor = entry[0] if len(entry) > 0 else "Unknown"
                            value = entry[1] if len(entry) > 1 else 0
                            value_str = "ON" if value == 1 else ("OFF" if value == 0 else str(value))
                            
                            info = ""
                            if len(entry) > 2:
                                info = str(entry[2])
                            
                            text.insert('end', f"{sensor:<25} {value_str:<10} {info}\n")
                    
                    msg = f"✓ {pending_count} pending, {len(entries)} in database"
                    status_label.config(text=msg, fg="green")
                except Exception as e:
                    text.delete(1.0, 'end')
                    text.insert('end', f"Error: {e}\n")
                    status_label.config(text=f"Error: {e}", fg="red")
            
            threading.Thread(target=worker, daemon=True).start()
        
        # Button row
        button_frame = tk.Frame(popup, bg="#2a2a2a")
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Refresh", command=refresh, bg="#444444", fg="white", font=("Arial", 11), width=12).pack(side="left", padx=5)
        tk.Button(button_frame, text="Close", command=popup.destroy, bg="#444444", fg="white", font=("Arial", 11), width=12).pack(side="left", padx=5)
        
        # Initial load
        refresh()
    
    def _get_recent_database_entries(self, limit=10):
        """Fetch the most recent entries from the database."""
        if not psycopg2:
            return []
        
        try:
            connection = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )
            
            cursor = connection.cursor()
            
            # Try multiple query strategies
            queries = [
                """SELECT sensor_naam, meting_waarde, 
                         COALESCE(timestamp, NOW()) as time 
                   FROM sensor_metingen 
                   ORDER BY id DESC 
                   LIMIT %s""",
                """SELECT sensor_naam, meting_waarde 
                   FROM sensor_metingen 
                   ORDER BY id DESC 
                   LIMIT %s""",
                """SELECT sensor_naam, meting_waarde, timestamp 
                   FROM sensor_metingen 
                   ORDER BY timestamp DESC 
                   LIMIT %s""",
                """SELECT sensor_naam, meting_waarde 
                   FROM sensor_metingen 
                   LIMIT %s"""
            ]
            
            results = []
            for sql in queries:
                try:
                    cursor.execute(sql, (limit,))
                    results = cursor.fetchall()
                    break
                except Exception:
                    continue
            
            cursor.close()
            connection.close()
            
            return results
        
        except Exception as e:
            print(f"Database query error: {e}")
            return []