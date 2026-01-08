import tkinter as tk
from tkinter import ttk
import csv
import os
import threading
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


class AIBoard(tk.Frame):
    """Simple AI tools panel: fit a linear model from local CSV and predict from a user input."""
    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e1e")
        self.parent = parent

        top = tk.Frame(self, bg="#1e1e1e")
        top.pack(fill="x", padx=8, pady=8)
        tk.Label(top, text="AI Tools", bg="#1e1e1e", fg="white", font=("Arial", 16)).pack(side="left")

        form = tk.Frame(self, bg="#1e1e1e")
        form.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(form, text="Dataset:", bg="#1e1e1e", fg="white").grid(row=0, column=0, sticky="w")
        self.dataset_var = tk.StringVar(value="panelen_data.csv")
        self.dataset_combo = ttk.Combobox(form, textvariable=self.dataset_var, values=self._available_datasets(), state="readonly", width=30)
        self.dataset_combo.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        tk.Label(form, text="Cloud cover % (0-100):", bg="#1e1e1e", fg="white").grid(row=1, column=0, sticky="w")
        self.cloud_var = tk.DoubleVar(value=50.0)
        self.cloud_entry = tk.Entry(form, textvariable=self.cloud_var, width=12)
        self.cloud_entry.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        self.coef_label = tk.Label(form, text="Model: a=?, b=?", bg="#1e1e1e", fg="white")
        self.coef_label.grid(row=2, column=0, columnspan=2, pady=6)

        btn_row = tk.Frame(form, bg="#1e1e1e")
        btn_row.grid(row=3, column=0, columnspan=2, pady=6)
        tk.Button(btn_row, text="Fit model", command=self.fit_model).pack(side="left", padx=6)
        tk.Button(btn_row, text="Predict", command=self.predict).pack(side="left", padx=6)
        tk.Button(btn_row, text="Refresh datasets", command=self.refresh).pack(side="left", padx=6)
        tk.Button(btn_row, text="Close", command=lambda: parent.on_nav(0)).pack(side="left", padx=6)

        self.result = tk.Text(self, height=6, bg="#2a2a2a", fg="white")
        self.result.pack(fill="x", padx=8, pady=8)

        self.a = 0.0
        self.b = 0.0

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
        self.result.insert("end", "Datasets refreshed\n")

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
                    self.result.insert("end", f'Not enough data in {os.path.basename(dataset)}\n')
                    return
                coeff = al.gradient_descent(xs, ys, num_iterations=50000, learning_rate=0.0001)
                self.a, self.b = coeff[0], coeff[1]
                self.coef_label.config(text=f"Model: a={self.a:.3f}, b={self.b:.6f}")
                self.result.insert("end", f'Fitted model from {os.path.basename(dataset)}\n  a={self.a:.3f}, b={self.b:.6f}\n')
            except FileNotFoundError:
                self.result.insert("end", f'Dataset not found: {dataset}\n')
            except Exception as e:
                self.result.insert("end", f'Fit error: {e}\n')

        threading.Thread(target=worker, daemon=True).start()
    def predict(self):
        try:
            x = float(self.cloud_var.get())
        except Exception:
            self.result.insert("end", "Invalid cloud cover value\n")
            return
        y = self.a + self.b * x
        self.result.insert("end", f'Input cloud={x} -> Predicted kW: {y:.3f}\n')
