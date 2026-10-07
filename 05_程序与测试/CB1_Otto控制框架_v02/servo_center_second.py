"""CB1 second Otto: unloaded servo check, then hold S1-S4 at 90 degrees.

Board use (MicroPython REPL):
    import servo_center_second as center
    center.start(unloaded=True)  # horns/legs/feet must be detached
    center.off()                 # stop PWM after installing horns

Importing this module never moves a servo. This file does not change boot.py.
S1/S2/S3/S4 = GPIO 3/2/1/0; only 180-degree POSITION servos may be used.
"""

import time
from machine import Pin, PWM

PORTS = (('S1', 3, 'left_hip'),
         ('S2', 2, 'left_ankle'),
         ('S3', 1, 'right_hip'),
         ('S4', 0, 'right_ankle'))

_channels = {}


def _write_us(pwm, us):
    if hasattr(pwm, 'duty_ns'):
        pwm.duty_ns(int(us * 1000))
    elif hasattr(pwm, 'duty_u16'):
        pwm.duty_u16(int(us * 65535 / 20000))
    else:
        pwm.duty(int(us * 1023 / 20000))


def _angle(pwm, degrees):
    # PG001 project calibration: 0 deg=500 us, 90=1500 us, 180=2500 us.
    if degrees not in (90, 180):
        raise ValueError('this installation check only uses 90 or 180 deg')
    _write_us(pwm, 500 + degrees * 2000 / 180)


def start(unloaded=False):
    """First center all four, then check each 90->180->90; hold all at 90."""
    if not unloaded:
        raise RuntimeError('detach all four horns/legs/feet, then call start(unloaded=True)')
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError('GPIO10 != 0: this is not a CB1 receiver board')
    if _channels:
        raise RuntimeError('PWM already active in this module; call off() before restarting')

    try:
        for port, gpio, joint in PORTS:
            pwm = PWM(Pin(gpio), freq=50, duty=0)
            _channels[port] = pwm
            print(port, joint, 'GPIO', gpio, '-> 90 deg CENTER')
            _angle(pwm, 90)
            time.sleep_ms(1500)
        print('All four centered. Starting individual unloaded checks.')
        for port, gpio, joint in PORTS:
            pwm = _channels[port]
            print(port, joint, '90 -> 180 deg')
            _angle(pwm, 180)
            time.sleep_ms(3000)
            print(port, joint, '180 -> 90 deg')
            _angle(pwm, 90)
            time.sleep_ms(1500)
        print('DONE: S1-S4 all HOLDING 90 deg. Install horns now; call off() afterwards.')
    except BaseException:
        # An interrupted sweep must not leave a joint driving an end position.
        for pwm in _channels.values():
            try:
                _angle(pwm, 90)
            except Exception:
                pass
        off()
        raise


def off():
    """Stop all PWM outputs; this does not physically disconnect servo power."""
    for pwm in _channels.values():
        try:
            _write_us(pwm, 0)
        finally:
            pwm.deinit()
    _channels.clear()
    print('S1-S4 PWM off')


def status():
    print('holding ports:', tuple(_channels))


def wiggle():
    """Assembly-safe S1-S4 +5-degree check, then hold every port at 90."""
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError('GPIO10 != 0: this is not a CB1 receiver board')
    try:
        for port, gpio, joint in PORTS:
            if port not in _channels:
                _channels[port] = PWM(Pin(gpio), freq=50, duty=0)
            _angle(_channels[port], 90)
            print(port, joint, '-> 90 deg CENTER')
            time.sleep_ms(600)
        for port, gpio, joint in PORTS:
            print(port, joint, '90 -> 95 deg (small movement)')
            _write_us(_channels[port], 500 + 95 * 2000 / 180)
            time.sleep_ms(1500)
            print(port, joint, '95 -> 90 deg')
            _angle(_channels[port], 90)
            time.sleep_ms(700)
        print('DONE: S1-S4 all HOLDING 90 deg')
    except BaseException:
        for pwm in _channels.values():
            try:
                _angle(pwm, 90)
            except Exception:
                pass
        raise
