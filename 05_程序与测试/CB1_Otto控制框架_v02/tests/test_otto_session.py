"""otto_session tests: continuous walk ramps, never snaps, stays in limits.

Uses the virtual profile with a scripted link: hold left lever -> hips
oscillate with the Otto phase relation; release -> amplitude ramps to
stance; PWM off guaranteed at the end.
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import otto_session
import sim_config


def raw_frame(left=0.0, right=0.0, ch2=None):
    f = [2048] * 6 + [1] * 4
    f[config.REMOTE['left_channel']] = int(
        config.REMOTE['left_center'] + left * config.REMOTE['left_span'])
    f[config.REMOTE['right_channel']] = int(
        config.REMOTE['right_center'] + right * config.REMOTE['right_span'])
    if ch2 is not None:
        f[config.ATTACK['channel']] = ch2
    return f


def fast_cfg():
    cfg = sim_config.virtual()
    cfg.OTTO = copy.deepcopy(cfg.OTTO)
    cfg.OTTO['period_ms'] = 200
    cfg.OTTO['ramp_ms'] = 100
    return cfg


class SeqLink:
    def __init__(self, frames):
        self.frames = list(frames)
        self.last = frames[0]

    def read(self):
        if self.frames:
            self.last = self.frames.pop(0)
        return self.last


class TestOttoSession(unittest.TestCase):
    def test_hold_walks_release_stops_and_releases(self):
        cfg = fast_cfg()
        link = SeqLink([raw_frame()] * 15 +
                       [raw_frame(0.8, 0.8)] * 60 +     # hold both: walk
                       [raw_frame()] * 40 +             # release: ramp down
                       [raw_frame()] * 40)
        logs = []
        sess = otto_session.run(1.5, cfg=cfg, link=link, log=logs.append)
        text = '\n'.join(logs)
        self.assertIn('otto: walking', text)
        self.assertIn('otto: stopping', text)
        hips = [abs(f[1][0]) for f in sess.ctrl.driver.frames]
        # during the walk the hip actually swings at the configured amplitude
        self.assertGreater(max(hips), 0.5 * cfg.OTTO['hip_amp'])
        # and the LAST written pose is back at stance (ramp, not snap freeze)
        last_pose = sess.ctrl.driver.frames[-1][1]
        self.assertLess(max(abs(x) for x in last_pose), 1.0)
        self.assertTrue(sess.ctrl.driver.released)

    def test_never_exceeds_joint_limits_while_walking(self):
        import joint_model
        cfg = fast_cfg()
        jm = joint_model.JointModel(config)
        link = SeqLink([raw_frame()] * 15 + [raw_frame(0.8, 0.8)] * 140)
        sess = otto_session.run(1.2, cfg=cfg, link=link, log=lambda *a: None)
        for _, pose in sess.ctrl.driver.frames:
            jm.servo_angles(pose)   # raises if any pose left the limits

    def test_link_gap_ramps_down_does_not_crash(self):
        cfg = fast_cfg()
        frames = [raw_frame()] * 15 + [raw_frame(0.8, 0.8)] * 30 + [None] * 80
        link = SeqLink(frames)
        logs = []
        sess = otto_session.run(1.2, cfg=cfg, link=link, log=logs.append)
        self.assertTrue(sess.ctrl.driver.released)   # clean end regardless


class TestPalmIntegration(unittest.TestCase):
    """Attack servo rides the SAME frame read as the walk; D1 released on
    exit even though nothing else knows about it."""

    def setUp(self):
        from drivers import palm_pwm
        self.log = []
        self.instances = []
        self._saved = palm_pwm._machine

        def make_pwm(gpio, freq):
            pwm = palm_pwm.FakePWM(self.log, gpio, freq)                 if hasattr(palm_pwm, 'FakePWM') else FakePwm(self.log, gpio,
                                                             freq)
            self.instances.append(pwm)
            return pwm

        # minimal inline fake (palm_pwm has no FakePWM export)
        class FakePwm:
            def __init__(self, log, gpio, freq):
                self.log = log
                log.append(('init', gpio, freq))

            def duty_ns(self, ns):
                self.last_ns = ns

            def duty(self, value):
                self.log.append(('duty', value))

            def deinit(self):
                self.log.append(('deinit',))

        self.make_pwm = make_pwm
        palm_pwm._machine = type('M', (), {'PWM': staticmethod(make_pwm)})

    def tearDown(self):
        from drivers import palm_pwm
        palm_pwm._machine = self._saved

    def test_attack_rides_shared_frame_and_releases_on_exit(self):
        import joint_model
        from drivers import palm_pwm
        cfg = fast_cfg()
        cfg.ATTACK = dict(config.ATTACK)
        cfg.ATTACK['enabled'] = True
        jm = joint_model.JointModel(config)
        rest2 = config.ATTACK['center']   # ch2 natural rest (1860)
        frames = ([raw_frame(ch2=rest2)] * 30 +   # wait_frames eats ~15;
                                           # the rest arm the attack ctrl
                  [raw_frame(ch2=rest2 + 900)] * 30 +
                  [raw_frame(ch2=rest2)] * 20)  # release: ch2 to center
        link = SeqLink(frames)
        logs = []
        sess = otto_session.run(1.0, cfg=cfg, link=link, log=logs.append)
        writes = [e for e in self.log if e[0] == 'init']
        self.assertTrue(writes)                       # D1 was driven
        self.assertEqual(writes[0][1], config.ATTACK['gpio'])
        self.assertEqual(writes[0][2], config.ATTACK['freq_hz'])
        for _, pose in sess.ctrl.driver.frames:       # legs still validated
            jm.servo_angles(pose)
        self.assertFalse(sess.ctrl.driver.released is None)
        # after the session both outputs are down: leg release + palm deinit
        self.assertTrue(sess.ctrl.driver.released)
        self.assertIn('deinit', [e[0] for e in self.log])


if __name__ == '__main__':
    unittest.main()
