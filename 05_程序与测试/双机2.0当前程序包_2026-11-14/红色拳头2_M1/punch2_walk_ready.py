"""New red receiver, walking only while the upper module is assembled.

Confirmed wiring: left Y L3/ch2, right Y R3/ch5, attack R1/ch3, K1/ch6.
Stationary readings on 2026-11-13; physical direction still needs observation.
No motor driver is created, even if a caller requests mode='both'.
"""
import robot_remote

ATTACK_KIND = 'punch'
MAPPING = dict(left=2,right=5,attack=3,dance=6,
               left_center=2002,right_center=1990,attack_center=2115,
               attack_up_is_high=True,dance_enabled=False)

def run(seconds=30,mode='walk',trace=False):
    return robot_remote.run(seconds=seconds,mode='walk',mapping=MAPPING,
                            trace=trace,attack_kind=ATTACK_KIND)
