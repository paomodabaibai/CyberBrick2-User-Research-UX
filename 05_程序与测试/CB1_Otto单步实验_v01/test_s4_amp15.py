import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
try:
    print('S4 +/-15 degrees x3 START')
    out.joint(3, 0)
    time.sleep_ms(300)
    for cycle in range(3):
        for a in list(range(0, 16, 2)) + list(range(12, -16, -2)) + list(range(-12, 1, 2)):
            out.joint(3, a)
            time.sleep_ms(80)
    time.sleep_ms(300)
finally:
    out.close()
    print('S4 PWM OFF')
