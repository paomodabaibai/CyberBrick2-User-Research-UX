"""Acceptance tests 1-4: command mapping (trigger/hold/recenter/conflict/busy)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import input_adapter as IA
from command_mapper import (CommandMapper, STEP_LEFT, STEP_RIGHT, STOP,
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

    def test_2_hold_never_repeats(self):
        values = [(0.9, 0.0)] * 200   # pushed and held for 4 seconds
        self.assertEqual(self.feed(values), [STEP_LEFT])

    def test_3_recenter_rearms(self):
        self.feed([(0.0, 0.0), (0.9, 0.0)] + [(0.9, 0.0)] * 10)
        events = self.feed([(0.0, 0.0)] * 3 + [(0.0, 0.9)])
        self.assertEqual(events, [STEP_RIGHT])

    def test_3b_partial_release_does_not_rearm(self):
        self.feed([(0.9, 0.0)])
        # lever 1 released only into the band edge of lever 2: not both centered
        self.feed([(0.0, 0.6)] * 5)
        events = self.feed([(0.0, 0.9)])
        self.assertEqual(events, [])          # still disarmed
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

    def test_4c_busy_drop_leaves_no_delayed_action(self):
        # left step request arrives while the controller is busy: dropped
        # once, never queued, never repeated per tick
        events = self.feed([(0.9, 0.0)] * 5, busy=True)
        self.assertEqual(events, [DROPPED_BUSY])
        self.assertEqual(self.feed([(0.9, 0.0)] * 10, busy=True), [])
        # lever held through the whole busy window must not fire afterwards
        self.assertEqual(self.feed([(0.9, 0.0)] * 10, busy=False), [])
        self.assertEqual(self.feed([(0.0, 0.0)] * 3), [])
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
