"""New D2 receiver must not change the existing D1 robot."""
import unittest
import palm_remote_ready as old
import palm2_remote_ready as new
from drivers import palm_pwm
import robot_remote as core

class TestPalm2Profile(unittest.TestCase):
    def test_new_wiring_and_old_profile_are_separate(self):
        self.assertEqual(old.PALM['gpio'], 21)
        self.assertEqual(new.PALM['gpio'], 20)
        self.assertEqual([new.MAPPING[k] for k in ('left','right','attack','dance')],[2,5,3,6])
        self.assertEqual([old.MAPPING[k] for k in ('left','right','attack','dance')],[3,0,2,9])
        self.assertEqual(new.PALM['channel'],3)
        self.assertEqual(new.PALM['center'],new.MAPPING['attack_center'])
        self.assertEqual(new.PALM['delta_us'],600)
        self.assertEqual(old.PALM['delta_us'],600)
        self.assertIsNot(new.PALM, old.PALM)

    def test_high_drive_both_directions_release_and_loss(self):
        from attack_control import AttackController
        controller = AttackController(new.PALM)
        raw = [2000]*6+[1]*4
        raw[3] = new.PALM['center']
        self.assertEqual(controller.update(raw,0),1500)
        raw[3] = 4095
        self.assertEqual(controller.update(raw,20),2100)
        raw[3] = 0
        self.assertEqual(controller.update(raw,40),1500)
        self.assertEqual(controller.update(raw,200),900)
        raw[3] = new.PALM['center']
        self.assertEqual(controller.update(raw,220),1500)
        self.assertIsNone(controller.update(None,240))

    def test_X_axes_ignored_and_K1_is_the_only_dance_button(self):
        raw=[2000]*6+[1]*4
        for key in ('left','right','attack'):
            raw[new.MAPPING[key]]=new.MAPPING[key+'_center']
        policy=core.RemotePolicy(new.MAPPING)
        policy.update(raw,0)
        policy.update(raw,500)
        self.assertTrue(policy.armed)
        raw[1]=0;raw[4]=4095;raw[9]=0
        self.assertEqual(policy.update(raw,520),(0.0,0.0,0))
        self.assertFalse(policy.dance_active)
        raw[6]=0
        policy.update(raw,540)
        self.assertTrue(policy.dance_active)
        raw[6]=1
        policy.update(raw,560)
        self.assertFalse(policy.dance_active)

    def test_each_Y_axis_retains_forward_and_reverse(self):
        for key in ('left','right'):
            for sign in (-1,1):
                raw=[2000]*6+[1]*4
                for k in ('left','right','attack'):
                    raw[new.MAPPING[k]]=new.MAPPING[k+'_center']
                p=core.RemotePolicy(new.MAPPING)
                p.update(raw,0);p.update(raw,500)
                raw[new.MAPPING[key]]+=sign*1200
                p.update(raw,520)
                self.assertEqual(p.walk_direction,sign)
                self.assertNotEqual(p.stride_turn,0)

    def test_lazy_pwm_uses_only_d2(self):
        events = []
        class PWM:
            def __init__(self, pin, hz): events.append(('init', pin, hz))
            def duty_ns(self, ns): events.append(('pulse', ns))
            def duty(self, value): events.append(('duty', value))
            def deinit(self): events.append(('off',))
        saved = palm_pwm._machine
        palm_pwm._machine = type('Machine', (), {'PWM': PWM})
        try:
            driver = palm_pwm.PalmPwmDriver(new.PALM)
            self.assertEqual(events, [])
            driver.write_us(1700)
            driver.release()
            self.assertEqual(events, [('init',20,50), ('pulse',1700000),
                                     ('pulse',1500000), ('duty',0), ('off',)])
        finally:
            palm_pwm._machine = saved

if __name__ == '__main__':
    unittest.main()
