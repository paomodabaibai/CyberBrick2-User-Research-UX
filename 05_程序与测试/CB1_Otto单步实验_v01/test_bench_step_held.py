import time
import machine
import milk_config as C
from milk_hw import Output
from milk_core import Gait
assert machine.Pin(10, machine.Pin.IN).value() == 0
# Held-robot single step: run the 4-phase gait once, small amplitudes.
# S2 (GPIO2, 360-degree servo) is NEVER driven here: joints are written
# one by one for indices 0/1/3 only, so no PWM is created on GPIO2 at all.
# A freewheeling unpowered servo is expected and fine while held.
DRIVE = [0, 1, 3]  # left_hip, right_hip, right_ankle
out = Output()
gait = Gait(C.HIP, C.LEAN, C.LIFT, C.PHASE_MS, C.LEFT_SIGN)

def drive(pose):
    for i in DRIVE:
        out.joint(i, pose[i])

try:
    print('center pose', [round(x,1) for x in gait.pose])
    drive(gait.pose)
    time.sleep_ms(800)
    ok = gait.start('left')
    print('start left:', ok)
    last = time.ticks_ms()
    shown = None
    while gait.busy:
        time.sleep_ms(20)
        now = time.ticks_ms()
        pose = gait.tick(min(40, time.ticks_diff(now, last)))
        drive(pose)
        last = now
        if gait.phase != shown:
            shown = gait.phase
            print(gait.phase, [round(x,1) for x in pose])
    print('final pose', [round(x,1) for x in gait.pose])
    time.sleep_ms(1500)
    print('return to center')
    for t in range(20):
        u = (t+1) / 20.0
        u = u*u*(3-2*u)
        drive([p*(1-u) for p in gait.pose])
        time.sleep_ms(50)
    print('done')
finally:
    out.close()
    print('PWM OFF')
