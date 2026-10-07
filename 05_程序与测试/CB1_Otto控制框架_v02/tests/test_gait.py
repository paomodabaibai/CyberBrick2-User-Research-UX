"""Acceptance tests 5-7 + 11, plus task-2 phase-ordering tests: swing before
landing, land holds hips, per-hip starts, configurable signs.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import sim_config
import joint_model
import gait_planner
import trajectory

VC = sim_config.virtual()
JM = joint_model.JointModel(VC)


def run_trajectory(traj, tick=20):
    poses = []
    done = False
    while not done:
        pose, phase, done = traj.update(tick)
        poses.append(pose)
    return poses


class TestFirstAndAlternate(unittest.TestCase):
    def test_5a_first_step_left(self):
        traj = gait_planner.GaitPlanner(VC).plan_step(
            'left', [0.0] * 4, None, jm=JM)
        seg_names = [s.name for s in traj.segments]
        self.assertEqual(seg_names, ['prepare', 'weight_shift',
                                     'unload_swing', 'land', 'stabilize'])
        poses = run_trajectory(traj)
        end = poses[-1]
        for a, b in zip(end, [config.GAIT['hip_swing'],
                              config.GAIT['hip_swing'], 0.0, 0.0]):
            self.assertAlmostEqual(a, b, places=6)

    def test_5b_first_step_right_mirrors(self):
        traj = gait_planner.GaitPlanner(VC).plan_step(
            'right', [0.0] * 4, None, jm=JM)
        end = run_trajectory(traj)[-1]
        h = config.GAIT['hip_swing']
        self.assertAlmostEqual(end[0], -h)
        self.assertAlmostEqual(end[1], -h)
        # swing pose: the STEPPING ankle (index 3, S4) tilts TOE-DOWN
        # (unloaded/lifted) and the support ankle (S2) toe-up. With the
        # 2026-09-24 flipped ankle signs (-1/-1) and S4+=toe down, the
        # right-step stepping ankle is POSITIVE; support is negative.
        swing = traj.segments[2].target
        self.assertAlmostEqual(swing[3], (config.GAIT['lean'] + config.GAIT['lift']))
        self.assertAlmostEqual(swing[2], config.GAIT['lean'])

    def test_6_alternate_step_continuous_no_jump(self):
        p = gait_planner.GaitPlanner(VC)
        first = run_trajectory(p.plan_step('left', [0.0] * 4, None, jm=JM))
        traj2 = p.plan_step('right', first[-1], 'left', jm=JM)
        # seamless handover: second trajectory starts exactly at first end
        # (v03 prepare retracts from there; the START must be the end pose)
        self.assertEqual(traj2.pose, first[-1])
        second = run_trajectory(traj2)
        # per-tick change must stay small for a 20 ms loop (smooth steps)
        max_step = max(abs(b[i] - a[i])
                       for a, b in zip(second, second[1:])
                       for i in range(4))
        # 16 deg hip swing across >= 250 ms -> bound well below a servo jump
        # (2026-09-24: raised to 5 with lean=15/lift=10 v03 amplitudes - the
        # ankle now covers 25 deg inside the 300 ms swing phase)
        self.assertLess(max_step, 5.0)
        # alternate end mirrors the first step
        self.assertAlmostEqual(second[-1][0], -config.GAIT['hip_swing'])


class TestSameSide(unittest.TestCase):
    """v03 (2026-09-24): repeated same-side steps are SUPPORTED - the user's
    control model is hold-one-lever = continuous same-side steps = turn."""

    def test_7_same_side_retracts_through_center(self):
        p = gait_planner.GaitPlanner(VC)
        first = run_trajectory(p.plan_step('left', [0.0] * 4, None, jm=JM))
        traj = p.plan_step('left', first[-1], 'left', jm=JM)
        segs = traj.segments
        # prepare RETRACTS the hips to stance (0), not holds them apart
        self.assertEqual(segs[0].target, [0.0, 0.0, 0.0, 0.0])
        # the step still ends at the full swing bias
        end = run_trajectory(traj)[-1]
        for a, b in zip(end, [config.GAIT['hip_swing'],
                               config.GAIT['hip_swing'], 0.0, 0.0]):
            self.assertAlmostEqual(a, b, places=6)
        self.assertEqual(p.same_side_strategy('left', 'left'), 'retract')

    def test_7b_same_side_still_smooth(self):
        p = gait_planner.GaitPlanner(VC)
        first = run_trajectory(p.plan_step('left', [0.0] * 4, None, jm=JM))
        traj2 = p.plan_step('left', first[-1], 'left', jm=JM)
        self.assertEqual(traj2.pose, first[-1])   # seamless handover
        second = run_trajectory(traj2)
        max_step = max(abs(b[i] - a[i])
                       for a, b in zip(second, second[1:])
                       for i in range(4))
        self.assertLess(max_step, 5.0)   # v03 amplitudes (see test_6 note)


class TestBackwardStep(unittest.TestCase):
    """v03: backward=True reverses the hip swing only; the weight-shift
    lean still depends on the stepping SIDE (weight must go onto the same
    support foot whichever way the foot travels)."""

    def test_backward_swings_hips_the_other_way(self):
        p = gait_planner.GaitPlanner(VC)
        fwd = p.plan_step('left', [0.0] * 4, None, jm=JM)
        back = p.plan_step('left', [0.0] * 4, None, backward=True, jm=JM)
        h = config.GAIT['hip_swing']
        self.assertAlmostEqual(fwd.segments[2].target[0], h)
        self.assertAlmostEqual(back.segments[2].target[0], -h)
        self.assertAlmostEqual(back.segments[-1].target[1], -h)
        # lean targets identical: same side, same support, same weight shift
        self.assertEqual(fwd.segments[1].target, back.segments[1].target)
        self.assertEqual(fwd.segments[2].target[2:],
                         back.segments[2].target[2:])
        # phase set unchanged
        self.assertEqual([s.name for s in back.segments],
                         ['prepare', 'weight_shift', 'unload_swing',
                          'land', 'stabilize'])

    def test_backward_right_mirrors(self):
        p = gait_planner.GaitPlanner(VC)
        back = p.plan_step('right', [0.0] * 4, None, backward=True, jm=JM)
        h = config.GAIT['hip_swing']
        # right side has step_sign -1: backward flips it to +h
        self.assertAlmostEqual(back.segments[2].target[0], h)
        self.assertAlmostEqual(back.segments[2].target[1], h)


class TestPhaseOrdering(unittest.TestCase):
    """Task 2: the MAIN hip swing belongs to unload_swing; land only sets
    the foot down; each hip starts from its own current value."""

    def test_swing_completes_during_unload_swing(self):
        p = gait_planner.GaitPlanner(VC)
        traj = p.plan_step('left', [0.0] * 4, None, jm=JM)
        segs = traj.segments
        h = config.GAIT['hip_swing']
        # end of unload_swing: hips already at the full swing bias
        self.assertAlmostEqual(segs[2].target[0], h)
        self.assertAlmostEqual(segs[2].target[1], h)
        # land and stabilize HOLD that bias (no second swing)
        for seg in segs[3:]:
            self.assertAlmostEqual(seg.target[0], h)
            self.assertAlmostEqual(seg.target[1], h)

    def test_land_phase_moves_hips_not_at_all(self):
        p = gait_planner.GaitPlanner(VC)
        traj = p.plan_step('left', [0.0] * 4, None, jm=JM)
        max_hip_delta_in_land = 0.0
        done = False
        while not done:
            prev = list(traj.pose)
            pose, phase, done = traj.update(20)
            if phase == 'land':
                max_hip_delta_in_land = max(
                    max_hip_delta_in_land,
                    abs(pose[0] - prev[0]), abs(pose[1] - prev[1]))
        self.assertLess(max_hip_delta_in_land, 0.2)   # ~zero vs servo resolution
        # land did move the ankles back to contact
        self.assertAlmostEqual(traj.pose[2], 0.0, places=6)
        self.assertAlmostEqual(traj.pose[3], 0.0, places=6)

    def test_asymmetric_start_retracts_each_hip_smoothly(self):
        p = gait_planner.GaitPlanner(VC)
        start = [3.0, -2.0, 1.0, 0.5]     # e.g. frozen mid-step by a stop
        traj = p.plan_step('left', start, None, jm=JM)
        segs = traj.segments
        # v03 prepare retracts BOTH hips to stance (0) - never assume they
        # are equal: each interpolates from its own value through 20 ms ticks
        self.assertEqual(segs[0].target, [0.0, 0.0, 0.0, 0.0])
        # weight_shift holds the retracted stance
        self.assertEqual(segs[1].target[:2], [0.0, 0.0])
        # interpolation starts from the real commanded pose, no teleport
        pose, phase, done = traj.update(1)
        self.assertAlmostEqual(pose[0], 3.0, places=3)
        self.assertAlmostEqual(pose[1], -2.0, places=3)
        self.assertFalse(done)

    def test_phase_continuity_by_construction(self):
        p = gait_planner.GaitPlanner(VC)
        traj = p.plan_step('left', [1.5, -0.5, 0.2, 0.0], None, jm=JM)
        prev = list(traj.pose)
        done = False
        while not done:
            pose, phase, done = traj.update(20)
            for a, b in zip(prev, pose):
                self.assertLessEqual(abs(b - a), 5.0)
            prev = pose

    def test_step_and_ankle_signs_are_configurable(self):
        import copy
        cfg = sim_config.virtual()
        cfg.GAIT = copy.deepcopy(VC.GAIT)
        s_l = cfg.GAIT['step_sign_left'] = -1.0
        cfg.GAIT['step_sign_right'] = 1.0
        a_l = cfg.GAIT['ankle_sign_left'] = -1.0
        cfg.GAIT['ankle_sign_right'] = 1.0
        p = gait_planner.GaitPlanner(cfg)
        traj = p.plan_step('left', [0.0] * 4, None, jm=JM)
        h = config.GAIT['hip_swing']
        lean = config.GAIT['lean']
        # flipped hip sign mirrors the whole step
        self.assertAlmostEqual(traj.segments[-1].target[0], s_l * h)
        # each ankle composes the STEP side sign with ITS OWN ankle sign
        self.assertAlmostEqual(traj.segments[1].target[2], s_l * a_l * lean)
        self.assertAlmostEqual(traj.segments[1].target[3], s_l * 1.0 * lean)
        self.assertAlmostEqual(traj.segments[2].target[2],
                               s_l * a_l * (lean + config.GAIT['lift']))
        end = run_trajectory(traj)[-1]
        self.assertAlmostEqual(end[0], s_l * h)

    def test_mirrored_ankles_need_per_side_signs(self):
        """2026-09-23 observation: S2+=toe up, S4+=toe down. Same spatial
        foot tilt therefore needs OPPOSITE electrical offsets - the old
        single shared ankle sign could never do this."""
        import copy
        cfg = sim_config.virtual()
        cfg.GAIT = copy.deepcopy(VC.GAIT)
        cfg.GAIT['ankle_sign_left'] = 1.0
        cfg.GAIT['ankle_sign_right'] = -1.0
        p = gait_planner.GaitPlanner(cfg)
        lean = config.GAIT['lean']
        traj = p.plan_step('left', [0.0] * 4, None, jm=JM)
        ws = traj.segments[1].target
        self.assertAlmostEqual(ws[2], lean)     # left ankle +
        self.assertAlmostEqual(ws[3], -lean)    # right ankle - (mirrored pair)
        # stepping ankle takes the stepping side's sign
        us = traj.segments[2].target
        self.assertAlmostEqual(us[2], lean + config.GAIT['lift'])
        self.assertAlmostEqual(us[3], -(lean))
        # legacy single ankle_sign still works via fallback
        cfg2 = sim_config.virtual()
        cfg2.GAIT = copy.deepcopy(VC.GAIT)
        cfg2.GAIT.pop('ankle_sign_left', None)
        cfg2.GAIT.pop('ankle_sign_right', None)
        cfg2.GAIT['ankle_sign'] = -1.0
        p2 = gait_planner.GaitPlanner(cfg2)
        traj2 = p2.plan_step('left', [0.0] * 4, None, jm=JM)
        self.assertAlmostEqual(traj2.segments[1].target[2], -lean)
        self.assertAlmostEqual(traj2.segments[1].target[3], -lean)


class TestTimeBased(unittest.TestCase):
    def test_11_jittered_update_reaches_same_result(self):
        p = gait_planner.GaitPlanner(VC)
        total = sum(s.duration_ms for s in
                    p.plan_step('left', [0.0] * 4, None).segments)
        # uniform feed
        t1 = p.plan_step('left', [0.0] * 4, None)
        run_trajectory(t1, tick=20)
        # jittered feed with the same total elapsed time
        t2 = p.plan_step('left', [0.0] * 4, None)
        dts = [7, 41, 3, 66, 12, 25, 9, 58]
        i = 0
        elapsed = 0
        done = False
        while not done:
            dt = dts[i % len(dts)]
            _, _, done = t2.update(dt)
            elapsed += dt
            i += 1
        self.assertGreater(elapsed, 0)
        for a, b in zip(t1.pose, t2.pose):
            self.assertAlmostEqual(a, b, places=6)

    def test_11b_partial_time_progresses_proportionally(self):
        traj = trajectory.Trajectory([('s', 400, [8.0, 8.0, 0.0, 0.0])],
                                     [0.0, 0.0, 0.0, 0.0])
        pose, name, done = traj.update(100)   # 25 % of the segment
        self.assertFalse(done)
        # default easing is smoothstep, not linear: 8 * smoothstep(0.25)
        expected = 8.0 * trajectory.smoothstep(0.25)
        self.assertAlmostEqual(pose[0], expected, places=6)
        self.assertAlmostEqual(pose[1], expected, places=6)


class TestLimits(unittest.TestCase):
    def test_10b_out_of_limit_rejected_not_clamped(self):
        import copy
        cfg = sim_config.virtual()
        cfg.GAIT = copy.deepcopy(VC.GAIT)
        cfg.GAIT['hip_swing'] = 40.0   # hip target 90+40=130 > max 115
        p = gait_planner.GaitPlanner(cfg)
        with self.assertRaises(joint_model.LimitViolation):
            p.plan_step('left', [0.0] * 4, None, jm=JM)


if __name__ == '__main__':
    unittest.main()
