"""center_joint tests: single-channel 90-degree centering utility.

Import-safe, name-based channel lookup, loud refusal of continuous S2, and
a real policy test of Cb1PwmDriver.write_one against a stub machine.
"""
import copy
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import sim_config
import center_joint


def variant(joint=None, **overrides):
    cfg = sim_config.virtual()
    cfg.JOINTS = copy.deepcopy(cfg.JOINTS)
    name = overrides.pop('name', joint)
    if name:
        cfg.JOINTS[name].update(overrides)
    return cfg


def make_hw_copy(uncalibrated=None):
    """Deep copy of the real config, optionally degrading one joint to
    uncalibrated (the real robot is calibrated since 2026-09-23)."""

    class Cfg:
        pass

    cfg = Cfg()
    for k, v in config.__dict__.items():
        if k.isupper():
            setattr(cfg, k, copy.deepcopy(v))
    if uncalibrated:
        cfg.JOINTS[uncalibrated]['calibrated'] = False
    return cfg


class StubPin:
    value_on_board = 0
    IN = 1
    OUT = 3

    def __init__(self, pin, mode=None):
        self.pin = pin

    def value(self, v=None):
        return StubPin.value_on_board


class StubPwm:
    def __init__(self, pin, freq, duty=0):
        self.pin = pin.pin if hasattr(pin, 'pin') else pin
        self.freq = freq
        self.duty_written = [duty] if duty else []
        self.duty_ns_written = []

    def duty(self, d):
        self.duty_written.append(d)

    def duty_ns(self, ns):
        self.duty_ns_written.append(ns)

    def deinit(self):
        pass


def install_stub_machine():
    import types
    import importlib
    import drivers.cb1_pwm as mod
    stub = types.ModuleType('machine')
    stub.Pin = StubPin
    stub.PWM = StubPwm
    sys.modules['machine'] = stub
    importlib.reload(mod)
    return mod


class TestCenterJoint(unittest.TestCase):
    def setUp(self):
        center_joint._driver = None
        center_joint._driver_cfg = None

    def tearDown(self):
        center_joint._driver = None
        center_joint._driver_cfg = None

    def test_import_and_list_are_read_only(self):
        self.assertIsNone(center_joint._driver)      # import creates nothing
        out = io.StringIO()
        with redirect_stdout(out):
            center_joint.list()
        text = out.getvalue()
        self.assertIn('left_ankle', text)
        # real config is calibrated since 2026-09-23: no refusal line
        self.assertNotIn('walking NOT ready', text)
        # degraded copy still reports honestly
        out2 = io.StringIO()
        with redirect_stdout(out2):
            center_joint.list(make_hw_copy('left_ankle'))
        self.assertIn('walking NOT ready', out2.getvalue())

    def test_unknown_joint_rejected(self):
        with self.assertRaises(ValueError):
            center_joint.send('front_leg', confirmed=True)

    def test_unconfirmed_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'confirmed'):
            center_joint.send('right_hip')

    def test_disabled_channel_rejected(self):
        # No channel is disabled in the real config any more (S2 now a
        # position servo), so the refusal is exercised on a disabled variant.
        cfg = variant(joint='right_ankle', enabled=False)
        with self.assertRaisesRegex(RuntimeError, 'disabled'):
            center_joint.send('right_ankle', cfg=cfg, confirmed=True,
                              allow_sim=True)

    def test_continuous_actuator_rejected_even_if_enabled(self):
        cfg = variant(joint='left_ankle', enabled=True,
                      actuator='continuous', calibrated=True)
        with self.assertRaisesRegex(RuntimeError, 'continuous'):
            center_joint.send('left_ankle', cfg=cfg, confirmed=True,
                              allow_sim=True)

    def test_sim_driver_refused_without_allow_sim(self):
        with self.assertRaisesRegex(RuntimeError, 'simulation driver'):
            center_joint.send('right_hip', confirmed=True)   # PC config='sim'

    def test_send_pulses_only_named_channel(self):
        drv = center_joint.send('right_hip', confirmed=True, allow_sim=True)
        self.assertEqual(drv.singles, [('right_hip', 90.0)])
        self.assertEqual(drv.frames, [])             # no full-pose write
        center_joint.off()
        self.assertTrue(drv.released)

    def test_send_custom_angle_and_auto_off(self):
        drv = center_joint.send('left_hip', angle=95.0, seconds=0,
                                confirmed=True, allow_sim=True)
        self.assertEqual(drv.singles, [('left_hip', 95.0)])
        self.assertTrue(drv.released)                # seconds=0 -> auto off


