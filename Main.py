from DashBoard import App
import argparse
import sys
import os
import sys

# Add AIFiles to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AIFiles'))

try:
    from Smarthome_AI import check_schedule
    AI_AVAILABLE = True
except Exception as e:
    print(f"AI module import failed: {e}")
    AI_AVAILABLE = False

def try_import_micro():
	try:
		import Micro
		print("Micro imported")
		return True
	except Exception as e:
		print(f"Micro import failed: {e}")
		return False

def main(argv=None):
	parser = argparse.ArgumentParser(description='TinyHouse Smart Home')
	parser.add_argument('--no-micro', action='store_true', help='Skip Micro import')
	args = parser.parse_args(argv)

	if not args.no_micro:
		try_import_micro()
	else:
		print('Micro skipped')

	app = App()

	if AI_AVAILABLE:
		def periodic_ai_check():
			check_schedule()
			app.after(100000, periodic_ai_check)  # Check every 100 seconds
		app.after(100000, periodic_ai_check)
	
	app.mainloop()

if __name__ == "__main__":
	main(sys.argv[1:])
