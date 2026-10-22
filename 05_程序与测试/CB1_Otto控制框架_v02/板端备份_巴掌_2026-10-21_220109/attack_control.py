"""Attack controller: ch2 stick -> palm pulse command (pure logic).

No machine import - the PWM lives in drivers/palm_pwm.py. This module
only turns a raw remote frame into a target pulse width:

    None                -> palm disabled / link lost / not yet armed:
                           the driver must STOP and RELEASE
    neutral_us          -> engaged but centered: continuous stop pulse
                           (a continuous servo needs the neutral pulse to
                           not creep; only release kills the signal)
    neutral +/- delta   -> fixed low speed, direction by stick side;
                           magnitude of deflection is ignored (plan:
                           fixed low speed first)

State machine (D1 execution plan 2026-09-26):
- arm: the first valid frame with the stick inside the EXIT deadband.
  A stick held deflected at boot NEVER spins.
- hysteresis: engaging needs |axis| > ENTER; engaged stays until
  |axis| <= EXIT (between the two, an engaged command keeps running).
- reversal: commanding the opposite direction directly (without passing
  neutral) dwells at neutral for reverse_dwell_ms first; releasing
  during the dwell cancels the reversal.
- link loss / malformed frame: disarm + None; after recovery the stick
  must return to center before it can command again.
- an unchanged stick value is a valid continuous command - staleness is
  never inferred from repeated values.
"""
import input_adapter
import timeutil


class AttackController:
    def __init__(self, cfg, now_ms=None):
        self.cfg = dict(cfg)
        self._now = now_ms or timeutil.now_ms
        self.armed = False        # center observed since boot/loss
        self.engaged = False      # palm actively commanded
        self.last_dir = 0         # -1/+1 last commanded side; 0 = neutral
        self._reverse_since = None

    def _axis(self, frame):
        if not input_adapter.valid_frame(frame):
            return None
        raw = frame[self.cfg['channel']]
        axis = ((raw - self.cfg['center']) / float(self.cfg['span'])
                * self.cfg['direction'])
        return max(-1.0, min(1.0, axis))

    def update(self, frame, now_ms):
        if not self.cfg.get('enabled', False):
            return None
        axis = self._axis(frame)
        if axis is None:                       # lost / malformed / disabled
            self.armed = False
            self.engaged = False
            self.last_dir = 0
            self._reverse_since = None
            return None
        cfg = self.cfg

        if not self.armed:
            if abs(axis) <= cfg['exit_deadband']:
                self.armed = True              # stick observed centered
            else:
                return None                    # boot with stick deflected

        if self.engaged and abs(axis) <= cfg['exit_deadband']:
            self.engaged = False               # back inside EXIT: stop
            self.last_dir = 0
            self._reverse_since = None
        if not self.engaged and abs(axis) > cfg['enter_deadband']:
            self.engaged = True                # fresh engage: no dwell
            self._reverse_since = None

        if not self.engaged:
            return cfg['neutral_us']           # continuous stop pulse

        # Engaged: a direction change while already running (stick slammed
        # straight across center without entering the EXIT band) dwells at
        # neutral before reversing.
        desired = 1.0 if axis > 0 else -1.0
        if (desired != self.last_dir and self.last_dir != 0
                and self._reverse_since is None):
            self._reverse_since = now_ms
        if self._reverse_since is not None:
            if timeutil.diff_ms(now_ms, self._reverse_since) \
                    < cfg['reverse_dwell_ms']:
                return cfg['neutral_us']       # dwell before reversing
            self._reverse_since = None

        self.last_dir = desired
        return int(cfg['neutral_us'] + desired * cfg['delta_us'])
