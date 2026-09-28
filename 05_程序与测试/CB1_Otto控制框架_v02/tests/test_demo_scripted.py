"""demo_scripted tests: the no-radio fallback drives the real gait stack.

Proves that scripted frames through ScriptedLink produce the same strict
enable -> alternating steps -> guaranteed release flow as real remote
frames, using the 20 ms-phase virtual profile so the test stays fast.
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import demo_scripted
import sim_config


def fast_cfg():
    cfg = sim_config.virtual()
    cfg.GAIT = copy.deepcopy(cfg.GAIT)
    for k in list(cfg.GAIT):
        if k.endswith('_ms'):
            cfg.GAIT[k] = 20
    return cfg


class TestDemoScripted(unittest.TestCase):
    def test_two_pairs_alternate_and_release(self):
        cfg = fast_cfg()
        logs = []
        # 20ms gait phases: step ~100 ms; push 60 ms, recenter 200 ms
        sess = demo_scripted.run(2, cfg=cfg, log=logs.append,
                                 cycle=(0.06, 0.2))
        text = '\n'.join(logs)
        self.assertIn('step start left', text)
        self.assertIn('step done left', text)
        self.assertIn('step start right', text)
        self.assertIn('step done right', text)
        # two LEFT steps total => 2 pairs actually ran
        self.assertEqual(text.count('step start left'), 2)
        self.assertIn('PWM off', text)
        self.assertIn('done, state=', text)
        self.assertTrue(sess.ctrl.driver.released)
        self.assertEqual(sess.ctrl.state, 'disabled')

    def test_frames_are_valid_and_centered_before_push(self):
        link = demo_scripted.build_link(1)
        f0 = link.read()
        self.assertEqual(len(f0), 10)
        # initial frame: both levers at measured resting centers, K4 released
        self.assertEqual(f0[0], demo_scripted._CENTER_L)
        self.assertEqual(f0[3], demo_scripted._CENTER_R)
        self.assertEqual(f0[9], 1)
        # push frames exceed the step threshold after normalization
        import config
        import input_adapter
        pushed = demo_scripted._L_FRAME
        u = input_adapter.from_rc(pushed, 0, config)
        self.assertGreater(u.left, config.STEP_THRESHOLD)
        self.assertLess(abs(u.right), config.RECENTER_BAND)
        self.assertFalse(u.stop_pressed)

    def test_release_happens_even_on_crash(self):
        # A link that explodes mid-session must still release the PWM.
        class BombLink:
            def __init__(self):
                self.n = 0

            def read(self):
                self.n += 1
                if self.n > 3:
                    raise RuntimeError('boom')
                return demo_scripted._CENTER

        logs = []
        self.assertRaises(RuntimeError, demo_scripted.run, 1,
                          cfg=fast_cfg(), log=logs.append, link=BombLink())
        self.assertIn('PWM off', '\n'.join(logs))


if __name__ == '__main__':
    unittest.main()
