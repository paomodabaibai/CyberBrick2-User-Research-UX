"""otto_oscillator / otto_session tests: the continuous gait experiment.

Proves the Otto-phase relation (ankle lags hip by 90 deg), uniform
amplitude scaling, limit safety over the whole cycle, and that the
session ramps (never snaps) between standing and walking.
"""
import copy
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import joint_model
import otto_oscillator
import sim_config

VC = sim_config.virtual()
JM = joint_model.JointModel(VC)


def cycle_poses(steps=72):
    o = config.OTTO
    out = []
    for i in range(steps):
        phase = 2.0 * math.pi * i / steps
        out.append(otto_oscillator.pose_offsets(
            phase, 1.0, o['hip_amp'], o['ankle_amp'], o['bias']))
    return out


class TestOscillator(unittest.TestCase):
    def test_phase_relation_ankle_lags_hip_by_90(self):
        o = config.OTTO
        # at phase 90 deg the hip is at max stride while the ankle crosses
        # zero (weight transfers at maximum stride - Otto's -90 deg lag)
        p = otto_oscillator.pose_offsets(math.pi / 2, 1.0,
                                         o['hip_amp'], o['ankle_amp'],
                                         o['bias'])
        self.assertAlmostEqual(p[0], o['hip_amp'], places=6)
        self.assertAlmostEqual(p[2], o['bias'], places=6)   # pure bias left
        self.assertAlmostEqual(p[3], -o['bias'], places=6)
        # at phase 0: hips centered, ankles at the negative extreme
        p0 = otto_oscillator.pose_offsets(0.0, 1.0,
                                          o['hip_amp'], o['ankle_amp'],
                                          o['bias'])
        self.assertAlmostEqual(p0[0], 0.0, places=6)
        self.assertAlmostEqual(p0[2], -o['ankle_amp'] + o['bias'], places=6)
        self.assertAlmostEqual(p0[3], -o['ankle_amp'] - o['bias'], places=6)

    def test_hips_identical_scissor(self):
        for pose in cycle_poses(36):
            self.assertAlmostEqual(pose[0], pose[1], places=6)

    def test_full_cycle_within_joint_limits(self):
        jm = joint_model.JointModel(config)
        for pose in cycle_poses(120):
            jm.servo_angles(pose)   # raises LimitViolation if outside

    def test_scale_zero_is_stance_and_never_clipped(self):
        o = config.OTTO
        for i in range(24):
            phase = 2.0 * math.pi * i / 24
            pose = otto_oscillator.pose_offsets(phase, 0.0,
                                                o['hip_amp'],
                                                o['ankle_amp'], o['bias'],
                                                turn=0.7,
                                                turn_split=o['turn_split'])
            self.assertEqual(pose, [0.0, 0.0, 0.0, 0.0])   # flat stance
        # scale 0.5 keeps the waveform shape (proportional, not clipped)
        full = otto_oscillator.pose_offsets(math.pi / 2, 1.0,
                                            o['hip_amp'], o['ankle_amp'],
                                            o['bias'])
        half = otto_oscillator.pose_offsets(math.pi / 2, 0.5,
                                            o['hip_amp'], o['ankle_amp'],
                                            o['bias'])
        for a, b in zip(full, half):
            self.assertAlmostEqual(b, a * 0.5, places=6)


if __name__ == '__main__':
    unittest.main()


