"""bench_v02.py - 台架操作脚本（阶段A交付，五类入口，板上 REPL 使用）。

IMPORT-SAFE: importing this module creates NO PWM object, NO remote link and
never moves anything - every action lives behind an explicit function.

Channels are ALWAYS chosen through the joint name -> port/gpio map in
config.JOINTS. No script ever guesses a servo by list position.

Five entries (each accepts cfg=/link=/session= injection for PC tests; on
the board call them without arguments):
    bench_v02.diag()                  # 1 read-only: capability report,
                                      #   no link, no driver, no PWM
    bench_v02.monitor()               #   (remote watch without PWM)
    bench_v02.joint('right_hip', 5,
                    confirmed=True)   # 2 supported single joint, |deg|<=10,
                                      #   ends at stance with PWM off
    bench_v02.demo3()                 # 3 incomplete-output demo: refuses to
                                      #   run when nothing is missing, never
                                      #   reports a "full gait success"
    bench_v02.gait()                  # 4 full four-joint step: strict
                                      #   enable, refuses while incomplete
    bench_v02.remote_gait()           # 5 full flow on the live remote
                                      #   (run/pause/enable/resume/release)

Every moving entry prints its range, duration and end behaviour BEFORE the
first pulse and requires confirmed=True (robot supported, power switch at
hand). Driver 'sim' is refused for moving entries unless allow_sim=True, so
a PC-only driver can never be mistaken for real servo motion.

Board-compatible: no os.path / sys.path, no f-strings, no machine import at
module level.
"""
import time

import config
import controller
import gait_planner
import input_adapter
import joint_model
import states
import timeutil
from drivers import create_driver
from main_v02 import BoardSession, RcLink, _sleep_ms


def _build(cfg):
    jm = joint_model.JointModel(cfg)
    driver = create_driver(jm, cfg)
    ctrl = controller.Controller(cfg, jm, gait_planner.GaitPlanner(cfg),
                                 driver, log=_print_log)
    return jm, driver, ctrl


def _print_log(msg):
    print('  [v02] %s' % msg)


def _require_confirmed(confirmed):
    if not confirmed:
        raise RuntimeError('bench move refused: pass confirmed=True only '
                           'with the robot SUPPORTED and the power switch '
                           'at hand')


def _refuse_sim_driver(cfg, allow_sim):
    if cfg.DRIVER == 'sim' and not allow_sim:
        raise RuntimeError('bench move refused: DRIVER=%r is the PC-only '
                           'simulation driver - servos would NOT move. On '
                           'the board use DRIVER=\'cb1_pwm\', or pass '
                           'allow_sim=True for a pure software rehearsal.'
                           % cfg.DRIVER)


# --- 1. read-only diagnostics -------------------------------------------
def diag(cfg=config):
    """Print the joint capability report and walking gate. Touches nothing:
    no RcLink, no driver, no PWM. Safe any time."""
    jm = joint_model.JointModel(cfg)
    blockers = jm.walk_blockers()
    print('bench diag: DRIVER=%r' % cfg.DRIVER)
    print('  %-11s %-3s %-5s %-8s %-11s %-6s %s'
          % ('joint', 'port', 'gpio', 'enabled', 'actuator', 'calib', 'range'))
    for name in cfg.JOINT_ORDER:
        j = cfg.JOINTS[name]
        print('  %-11s %-3s %-5d %-8s %-11s %-6s %.0f..%.0f (center %.1f)'
              % (name, j['port'], j['gpio'], j['enabled'], j['actuator'],
                 j['calibrated'], j['min'], j['max'], j['center']))
    if blockers:
        print('  walking: BLOCKED - %s' % '; '.join(blockers))
        print('  -> use demo3() for an explicitly incomplete-output demo')
    else:
        print('  walking: all four joints enabled/position/calibrated')
    return blockers


# --- 2. remote monitoring without PWM -----------------------------------
def monitor(link=None, cfg=config, ticks=None, tick_ms=200):
    """Watch left/right levers and K4. NO driver is created, so NO PWM can
    ever come out. Ctrl-C (or ticks limit) ends it. Also note: this only
    shows what rc_slave_data returns right now; a cached old frame after a
    physical link loss is indistinguishable (no seq / rx timestamp).
    """
    if link is None:
        link = RcLink()
    print('bench monitor: reading the remote, PWM impossible here. '
          'Ctrl-C to stop.')
    try:
        i = 0
        while ticks is None or i < ticks:
            inp = input_adapter.from_rc(link.read(), timeutil.now_ms(), cfg)
            print('  L=%+.2f R=%+.2f K4=%s link=%s'
                  % (inp.left, inp.right,
                     'PRESSED' if inp.stop_pressed else 'up',
                     'ok' if inp.connected else 'NONE'))
            _sleep_ms(tick_ms)
            i += 1
    except KeyboardInterrupt:
        print('bench monitor: stopped (no PWM existed at any time)')
    return None


