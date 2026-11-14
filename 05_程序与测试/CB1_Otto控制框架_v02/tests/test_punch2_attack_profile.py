import unittest
import robot_remote as core
from test_shared_robot_remote import exercise, sample


class Punch2AttackTests(unittest.TestCase):
    def test_combined_entry_preserves_walking_and_controls_m1(self):
        import punch2_remote_ready as profile
        import punch2_walk_ready as walk
        def no_button(t):
            raw = sample(t)
            if raw is not None:
                raw[9] = 1
            return raw
        both, _ = exercise('punch', profile=profile, script=no_button)
        legs, _ = exercise('punch', profile=walk, script=no_button)
        leg = lambda ev: [e for e in ev if e[0] == 'pulse']
        self.assertEqual(leg(both), leg(legs))
        motor = [e for e in both if e[0] == 'motor']
        self.assertEqual(set(e[2] for e in motor), {1})
        self.assertEqual(set(e[3] for e in motor), {0, 1024, 1800})
        self.assertEqual(motor[-1][3], 0)

    def test_k1_hold_dances_release_restores_remote(self):
        import punch2_remote_ready as profile
        self.assertEqual(profile.MAPPING['dance'], 6)
        self.assertTrue(profile.MAPPING['dance_enabled'])
        c = profile.MAPPING
        raw = [2000] * 6 + [1] * 4
        for key in ('left', 'right', 'attack'):
            raw[c[key]] = c[key + '_center']
        p = core.RemotePolicy(c)
        p.update(raw, 0); p.update(raw, 500)
        raw[6] = 0
        self.assertEqual(p.update(raw, 520), (0, 0, 0))
        self.assertTrue(p.dance_active)
        raw[6] = 1
        p.update(raw, 540)
        self.assertFalse(p.dance_active)
        raw[c['attack']] = 4095
        self.assertEqual(p.update(raw, 560)[2], 1024)
        events, _ = exercise('punch', profile=profile)
        self.assertIn(('motor', 1200, 1, 0), events)
        poses = [e[3] for e in events if e[0] == 'pulse' and 1200 <= e[1] < 1800]
        self.assertTrue(any(abs(ns - 1500000) > 100000 for ns in poses))

    def test_hold_over_five_seconds_release_and_link_loss(self):
        import punch2_remote_ready as profile
        c = profile.MAPPING
        p = core.RemotePolicy(c)
        raw = [2000] * 6 + [1] * 4
        for key in ('left', 'right', 'attack'):
            raw[c[key]] = c[key + '_center']
        p.update(raw, 0)
        p.update(raw, 500)
        for up, expected in ((True, 1024), (False, 1800)):
            raw[c['attack']] = 4095 if up == c['attack_up_is_high'] else 0
            for t in range(520, 10520, 20):
                self.assertEqual(p.update(raw, t)[2], expected)
            raw[c['attack']] = c['attack_center']
            self.assertEqual(p.update(raw, 10520)[2], 0)
        self.assertEqual(p.update(None, 10540)[2], 0)
        self.assertFalse(p.armed)


if __name__ == '__main__':
    unittest.main()
