#Mircocontroller intergration page
import time
import threading

class MicroController:
	"""
	Microcontroller serial client for talking to a Pico running a simple
	serial command loop.

	Features:
	- `connect(port, baud)` opens a serial connection using pyserial
	- `send_command(cmd)` writes a command to the device and returns the response
	- `send_command_async(cmd, callback)` runs the send in a background thread
	- `toggle_led(idx)` convenience wrapper that sends `TOGGLE {idx}`

	If pyserial is not installed or the port cannot be opened, `connect` returns False.
	"""
	def __init__(self):
		self.is_connected = False
		self.port = None
		self.baud = None
		self.ser = None
		self._lock = threading.Lock()

	@staticmethod
	def list_ports():
		try:
			import serial.tools.list_ports as lp
			return [p.device for p in lp.comports()]
		except Exception:
			# safe fallback for development
			return ["COM1", "COM3", "/dev/ttyUSB0"]

	@staticmethod
	def auto_detect():
		ports = MicroController.list_ports()
		return ports[0] if ports else None

	def connect(self, port=None, baud=115200, timeout=1.0):
		"""Open a serial connection to the Pico. Returns True on success."""
		try:
			import serial
		except Exception:
			print("pyserial not installed - please install with: pip install pyserial")
			return False

		if port is None:
			port = MicroController.auto_detect()
		if not port:
			print("No serial port specified or detected")
			return False

		try:
			self.ser = serial.Serial(port, baud, timeout=timeout)
			self.port = port
			self.baud = baud
			self.is_connected = True
			return True
		except Exception as e:
			print("Failed to open serial port:", e)
			self.ser = None
			self.is_connected = False
			return False

	def disconnect(self):
		try:
			if self.ser:
				self.ser.close()
		except Exception:
			pass
		self.ser = None
		self.is_connected = False
		self.port = None

	def send_command(self, cmd, timeout=1.0):
		"""Send a line command to the Pico and return the single-line response.

		This is blocking and will raise RuntimeError if not connected.
		"""
		if not self.is_connected or self.ser is None:
			raise RuntimeError("Not connected to microcontroller")

		with self._lock:
			try:
				line = (cmd.strip() + "\n").encode()
				self.ser.write(line)
				self.ser.flush()
				resp = self.ser.readline()
				if not resp:
					return ""
				return resp.decode(errors='ignore').strip()
			except Exception as e:
				print("Serial send failed:", e)
				return ""

	def send_command_async(self, cmd, callback=None):
		"""Send a command in a background thread. If callback provided, it's called with the response."""
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
		"""Send a simple toggle command to the Pico for the given device id."""
		try:
			resp = self.send_command(f"TOGGLE {idx}")
			return resp.upper().startswith('OK')
		except RuntimeError:
			# not connected
			return False
		except Exception:
			return False

# ---------------------- Microcontroller helpers (desktop-only) ----------------------
# MicroPython / Pico-specific code has been removed for now. We'll add it back
# later when you're ready. Below is a small desktop-only simulation helper for
# testing on your development machine and a commented reference to the tutorial
# MicroPython snippet you provided.

def sim_blink(pin=15, interval=0.5, count=10):
	"""Simulate blinking an LED on a development machine by printing ON/OFF.

	Args:
		pin (int): GPIO pin number (kept for compatibility with later code)
		interval (float): seconds LED is on / off each cycle
		count (int|None): number of cycles to run (None = run forever)
	"""
	cycles = 0
	while count is None or cycles < count:
		print(f"[SIM] LED {pin} ON")
		time.sleep(interval)
		print(f"[SIM] LED {pin} OFF")
		time.sleep(interval)
		cycles += 1


# Reference MicroPython snippet (commented) — re-add later if needed:
#
# from machine import Pin
# import utime
#
# led = Pin(15, Pin.OUT)
# while True:
#     led.value(1)
#     utime.sleep(2)
#     led.value(0)
#     utime.sleep(2)
#
# (Source: user's tutorial)


if __name__ == '__main__':
	print('Running simulated blink demo (pin=15)')
	sim_blink(pin=15, interval=0.5, count=20)