# --- 3. supported single-joint test -------------------------------------
def joint(name, deg, cfg=config, confirmed=False, allow_sim=False,
          hold_ms=800):
    """Move ONE named joint to a small offset and back, then PWM off.

    - deg: bench range is ±10 degrees max, and inside the joint limits.
    - Requires enabled + 'position' for that joint; a disabled channel or a
      continuous servo is refused loudly (never silently skipped).
    - End behaviour: back to all-zero stance, hold briefly, PWM off.
    """
    if name not in cfg.JOINT_ORDER:
        raise ValueError('unknown joint %r; choose from %s'
                         % (name, cfg.JOINT_ORDER))
    if abs(deg) > 10:
        raise RuntimeError('bench move refused: |deg|=%s exceeds the ±10 '
                           'degree bench range' % deg)
    j = cfg.JOINTS[name]
    if not j.get('enabled', True):
        raise RuntimeError('bench move refused: %s (%s/GPIO%d) is disabled '
                           'in config - fix config first, never bypass'
                           % (name, j['port'], j['gpio']))
    if j['actuator'] != 'position':
        raise RuntimeError('bench move refused: %s is a %r actuator and '
                           'must never receive a position command'
                           % (name, j['actuator']))
    _require_confirmed(confirmed)
    _refuse_sim_driver(cfg, allow_sim)
    jm, driver, _ = _build(cfg)
    idx = cfg.JOINT_INDEX[name]
    pose = [0.0] * len(cfg.JOINT_ORDER)
    pose[idx] = float(deg)
    jm.servo_angles(pose)   # limit check before any pulse
    print('bench joint: %s (%s/GPIO%d) -> %+.1f deg, hold %d ms, then back '
          'to stance and PWM off' % (name, j['port'], j['gpio'], deg,
                                     hold_ms))
    try:
        driver.write(pose)
        _sleep_ms(hold_ms)
        driver.write([0.0] * len(cfg.JOINT_ORDER))
        _sleep_ms(hold_ms)
    finally:
        driver.release()
        print('bench joint: done, PWM off (servo power stays on)')
    return driver   # returned for inspection/logging; released either way


# --- shared scripted step ------------------------------------------------
def _scripted_step(side, ctrl, cfg, total_ms=2600, tick_ms=20):
    """One step driven by manual inputs (no remote involved), real clock."""
    t0 = timeutil.now_ms()
    i = 0
    while timeutil.diff_ms(timeutil.now_ms(), t0) < total_ms:
        push = 0.9 if timeutil.diff_ms(timeutil.now_ms(), t0) < 120 else 0.0
        inp = input_adapter.from_manual(
            push if side == 'left' else 0.0,
            push if side == 'right' else 0.0)
        ctrl.update(inp, timeutil.now_ms())
        _sleep_ms(tick_ms)
        i += 1
    return i


def _run_demo(kind, side, cfg, allow_sim, confirmed, total_ms=2600):
    _require_confirmed(confirmed)
    _refuse_sim_driver(cfg, allow_sim)
    jm, driver, ctrl = _build(cfg)
    blockers = jm.walk_blockers()
    try:
        if kind == 'demo3':
            if not blockers:
                raise RuntimeError('demo3 refused: output is COMPLETE - '
                                   'use gait() for the real four-joint step')
            ctrl.enable_debug()   # marks every action as incomplete
            print('bench demo3: INCOMPLETE OUTPUT (%s). Command-sequence '
                  'check ONLY - not a gait, no stance/walk claim.'
                  % '; '.join(blockers))
        else:
            if blockers:
                raise RuntimeError('gait refused: walking needs 4 enabled, '
                                   'position-type, calibrated joints: %s'
                                   % '; '.join(blockers))
            ctrl.enable()
            print('bench gait: strict enable ok; ONE scripted %s step '
                  '(~1.8 s), then PWM off' % side)
        _scripted_step(side, ctrl, cfg, total_ms=total_ms)
        print('bench %s: final state=%s' % (kind, ctrl.state))
    finally:
        ctrl.release_output()
        print('bench %s: PWM off (servo power stays on)' % kind)


# --- 4. incomplete three-joint demo --------------------------------------
def demo3(cfg=config, allow_sim=False, confirmed=False, total_ms=2600):
    """Three-joint (missing left ankle) command-sequence demo. Refuses when
    nothing is missing, runs enable_debug, marks output incomplete, and
    never claims a stance or walk success."""
    _run_demo('demo3', 'left', cfg, allow_sim, confirmed, total_ms)


# --- 5. full four-joint gait ---------------------------------------------
def gait(cfg=config, allow_sim=False, confirmed=False, side='left',
         total_ms=2600):
    """ONE scripted four-joint step after a strict enable. Refused loudly
    while any joint is missing/uncalibrated."""
    if side not in ('left', 'right'):
        raise ValueError("side must be 'left' or 'right'")
    _run_demo('gait', side, cfg, allow_sim, confirmed, total_ms)


# --- convenience: the full documented remote flow ------------------------
def remote_gait(cfg=config, link=None):
    """Run the operator loop for live remote walking (left lever = left
    step, right = right). This is just main_v02.run() with a bench banner;
    pause/enable/recover/release semantics are documented in main_v02."""
    import main_v02
    print('bench remote_gait: left lever = LEFT step, right = RIGHT step; '
          'one push = one step; K4 stops; Ctrl-C pauses.')
    return main_v02.run(cfg, link=link)
