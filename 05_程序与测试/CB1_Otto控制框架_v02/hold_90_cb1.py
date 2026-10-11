"""CB1 Otto assembly tool: hold S1-S4 position servos at electrical 90 deg.

Works on either robot, one receiver board at a time. Importing is inert.
REPL: import hold_90_cb1 as h; h.hold()
      h.status(); h.off()
Does not touch D1/D2, M1/M2, boot.py or radio pairing.
"""

from machine import Pin, PWM


PORTS = (("S1", 3, "left_hip"),
         ("S2", 2, "left_ankle"),
         ("S3", 1, "right_hip"),
         ("S4", 0, "right_ankle"))

_channels = {}


def _center(pwm):
    # PG001 project calibration: 50 Hz, 90 deg = 1500 microseconds.
    if hasattr(pwm, "duty_ns"):
        pwm.duty_ns(1500000)
    elif hasattr(pwm, "duty_u16"):
        pwm.duty_u16(int(1500 * 65535 / 20000))
    else:
        pwm.duty(int(1500 * 1023 / 20000))


def hold():
    """Center and continuously hold four 180-degree position servos.

    A call can move installed legs suddenly. Support the robot before use.
    PWM persists in module globals until off() or board reset/power loss.
    """
    if Pin(10, Pin.IN).value() != 0:
        raise RuntimeError("GPIO10 != 0: connect a CB1 receiver, not transmitter")
    try:
        for port, gpio, joint in PORTS:
            if port not in _channels:
                _channels[port] = PWM(Pin(gpio), freq=50)
            _center(_channels[port])
            print(port, joint, "GPIO", gpio, "holding 90 deg")
    except BaseException:
        off()
        raise
    print("S1-S4 holding 90 deg; do not unplug power while fitting horns")


def status():
    print("active PWM ports:", tuple(_channels))


def off():
    """Stop PWM pulses. This does not cut servo power at the battery."""
    for pwm in _channels.values():
        try:
            pwm.deinit()
        except Exception:
            pass
    _channels.clear()
    print("S1-S4 PWM off")
