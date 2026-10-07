"""Acceptance tests 1-4 + v03: command mapping.

v03 semantics (2026-09-24): backward pulls request backward steps; a held
lever re-triggers once the busy window ends (continuous stepping); conflict
covers any mix of two engaged levers; recenter is required only after
enable/recover/link-loss (the controller disarms), not after each step.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import input_adapter as IA
from command_mapper import (CommandMapper, STEP_LEFT, STEP_RIGHT,
                            STEP_BACK_LEFT, STEP_BACK_RIGHT, STOP,
                            LINK_LOST, REJECTED_CONFLICT, DROPPED_BUSY)


def inp(l, r, stop=False, connected=True, t=0):
    return IA.from_manual(l, r, stop, connected, t)


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.m = CommandMapper(config)

    def feed(self, values, busy=False):
        events = []
        for i, v in enumerate(values):
            l, r = v[0], v[1]
            stop = v[2] if len(v) > 2 else False
            events += self.m.update(inp(l, r, stop, t=i * 20), busy=busy)
        return events

    def test_1_single_push_single_request(self):
        values = [(0.0, 0.0)] + [(0.9, 0.0)] * 30
        self.assertEqual(self.feed(values), [STEP_LEFT])

    def test_2_hold_fires_once_until_busy_cycle(self):
        # held without any busy feedback: still exactly one request
        values = [(0.9, 0.0)] * 200
        self.assertEqual(self.feed(values), [STEP_LEFT])

    def test_2b_hold_repeats_after_busy_ends(self):
        # v03 continuous stepping: the lever held through a busy window
        # fires again the moment busy ends (no recenter needed)
        self.feed([(0.0, 0.0), (0.9, 0.0)])                 # fires STEP_LEFT
        self.assertEqual(self.feed([(0.9, 0.0)] * 5, busy=True),
                         [DROPPED_BUSY])                    # held in flight
        self.assertEqual(self.feed([(0.9, 0.0)]), [STEP_LEFT])  # re-fires

    def test_3_recenter_rearms(self):
        self.feed([(0.0, 0.0), (0.9, 0.0)] + [(0.9, 0.0)] * 10)
        events = self.feed([(0.0, 0.0)] * 3 + [(0.0, 0.9)])
        self.assertEqual(events, [STEP_RIGHT])

    def test_3b_partial_release_does_not_rearm(self):
        self.feed([(0.9, 0.0)])
        # lever 1 released only into the band edge of lever 2: not both centered
        self.feed([(0.0, 0.6)] * 5)
        events = self.feed([(0.0, 0.9)])
        self.assertEqual(events, [])          # still one-shot per push
        self.feed([(0.0, 0.0)] * 3)
        self.assertEqual(self.feed([(0.0, 0.9)]), [STEP_RIGHT])

    def test_4a_conflict_rejects_and_leaves_no_delayed_action(self):
        events = self.feed([(0.9, 0.9)] * 30)
        self.assertEqual(events, [REJECTED_CONFLICT])
        self.assertEqual(self.feed([(0.0, 0.0)] * 5), [])   # nothing pending
        self.assertEqual(self.feed([(0.0, 0.9)]), [STEP_RIGHT])

    def test_4b_conflict_not_repeated_while_held(self):
        self.feed([(0.9, 0.9)])
        self.assertEqual(self.feed([(0.9, 0.9)] * 20), [])

    def test_4c_busy_drop_then_rearm_only_via_center_or_busy_cycle(self):
        # left step request arrives while the controller is busy: dropped
        # once, never queued, never repeated per tick
        events = self.feed([(0.9, 0.0)] * 5, busy=True)
        self.assertEqual(events, [DROPPED_BUSY])
        self.assertEqual(self.feed([(0.9, 0.0)] * 10, busy=True), [])
        # v03: busy window ended with the lever still held -> re-fires
        # (continuous stepping); releasing to center re-arms one-shot again
        self.assertEqual(self.feed([(0.9, 0.0)] * 3), [STEP_LEFT])
        self.feed([(0.0, 0.0)] * 3)
        self.assertEqual(self.feed([(0.9, 0.0)]), [STEP_LEFT])

    def test_4d_conflict_covers_forward_backward_mix(self):
        # left forward + right backward: two engaged levers, still a conflict
        events = self.feed([(0.9, -0.9)] * 5)
        self.assertEqual(events, [REJECTED_CONFLICT])

    def test_5_backward_pulls_request_backward_steps(self):
        self.assertEqual(self.feed([(0.0, 0.0), (-0.9, 0.0), (-0.9, 0.0)]),
                         [STEP_BACK_LEFT])
        self.feed([(0.0, 0.0)] * 3)
        self.assertEqual(self.feed([(0.0, -0.9)]), [STEP_BACK_RIGHT])

    def test_5b_backward_held_repeats_after_busy(self):
        self.feed([(0.0, 0.0), (-0.9, 0.0)])
        self.assertEqual(self.feed([(-0.9, 0.0)] * 4, busy=True),
                         [DROPPED_BUSY])
        self.assertEqual(self.feed([(-0.9, 0.0)]), [STEP_BACK_LEFT])

    def test_disarmed_blocks_until_centered(self):
        # what the controller does after enable()/recover(): mapper.ready=False
        self.m.ready = False
        self.assertEqual(self.feed([(0.9, 0.0)] * 5), [])
        self.assertEqual(self.feed([(0.0, 0.0)] * 2), [])   # recenter...
        self.assertEqual(self.feed([(0.9, 0.0)]), [STEP_LEFT])

    def test_8a_stop_priority(self):
        events = self.feed([(0.9, 0.9, True)])
        self.assertEqual(events, [STOP])

    def test_8b_link_lost(self):
        values = [(0.0, 0.0)] * 3
        events = []
        for i, (l, r) in enumerate(values):
            events += self.m.update(inp(l, r, connected=False, t=i * 20))
        self.assertEqual(events, [LINK_LOST])


if __name__ == '__main__':
    unittest.main()
