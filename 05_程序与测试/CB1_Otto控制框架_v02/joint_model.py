"""Joint model: centers, mirrored directions, limits, angle conversion.

Logical pose = per-joint offsets in degrees from the calibrated stance,
ordered as config.JOINT_ORDER. Only this layer converts to servo angles and
to PWM pulse widths; everything upstream stays in logical offsets.

This layer also owns actuator capability reporting (task: missing hardware
must never be hidden). Walking requires every joint to be enabled, a
'position' actuator, and calibrated.
"""


class LimitViolation(Exception):
    """A requested pose leaves a joint's calibrated range. Never clamp."""


def _walk_blockers(joints):
    blockers = []
    for name in joints:
        cfg = joints[name]
        if not cfg.get('enabled', True):
            blockers.append('%s: channel disabled' % name)
        elif cfg.get('actuator') != 'position':
            blockers.append('%s: %s actuator cannot hold a pose'
                            % (name, cfg.get('actuator')))
        elif not cfg.get('calibrated', False):
            blockers.append('%s: not calibrated' % name)
    return blockers


class JointModel:
    def __init__(self, config):
        self.order = list(config.JOINT_ORDER)
        self.index = dict(config.JOINT_INDEX)
        self.joints = {name: dict(cfg) for name, cfg in config.JOINTS.items()}
        self.pulse0 = config.PULSE_AT_0_US
        self.pulse180 = config.PULSE_AT_180_US

    # --- capability (task 4) ---------------------------------------------
    def walk_blockers(self):
        """Human-readable list of reasons walking must not be enabled."""
        return _walk_blockers(self.joints)

    def can_walk(self):
        return not self.walk_blockers()

    def output_blockers(self):
        """Joints the driver must never command (disabled/continuous)."""
        out = []
        for name, cfg in self.joints.items():
            if not cfg.get('enabled', True):
                out.append('%s: disabled' % name)
            elif cfg.get('actuator') != 'position':
                out.append('%s: continuous' % name)
        return out

    # --- geometry ---------------------------------------------------------
    def servo_angle(self, name, offset):
        cfg = self.joints[name]
        angle = cfg['center'] + cfg['trim'] + cfg['direction'] * offset
        if not cfg['min'] <= angle <= cfg['max']:
            raise LimitViolation('%s offset %.2f -> %.2f outside [%.0f, %.0f]'
                                 % (name, offset, angle, cfg['min'], cfg['max']))
        return angle

    def servo_angles(self, pose):
        """pose: list of offsets in JOINT_ORDER. Validates ALL before use."""
        angles = [self.servo_angle(name, offset)
                  for name, offset in zip(self.order, pose)]
        return angles

    def pulses(self, pose):
        return [self.pulse0 + angle / 180.0 * (self.pulse180 - self.pulse0)
                for angle in self.servo_angles(pose)]

    def pose_from_levers(self, left, right):
        raise NotImplementedError  # reserved for future direct-lever modes
