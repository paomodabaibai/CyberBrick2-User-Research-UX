"""Install as main.py on the SECOND CB1 receiver only.

On power-up, use both walking sticks and the two-speed punch stick.
The controller itself requires all sticks neutral before arming. On a radio
loss or K4 press it stops and requires a fresh neutral interval. Unexpected
errors release PWM/M1 in run() before this entry retries.
"""
import time
from machine import Pin
import second_remote_ready as remote

if Pin(10, Pin.IN).value() != 0:
    raise RuntimeError('second_punch_main requires a CB1 receiver')

while True:
    try:
        remote.run(seconds=None, mode='both')
    except Exception as exc:
        print('second punch: session error; outputs released:', exc)
        time.sleep(2)
