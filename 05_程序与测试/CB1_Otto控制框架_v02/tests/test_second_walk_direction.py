"""Regression: real second-board entry -> measured ADC -> gait -> GPIO PWM.

All machine/radio/time boundaries are faked. No board is opened or moved.
"""
import types
import unittest
from unittest.mock import patch

import robot_remote as punch
import second_remote_ready as ready
from otto_oscillator import pose_offsets as real_pose


def frame(left=0, right=0):
    raw = [2048] * 6 + [1] * 4
    for key, axis in (('left', left), ('right', right)):
        raw[ready.MAPPING[key]] = round(ready.MAPPING[key + '_center'] + axis * 1700)
    raw[ready.MAPPING['attack']] = ready.MAPPING['attack_center']
    return raw


def exercise(command, seconds=3):
    clock, samples, writes = [0], [], []

    class Pin:
        IN = 0
        def __init__(self, gpio, *args): self.gpio = gpio
        def value(self): return 0

    class PWM:
        def __init__(self, pin, freq): self.gpio = pin.gpio
        def duty_ns(self, ns): writes.append((clock[0], self.gpio, ns))
        def deinit(self): pass

    machine = types.ModuleType('machine')
    machine.Pin, machine.PWM = Pin, PWM
    radio = types.ModuleType('rc_module')
    radio.rc_slave_init = lambda: True
    radio.rc_slave_data = lambda: frame(*command(clock[0]))
    bbl = types.ModuleType('bbl')
    motors = types.ModuleType('bbl.motors')
    class UnusedMotor:
        def __init__(self): raise AssertionError('walk-only test created motor')
    motors.MotorsController = UnusedMotor

    def sleep(ms): clock[0] += ms

    def capture(phase, scale, hip, ankle, bias, **kwargs):
        pose = real_pose(phase, scale, hip, ankle, bias, **kwargs)
        samples.append(dict(time=clock[0], phase=phase, scale=scale,
                            hip=hip, ankle=ankle, bias=bias, pose=pose,
                            **kwargs))
        return pose

    with patch.dict('sys.modules', {'machine': machine, 'rc_module': radio,
                                   'bbl': bbl, 'bbl.motors': motors}), \
         patch.object(punch, '_clock', lambda: clock[0]), \
         patch.object(punch, '_sleep', sleep), \
         patch.object(punch, 'pose_offsets', capture), \
         patch('builtins.print'):
        ready.run(seconds, mode='walk')
    return samples, writes


def steady_command(left, right):
    return lambda t: (0, 0) if t < 600 else (left, right)