class TestTurnAndBackward(unittest.TestCase):
    """v05 full control: turn via asymmetric hip amplitudes, backward via
    the ankle phase sign - both inside limits over the whole cycle."""

    def test_turn_splits_hip_amplitudes(self):
        o = config.OTTO
        straight = otto_oscillator.pose_offsets(
            math.pi / 2, 1.0, o['hip_amp'], o['ankle_amp'], o['bias'])
        left = otto_oscillator.pose_offsets(
            math.pi / 2, 1.0, o['hip_amp'], o['ankle_amp'], o['bias'],
            turn=1.0, turn_split=o['turn_split'])
        self.assertAlmostEqual(straight[0], o['hip_amp'])
        # turn splits DOWNWARD from hip_amp (the scissor hits the -20
        # backward limit on both hips, so amplitudes may only shrink);
        # turn=+1 shrinks the LEFT amplitude. Physical arc direction is
        # empirical - flip the session's turn sign if it curves wrong.
        self.assertAlmostEqual(left[0], o['hip_amp'] - o['turn_split'])
        self.assertAlmostEqual(left[1], o['hip_amp'])
        # mirrored split for the other direction
        right = otto_oscillator.pose_offsets(
            math.pi / 2, 1.0, o['hip_amp'], o['ankle_amp'], o['bias'],
            turn=-1.0, turn_split=o['turn_split'])
        self.assertAlmostEqual(right[0], o['hip_amp'])
        self.assertAlmostEqual(right[1], o['hip_amp'] - o['turn_split'])

    def test_backward_flips_ankle_phase_only(self):
        o = config.OTTO
        fwd = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                           o['ankle_amp'], o['bias'])
        back = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                            o['ankle_amp'], o['bias'],
                                            direction=-1.0)
        # hips identical either way; ankle extremes are mirrored
        self.assertEqual(fwd[0], back[0])
        self.assertEqual(fwd[1], back[1])
        self.assertAlmostEqual(back[2], o['ankle_amp'] + o['bias'])
        self.assertAlmostEqual(back[3], o['ankle_amp'] - o['bias'])

    def test_turn_with_backward_direction_also_symmetric(self):
        o = config.OTTO
        for turn in (-1.0, 1.0):
            left_in = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                                   o['ankle_amp'], o['bias'],
                                                   turn=turn,
                                                   turn_split=o['turn_split'],
                                                   direction=-1.0)
            self.assertAlmostEqual(left_in[2], o['ankle_amp'] + o['bias'],
                                   places=6)
            self.assertAlmostEqual(left_in[3], o['ankle_amp'] - o['bias'],
                                   places=6)

    def test_turn_and_backward_cycle_stays_in_limits(self):
        import joint_model
        o = config.OTTO
        jm = joint_model.JointModel(config)
        for turn in (1.0, -1.0):
            for direction in (1.0, -1.0):
                for i in range(60):
                    phase = 2.0 * math.pi * i / 60
                    pose = otto_oscillator.pose_offsets(
                        phase, 1.0, o['hip_amp'], o['ankle_amp'], o['bias'],
                        turn=turn, turn_split=o['turn_split'],
                        direction=direction)
                    jm.servo_angles(pose)   # raises on limit violation
"""otto_oscillator / otto_session tests: the continuous gait experiment.

Proves the Otto-phase relation (ankle lags hip by 90 deg), uniform
amplitude scaling, limit safety over the whole cycle, and that the
session ramps (never snaps) between standing and walking.
"""
import copy
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import joint_model
import otto_oscillator
import sim_config

VC = sim_config.virtual()
JM = joint_model.JointModel(VC)


def cycle_poses(steps=72):
    o = config.OTTO
    out = []
    for i in range(steps):
        phase = 2.0 * math.pi * i / steps
        out.append(otto_oscillator.pose_offsets(
            phase, 1.0, o['hip_amp'], o['ankle_amp'], o['bias']))
    return out


class TestOscillator(unittest.TestCase):
    def test_phase_relation_ankle_lags_hip_by_90(self):
        o = config.OTTO
        # at phase 90 deg the hip is at max stride while the ankle crosses
        # zero (weight transfers at maximum stride - Otto's -90 deg lag)
        p = otto_oscillator.pose_offsets(math.pi / 2, 1.0,
                                         o['hip_amp'], o['ankle_amp'],
                                         o['bias'])
        self.assertAlmostEqual(p[0], o['hip_amp'], places=6)
        self.assertAlmostEqual(p[2], o['bias'], places=6)   # pure bias left
        self.assertAlmostEqual(p[3], -o['bias'], places=6)
        # at phase 0: hips centered, ankles at the negative extreme
        p0 = otto_oscillator.pose_offsets(0.0, 1.0,
                                          o['hip_amp'], o['ankle_amp'],
                                          o['bias'])
        self.assertAlmostEqual(p0[0], 0.0, places=6)
        self.assertAlmostEqual(p0[2], -o['ankle_amp'] + o['bias'], places=6)
        self.assertAlmostEqual(p0[3], -o['ankle_amp'] - o['bias'], places=6)

    def test_hips_identical_scissor(self):
        for pose in cycle_poses(36):
            self.assertAlmostEqual(pose[0], pose[1], places=6)

    def test_full_cycle_within_joint_limits(self):
        jm = joint_model.JointModel(config)
        for pose in cycle_poses(120):
            jm.servo_angles(pose)   # raises LimitViolation if outside

    def test_scale_zero_is_stance_and_never_clipped(self):
        o = config.OTTO
        for i in range(24):
            phase = 2.0 * math.pi * i / 24
            pose = otto_oscillator.pose_offsets(phase, 0.0,
                                                o['hip_amp'],
                                                o['ankle_amp'], o['bias'],
                                                turn=0.7,
                                                turn_split=o['turn_split'])
            self.assertEqual(pose, [0.0, 0.0, 0.0, 0.0])   # flat stance
        # scale 0.5 keeps the waveform shape (proportional, not clipped)
        full = otto_oscillator.pose_offsets(math.pi / 2, 1.0,
                                            o['hip_amp'], o['ankle_amp'],
                                            o['bias'])
        half = otto_oscillator.pose_offsets(math.pi / 2, 0.5,
                                            o['hip_amp'], o['ankle_amp'],
                                            o['bias'])
        for a, b in zip(full, half):
            self.assertAlmostEqual(b, a * 0.5, places=6)


