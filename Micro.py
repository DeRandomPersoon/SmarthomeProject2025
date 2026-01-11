import time
import threading

class MicroController:
	"""Serial client for Pico control via pyserial."""
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
			return ["COM1", "COM3", "/dev/ttyUSB0"]

	@staticmethod
	def auto_detect():
		ports = MicroController.list_ports()
		return ports[0] if ports else None

	def connect(self, port=None, baud=115200, timeout=1.0):
		try:
			import serial
		except Exception:
			print("pyserial missing")
			return False

		if port is None:
			port = MicroController.auto_detect()
		if not port:
			print("No port found")
			return False

		try:
			self.ser = serial.Serial(port, baud, timeout=timeout)
			self.port = port
			self.baud = baud
			self.is_connected = True
			return True
		except Exception as e:
			print(f"Serial open failed: {e}")
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
				print(f"Serial send failed: {e}")
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
		try:
			resp = self.send_command(f"TOGGLE {idx}")
			return resp.upper().startswith('OK')
		except RuntimeError:
			return False
		except Exception:
			return False

def sim_blink(pin=15, interval=0.5, count=10):
	cycles = 0
	while count is None or cycles < count:
		print(f"[SIM] LED {pin} ON")
		time.sleep(interval)
		print(f"[SIM] LED {pin} OFF")
		time.sleep(interval)
		cycles += 1

if __name__ == '__main__':
	print('Sim blink demo (pin=15)')
	sim_blink(pin=15, interval=0.5, count=20)
