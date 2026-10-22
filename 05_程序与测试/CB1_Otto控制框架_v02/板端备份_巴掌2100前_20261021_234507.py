"""First/palm receiver profile. Import creates no PWM or wireless activity.

Only measured stick centres and the attack device differ from the punch.
K4, legs, reverse, limits, arming and the power-on loop are shared.
"""
import robot_remote

ATTACK_KIND = 'palm'
MAPPING = dict(left=3, right=0, attack=2, dance=9,
               left_center=1797, right_center=1959, attack_center=1860,
               attack_up_is_high=True)

PALM = dict(enabled=True, actuator='continuous',
            channel=2, center=1860, span=1800, direction=1,
            gpio=21, freq_hz=50, neutral_us=1500, delta_us=300,
            enter_deadband=0.15, exit_deadband=0.10, reverse_dwell_ms=150)


def run(seconds=30, mode='both', trace=False):
    return robot_remote.run(seconds=seconds, mode=mode, mapping=MAPPING,
                            trace=trace, attack_kind=ATTACK_KIND, palm_cfg=PALM)
