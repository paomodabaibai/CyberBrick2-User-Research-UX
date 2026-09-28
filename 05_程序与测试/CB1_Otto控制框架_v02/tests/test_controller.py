"""Controller tests: stop/fault (8-9), explicit enable & recenter (task 1),
timing anomalies (task 3), stale-state cleanup (task 5), joint conversion
(10), sim isolation (12). Runs on the VIRTUAL profile; capability gating
against the REAL config is covered in test_capabilities.py.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import sim_config
import input_adapter as IA
import joint_model
import gait_planner
import controller
import states as S
import timeutil
from drivers import create_driver

VC = sim_config.virtual()
JM = joint_model.JointModel(VC)


def make_stack(cfg=None):
    cfg = cfg or sim_config.virtual()
    jm = joint_model.JointModel(cfg)
    planner = gait_planner.GaitPlanner(cfg)
    driver = create_driver(jm, cfg)
    ctrl = controller.Controller(cfg, jm, planner, driver)
    return ctrl, driver


def run(ctrl, t0, ticks, left=0.0, right=0.0, stop=False, link=True):
    wrap = (1 << 30) - 1          # timestamps wrap like the board counter
    for i in range(ticks):
        t = (t0 + i * 20) & wrap
        inp = IA.from_manual(left, right, stop, link, t)
        ctrl.update(inp, t)
    return t0 + ticks * 20


class TestStopAndFault(unittest.TestCase):
    def test_8_stop_cancels_midstep_and_freezes(self):
        ctrl, driver = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 3)
        self.assertEqual(ctrl.state, S.READY)
        t = run(ctrl, t, 3, left=0.9)
        self.assertEqual(ctrl.state, S.WALKING)
        frozen = run(ctrl, t, 10, stop=True)
        self.assertEqual(ctrl.state, S.STOPPED)
        held = list(ctrl.pose)
        # task 5: interrupted action leaves NO residue to inherit
        self.assertIsNone(ctrl.trajectory)
        self.assertIsNone(ctrl.phase)
        self.assertIsNone(ctrl.step_side)
        # old action must not resume on its own
        t2 = run(ctrl, frozen, 40)
        self.assertEqual(ctrl.state, S.STOPPED)
        self.assertEqual(ctrl.pose, held)
        self.assertTrue(driver.frames)          # held pose had been written
        self.assertFalse(driver.released)       # stop holds, does not release

    def test_8b_release_clears_state_and_disables(self):
        ctrl, driver = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 3, left=0.9)
        ctrl.release_output()
        self.assertEqual(ctrl.state, S.DISABLED)
        self.assertTrue(driver.released)
        self.assertIsNone(ctrl.trajectory)
        self.assertIsNone(ctrl.phase)
        # re-enable starts clean (no stale action)
        ctrl.enable()
        self.assertIsNone(ctrl.trajectory)
        self.assertEqual(ctrl.state, S.READY)

    def test_9_link_loss_faults_reconnect_does_not_resume(self):
        ctrl, driver = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 3)               # observe recenter -> trigger armed
        t = run(ctrl, t, 3, left=0.9)
        self.assertEqual(ctrl.state, S.WALKING)
        t = run(ctrl, t, 40, link=False)
        self.assertEqual(ctrl.state, S.FAULT)
        self.assertIsNone(ctrl.trajectory)
        # link comes back: still faulted, no auto walk
        t = run(ctrl, t, 50)
        self.assertEqual(ctrl.state, S.FAULT)
        self.assertEqual(ctrl.recover(), S.READY)
        # and a held lever that was never recentred must not fire now
        t = run(ctrl, t, 10, left=0.9)
        self.assertEqual(ctrl.state, S.READY)

    def test_9b_recover_after_stop_needs_recenter_then_steps(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        ctrl.stop('bench')
        self.assertEqual(ctrl.recover(), S.READY)
        # old held input does not trigger (task 1: recover re-arms via center)
        t = run(ctrl, 0, 3, left=0.9)
        self.assertEqual(ctrl.state, S.READY)
        t = run(ctrl, t, 3)                     # both levers centered
        t = run(ctrl, t, 3, left=0.9)
        self.assertEqual(ctrl.state, S.WALKING)

    def test_k4_stops_then_explicit_recover(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        run(ctrl, 0, 3, left=0.9)
        run(ctrl, 100, 3, stop=True)
        self.assertEqual(ctrl.state, S.STOPPED)
        self.assertEqual(ctrl.recover(), S.READY)

    def test_enable_after_fault_requires_recover(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        ctrl.fault('test')
        with self.assertRaises(RuntimeError):
            ctrl.enable()

    def test_disabled_ignores_input(self):
        ctrl, _ = make_stack()
        t = run(ctrl, 0, 5, left=0.9)
        self.assertEqual(ctrl.state, S.DISABLED)
        self.assertEqual(ctrl.driver.frames, [])


class TestExplicitEnable(unittest.TestCase):
    def test_enable_requires_recenter_before_first_step(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 3, left=0.9)     # lever pushed since before enable
        self.assertEqual(ctrl.state, S.READY)
        self.assertEqual(ctrl.driver.frames[-1][1], [0.0] * 4)  # stance only
        t = run(ctrl, t, 3)               # observe both levers centered
        t = run(ctrl, t, 3, left=0.9)
        self.assertEqual(ctrl.state, S.WALKING)

    def test_enable_disarms_even_if_frame_is_centered_then_pushes(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 2)               # centered -> armed again
        t = run(ctrl, t, 3, left=0.9)
        self.assertEqual(ctrl.state, S.WALKING)

    def test_stop_keeps_no_auto_resume_and_recenter_gate(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 3, left=0.9)     # WALKING (armed by centering above)
        run(ctrl, t, 3, stop=True)
        self.assertEqual(ctrl.recover(), S.READY)
        # immediately pushing again must not fire (no observed recenter yet)
        t = run(ctrl, 0, 3, left=0.9)
        self.assertEqual(ctrl.state, S.READY)


class TestTiming(unittest.TestCase):
    def test_negative_dt_never_moves_pose(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 3)               # recenter observed -> armed
        t = run(ctrl, t, 3, left=0.9)
        self.assertEqual(ctrl.state, S.WALKING)
        pose_before = list(ctrl.pose)
        # clock jumps backwards: treated as zero elapsed
        ctrl.update(IA.from_manual(0.9, 0.0, False, True, t - 1000), t - 1000)
        self.assertEqual(ctrl.pose, pose_before)

    def test_stall_while_walking_faults_instead_of_jumping(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 3)
        t = run(ctrl, t, 3, left=0.9)
        self.assertEqual(ctrl.state, S.WALKING)
        pose_before = list(ctrl.pose)
        # one huge gap (> STALL_MS): must NOT consume it as gait time
        ctrl.update(IA.from_manual(0.0, 0.0, False, True, t + 5000), t + 5000)
        self.assertEqual(ctrl.state, S.FAULT)
        self.assertIn('stall', ctrl.reason)
        self.assertEqual(ctrl.pose, pose_before)   # pose did not teleport
        self.assertIsNone(ctrl.trajectory)

    def test_long_idle_then_first_step_does_not_inherit_wait(self):
        ctrl, _ = make_stack()
        ctrl.enable()
        t = run(ctrl, 0, 3)
        # idle gap in READY (allowed: nothing in flight)
        ctrl.update(IA.from_manual(0.0, 0.0, False, True, t + 400), t + 400)
        t = t + 400
        t = run(ctrl, t, 1, left=0.9)     # the tick that STARTS the step
        self.assertEqual(ctrl.state, S.WALKING)
        # the starting tick contributed zero gait time (old wait discarded)
        self.assertEqual(ctrl.trajectory.elapsed_in_seg, 0.0)
        t = run(ctrl, t, 2, left=0.9)     # two normal ticks -> 40 ms elapsed
        self.assertAlmostEqual(ctrl.trajectory.elapsed_in_seg, 40.0)

    def test_timeutil_wrap_difference(self):
        wrap = 1 << 30
        self.assertEqual(timeutil.diff_ms(5, wrap - 10), 15)
        self.assertEqual(timeutil.diff_ms(wrap - 10, 5), -15)
        self.assertEqual(timeutil.diff_ms(0, 0), 0)

    def test_walk_across_counter_wrap_same_result(self):
        wrap = 1 << 30
        # uniform feed below the wrap point
        c1, _ = make_stack()
        c1.enable()
        t = run(c1, 0, 3, left=0.9)
        run(c1, t, 90)
        # same feed crossing the wrap point
        c2, _ = make_stack()
        c2.enable()
        t0 = wrap - 50
        t = run(c2, t0, 3, left=0.9)
        run(c2, t, 90)
        for a, b in zip(c1.pose, c2.pose):
            self.assertAlmostEqual(a, b, places=6)


class TestJointConversion(unittest.TestCase):
    def test_10_center_direction_mirror_limits(self):
        self.assertEqual(JM.servo_angle('left_hip', 0.0), 90.0)
        self.assertEqual(JM.servo_angle('left_hip', 8.0), 98.0)
        # mirrored joint: direction=-1 flips the offset
        import copy
        cfg = sim_config.virtual()
        cfg.JOINTS = copy.deepcopy(VC.JOINTS)
        cfg.JOINTS['left_hip']['direction'] = -1
        jm2 = joint_model.JointModel(cfg)
        self.assertEqual(jm2.servo_angle('left_hip', 8.0), 82.0)

    def test_10b_limit_violation_raises(self):
        with self.assertRaises(joint_model.LimitViolation):
            JM.servo_angles([45.0, 0.0, 0.0, 0.0])   # 90+45=135 > 115

    def test_10c_pulse_midpoint(self):
        self.assertAlmostEqual(JM.pulses([0.0, 0.0, 0.0, 0.0])[0], 1500.0)


class TestSimIsolation(unittest.TestCase):
    def test_12_default_mode_no_machine_no_pwm(self):
        # start from a clean slate: capability tests may have imported the
        # cb1 driver with a stub machine earlier in this process
        sys.modules.pop('machine', None)
        sys.modules.pop('drivers.cb1_pwm', None)
        driver = create_driver(JM, VC)
        self.assertEqual(type(driver).__name__, 'SimDriver')
        self.assertNotIn('machine', sys.modules)
        self.assertNotIn('drivers.cb1_pwm', sys.modules)
        # exercise a short replay through Simulator as well
        from simulator import Simulator
        sim = Simulator()
        sim.run_script([(0, 'enable', None), (100, 'lever_left', 0.9),
                        (2500, 'lever_left', 0.0)], total_ms=3200)
        self.assertTrue(sim.driver.frames)
        self.assertNotIn('machine', sys.modules)   # sim path never loads it


if __name__ == '__main__':
    unittest.main()
