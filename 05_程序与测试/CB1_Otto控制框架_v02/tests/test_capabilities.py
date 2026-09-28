"""Task 4: actuator capability gating and config-driven channels.

The cb1_pwm driver is exercised against a STUB machine module so channel
creation policy is tested on the PC. Real PWM behaviour on the ESP32-C3
remains board-unverified and must not be claimed.
"""
import os
import sys
import types
import unittest
import importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import sim_config
import joint_model
import controller
import gait_planner
import states as S


def variant_profile(**joint_overrides):
    cfg = sim_config.virtual()
    import copy
    cfg.JOINTS = copy.deepcopy(cfg.JOINTS)
    name = joint_overrides.pop('joint')
    cfg.JOINTS[name].update(joint_overrides)
    return cfg


def hardware_copy():
    """A deep copy of the real hardware config as a plain object, so tests
    can degrade it without touching the global module."""
    import copy

    class Cfg:
        pass

    cfg = Cfg()
    for k, v in config.__dict__.items():
        if k.isupper():
            setattr(cfg, k, copy.deepcopy(v))
    return cfg


def make_ctrl(cfg):
    jm = joint_model.JointModel(cfg)
    from drivers import create_driver
    return controller.Controller(cfg, jm, gait_planner.GaitPlanner(cfg),
                                 create_driver(jm, cfg)), jm


class TestWalkCapabilityGate(unittest.TestCase):
    def test_virtual_profile_can_walk(self):
        ctrl, jm = make_ctrl(sim_config.virtual())
        self.assertEqual(jm.walk_blockers(), [])
        self.assertEqual(ctrl.enable(), S.READY)

    def test_real_config_calibrated_enables(self):
        # 2026-09-23 evening: all four joints centered and user-confirmed on
        # the robot, so the strict gate now opens on the real config.
        ctrl, jm = make_ctrl(config)
        self.assertEqual(jm.walk_blockers(), [])
        self.assertEqual(ctrl.enable(), S.READY)

    def test_uncalibrated_copy_still_refused(self):
        # The gate itself must keep refusing anything uncalibrated (verify
        # on a degraded copy - the real robot is calibrated now).
        cfg = hardware_copy()
        cfg.JOINTS['left_ankle']['calibrated'] = False
        ctrl, jm = make_ctrl(cfg)
        self.assertIn('left_ankle: not calibrated', jm.walk_blockers())
        with self.assertRaises(RuntimeError) as ctx:
            ctrl.enable()
        self.assertIn('not calibrated', str(ctx.exception))
        self.assertEqual(ctrl.state, S.DISABLED)
        self.assertEqual(ctrl.driver.frames, [])

    def test_continuous_channel_is_reported_when_enabled(self):
        ctrl, jm = make_ctrl(variant_profile(joint='left_ankle', enabled=True,
                                             actuator='continuous',
                                             calibrated=True))
        self.assertIn('left_ankle: continuous actuator cannot hold a pose',
                      jm.walk_blockers())
        with self.assertRaises(RuntimeError):
            ctrl.enable()

    def test_missing_joint_rejected(self):
        ctrl, jm = make_ctrl(variant_profile(joint='right_ankle',
                                             enabled=False))
        with self.assertRaises(RuntimeError) as ctx:
            ctrl.enable()
        self.assertIn('right_ankle: channel disabled', str(ctx.exception))

    def test_uncalibrated_joint_rejected(self):
        ctrl, jm = make_ctrl(variant_profile(joint='left_hip',
                                             calibrated=False))
        with self.assertRaises(RuntimeError) as ctx:
            ctrl.enable()
        self.assertIn('left_hip: not calibrated', str(ctx.exception))

    def test_wrong_actuator_type_rejected(self):
        ctrl, jm = make_ctrl(variant_profile(joint='right_hip',
                                             actuator='continuous'))
        with self.assertRaises(RuntimeError) as ctx:
            ctrl.enable()
        self.assertIn('right_hip: continuous actuator', str(ctx.exception))

    def test_debug_enable_allows_incomplete_and_marks_it(self):
        def degraded():
            cfg = hardware_copy()
            cfg.JOINTS['right_hip']['calibrated'] = False
            return cfg

        ctrl, _ = make_ctrl(degraded())
        logs = []
        ctrl.log = logs.append
        self.assertEqual(ctrl.enable_debug(), S.READY)
        self.assertTrue(any('INCOMPLETE OUTPUT' in m for m in logs))
        ctrl2, _ = make_ctrl(degraded())
        ctrl2.enable_debug()
        ctrl2.request_step('left')
        self.assertEqual(ctrl2.state, S.WALKING)
        done_logs = []
        ctrl2.log = done_logs.append
        import input_adapter as IA
        t = 0
        while ctrl2.state == S.WALKING:
            ctrl2.update(IA.from_manual(0, 0, False, True, t), t)
            t += 20
        self.assertTrue(any('DEBUG incomplete output' in m for m in done_logs))


