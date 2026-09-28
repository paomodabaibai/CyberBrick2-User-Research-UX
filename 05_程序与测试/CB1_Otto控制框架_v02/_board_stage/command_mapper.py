"""Command mapper: lever pushes -> single-step requests, stop, rejections.

Rules (v1 operation):
- push a lever forward past STEP_THRESHOLD: one STEP request for that side
- holding the push never repeats; BOTH levers must come back inside
  RECENTER_BAND before anything can trigger again
- both levers pushed forward together: the request is rejected until recenter
- a request arriving while the controller is busy is dropped once (DROPPED_BUSY),
  never queued; a lever held straight through the busy window stays disarmed
- K4 (stop button) pressed: STOP event, takes priority over steps
- backward pull: no action in v02 (interface kept)
- link loss is surfaced as LINK_LOST once per loss so the controller can fault

The mapper is a pure event filter: it never touches poses or the driver.
"""

STEP_LEFT = 'step_left'
STEP_RIGHT = 'step_right'
STOP = 'stop'
LINK_LOST = 'link_lost'
REJECTED_CONFLICT = 'rejected_conflict'
DROPPED_BUSY = 'dropped_busy'

_LEFT = 'left'
_RIGHT = 'right'


class CommandMapper:
    def __init__(self, config):
        self.threshold = config.STEP_THRESHOLD
        self.recenter_band = config.RECENTER_BAND
        self.ready = True   # both levers seen near center since last trigger
        self._link_ok = True

    def _near_center(self, value):
        return abs(value) <= self.recenter_band

    def update(self, inp, busy=False):
        """One UnifiedInput -> list of event strings (may be empty)."""
        events = []
        if not inp.connected:
            first_loss = self._link_ok
            self._link_ok = False
            self.ready = True
            return [LINK_LOST] if first_loss else []
        self._link_ok = True
        if inp.stop_pressed:
            self.ready = True
            events.append(STOP)
            return events

        both_forward = (inp.left > self.threshold
                        and inp.right > self.threshold)
        both_centered = (self._near_center(inp.left)
                         and self._near_center(inp.right))
        if both_centered:
            self.ready = True
            return events

        if both_forward:
            if self.ready:
                self.ready = False
                events.append(REJECTED_CONFLICT)
            return events

        if not self.ready or busy:
            # Hold without recenter never retriggers; busy requests are
            # dropped, never queued. Consuming `ready` here also prevents a
            # lever held straight through a step from firing afterwards.
            forward = (inp.left > self.threshold
                       or inp.right > self.threshold)
            if busy and forward and self.ready:
                self.ready = False
                events.append(DROPPED_BUSY)
            return events

        if inp.left > self.threshold:
            self.ready = False
            events.append(STEP_LEFT)
        elif inp.right > self.threshold:
            self.ready = False
            events.append(STEP_RIGHT)
        return events
