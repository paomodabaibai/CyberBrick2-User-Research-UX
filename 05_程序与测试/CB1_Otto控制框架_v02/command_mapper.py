"""Command mapper: lever pushes -> step requests (forward/backward), stop.

v03 operation rules (changed 2026-09-24 after live remote-walk validation):
- push a lever FORWARD past STEP_THRESHOLD: one FORWARD step request (left
  lever -> left foot, right lever -> right foot)
- pull a lever BACKWARD past -STEP_THRESHOLD: one BACKWARD step request on
  the same foot
- CONTINUOUS STEPPING: a lever held engaged re-triggers as soon as the
  previous step finishes (holding left forward = repeated left steps =
  turn right; same for backward pulls). Requests during a step are still
  dropped, never queued.
- BOTH levers engaged (any mix of forward/backward): conflict, rejected
  once per hold
- recenter (both levers inside RECENTER_BAND) is required ONLY after
  enable/recover/link-loss - a single push-and-hold is a valid continuous
  command, not a stuck trigger
- K4 pressed: STOP event, takes priority over steps
- link loss surfaced as LINK_LOST once per loss so the controller can fault

The mapper is a pure event filter: it never touches poses or the driver.
"""

STEP_LEFT = 'step_left'
STEP_RIGHT = 'step_right'
STEP_BACK_LEFT = 'step_back_left'
STEP_BACK_RIGHT = 'step_back_right'
STOP = 'stop'
LINK_LOST = 'link_lost'
REJECTED_CONFLICT = 'rejected_conflict'
DROPPED_BUSY = 'dropped_busy'


class CommandMapper:
    def __init__(self, config):
        self.threshold = config.STEP_THRESHOLD
        self.recenter_band = config.RECENTER_BAND
        self.ready = True   # False until levers are seen near center
                             # (set after enable/recover; one push then
                             # re-arms by itself - continuous stepping)
        self._link_ok = True
        self._fired = False        # a request fired for this push
        self._busy_noted = False   # DROPPED_BUSY emitted for this busy window
        self._conflict_noted = False

    def _near_center(self, value):
        return abs(value) <= self.recenter_band

    def update(self, inp, busy=False):
        """One UnifiedInput -> list of event strings (may be empty)."""
        events = []
        if not inp.connected:
            first_loss = self._link_ok
            self._link_ok = False
            self.ready = True
            self._reset_hold_flags()
            return [LINK_LOST] if first_loss else []
        self._link_ok = True
        if inp.stop_pressed:
            self.ready = True
            self._reset_hold_flags()
            events.append(STOP)
            return events

        both_centered = (self._near_center(inp.left)
                         and self._near_center(inp.right))
        if both_centered:
            self.ready = True
            self._reset_hold_flags()
            return events

        if not self.ready:
            # waiting for the recenter after enable/recover: hold everything
            return events

        l_fwd = inp.left > self.threshold
        r_fwd = inp.right > self.threshold
        l_back = inp.left < -self.threshold
        r_back = inp.right < -self.threshold
        l_any = l_fwd or l_back
        r_any = r_fwd or r_back

        if l_any and r_any:
            # two engaged levers can never become one step
            if not self._conflict_noted:
                self._conflict_noted = True
                events.append(REJECTED_CONFLICT)
            return events

        if busy:
            # A step is in flight: note the hold once, drop every request.
            # _fired is cleared here so the SAME held lever re-triggers the
            # moment the controller reports not-busy again (continuous
            # stepping); it does not queue anything.
            self._fired = False
            self._conflict_noted = False
            if (l_any or r_any) and not self._busy_noted:
                self._busy_noted = True
                events.append(DROPPED_BUSY)
            return events
        self._busy_noted = False

        if self._fired:
            # single push already produced its request; recenter re-arms
            return events

        if l_fwd:
            events.append(STEP_LEFT)
        elif r_fwd:
            events.append(STEP_RIGHT)
        elif l_back:
            events.append(STEP_BACK_LEFT)
        elif r_back:
            events.append(STEP_BACK_RIGHT)
        if events:
            self._fired = True
        return events

    def _reset_hold_flags(self):
        self._fired = False
        self._busy_noted = False
        self._conflict_noted = False
