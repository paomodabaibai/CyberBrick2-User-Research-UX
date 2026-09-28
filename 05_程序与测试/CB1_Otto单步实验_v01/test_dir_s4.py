import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
try:
    print('S4 right_ankle +10 NOW')
    out.joint(3, 10)
    time.sleep_ms(2000)
    out.joint(3, 0)
    time.sleep_ms(800)
    print('S4 right_ankle -10 NOW')
    out.joint(3, -10)
    time.sleep_ms(2000)
    out.joint(3, 0)
    time.sleep_ms(500)
finally:
    out.close()
    print('S4 PWM OFF')
