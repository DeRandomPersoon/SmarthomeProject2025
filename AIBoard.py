import tkinter as tk
from tkinter import ttk
import csv
import os
import threading
from BasePage import BasePage
import openmeteo_requests
import requests_cache
from retry_requests import retry

try:
    import algroritmes as al
except Exception:
    try:
        from AIFiles import algroritmes as al
    except Exception:
        # attempt to load module directly from AIFiles/algroritmes.py
        try:
            import importlib.util
            path = os.path.join(os.path.dirname(__file__), 'AIFiles', 'algroritmes.py')
            if os.path.exists(path):
                spec = importlib.util.spec_from_file_location('algroritmes', path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                al = mod
            else:
                al = None
        except Exception:
            al = None


class AIBoard(BasePage):
    """Simple AI tools panel: fit a linear model from local CSV and predict from a user input."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        # Use shared layout; hide this page's nav when embedded under MainPage
        self.hide_nav()

        top = tk.Frame(self.content, bg="#1e1e1e")
        top.pack(fill="x", padx=8, pady=8)
        tk.Label(top, text="AI Tools", bg="#1e1e1e", fg="white", font=("Arial", 16)).pack(side="left")

        form = tk.Frame(self.content, bg="#1e1e1e")
        form.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(form, text="Dataset:", bg="#1e1e1e", fg="white").grid(row=0, column=0, sticky="w")
        self.dataset_var = tk.StringVar(value="panelen_data.csv")
        self.dataset_combo = ttk.Combobox(form, textvariable=self.dataset_var, values=self._available_datasets(), state="readonly", width=30)
        self.dataset_combo.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        tk.Label(form, text="Cloud cover % (0-100):", bg="#1e1e1e", fg="white").grid(row=1, column=0, sticky="w")
        self.cloud_var = tk.DoubleVar(value=50.0)
        
        # Display for fetched value
        self.cloud_entry = tk.Label(form, text="Loading...", bg="#2a2a2a", fg="white", width=12, relief="sunken", padx=6, pady=3)
        self.cloud_entry.grid(row=1, column=1, sticky="w", padx=6, pady=6)
        
        # Manual input field as failsafe
        self.cloud_input = tk.Entry(form, textvariable=self.cloud_var, width=12)
        self.cloud_input.grid(row=1, column=2, sticky="w", padx=6, pady=6)
        
        tk.Button(form, text="Fetch", command=self.fetch_cloud_cover).grid(row=1, column=3, sticky="w", padx=6, pady=6)

        self.coef_label = tk.Label(form, text="Model: a=?, b=?", bg="#1e1e1e", fg="white")
        self.coef_label.grid(row=2, column=0, columnspan=2, pady=6)

        btn_row = tk.Frame(form, bg="#1e1e1e")
        btn_row.grid(row=3, column=0, columnspan=2, pady=6)
        tk.Button(btn_row, text="Fit model", command=self.fit_model).pack(side="left", padx=6)
        tk.Button(btn_row, text="Predict", command=self.predict).pack(side="left", padx=6)
        tk.Button(btn_row, text="Refresh datasets", command=self.refresh).pack(side="left", padx=6)
        tk.Button(btn_row, text="Close", command=lambda: self.on_nav(0)).pack(side="left", padx=6)

        self.result = tk.Text(self.content, height=6, bg="#2a2a2a", fg="white")
        self.result.pack(fill="x", padx=8, pady=8)

        self.a = 0.0
        self.b = 0.0

        # initial fetch of cloud cover (non-blocking)
        self.fetch_cloud_cover()
        # initial fit (non-blocking)
        self.fit_model()

    def _available_datasets(self):
        files = []
        base = os.path.dirname(__file__)
        # look in AIBoard folder, AIFiles folder, and project root
        candidates = [base, os.path.join(base, 'AIFiles'), os.path.abspath(os.path.join(base, '..'))]
        for d in candidates:
            for f in ("panelen_data.csv", "panelen_data_extra.csv"):
                p = os.path.join(d, f)
                if os.path.exists(p) and f not in files:
                    files.append(f)
        return files or ["panelen_data.csv"]

    def _find_dataset_path(self, name):
        base = os.path.dirname(__file__)
        candidates = [base, os.path.join(base, 'AIFiles'), os.path.abspath(os.path.join(base, '..'))]
        for d in candidates:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
        # fallback to the provided name (will raise later if missing)
        return os.path.join(base, name)

    def refresh(self):
        self.dataset_combo["values"] = self._available_datasets()
        self.safe_insert("Datasets refreshed\n")

    def safe_insert(self, text):
        """Insert text into result Text widget safely from any thread."""
        try:
            if getattr(self, 'result', None) and self.result.winfo_exists():
                self.result.insert("end", text)
                self.result.see("end")
        except Exception:
            pass

    def safe_set_coef(self, text):
        try:
            if getattr(self, 'coef_label', None) and self.coef_label.winfo_exists():
                self.coef_label.config(text=text)
        except Exception:
            pass

    def fit_model(self):
        if al is None:
            self.result.insert("end", "algroritmes module not found (looked in project root and AIFiles).\nPlease ensure the module is available.\n")
            return
        dataset = self._find_dataset_path(self.dataset_var.get())

        def worker():
            try:
                xs = []
                ys = []
                with open(dataset, newline="", encoding="utf-8") as f:
                    r = csv.DictReader(f)
                    for row in r:
                        try:
                            x = float(row.get('Gem%BewolkingDag') or row.get('Gem%BewolkingDag') or 0)
                            y = float(row.get('KiloWattDag') or row.get('KiloWattDag') or 0)
                        except Exception:
                            continue
                        xs.append(x)
                        ys.append(y)
                if len(xs) < 2:
                    self.after(0, lambda: self.safe_insert(f'Not enough data in {os.path.basename(dataset)}\n'))
                    return
                coeff = al.gradient_descent(xs, ys, num_iterations=50000, learning_rate=0.0001)
                self.a, self.b = coeff[0], coeff[1]
                # update UI on main thread
                self.after(0, lambda: self.safe_set_coef(f"Model: a={self.a:.3f}, b={self.b:.6f}"))
                self.after(0, lambda: self.safe_insert(f'Fitted model from {os.path.basename(dataset)}\n  a={self.a:.3f}, b={self.b:.6f}\n'))
            except FileNotFoundError:
                self.after(0, lambda: self.safe_insert(f'Dataset not found: {dataset}\n'))
            except Exception as e:
                self.after(0, lambda: self.safe_insert(f'Fit error: {e}\n'))

        threading.Thread(target=worker, daemon=True).start()

    def fetch_cloud_cover(self):
        """Fetch current cloud cover from Open-Meteo API"""
        def worker():
            try:
                self.after(0, lambda: self.cloud_entry.config(text="Fetching..."))
                cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
                retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
                openmeteo = openmeteo_requests.Client(session=retry_session)
                
                params = {
                    "latitude": 52.0386111,
                    "longitude": 5.066666666666666,
                    "hourly": "cloud_cover",
                    "forecast_days": 1,
                }
                responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
                
                response = responses[0]
                hourly = response.Hourly()
                hourly_cloud_cover = hourly.Variables(0).ValuesAsNumpy()
                
                # Calculate average cloud cover for today (first 24 hours)
                avg_cloud_cover = float(sum(hourly_cloud_cover[:24]) / 24)
                self.cloud_var.set(avg_cloud_cover)
                
                self.after(0, lambda: self.cloud_entry.config(text=f"{avg_cloud_cover:.1f}%"))
                self.after(0, lambda: self.safe_insert(f'Fetched cloud cover: {avg_cloud_cover:.1f}%\n'))
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: self.cloud_entry.config(text="Error fetching"))
                self.after(0, lambda: self.safe_insert(f'Error fetching cloud cover: {error_msg}\n'))
        
        threading.Thread(target=worker, daemon=True).start()

    def predict(self):
        try:
            x = float(self.cloud_var.get())
        except Exception:
            self.safe_insert("Invalid cloud cover value\n")
            return
        y = self.a + self.b * x
        self.safe_insert(f'Input cloud={x} -> Predicted kW: {y:.3f}\n')
