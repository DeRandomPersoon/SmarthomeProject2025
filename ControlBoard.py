import tkinter as tk
import threading
import json
import os
import datetime
import time
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

DB_HOST = "4.233.209.202"
DB_NAME = "TinyHomeTeam"
DB_USER = "postgres"
DB_PASSWORD = "730879"
DB_PORT = "5432"

class ControlBoard(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.hide_nav()

        top = tk.Frame(self.content, bg="#1e1e1e")
        top.pack(fill="x", padx=10, pady=(10, 0))
        if psycopg2:
            tk.Button(top, text="View Database", command=self.show_database_window, bg="#444444", fg="white").pack(side="right", padx=5)
            tk.Button(top, text="Add Test Data", command=self.add_test_data, bg="#444444", fg="white").pack(side="right", padx=5)

        self.btn_frame = tk.Frame(self.content, bg="#1e1e1e")
        self.btn_frame.pack(expand=True, pady=20)

        self.light_buttons = []
        self.light_on_vars = []
        self.light_off_vars = []

        for i in range(4):
            row = tk.Frame(self.btn_frame, bg="#1e1e1e")
            row.pack(pady=8, anchor='center')

            label = "Light" if i == 0 else ("Curtains" if i == 1 else ("Heating" if i == 2 else "Buzzer"))
            b = tk.Button(
                row,
                text=f"{label}",
                width=14,
                height=2,
                font=("Arial", 16),
                command=lambda n=i: self._device_button_pressed(n),
            )
            b.grid(row=0, column=0, padx=(0,10))
            b._orig_bg = b.cget('bg')
            self.light_buttons.append(b)

            on_var = tk.StringVar(value="07:00")
            off_var = tk.StringVar(value="23:00")
            self.light_on_vars.append(on_var)
            self.light_off_vars.append(off_var)

            tk.Label(row, text="On:", bg="#1e1e1e", fg="white").grid(row=0, column=1)
            on_entry = tk.Entry(row, textvariable=on_var, width=6)
            on_entry.grid(row=0, column=2, padx=(4,10))

            tk.Label(row, text="Off:", bg="#1e1e1e", fg="white").grid(row=0, column=3)
            off_entry = tk.Entry(row, textvariable=off_var, width=6)
            off_entry.grid(row=0, column=4, padx=(4,10))

            on_var.trace_add('write', lambda *a, idx=i: self.per_light_slot_update(idx))
            off_var.trace_add('write', lambda *a, idx=i: self.per_light_slot_update(idx))

            tk.Button(row, text="Clear slot", command=lambda n=i: self.clear_light_slot(n)).grid(row=0, column=5, padx=6)
            tk.Button(row, text="Edit schedule", command=lambda n=i: self.show_schedule_editor(n)).grid(row=0, column=6, padx=6)

        self.status = tk.Label(self.content, text="Pico: not connected", bg="#1e1e1e", fg="white", font=("Arial", 12))
        self.status.pack(pady=8)

        self.ip_var = tk.StringVar(value="192.168.2.98")
        ip_row = tk.Frame(self.content, bg="#1e1e1e")
        ip_row.pack(pady=(0,10))
        tk.Label(ip_row, text="Pico IP:", bg="#1e1e1e", fg="white").pack(side="left", padx=(0,4))
        ip_entry = tk.Entry(ip_row, textvariable=self.ip_var, width=15)
        ip_entry.pack(side="left", padx=4)
        tk.Button(ip_row, text="Connect", command=self._connect_wifi).pack(side="left", padx=6)

        self.micro = None
        self.selected_port = None

        self.schedules = {"lights": [], "curtains": [], "heating": [], "buzzer": []}
        self.light_states = [False] * 3
        self.curtain_states = [False] * 3
        self.buzzer_states = [False]
        self.curtain_duration_var = tk.IntVar(value=5)

        self.log_text = tk.Text(self.content, height=6, bg="#2a2a2a", fg="white")
        self.log_text.pack(fill="x", padx=8, pady=6)

        self._load_schedules()
        self._refresh_schedule_views()

        self._scheduler_stop = False
        threading.Thread(target=self._schedule_worker, daemon=True).start()

        if psycopg2:
            threading.Thread(target=self._database_uploader, daemon=True).start()

        if WiFiController:
            try:
                if os.path.exists(SETTINGS_FILE):
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        s = json.load(f)
                        ip = s.get("pico_ip") or "192.168.2.98"
                        self.ip_var.set(ip)
                        threading.Thread(target=self._connect_wifi_worker, args=(ip,), daemon=True).start()
            except Exception:
                pass

    def _connect_worker(self, port, baud):
        try:
            mc = MicroController()
            ok = mc.connect(port, baud)
            if ok:
                self.micro = mc
                self.selected_port = port
                self.status.config(text=f"Micro: connected ({port})")
            else:
                self.status.config(text="Micro: connect failed")
        except Exception:
            self.status.config(text="Micro: error")

    def _refresh_ports(self):
        if not MicroController:
            self.status.config(text="pyserial not installed")
            return
        try:
            ports = MicroController.list_ports() or []
        except Exception:
            ports = []
        menu = self.port_menu['menu']
        menu.delete(0, 'end')
        for p in ports:
            menu.add_command(label=p, command=lambda v=p: self.port_var.set(v))
        if ports:
            if not self.port_var.get():
                self.port_var.set(ports[0])
            self.status.config(text=f"Ports: {', '.join(ports)}")
        else:
            self.port_var.set("")
            self.status.config(text="No ports found")

    def _connect_selected(self):
        if not MicroController:
            self.status.config(text="pyserial not installed")
            return
        port = self.port_var.get().strip()
        if not port:
            self.status.config(text="Select a port first")
            return
        self.status.config(text=f"Connecting {port}...")
        threading.Thread(target=self._connect_worker, args=(port, 115200), daemon=True).start()

    def _connect_wifi(self):
        """Connect to Pico W over WiFi."""
        if not WiFiController:
            self.status.config(text="requests library not installed")
            return
        ip = self.ip_var.get().strip()
        if not ip:
            self.status.config(text="Enter Pico IP first")
            return
        self.status.config(text=f"Connecting {ip}...")
        threading.Thread(target=self._connect_wifi_worker, args=(ip,), daemon=True).start()

    def _connect_wifi_worker(self, ip):
        """Connect to Pico W in background."""
        try:
            wc = WiFiController(host=ip, port=80)
            ok = wc.connect(ip, 80)
            if ok:
                self.micro = wc
                self.status.config(text=f"Pico: connected ({ip})")
                try:
                    settings = {"pico_ip": ip, "baud": 115200}
                    if os.path.exists(SETTINGS_FILE):
                        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                            settings.update(json.load(f))
                    settings["pico_ip"] = ip
                    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                        json.dump(settings, f, indent=2)
                except Exception:
                    pass
            else:
                self.status.config(text="Pico: connect failed")
        except Exception as e:
            self.status.config(text=f"Pico: error ({e})")

    def _connect_auto(self):
        if not MicroController:
            self.status.config(text="pyserial not installed")
            return
        try:
            port = MicroController.auto_detect()
        except Exception:
            port = None
        if not port:
            self.status.config(text="No port found")
            return
        self.status.config(text=f"Connecting {port}...")
        threading.Thread(target=self._connect_worker, args=(port, 115200), daemon=True).start()

    def toggle_light(self, idx):
        if self.micro and getattr(self.micro, 'is_connected', False):
            self.status.config(text=f"Sending toggle {idx+1}...")
            def worker():
                ok = self.micro.toggle_led(idx + 1)
                if ok:
                    self.light_states[idx] = not self.light_states[idx]
                    self._update_light_visual(idx)
                    device_name = "Light" if idx == 0 else ("Curtain" if idx == 1 else "Heating")
                    self._log_to_database(f"{device_name}_{idx+1}", 1 if self.light_states[idx] else 0)
                self.status.config(text=(f"Toggled {idx+1}" if ok else "Send failed"))
            threading.Thread(target=worker, daemon=True).start()
            return

        self.light_states[idx] = not self.light_states[idx]
        self._update_light_visual(idx)
        self.status.config(text=f"Light {idx+1} toggled (simulated)")

    def _update_light_visual(self, idx):
        b = self.light_buttons[idx]
        if self.light_states[idx]:
            b.config(bg="#ffd966", fg="black")
        else:
            b.config(bg=b._orig_bg, fg="black")

    def _update_curtain_visual(self, idx):
        b = self.light_buttons[idx]
        if self.curtain_states[idx]:
            b.config(bg="#8ec6ff", fg="black")
        else:
            b.config(bg=b._orig_bg, fg="black")

    def _load_schedules(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    s = json.load(f)
                    sched = s.get('schedules') or {}
                    self.schedules['lights'] = sched.get('lights', [])
                    self.schedules['curtains'] = sched.get('curtains', [])
        except Exception:
            pass
        self._set_per_light_vars_from_schedules()

    def _set_per_light_vars_from_schedules(self):
        for i in range(len(self.light_on_vars)):
            slot = None
            try:
                if i == 0:
                    for s in reversed(self.schedules.get('lights', [])):
                        if s.get('light') == i:
                            slot = s
                            break
                    if slot:
                        self.light_on_vars[i].set(slot['on'])
                        self.light_off_vars[i].set(slot['off'])
                elif i == 1:
                    for s in reversed(self.schedules.get('curtains', [])):
                        slot = s
                        break
                    if slot:
                        self.light_on_vars[i].set(slot['open'])
                        self.light_off_vars[i].set(slot['close'])
                elif i == 2:
                    for s in reversed(self.schedules.get('heating', [])):
                        slot = s
                        break
                    if slot:
                        self.light_on_vars[i].set(slot['on'])
                        self.light_off_vars[i].set(slot['off'])
                elif i == 3:
                    for s in reversed(self.schedules.get('buzzer', [])):
                        slot = s
                        break
                    if slot:
                        self.light_on_vars[i].set(slot['time'])
                        self.light_off_vars[i].set('')
            except Exception:
                pass

    def _save_schedules(self):
        try:
            data = {}
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except Exception:
                        data = {}
            data['schedules'] = self.schedules
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.log(f"Save schedules failed: {e}")

    def _refresh_schedule_views(self):
        if hasattr(self, 'light_listbox'):
            try:
                self.light_listbox.delete(0, 'end')
                for s in self.schedules['lights']:
                    if 'light' in s:
                        self.light_listbox.insert('end', f"Light {s['light']+1}: ON {s['on']}  -  OFF {s['off']}")
                    else:
                        self.light_listbox.insert('end', f"ON {s['on']}  -  OFF {s['off']}")
            except Exception:
                pass

        if hasattr(self, 'curtain_listbox'):
            try:
                self.curtain_listbox.delete(0, 'end')
                for s in self.schedules['curtains']:
                    self.curtain_listbox.insert('end', f"OPEN {s['open']} ({s.get('duration',5)}s)  -  CLOSE {s['close']}")
            except Exception:
                pass

        self._set_per_light_vars_from_schedules()

    def add_light_timeslot(self):
        on = self.light_on_vars[0].get().strip() if self.light_on_vars else "07:00"
        off = self.light_off_vars[0].get().strip() if self.light_off_vars else "23:00"
        try:
            _ = datetime.datetime.strptime(on, '%H:%M')
            _ = datetime.datetime.strptime(off, '%H:%M')
        except Exception:
            self.log('Invalid time format for light slot (use HH:MM)')
            return
        self.schedules['lights'].append({'on': on, 'off': off})
        self._save_schedules()
        self._refresh_schedule_views()
        self.log(f'Added light slot: {on} -> {off}')

    def per_light_slot_update(self, idx):
        on = self.light_on_vars[idx].get().strip()
        off = self.light_off_vars[idx].get().strip()
        try:
            _ = datetime.datetime.strptime(on, '%H:%M')
            _ = datetime.datetime.strptime(off, '%H:%M')
        except Exception:
            return

        if idx == 0:
            self.schedules['lights'] = [s for s in self.schedules['lights'] if s.get('light') != idx]
            self.schedules['lights'].append({'light': idx, 'on': on, 'off': off})
            self._save_schedules()
            self._refresh_schedule_views()
            self.log(f'Updated light {idx+1} slot: {on} -> {off}')
        elif idx == 1:
            dur = int(self.curtain_duration_var.get()) if getattr(self, 'curtain_duration_var', None) else 5
            self.schedules['curtains'].append({'open': on, 'close': off, 'duration': dur, 'last_open': None, 'last_close': None})
            self._save_schedules()
            self._refresh_schedule_views()
            self.log(f'Updated curtains slot: {on} -> {off} (+{dur}s)')
        else:
            self.schedules['heating'] = [s for s in self.schedules['heating']]
            self.schedules['heating'] = []
            self.schedules['heating'].append({'on': on, 'off': off})
            self._save_schedules()
            self._refresh_schedule_views()
            self.log(f'Updated heating slot: {on} -> {off}')

    def clear_light_slot(self, idx):
        before = len(self.schedules['lights'])
        self.schedules['lights'] = [s for s in self.schedules['lights'] if s.get('light') != idx]
        after = len(self.schedules['lights'])
        if before != after:
            self._save_schedules()
            self._refresh_schedule_views()
            self.log(f'Cleared slot for light {idx+1}')

    def show_schedule_editor(self, idx):
        if idx == 0:
            self._show_light_schedule_popup(idx)
        elif idx == 1:
            self._show_curtain_schedule_popup()
        elif idx == 2:
            self._show_heating_schedule_popup()
        else:
            self._show_buzzer_schedule_popup()

    def _show_light_schedule_popup(self, idx):
        popup = tk.Toplevel(self)
        popup.title(f"Light {idx+1} schedules")
        popup.geometry("420x300")

        lb = tk.Listbox(popup, width=48, height=8)
        lb.pack(padx=8, pady=8)

        tk.Label(popup, text="Use this popup to manage multiple on/off slots for the device.", bg="#ffffff", fg="#000000").pack(padx=8, pady=(0,6))

        def refresh_list():
            lb.delete(0, 'end')
            for i, s in enumerate(self.schedules.get('lights', [])):
                if s.get('light') == idx:
                    lb.insert('end', f"{i}: ON {s['on']} - OFF {s['off']}")

        on_var = tk.StringVar(value=self.light_on_vars[idx].get())
        off_var = tk.StringVar(value=self.light_off_vars[idx].get())

        row = tk.Frame(popup)
        row.pack(padx=8, pady=4)
        tk.Label(row, text="On (HH:MM):").grid(row=0, column=0)
        tk.Entry(row, textvariable=on_var, width=8).grid(row=0, column=1, padx=6)
        tk.Label(row, text="Off (HH:MM):").grid(row=0, column=2)
        tk.Entry(row, textvariable=off_var, width=8).grid(row=0, column=3, padx=6)

        def add_slot():
            try:
                _ = datetime.datetime.strptime(on_var.get(), '%H:%M')
                _ = datetime.datetime.strptime(off_var.get(), '%H:%M')
            except Exception:
                self.log('Invalid time format (use HH:MM)')
                return
            self.schedules['lights'].append({'light': idx, 'on': on_var.get(), 'off': off_var.get()})
            self._save_schedules()
            self._refresh_schedule_views()
            refresh_list()

        def remove_selected():
            sel = lb.curselection()
            if not sel:
                return
            # need to find nth entry for this light
            # build filtered index list
            indices = [i for i, s in enumerate(self.schedules.get('lights', [])) if s.get('light') == idx]
            try:
                actual = indices[sel[0]]
                self.schedules['lights'].pop(actual)
                self._save_schedules()
                self._refresh_schedule_views()
                refresh_list()
            except Exception:
                pass

        tk.Button(popup, text="Add slot", command=add_slot).pack(padx=6, pady=6)
        tk.Button(popup, text="Remove selected", command=remove_selected).pack(padx=6)
        refresh_list()
    def _show_curtain_schedule_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Curtain schedules")
        popup.geometry("480x320")

        lb = tk.Listbox(popup, width=64, height=8)
        lb.pack(padx=8, pady=8)

        def refresh_list():
            lb.delete(0, 'end')
            for i, s in enumerate(self.schedules.get('curtains', [])):
                lb.insert('end', f"{i}: OPEN {s['open']} (+{s.get('duration',5)}s) - CLOSE {s['close']}")

        open_var = tk.StringVar(value="07:00")
        close_var = tk.StringVar(value="22:00")
        duration_var = tk.IntVar(value=self.curtain_duration_var.get())

        row = tk.Frame(popup)
        row.pack(padx=8, pady=4)
        tk.Label(row, text="Open (HH:MM):").grid(row=0, column=0)
        tk.Entry(row, textvariable=open_var, width=8).grid(row=0, column=1, padx=6)
        tk.Label(row, text="Close (HH:MM):").grid(row=0, column=2)
        tk.Entry(row, textvariable=close_var, width=8).grid(row=0, column=3, padx=6)
        tk.Label(row, text="Duration (s):").grid(row=1, column=0)
        tk.Entry(row, textvariable=duration_var, width=8).grid(row=1, column=1, padx=6)

        def add_slot():
            try:
                _ = datetime.datetime.strptime(open_var.get(), '%H:%M')
                _ = datetime.datetime.strptime(close_var.get(), '%H:%M')
            except Exception:
                self.log('Invalid time format (use HH:MM)')
                return
            try:
                d = int(duration_var.get())
            except Exception:
                self.log('Invalid duration')
                return
            self.schedules['curtains'].append({'open': open_var.get(), 'close': close_var.get(), 'duration': d, 'last_open': None, 'last_close': None})
            self._save_schedules()
            self._refresh_schedule_views()
            refresh_list()

        def remove_selected():
            sel = lb.curselection()
            if not sel:
                return
            try:
                idx = sel[0]
                self.schedules['curtains'].pop(idx)
                self._save_schedules()
                self._refresh_schedule_views()
                refresh_list()
            except Exception:
                pass

        tk.Button(popup, text="Add slot", command=add_slot).pack(padx=6, pady=6)
        tk.Button(popup, text="Remove selected", command=remove_selected).pack(padx=6)

    def _show_heating_schedule_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Heating schedules")
        popup.geometry("420x300")

        lb = tk.Listbox(popup, width=48, height=8)
        lb.pack(padx=8, pady=8)

        tk.Label(popup, text="Use this popup to manage heating on/off schedules.", bg="#ffffff", fg="#000000").pack(padx=8, pady=(0,6))

        def refresh_list():
            lb.delete(0, 'end')
            for i, s in enumerate(self.schedules.get('heating', [])):
                lb.insert('end', f"{i}: ON {s['on']} - OFF {s['off']}")

        on_var = tk.StringVar(value=self.light_on_vars[2].get())
        off_var = tk.StringVar(value=self.light_off_vars[2].get())

        row = tk.Frame(popup)
        row.pack(padx=8, pady=4)
        tk.Label(row, text="On (HH:MM):").grid(row=0, column=0)
        tk.Entry(row, textvariable=on_var, width=8).grid(row=0, column=1, padx=6)
        tk.Label(row, text="Off (HH:MM):").grid(row=0, column=2)
        tk.Entry(row, textvariable=off_var, width=8).grid(row=0, column=3, padx=6)

        def add_slot():
            try:
                _ = datetime.datetime.strptime(on_var.get(), '%H:%M')
                _ = datetime.datetime.strptime(off_var.get(), '%H:%M')
            except Exception:
                self.log('Invalid time format (use HH:MM)')
                return
            self.schedules['heating'].append({'on': on_var.get(), 'off': off_var.get()})
            self._save_schedules()
            self._refresh_schedule_views()
            refresh_list()

        def remove_selected():
            sel = lb.curselection()
            if not sel:
                return
            try:
                idx = sel[0]
                self.schedules['heating'].pop(idx)
                self._save_schedules()
                self._refresh_schedule_views()
                refresh_list()
            except Exception:
                pass

        tk.Button(popup, text="Add slot", command=add_slot).pack(padx=6, pady=6)
        tk.Button(popup, text="Remove selected", command=remove_selected).pack(padx=6)

        refresh_list()
    def remove_light_timeslot(self):
        if hasattr(self, 'light_listbox'):
            sel = self.light_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            try:
                slot = self.schedules['lights'].pop(idx)
                self._save_schedules()
                self._refresh_schedule_views()
                self.log(f'Removed light slot: {slot["on"]} -> {slot["off"]}')
            except Exception:
                pass
        else:
            self.log('No inline light list available - use Edit schedule on the device to remove slots')

    def add_curtain_timeslot(self):
        open_t = self.curtain_open_var.get().strip()
        close_t = self.curtain_close_var.get().strip()
        try:
            duration = int(self.curtain_duration_var.get())
        except Exception:
            self.log('Invalid duration for curtain slot')
            return
        try:
            _ = datetime.datetime.strptime(open_t, '%H:%M')
            _ = datetime.datetime.strptime(close_t, '%H:%M')
        except Exception:
            self.log('Invalid time format for curtain slot (use HH:MM)')
            return
        slot = {'open': open_t, 'close': close_t, 'duration': int(duration), 'last_open': None, 'last_close': None}
        self.schedules['curtains'].append(slot)
        self._save_schedules()
        self._refresh_schedule_views()
        self.log(f'Added curtain slot: {open_t} (+{duration}s) -> {close_t}')

    def remove_curtain_timeslot(self):
        if hasattr(self, 'curtain_listbox'):
            sel = self.curtain_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            try:
                slot = self.schedules['curtains'].pop(idx)
                self._save_schedules()
                self._refresh_schedule_views()
                self.log(f'Removed curtain slot: {slot.get("open")} -> {slot.get("close")}')
            except Exception:
                pass
        else:
            self.log('No inline curtain list available - use Edit schedule on the device to remove slots')

    def _schedule_worker(self):
        while not getattr(self, '_scheduler_stop', False):
            now = datetime.datetime.now()
            now_time = now.time()

            for slot in self.schedules.get('lights', []):
                try:
                    on_t = datetime.datetime.strptime(slot['on'], '%H:%M').time()
                    off_t = datetime.datetime.strptime(slot['off'], '%H:%M').time()
                except Exception:
                    continue
                desired = self._is_time_in_range(on_t, off_t, now_time)
                idx = slot.get('light', 0)
                if not isinstance(idx, int) or idx < 0 or idx >= len(self.light_states):
                    idx = 0
                if desired != self.light_states[idx]:
                    self.set_light_state(idx, desired, reason='schedule')

            for slot in self.schedules.get('heating', []):
                try:
                    on_h = datetime.datetime.strptime(slot['on'], '%H:%M').time()
                    off_h = datetime.datetime.strptime(slot['off'], '%H:%M').time()
                except Exception:
                    continue
                desired_h = self._is_time_in_range(on_h, off_h, now_time)
                if desired_h != self.light_states[2]:
                    self.set_light_state(2, desired_h, reason='schedule')

            for slot in self.schedules.get('curtains', []):
                try:
                    open_t = datetime.datetime.strptime(slot['open'], '%H:%M').time()
                    close_t = datetime.datetime.strptime(slot['close'], '%H:%M').time()
                except Exception:
                    continue
                if now_time.hour == open_t.hour and now_time.minute == open_t.minute:
                    if slot.get('last_open') != now.date().isoformat():
                        self.open_curtain(1, slot.get('duration', 5), reason='schedule')
                        slot['last_open'] = now.date().isoformat()
                        self._save_schedules()
                if now_time.hour == close_t.hour and now_time.minute == close_t.minute:
                    if slot.get('last_close') != now.date().isoformat():
                        self.close_curtain(1, reason='schedule')
                        slot['last_close'] = now.date().isoformat()
                        self._save_schedules()

            for slot in self.schedules.get('buzzer', []):
                try:
                    buzzer_t = datetime.datetime.strptime(slot['time'], '%H:%M').time()
                except Exception:
                    continue
                if now_time.hour == buzzer_t.hour and now_time.minute == buzzer_t.minute:
                    if slot.get('last_trigger') != now.date().isoformat():
                        self.trigger_buzzer(reason='alarm')
                        slot['last_trigger'] = now.date().isoformat()
                        self._save_schedules()

            for _ in range(4):
                if getattr(self, '_scheduler_stop', False):
                    break
                time.sleep(5)

    def _is_time_in_range(self, start, end, now_time):
        if start <= end:
            return start <= now_time < end
        else:
            return now_time >= start or now_time < end

    def set_light_state(self, idx, on, reason=''):
        self.light_states[idx] = bool(on)
        self._update_light_visual(idx)
        name = "Light" if idx == 0 else ("Curtain" if idx == 1 else "Heating")
        self.log(f'{name} {idx+1} -> {"ON" if on else "OFF"} ({reason})')

    def open_curtain(self, idx, duration=5, reason=''):
        self.curtain_states[idx] = True
        self._update_curtain_visual(idx)
        self.log(f'Curtain {idx+1} opened for {duration}s ({reason})')
        def closer():
            try:
                time.sleep(duration)
                self.close_curtain(idx, reason='auto')
            except Exception:
                pass
        threading.Thread(target=closer, daemon=True).start()

    def _device_button_pressed(self, idx):
        if idx == 0:
            self.toggle_light(0)
        elif idx == 1:
            dur = int(self.curtain_duration_var.get()) if getattr(self, 'curtain_duration_var', None) else 5
            self.open_curtain(1, duration=dur, reason='manual')
        elif idx == 2:
            new_state = not self.light_states[2]
            self.set_light_state(2, new_state, reason='manual')
        elif idx == 3:
            self.trigger_buzzer(reason='manual')

    def close_curtain(self, idx, reason=''):
        self.curtain_states[idx] = False
        self._update_curtain_visual(idx)
        self.log(f'Curtain {idx+1} closed ({reason})')

    def trigger_buzzer(self, reason=''):
        """Trigger buzzer pulse on Pico W."""
        if self.micro and getattr(self.micro, 'is_connected', False):
            self.status.config(text="Sending buzzer pulse...")
            def worker():
                try:
                    resp = self.micro.send_command("BUZZER PULSE")
                    self.log(f'Buzzer triggered ({reason})')
                    self._log_to_database("Buzzer", 1)
                    self.status.config(text="Buzzer pulsed")
                except Exception as e:
                    self.log(f'Buzzer failed: {e}')
                    self.status.config(text="Buzzer failed")
            threading.Thread(target=worker, daemon=True).start()
        else:
            self.log(f'Buzzer triggered (simulated) ({reason})')
            self.status.config(text="Buzzer pulsed (simulated)")

    def _show_buzzer_schedule_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Buzzer Alarm schedules")
        popup.geometry("420x300")

        lb = tk.Listbox(popup, width=48, height=8)
        lb.pack(padx=8, pady=8)

        tk.Label(popup, text="Set alarm times for buzzer to trigger.", bg="#ffffff", fg="#000000").pack(padx=8, pady=(0,6))

        def refresh_list():
            lb.delete(0, 'end')
            for i, s in enumerate(self.schedules.get('buzzer', [])):
                lb.insert('end', f"{i}: ALARM {s['time']}")

        time_var = tk.StringVar(value="07:00")

        row = tk.Frame(popup)
        row.pack(padx=8, pady=4)
        tk.Label(row, text="Alarm Time (HH:MM):").grid(row=0, column=0)
        tk.Entry(row, textvariable=time_var, width=8).grid(row=0, column=1, padx=6)

        def add_slot():
            try:
                _ = datetime.datetime.strptime(time_var.get(), '%H:%M')
            except Exception:
                self.log('Invalid time format (use HH:MM)')
                return
            self.schedules['buzzer'].append({'time': time_var.get(), 'last_trigger': None})
            self._save_schedules()
            self._refresh_schedule_views()
            refresh_list()

        def remove_selected():
            sel = lb.curselection()
            if not sel:
                return
            try:
                self.schedules['buzzer'].pop(sel[0])
                self._save_schedules()
                self._refresh_schedule_views()
                refresh_list()
            except Exception:
                pass

        tk.Button(popup, text="Add alarm", command=add_slot).pack(padx=6, pady=6)
        tk.Button(popup, text="Remove selected", command=remove_selected).pack(padx=6)
        refresh_list()

    def add_test_data(self):
        try:
            self._log_to_database("test_sensor", 999)
            self._log_to_database("Light_1", 1)
            self._log_to_database("Motion_Sensor", 1)
            self._log_to_database("Heating_3", 0)
            
            file_path = os.path.abspath(DATA_FILE)
            self.log(f"Test data added to: {file_path}")
            self.status.config(text=f"Test data added to data.txt")
        except Exception as e:
            self.log(f"Failed to add test data: {e}")
            self.status.config(text=f"Test data failed: {e}")

    def _log_to_database(self, sensor_name, value):
        if not psycopg2:
            return
        
        if not os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'w') as f:
                    pass
            except Exception as e:
                print(f"Create data file failed: {e}")
                return
        
        try:
            with open(DATA_FILE, 'a') as f:
                f.write(f"{sensor_name}, {value}\n")
        except Exception as e:
            print(f"Write data file failed: {e}")
    
    def _database_uploader(self):
        while not getattr(self, '_scheduler_stop', False):
            try:
                self._upload_buffered_data()
            except Exception as e:
                print(f"Database upload error: {e}")
            time.sleep(5)
    
    def _upload_buffered_data(self):
        if not os.path.exists(DATA_FILE):
            return
        
        try:
            with open(DATA_FILE, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Read data file failed: {e}")
            return
        
        if len(lines) == 0:
            return
        
        pending_lines = []
        uploaded_lines = []
        
        for line in lines:
            if line.strip():
                pending_lines.append(line)
        
        if len(pending_lines) == 0:
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
            
            newly_uploaded = []
            
            for line in pending_lines:
                line = line.strip()
                
                try:
                    parts = line.split(',')
                    
                    if len(parts) == 2:
                        sensor_name = parts[0].strip()[:50]
                        value = float(parts[1].strip())
                        
                        sql = "INSERT INTO sensor_metingen (sensor_naam, meting_waarde) VALUES (%s, %s)"
                        cursor.execute(sql, (sensor_name, value))
                        
                        newly_uploaded.append(f"{line}\n")
                        self.log(f"Uploaded: {sensor_name} -> {value}")
                
                except ValueError:
                    self.log(f"Invalid data line: {line}")
                    newly_uploaded.append(f"[ERROR] {line}\n")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            all_uploaded = uploaded_lines + newly_uploaded
            recent_uploaded = all_uploaded[-50:]
            
            with open(DATA_FILE, 'w') as f:
                for line in recent_uploaded:
                    f.write(line)
        
        except Exception as e:
            self.log(f"Database error: {e}")
    
    def _get_recent_database_entries(self, limit=10):
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
            
            connection.rollback()
            cursor = connection.cursor()
            
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
            last_error = None
            
            for sql in queries:
                try:
                    cursor.execute(sql, (limit,))
                    results = cursor.fetchall()
                    break
                except Exception as e:
                    last_error = e
                    continue
            
            cursor.close()
            connection.close()
            
            if not results and last_error:
                print(f"DB queries failed: {last_error}")
            
            return results
        
        except Exception as e:
            print(f"DB connection failed: {e}")
            return []
    
    def show_database_window(self):
        if not psycopg2:
            self.log("psycopg2 library not installed")
            return
        
        popup = tk.Toplevel(self)
        popup.title("Recent Database Entries")
        popup.geometry("600x400")
        popup.configure(bg="#2a2a2a")
        
        tk.Label(popup, text="10 Most Recent Events", bg="#2a2a2a", fg="white", font=("Arial", 14, "bold")).pack(pady=10)
        
        frame = tk.Frame(popup, bg="#2a2a2a")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        text = tk.Text(frame, bg="#1e1e1e", fg="white", font=("Courier", 10), yscrollcommand=scrollbar.set)
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)
        
        status_label = tk.Label(popup, text="", bg="#2a2a2a", fg="yellow", font=("Arial", 10))
        status_label.pack(pady=5)
        
        def test_connection():
            status_label.config(text="Testing connection...", fg="yellow")
            
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
                    status_label.config(text="✓ Connection successful!", fg="green")
                    self.log("Database connection test: SUCCESS")
                except Exception as e:
                    status_label.config(text=f"✗ Connection failed: {e}", fg="red")
                    self.log(f"Database connection test: FAILED - {e}")
            
            threading.Thread(target=worker, daemon=True).start()
        
        def push_now():
            status_label.config(text="Pushing data...", fg="yellow")
            
            def worker():
                try:
                    self._upload_buffered_data()
                    status_label.config(text="✓ Data pushed successfully!", fg="green")
                    self.log("Manual data push completed")
                except Exception as e:
                    status_label.config(text=f"✗ Push failed: {e}", fg="red")
                    self.log(f"Manual data push failed: {e}")
            
            threading.Thread(target=worker, daemon=True).start()
        
        def refresh():
            text.delete(1.0, 'end')
            text.insert('end', "Loading...\n")
            status_label.config(text="Pulling data...", fg="yellow")
            
            def worker():
                try:
                    file_path = os.path.abspath(DATA_FILE)
                    text.delete(1.0, 'end')
                    text.insert('end', f"Data file: {file_path}\n\n")
                    
                    pending_count = 0
                    if os.path.exists(DATA_FILE):
                        try:
                            with open(DATA_FILE, 'r') as f:
                                all_lines = f.readlines()
                            
                            pending_lines = [line for line in all_lines if line.strip()]
                            
                            if pending_lines:
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
                            text.insert('end', f"Could not read data.txt: {e}\n\n")
                    else:
                        text.insert('end', "data.txt does not exist yet. Click 'Add Test Data' button to create it.\n\n")
                    
                    entries = self._get_recent_database_entries(10)
                    
                    if entries:
                        text.insert('end', "=== DATABASE (from server) ===\n")
                        text.insert('end', f"{'Sensor/Device':<25} {'Value':<10} {'Timestamp'}\n")
                        text.insert('end', "-" * 70 + "\n")
                        
                        for entry in entries:
                            if len(entry) == 3:
                                sensor, value, timestamp = entry
                                value_str = "ON" if value == 1 else ("OFF" if value == 0 else str(value))
                                text.insert('end', f"{sensor:<25} {value_str:<10} {timestamp}\n")
                            elif len(entry) == 2:
                                sensor, value = entry
                                value_str = "ON" if value == 1 else ("OFF" if value == 0 else str(value))
                                text.insert('end', f"{sensor:<25} {value_str:<10} (no timestamp)\n")
                    elif os.path.exists(DATA_FILE):
                        text.insert('end', "No database entries found.\n")
                    
                    msg = f"✓ {pending_count} pending, {len(entries)} in database"
                    status_label.config(text=msg, fg="green")
                except Exception as e:
                    text.delete(1.0, 'end')
                    text.insert('end', f"Error fetching data: {e}\n")
                    status_label.config(text=f"✗ Pull failed: {e}", fg="red")
            
            threading.Thread(target=worker, daemon=True).start()
        
        button_frame = tk.Frame(popup, bg="#2a2a2a")
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Test Connection", command=test_connection, bg="#444444", fg="white", font=("Arial", 11), width=15).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Push Now", command=push_now, bg="#444444", fg="white", font=("Arial", 11), width=15).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Pull / Refresh", command=refresh, bg="#444444", fg="white", font=("Arial", 11), width=15).grid(row=0, column=2, padx=5)
        
        refresh()

    def log(self, msg):
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.log_text.insert('end', f"[{ts}] {msg}\n")
            self.log_text.see('end')
        except Exception:
            pass