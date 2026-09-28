import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
try:
    print('S4 +/-5 degrees START')
    out.joint(3, 0)
    time.sleep_ms(300)
    for cycle in range(2):
        for a in list(range(0, 6)) + list(range(4, -6, -1)) + list(range(-4, 1)):
            out.joint(3, a)
            time.sleep_ms(60)
    time.sleep_ms(300)
finally:
    out.close()
    print('S4 PWM OFF')
