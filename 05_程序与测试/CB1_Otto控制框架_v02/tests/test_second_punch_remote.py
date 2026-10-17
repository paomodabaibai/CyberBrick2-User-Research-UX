import unittest
import types
from unittest.mock import patch
import second_punch_remote as punch


def frame(left=1797, right=1959, attack=1825, stop=1):
    raw = [1959, 0, 1825, 1797, 0, 0, 1, 1, 1, 1]
    raw[3], raw[0], raw[2], raw[9] = left, right, attack, stop
    return raw


class PunchPolicyTests(unittest.TestCase):
    def armed(self):
        p = punch.RemotePolicy()
        p.update(frame(), 0)
        p.update(frame(), 500)
        self.assertTrue(p.armed)
        return p

    def test_start_with_stick_deflected_cannot_arm(self):
        p = punch.RemotePolicy()
        for t in (0, 500, 1000):
            self.assertEqual(p.update(frame(attack=4000), t), (0, 0, 0))
        self.assertFalse(p.armed)

    def test_neutral_must_be_continuous(self):
        p = punch.RemotePolicy()
        p.update(frame(), 0)
        p.update(frame(left=4000), 499)
        p.update(frame(), 500)
        p.update(frame(), 999)
        self.assertFalse(p.armed)
        p.update(frame(), 1000)
        self.assertTrue(p.armed)

    def test_attack_continues_while_held_and_stops_on_release(self):
        p = self.armed()
        self.assertEqual(p.update(frame(attack=4000), 600)[2], 1024)
        self.assertEqual(p.update(frame(attack=4000), 2100)[2], 1024)
        self.assertEqual(p.update(frame(attack=4000), 6000)[2], 1024)
        self.assertEqual(p.update(frame(attack=4000), 15000)[2], 1024)
        p.update(frame(), 15010)
        self.assertEqual(p.update(frame(), 15011)[2], 0)
        self.assertEqual(p.update(frame(attack=4000), 15020)[2], 1024)

    def test_attack_both_directions_are_forward_only(self):
        p = self.armed()
        self.assertEqual(p.update(frame(attack=0), 600)[2], 1800)

    def test_attack_two_speeds_follow_configured_up_direction(self):
        p = punch.RemotePolicy({'slow_speed': 800, 'fast_speed': 1800,
                                'attack_up_is_high': True})
        p.update(frame(), 0)
        p.update(frame(), 500)
        self.assertEqual(p.update(frame(attack=4000), 600)[2], 800)
        self.assertEqual(p.update(frame(attack=4000), 6000)[2], 800)
        self.assertEqual(p.update(frame(), 6010)[2], 0)
        self.assertEqual(p.update(frame(attack=0), 6020)[2], 1800)
        p2 = punch.RemotePolicy({'slow_speed': 800, 'fast_speed': 1800,
                                 'attack_up_is_high': False})
        p2.update(frame(), 0)
        p2.update(frame(), 500)
        self.assertEqual(p2.update(frame(attack=0), 600)[2], 800)
        self.assertEqual(p2.update(frame(), 610)[2], 0)
        self.assertEqual(p2.update(frame(attack=4000), 620)[2], 1800)

    def test_attack_can_cross_partial_zone_before_full_push(self):
        p = self.armed()
        self.assertEqual(p.update(frame(attack=2300), 600)[2], 0)
        self.assertEqual(p.update(frame(attack=2500), 620)[2], 0)
        self.assertEqual(p.update(frame(attack=4000), 640)[2], 1024)

    def test_release_stops_and_partial_return_does_not_rearm(self):
        p = self.armed()
        p.update(frame(attack=4000), 600)
        self.assertEqual(p.update(frame(attack=2300), 620)[2], 0)
        self.assertEqual(p.update(frame(attack=4000), 640)[2], 0)
        p.update(frame(), 660)
        self.assertEqual(p.update(frame(attack=4000), 680)[2], 1024)

    def test_loss_requires_neutral_before_restart(self):
        p = self.armed()
        p.update(frame(left=4000, right=4000, attack=4000), 600)
        self.assertEqual(p.update(None, 620), (0, 0, 0))
        self.assertEqual(p.update(frame(left=4000, right=4000, attack=4000), 640), (0, 0, 0))
        self.assertFalse(p.armed)

    def test_k4_hold_dances_and_suppresses_walk_and_punch(self):
        p = self.armed()
        self.assertEqual(p.update(frame(left=4000, right=4000, attack=4000, stop=0), 600), (0, 0, 0))
        self.assertTrue(p.armed)
        self.assertTrue(p.dance_active)
        self.assertEqual(p.update(frame(left=4000, right=4000, attack=4000, stop=0), 620), (0, 0, 0))
        self.assertTrue(p.dance_active)
        self.assertEqual(p.update(frame(stop=1), 640), (0, 0, 0))
        self.assertFalse(p.dance_active)

    def test_dance_offsets_are_bounded_smooth_and_vary_over_time(self):
        dance = punch.DanceMotion(start_ms=100, start_pose=(0, 0, 0, 0))
        poses = [dance.pose(t) for t in range(100, 2100, 20)]
        self.assertEqual(poses[0], (0, 0, 0, 0))
        self.assertGreater(len(set(tuple(round(v, 2) for v in p) for p in poses)), 20)
        self.assertTrue(all(abs(p[i]) <= 25
                            for p in poses for i in range(4)))
        self.assertGreaterEqual(max(abs(p[i]) for p in poses for i in (0, 1)), 16)
        self.assertGreaterEqual(max(abs(p[i]) for p in poses for i in (2, 3)), 12)
        self.assertTrue(all(max(abs(a-b) for a, b in zip(left, right)) <= 3.5
                            for left, right in zip(poses, poses[1:])))

    def test_dance_alternates_large_targets_and_holds_each_pose(self):
        dance = punch.DanceMotion(100)
        for step in range(8):
            first = dance.pose(100 + step * 450 + 310)
            held = dance.pose(100 + step * 450 + 430)
            self.assertEqual(first, held)
            for i, limit in enumerate((25, 25, 25, 25)):
                self.assertGreaterEqual(abs(first[i]) + 1e-9, limit * 0.8)
            if step:
                self.assertTrue(all(a*b < 0 for a, b in zip(previous, first)))
            previous = first

    def test_invalid_frame_fails_closed(self):
        for raw in ([], [1] * 9, frame(attack=float('nan')), frame(left=5000), frame(stop=2)):
            p = self.armed()
            self.assertEqual(p.update(raw, 600), (0, 0, 0))
            self.assertFalse(p.armed)

    def test_walk_and_attack_same_frame(self):
        p = self.armed()
        drive, turn, speed = p.update(frame(left=3597, right=3759, attack=4000), 600)
        self.assertEqual((drive, turn, speed), (1, 0, 1024))

    def test_single_stick_turn_and_reverse(self):
        p = self.armed()
        drive, turn, _ = p.update(frame(left=3597), 600)
        self.assertEqual((drive, turn), (0, -1))
        self.assertLess(p.update(frame(left=0, right=0), 620)[0], 0)

    def test_invalid_parameters_do_not_construct_hardware(self):
        for cfg in ({'slow_speed': -1}, {'fast_speed': 2049},
                    {'fast_speed': 1024}, {'attack_up_is_high': 1},
                    {'left': 9}, {'span': 0}):
            with self.assertRaises(ValueError):
                punch.RemotePolicy(cfg)


