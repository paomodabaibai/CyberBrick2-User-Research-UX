import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
# S1 and S4 driven anti-phase to tell one shared servo apart from two feet.
try:
    print('S1 vs S4 anti-phase START')
    out.joint(0, 0)
    out.joint(3, 0)
    time.sleep_ms(500)
    for cycle in range(3):
        out.joint(0, 15)
        out.joint(3, -15)
        time.sleep_ms(1200)
        out.joint(0, -15)
        out.joint(3, 15)
        time.sleep_ms(1200)
    out.joint(0, 0)
    out.joint(3, 0)
    time.sleep_ms(300)
finally:
    out.close()
    print('S1/S4 PWM OFF')
