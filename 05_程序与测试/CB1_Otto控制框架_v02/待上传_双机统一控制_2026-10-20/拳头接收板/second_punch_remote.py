"""Compatibility entry; both robots use robot_remote as the sole control core."""
from robot_remote import (RemotePolicy, WalkMotion, DanceMotion, run, monitor,
                          motor_service, diff, PORTS, DEFAULT, CONTROL_VERSION,
                          HIP_AMP, ANKLE_AMP, BIAS, TURN_SPLIT, run_forever)
