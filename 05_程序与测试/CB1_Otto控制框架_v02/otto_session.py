"""Otto continuous-walk session: full control on the proven stack (v05).

Continuous oscillator proven to produce real displacement. Control model
(user spec 2026-09-24 late):

    BOTH sticks the same direction -> WALK that direction (straight);
        push-pull difference between them steers slightly (see steer_trim)
    ONE stick only, any direction -> TURN IN PLACE-ish arc (no travel):
        left fwd / right back = one way, right fwd / left back = other
    release everything             -> ramp down, stand (no snap)

Math per tick (normalized axes, deadband applied):
    same = (l + r) / 2   common mode  -> drive when sticks agree
    diff = (r - l) / 2   differential -> turn
Same-direction sticks: drive = same, turn = diff + steer_trim.
Single stick: drive = 0 (no travel), turn = clamped differential.
The oscillator energy follows "any stick engaged", direction follows the
sign of drive.
"""
import math
import time

import config
import input_adapter
import main_v02
import timeutil
import walk_session
from attack_control import AttackController
from drivers.palm_pwm import PalmPwmDriver
from otto_oscillator import pose_offsets


def _axes(inp, threshold):
    """(drive, turn, engaged) from one UnifiedInput.

    Same-direction sticks: drive = common mode, turn = differential.
    The mechanical yaw bias on straight walks is corrected by
    OTTO['steer_trim'], which offsets the amplitude split only.
    Single stick (either direction): drive = 0 - it TURN, per user spec;
    direction: left-fwd/right-back = one way, right-fwd/left-back = other.
    """
    l = inp.left if inp.connected else 0.0
    r = inp.right if inp.connected else 0.0

    def active(v):
        return v if abs(v) >= threshold else 0.0

    l, r = active(l), active(r)
    if l != 0.0 and r != 0.0 and (l > 0.0) == (r > 0.0):
        return (l + r) / 2.0, max(-1.0, min(1.0, (r - l) / 2.0)), True
    if l != 0.0 or r != 0.0:
        turn = (max(0.0, r) + max(0.0, -l)) - (max(0.0, l) + max(0.0, -r))
        return 0.0, max(-1.0, min(1.0, turn)), True
    return 0.0, 0.0, False


def run(seconds=None, cfg=None, link=None, log=print):
    cfg = cfg or config
    o = cfg.OTTO
    session = main_v02.start(cfg, link=link)
    if session.link is None:
        session.link = link or main_v02.RcLink()
    # Construction is hardware-free for both - safe to hold across finally.
    attack = AttackController(cfg.ATTACK)
    palm = PalmPwmDriver(cfg.ATTACK)
    log('otto_session: %s - hold sticks FORWARD = walk, ONE stick = arc, '
        'BACK = backward, release = stand (period %dms, hip %.0f+/-%.0f, '
        'ankle %.0f)' % ('until power off' if seconds is None else '%.0fs' % seconds,
                         o['period_ms'], o['hip_amp'], o['turn_split'],
                         o['ankle_amp']))
    try:
        if not walk_session.wait_for_frames(session.link, cfg):
            raise RuntimeError('otto_session: no frames - check transmitter')
        session.enable()
        phase = 0.0
        scale = 0.0
        drive_dir = 1.0
        turn = 0.0
        was_walking = False
        t_start = timeutil.now_ms()
        last = t_start
        end = None if seconds is None else t_start + int(seconds * 1000)
        while end is None or timeutil.now_ms() < end:
            now = timeutil.now_ms()
            dt = timeutil.diff_ms(now, last)
            last = now
            raw = session.link.read()          # ONE read shared by both
            inp = input_adapter.from_rc(raw, now, cfg)
            # --- palm first: its stop must not be skipped by the leg
            # logic's continue on link gaps ---
            try:
                pulse = attack.update(raw, now)
                if pulse is None:
                    palm.release()
                else:
                    palm.write_us(pulse)
            except Exception as exc:
                log('otto: palm driver error: %r - releasing' % exc)
                palm.release()
            drive, turn, engaged = _axes(inp, o['drive_threshold'])
            # steer_trim corrects straight-walk yaw only; a turning gait
            # must stay symmetric (30/10 vs 10/30), no trim mixing in
            yaw_trim = o.get('steer_trim', 0.0) if abs(drive) > 0.0 else 0.0
            target = 1.0 if engaged else 0.0
            if scale < target:
                scale = min(target, scale + dt / float(o['ramp_ms']))
            elif scale > target:
                scale = max(target, scale - dt / float(o['ramp_ms']))
            if engaged:
                drive_dir = 1.0 if drive > 0 else (-1.0 if drive < 0
                                                   else 1.0)
            walking = scale > 0.0 and engaged
            if walking:
                if not was_walking:
                    log('otto: walking (dir=%s, phase reset)' %
                        ('fwd' if drive_dir > 0 else 'back'))
                phase += 2.0 * math.pi * dt / float(o['period_ms'])
            elif was_walking:
                log('otto: stopping (ramping down)')
            was_walking = walking
            pose = pose_offsets(phase, scale, o['hip_amp'], o['ankle_amp'],
                                o['bias'], turn=turn,
                                turn_split=o['turn_split'],
                                direction=drive_dir,
                                yaw_trim=yaw_trim)
            session.ctrl.jm.servo_angles(pose)   # limit validation, raises
            session.ctrl.driver.write(pose)
            if not inp.connected:
                main_v02._sleep_ms(50)      # brief link gap: hold, re-read
                continue
            main_v02._sleep_ms(max(1, cfg.LOOP_MS -
                                   timeutil.diff_ms(timeutil.now_ms(), now)))
        log('otto_session: time up, last scale=%.2f' % scale)
    finally:
        try:
            if session is not None:
                session.release()
        finally:
            palm.release()          # D1 released even if the leg release errs
        log('otto_session: PWM off (servo power stays on)')
    return session
