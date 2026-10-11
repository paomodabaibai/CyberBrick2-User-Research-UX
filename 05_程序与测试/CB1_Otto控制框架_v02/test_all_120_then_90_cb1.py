"""Assembly check: move CB1 S1-S4 together to 120°, then hold 90°.

Run on the receiver: import test_all_120_then_90_cb1 as t; t.run()
Importing this module alone does not move the servos.
"""

import time
from machine import Pin
import hold_90_cb1 as center


def run(wait_seconds=1.5):
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError("This must run on a CB1 receiver")
    center.hold()
    try:
        for port, _, _ in center.PORTS:
            center._channels[port].duty_ns(1667000)
        print("S1-S4: 120 degrees")
        time.sleep(wait_seconds)
    finally:
        for port, _, _ in center.PORTS:
            center._channels[port].duty_ns(1500000)
        print("S1-S4: holding 90 degrees")
