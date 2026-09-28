import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
try:
    print('S3 +/-5 degrees START')
    out.joint(2, 0)
    time.sleep_ms(300)
    for cycle in range(2):
        for a in list(range(0, 6)) + list(range(4, -6, -1)) + list(range(-4, 1)):
            out.joint(2, a)
            time.sleep_ms(60)
    time.sleep_ms(300)
finally:
    out.close()
    print('S3 PWM OFF')
