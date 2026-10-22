"""Input adapter: raw remote frames or scripted data -> UnifiedInput."""

REMOTE_CHANNELS = ('L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'K1', 'K2', 'K3', 'K4')


class UnifiedInput:
    def __init__(self, left, right, stop_pressed, connected, timestamp_ms):
        self.left = left              # -1..1, forward positive
        self.right = right            # -1..1, forward positive
        self.stop_pressed = stop_pressed
        self.connected = connected
        self.timestamp_ms = timestamp_ms

    def __repr__(self):
        return ('UnifiedInput(l=%.2f r=%.2f stop=%s link=%s t=%d)'
                % (self.left, self.right, self.stop_pressed,
                   self.connected, self.timestamp_ms))


def _axis(raw, center, span, direction):
    return max(-1.0, min(1.0, (raw - center) / float(span) * direction))


def valid_frame(frame):
    return (isinstance(frame, (list, tuple)) and len(frame) == 10
            and all(isinstance(x, int) and 0 <= x <= 4095 for x in frame[:6])
            and all(x in (0, 1) for x in frame[6:]))


def from_rc(frame, now_ms, config):
    """Official 10-value frame -> UnifiedInput. Bad/missing frame = no link.

    FRESHNESS LIMITATION (do not "fix" by faking): rc_slave_data() gives no
    sequence number or receive timestamp. `now_ms` is the READ time, not the
    data time, so a cached stale frame is indistinguishable from a fresh one.
    connected=True therefore means "a frame was returned this tick", nothing
    more. Staleness must never be inferred from unchanged lever values.
    """
    rc = config.REMOTE
    if not valid_frame(frame):
        return UnifiedInput(0.0, 0.0, False, False, now_ms)
    left = _axis(frame[rc['left_channel']], rc['left_center'],
                 rc['left_span'], rc['left_direction'])
    right = _axis(frame[rc['right_channel']], rc['right_center'],
                  rc['right_span'], rc['right_direction'])
    stop = (rc['stop_button'] is not None
            and frame[6 + rc['stop_button']] == rc['button_active'])
    return UnifiedInput(left, right, stop, True, now_ms)


def from_manual(left, right, stop_pressed=False, connected=True, now_ms=0):
    """Direct normalized inputs for scripted simulation and debug."""
    return UnifiedInput(max(-1.0, min(1.0, left)), max(-1.0, min(1.0, right)),
                        stop_pressed, connected, now_ms)
