"""WiFi HTTP server for Pico W: control LED, buzzer, and handle button presses.

Upload as main.py to your Pico W.
"""

import network
import socket
import json
from machine import Pin
import utime

# ===== WiFi Configuration =====
SSID = "H368N94FF9A"
PASSWORD = "45EEFEFE9547"

# ===== GPIO Setup =====
LED = Pin(15, Pin.OUT)
BUZZER = Pin(6, Pin.OUT)
BUTTON_GREEN = Pin(14, Pin.IN, Pin.PULL_DOWN)

# Button state tracking
button_pressed = False
last_button_time = 0


def connect_wifi():
    """Connect Pico W to WiFi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    timeout = 20
    while not wlan.isconnected() and timeout > 0:
        utime.sleep(0.5)
        timeout -= 1
    if wlan.isconnected():
        print("WiFi connected:", wlan.ifconfig()[0])
        return wlan
    else:
        print("WiFi failed to connect")
        return None


def handle_request(request_line):
    """Parse HTTP request and return response."""
    global button_pressed
    try:
        parts = request_line.split()
        if len(parts) < 2:
            return "400 Bad Request", ""
        method = parts[0]
        path = parts[1]
        
        if method != "GET":
            return "405 Method Not Allowed", ""
        
        # LED endpoints
        if path == "/toggle":
            if LED.value():
                LED.value(0)
                state = "OFF"
            else:
                LED.value(1)
                state = "ON"
            print(f"LED toggled to {state}")
            return "200 OK", json.dumps({"state": state})
        elif path == "/on":
            LED.value(1)
            print("LED turned ON")
            return "200 OK", json.dumps({"state": "ON"})
        elif path == "/off":
            LED.value(0)
            print("LED turned OFF")
            return "200 OK", json.dumps({"state": "OFF"})
        elif path == "/state":
            state = "ON" if LED.value() else "OFF"
            return "200 OK", json.dumps({"state": state})
        
        # Buzzer endpoints
        elif path == "/buzzer/on":
            BUZZER.value(1)
            print("Buzzer turned ON")
            return "200 OK", json.dumps({"buzzer": "ON"})
        elif path == "/buzzer/off":
            BUZZER.value(0)
            print("Buzzer turned OFF")
            return "200 OK", json.dumps({"buzzer": "OFF"})
        elif path == "/buzzer/pulse":
            print("Buzzer pulse starting...")
            BUZZER.value(1)
            utime.sleep(2)
            BUZZER.value(0)
            print("Buzzer pulse completed")
            return "200 OK", json.dumps({"buzzer": "PULSED"})
        
        # Button check endpoint
        elif path == "/button/check":
            pressed = button_pressed
            if pressed:
                button_pressed = False
                print("Button press detected and cleared")
            return "200 OK", json.dumps({"pressed": pressed})
        
        else:
            return "404 Not Found", ""
    
    except Exception as e:
        print(f"Error handling request: {e}")
        return "500 Internal Server Error", str(e)


def button_handler(pin):
    """Handle button interrupts."""
    global button_pressed, last_button_time
    current_time = utime.ticks_ms()
    
    # Debounce
    if utime.ticks_diff(current_time, last_button_time) < 200:
        return
    
    if pin == BUTTON_GREEN and BUTTON_GREEN.value():
        button_pressed = True
        last_button_time = current_time
        print("=" * 50)
        print("GREEN BUTTON PRESSED")
        print("Button flag set - waiting for PC to poll")
        print("=" * 50)


def setup_buttons():
    """Set up button interrupt handlers."""
    BUTTON_GREEN.irq(trigger=Pin.IRQ_RISING, handler=button_handler)
    print("Button interrupt configured")


def run_server(wlan, port=80):
    """Run HTTP server."""
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(5)
    print(f"Server listening on {wlan.ifconfig()[0]}:{port}")
    
    # Setup button interrupts
    setup_buttons()
    
    while True:
        try:
            conn, addr = sock.accept()
            request = conn.recv(1024).decode()
            if request:
                request_line = request.split("\r\n")[0]
                print(f"Request: {request_line}")
                status, body = handle_request(request_line)
                response = f"HTTP/1.1 {status}\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{body}"
                conn.sendall(response.encode())
            conn.close()
        except Exception as e:
            print(f"Server error: {e}")
            try:
                conn.close()
            except:
                pass


if __name__ == "__main__":
    print("=" * 50)
    print("Starting WiFi Pico server...")
    print("=" * 50)
    wlan = connect_wifi()
    if wlan:
        run_server(wlan)
    else:
        print("Failed to connect to WiFi; server not running")
