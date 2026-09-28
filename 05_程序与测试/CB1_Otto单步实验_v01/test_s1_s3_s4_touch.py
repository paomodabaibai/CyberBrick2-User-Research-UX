import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
# Sequential identification with long gaps for tactile (fingertip) checks.
CHANNELS = [('S1', 0), ('S3', 2), ('S4', 3)]
try:
    for label, ch in CHANNELS:
        print('=== %s MOVE NOW ===' % label)
        out.joint(ch, 0)
        time.sleep_ms(300)
        for cycle in range(2):
            for a in list(range(0, 16, 2)) + list(range(12, -16, -2)) + list(range(-12, 1, 2)):
                out.joint(ch, a)
                time.sleep_ms(80)
        out.joint(ch, 0)
        print('=== %s STOP, feel next ===' % label)
        time.sleep_ms(4000)
finally:
    out.close()
    print('ALL PWM OFF')
