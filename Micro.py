#Mircocontroller intergration page
import time

class MicroController:
	"""
	Simple local stub for development:
	- list_ports() / auto_detect() use pyserial if available, otherwise return a simulated list
	- connect(port, baud) simulates a quick connect
	- disconnect(), toggle_led() are simulated
	Replace with real implementation when integrating hardware.
	"""
	def __init__(self):
		self.is_connected = False
		self.port = None
		self.baud = None

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

	def connect(self, port, baud=115200):
		# simulate a short connection attempt
		time.sleep(0.05)
		self.port = port
		self.baud = baud
		self.is_connected = True
		return True

	def disconnect(self):
		self.is_connected = False
		self.port = None

	def toggle_led(self, idx):
		# simulate sending a command
		time.sleep(0.02)
		return True