class PunchLoopTests(unittest.TestCase):
    def exercise(self, mode='both', failure=False, loss=False, native_pwm=False,
                 unbounded=False, dance=False):
        clock = [0]
        events = []
        pwms = []

        class Pin:
            IN = 0
            def __init__(self, gpio, *args):
                self.gpio = gpio
            def value(self):
                return 0

        class PWM:
            def __init__(self, pin, freq):
                self.pin = pin
                self.off = False
                self.writes = []
                pwms.append(self)
            def duty_ns(self, ns):
                events.append(('leg', clock[0]))
                self.writes.append((clock[0], ns))
                if failure and clock[0] >= 600:
                    raise RuntimeError('injected PWM failure')
            def deinit(self):
                self.off = True

        class Motors:
            def stop(self, n):
                events.append(('stop', clock[0]))
            def set_speed(self, n, speed):
                events.append(('motor', clock[0]))
            def motors_period_cb(self):
                events.append(('service', clock[0]))

        if native_pwm:
            delattr(Motors, 'motors_period_cb')

        def read():
            if loss and clock[0] >= 700:
                return None
            if dance:
                if 600 <= clock[0] < 900:
                    return frame(left=3597, right=3759, attack=4000, stop=0)
                if 560 <= clock[0] < 600:
                    return frame(attack=4000)
                return frame()
            if clock[0] >= 600:
                return frame(left=3597, right=3759, attack=4000)
            return frame()

        machine = types.ModuleType('machine')
        machine.Pin, machine.PWM = Pin, PWM
        rc = types.ModuleType('rc_module')
        rc.rc_slave_init = lambda: True
        rc.rc_slave_data = read
        bbl = types.ModuleType('bbl')
        motors = types.ModuleType('bbl.motors')
        motors.MotorsController = Motors
        def sleep(ms):
            clock[0] += ms
            if unbounded and clock[0] >= 2000:
                raise KeyboardInterrupt()
        with patch.dict('sys.modules', {'machine': machine, 'rc_module': rc,
                                       'bbl': bbl, 'bbl.motors': motors}), \
             patch.object(punch, '_clock', lambda: clock[0]), \
             patch.object(punch, '_sleep', sleep), \
             patch('builtins.print'):
            if failure:
                with self.assertRaises(RuntimeError):
                    punch.run(1, mode)
            elif unbounded:
                with self.assertRaises(KeyboardInterrupt):
                    punch.run(None, mode)
            else:
                punch.run(1, mode)
        self.assertTrue(all(p.off for p in pwms))
        if mode != 'walk':
            self.assertEqual(events[-1][0], 'stop')
        return events, pwms

    def test_concurrent_loop_services_motor_and_releases_outputs(self):
        events, pwms = self.exercise()
        self.assertEqual(len(pwms), 4)
        self.assertIn(('motor', 600), events)
        service = [t for kind, t in events if kind == 'service']
        self.assertEqual(max(b-a for a, b in zip(service, service[1:])), 1)

    def test_pwm_exception_stops_motor(self):
        self.exercise(failure=True)

    def test_radio_loss_stops_motor_and_does_not_recreate_pwm(self):
        events, pwms = self.exercise(loss=True)
        self.assertIn(('stop', 700), events)
        self.assertEqual(len(pwms), 4)
        self.assertFalse(any(kind == 'leg' and t >= 700 for kind, t in events))

    def test_attack_only_never_creates_leg_pwm(self):
        _, pwms = self.exercise(mode='attack')
        self.assertEqual(pwms, [])

    def test_walk_only_does_not_construct_motor(self):
        events, _ = self.exercise(mode='walk')
        self.assertFalse(any(kind in ('motor', 'stop', 'service') for kind, _ in events))

    def test_native_easypwm_driver_needs_no_callback(self):
        events, pwms = self.exercise(native_pwm=True)
        self.assertEqual(len(pwms), 4)
        self.assertIn(('motor', 600), events)
        self.assertFalse(any(kind == 'service' for kind, _ in events))

    def test_unbounded_session_keeps_walking_and_punching_until_interrupted(self):
        events, pwms = self.exercise(unbounded=True)
        self.assertEqual(len(pwms), 4)
        self.assertTrue(any(kind == 'leg' and t >= 1500 for kind, t in events))
        self.assertIn(('motor', 600), events)
        self.assertEqual(events[-1][0], 'stop')

    def test_held_k4_stops_motor_and_moves_legs_within_limits(self):
        events, pwms = self.exercise(dance=True)
        self.assertIn(('motor', 560), events)
        self.assertIn(('stop', 600), events)
        self.assertFalse(any(kind == 'motor' and 600 <= t < 900 for kind, t in events))
        dance_writes = [(t, ns) for pwm in pwms for t, ns in pwm.writes
                        if 600 <= t < 900]
        self.assertGreater(len(dance_writes), 30)
        self.assertGreater(len(set(ns for _, ns in dance_writes)), 8)
        self.assertTrue(all(1222000 <= ns <= 1778000 for _, ns in dance_writes))


if __name__ == '__main__':
    unittest.main()
