"""Second CB1: bounded remote walking + forward-only M1 punch experiment.

Import is inert. monitor() samples radio only; run() explicitly moves hardware.
Uses the second robot's proven 20/16 gait, not the first robot's calibration.
"""
import math
import time
from otto_oscillator import pose_offsets

PORTS = (3, 1, 2, 0)  # S1,S3,S2,S4: oscillator joint order
DEFAULT = dict(left=3, right=0, attack=2, stop=9,
               left_center=1797, right_center=1959, attack_center=1825,
               span=1800, threshold=0.4, neutral=0.15,
               arm_ms=500, slow_speed=1024, fast_speed=1800,
               attack_up_is_high=True)


def motor_service(motor):
    """Older boards need a callback; current easypwm boards run PWM natively."""
    return getattr(motor, 'motors_period_cb', None)


def diff(a, b):
    fn = getattr(time, 'ticks_diff', None)
    return fn(a, b) if fn else a - b


class RemotePolicy:
    """Pure frame policy. Loss/stop/timeout disarm until neutral is observed."""
    def __init__(self, mapping=None):
        self.cfg = dict(DEFAULT)
        if mapping:
            self.cfg.update(mapping)
        c = self.cfg
        channels = [c[k] for k in ('left', 'right', 'attack', 'stop')]
        if (any(not isinstance(v, int) or not 0 <= v < 10 for v in channels)
                or len(set(channels)) != 4
                or c['span'] <= 0 or not 0 < c['neutral'] < c['threshold'] <= 1
                or not 1 <= c['arm_ms'] <= 2000
                or not 0 < c['slow_speed'] < c['fast_speed'] <= 2048
                or not isinstance(c['attack_up_is_high'], bool)):
            raise ValueError('invalid mapping/test limits')
        self.reset()

    def reset(self):
        self.armed = False
        self.neutral_since = None
        self.attack_active = False
        self.attack_ready = False

    def update(self, raw, now):
        c = self.cfg
        try:
            if raw is None or len(raw) != 10:
                raise ValueError('frame')
            vals = [float(raw[c[k]]) for k in ('left', 'right', 'attack')]
            if any(not 0 <= v <= 4095 for v in vals):
                raise ValueError('ADC')
            stop = raw[c['stop']]
            if stop not in (0, 1) or stop == 0:  # active-low K4
                raise ValueError('stop')
        except (TypeError, ValueError, IndexError, KeyError):
            self.reset()
            return 0.0, 0.0, 0
        axes = [max(-1.0, min(1.0, (v - c[k]) / c['span']))
                for v, k in zip(vals, ('left_center', 'right_center', 'attack_center'))]
        neutral = all(abs(v) <= c['neutral'] for v in axes)
        if not self.armed:
            if not neutral:
                self.neutral_since = None
            elif self.neutral_since is None:
                self.neutral_since = now
            elif diff(now, self.neutral_since) >= c['arm_ms']:
                self.armed = True
                self.attack_ready = True
            return 0.0, 0.0, 0
        l, r, a = axes
        l = l if abs(l) >= c['threshold'] else 0.0
        r = r if abs(r) >= c['threshold'] else 0.0
        drive = (l + r) / 2 if l * r > 0 else 0.0
        turn = (r - l) / 2 if drive else max(-1.0, min(1.0, r - l))
        speed = 0
        if abs(a) <= c['neutral']:
            self.attack_ready = True
            self.attack_active = False
        elif abs(a) >= c['threshold'] and self.attack_ready:
            self.attack_active = True
            up = (a > 0) == c['attack_up_is_high']
            speed = c['slow_speed'] if up else c['fast_speed']
        else:
            # On the outward stroke, the stick must cross this partial zone.
            # Keep the initial trigger armed; after a punch began, partial
            # return stops it and requires full neutral before retrigger.
            if self.attack_active:
                self.attack_ready = False
                self.attack_active = False
        return drive, turn, speed


def _clock():
    fn = getattr(time, 'ticks_ms', None)
    return fn() if fn else int(time.monotonic() * 1000)


def _sleep(ms):
    fn = getattr(time, 'sleep_ms', None)
    if fn:
        fn(ms)
    else:
        time.sleep(ms / 1000.0)


def monitor(seconds=15):
    """Radio-only sampling; REPL takeover may interrupt the previous app."""
    if not 1 <= seconds <= 60:
        raise ValueError('seconds 1..60')
    import rc_module
    if rc_module.rc_slave_init() is False:
        raise RuntimeError('radio init failed')
    start = _clock()
    while diff(_clock(), start) < seconds * 1000:
        print(rc_module.rc_slave_data())
        _sleep(200)


