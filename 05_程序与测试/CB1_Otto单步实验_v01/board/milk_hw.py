import milk_config as C
from milk_core import servo_angle

class Output:
    def __init__(self):
        self.channels = {}

    def pulse(self, pin, us):
        if not 500 <= us <= 2500:
            raise ValueError('PWM pulse outside 500..2500 us')
        from machine import Pin, PWM
        if pin not in self.channels:
            self.channels[pin] = PWM(Pin(pin), freq=50, duty=0)
        p = self.channels[pin]
        if hasattr(p, 'duty_ns'):
            p.duty_ns(int(us*1000))
        else:
            p.duty(int(us*1023/20000))

    def joint(self, index, offset):
        cfg = C.JOINTS[index]
        angle = servo_angle(offset, cfg)
        self.pulse(cfg['pin'], C.PULSE_AT_0_US + angle/180*(C.PULSE_AT_180_US-C.PULSE_AT_0_US))

    def pose(self, offsets):
        # Validate all joints before writing any output.
        for offset,cfg in zip(offsets,C.JOINTS):
            servo_angle(offset,cfg)
        for i,offset in enumerate(offsets):
            self.joint(i,offset)

    def close(self):
        for p in self.channels.values():
            p.duty(0)
            p.deinit()
        self.channels = {}

class Attack:
    def __init__(self, output):
        self.out = output
        self.busy = False
        self.elapsed = 0
        self.last = True  # Require button release before first attack.

    def update(self, pressed, allow, dt):
        edge = pressed and not self.last
        self.last = pressed
        if not C.ATTACK_ENABLED:
            return
        if not allow:
            self.stop()
            return
        if edge and not self.busy:
            self.busy, self.elapsed = True, 0
        if self.busy:
            self.elapsed += dt
            if self.elapsed >= C.ATTACK_MAX_MS or (C.ATTACK_MODE == 'continuous' and not pressed):
                self.stop()
            elif C.ATTACK_MODE == 'continuous':
                self.out.pulse(C.ATTACK_PIN, C.ATTACK_RUN_US)
            else:
                # Smooth out-and-back, bounded to a small calibration sweep.
                t = self.elapsed / C.ATTACK_MAX_MS
                u = 2*t if t < .5 else 2*(1-t)
                u = u*u*(3-2*u)
                self.out.pulse(C.ATTACK_PIN, C.ATTACK_REST_US + u*(C.ATTACK_HIT_US-C.ATTACK_REST_US))

    def stop(self):
        self.busy = False
        if C.ATTACK_ENABLED:
            self.out.pulse(C.ATTACK_PIN, C.ATTACK_STOP_US if C.ATTACK_MODE == 'continuous' else C.ATTACK_REST_US)
