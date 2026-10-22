"""walk_session tests: time-boxed remote walking on scripted frames.

Proves the documented bench-night flow end to end: strict enable from a live
frame, lever-triggered ALTERNATING steps, and guaranteed release at the end -
without any real remote or real clock dependence beyond the 20 ms loop.
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import sim_config
import walk_session


def raw_frame(left=0.0, right=0.0, k4=1):
    f = [2048] * 6 + [1] * 4
    f[config.REMOTE['left_channel']] = int(
        config.REMOTE['left_center'] + left * config.REMOTE['left_span'])
    f[config.REMOTE['right_channel']] = int(
        config.REMOTE['right_center'] + right * config.REMOTE['right_span'])
    f[6 + config.REMOTE['stop_button']] = k4
    return f


class SeqLink:
    """Pops scripted frames; repeats the last one when the script runs out."""

    def __init__(self, frames):
        self.frames = list(frames)
        self.last = frames[0]

    def read(self):
        if self.frames:
            self.last = self.frames.pop(0)
        return self.last


def small_gait_cfg():
    """Virtual profile with 20 ms phases and a scripted left-then-right
    walk: 10 center frames, a left push, 30 center, a right push, center."""
    cfg = sim_config.virtual()
    cfg.GAIT = copy.deepcopy(cfg.GAIT)
    for k in list(cfg.GAIT):
        if k.endswith('_ms'):
            cfg.GAIT[k] = 20
    frames = ([raw_frame(0, 0)] * 10 +
              [raw_frame(left=0.8)] + [raw_frame(0, 0)] * 30 +
              [raw_frame(right=0.8)] + [raw_frame(0, 0)] * 200)
    return cfg, SeqLink(frames)


class TestWalkSession(unittest.TestCase):
    def test_enable_step_alternate_release_end_to_end(self):
        cfg, link = small_gait_cfg()
        logs = []
        sess = walk_session.run(1.5, cfg=cfg, link=link, log=logs.append)
        text = '\n'.join(logs)
        self.assertIn('step start left', text)
        self.assertIn('step done left', text)
        self.assertIn('step start right', text)      # alternation works
        self.assertIn('PWM off', text)
        self.assertIn('time up, state=ready', text)
        self.assertTrue(sess.ctrl.driver.released)   # guaranteed cleanup
        self.assertEqual(sess.ctrl.state, 'disabled')

    def test_k4_stop_then_release(self):
        cfg, _ = small_gait_cfg()
        link = SeqLink([raw_frame(0, 0)] * 5 +
                       [raw_frame(left=0.8)] + [raw_frame(0, 0)] * 3 +
                       [raw_frame(0, 0, k4=0)] + [raw_frame(0, 0)] * 200)
        logs = []
        sess = walk_session.run(1.5, cfg=cfg, link=link, log=logs.append)
        text = '\n'.join(logs)
        self.assertIn('step start left', text)
        self.assertIn('K4', text)                    # stop observed
        self.assertIn('state=stopped', text.lower())
        self.assertTrue(sess.ctrl.driver.released)

    def test_enable_refused_without_frame_never_moves(self):
        # No frames at all: enable must refuse before anything moves.
        class DeadLink:
            def read(self):
                return None

        import main_v02
        logs = []
        sess = main_v02.start(sim_config.virtual())
        self.assertRaises(RuntimeError, walk_session.run, 0.5,
                          cfg=sim_config.virtual(), link=DeadLink(),
                          session=sess, log=logs.append)
        self.assertEqual(sess.ctrl.state, 'disabled')
        self.assertEqual(sess.ctrl.driver.frames, [])   # never moved


if __name__ == '__main__':
    unittest.main()
