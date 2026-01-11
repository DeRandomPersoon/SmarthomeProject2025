# SmarthomeProject2025
Desktop dashboard for the TinyHouse smart home model plus the Pico W firmware it chats with.

## How to run
- Start the desktop app with `python Main.py`. No need to run the other pages directly; the main window pulls them in for you.
- Flash the Pico W by opening `pico_serial_main.py` (or `pico_serial_main_clean.py` if you like the tidy version) in Thonny and using **Save as main.py** on the device.

## What each file does
- [Main.py](Main.py): Entry point that launches the Tkinter dashboard and wires up pages.
- [DashBoard.py](DashBoard.py): Hosts the main layout and navigation between pages (gauge, AI, control, settings).
- [BasePage.py](BasePage.py): Shared base frame providing the bottom nav bar and content area used by all pages.
- [ControlBoard.py](ControlBoard.py): Manual controls, schedules, and database logging for lights, curtains, and heating that talk to the Pico over WiFi. Also handles PostgreSQL data uploads.
- [SettingsPage.py](SettingsPage.py): Connection setup and testing for serial ports and Pico WiFi IP; database controls for testing and viewing data; saves selections to settings.json.
- [data.txt](data.txt): Buffer file that stores sensor/button events locally before uploading to the PostgreSQL database every 5 seconds.
- [AIBoard.py](AIBoard.py): Simple AI tools panel to load CSV data, fetch cloud cover, and run quick predictions.
- [WiFiController.py](WiFiController.py): Little HTTP helper the app uses to talk to the Pico W endpoints.
- [pico_serial_main.py](pico_serial_main.py): MicroPython HTTP server for the Pico W (LED/buzzer control); upload to the Pico via Thonny as main.py.
- [pico_serial_main_clean.py](pico_serial_main_clean.py): Clean reference version of the Pico firmware with the same endpoints.

## Notes
- Settings (serial port, baud, Pico IP, schedules) are stored in settings.json in this folder.
- Ensure the Pico is on the same network as the PC when using WiFi control.
- Connection flow: the Settings page saves the Pico IP, ControlBoard reads it on start, and `WiFiController` fires simple HTTP GET calls (e.g., `/state`, `/toggle`, `/buzzer/pulse`) to the Pico W server running from `pico_serial_main.py`.
- The Pico firmware serves JSON responses over port 80; no persistent socket is needed because each action is a short HTTP request.

## Database Integration
- The app logs all button presses and sensor events to a PostgreSQL database hosted at 4.233.209.202.
- Events are first buffered to `data.txt` in CSV format (sensor_name, value), then uploaded every 5 seconds by a background thread.
- The `data.txt` file keeps the last 50 uploaded entries as a visible history.
- Database controls available in Settings page: Test Connection, Push Data Now, and View Database.
- View Database button shows both pending data (waiting in data.txt) and recent database entries.
- Requires `psycopg2-binary` library: install with `pip install --only-binary=:all: psycopg2-binary`.

## Credits
This project was made by: Thijs, Timo, Samir, and Emre.

## Sources
**Languages & Frameworks:**
- [Python 3](https://www.python.org/) - Desktop application
- [MicroPython](https://micropython.org/) - Pico W firmware
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework for the dashboard
- [psycopg2](https://www.psycopg.org/) - PostgreSQL database adapter for Python


**Hardware:**
- [Raspberry Pi Pico W](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) - WiFi-enabled microcontroller

**APIs & Protocols:**
- HTTP/REST - Communication between desktop app and Pico W
- JSON - Data serialization
- CSV - Data storage for panel information and database buffering
- PostgreSQL - Database for logging sensor events and button presses

**Tools:**
- [Thonny](https://thonny.org/) - MicroPython IDE for Pico W development
- [Youtube] (https://youtube.com) - Coding tutorials and microcontroller intergration
- [GithubCopilot] (https://github.com) - Helping in catching and removing errors before it gets worse
- [Chatgpt-5] (https://chatgpt.com) - Helping with layout of buttons and textfields
