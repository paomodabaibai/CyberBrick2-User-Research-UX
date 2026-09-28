"""Board-session tests: remote link -> BoardSession entries -> state.

Two layers are covered:
- loop_once(frame, now): pure logic, frame and clock injected (no link).
- poll()/enable()/recover()/run(): the REAL documented operator flow - the
  session reads the FakeLink itself and gates on that fresh read, so the
  tests exercise exactly what an operator types, never bypassing the entry.

Runs on the virtual profile with the sim driver; no machine, no hardware.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import sim_config
import states
import timeutil
import main_v02


def raw_frame(left=None, right=None, k4=1):
    """Build a valid 10-value rc frame using measured remote mapping."""
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
    """Stands in for RcLink: read() returns whatever the test staged.

    Setting frame=None simulates a dead link (rc_slave_data returning
    nothing usable). read_count proves the session actually read the link
    at entry time instead of trusting saved input.
    """

    def __init__(self, frame=None, fail_init=False):
        self.frame = frame
        self.read_count = 0
        self.fail_init = fail_init

    def read(self):
        self.read_count += 1
        return self.frame


class FakeClock:
    """Replaces timeutil.now_ms with a deterministic 20 ms ticker."""

    def __init__(self, t0=1000):
        self.t = t0

    def __call__(self):
        self.t += 20
        return self.t & ((1 << 30) - 1)


def make_session(link=None):
    cfg = sim_config.virtual()
    return main_v02.start(cfg, link)


class PauseLink(FakeLink):
    """Raises KeyboardInterrupt after N reads, like Ctrl-C in run()."""

    def __init__(self, after_reads=1):
        FakeLink.__init__(self, raw_frame())
        self.after = after_reads

    def read(self):
        if self.read_count >= self.after:
            raise KeyboardInterrupt
        return FakeLink.read(self)


class TestNoAutoEnable(unittest.TestCase):
    def test_valid_frames_never_enable(self):
        s = make_session()
        for i in range(20):
            st = s.loop_once(raw_frame(left=0.9), i * 20)
        self.assertEqual(st, states.DISABLED)
        self.assertEqual(s.ctrl.driver.frames, [])

    def test_no_link_stays_disabled(self):
        s = make_session()
        self.assertEqual(s.loop_once(None, 20), states.DISABLED)
        self.assertEqual(s.loop_once([1] * 5, 40), states.DISABLED)

    def test_polling_good_frames_never_enables(self):
        clock = FakeClock()
        saved = timeutil.now_ms
        timeutil.now_ms = clock
        try:
            s = make_session(FakeLink(raw_frame()))
            for _ in range(10):
                self.assertEqual(s.poll(), states.DISABLED)
        finally:
            timeutil.now_ms = saved


class TestOperatorEntries(unittest.TestCase):
    """enable/recover/poll gate on a FRESH link read, not saved input."""

    def setUp(self):
        self._saved_now = timeutil.now_ms
        timeutil.now_ms = FakeClock()

    def tearDown(self):
        timeutil.now_ms = self._saved_now

    def test_poll_requires_link(self):
        s = make_session()
        with self.assertRaisesRegex(RuntimeError, 'no remote link'):
            s.poll()

    def test_enable_reads_the_link_itself(self):
        s = make_session(FakeLink(raw_frame()))
        before = s.link.read_count
        s.enable()
        self.assertEqual(s.ctrl.state, states.READY)
        self.assertGreater(s.link.read_count, before)

    def test_enable_rejected_without_fresh_frame_even_if_input_was_saved(self):
        s = make_session(FakeLink(raw_frame()))
        s.poll()                                   # saves a connected input
        s.link.frame = None                        # link dies afterwards
        with self.assertRaisesRegex(RuntimeError, 'no valid frame'):
            s.enable()
        self.assertEqual(s.ctrl.state, states.DISABLED)
        self.assertFalse(s.last_inp.connected)

    def test_enable_rejected_while_k4_held_right_now(self):
        s = make_session(FakeLink(raw_frame(k4=0)))
        with self.assertRaisesRegex(RuntimeError, 'K4'):
            s.enable()
        self.assertEqual(s.ctrl.state, states.DISABLED)
        s.link.frame = raw_frame()                 # K4 released
        s.enable()
        self.assertEqual(s.ctrl.state, states.READY)

    def test_enable_feeds_live_frame_recenter_gate_applies(self):
        s = make_session(FakeLink(raw_frame(left=0.9)))
        s.enable()                                 # enabled with lever held
        self.assertEqual(s.ctrl.state, states.READY)
        for _ in range(5):                         # held lever never fires
            self.assertEqual(s.poll(), states.READY)
        s.link.frame = raw_frame()                 # recenter observed
        s.poll()
        s.link.frame = raw_frame(left=0.9)
        self.assertEqual(s.poll(), states.WALKING)

    def test_enable_debug_same_live_gate(self):
        s = make_session(FakeLink(None))
        with self.assertRaises(RuntimeError):
            s.enable_debug()
        s.link.frame = raw_frame()
        self.assertEqual(s.enable_debug(), states.READY)
        self.assertTrue(s.ctrl.debug_incomplete is not None)

    def test_recover_same_fresh_gate(self):
        s = make_session(FakeLink(raw_frame()))
        s.enable()
        s.link.frame = raw_frame(k4=0)             # stop via poll
        self.assertEqual(s.poll(), states.STOPPED)
        s.link.frame = None                        # link dead: no recover
        with self.assertRaisesRegex(RuntimeError, 'no valid frame'):
            s.recover()
        s.link.frame = raw_frame(k4=0)             # K4 still held: no recover
        with self.assertRaisesRegex(RuntimeError, 'K4'):
            s.recover()
        s.link.frame = raw_frame()                 # live and K4 free
        self.assertEqual(s.recover(), states.READY)
        self.assertTrue(s.ctrl.debug_incomplete is None)


class TestPauseSemantics(unittest.TestCase):
    """Ctrl-C pause: cancel active gait, honest protection limits, explicit
    cleanup - and resume() is ONLY the loop, never enable/recover."""

    def setUp(self):
        self._saved_now = timeutil.now_ms
        timeutil.now_ms = FakeClock()

    def tearDown(self):
        timeutil.now_ms = self._saved_now

    def test_pause_cancels_active_gait(self):
        s = make_session(FakeLink(raw_frame()))
        s.enable()
        s.poll()                                   # recenter observed
        s.link.frame = raw_frame(left=0.9)
        self.assertEqual(s.poll(), states.WALKING)
        writes = len(s.ctrl.driver.frames)
        main_v02.pause(s)
        self.assertEqual(s.ctrl.state, states.STOPPED)
        self.assertIsNone(s.ctrl.trajectory)
        # a resumed loop keeps polling, but the cancelled step never continues
        for _ in range(5):
            self.assertEqual(s.poll(), states.STOPPED)
        self.assertEqual(len(s.ctrl.driver.frames), writes)

    def test_pause_time_never_counts_into_next_step(self):
        s = make_session(FakeLink(raw_frame()))
        s.enable()
        s.poll()
        s.link.frame = raw_frame(left=0.9)
        s.poll()                                   # WALKING
        main_v02.pause(s)                          # STOPPED, pose held
        timeutil.now_ms.t += 10_000                # paused for 10 s
        self.assertEqual(s.recover(), states.READY)
        s.link.frame = raw_frame()
        s.poll()                                   # recenter observed
        s.link.frame = raw_frame(left=0.9)
        self.assertEqual(s.poll(), states.WALKING)
        # the new step starts from elapsed 0 despite the 10 s gap
        self.assertEqual(s.ctrl.trajectory.elapsed_in_seg, 0.0)
        self.assertNotEqual(s.ctrl.state, states.FAULT)
        s.link.frame = raw_frame()
        for _ in range(200):
            if s.poll() == states.READY:
                break
        else:
            self.fail('fresh step after pause never finished')

    def test_pause_on_non_walking_state_is_harmless(self):
        s = make_session(FakeLink(raw_frame()))
        s.enable()
        main_v02.pause(s)
        self.assertEqual(s.ctrl.state, states.READY)

    def test_resume_is_not_recover_no_motion_after_resume(self):
        s = make_session(FakeLink(raw_frame()))
        s.enable()
        s.poll()
        s.link.frame = raw_frame(left=0.9)
        s.poll()
        main_v02.pause(s)
        main_v02.SESSION = s
        s.link = FakeLink(raw_frame(left=0.9))     # lever still pushed
        # make the second resumed tick raise KeyboardInterrupt like Ctrl-C
        class StopAfterOne(FakeLink):
            def read(self):
                if self.read_count >= 1:
                    raise KeyboardInterrupt
                return FakeLink.read(self)
        s.link = StopAfterOne(raw_frame(left=0.9))
        s2 = main_v02.resume()
        self.assertIs(s2, s)
        self.assertEqual(s.ctrl.state, states.STOPPED)   # NOT walking again
        self.assertFalse(s.ctrl.driver.released)
        main_v02.SESSION = None

    def test_unexpected_exception_releases_output_then_reraises(self):
        class BoomLink:
            def __init__(self):
                self.n = 0

            def read(self):
                self.n += 1
                if self.n > 2:
                    raise RuntimeError('sensor exploded')
                return raw_frame()

        s = make_session(BoomLink())
        with self.assertRaisesRegex(RuntimeError, 'sensor exploded'):
            main_v02.run(session=s)
        self.assertTrue(s.ctrl.driver.released)
        self.assertEqual(s.ctrl.state, states.DISABLED)

    def test_start_keyword_link_matches_readme_example(self):
        s = main_v02.start(link=FakeLink(raw_frame()))
        self.assertIsNotNone(s.link)
        self.assertEqual(s.ctrl.state, states.DISABLED)
        self.assertEqual(s.ctrl.driver.frames, [])   # import/start never moves


class TestDocumentedFlowEndToEnd(unittest.TestCase):
    """The exact README flow, executed through the public entries only."""

    def setUp(self):
        self._saved_now = timeutil.now_ms
        timeutil.now_ms = FakeClock()

    def tearDown(self):
        timeutil.now_ms = self._saved_now

    def walk_to_done(self, side):
        """Poll until the started step finishes (5 segments, ~1.8 s)."""
        s = self.s
        s.link.frame = raw_frame(left=0.9 if side == 'left' else None,
                                 right=None if side == 'left' else 0.9)
        self.assertEqual(s.poll(), states.WALKING)
        s.link.frame = raw_frame()
        for _ in range(200):
            if s.poll() == states.READY:
                return
        self.fail('step never finished')

    def test_init_read_enable_run_stop_recover_exit(self):
        # 1. init: session + link, nothing moving
        self.s = make_session(FakeLink(raw_frame()))
        s = self.s
        for _ in range(3):
            self.assertEqual(s.poll(), states.DISABLED)
        self.assertEqual(s.ctrl.driver.frames, [])
        # 3. explicit enable
        self.assertEqual(s.enable(), states.READY)
        # 4. run: recenter observed -> alternate steps work
        s.poll()
        self.walk_to_done('left')
        self.walk_to_done('right')
        # 5. stop (K4) and recover through the live gate
        s.link.frame = raw_frame(k4=0)
        self.assertEqual(s.poll(), states.STOPPED)
        s.link.frame = raw_frame()
        self.assertEqual(s.recover(), states.READY)
        s.poll()                                   # recenter observed
        self.walk_to_done('left')
        # 6. exit: PWM off, disabled
        self.assertEqual(s.release(), states.DISABLED)
        self.assertTrue(s.ctrl.driver.released)

    def test_run_pauses_on_ctrl_c_session_survives(self):
        s = main_v02.run(sim_config.virtual(), link=PauseLink(after_reads=2))
        self.assertIs(s, main_v02.SESSION)
        self.assertEqual(s.ctrl.state, states.DISABLED)  # paused, not enabled
        self.assertFalse(s.ctrl.driver.released)         # torque held
        # resume() re-enters the loop with the same session
        s.link = PauseLink(after_reads=1)                # interrupt immediately
        s2 = main_v02.resume()
        self.assertIs(s2, s)
        # explicit exit releases output
        self.assertEqual(s.release(), states.DISABLED)
        self.assertTrue(s.ctrl.driver.released)

    def test_resume_without_session_raises(self):
        saved = main_v02.SESSION
        main_v02.SESSION = None
        try:
            with self.assertRaisesRegex(RuntimeError, 'no paused session'):
                main_v02.resume()
        finally:
            main_v02.SESSION = saved


if __name__ == '__main__':
    unittest.main()
