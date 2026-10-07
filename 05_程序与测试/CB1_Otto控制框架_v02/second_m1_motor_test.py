"""Five-second M1 motor check for second CB1 robot; import is inert."""
import time
from machine import Pin
from bbl.motors import MotorsController


def run(seconds=5, speed=1024):
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError('not a CB1 receiver board')
    if not (1 <= seconds <= 10 and 0 < abs(speed) <= 2048):
        raise ValueError('seconds 1..10, speed -2048..2048 excluding 0')
    motor = MotorsController()
    print('M1 running', speed, 'for', seconds, 'seconds')
    try:
        motor.set_speed(1, speed)
        end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            motor.motors_period_cb()
            time.sleep_ms(1)
    finally:
        motor.stop(1)
        print('M1 stopped')