if __name__ == '__main__':
    unittest.main()


class TestTurnAndBackward(unittest.TestCase):
    """v05 full control: turn via asymmetric hip amplitudes, backward via
    the ankle phase sign - both inside limits over the whole cycle."""

    def test_turn_splits_hip_amplitudes(self):
        o = config.OTTO
        straight = otto_oscillator.pose_offsets(
            math.pi / 2, 1.0, o['hip_amp'], o['ankle_amp'], o['bias'])
        left = otto_oscillator.pose_offsets(
            math.pi / 2, 1.0, o['hip_amp'], o['ankle_amp'], o['bias'],
            turn=1.0, turn_split=o['turn_split'])
        self.assertAlmostEqual(straight[0], o['hip_amp'])
        # turn splits DOWNWARD from hip_amp (the scissor hits the -20
        # backward limit on both hips, so amplitudes may only shrink);
        # turn=+1 shrinks the LEFT amplitude. Physical arc direction is
        # empirical - flip the session's turn sign if it curves wrong.
        self.assertAlmostEqual(left[0], o['hip_amp'] - o['turn_split'])
        self.assertAlmostEqual(left[1], o['hip_amp'])
        # mirrored split for the other direction
        right = otto_oscillator.pose_offsets(
            math.pi / 2, 1.0, o['hip_amp'], o['ankle_amp'], o['bias'],
            turn=-1.0, turn_split=o['turn_split'])
        self.assertAlmostEqual(right[0], o['hip_amp'])
        self.assertAlmostEqual(right[1], o['hip_amp'] - o['turn_split'])

    def test_backward_flips_ankle_phase_only(self):
        o = config.OTTO
        fwd = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                           o['ankle_amp'], o['bias'])
        back = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                            o['ankle_amp'], o['bias'],
                                            direction=-1.0)
        # hips identical either way; ankle extremes are mirrored
        self.assertEqual(fwd[0], back[0])
        self.assertEqual(fwd[1], back[1])
        self.assertAlmostEqual(back[2], o['ankle_amp'] + o['bias'])
        self.assertAlmostEqual(back[3], o['ankle_amp'] - o['bias'])

    def test_turn_with_backward_direction_also_symmetric(self):
        o = config.OTTO
        for turn in (-1.0, 1.0):
            left_in = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                                   o['ankle_amp'], o['bias'],
                                                   turn=turn,
                                                   turn_split=o['turn_split'],
                                                   direction=-1.0)
            self.assertAlmostEqual(left_in[2], o['ankle_amp'] + o['bias'],
                                   places=6)
            self.assertAlmostEqual(left_in[3], o['ankle_amp'] - o['bias'],
                                   places=6)

    def test_turn_and_backward_cycle_stays_in_limits(self):
        import joint_model
        o = config.OTTO
        jm = joint_model.JointModel(config)
        for turn in (1.0, -1.0):
            for direction in (1.0, -1.0):
                for i in range(60):
                    phase = 2.0 * math.pi * i / 60
                    pose = otto_oscillator.pose_offsets(
                        phase, 1.0, o['hip_amp'], o['ankle_amp'], o['bias'],
                        turn=turn, turn_split=o['turn_split'],
                        direction=direction)
                    jm.servo_angles(pose)   # raises on limit violation


    def test_ankle_waveform_identical_for_both_turn_directions(self):
        """Otto turn only swaps hip amplitudes (30/10 vs 10/30); the ankle
        coordination is IDENTICAL. A 180-deg flip added when turn>0 made
        one side's gait the backward ankle waveform - both commands then
        yawed the same way (fixed 2026-09-25, must stay fixed)."""
        o = config.OTTO
        left_in = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                               o['ankle_amp'], o['bias'],
                                               turn=-1.0,
                                               turn_split=o['turn_split'])
        right_in = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                                o['ankle_amp'], o['bias'],
                                                turn=1.0,
                                                turn_split=o['turn_split'])
        # ankles: IDENTICAL waveform for both turn directions (Otto keeps
        # the same -90 deg lag; only hip amplitudes swap)
        self.assertAlmostEqual(left_in[2], right_in[2], places=6)
        self.assertAlmostEqual(left_in[3], right_in[3], places=6)
        # hips: at max stride the amplitudes are exactly swapped 10/30
        p90_l = otto_oscillator.pose_offsets(math.pi / 2, 1.0, o['hip_amp'],
                                             o['ankle_amp'], o['bias'],
                                             turn=-1.0,
                                             turn_split=o['turn_split'])
        p90_r = otto_oscillator.pose_offsets(math.pi / 2, 1.0, o['hip_amp'],
                                             o['ankle_amp'], o['bias'],
                                             turn=1.0,
                                             turn_split=o['turn_split'])
        self.assertAlmostEqual(p90_l[0], p90_r[1], places=6)
        self.assertAlmostEqual(p90_l[1], p90_r[0], places=6)
        # amplitude difference equals the split: 30 vs 10 at hip_amp=30
        self.assertAlmostEqual(abs(p90_l[0] - p90_l[1]),
                               o['turn_split'], places=6)


