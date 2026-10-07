"""PalmPwmDriver tests: D1/GPIO21 pulse writer with a fake machine.

Contract (D1 execution plan):
- construction creates NO pwm; the PWM object is created lazily on the
  first write_us (import side effects forbidden)
- 50 Hz on the configured GPIO only; pulse widths limited to
  neutral +/- delta (out-of-range raises, never silently clamped)
- stop(): writes neutral ONLY if the pwm already exists (stopping must
  not create hardware state)
- release(): neutral -> duty(0) -> deinit; repeatable; a later write_us
  recreates the channel
- never touches the leg GPIOs or changes the leg PWM setup
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from drivers import palm_pwm


class FakePWM:
    def __init__(self, log, gpio, freq):
        self.log = log
        log.append(('init', gpio, freq))

    def duty_ns(self, ns):
        self.last_ns = ns

    def duty(self, value):
        self.log.append(('duty', value))

    def deinit(self):
        pass


class TestPalmPwm(unittest.TestCase):
    def setUp(self):
        self.log = []
        self.instances = []
        self._saved = palm_pwm._machine

        def make_pwm(gpio, freq):
            pwm = FakePWM(self.log, gpio, freq)
            self.instances.append(pwm)
            return pwm

        palm_pwm._machine = type('M', (), {'PWM': staticmethod(make_pwm)})

    def tearDown(self):
        palm_pwm._machine = self._saved

    def make(self, **overrides):
        cfg = dict(config.ATTACK)
        cfg.update(overrides)
        return palm_pwm.PalmPwmDriver(cfg)

    def test_construction_creates_no_pwm(self):
        drv = self.make()
        self.assertEqual(self.log, [])
        self.assertFalse(drv.is_active())
        self.assertIsNone(drv.last_pulse_us())

    def test_write_creates_gpio_50hz_and_sets_pulse(self):
        drv = self.make()
        drv.write_us(1600)
        self.assertEqual(self.log[0], ('init', config.ATTACK['gpio'],
                                       config.ATTACK['freq_hz']))
        self.assertTrue(drv.is_active())
        self.assertEqual(drv.last_pulse_us(), 1600)
        self.assertEqual(self.instances[-1].last_ns, 1600 * 1000)

    def test_out_of_range_pulse_raises_never_clamps(self):
        drv = self.make()
        self.assertRaises(ValueError, drv.write_us,
                          config.ATTACK['neutral_us'] - 201)
        self.assertRaises(ValueError, drv.write_us,
                          config.ATTACK['neutral_us'] + 201)
        self.assertEqual(self.log, [])          # nothing was ever created

    def test_stop_writes_neutral_only_if_active(self):
        drv = self.make()
        drv.stop()
        self.assertEqual(self.log, [])          # not active: no PWM created
        drv.write_us(1600)
        drv.stop()
        self.assertEqual(drv.last_pulse_us(), config.ATTACK['neutral_us'])

    def test_release_sequence_and_repeatability(self):
        drv = self.make()
        drv.release()                            # nothing active: no-op
        self.assertEqual(self.log, [])
        drv.write_us(1400)
        drv.release()
        self.assertIn(('duty', 0), self.log)     # pulses off
        self.assertFalse(drv.is_active())
        self.assertIsNone(drv.last_pulse_us())   # neutral then deinit
        drv.release()                            # repeatable: still a no-op
        self.assertEqual(len(self.log), 2)       # init, duty0 (no new PWM)
        drv.write_us(1600)                       # can come back afterwards
        self.assertEqual(drv.last_pulse_us(), 1600)

    def test_only_the_configured_gpio_is_touched(self):
        drv = self.make()
        drv.write_us(1600)
        for entry in self.log:
            if entry[0] == 'init':
                self.assertEqual(entry[1], config.ATTACK['gpio'])
                self.assertEqual(entry[2], config.ATTACK['freq_hz'])


if __name__ == '__main__':
    unittest.main()
