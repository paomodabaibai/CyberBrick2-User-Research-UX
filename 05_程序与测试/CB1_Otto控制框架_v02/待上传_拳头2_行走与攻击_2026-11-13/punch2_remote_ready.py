"""New fist robot: unchanged walking plus held, two-speed M1 attack."""
import robot_remote
from punch2_walk_ready import MAPPING as WALK_MAPPING

ATTACK_KIND = 'punch'
MAPPING = dict(WALK_MAPPING)
MAPPING.update(slow_speed=1024, fast_speed=1800)


def run(seconds=30, mode='both', trace=False):
    return robot_remote.run(seconds=seconds, mode=mode, mapping=MAPPING,
                            trace=trace, attack_kind=ATTACK_KIND)
