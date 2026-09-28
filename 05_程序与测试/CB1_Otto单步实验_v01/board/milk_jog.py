import time
import machine
import rc_module
from milk_hw import Output
assert machine.Pin(10, machine.Pin.IN).value() == 0
# Jog mode: levers directly wiggle two servos for bench observation.
# Left lever (ch0) -> S1 left_hip, right lever (ch3) -> S4 right_ankle.
# K4 held -> both centered. Ctrl-C or timeout ends and releases PWM.
JOY_DEAD = 0.06
JOG_LIMIT = 15        # degrees, inside JOINTS 65..115 limits
LEFT_REST = 1959
RIGHT_REST = 1797
SPAN = 1800
DURATION_S = 120

def norm(raw, rest):
    v = (raw - rest) / SPAN
    if abs(v) < JOY_DEAD:
        return 0.0
    return max(-1.0, min(1.0, v))

if rc_module.rc_slave_init() is False:
    raise RuntimeError('RC init failed')
out = Output()
t0 = time.ticks_ms()
last_print = 0
try:
    print('JOG %ds: left lever->S1, right lever->S4, hold K4=center' % DURATION_S)
    while time.ticks_diff(time.ticks_ms(), t0) < DURATION_S * 1000:
        time.sleep_ms(20)
        data = rc_module.rc_slave_data()
        if not isinstance(data, (list, tuple)) or len(data) != 10:
            out.joint(0, 0)
            out.joint(3, 0)
            print('LINK LOST: centered')
            time.sleep_ms(300)
            continue
        left = norm(data[0], LEFT_REST)
        right = norm(data[3], RIGHT_REST)
        if data[9] == 0:
            out.joint(0, 0)
            out.joint(3, 0)
        else:
            out.joint(0, int(left * JOG_LIMIT))
            out.joint(3, int(right * JOG_LIMIT))
        now = time.ticks_ms()
        if time.ticks_diff(now, last_print) > 1000:
            last_print = now
            print('L %.2f R %.2f' % (left, right))
finally:
    out.close()
    print('JOG END, PWM OFF')
