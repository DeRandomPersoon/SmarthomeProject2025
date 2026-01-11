from DashBoard import App
import argparse
import sys


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
	app.mainloop()


if __name__ == "__main__":
	main(sys.argv[1:])
