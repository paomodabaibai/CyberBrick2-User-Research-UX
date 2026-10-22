"""Install as main.py on the SECOND CB1 receiver only.

On power-up, use both walking sticks, the two-speed punch stick, and held K4
for a small random dance. All sticks must be neutral before arming. Radio loss
stops motion and requires a fresh neutral interval. Unexpected errors release
PWM/M1 in run() before this entry retries.
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
