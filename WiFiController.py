"""
Lightweight HTTP client for talking to the Pico W firmware endpoints.
Wraps GET calls for toggling lights and buzzer while handling basic connection testing.
Used as a drop-in replacement for the old serial-based MicroController.
"""
import requests
import threading


class WiFiController:
    """
    HTTP client for controlling Pico W over WiFi.
    
    Replaces serial-based MicroController for WiFi-enabled Pico devices.
    """
    def __init__(self, host="pico.local", port=80, timeout=2.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.is_connected = False
        self.base_url = f"http://{host}:{port}"

    def connect(self, host=None, port=None):
        """Test connection to the Pico W HTTP server."""
        if host:
            self.host = host
        if port:
            self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        try:
            resp = requests.get(f"{self.base_url}/state", timeout=self.timeout)
            if resp.status_code == 200:
                self.is_connected = True
                return True
        except Exception as e:
            print(f"WiFi connect failed: {e}")
        self.is_connected = False
        return False

    def disconnect(self):
        """No-op for HTTP (stateless)."""
        self.is_connected = False

    def send_command(self, cmd, timeout=None):
        """Send an HTTP command and return response."""
        if not self.is_connected:
            raise RuntimeError("Not connected to Pico W")
        
        t = timeout or self.timeout
        # Use longer timeout for buzzer pulse (needs 2+ seconds)
        if cmd == "BUZZER PULSE":
            t = 5.0
        
        try:
            if cmd == "PING":
                resp = requests.get(f"{self.base_url}/state", timeout=t)
            elif cmd == "TOGGLE 1":
                resp = requests.get(f"{self.base_url}/toggle", timeout=t)
            elif cmd == "STATE 1":
                resp = requests.get(f"{self.base_url}/state", timeout=t)
            elif cmd == "BUZZER ON":
                resp = requests.get(f"{self.base_url}/buzzer/on", timeout=t)
            elif cmd == "BUZZER OFF":
                resp = requests.get(f"{self.base_url}/buzzer/off", timeout=t)
            elif cmd == "BUZZER PULSE":
                resp = requests.get(f"{self.base_url}/buzzer/pulse", timeout=t)
            elif cmd == "BUTTON CHECK":
                resp = requests.get(f"{self.base_url}/button/check", timeout=t)
            else:
                return ""
            
            if resp.status_code == 200:
                data = resp.json()
                # Try to return state, buzzer, pressed, or temp value
                return data.get("state", data.get("buzzer", data.get("pressed", data.get("temp", ""))))
            return ""
        except Exception as e:
            print(f"WiFi command failed: {e}")
            return ""

    def send_command_async(self, cmd, callback=None):
        """Send a command in a background thread."""
        def _worker():
            resp = ""
            try:
                resp = self.send_command(cmd)
            except Exception as e:
                resp = f"ERR {e}"
            if callback:
                try:
                    callback(resp)
                except Exception:
                    pass
        threading.Thread(target=_worker, daemon=True).start()

    def toggle_led(self, idx):
        """Send a toggle command (idx is ignored; always toggles device 1)."""
        try:
            resp = self.send_command("TOGGLE 1")
            return resp.upper() in ("ON", "OFF")
        except RuntimeError:
            return False
        except Exception:
            return False