class StubPwm:
    def __init__(self, pin, freq=None, duty=None):
        self.pin = pin
        self.commands = []

    def duty_ns(self, ns):
        self.commands.append(ns)

    def duty(self, level):
        self.commands.append(level)

    def deinit(self):
        self.commands.append('deinit')


class StubPin:
    OUT = 'out'
    IN = 'in'

    value_on_board = 0        # class attr: GPIO10 reads 0 (receiver)

    def __init__(self, pin, mode=None):
        self.pin = pin

    def value(self, v=None):
        return StubPin.value_on_board


def install_stub_machine():
    stub = types.ModuleType('machine')
    stub.Pin = StubPin
    stub.PWM = StubPwm
    sys.modules['machine'] = stub
    import drivers.cb1_pwm as mod
    importlib.reload(mod)
    return mod


class TestConfigDrivenChannels(unittest.TestCase):
    def setUp(self):
        self.saved_machine = sys.modules.get('machine')
        self.mod = install_stub_machine()

    def tearDown(self):
        sys.modules.pop('machine', None)
        import drivers.cb1_pwm as mod
        importlib.reload(mod)
        if self.saved_machine is not None:
            sys.modules['machine'] = self.saved_machine

    def make_driver(self, cfg):
        jm = joint_model.JointModel(cfg)
        return self.mod.Cb1PwmDriver(jm), jm

    def test_real_config_drives_all_four_position_channels(self):
        # Real truth since the S2 swap: four enabled position channels, so a
        # full-pose write pulses GPIO 0, 1, 2 and 3. (Continuous-channel
        # exclusion is covered by the variant test below.)
        cfg = config
        driver, jm = self.make_driver(cfg)
        driver.write([0.0, 0.0, 0.0, 0.0])
        created = sorted(driver.channels.keys())
        self.assertEqual(created, [0, 1, 2, 3])   # incl. GPIO2 (S2)
        driver.write([8.0, -8.0, 0.0, 0.0])
        self.assertEqual(sorted(driver.channels.keys()), [0, 1, 2, 3])
        driver.release()
        self.assertEqual(driver.channels, {})

    def test_enabled_position_channels_receive_pulses(self):
        cfg = sim_config.virtual()
        driver, jm = self.make_driver(cfg)
        driver.write([0.0, 0.0, 0.0, 0.0])
        self.assertEqual(sorted(driver.channels.keys()), [0, 1, 2, 3])
        # center pose -> 1500 us -> 1_500_000 ns on every channel
        for gpio in driver.channels:
            self.assertEqual(driver.channels[gpio].commands[-1], 1500000)

    def test_continuous_joint_never_commanded_even_if_enabled(self):
        cfg = variant_profile(joint='left_ankle', enabled=True,
                              actuator='continuous', calibrated=True)
        driver, jm = self.make_driver(cfg)
        driver.write([0.0, 0.0, 5.0, 0.0])
        self.assertNotIn(2, driver.channels)      # no PWM despite enabled

    def test_gpio10_guard_rejects_transmitter(self):
        StubPin.value_on_board = 1
        try:
            jm = joint_model.JointModel(config)
            with self.assertRaises(RuntimeError):
                self.mod.Cb1PwmDriver(jm)
        finally:
            StubPin.value_on_board = 0


