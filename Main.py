#Main python script for starting program, DO NOT PUT CODE INTO THIS PAGE FOR DASHBOARD OR M.CONTROLLER

# Main.py
"""
Main entry point for the TinyHouse Smart Home System.
This file should only start the application and connect modules together.
"""

from DashBoard import App
import argparse
import sys


def try_import_micro():
	"""Attempt to import `Micro` safely and report status."""
	try:
		import Micro  # triggers Micro's auto-start blink on import
		print("Micro imported successfully (auto-start blink may be running).")
		return True
	except Exception as e:
		print("Micro import failed (blink disabled):", e)
		return False


def main(argv=None):
	"""Main entrypoint. Use --no-micro to disable importing the Micro module."""
	parser = argparse.ArgumentParser(description='Start the TinyHouse Smart Home System')
	parser.add_argument('--no-micro', action='store_true', help='Disable Micro module import (no auto blink)')
	args = parser.parse_args(argv)

	# Import Micro (optional) before starting GUI so any auto-start behavior runs.
	if not args.no_micro:
		try_import_micro()
	else:
		print('Micro import skipped (--no-micro)')

	# Start the dashboard GUI
	app = App()
	app.mainloop()


if __name__ == "__main__":
	main(sys.argv[1:])
