"""Second robot entry and measured stick mapping; import is inert.

Left ch3, right ch0, punch ch2 and K4 dance ch9 were verified one at a time.
Pass seconds=None for continuous control from second_punch_main.py (board main.py).
"""
import robot_remote

ATTACK_KIND = 'punch'
MAPPING = dict(left=3, right=0, attack=2, dance=9,
               left_center=2051, right_center=2128, attack_center=2146,
               attack_up_is_high=True)


def run(seconds=30, mode='both', trace=False):
    return robot_remote.run(seconds=seconds, mode=mode,
                            mapping=MAPPING, trace=trace,
                            attack_kind=ATTACK_KIND)
