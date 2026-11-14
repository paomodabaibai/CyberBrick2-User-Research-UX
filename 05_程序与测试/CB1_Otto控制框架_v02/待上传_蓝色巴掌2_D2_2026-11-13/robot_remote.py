"""Shared CB1 control: walking, held-K4 dance and a selected attack output.

Import is inert. monitor() samples radio only; run() explicitly moves hardware.
Uses the original palm robot's 30/20 amplitudes and three-to-one turn ratio.
"""
import math
import time
from otto_oscillator import pose_offsets

PORTS = (3, 1, 2, 0)  # S1,S3,S2,S4: oscillator joint order
CONTROL_VERSION = 'cb1-shared-palm-gait-30-20-2026-10-20'
HIP_AMP = 30.0
ANKLE_AMP = 20.0
BIAS = 4.0
TURN_SPLIT = 20.0  # original palm turn amplitudes: 30:10
# User requested the larger palm gait for both robots. The punch's expanded
# hip range is pending a physical clearance check; ankles and dance stay +/-25.
JOINT_LIMITS = ((60.0, 120.0), (60.0, 120.0), (65.0, 115.0), (65.0, 115.0))
DEFAULT = dict(left=3, right=0, attack=2, dance=9,
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
    """Pure frame policy. Radio loss disarms until neutral is observed."""
    def __init__(self, mapping=None):
        self.cfg = dict(DEFAULT)
        if mapping:
            self.cfg.update(mapping)
        c = self.cfg
        channels = [c[k] for k in ('left', 'right', 'attack', 'dance')]
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
        self.dance_active = False
        self.walk_direction = 1
        self.stride_turn = 0.0

    def update(self, raw, now):
        c = self.cfg
        try:
            if raw is None or len(raw) != 10:
                raise ValueError('frame')
            vals = [float(raw[c[k]]) for k in ('left', 'right', 'attack')]
            if any(not 0 <= v <= 4095 for v in vals):
                raise ValueError('ADC')
            button = raw[c['dance']]
            if button not in (0, 1):  # active-low K4
                raise ValueError('dance button')
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
        self.dance_active = button == 0
        if self.dance_active:
            self.attack_active = False
            self.attack_ready = False
            self.walk_direction = 1
            self.stride_turn = 0.0
            return 0.0, 0.0, 0
        l, r, a = axes
        l = l if abs(l) >= c['threshold'] else 0.0
        r = r if abs(r) >= c['threshold'] else 0.0
        drive = (l + r) / 2 if l * r > 0 else 0.0
        turn = (r - l) / 2 if drive else max(-1.0, min(1.0, r - l))
        # A single stick has drive==0 for the existing arc API. That does
        # NOT mean forward: retain the sign of the one active walking stick.
        single_reverse = l * r == 0 and l + r < 0
        self.walk_direction = -1 if drive < 0 or single_reverse else 1
        # 'turn' is a signed steering request; the oscillator needs a stride
        # SIDE. Reverse both levers -> keep the same larger-stride leg and
        # change ankle travel phase only. Opposed levers keep the old arc
        # behavior; the four-joint Otto cannot counter-rotate two legs.
        self.stride_turn = turn * self.walk_direction
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


class WalkMotion:
    """Pure gait state. Reverse through stance, never flip loaded ankles.

    phase continues during a stop ramp; the last stride split is retained.
    The first robot's oscillator and calibration are not changed here.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.phase = 0.0
        self.scale = 0.0
        self.direction = 1
        self.turn = 0.0

    def step(self, dt, engaged, turn, direction):
        if not 0 <= dt <= 100 or direction not in (-1, 1):
            raise ValueError('walk tick dt 0..100ms, direction +/-1')
        if self.scale == 0 and engaged:
            self.direction = direction
            self.turn = turn
            self.phase = 0.0
        reversing = engaged and direction != self.direction
        target = 1.0 if engaged and not reversing else 0.0
        delta = dt / 500.0
        self.scale = (min(target, self.scale + delta) if target > self.scale
                      else max(target, self.scale - delta))
        if self.scale == 0:
            self.phase = 0.0
            self.turn = turn if engaged else 0.0
            if engaged:
                self.direction = direction
        elif engaged and not reversing:
            # Avoid an amplitude jump when changing which stick is active.
            slew = dt / 200.0
            self.turn += max(-slew, min(slew, turn - self.turn))
        if self.scale > 0:
            self.phase = (self.phase + 2 * math.pi * dt / 1000.0) % (2 * math.pi)
        return pose_offsets(self.phase, self.scale, HIP_AMP, ANKLE_AMP, BIAS,
                            turn=self.turn, turn_split=TURN_SPLIT,
                            direction=self.direction, yaw_trim=0)


class DanceMotion:
    """Alternate large poses, with a brief hold so servos reach each target."""
    STEP_MS = 450
    MOVE_MS = 300
    LIMITS = (25, 25, 25, 25)  # hips then ankles, in degrees

    def __init__(self, start_ms, start_pose=(0, 0, 0, 0)):
        self.start_ms = start_ms
        self.start_pose = tuple(start_pose)
        self.seed = (start_ms ^ 0x5A17C3D9) & 0xffffffff

    def _target(self, index):
        state = (self.seed + index * 2654435761) & 0xffffffff
        pose = []
        for joint, limit in enumerate(self.LIMITS):
            state = (1664525 * state + 1013904223) & 0xffffffff
            magnitude = limit * (80 + (state >> 16) % 21) / 100.0
            sign = -1 if (index + (joint == 1)) % 2 else 1
            pose.append(sign * magnitude)
        return tuple(pose)

    def pose(self, now):
        elapsed = max(0, diff(now, self.start_ms))
        step = elapsed // self.STEP_MS
        fraction = min(1.0, (elapsed % self.STEP_MS) / self.MOVE_MS)
        before = self.start_pose if step == 0 else self._target(step - 1)
        after = self._target(step)
        return tuple(a + (b - a) * fraction for a, b in zip(before, after))


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


def _palm_config(cfg, policy):
    """Validate continuous-servo routing before opening any board hardware."""
    if cfg is None:
        raise ValueError('palm_cfg is required for palm attack')
    cfg = dict(cfg)
    try:
        valid = (cfg['enabled'] is True and cfg['actuator'] == 'continuous'
                 and cfg['gpio'] == 21 and cfg['freq_hz'] == 50
                 and cfg['channel'] == policy.cfg['attack']
                 and cfg['center'] == policy.cfg['attack_center']
                 and cfg['span'] == policy.cfg['span']
                 and cfg['direction'] in (-1, 1)
                 and 0 <= cfg['exit_deadband'] < cfg['enter_deadband'] < 1
                 and 0 <= cfg['reverse_dwell_ms'] <= 1000
                 and cfg['delta_us'] > 0
                 and 500 <= cfg['neutral_us'] - cfg['delta_us']
                 and cfg['neutral_us'] + cfg['delta_us'] <= 2500)
    except (KeyError, TypeError):
        valid = False
    if not valid:
        raise ValueError('invalid D1 palm configuration')
    return cfg


def run(seconds=30, mode='both', mapping=None, trace=False,
        attack_kind='punch', palm_cfg=None):
    """Remote control session. None keeps running until interrupted or reset.

    mode: walk / attack / both. All three axes must neutralize to arm.
    Ctrl-C, a finite time limit or an exception stops M1 and releases legs.
    """
    if ((seconds is not None and not 1 <= seconds <= 120)
            or mode not in ('walk', 'attack', 'both')
            or attack_kind not in ('punch', 'palm')):
        raise ValueError('seconds None or 1..120; mode walk/attack/both; attack punch/palm')
    policy = RemotePolicy(mapping)
    if attack_kind == 'palm':
        palm_cfg = _palm_config(palm_cfg, policy)
    from machine import Pin, PWM
    import rc_module
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError('not a CB1 receiver')
    channels = []
    motor = None
    palm = None
    palm_control = None
    service = None
    trace_frames = 0
    trace_engaged = 0
    trace_attack_ticks = 0
    trace_dance_ticks = 0
    trace_attack_min = 4096
    trace_attack_max = -1
    trace_min_angle = 180
    trace_max_angle = 0
    try:
        if rc_module.rc_slave_init() is False:
            raise RuntimeError('radio init failed')
        if mode != 'walk' and attack_kind == 'punch':
            from bbl.motors import MotorsController
            motor = MotorsController()
            motor.stop(1)
            service = motor_service(motor)
        elif mode != 'walk':
            from attack_control import AttackController
            from drivers.palm_pwm import PalmPwmDriver
            palm_control = AttackController(palm_cfg)
            palm = PalmPwmDriver(palm_cfg)
        start = _clock()
        last = start
        next_frame = start
        walk_motion = WalkMotion()
        last_speed = 0
        was_armed = False
        dance_motion = None
        last_pose = (0, 0, 0, 0)
        print(CONTROL_VERSION)
        print('CB1', attack_kind, mode, seconds,
              's; neutral 0.5s to arm; hold K4 to dance')
        while seconds is None or diff(_clock(), start) < seconds * 1000:
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
                if trace and speed and attack_kind == 'punch':
                    trace_attack_ticks += 1
                if dt < 0 or dt > 100:
                    policy.reset()
                    drive, turn, speed = 0.0, 0.0, 0
                if policy.dance_active and mode != 'attack':
                    if dance_motion is None:
                        dance_motion = DanceMotion(now, last_pose)
                        walk_motion.reset()
                    if trace:
                        trace_dance_ticks += 1
                else:
                    dance_motion = None
                if policy.armed != was_armed:
                    print('ARMED' if policy.armed else 'STOPPED: neutral to rearm')
                    was_armed = policy.armed
                if motor and speed != last_speed:
                    if speed:
                        motor.set_speed(1, speed)
                    else:
                        motor.stop(1)
                    last_speed = speed
                if palm is not None:
                    if not policy.armed or policy.dance_active:
                        palm_control.update(None, now)
                        if policy.armed:
                            palm.stop()  # dance: stop without creating PWM
                        else:
                            palm.release()
                    else:
                        pulse = palm_control.update(raw, now)
                        if pulse is None:
                            palm.release()
                        else:
                            palm.write_us(pulse)
                            if trace and pulse != palm_cfg['neutral_us']:
                                trace_attack_ticks += 1
                if mode != 'attack':
                    if not policy.armed:
                        for pwm in channels:
                            pwm.deinit()
                        channels = []
                        walk_motion.reset()
                        last_pose = (0, 0, 0, 0)
                    else:
                        if not channels:
                            for gpio in PORTS:
                                channels.append(PWM(Pin(gpio), freq=50))
                        if dance_motion:
                            pose = dance_motion.pose(now)
                        else:
                            engaged = drive != 0 or turn != 0
                            if trace and engaged:
                                trace_engaged += 1
                            pose = walk_motion.step(dt, engaged,
                                                    policy.stride_turn,
                                                    policy.walk_direction)
                        for pwm, offset, limits in zip(channels, pose, JOINT_LIMITS):
                            angle = 90 + offset
                            if not limits[0] <= angle <= limits[1]:
                                raise ValueError('shared robot joint angle limit')
                            if trace:
                                trace_min_angle = min(trace_min_angle, angle)
                                trace_max_angle = max(trace_max_angle, angle)
                            pwm.duty_ns(int(500 + angle * 2000 / 180) * 1000)
                        last_pose = pose
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
            try:
                if palm is not None:
                    palm.release()
            finally:
                for pwm in channels:
                    try:
                        pwm.deinit()
                    except Exception:
                        pass
        print('CB1', attack_kind, ': attack stopped; leg PWM off (power remains on)')
        if trace:
            print('trace: frames', trace_frames, 'engaged', trace_engaged,
                  'angle_min', trace_min_angle, 'angle_max', trace_max_angle,
                  'attack_ticks', trace_attack_ticks,
                  'dance_ticks', trace_dance_ticks,
                  'attack_min', trace_attack_min, 'attack_max', trace_attack_max)


def run_forever(profile):
    """Identical power-on/retry lifecycle for both receiver profiles."""
    from machine import Pin
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError('CB1 receiver required')
    while True:
        try:
            profile.run(seconds=None, mode='both')
        except Exception as exc:
            print(CONTROL_VERSION, 'session error; outputs released:', exc)
            time.sleep(2)
