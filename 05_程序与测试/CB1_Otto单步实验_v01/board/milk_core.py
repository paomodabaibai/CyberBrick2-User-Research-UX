"""Hardware independent experimental Otto single-step controller.

Joint order: left hip, right hip, left ankle, right ankle.
Angles are offsets from calibrated stance, NOT absolute shaft angles.
This is a staged experimental gait, not an Otto library port.
"""

def servo_angle(offset, config):
    value = config['center'] + config['trim'] + config['direction'] * offset
    if not config['min'] <= value <= config['max']:
        raise ValueError('Joint outside calibrated limits')
    return value


class Trigger:
    def __init__(self):
        self.ready = False

    def update(self, left, right, busy=False):
        # Both levers must return to neutral before another event.
        if abs(left) < 0.20 and abs(right) < 0.20:
            self.ready = True
            return None
        if left < 0.55 and right < 0.55:
            return None
        ready, self.ready = self.ready, False
        if not ready or busy or (left >= 0.55 and right >= 0.55):
            return None
        return 'left' if left >= 0.55 else 'right'


class Gait:
    def __init__(self, hip=8, lean=7, lift=3, phase_ms=450, left_sign=1):
        if phase_ms < 200 or not (0 < hip <= 20 and 0 < lean <= 15 and 0 <= lift <= 10):
            raise ValueError('Invalid experimental gait parameters')
        if left_sign not in (-1, 1):
            raise ValueError('left_sign must be +1 or -1')
        self.hip, self.lean, self.lift = hip, lean, lift
        self.phase_ms, self.left_sign = phase_ms, left_sign
        self.pose = [0.0]*4
        self.busy = False
        self.fault = False
        self.last_side = None
        self.phase = 'idle'
        self.queue = []

    def start(self, side):
        if side not in ('left', 'right'):
            raise ValueError('Expected left or right')
        if self.busy or self.fault or side == self.last_side:
            return False
        sign = self.left_sign * (1 if side == 'left' else -1)
        # Same electrical phase in the Otto reference. Direction calibration
        # must map these coordinates to the actual mirrored installation.
        ankle = sign*self.lean
        feet = [ankle, ankle]
        feet[0 if side == 'left' else 1] += sign*self.lift
        target = sign*self.hip
        self.queue = [
            ('weight_shift', [self.pose[0], self.pose[1], ankle, ankle]),
            ('unload', [self.pose[0], self.pose[1]] + feet),
            ('swing', [target, target] + feet),
            ('land', [target, target, 0, 0]),
        ]
        self.last_side = side
        self.busy = True
        self._next()
        return True

    def _next(self):
        if not self.queue:
            self.busy, self.phase = False, 'idle'
            return
        self.phase, self.target = self.queue.pop(0)
        self.origin = self.pose[:]
        self.elapsed = 0

    def tick(self, dt_ms):
        if self.busy:
            self.elapsed += max(0, dt_ms)
            t = min(1.0, self.elapsed / self.phase_ms)
            t = t*t*(3-2*t)
            self.pose = [a+(b-a)*t for a,b in zip(self.origin, self.target)]
            if self.elapsed >= self.phase_ms:
                self._next()
        return self.pose[:]

    def stop(self):
        # Hold latest command. No automatic recenter while one foot bears load.
        self.queue = []
        self.busy, self.fault, self.phase = False, True, 'stopped'


class RemoteGate:
    """No PWM logic here. Explicit neutral + enable hold required after fault."""
    def __init__(self):
        self.armed = False
        self.neutral_ms = 0

    def update(self, valid, neutral, enable, stop, dt):
        if not valid or stop:
            self.armed = False
            self.neutral_ms = 0
        elif not self.armed:
            self.neutral_ms = self.neutral_ms + dt if neutral and enable else 0
            if self.neutral_ms >= 1000:
                self.armed = True
        return self.armed
