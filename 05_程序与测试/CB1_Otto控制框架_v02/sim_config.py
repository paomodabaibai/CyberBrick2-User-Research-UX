"""PC-only virtual profile: four VIRTUAL position servos, fully calibrated.

This isolates simulation from hardware truth: config.py keeps the real
wiring/facts (left_ankle = disabled continuous placeholder, nothing
calibrated), while the simulator and PC tests run against this profile so a
missing or uncalibrated actuator on the real robot can never be hidden by
simulation defaults. Never upload or import this on the board.
"""
import copy

import config as hardware


class _Profile:
    pass


def virtual():
    cfg = _Profile()
    for name in dir(hardware):
        if name.isupper():
            setattr(cfg, name, getattr(hardware, name))
    cfg.JOINTS = copy.deepcopy(hardware.JOINTS)
    for joint in cfg.JOINTS.values():
        joint['enabled'] = True
        joint['actuator'] = 'position'
        joint['calibrated'] = True
    cfg.GAIT = copy.deepcopy(hardware.GAIT)
    return cfg
