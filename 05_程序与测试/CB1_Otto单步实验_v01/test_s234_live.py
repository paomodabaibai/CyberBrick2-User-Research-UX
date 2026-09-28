import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
# S1(GPIO3)=right_ankle confirmed 2026-09-22; testing S2(GPIO2) S3(GPIO1) S4(GPIO0).
CHANNELS = [('S2', 1), ('S3', 2), ('S4', 3)]
try:
    for label, ch in CHANNELS:
        print('=== %s START ===' % label)
        out.joint(ch, 0)
        time.sleep_ms(1000)
        for cycle in range(2):
            for a in list(range(0, 6)) + list(range(4, -6, -1)) + list(range(-4, 1)):
                out.joint(ch, a)
                time.sleep_ms(60)
        time.sleep_ms(300)
        print('=== %s DONE ===' % label)
        time.sleep_ms(2000)
finally:
    out.close()
    print('ALL PWM OFF')
