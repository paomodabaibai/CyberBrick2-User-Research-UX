"""Read-only mirror of battery_walk's arm gate; NEVER creates PWM/enables.

Run manually: import diagnose_arm; diagnose_arm.run(60)
Reports which condition resets the hold timer. A WOULD_ENABLE event is
only a prediction: the real enable() performs an additional live read.
No controller/driver modules are imported or instantiated here.
"""
import time
import config
import input_adapter
import timeutil


class ArmProbe:
    def __init__(self, band=0.20, hold_ms=1000):
        self.band = band
        self.hold_ms = hold_ms
        self.held_at = None
        self.armed_hold = False
        self.max_hold_ms = 0
        self.frames = 0
        self.invalid = 0
        self.resets = dict(no_frame=0, not_centered=0, short_release=0)
        self.would_enable = 0

    def update(self, inp, now):
        self.frames += 1
        held = (0 if self.held_at is None else
                max(0, timeutil.diff_ms(now, self.held_at)))
        events = []
        if not inp.connected:
            self.invalid += 1
            reason = 'no_frame'
        elif abs(inp.left) > self.band or abs(inp.right) > self.band:
            reason = 'not_centered'
        else:
            reason = None
        if reason:
            if self.held_at is not None or self.armed_hold:
                self.resets[reason] += 1
                events.append('RESET %s after %dms' % (reason, held))
            self.held_at = None
            self.armed_hold = False
            return reason, events
        if inp.stop_pressed:
            if self.held_at is None:
                self.held_at = now
                held = 0
                events.append('PRESS timer started')
            self.max_hold_ms = max(self.max_hold_ms, held)
            if held >= self.hold_ms and not self.armed_hold:
                self.armed_hold = True
                events.append('HOLD_OK release K4 to complete gesture')
            return 'hold_ok' if self.armed_hold else 'holding', events
        if self.armed_hold:
            self.would_enable += 1
            events.append('WOULD_ENABLE (diagnosis only; NO PWM)')
        elif self.held_at is not None:
            self.resets['short_release'] += 1
            events.append('RESET short_release after %dms' % held)
        self.held_at = None
        self.armed_hold = False
        return 'waiting_press', events


def run(seconds=60, read=None, log=print):
    if read is None:
        import rc_module
        if rc_module.rc_slave_init() is False:
            raise RuntimeError('rc_slave_init failed')
        read = rc_module.rc_slave_data
    probe = ArmProbe(config.RECENTER_BAND)
    start = timeutil.now_ms()
    heartbeat = start
    previous = None
    log('ARM PROBE START: NO PWM. Center both levers; hold K4 5s, release.')
    try:
        while timeutil.diff_ms(timeutil.now_ms(), start) < seconds * 1000:
            now = timeutil.now_ms()
            raw = read()
            inp = input_adapter.from_rc(raw, now, config)
            status, events = probe.update(inp, now)
            key = (inp.connected, inp.stop_pressed, status)
            if events or key != previous or timeutil.diff_ms(now, heartbeat) >= 1000:
                log('t=%dms state=%s link=%s K4=%s L=%.3f R=%.3f events=%s' %
                    (timeutil.diff_ms(now, start), status, inp.connected,
                     raw[9] if input_adapter.valid_frame(raw) else None,
                     inp.left, inp.right, events))
                heartbeat = now
                previous = key
            if hasattr(time, 'sleep_ms'):
                time.sleep_ms(20)
            else:
                time.sleep(0.02)
    finally:
        log('SUMMARY samples=%d invalid=%d max_hold_ms=%d resets=%s '
            'would_enable=%d; NO PWM WAS CREATED' %
            (probe.frames, probe.invalid, probe.max_hold_ms, probe.resets,
             probe.would_enable))
    return probe
