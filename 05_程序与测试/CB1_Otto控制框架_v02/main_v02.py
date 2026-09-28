"""CB1 onboard 20 ms main loop for the v02 framework.

Receiver board only: run with DRIVER='cb1_pwm' in the board's config.py.
    mpremote connect COM7 run main_v02.py

ENABLE IS EXPLICIT AND MANUAL - valid remote frames never enable anything,
and nothing in this module re-introduces auto-enable.

Complete operator flow (single-threaded REPL; Ctrl-C pauses, session stays):
    import main_v02
    main_v02.run()                     # 1+2. init link, read continuously
    <Ctrl-C>                           #    pause: any active gait is
                                       #    CANCELLED (STOPPED, pose held);
                                       #    K4/link-loss detection are DOWN
                                       #    while paused - output is held
                                       #    but NOT remote-protected
    main_v02.SESSION.enable()          # 3. explicit enable: re-reads the
                                       #    remote NOW, refuses without a
                                       #    valid frame or while K4 is held
    main_v02.resume()                  # 4. run again (this is ONLY the
                                       #    loop, not enable/recover);
                                       #    steps only after the levers
                                       #    were seen near center
    <Ctrl-C>
    main_v02.SESSION.recover()         # 5. after stop/fault; same live
                                       #    re-read + K4 gate + recenter
    main_v02.SESSION.release()         # 6. exit: PWM off (stops the pulse
                                       #    signal; servo POWER stays on -
                                       #    only a physical switch cuts it)

Step-by-step alternative instead of run(): create the session once, then
call poll() per tick from the REPL:
    s = main_v02.start(link=main_v02.RcLink())
    s.poll()                           # one remote read + controller tick
    s.enable(); s.poll(); ...

FRESHNESS LIMITATION (documented, never faked): rc_slave_data() exposes no
sequence number or receive timestamp. Every read returns whatever the
receiver firmware currently holds, which can be a cached old frame after a
physical link loss. enable()/recover() therefore guarantee "the remote was
read at this instant" - they cannot guarantee the frame was just generated.

The per-frame logic lives in BoardSession.loop_once so the PC test suite can
exercise it with the sim driver; this module never imports machine itself
and uses no os.path / sys.path tricks (board files import top-level).
"""
import time

import config
import states
import controller
import gait_planner
import input_adapter
import joint_model
import timeutil
from drivers import create_driver


def build_controller(cfg=config):
    jm = joint_model.JointModel(cfg)
    return controller.Controller(cfg, jm, gait_planner.GaitPlanner(cfg),
                                 create_driver(jm, cfg))


class RcLink:
    """Remote link: owns rc_module init/read in exactly one place."""

    def __init__(self):
        import rc_module
        self._rc = rc_module
        if self._rc.rc_slave_init() is False:
            raise RuntimeError('rc_slave_init failed')

    def read(self):
        return self._rc.rc_slave_data()


class BoardSession:
    """Raw RC frame -> UnifiedInput -> controller, one frame per call.

    Freshness bookkeeping (honest): the official rc API exposes no receive
    timestamp, so 'connected' can only mean "a frame came back this tick".
    last_valid_ms records the last tick that had a frame; nothing infers
    staleness from unchanged lever values, and config's timeout_ms is
    documented as unapplicable instead of being faked.
    """

    def __init__(self, ctrl, cfg=config, link=None):
        self.ctrl = ctrl
        self.cfg = cfg
        self.link = link
        self.last_inp = None
        self.last_valid_ms = None

    def loop_once(self, frame, now_ms):
        """One pure-logic tick; tests inject the frame and clock directly."""
        inp = input_adapter.from_rc(frame, now_ms, self.cfg)
        self.last_inp = inp
        if inp.connected:
            self.last_valid_ms = now_ms
        self.ctrl.update(inp, now_ms)
        return self.ctrl.state

    def poll(self):
        """One live tick: read the remote NOW, then update.

        REPL-friendly single step. Use run()/resume() for a continuous loop.
        """
        if self.link is None:
            raise RuntimeError('poll rejected: no remote link attached '
                               '(start(link=RcLink()))')
        return self.loop_once(self.link.read(), timeutil.now_ms())

    # --- explicit operator entries, all on a FRESH remote read -----------
    # They never trust last_inp: that value can be arbitrarily old (the loop
    # may have been paused at Ctrl-C), so gating on it could mistake a stale
    # frame for the current remote state.
    def _live_input(self, action):
        if self.link is None:
            raise RuntimeError('%s rejected: no remote link attached' % action)
        now = timeutil.now_ms()
        inp = input_adapter.from_rc(self.link.read(), now, self.cfg)
        self.last_inp = inp
        if inp.connected:
            self.last_valid_ms = now
        else:
            raise RuntimeError(
                '%s rejected: remote returned no valid frame just now '
                '(check transmitter/link)' % action)
        if inp.stop_pressed:
            raise RuntimeError('%s rejected: K4 (stop) is held right now'
                               % action)
        return inp, now

    def enable(self):
        """Strict enable. Walking needs 4 enabled/position/calibrated joints."""
        inp, now = self._live_input('enable')
        state = self.ctrl.enable()
        # Feed the live frame so recenter observation starts from the real
        # current lever positions, not from an assumption of center.
        self.ctrl.update(inp, now)
        return state

    def enable_debug(self):
        """Debug enable with incomplete output (marked on every action)."""
        inp, now = self._live_input('enable_debug')
        state = self.ctrl.enable_debug()
        self.ctrl.update(inp, now)
        return state

    def recover(self):
        """After STOPPED/FAULT: live re-read + K4 gate + recenter required."""
        inp, now = self._live_input('recover')
        state = self.ctrl.recover()
        self.ctrl.update(inp, now)
        return state

    def stop(self):
        self.ctrl.stop('operator stop')
        return self.ctrl.state

    def release(self):
        """PWM off: stops the pulse signal. This does NOT cut servo power -
        only a physical switch does; servos may still be back-drivable."""
        self.ctrl.release_output()
        return self.ctrl.state


