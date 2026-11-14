"""D1/GPIO21 pulse writer for the palm's continuous rotation servo.

The ONLY writer of this pin. Deliberately separate from the leg driver:
a continuous servo takes speed pulses (neutral = stop), never angles,
and must never be pulled into the joint position model or its limit
validation.

- construction creates NO hardware state; the PWM object appears lazily
  on the first write_us
- pulse widths are validated against neutral +/- delta: out-of-range
  raises instead of clamping into unexpected motion
- stop(): continuous stop pulse (neutral), but only if the channel is
  already active - stopping must not create hardware
- release(): neutral -> duty(0) -> deinit; safe to call repeatedly
"""
_machine = None


def _machine_module():
    """Lazy machine import: PC tests stub palm_pwm._machine directly."""
    global _machine
    if _machine is None:
        import machine
        _machine = machine
    return _machine


class PalmPwmDriver:
    def __init__(self, cfg):
        self.cfg = dict(cfg)
        self._pwm = None
        self._pulse_us = None

    def is_active(self):
        return self._pwm is not None

    def last_pulse_us(self):
        return self._pulse_us

    def _limits(self):
        n = int(self.cfg['neutral_us'])
        d = int(self.cfg['delta_us'])
        return n - d, n + d

    def write_us(self, pulse_us):
        lo, hi = self._limits()
        pulse_us = int(pulse_us)
        if not lo <= pulse_us <= hi:
            raise ValueError('palm pulse %dus outside [%d, %d]'
                             % (pulse_us, lo, hi))
        if self._pwm is None:
            m = _machine_module()
            self._pwm = m.PWM(self.cfg['gpio'], int(self.cfg['freq_hz']))
        self._set_pulse(pulse_us)

    def _set_pulse(self, pulse_us):
        us = int(pulse_us)
        if hasattr(self._pwm, 'duty_ns'):
            self._pwm.duty_ns(us * 1000)
        else:
            self._pwm.duty(int(us * 1023 / 20000))
        self._pulse_us = us

    def stop(self):
        if self._pwm is not None:
            self._set_pulse(self.cfg['neutral_us'])

    def release(self):
        if self._pwm is None:
            return
        self._set_pulse(self.cfg['neutral_us'])
        if hasattr(self._pwm, 'duty'):
            self._pwm.duty(0)
        self._pwm.deinit()
        self._pwm = None
        self._pulse_us = None