class TestYawTrimSeparation(unittest.TestCase):
    """Regression: steer_trim fed into the ankle-flip decision and made
    straight walks run backwards. Trim may reshape the amplitude split
    but must NEVER flip the ankle phase."""

    def test_straight_with_trim_keeps_base_ankle_phase(self):
        o = config.OTTO
        base = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                            o['ankle_amp'], o['bias'])
        trimmed = otto_oscillator.pose_offsets(0.0, 1.0, o['hip_amp'],
                                               o['ankle_amp'], o['bias'],
                                               yaw_trim=0.2)
        # phase 0 is the ankle negative extreme in BOTH cases
        self.assertLess(base[2], 0.0)
        self.assertLess(trimmed[2], 0.0)
        self.assertLess(base[3], 0.0)
        self.assertLess(trimmed[3], 0.0)
        # the amplitude split follows the trim: at max stride (phase 90)
        # positive trim shrinks the LEFT hip amplitude
        base90 = otto_oscillator.pose_offsets(math.pi / 2, 1.0, o['hip_amp'],
                                              o['ankle_amp'], o['bias'])
        trim90 = otto_oscillator.pose_offsets(math.pi / 2, 1.0, o['hip_amp'],
                                              o['ankle_amp'], o['bias'],
                                              yaw_trim=0.2)
        self.assertLess(trim90[0], base90[0])
        self.assertAlmostEqual(trim90[1], base90[1], places=6)

    def test_small_trim_cannot_flip_ankle_phase(self):
        o = config.OTTO
        a = otto_oscillator.pose_offsets(math.pi / 2, 1.0, o['hip_amp'],
                                         o['ankle_amp'], o['bias'],
                                         yaw_trim=0.2)
        b = otto_oscillator.pose_offsets(math.pi / 2, 1.0, o['hip_amp'],
                                         o['ankle_amp'], o['bias'],
                                         yaw_trim=-0.2)
        # with zero raw turn the ankle stays on the base 90-deg lag
        # regardless of trim direction (only the bias rides on top)
        self.assertAlmostEqual(a[2] - o['bias'], b[2] - o['bias'], places=6)
        self.assertAlmostEqual(a[2], o['bias'], places=6)
