import time
import machine
import milk_config as C
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
# Drive a joint by PORT number (S1..S4 -> GPIO 3,2,1,0) to avoid index bugs.
PORT_TO_INDEX = {j['pin']: i for i, j in enumerate(C.JOINTS)}
PORT_GPIO = {'S1': 3, 'S3': 1, 'S4': 0}  # S2 has the 360-degree servo, skip.
PORT_NAME = {3: 'left_hip', 1: 'right_hip', 0: 'right_ankle'}
out = Output()
try:
    for label, gpio in [('S1', 3), ('S3', 1), ('S4', 0)]:
        idx = PORT_TO_INDEX[gpio]
        print('=== %s (%s, GPIO%d) +10 NOW ===' % (label, PORT_NAME[gpio], gpio))
        out.joint(idx, 10)
        time.sleep_ms(2000)
        out.joint(idx, 0)
        time.sleep_ms(800)
        print('=== %s -10 NOW ===' % (label,))
        out.joint(idx, -10)
        time.sleep_ms(2000)
        out.joint(idx, 0)
        time.sleep_ms(1500)
finally:
    out.close()
    print('ALL PWM OFF')