class SecondWalkDirectionTests(unittest.TestCase):
    def test_measured_adc_endpoints_keep_direction_and_stride_side_separate(self):
        # Signed turn remains the existing policy API; stride_turn is the
        # amplitude allocation supplied to the oscillator, not a yaw promise.
        for left,right,direction,stride in ((1,0,1,-1),(-1,0,-1,-1),
                                            (0,1,1,1),(0,-1,-1,1),
                                            (1,1,1,0),(-1,-1,-1,0)):
            with self.subTest(left=left,right=right):
                p=punch.RemotePolicy(ready.MAPPING)
                p.update(frame(),0);p.update(frame(),500)
                raw=frame()
                for key,value in (('left',left),('right',right)):
                    if value: raw[ready.MAPPING[key]]=4095 if value>0 else 0
                p.update(raw,600)
                self.assertEqual(p.walk_direction,direction)
                self.assertEqual(p.stride_turn,stride)

    def test_pull_back_uses_backward_ankle_phase_in_actual_loop(self):
        for side in ('left', 'right'):
            with self.subTest(side=side):
                args = (-1, 0) if side == 'left' else (0, -1)
                samples, _ = exercise(steady_command(*args))
                moving = [s for s in samples if s['time'] >= 1200]
                self.assertTrue(moving)
                self.assertTrue(all(s['direction'] == -1 for s in moving),
                                'single-stick reverse was lost before pose_offsets')

    def test_same_stick_reverse_keeps_stride_side_and_reverses_ankles(self):
        for side in ('left', 'right'):
            args = (1, 0) if side == 'left' else (0, 1)
            forward, _ = exercise(steady_command(*args))
            backward, _ = exercise(steady_command(*[-v for v in args]))
            for f, b in zip(forward, backward):
                if f['time'] < 1200: continue
                self.assertAlmostEqual(f['pose'][0], b['pose'][0])
                self.assertAlmostEqual(f['pose'][1], b['pose'][1])
                self.assertAlmostEqual(f['pose'][2] + b['pose'][2], 2 * f['bias'])
                self.assertAlmostEqual(f['pose'][3] + b['pose'][3], -2 * f['bias'])

    def test_left_right_commands_are_mirrored_for_each_travel_direction(self):
        for direction in (-1, 1):
            left, _ = exercise(steady_command(direction, 0))
            right, _ = exercise(steady_command(0, direction))
            for l, r in zip(left, right):
                if l['time'] < 1200: continue
                self.assertAlmostEqual(l['pose'][0], r['pose'][1])
                self.assertAlmostEqual(l['pose'][1], r['pose'][0])
                self.assertEqual(l['pose'][2:], r['pose'][2:])

    def test_saturated_single_turn_has_reference_three_to_one_stride_ratio(self):
        samples, _ = exercise(steady_command(1, 0))
        s = next(s for s in samples if s['time'] >= 1200)
        # Normalize to a full turn independently of unequal ADC endpoint spans.
        large, small = s['hip'], s['hip'] - s['turn_split']
        self.assertAlmostEqual(large / small, 3.0)
        self.assertEqual(large, 30, 'user requested the original palm stride')

    def test_direction_change_decelerates_to_zero_before_phase_switch(self):
        def commands(t):
            if t < 600: return 0, 0
            return (1, 0) if t < 1700 else (-1, 0)
        samples, _ = exercise(commands, 4)
        changed = [i for i in range(1, len(samples))
                   if samples[i]['direction'] != samples[i-1]['direction']]
        self.assertTrue(changed, 'backward direction never reached oscillator')
        for i in changed:
            self.assertEqual(samples[i]['scale'], 0)
        for before, after in zip(samples, samples[1:]):
            self.assertLessEqual(max(abs(a-b) for a,b in zip(before['pose'],after['pose'])), 5)

    def test_reverse_unequal_sticks_keeps_larger_stride_on_stronger_stick(self):
        forward, _ = exercise(steady_command(1, .5))
        backward, _ = exercise(steady_command(-1, -.5))
        for f,b in zip(forward, backward):
            if f['time'] < 1200: continue
            self.assertAlmostEqual(f['pose'][0], b['pose'][0])
            self.assertAlmostEqual(f['pose'][1], b['pose'][1])

    def test_all_eight_directions_produce_bounded_pwm_on_correct_channels(self):
        for l,r in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
            with self.subTest(left=l,right=r):
                samples,writes=exercise(steady_command(l,r))
                self.assertEqual({gpio for _,gpio,_ in writes},{3,1,2,0})
                for s in samples:
                    self.assertTrue(all(60 <= 90+v <= 120 for v in s['pose'][:2]))
                    self.assertTrue(all(65 <= 90+v <= 115 for v in s['pose'][2:]))
                for _,gpio,ns in writes:
                    lo,hi=(1166000,1833000) if gpio in (3,1) else (1222000,1778000)
                    self.assertTrue(lo <= ns <= hi)

    def test_release_returns_to_stance_after_ramp(self):
        samples,_=exercise(lambda t: (-1,0) if 600 <= t < 1800 else (0,0))
        self.assertTrue(all(max(abs(v) for v in s['pose']) < 1e-9
                            for s in samples if s['time'] >= 2400))

    def test_cancelled_reverse_does_not_latch_an_old_direction(self):
        def commands(t):
            if t < 600: return 0,0
            if 1700 <= t < 1900: return -1,0
            return 1,0
        samples,_=exercise(commands,4)
        self.assertTrue(all(s['direction']==1 for s in samples))
        self.assertTrue(all(s['scale']==1 for s in samples if s['time']>=2400))

    def test_release_during_reverse_finishes_at_stance(self):
        def commands(t):
            if 600 <= t < 1700: return 0,1
            if 1700 <= t < 1900: return 0,-1
            return 0,0
        samples,_=exercise(commands,4)
        self.assertTrue(all(s['scale']==0 for s in samples if s['time']>=2400))


if __name__ == '__main__': unittest.main()
