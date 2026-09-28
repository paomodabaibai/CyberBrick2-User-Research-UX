"""Time-based trajectory: chained segments with smooth interpolation.

Segments interpolate from the pose captured at segment entry (continuity by
construction) to the segment target over its duration. Progress advances by
actual elapsed time, so loop-rate jitter cannot distort the shape.
"""

import joint_model


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class Segment:
    def __init__(self, name, duration_ms, target, easing=smoothstep):
        if duration_ms <= 0:
            raise ValueError('Segment %s needs positive duration' % name)
        self.name = name
        self.duration_ms = duration_ms
        self.target = list(target)
        self.easing = easing


class Trajectory:
    def __init__(self, segments, start_pose, joint_model_ref=None):
        if not segments:
            raise ValueError('Trajectory needs at least one segment')
        self.segments = [Segment(n, d, t) for (n, d, t) in segments]
        self.start_pose = list(start_pose)
        self.jm = joint_model_ref
        self.validate_targets()
        self.reset()

    def validate_targets(self):
        """Reject the whole action if any target leaves joint limits."""
        if self.jm is None:
            return
        origin = list(self.start_pose)
        for seg in self.segments:
            # A target is reached from the previous segment's target (or the
            # true start pose), matching how update() will actually run.
            try:
                self.jm.servo_angles(seg.target)
            except joint_model.LimitViolation as exc:
                raise joint_model.LimitViolation(
                    'segment %s: %s' % (seg.name, exc))
            origin = seg.target

    def reset(self):
        self.origin = list(self.start_pose)
        self.seg_index = 0
        self.elapsed_in_seg = 0.0
        self.pose = list(self.start_pose)
        self.done = False

    def current_segment(self):
        return self.segments[self.seg_index] if not self.done else None

    def update(self, dt_ms):
        """Advance by elapsed time; returns (pose, segment_name, done)."""
        if self.done:
            return list(self.segments[-1].target), None, True
        remaining = max(0.0, float(dt_ms))
        while remaining > 0.0 and self.seg_index < len(self.segments):
            seg = self.segments[self.seg_index]
            take = min(remaining, seg.duration_ms - self.elapsed_in_seg)
            self.elapsed_in_seg += take
            remaining -= take
            u = seg.easing(self.elapsed_in_seg / seg.duration_ms)
            self.pose = [a + (b - a) * u
                         for a, b in zip(self.origin, seg.target)]
            if self.elapsed_in_seg >= seg.duration_ms:
                self.origin = seg.target
                self.seg_index += 1
                self.elapsed_in_seg = 0.0
        if self.seg_index >= len(self.segments):
            self.done = True
            return list(self.segments[-1].target), None, True
        return list(self.pose), self.segments[self.seg_index].name, False
