"""Second robot manual timed entry; import is inert.

Left ch3, right ch0, punch ch2 and K4 ch9 were verified one stick at a time.
Receiver has no active boot.py/main.py; this does not auto-start on power-up.
"""
import second_punch_remote

MAPPING = dict(left=3, right=0, attack=2, stop=9,
               left_center=2051, right_center=2128, attack_center=2146,
               attack_up_is_high=True)


def run(seconds=30, mode='both', trace=False):
    return second_punch_remote.run(seconds=seconds, mode=mode,
                                   mapping=MAPPING, trace=trace)