def start(cfg=None, link=None):
    """Create the board session without touching the remote.

    Pass link=RcLink() (or let run() create it) when the remote is needed.
    """
    return BoardSession(build_controller(cfg or config), cfg or config, link)


def _sleep_ms(ms):
    if hasattr(time, 'sleep_ms'):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


# Set by run()/resume(); the REPL handle between Ctrl-C pauses.
SESSION = None


def pause(session):
    """Ctrl-C semantics for the run() loop.

    - An ACTIVE GAIT IS CANCELLED (STOPPED, pose held, trajectory cleared):
      resuming the loop can never continue the interrupted step by itself.
      Getting back to READY requires an explicit recover() + recenter.
    - While paused NOTHING POLLS: K4 and software link-loss detection DO NOT
      run. Held output is NOT under remote protection - the operator is.
    """
    if session.ctrl.state == states.WALKING:
        session.ctrl.stop('paused by Ctrl-C')
    return session


def run(cfg=None, link=None, session=None):
    """Blocking operator loop. Ctrl-C PAUSES via pause() (active gait
    cancelled, torque output held but NOT remote-protected); the session is
    stored in main_v02.SESSION so the operator can enable/recover/release
    from the REPL, then main_v02.resume() continues the loop.

    resume() is NOT enable and NOT recover: it only re-enters the loop.

    Any OTHER exception releases the output (PWM off) before re-raising -
    the process never dies silently with unclear output state.
    """
    global SESSION
    session = session or SESSION or start(cfg, link=link)
    if session.link is None:
        session.link = link or RcLink()
    SESSION = session
    print('v02 loop start: DRIVER=%s, frames flowing; enable is MANUAL '
          '(Ctrl-C to pause, then SESSION.enable())' % session.cfg.DRIVER)
    try:
        while True:
            t0 = timeutil.now_ms()
            session.poll()
            elapsed = timeutil.diff_ms(timeutil.now_ms(), t0)
            _sleep_ms(max(1, session.cfg.LOOP_MS - elapsed))
    except KeyboardInterrupt:
        pause(session)
        print('v02 loop paused: state=%s. While paused K4 and link-loss '
              'detection DO NOT run; held output is NOT remote-protected.'
              % session.ctrl.state)
        print('  SESSION.enable() / SESSION.recover() / SESSION.stop(); '
              'SESSION.release() = PWM off (servo power stays on); '
              'main_v02.resume() to continue (resume is NOT recover)')
        return session
    except Exception as exc:
        session.release()
        print('v02 loop CRASHED: %r; output released (PWM off). '
              'Investigate before restarting.' % exc)
        raise


def resume():
    """Re-enter the run() loop for the paused session. This is ONLY the
    loop - not an enable, not a recover."""
    if SESSION is None:
        raise RuntimeError('no paused session: call main_v02.run() first')
    return run(session=SESSION)


def main():
    run()


if __name__ == '__main__':
    main()
