"""Scripted-gait fallback demo: NO radio needed.

The 2.4G link is down (transmitter solid green, 598/598 frame reads None;
pairing can only be restored via the MakerWorld app). For the presentation
this script feeds the SAME strict-enable + gait stack scripted synthetic
frames through a fake link, so the robot performs alternating left/right
steps exactly as it would from real lever pushes - the command mapper sees
normal frames and nothing inside the controller is bypassed or faked.

The link object only replaces rc_module.rc_slave_data(); enable() still
reads a live frame from it, K4 stays released throughout, and the session
is time-boxed with finally-guaranteed PWM off, like walk_session.

Board usage (robot SUPPORTED until stance is proven):
    import demo_scripted
    demo_scripted.run(steps=2)      # 2 left+right pairs, ~13 s total
"""
import config
import main_v02
import states
import timeutil

# Raw ADC values derived from config.REMOTE (measured resting centers).
_PUSH = 0.8  # normalized forward push, above STEP_THRESHOLD (0.55)
_CENTER_L = config.REMOTE['left_center']
_CENTER_R = config.REMOTE['right_center']
_SPAN = config.REMOTE['left_span']
_L_PUSH = int(_CENTER_L + _PUSH * _SPAN)
_R_PUSH = int(_CENTER_R + _PUSH * _SPAN)

INITIAL_S = 0.5   # centered frames before enable, so enable sees recenter
TAIL_S = 1.0      # stabilized stance after the last step, before release


def _frame(left_raw, right_raw):
    # Official 10-value frame [L1,L2,L3,R1,R2,R3,K1,K2,K3,K4];
    # lever values go to their CONFIGURED channels (left/right were
    # swapped 2026-09-24 evening: left=3, right=0).
    f = [2048] * 6 + [1] * 4
    f[config.REMOTE['left_channel']] = left_raw
    f[config.REMOTE['right_channel']] = right_raw
    return f


_CENTER = _frame(_CENTER_L, _CENTER_R)
_L_FRAME = _frame(_L_PUSH, _CENTER_R)
_R_FRAME = _frame(_CENTER_L, _R_PUSH)


class ScriptedLink:
    """Plays a fixed timeline of frames; read() = one remote sample.

    Timeline entries: (duration_s, frame). After the last entry the link
    keeps returning the final frame, so the session never sees a link loss.
    """

    def __init__(self, timeline):
        self.timeline = timeline
        self.t0 = None

    def start(self):
        self.t0 = timeutil.now_ms()

    def read(self):
        if self.t0 is None:
            self.start()
        el = timeutil.diff_ms(timeutil.now_ms(), self.t0)
        acc = 0
        for dur_s, frame in self.timeline:
            acc += int(dur_s * 1000)
            if el < acc:
                return frame
        return self.timeline[-1][1]


def build_link(steps=2, cycle=None):
    """One cycle: push LEFT (the step runs while held), then recenter long
    enough for the full gait (1800 ms phase sum) to finish. Left and right
    alternate, so the v02 no-repeat rule is never hit."""
    cycle = cycle or (1.2, 2.4)  # push, recenter-after-step
    p, r = cycle
    tl = [(INITIAL_S, _CENTER)]
    for i in range(steps):
        tl.append((p, _L_FRAME))
        tl.append((r, _CENTER))
        tl.append((p, _R_FRAME))
        tl.append((r, _CENTER))
    tl.append((TAIL_S, _CENTER))
    return ScriptedLink(tl)


def total_seconds(steps=2, cycle=None):
    p, r = cycle or (1.2, 2.4)
    return INITIAL_S + steps * 2 * (p + r) + TAIL_S


def run(steps=2, cfg=None, log=print, cycle=None, link=None):
    """Time-boxed scripted walk. ALWAYS releases PWM at the end."""
    cfg = cfg or config
    link = link or build_link(steps, cycle)
    session = main_v02.start(cfg, link=link)
    session.ctrl.log = log
    total = total_seconds(steps, cycle) + 0.5
    log('demo_scripted: %d step pair(s), ~%.0fs, strict enable on scripted '
        'frames (NO radio involved)' % (steps, total))
    try:
        session.enable()
        if hasattr(link, 'start'):
            link.start()  # restart the timeline now that enable passed
        t_start = timeutil.now_ms()
        end = t_start + int(total * 1000)
        last_state = None
        while timeutil.now_ms() < end:
            t0 = timeutil.now_ms()
            state = session.poll()
            if state != last_state:
                el = timeutil.diff_ms(timeutil.now_ms(), t_start)
                log('demo_scripted: t+%d.%03ds state=%s' %
                    (el // 1000, el % 1000, state))
                last_state = state
            main_v02._sleep_ms(max(1, cfg.LOOP_MS -
                                   timeutil.diff_ms(timeutil.now_ms(), t0)))
        log('demo_scripted: done, state=%s' % session.ctrl.state)
    finally:
        session.release()
        log('demo_scripted: PWM off (servo power stays on)')
    return session
