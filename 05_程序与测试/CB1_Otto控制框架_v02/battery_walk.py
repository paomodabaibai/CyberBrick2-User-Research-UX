"""Battery-powered standing remote mode: ALWAYS ON after power-up.

v04 semantics (user decision 2026-09-24 evening):
- On power-up the board waits for stable remote frames, then ENABLES BY
  ITSELF and stays enabled FOREVER (no time limit, no arming gesture -
  K4 has no function at all now).
- Push a lever -> that foot steps; hold it -> continuous steps; pull it
  back -> backward steps. Levers centered -> robot just stands.
- Link loss -> FAULT (PWM keeps holding the last pose); when frames
  return the session auto-recovers and stands ready again.
- The only stop is the physical power switch (or unplugging the battery).

Board safety note: power-up with the robot on a mousepad and room to
stand; it will hold stance (all servos energized) immediately after the
link comes up.
"""
import time

import config
import input_adapter
import main_v02
import states
import timeutil


def _frames_stable(link, need=10, timeout_ms=15000):
    good = 0
    t0 = timeutil.now_ms()
    while timeutil.diff_ms(timeutil.now_ms(), t0) < timeout_ms:
        inp = input_adapter.from_rc(link.read(), timeutil.now_ms(), config)
        good = good + 1 if inp.connected else 0
        if good >= need:
            return True
        main_v02._sleep_ms(20)
    return False


def run():
    session = None
    try:
        link = main_v02.RcLink()
        session = main_v02.start(link=link)
        print('battery_walk: waiting for remote link...')
        if not _frames_stable(link):
            print('battery_walk: no link; retrying forever (power off to '
                  'stop)')
            while not _frames_stable(link, need=10, timeout_ms=30000):
                main_v02._sleep_ms(200)
        print('battery_walk: link up, auto-enabling stance; push a lever '
              'to step (hold = repeat, pull back = backward)')
        session.enable()
        while True:
            tick = timeutil.now_ms()
            state = session.poll()
            if state == states.FAULT:
                # Link loss: hold pose, wait for frames, auto-recover.
                print('battery_walk: link lost - holding pose; will '
                      'auto-recover when frames return')
                while not _frames_stable(link, need=10, timeout_ms=30000):
                    main_v02._sleep_ms(200)
                session.recover()
                print('battery_walk: link back, recovered to ready')
            main_v02._sleep_ms(max(1, config.LOOP_MS -
                                   timeutil.diff_ms(timeutil.now_ms(), tick)))
    except Exception as exc:
        print('battery_walk: error:', exc)
    finally:
        if session is not None:
            session.release()
        print('battery_walk: PWM off')
