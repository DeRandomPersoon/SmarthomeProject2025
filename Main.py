#Main python script for starting program, DO NOT PUT CODE INTO THIS PAGE FOR DASHBOARD OR M.CONTROLLER

# Main.py
"""
Main entry point for the TinyHouse Smart Home System.
This file should only start the application and connect modules together.
"""

from DashBoard import App
# If you want Micro.py to run in background:
# from Micro import MicroController

def main():
    # Optional: Start microcontroller logic
    # micro = MicroController()
    # micro.start()

    # Start the dashboard GUI
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
