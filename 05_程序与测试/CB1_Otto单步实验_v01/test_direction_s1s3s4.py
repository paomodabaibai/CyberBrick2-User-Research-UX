import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
# Direction check: +offset first, then -offset, so user can note signs.
CHANNELS = [('S1 left_hip', 0), ('S3 right_hip', 2), ('S4 right_ankle', 3)]
try:
    for label, ch in CHANNELS:
        print('=== %s : +10 NOW ===' % label)
        out.joint(ch, 10)
        time.sleep_ms(2000)
        out.joint(ch, 0)
        time.sleep_ms(800)
        print('=== %s : -10 NOW ===' % label)
        out.joint(ch, -10)
        time.sleep_ms(2000)
        out.joint(ch, 0)
        time.sleep_ms(1500)
finally:
    out.close()
    print('ALL PWM OFF')
