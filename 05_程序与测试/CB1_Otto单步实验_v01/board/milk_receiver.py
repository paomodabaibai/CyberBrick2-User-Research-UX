"""Manual entry point; do not name this main.py until bench testing is complete."""
import milk_config as C
from milk_core import Gait, Trigger, RemoteGate
from milk_hw import Output, Attack

def valid_frame(data):
    return (isinstance(data,(list,tuple)) and len(data)==10 and
            any(data) and all(isinstance(x,int) and 0<=x<=4095 for x in data[:6]) and
            all(x in (0,1) for x in data[6:]))

def axis(raw, center, span, direction):
    return max(-1,min(1,(raw-center)/span*direction))

def run():
    import time, rc_module
    if not C.CALIBRATED or not C.REMOTE_MAPPING_VERIFIED:
        raise RuntimeError('Run calibration and remote monitor first; no PWM started')
    if C.ATTACK_MODE not in ('position','continuous'):
        raise ValueError('Unknown attack mode')
    pins=[j['pin'] for j in C.JOINTS]
    if len(set(pins)) != 4 or (C.ATTACK_ENABLED and C.ATTACK_PIN in pins):
        raise ValueError('Duplicate PWM pin')
    if rc_module.rc_slave_init() is False:
        raise RuntimeError('RC init failed')
    out=Output()
    attack=Attack(out)
    gait=Gait(C.HIP,C.LEAN,C.LIFT,C.PHASE_MS,C.LEFT_SIGN)
    trigger=Trigger()
    gate=RemoteGate()
    last=time.ticks_ms()
    last_valid=last
    activated=False
    print('Supported robot ready? Neutral levers, release attack, hold enable 1 second.')
    try:
        while True:
            time.sleep_ms(C.LOOP_MS)
            now=time.ticks_ms()
            dt=time.ticks_diff(now,last)
            last=now
            data=rc_module.rc_slave_data()
            valid=valid_frame(data)
            if not valid:
                if activated:
                    attack.stop()
                gate.neutral_ms=0
                if activated and time.ticks_diff(now,last_valid)>C.LINK_TIMEOUT_MS:
                    gait.stop()
                    gate.armed=False
                    print('LINK LOST: holding legs. Support robot, Ctrl-C, restart to recover.')
                    activated=False
                continue
            last_valid=now
            left=axis(data[C.LEFT_CHANNEL],C.LEFT_CENTER,C.LEFT_SPAN,C.LEFT_DIRECTION)
            right=axis(data[C.RIGHT_CHANNEL],C.RIGHT_CENTER,C.RIGHT_SPAN,C.RIGHT_DIRECTION)
            # Optional channels: a None button index means "not wired"; using
            # the same index for stop and enable would self-disarm on press.
            pressed=C.ATTACK_BUTTON is not None and data[C.ATTACK_BUTTON]==C.BUTTON_ACTIVE
            stop=C.STOP_BUTTON is not None and data[C.STOP_BUTTON]==C.BUTTON_ACTIVE
            enable=C.ENABLE_BUTTON is not None and data[C.ENABLE_BUTTON]==C.BUTTON_ACTIVE
            if activated and (stop or dt>150):
                gait.stop()
                attack.stop()
                activated=False
                gate.armed=False
                print('STOP latched: support robot, Ctrl-C, restart to recover.')
            if gait.fault:
                continue
            was_armed=gate.armed
            # Neutral is levers-only on purpose: with one shared button the
            # enable hold itself must not break the neutral requirement.
            gate.update(True,abs(left)<.2 and abs(right)<.2,enable,stop,min(dt,40))
            if not gate.armed:
                trigger=Trigger()
                continue
            if not was_armed:
                out.pose(gait.pose)
                activated=True
                print('ARMED (initial stance commanded)')
            event=trigger.update(left,right,gait.busy or attack.busy or pressed)
            if event and not gait.start(event):
                print('Same-side step rejected: alternate feet in v01')
            out.pose(gait.tick(min(dt,40)))
            attack.update(pressed,not gait.busy,min(dt,40))
    finally:
        # Ctrl-C releases holding torque; support robot before interrupting.
        try:
            if activated or C.ATTACK_ENABLED:
                attack.stop()
        finally:
            out.close()
