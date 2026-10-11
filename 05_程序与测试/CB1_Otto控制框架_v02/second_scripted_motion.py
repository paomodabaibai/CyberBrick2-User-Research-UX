"""Explicit serial-only 2s forward + 2s candidate left arc. Import is inert."""
import math
import time
from otto_oscillator import pose_offsets


def run():
    from machine import Pin, PWM
    from bbl.motors import MotorsController
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError('not receiver')
    channels = []
    motor = None
    last_pose = [0.0] * 4

    def write(pose):
        for pwm, offset in zip(channels, pose):
            angle = 90 + offset
            if not 65 <= angle <= 115:
                raise ValueError('angle limit')
            pwm.duty_ns(int(500 + angle * 2000 / 180) * 1000)

    try:
        motor = MotorsController()
        motor.stop(1)
        for gpio in (3, 1, 2, 0):
            channels.append(PWM(Pin(gpio), freq=50))
        write(last_pose)
        print('READY: centered, starts in 2 seconds; M1 stopped')
        time.sleep_ms(2000)
        start = time.ticks_ms()
        stage = -1
        while True:
            elapsed = time.ticks_diff(time.ticks_ms(), start)
            if elapsed >= 4000:
                break
            current = 0 if elapsed < 2000 else 1
            if current != stage:
                print('FORWARD 2s' if current == 0 else 'LEFT ARC 2s: candidate turn=+1')
                stage = current
            # Forward phase relation and previously tested 20/16 amplitudes.
            # Positive turn shortens left hip excursion; observe actual yaw.
            turn = 0 if current == 0 else min(1.0, (elapsed - 2000) / 300.0)
            scale = min(1.0, elapsed / 500.0)
            last_pose = pose_offsets(2 * math.pi * elapsed / 1000.0,
                                     scale, 20, 16, 4, turn=turn,
                                     turn_split=10, direction=1, yaw_trim=0)
            write(last_pose)
            time.sleep_ms(20)
        # Separate 300ms settling phase, outside the requested motion windows.
        settle = time.ticks_ms()
        while True:
            fraction = min(1.0, time.ticks_diff(time.ticks_ms(), settle) / 300.0)
            write([v * (1 - fraction) for v in last_pose])
            if fraction >= 1:
                break
            time.sleep_ms(20)
        print('DONE: recentered')
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
        print('PWM OFF; M1 stopped; servo power remains on')
