import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
try:
    print('sanity: S1 left_hip +/-10')
    out.joint(0, 10)
    time.sleep_ms(1200)
    out.joint(0, -10)
    time.sleep_ms(1200)
    out.joint(0, 0)
    time.sleep_ms(2000)
    print('test: S3 right_hip +/-15')
    out.joint(2, 15)
    time.sleep_ms(1500)
    out.joint(2, -15)
    time.sleep_ms(1500)
    out.joint(2, 0)
    time.sleep_ms(500)
finally:
    out.close()
    print('ALL PWM OFF')
