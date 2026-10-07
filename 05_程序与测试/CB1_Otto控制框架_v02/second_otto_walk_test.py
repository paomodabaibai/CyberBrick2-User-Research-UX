"""Time-limited Otto gait check for the second, newly assembled CB1 robot.

Run from REPL: import second_otto_walk_test as test; test.run()
No boot-file changes, radio, or attack actuator. Importing is inert.
"""
import math
import time
from machine import Pin, PWM
from otto_oscillator import pose_offsets

PORTS = (('S1', 3), ('S3', 1), ('S2', 2), ('S4', 0))


def _pulse(pwm, angle):
    us = int(500 + angle * 2000 / 180)
    pwm.duty_ns(us * 1000)


def run(cycles=3, hip=20, ankle=16, period_ms=1000):
    """Walk in place/forward briefly, recenter, then turn PWM off.

    Start with the robot supported; only proceed to floor testing once
    the physical direction and clearance have been observed.
    """
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError('not a CB1 receiver board (GPIO10 != 0)')
    if not (1 <= cycles <= 5 and 0 < hip <= 25 and 0 < ankle <= 20):
        raise ValueError('test limits: cycles 1..5, hip 0..25, ankle 0..20')
    channels = []
    try:
        for port, gpio in PORTS:
            channels.append(PWM(Pin(gpio), freq=50))
        for pwm in channels:
            _pulse(pwm, 90)
        print('second Otto: centered; starting in 2 s')
        time.sleep_ms(2000)
        start = time.ticks_ms()
        duration = int(cycles * period_ms)
        while True:
            elapsed = time.ticks_diff(time.ticks_ms(), start)
            if elapsed >= duration:
                break
            # Use the first robot's continuous-oscillator phase relation.
            phase = 2 * math.pi * elapsed / period_ms
            ramp = min(1.0, elapsed / 500, (duration - elapsed) / 500)
            pose = pose_offsets(phase, ramp, hip, ankle, 4.0)
            for pwm, offset in zip(channels, pose):
                _pulse(pwm, 90 + offset)
            time.sleep_ms(20)
        print('second Otto: gait done; returning to 90')
    finally:
        for pwm in channels:
            try:
                _pulse(pwm, 90)
            except Exception:
                pass
        time.sleep_ms(700)
        for pwm in channels:
            try:
                pwm.deinit()
            except Exception:
                pass
        print('second Otto: PWM off')
