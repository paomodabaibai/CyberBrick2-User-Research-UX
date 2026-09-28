import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
# Final wiring verification: S1=left_hip S2=left_ankle S3=right_hip S4=right_ankle.
CHANNELS = [('S1 left_hip', 0), ('S2 left_ankle', 1), ('S3 right_hip', 2), ('S4 right_ankle', 3)]
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
        print('=== %s STOP ===' % label)
        time.sleep_ms(3000)
finally:
    out.close()
    print('ALL PWM OFF')
