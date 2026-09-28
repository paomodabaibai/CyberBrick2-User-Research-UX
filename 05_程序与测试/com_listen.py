"""Passive serial logger: opens a COM port WITHOUT asserting DTR/RTS and
WITHOUT sending anything, so a running/resetting board's boot output is
captured undisturbed. Never transmits; never resets.

Usage: python com_listen.py COM7 90 output.txt
"""
import sys
import time

import serial


def main():
    port, seconds, out_path = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 115200
    ser.timeout = 0.2
    ser.open()
    # Explicitly deassert modem lines: on many ESP32 boards a DTR/RTS pulse
    # would reset the chip - the thing this tool must avoid.
    ser.dtr = False
    ser.rts = False
    t0 = time.time()
    with open(out_path, 'w', encoding='utf-8', errors='replace') as f:
        while time.time() - t0 < seconds:
            data = ser.read(512)
            if data:
                stamp = time.time() - t0
                text = data.decode('utf-8', errors='replace')
                line = '[%6.2fs] %s' % (stamp, text)
                f.write(line)
                f.flush()
    ser.close()
    print('listener done: %s -> %s' % (port, out_path))


if __name__ == '__main__':
    main()