class TestOneChannelGuarantee(unittest.TestCase):
    """复核修正：切换关节自动释放旧通道；seconds 等待被打断也保证关闭。"""

    def setUp(self):
        center_joint._driver = None
        center_joint._driver_cfg = None
        center_joint._active = None

    def tearDown(self):
        center_joint._driver = None
        center_joint._driver_cfg = None
        center_joint._active = None

    def test_switching_joint_releases_previous_channel(self):
        import sys
        import types
        import importlib
        import drivers.cb1_pwm as mod
        old = sys.modules.get('machine')
        stub = types.ModuleType('machine')
        stub.Pin = StubPin
        stub.PWM = StubPwm
        sys.modules['machine'] = stub
        importlib.reload(mod)
        try:
            cfg = sim_config.virtual()
            cfg.DRIVER = 'cb1_pwm'
            center_joint.send('left_hip', cfg=cfg, confirmed=True)
            drv = center_joint._driver
            self.assertEqual(sorted(drv.channels.keys()), [3])   # GPIO3 only
            center_joint.send('right_hip', cfg=cfg, confirmed=True)
            # previous channel MUST be gone even though off() was never called
            self.assertEqual(sorted(drv.channels.keys()), [1])
        finally:
            sys.modules.pop('machine', None)
            if old is not None:
                sys.modules['machine'] = old
            importlib.reload(mod)

    def test_seconds_wait_interrupted_by_ctrl_c_still_releases(self):
        original = center_joint._sleep

        def boom(seconds):
            raise KeyboardInterrupt

        center_joint._sleep = boom
        try:
            with self.assertRaises(KeyboardInterrupt):
                center_joint.send('right_hip', seconds=5, confirmed=True,
                                  allow_sim=True)
        finally:
            center_joint._sleep = original
        self.assertTrue(center_joint._driver.released)
        self.assertIsNone(center_joint._active)

    def test_seconds_wait_exception_still_releases(self):
        original = center_joint._sleep

        def boom(seconds):
            raise RuntimeError('wait failed')

        center_joint._sleep = boom
        try:
            with self.assertRaisesRegex(RuntimeError, 'wait failed'):
                center_joint.send('right_hip', seconds=5, confirmed=True,
                                  allow_sim=True)
        finally:
            center_joint._sleep = original
        self.assertTrue(center_joint._driver.released)
        self.assertIsNone(center_joint._active)


class TestCb1WriteOnePolicy(unittest.TestCase):
    """write_one channel policy on the real driver with a stub machine."""

    def setUp(self):
        import sys
        self._had_machine = 'machine' in sys.modules
        self._old = sys.modules.get('machine')
        self.mod = install_stub_machine()

    def tearDown(self):
        import sys
        import importlib
        sys.modules.pop('machine', None)
        if self._had_machine and self._old is not None:
            sys.modules['machine'] = self._old
        importlib.reload(self.mod)

    def test_write_one_center_pulse_and_channel_policy(self):
        import joint_model
        jm = joint_model.JointModel(config)
        drv = self.mod.Cb1PwmDriver(jm)
        drv.write_one('right_hip', 90.0)
        self.assertEqual(list(drv.channels.keys()), [1])   # S3/GPIO1 only
        p = drv.channels[1]
        self.assertEqual(p.duty_ns_written, [1500000])     # 90 deg = midpoint
        # S2 swapped to a position servo on 2026-09-23: write_one now
        # creates its channel too (the continuous refusal is covered in
        # TestCenterJoint via a continuous variant).
        drv.write_one('left_ankle', 90.0)
        self.assertEqual(list(drv.channels.keys()), [1, 2])
        self.assertEqual(drv.channels[2].duty_ns_written, [1500000])
        drv.release()
        self.assertEqual(drv.channels, {})


if __name__ == '__main__':
    unittest.main()
