"""bench_v02 tests: import-safe, name-based channel selection, honest
refusals - the bench must never move on import, never guess a servo by
position, and never dress an incomplete output up as a full gait."""
import copy
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import sim_config
import bench_v02


def raw_frame(left=None, right=None, k4=1):
    f = [2048] * 6 + [1] * 4
    if left is not None:
        f[config.REMOTE['left_channel']] = int(
            config.REMOTE['left_center'] + left * config.REMOTE['left_span'])
    if right is not None:
        f[config.REMOTE['right_channel']] = int(
            config.REMOTE['right_center'] + right * config.REMOTE['right_span'])
    f[6 + config.REMOTE['stop_button']] = k4
    return f


class FakeLink:
    def __init__(self, frame=None):
        self.frame = frame

    def read(self):
        return self.frame


def hw_copy(uncalibrated=None):
    """Deep copy of the real config; optionally degrade one joint so the
    incomplete-output paths stay testable now that the real robot IS
    calibrated."""
    import copy as _copy

    class Cfg:
        pass

    cfg = Cfg()
    for k, v in config.__dict__.items():
        if k.isupper():
            setattr(cfg, k, _copy.deepcopy(v))
    if uncalibrated:
        cfg.JOINTS[uncalibrated]['calibrated'] = False
    return cfg


def small_gait_cfg():
    """Virtual profile with 20 ms phases so scripted steps run in ~0.1 s."""
    cfg = sim_config.virtual()
    cfg.GAIT = copy.deepcopy(cfg.GAIT)
    for k in list(cfg.GAIT):
        if k.endswith('_ms'):
            cfg.GAIT[k] = 20
    return cfg


def run_capture(fn, *a, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = fn(*a, **kw)
    return result, buf.getvalue()


class TestDiagAndMonitor(unittest.TestCase):
    def test_import_and_diag_never_move_anything(self):
        self.assertIsNone(bench_v02.__dict__.get('driver'))
        blockers, out = run_capture(bench_v02.diag)
        self.assertEqual(blockers, [])                # real config calibrated
        self.assertIn('left_ankle', out)
        self.assertIn('walking: all four', out)
        self.assertEqual(config.DRIVER, 'sim')        # config untouched
        # the BLOCKED wording stays reachable on a degraded copy
        _, out2 = run_capture(bench_v02.diag, hw_copy(uncalibrated='left_ankle'))
        self.assertIn('BLOCKED', out2)
        self.assertNotIn('walking: all four', out2)

    def test_monitor_never_creates_pwm(self):
        out = run_capture(bench_v02.monitor,
                          link=FakeLink(raw_frame(left=0.0, right=0.0)),
                          ticks=3, tick_ms=0)[1]
        self.assertIn('PWM impossible', out)
        self.assertIn('L=+0.00', out)
        self.assertIn('link=ok', out)
        out = run_capture(bench_v02.monitor, link=FakeLink(None),
                          ticks=1, tick_ms=0)[1]
        self.assertIn('link=NONE', out)


class TestJointEntry(unittest.TestCase):
    def test_disabled_joint_refused(self):
        # Real config has no disabled channel since the S2 swap, so the
        # refusal is exercised on a disabled variant profile.
        cfg = sim_config.virtual()
        cfg.JOINTS['right_ankle']['enabled'] = False
        with self.assertRaisesRegex(RuntimeError, 'disabled'):
            bench_v02.joint('right_ankle', 5, cfg=cfg, confirmed=True,
                            allow_sim=True)

    def test_unknown_joint_and_range_refused(self):
        with self.assertRaises(ValueError):
            bench_v02.joint('front_left', 5)
        with self.assertRaisesRegex(RuntimeError, '±10'):
            bench_v02.joint('right_hip', 15, confirmed=True)

    def test_unconfirmed_and_sim_driver_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'confirmed'):
            bench_v02.joint('right_hip', 5)
        with self.assertRaisesRegex(RuntimeError, 'simulation driver'):
            bench_v02.joint('right_hip', 5, confirmed=True)  # allow_sim=False

    def test_joint_moves_by_name_and_releases(self):
        drv, out = run_capture(bench_v02.joint, 'right_hip', 5.0,
                               confirmed=True, allow_sim=True, hold_ms=0)
        poses = [p for _, p in drv.frames]
        self.assertEqual(poses[0][1], 5.0)            # right_hip only
        self.assertEqual(poses[1], [0.0, 0.0, 0.0, 0.0])
        self.assertTrue(drv.released)
        self.assertIn('S3/GPIO1', out)                # named port mapping
        self.assertIn('PWM off', out)


class TestDemo3AndGait(unittest.TestCase):
    def test_demo3_refuses_when_output_is_complete(self):
        with self.assertRaisesRegex(RuntimeError, 'use gait'):
            bench_v02.demo3(cfg=small_gait_cfg(), allow_sim=True,
                            confirmed=True, total_ms=200)

    def test_demo3_marks_incomplete_never_claims_gait(self):
        out = run_capture(bench_v02.demo3, cfg=hw_copy('left_ankle'),
                          allow_sim=True, confirmed=True,
                          total_ms=400)[1]
        self.assertIn('INCOMPLETE OUTPUT', out)
        self.assertIn('not a gait', out)
        self.assertIn('PWM off', out)
        self.assertNotIn('success', out.lower())

    def test_gait_refused_while_incomplete(self):
        with self.assertRaisesRegex(RuntimeError, 'gait refused'):
            bench_v02.gait(cfg=hw_copy('left_ankle'), allow_sim=True,
                           confirmed=True, total_ms=200)

    def test_gait_runs_one_strict_step_when_complete(self):
        out = run_capture(bench_v02.gait, cfg=small_gait_cfg(),
                          allow_sim=True, confirmed=True,
                          total_ms=400)[1]
        self.assertIn('strict enable ok', out)
        self.assertIn('final state=ready', out)
        self.assertIn('PWM off', out)


if __name__ == '__main__':
    unittest.main()
