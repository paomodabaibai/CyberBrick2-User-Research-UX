"""Operator-started live remote walk with input-boundary diagnostics."""
import config
import input_adapter
import main_v02
import timeutil
import states


def run(seconds=90):
    session = main_v02.start(link=main_v02.RcLink())
    session.ctrl.log = print
    previous = None
    last_print = timeutil.now_ms()
    started = last_print
    try:
        # No output until a live centered frame with K4 released arrives.
        while timeutil.diff_ms(timeutil.now_ms(), started) < 10000:
            raw = session.link.read()
            inp = input_adapter.from_rc(raw, timeutil.now_ms(), config)
            if (inp.connected and not inp.stop_pressed and
                    abs(inp.left) <= config.RECENTER_BAND and
                    abs(inp.right) <= config.RECENTER_BAND):
                break
            main_v02._sleep_ms(20)
        else:
            raise RuntimeError('No centered live frame with K4 released in 10s')
        session.enable()
        started = timeutil.now_ms()
        print('TRACE WALK READY; no K4 needed; push left then right')
        while timeutil.diff_ms(timeutil.now_ms(), started) < seconds * 1000:
            now = timeutil.now_ms()
            raw = session.link.read()
            # Feed exactly the same sample to diagnostics and controller.
            state = session.loop_once(raw, now)
            inp = session.last_inp
            key = (state, round(inp.left, 1), round(inp.right, 1),
                   inp.stop_pressed, session.ctrl.mapper.ready)
            if key != previous or timeutil.diff_ms(now, last_print) >= 1000:
                print('t=%d raw=%s L=%.3f R=%.3f K4=%s state=%s '
                      'trigger_ready=%s phase=%s' %
                      (timeutil.diff_ms(now, started), raw, inp.left,
                       inp.right, inp.stop_pressed, state,
                       session.ctrl.mapper.ready, session.ctrl.phase))
                previous = key
                last_print = now
            if state in (states.FAULT, states.STOPPED):
                break
            main_v02._sleep_ms(20)
    finally:
        session.release()
        print('TRACE WALK PWM OFF')
