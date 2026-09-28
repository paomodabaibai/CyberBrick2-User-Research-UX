"""CB1 PWM driver. NEVER imported in simulation mode; machine loads lazily.

Channel policy is fully config-driven (task 4) - no joint names hardcoded:
- disabled joint            -> no PWM object is EVER created for it
- continuous actuator       -> never commanded through the angle interface,
                               no PWM object either
- enabled position actuator -> PWM created on first write, duty in µs

Wiring facts from v01 (2026-09-22, see 现场调试记录):
- receiver board: GPIO10 must read 0; S1/S2/S3/S4 = GPIO 3/2/1/0
- release() deinitializes all PWM; Ctrl-C in a REPL also falls through here

Board-side static check only: this module has been kept free of os.path /
sys.path and of anything beyond MicroPython's os/sys/time/machine surface.
Actual PWM behavior on the ESP32-C3 is UNVERIFIED until a bench session.
"""

class Cb1PwmDriver:
    def __init__(self, joint_model_ref):
        import machine  # deferred: only on real hardware
        if machine.Pin(10, machine.Pin.IN).value() != 0:
            raise RuntimeError('GPIO10 != 0: this is not the receiver board')
        self._machine = machine
        self.jm = joint_model_ref
        self.channels = {}

    def _commandable(self, name):
        cfg = self.jm.joints[name]
        return cfg.get('enabled', True) and cfg.get('actuator') == 'position'

    def write(self, pose, now_ms=None):
        pulses = self.jm.pulses(pose)
        for name, us in zip(self.jm.order, pulses):
            if not self._commandable(name):
                continue          # disabled/continuous: stays pulse-less
            from machine import Pin, PWM
            gpio = self.jm.joints[name]['gpio']
            if gpio not in self.channels:
                self.channels[gpio] = PWM(Pin(gpio), freq=50, duty=0)
            p = self.channels[gpio]
            if hasattr(p, 'duty_ns'):
                p.duty_ns(int(us * 1000))
            else:
                p.duty(int(us * 1023 / 20000))

    def write_one(self, name, angle_deg, now_ms=None):
        """Pulse exactly ONE named channel at an ABSOLUTE servo angle.

        For mechanical centering (90 deg) before horns are installed.
        Refuses disabled channels and continuous actuators loudly - a
        360-degree servo must never receive a position command. Angle maps
        linearly to the pulse range in config (0 -> PULSE_AT_0_US,
        180 -> PULSE_AT_180_US); center/trim are intentionally NOT applied:
        centering must show the raw electrical midpoint.
        """
        cfg = self.jm.joints[name]
        if not cfg.get('enabled', True):
            raise RuntimeError('write_one refused: %s is disabled in config'
                               % name)
        if cfg.get('actuator') != 'position':
            raise RuntimeError(
                'write_one refused: %s is a %r actuator - a continuous '
                'servo must never receive a position command'
                % (name, cfg.get('actuator')))
        if not 0.0 <= float(angle_deg) <= 180.0:
            raise ValueError('angle %s outside 0..180' % angle_deg)
        from machine import Pin, PWM
        gpio = cfg['gpio']
        if gpio not in self.channels:
            self.channels[gpio] = PWM(Pin(gpio), freq=50, duty=0)
        us = (self.jm.pulse0 + (self.jm.pulse180 - self.jm.pulse0)
              * float(angle_deg) / 180.0)
        p = self.channels[gpio]
        if hasattr(p, 'duty_ns'):
            p.duty_ns(int(us * 1000))
        else:
            p.duty(int(us * 1023 / 20000))

    def release(self):
        for p in self.channels.values():
            p.duty(0)
            p.deinit()
        self.channels = {}


def create(joint_model_ref, cfg):
    # Same-config rule: the guard checks the cfg the caller built its stack
    # from, never the global module (PC config stays 'sim').
    if cfg.DRIVER != 'cb1_pwm':
        raise RuntimeError('cb1 driver requested but DRIVER=%r' % cfg.DRIVER)
    return Cb1PwmDriver(joint_model_ref)
