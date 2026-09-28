import time
import machine
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
out = Output()
# S2 continuous sweep for ~60s so wiring can be watched/adjusted live.
try:
    print('S2 continuous +/-15 sweep, 60s')
    out.joint(1, 0)
    time.sleep_ms(300)
    t0 = time.ticks_ms()
    up = True
    a = 0
    while time.ticks_diff(time.ticks_ms(), t0) < 60000:
        out.joint(1, a)
        a = a + (2 if up else -2)
        if a >= 15:
            up = False
        elif a <= -15:
            up = True
        time.sleep_ms(80)
    out.joint(1, 0)
    time.sleep_ms(300)
finally:
    out.close()
    print('S2 PWM OFF')
