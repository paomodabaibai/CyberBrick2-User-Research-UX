"""Battery-powered, one-shot walking demo for the CB1 receiver.

Cold boot is inert. Arm with both levers centered, hold K4 for >=1 second,
then release K4. Once armed, K4 is stop-only. A link loss or stop ends this
session; power-cycle the receiver to try again. The session is time-limited
and releases all PWM in finally. No servo moves while waiting to arm.
"""
import time

import config
import input_adapter
import main_v02
import states
import timeutil


ARM_HOLD_MS = 1000
SESSION_MS = 120000


def _centered(inp):
    return (abs(inp.left) <= config.RECENTER_BAND and
            abs(inp.right) <= config.RECENTER_BAND)


def run():
    session = None
    try:
        link = main_v02.RcLink()
        session = main_v02.start(link=link)
        held_at = None
        armed_hold = False
        print('battery_walk: waiting for live remote; center both levers, '
              'hold K4 for 1s, release to enable')
        while True:
            now = timeutil.now_ms()
            inp = input_adapter.from_rc(link.read(), now, config)
            if not inp.connected or not _centered(inp):
                held_at = None
                armed_hold = False
            elif inp.stop_pressed:
                if held_at is None:
                    held_at = now
                if timeutil.diff_ms(now, held_at) >= ARM_HOLD_MS:
                    armed_hold = True
            elif armed_hold:
                # enable() performs its own live read and checks K4 again.
                # A transient missing frame must never bypass the gate.
                try:
                    session.enable()
                    break
                except RuntimeError as exc:
                    print('battery_walk: arm rejected:', exc)
                    held_at = None
                    armed_hold = False
            else:
                held_at = None
            main_v02._sleep_ms(config.LOOP_MS)

        print('battery_walk: enabled; move one lever forward for one step')
        started = timeutil.now_ms()
        last_state = None
        while timeutil.diff_ms(timeutil.now_ms(), started) < SESSION_MS:
            tick = timeutil.now_ms()
            state = session.poll()
            if state != last_state:
                print('battery_walk: state=', state)
                last_state = state
            if state in (states.STOPPED, states.FAULT):
                print('battery_walk: ended by stop/fault:', session.ctrl.reason)
                break
            main_v02._sleep_ms(max(1, config.LOOP_MS -
                                   timeutil.diff_ms(timeutil.now_ms(), tick)))
        print('battery_walk: session finished')
    except Exception as exc:
        print('battery_walk: error:', exc)
    finally:
        if session is not None:
            session.release()
        print('battery_walk: PWM off')
