import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
try:
    print('S3 right_hip +10 NOW')
    out.joint(2, 10)
    time.sleep_ms(2000)
    out.joint(2, 0)
    time.sleep_ms(800)
    print('S3 right_hip -10 NOW')
    out.joint(2, -10)
    time.sleep_ms(2000)
    out.joint(2, 0)
    time.sleep_ms(500)
finally:
    out.close()
    print('S3 PWM OFF')
