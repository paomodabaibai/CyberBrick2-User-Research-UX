"""Simulated driver: records every commanded pose, touches no hardware."""
import time


class SimDriver:
    def __init__(self):
        self.frames = []      # (timestamp_ms, pose copy)
        self.singles = []     # (joint_name, absolute_angle_deg) via write_one
        self.released = False
        self.t0 = time.ticks_ms() if hasattr(time, 'ticks_ms') else 0

    def write(self, pose, now_ms=None):
        self.released = False
        self.frames.append((now_ms, list(pose)))

    def write_one(self, name, angle_deg, now_ms=None):
        """Single-channel absolute-angle write (centering utility)."""
        self.released = False
        self.singles.append((name, angle_deg))

    def release(self):
        self.released = True

    def last_pose(self):
        return list(self.frames[-1][1]) if self.frames else None