class TestConfigIsolation(unittest.TestCase):
    def test_virtual_profile_never_mutates_hardware_truth(self):
        hw_before = repr((config.JOINTS, config.GAIT))
        cfg = sim_config.virtual()
        cfg.JOINTS['left_ankle']['enabled'] = True
        cfg.JOINTS['left_ankle']['actuator'] = 'position'
        cfg.JOINTS['left_ankle']['calibrated'] = True
        cfg.GAIT['hip_swing'] = 99.0
        self.assertEqual(repr((config.JOINTS, config.GAIT)), hw_before)
        self.assertTrue(config.JOINTS['left_ankle']['enabled'])
        self.assertEqual(config.JOINTS['left_ankle']['actuator'], 'position')
        self.assertTrue(config.JOINTS['left_ankle']['calibrated'])

    def test_swap_left_ankle_to_pg001_is_config_only(self):
        """Done 2026-09-23: the S2 swap needed only the JOINTS entry, no
        driver source change - kept as a regression test of the policy."""
        import copy

        class Cfg:
            pass

        cfg = Cfg()
        for k, v in config.__dict__.items():
            if k.isupper():
                setattr(cfg, k, copy.deepcopy(v))
        cfg.JOINTS['left_ankle'].update(enabled=True, actuator='position')
        for joint in cfg.JOINTS.values():   # tomorrow: after bench calibration
            joint['calibrated'] = True
        jm = joint_model.JointModel(cfg)
        self.assertEqual(jm.walk_blockers(), [])
        mod = install_stub_machine()
        try:
            driver = mod.Cb1PwmDriver(jm)
            driver.write([0.0, 0.0, 0.0, 0.0])
            self.assertIn(2, driver.channels)     # S2 now commanded
        finally:
            sys.modules.pop('machine', None)
            importlib.reload(mod)


class TestDriverSelectionFromConfig(unittest.TestCase):
    """Driver choice comes from the config object the caller passed in - a
    simulation profile must never select the hardware driver and vice
    versa, whatever the global config module happens to say."""

    def test_build_uses_passed_config_not_global(self):
        from drivers import create_driver
        cfg = sim_config.virtual()                  # built from sane globals
        jm = joint_model.JointModel(cfg)
        saved = config.DRIVER
        config.DRIVER = 'no_such_hardware_driver'   # poison the global AFTER
        try:
            ctrl = controller.Controller(
                cfg, jm, gait_planner.GaitPlanner(cfg),
                create_driver(jm, cfg))
            self.assertEqual(type(ctrl.driver).__name__, 'SimDriver')
        finally:
            config.DRIVER = saved

    def test_unknown_driver_in_cfg_is_rejected(self):
        from drivers import create_driver
        cfg = sim_config.virtual()
        cfg.DRIVER = 'bogus_mode'
        jm = joint_model.JointModel(cfg)
        with self.assertRaisesRegex(ValueError, 'bogus_mode'):
            create_driver(jm, cfg)


class TestWalkReadyMarkerHonesty(unittest.TestCase):
    """只要任一腿部关节不是已标定的180度位置舵机，任何入口都不得报告
    "四关节行走已准备好"（阶段一对中计划第6条）。真实硬件 2026-09-23 已
    四路标定，因此诚实性用降级副本验证。"""

    def test_calibrated_real_config_reports_ready(self):
        import io
        import main_v02
        import bench_v02
        from contextlib import redirect_stdout
        jm = joint_model.JointModel(config)
        self.assertTrue(jm.can_walk())
        buf = io.StringIO()
        with redirect_stdout(buf):
            blockers = bench_v02.diag()
        self.assertEqual(blockers, [])
        self.assertIn('walking: all four', buf.getvalue())
        self.assertNotIn('BLOCKED', buf.getvalue())
        self.assertEqual(main_v02.build_controller(config).enable(), S.READY)

    def test_incomplete_copy_never_reports_walk_ready(self):
        import io
        import main_v02
        import bench_v02
        import center_joint
        from contextlib import redirect_stdout
        cfg = hardware_copy()
        cfg.JOINTS['left_ankle']['calibrated'] = False
        jm = joint_model.JointModel(cfg)
        self.assertFalse(jm.can_walk())
        buf = io.StringIO()
        with redirect_stdout(buf):
            bench_v02.diag(cfg)
        self.assertIn('BLOCKED', buf.getvalue())
        self.assertNotIn('walking: all four', buf.getvalue())
        buf = io.StringIO()
        with redirect_stdout(buf):
            center_joint.list(cfg)
        self.assertIn('walking NOT ready', buf.getvalue())
        with self.assertRaises(RuntimeError):
            main_v02.build_controller(cfg).enable()   # strict gate refuses
        cfg = variant_profile(joint='left_ankle', enabled=True,
                              actuator='continuous')
        for j in cfg.JOINTS.values():
            j['calibrated'] = True
        jm = joint_model.JointModel(cfg)
        self.assertFalse(jm.can_walk())
        self.assertIn('continuous', '; '.join(jm.walk_blockers()))


if __name__ == '__main__':
    unittest.main()
