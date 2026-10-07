"""AttackController tests: ch2 axis -> palm pulse commands, pure logic.

Behavior contract (D1 execution plan 2026-09-26):
- axis = clamp((raw - center) / span * direction, -1, 1); speed command,
  never an angle
- startup: not armed; arms after the first valid frame with the stick
  inside the EXIT deadband (a stick held off-center at boot never spins)
- hysteresis: |axis| past ENTER starts; back inside EXIT stops
- engaged + centered -> neutral; one side neutral+delta, other neutral-delta
  (fixed low speed, magnitude-independent)
- reversing across center dwells at neutral >= reverse_dwell_ms first;
  releasing during the dwell cancels the reversal
- disabled / None frame / malformed frame -> None (driver releases)
- after a link loss, re-arming requires the stick to return to center
- an unchanged stick value is a valid continuous command (never treated
  as a stale link)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from attack_control import AttackController

A = config.ATTACK
NEUTRAL = A['neutral_us']
FWD = A['neutral_us'] + A['delta_us']    # direction=+1: positive axis
REV = A['neutral_us'] - A['delta_us']


def frame(ch2):
    f = [2048] * 6 + [1] * 4
    f[A['channel']] = ch2
    return f


def ch2_for(axis):
    """Raw ch2 value that normalizes to `axis` (direction=+1)."""
    return int(A['center'] + axis * A['span'])


class FakeClock:
    def __init__(self):
        self.t = 0

    def __call__(self):
        return self.t

    def advance(self, ms):
        self.t += ms


def make_ctrl(**overrides):
    cfg = dict(A)
    cfg['enabled'] = True            # unless a test overrides it to False
    cfg.update(overrides)
    clock = FakeClock()
    return AttackController(cfg, now_ms=clock), clock


class TestAttackController(unittest.TestCase):
    def test_disabled_always_none(self):
        c, _ = make_ctrl(enabled=False)
        self.assertIsNone(c.update(frame(ch2_for(0.0)), 0))
        self.assertIsNone(c.update(frame(ch2_for(0.9)), 100))
        self.assertIsNone(c.update(None, 200))

    def test_boot_with_stick_deflected_never_spins(self):
        c, _ = make_ctrl()
        self.assertIsNone(c.update(frame(ch2_for(0.9)), 0))
        self.assertIsNone(c.update(frame(ch2_for(0.9)), 1000))
        # recentering arms the controller and outputs the stop pulse
        self.assertEqual(c.update(frame(ch2_for(0.0)), 1100), NEUTRAL)
        # armed now: an engaged stick immediately commands
        self.assertEqual(c.update(frame(ch2_for(0.9)), 1200), FWD)

    def test_engage_disengage_hysteresis(self):
        c, _ = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)            # arm at center
        self.assertEqual(c.update(frame(ch2_for(0.9)), 100), FWD)
        # between EXIT (0.10) and ENTER (0.15) while engaged: STILL running
        # (hysteresis stops only when back inside the EXIT deadband)
        mid = ch2_for((A['enter_deadband'] + A['exit_deadband']) / 2)
        self.assertEqual(c.update(frame(mid), 200), FWD)
        # fully centered (inside EXIT): stopped at neutral, pulse keeps
        # flowing so the continuous servo cannot creep
        self.assertEqual(c.update(frame(ch2_for(0.0)), 300), NEUTRAL)

    def test_fixed_speed_both_directions(self):
        c, _ = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)
        self.assertEqual(c.update(frame(ch2_for(0.95)), 100), FWD)
        c.update(frame(ch2_for(0.0)), 200)          # back to neutral
        self.assertEqual(c.update(frame(ch2_for(0.0)), 300), NEUTRAL)
        self.assertEqual(c.update(frame(ch2_for(-0.95)), 400), REV)

    def test_partial_deflection_same_fixed_speed(self):
        c, _ = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)
        self.assertEqual(c.update(frame(ch2_for(0.5)), 100), FWD)

    def test_reverse_crossing_dwells_at_neutral(self):
        c, clock = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)
        self.assertEqual(c.update(frame(ch2_for(0.9)), 100), FWD)
        # slam straight across to the other side
        self.assertEqual(c.update(frame(ch2_for(-0.9)), 200), NEUTRAL)
        self.assertEqual(c.update(frame(ch2_for(-0.9)), 200 + 100), NEUTRAL)
        # after the dwell the reverse pulse appears
        self.assertEqual(c.update(frame(ch2_for(-0.9)),
                                  200 + A['reverse_dwell_ms']), REV)

    def test_release_during_reverse_dwell_cancels(self):
        c, clock = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)
        c.update(frame(ch2_for(0.9)), 100)
        self.assertEqual(c.update(frame(ch2_for(-0.9)), 200), NEUTRAL)
        # user releases mid-dwell: back to center, stays neutral, no REV
        self.assertEqual(c.update(frame(ch2_for(0.0)), 300), NEUTRAL)
        self.assertIsNone(c.update(None, 400))
        c2, _ = make_ctrl()
        c2.update(frame(ch2_for(0.0)), 0)
        self.assertEqual(c2.update(frame(ch2_for(0.9)), 100), FWD)

    def test_link_loss_disarms_and_blocks_until_recenter(self):
        c, _ = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)
        self.assertEqual(c.update(frame(ch2_for(0.9)), 100), FWD)
        self.assertIsNone(c.update(None, 200))              # link lost
        self.assertIsNone(c.update(frame(ch2_for(0.9)), 300))  # deflected
        self.assertIsNone(c.update(frame(ch2_for(0.9)), 5000))  # still no
        self.assertEqual(c.update(frame(ch2_for(0.0)), 5100), NEUTRAL)
        self.assertEqual(c.update(frame(ch2_for(0.9)), 5200), FWD)

    def test_malformed_frame_is_link_loss(self):
        c, _ = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)
        self.assertIsNone(c.update([1, 2, 3], 100))
        # invalid button byte: not a valid frame
        bad = frame(ch2_for(0.0))
        bad[9] = 5
        self.assertIsNone(c.update(bad, 200))

    def test_unchanged_stick_value_is_a_valid_command(self):
        c, _ = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)
        v = frame(ch2_for(0.9))
        self.assertEqual(c.update(v, 100), FWD)
        self.assertEqual(c.update(v, 200), FWD)   # same value, still FWD
        self.assertEqual(c.update(v, 30000), FWD) # and 30s later

    def test_deadband_boundaries(self):
        c, _ = make_ctrl()
        c.update(frame(ch2_for(0.0)), 0)
        # just past the ENTER deadband: engages ("越过" = strictly past)
        self.assertEqual(c.update(frame(ch2_for(A['enter_deadband'] + 0.01)),
                                  100), FWD)
        self.assertEqual(c.update(frame(ch2_for(0.0)), 200), NEUTRAL)
        # exactly at EXIT deadband from engaged: still stopped (hysteresis
        # engages only past ENTER); between EXIT and ENTER stays NEUTRAL
        self.assertEqual(c.update(frame(ch2_for(0.12)), 300), NEUTRAL)


if __name__ == '__main__':
    unittest.main()
