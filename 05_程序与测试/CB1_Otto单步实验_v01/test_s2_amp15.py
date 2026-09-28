import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
try:
    print('S2 +/-15 degrees START')
    out.joint(1, 0)
    time.sleep_ms(300)
    for cycle in range(2):
        for a in list(range(0, 16, 2)) + list(range(12, -16, -2)) + list(range(-12, 1, 2)):
            out.joint(1, a)
            time.sleep_ms(80)
    time.sleep_ms(300)
finally:
    out.close()
    print('S2 PWM OFF')
