"""WiFi HTTP server for Pico W: control LED (Pin 15) and buzzer (Pin 11).

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
BUZZER = Pin(11, Pin.OUT)
PIR = Pin(2, Pin.IN, Pin.PULL_DOWN)

# Motion detection state
motion_triggered_light = False
last_motion_time = 0
motion_timeout = 180


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
            global motion_triggered_light
            if LED.value():
                LED.value(0)
                state = "OFF"
            else:
                LED.value(1)
                state = "ON"
            motion_triggered_light = False
            print(f"LED toggled to {state} (manual)")
            return "200 OK", json.dumps({"state": state})
        elif path == "/on":
            motion_triggered_light = False
            LED.value(1)
            print("LED turned ON (manual)")
            return "200 OK", json.dumps({"state": "ON"})
        elif path == "/off":
            motion_triggered_light = False
            LED.value(0)
            print("LED turned OFF (manual)")
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
        
        else:
            return "404 Not Found", ""
    
    except Exception as e:
        print(f"Error handling request: {e}")
        return "500 Internal Server Error", str(e)


def run_server(wlan, port=80):
    """Run HTTP server."""
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(5)
    sock.settimeout(1.0)
    print(f"Server listening on {wlan.ifconfig()[0]}:{port}")
    
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
        except OSError:
            pass
        except Exception as e:
            print(f"Server error: {e}")
            try:
                conn.close()
            except:
                pass
        
        check_motion_timeout()


def pir_handler(pin):
    """Handle PIR motion detection."""
    global motion_triggered_light, last_motion_time
    if PIR.value():
        last_motion_time = utime.time()
        if not LED.value():
            LED.value(1)
            motion_triggered_light = True
            print("Motion detected - LED turned ON")
        elif motion_triggered_light:
            print("Motion detected - timer reset")


def check_motion_timeout():
    """Check if motion-triggered LED should auto-off."""
    global motion_triggered_light, last_motion_time
    if motion_triggered_light and LED.value():
        elapsed = utime.time() - last_motion_time
        if elapsed >= motion_timeout:
            LED.value(0)
            motion_triggered_light = False
            print("LED auto-off (no motion)")

def setup_pir():
    """Set up PIR sensor interrupt."""
    PIR.irq(trigger=Pin.IRQ_RISING, handler=pir_handler)
    print("PIR sensor configured on Pin 2")


if __name__ == "__main__":
    print("=" * 50)
    print("Starting WiFi Pico server...")
    print("=" * 50)
    wlan = connect_wifi()
    if wlan:
        setup_pir()
        run_server(wlan)
    else:
        print("Failed to connect to WiFi; server not running")
