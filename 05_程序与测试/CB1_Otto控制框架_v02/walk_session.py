"""Time-boxed remote walking session for live bench nights.

Why this instead of main_v02.run() for bench sessions: a serial exec cannot
forward Ctrl-C to the board, and the house rule for motion tests is a definite
duration with finally-guaranteed PWM off. This script enables STRICTLY (4
calibrated joints, live frame, K4 up), polls the remote for `seconds` while
printing every state change and controller event, then ALWAYS releases the
output - normal end, fault, or crash.

Board usage (transmitter ON; robot supported until stance is proven):
    import walk_session
    walk_session.run(45)        # push a lever forward past the threshold to
                                # trigger one step; recenter, then push again
Faults (K4, link loss, stall) are NOT auto-recovered: the state shows in the
printout and the session keeps polling until time is up or you re-run.
"""
import config
import main_v02
import states
import timeutil


def wait_for_frames(link, cfg, timeout_ms=8000, need=10, log=print):
    """Block until `need` consecutive valid frames arrive (or timeout).

    Why: right after a serial soft reset, rc_slave_init needs a moment
    before frames flow; enabling inside that cold window is rejected even
    though the link is fine (observed 2026-09-24: enable failed instantly,
    an 8 s probe seconds later read 199/200 frames).
    """
    import input_adapter
    t0 = timeutil.now_ms()
    good = 0
    while timeutil.diff_ms(timeutil.now_ms(), t0) < timeout_ms:
        inp = input_adapter.from_rc(link.read(), timeutil.now_ms(), cfg)
        good = good + 1 if inp.connected else 0
        if good >= need:
            return True
        main_v02._sleep_ms(20)
    return False


def run(seconds=45.0, cfg=None, link=None, session=None, log=print,
        warmup_ms=8000):
    cfg = cfg or config
    session = session or main_v02.start(cfg, link=link)
    if session.link is None:
        session.link = link or main_v02.RcLink()
    session.ctrl.log = log
    log('walk_session: %.1fs, strict enable (4 calibrated joints + live '
        'frame + K4 up)' % seconds)
    try:
        if not wait_for_frames(session.link, cfg, timeout_ms=warmup_ms,
                               log=log):
            raise RuntimeError('walk_session: no frames after %d ms - '
                               'check transmitter/link' % warmup_ms)
        session.enable()
        t_start = timeutil.now_ms()
        end = t_start + int(seconds * 1000)
        last_state = None
        while timeutil.now_ms() < end:
            t0 = timeutil.now_ms()
            state = session.poll()
            if state != last_state:
                el = timeutil.diff_ms(timeutil.now_ms(), t_start)
                log('walk_session: t+%d.%03ds state=%s' %
                    (el // 1000, el % 1000, state))
                last_state = state
            main_v02._sleep_ms(max(1, cfg.LOOP_MS -
                                   timeutil.diff_ms(timeutil.now_ms(), t0)))
        log('walk_session: time up, state=%s' % session.ctrl.state)
    finally:
        session.release()
        log('walk_session: PWM off (servo power stays on)')
    return session
