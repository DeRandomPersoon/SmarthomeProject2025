"""WiFi HTTP server for Pico W: toggle GP15 over the network.

Upload as main.py. Edit WiFi credentials below, then:
  - Connect to http://pico.local/toggle (or http://<pico-ip>/toggle)
  - Endpoints:
      /toggle     -> flips GP15, returns {"state":"ON"} or {"state":"OFF"}
      /on         -> sets GP15 high, returns {"state":"ON"}
      /off        -> sets GP15 low, returns {"state":"OFF"}
      /state      -> returns {"state":"ON"} or {"state":"OFF"}

Setup:
  1. Set SSID and PASSWORD below.
  2. Upload as main.py.
  3. Connect to the Pico's mDNS hostname (pico.local) or find its IP in your router.
"""

import network
import socket
import json
from machine import Pin
import utime

# ===== WiFi Configuration =====
SSID = "your_wifi_name"       # Change to your WiFi SSID
PASSWORD = "your_wifi_pass"   # Change to your WiFi password

# ===== GPIO Setup =====
LED = Pin(15, Pin.OUT)


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
        if path == "/toggle":
            if LED.value():
                LED.value(0)
                state = "OFF"
            else:
                LED.value(1)
                state = "ON"
            return "200 OK", json.dumps({"state": state})
        elif path == "/on":
            LED.value(1)
            return "200 OK", json.dumps({"state": "ON"})
        elif path == "/off":
            LED.value(0)
            return "200 OK", json.dumps({"state": "OFF"})
        elif path == "/state":
            state = "ON" if LED.value() else "OFF"
            return "200 OK", json.dumps({"state": state})
        else:
            return "404 Not Found", ""
    except Exception as e:
        return "500 Internal Server Error", str(e)


def run_server(wlan, port=80):
    """Run HTTP server."""
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(5)
    print(f"Server listening on {wlan.ifconfig()[0]}:{port}")
    while True:
        try:
            conn, addr = sock.accept()
            request = conn.recv(1024).decode()
            if request:
                request_line = request.split("\r\n")[0]
                status, body = handle_request(request_line)
                response = f"HTTP/1.1 {status}\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{body}"
                conn.sendall(response.encode())
            conn.close()
        except Exception as e:
            print("Error:", e)
            try:
                conn.close()
            except:
                pass


if __name__ == "__main__":
    print("Starting WiFi Pico server...")
    wlan = connect_wifi()
    if wlan:
        run_server(wlan)
    else:
        print("Failed to connect to WiFi; server not running")
