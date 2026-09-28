import unittest
from diagnose_arm import ArmProbe
from input_adapter import from_manual


class TestArmProbe(unittest.TestCase):
    def test_continuous_hold_and_release_predict_enable(self):
        p = ArmProbe()
        p.update(from_manual(0, 0, True), 0)
        p.update(from_manual(0, 0, True), 1000)
        p.update(from_manual(0, 0, False), 1100)
        self.assertEqual(p.would_enable, 1)

    def test_short_taps_never_predict_enable(self):
        p = ArmProbe()
        for t in range(0, 2000, 200):
            p.update(from_manual(0, 0, True), t)
            p.update(from_manual(0, 0, False), t + 100)
        self.assertEqual(p.would_enable, 0)
        self.assertEqual(p.resets['short_release'], 10)

    def test_link_loss_resets_hold(self):
        p = ArmProbe()
        p.update(from_manual(0, 0, True), 0)
        p.update(from_manual(0, 0, True, connected=False), 900)
        p.update(from_manual(0, 0, False), 1200)
        self.assertEqual(p.resets['no_frame'], 1)
        self.assertEqual(p.would_enable, 0)

    def test_either_lever_outside_center_resets_hold(self):
        for left, right in ((0.21, 0), (0, -0.21)):
            p = ArmProbe()
            p.update(from_manual(0, 0, True), 0)
            p.update(from_manual(left, right, True), 500)
            p.update(from_manual(0, 0, False), 1500)
            self.assertEqual(p.resets['not_centered'], 1)
            self.assertEqual(p.would_enable, 0)

    def test_hold_wraps_clock(self):
        p = ArmProbe()
        p.update(from_manual(0, 0, True), (1 << 30) - 500)
        p.update(from_manual(0, 0, True), 500)
        p.update(from_manual(0, 0, False), 520)
        self.assertEqual(p.would_enable, 1)
