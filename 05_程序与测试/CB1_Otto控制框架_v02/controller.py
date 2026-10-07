"""Whole-robot controller: states, request handling, trajectory execution.

Dependency direction (enforced by imports):
input -> command_mapper -> controller -> gait_planner -> trajectory
      -> joint_model -> driver. Nothing upstream touches PWM or angles.

Enable semantics (explicit, never automatic):
- controller.enable() is a deliberate operator/debug action. Valid remote
  frames NEVER enable anything.
- enable() is rejected while the capability report shows walking is not
  possible (disabled/continuous/uncalibrated joints) - missing hardware is
  never hidden. enable_debug() bypasses that but marks every action as an
  incomplete-output debug run.
- After enable() AND after every recover(), the trigger is disarmed: both
  levers must be observed near center before any step request can fire.
- K4 is stop-only. FAULT/STOPPED/reconnect never resume by themselves.
"""

import states as S
import command_mapper as CM
import gait_planner
import joint_model
import timeutil


class Controller:
    def __init__(self, config, joint_model_ref, planner, driver, log=None):
        self.cfg = config
        self.jm = joint_model_ref
        self.planner = planner
        self.driver = driver
        self.log = log or (lambda *a: None)
        self.mapper = CM.CommandMapper(config)
        self.state = S.DISABLED
        self.pose = [0.0] * len(config.JOINT_ORDER)
        self.last_commanded = list(self.pose)
        self.trajectory = None
        self.step_side = None          # foot requested for the current step
        self.support_side = None       # planned support side of current step
        self.last_foot = None          # which foot finished the previous step
        self.phase = None
        self.landed = False            # program state: 'land' phase finished
        self.reason = None
        self.debug_incomplete = None   # blockers list when enable_debug() used
        self._last_update_ms = None
        self._fresh_step = False       # just started: do not count old wait

    # --- internal helpers -------------------------------------------------
    def _clear_action(self):
        """Drop every residue of an interrupted action so a later recovery
        cannot inherit a stale trajectory or phase."""
        self.trajectory = None
        self.phase = None
        self.step_side = None
        self.support_side = None
        self.landed = False

    def _write_pose(self, pose):
        self.jm.servo_angles(pose)  # validate before any output
        self.last_commanded = list(pose)
        self.driver.write(pose)

    def _disarm_trigger(self):
        # Both levers must be seen near center before anything can fire.
        self.mapper.ready = False

    # --- explicit transitions -------------------------------------------
    def _enable_gate(self):
        if self.state == S.FAULT:
            raise RuntimeError('recover() required after fault; not enable()')
        if self.state != S.DISABLED:
            return False
        return True

    def enable(self):
        """Strict enable: refuses unless ALL four joints can walk."""
        if not self._enable_gate():
            return self.state
        blockers = self.jm.walk_blockers()
        if blockers:
            raise RuntimeError(
                'enable rejected (walking needs 4 enabled, position-type, '
                'calibrated joints): %s' % '; '.join(blockers))
        self.state = S.READY
        self._clear_action()
        self._disarm_trigger()
        self._write_pose(self.pose)
        self.log('enabled (stance commanded; recenter required before steps)')
        return self.state

    def enable_debug(self):
        """Debug enable with incomplete output. Every action it produces is
        marked as such - it must never be reported as a full gait."""
        if not self._enable_gate():
            return self.state
        self.debug_incomplete = self.jm.walk_blockers()
        self.state = S.READY
        self._clear_action()
        self._disarm_trigger()
        self._write_pose(self.pose)
        self.log('DEBUG enable: INCOMPLETE OUTPUT - %s; not a full gait'
                 % ('; '.join(self.debug_incomplete) or 'none'))
        return self.state

    def stop(self, reason='stop'):
        if self.state == S.WALKING:
            self.log('stop during %s step: %s' % (self.step_side, reason))
        self._clear_action()
        self.state = S.STOPPED
        self.reason = reason
        # Holds last_commanded pose on purpose. NOT a guarantee of standing.

    def fault(self, reason):
        self._clear_action()
        self.state = S.FAULT
        self.reason = reason
        self.log('FAULT: %s' % reason)

    def recover(self):
        """Explicit recovery after STOPPED/FAULT. Never automatic.
        Re-arms only after levers are seen centered again."""
        if self.state in (S.STOPPED, S.FAULT):
            self._clear_action()
            self.state = S.READY
            self.reason = None
            self._disarm_trigger()
            self.log('recovered to ready (pose held; recenter required)')
        return self.state

    def release_output(self):
        """Separate from stop: hands physical control back (PWM off)."""
        self._clear_action()
        self.driver.release()
        self.state = S.DISABLED
        self.log('output released (servo torque off)')

    # --- stepping --------------------------------------------------------
    def request_step(self, side, backward=False):
        if self.state == S.WALKING:
            self.log('request dropped (%s): step in progress' % side)
            return 'dropped'
        if self.state != S.READY:
            self.log('request rejected (%s): state=%s' % (side, self.state))
            return 'rejected'
        try:
            self.trajectory = self.planner.plan_step(
                side, self.pose, self.last_foot, backward=backward,
                jm=self.jm)
        except joint_model.LimitViolation as exc:
            self.log('request rejected (%s): %s' % (side, exc))
            return 'rejected_limit'
        self.step_side = side
        self.support_side = self.planner.support_side_strategy(side)
        self.state = S.WALKING
        self._fresh_step = True   # pre-request idle time must not count
        self.log('step start %s%s (support %s)%s' %
                 (side, ' BACKWARD' if backward else '', self.support_side,
                  ' [DEBUG incomplete output]' if self.debug_incomplete else ''))
        return 'started'

    # --- periodic update --------------------------------------------------
    def update(self, inp, now_ms):
        if self._last_update_ms is None:
            self._last_update_ms = now_ms
        dt = timeutil.diff_ms(now_ms, self._last_update_ms)
        self._last_update_ms = now_ms
        if dt < 0:
            dt = 0    # clock anomaly: time never moves backwards here
        if dt > self.cfg.STALL_MS:
            # Lost >=25 cycles: refuse to fast-forward the time-based
            # trajectory (it would skip phases and teleport the pose).
            if self.state == S.WALKING and self.trajectory is not None:
                self.fault('update stall %d ms: gait phases would be skipped'
                           % dt)
                return
            dt = 0    # idle stall: nothing in flight, just resume from now

        if self.state == S.DISABLED:
            return
        events = self.mapper.update(inp, busy=(self.state == S.WALKING))
        for ev in events:
            if ev == CM.LINK_LOST:
                self.fault('link lost (no valid frame)')
                return
            if ev == CM.STOP:
                self.stop('K4 pressed')
                continue
            if ev == CM.STEP_LEFT:
                self.request_step('left')
            elif ev == CM.STEP_RIGHT:
                self.request_step('right')
            elif ev == CM.STEP_BACK_LEFT:
                self.request_step('left', backward=True)
            elif ev == CM.STEP_BACK_RIGHT:
                self.request_step('right', backward=True)
            elif ev == CM.REJECTED_CONFLICT:
                self.log('request rejected: both levers forward (conflict)')
            elif ev == CM.DROPPED_BUSY:
                self.log('request dropped: step in progress')
            if self.state == S.FAULT:
                return

        if self.state == S.WALKING and self.trajectory is not None:
            eff_dt = 0 if self._fresh_step else dt
            self._fresh_step = False
            pose, phase, done = self.trajectory.update(eff_dt)
            self._write_pose(pose)
            self.pose = pose
            self.phase = phase
            if not self.landed and phase in (None, 'stabilize') and done:
                self.landed = True
            if done:
                self.last_foot = self.step_side
                self.log('step done %s pose=%s%s' %
                         (self.step_side, [round(x, 2) for x in pose],
                          ' [DEBUG incomplete output]'
                          if self.debug_incomplete else ''))
                self.trajectory = None
                self.step_side = None
                self.support_side = None
                self.phase = None
                self.state = S.READY