def run(seconds=30, mode='both', mapping=None, trace=False):
    """Bounded live test. Ctrl-C/time limit/exception stop M1 and release legs.

    mode: walk / attack / both. All three axes must neutralize to arm.
    Defaults are first-remote values; verify using monitor before running.
    """
    if not 1 <= seconds <= 120 or mode not in ('walk', 'attack', 'both'):
        raise ValueError('seconds 1..120; mode walk/attack/both')
    policy = RemotePolicy(mapping)
    from machine import Pin, PWM
    import rc_module
    from bbl.motors import MotorsController
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError('not a CB1 receiver')
    channels = []
    motor = None
    service = None
    trace_frames = 0
    trace_engaged = 0
    trace_attack_ticks = 0
    trace_attack_min = 4096
    trace_attack_max = -1
    trace_min_angle = 180
    trace_max_angle = 0
    try:
        if rc_module.rc_slave_init() is False:
            raise RuntimeError('radio init failed')
        if mode != 'walk':
            motor = MotorsController()
            motor.stop(1)
            service = motor_service(motor)
        start = _clock()
        last = start
        next_frame = start
        phase = 0.0
        scale = 0.0
        direction = 1
        last_speed = 0
        was_armed = False
        print('second punch:', mode, seconds, 's; neutral 0.5s to arm; K4 stops')
        while diff(_clock(), start) < seconds * 1000:
            now = _clock()
            if diff(now, next_frame) >= 0:
                dt = diff(now, last)
                last = now
                next_frame = now  # use diff below for wrap-safe scheduling
                raw = rc_module.rc_slave_data()
                if trace and raw is not None:
                    trace_frames += 1
                    if len(raw) == 10:
                        trace_attack_min = min(trace_attack_min, raw[policy.cfg['attack']])
                        trace_attack_max = max(trace_attack_max, raw[policy.cfg['attack']])
                drive, turn, speed = policy.update(raw, now)
                if trace and speed:
                    trace_attack_ticks += 1
                if dt < 0 or dt > 100:
                    policy.reset()
                    drive, turn, speed = 0.0, 0.0, 0
                if policy.armed != was_armed:
                    print('ARMED' if policy.armed else 'STOPPED: neutral to rearm')
                    was_armed = policy.armed
                if motor and speed != last_speed:
                    if speed:
                        motor.set_speed(1, speed)
                    else:
                        motor.stop(1)
                    last_speed = speed
                if mode != 'attack':
                    if not policy.armed:
                        for pwm in channels:
                            pwm.deinit()
                        channels = []
                        scale = 0.0
                        phase = 0.0
                    else:
                        if not channels:
                            for gpio in PORTS:
                                channels.append(PWM(Pin(gpio), freq=50))
                        engaged = drive != 0 or turn != 0
                        if trace and engaged:
                            trace_engaged += 1
                        target = 1.0 if engaged else 0.0
                        delta = dt / 500.0
                        scale = min(target, scale + delta) if target > scale else max(target, scale - delta)
                        if engaged:
                            direction = -1 if drive < 0 else 1
                            phase += 2 * math.pi * dt / 1000.0
                        pose = pose_offsets(phase, scale, 20, 16, 4,
                                            turn=turn, turn_split=10,
                                            direction=direction, yaw_trim=0)
                        for pwm, offset in zip(channels, pose):
                            angle = 90 + offset
                            if not 65 <= angle <= 115:
                                raise ValueError('second robot test angle limit')
                            if trace:
                                trace_min_angle = min(trace_min_angle, angle)
                                trace_max_angle = max(trace_max_angle, angle)
                            pwm.duty_ns(int(500 + angle * 2000 / 180) * 1000)
                # time.ticks_add is required at the 30-bit wrap boundary.
                add = getattr(time, 'ticks_add', None)
                next_frame = add(now, 20) if add else now + 20
            if service:
                service()  # older official software PWM needs ~1ms servicing
            _sleep(1)
    finally:
        try:
            if motor:
                motor.stop(1)
        finally:
            for pwm in channels:
                try:
                    pwm.deinit()
                except Exception:
                    pass
        print('second punch: M1 stopped; leg PWM off (power remains on)')
        if trace:
            print('trace: frames', trace_frames, 'engaged', trace_engaged,
                  'angle_min', trace_min_angle, 'angle_max', trace_max_angle,
                  'attack_ticks', trace_attack_ticks,
                  'attack_min', trace_attack_min, 'attack_max', trace_attack_max)
