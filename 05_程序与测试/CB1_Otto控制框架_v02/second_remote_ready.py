"""COM14 robot + COM15 remote, manual timed entry; import is inert.

Channel mapping retained at user request. Centers from current static frames.
No boot changes or automatic startup. Actual yaw/attack observed by operator.
"""
import second_punch_remote

MAPPING = dict(left=3, right=0, attack=2, stop=9,
               left_center=2051, right_center=2128, attack_center=2146)


def run(seconds=30, mode='both'):
    return second_punch_remote.run(seconds=seconds, mode=mode, mapping=MAPPING)
