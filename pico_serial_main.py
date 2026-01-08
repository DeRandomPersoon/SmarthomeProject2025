# MicroPython serial command loop for the Pico
# Save this as `main.py` on your Pico to accept simple commands over USB serial.
# Commands (text lines, newline-terminated):
#   READY printed at boot
#   ON <id>     -> turn light <id> on
#   OFF <id>    -> turn light <id> off
#   TOGGLE <id> -> toggle pin state for <id>
#   BLINK <id> <n> -> blink n times
# Replies:
#   OK ...  or ERR ...

from machine import Pin
import utime
import sys

# Map device ids to output pins (customize as needed)
DEV_MAP = {1: 15}  # device 1 -> GP15

pins = {k: Pin(v, Pin.OUT) for k, v in DEV_MAP.items()}
state = {k: 0 for k in DEV_MAP}

print('READY')

while True:
    line = sys.stdin.readline()
    if not line:
        utime.sleep(0.05)
        continue
    line = line.strip()
    if not line:
        continue
    parts = line.split()
    cmd = parts[0].upper()
    try:
        if cmd == 'ON' and len(parts) >= 2:
            i = int(parts[1])
            if i in pins:
                pins[i].value(1)
                state[i] = 1
                print('OK ON')
            else:
                print('ERR BAD_ID')
        elif cmd == 'OFF' and len(parts) >= 2:
            i = int(parts[1])
            if i in pins:
                pins[i].value(0)
                state[i] = 0
                print('OK OFF')
            else:
                print('ERR BAD_ID')
        elif cmd == 'TOGGLE' and len(parts) >= 2:
            i = int(parts[1])
            if i in pins:
                pins[i].value(1 - pins[i].value())
                state[i] = pins[i].value()
                print('OK TOGGLE')
            else:
                print('ERR BAD_ID')
        elif cmd == 'BLINK' and len(parts) >= 3:
            i = int(parts[1])
            n = int(parts[2])
            if i in pins:
                for _ in range(n):
                    pins[i].value(1)
                    utime.sleep(0.2)
                    pins[i].value(0)
                    utime.sleep(0.2)
                print('OK BLINK')
            else:
                print('ERR BAD_ID')
        else:
            print('ERR UNKNOWN')
    except Exception as e:
        print('ERR', e)