"""Single-step gait planner: five phases, forward/backward, same-side ok.

Phases for stepping with foot F (support = opposite foot). Targets are pose
offsets [left_hip, right_hip, left_ankle, right_ankle] relative to stance.
Let S = GAIT['step_sign_left'/'step_sign_right'] for the stepping side and
A_L/A_R = GAIT['ankle_sign_left'/'ankle_sign_right'] (per side: the mirrored
ankle install - S2+=toe up, S4+=toe down, observed 2026-09-23 - means one
shared sign would tilt the two feet in OPPOSITE spatial directions).

1. prepare       hips RETRACT to 0, ankles return to stance. The retract is
                 what makes repeated SAME-SIDE steps possible (v03): the
                 foot is carried back through center before the next swing,
                 so holding one lever = continuous same-side steps = turn.
                 For alternating steps this is the natural pass-through-
                 center of Otto-style walking.
2. weight_shift  hips hold 0; LEFT ankle leans S*A_L*lean, RIGHT ankle leans
                 S*A_R*lean. Weight moves onto the support foot regardless
                 of forward/backward - the lean direction depends only on
                 the stepping SIDE, never on the step direction.
3. unload_swing  MAIN HIP SWING: both hips go to W*hip_swing where
                 W = S for a forward step and -S for a backward step, while
                 the stepping ankle tilts further to S*A_side*(lean+lift)
                 (support ankle holds its lean value).
4. land          hips HOLD the swing bias; both ankles return to 0.
5. stabilize     hold the end pose. A quiet moment that leaves the bias the
                 NEXT step (either side, either direction) retracts from.

v03 changes (2026-09-24, after live remote-walk validation):
- repeated same-side steps are SUPPORTED via the prepare-phase retract
  (v02 rejected them; the user's control model is hold-to-repeat)
- backward=True plans the same five phases with the hip swing reversed

DISCLAIMER: signs are configuration on purpose: the mirrored hip install
means electrical sign and spatial direction agree only after live
observation; flip step_sign_* / ankle_sign_* in config, never the planner.
"""

import trajectory


class GaitPlanner:
    def __init__(self, config):
        g = config.GAIT
        self.hip = g['hip_swing']
        self.lean = g['lean']
        self.lift = g['lift']
        self.step_signs = {'left': g.get('step_sign_left', 1.0),
                           'right': g.get('step_sign_right', -1.0)}
        # Per-side ankle electrical signs; fall back to a shared legacy
        # ankle_sign if per-side keys are absent.
        legacy = g.get('ankle_sign', 1.0)
        self.ankle_signs = {'left': g.get('ankle_sign_left', legacy),
                            'right': g.get('ankle_sign_right', legacy)}
        self.durations = dict(
            prepare=g['phase_prepare_ms'],
            weight_shift=g['phase_weight_shift_ms'],
            unload_swing=g['phase_unload_swing_ms'],
            land=g['phase_land_ms'],
            stabilize=g['phase_stabilize_ms'],
        )
        self.support_side_strategy = self._default_support_side

    @staticmethod
    def _default_support_side(stepping_side):
        return 'right' if stepping_side == 'left' else 'left'

    def same_side_strategy(self, side, last_foot):
        """v03: same-side repetition retracts through center in prepare."""
        return 'retract'

    def plan_step(self, side, current_pose, last_foot, backward=False,
                  jm=None):
        """Build the five-phase Trajectory from the actual current pose."""
        if side not in ('left', 'right'):
            raise ValueError(side)
        s = self.step_signs[side]
        swing = -s if backward else s
        a_side = self.ankle_signs[side]
        lean_l = s * self.ankle_signs['left'] * self.lean
        lean_r = s * self.ankle_signs['right'] * self.lean
        stepping_ankle = s * a_side * (self.lean + self.lift)
        stepping_idx = 2 if side == 'left' else 3
        swing_ankles = [lean_l, lean_r]
        swing_ankles[stepping_idx - 2] = stepping_ankle
        hip_l = swing * self.hip
        hip_r = swing * self.hip
        d = self.durations
        segments = [
            # name, duration, [left_hip, right_hip, left_ankle, right_ankle]
            ('prepare',      d['prepare'],      [0.0, 0.0, 0.0, 0.0]),
            ('weight_shift', d['weight_shift'], [0.0, 0.0, lean_l, lean_r]),
            ('unload_swing', d['unload_swing'], [hip_l, hip_r,
                                                 swing_ankles[0],
                                                 swing_ankles[1]]),
            ('land',         d['land'],         [hip_l, hip_r, 0.0, 0.0]),
            ('stabilize',    d['stabilize'],    [hip_l, hip_r, 0.0, 0.0]),
        ]
        return trajectory.Trajectory(segments, current_pose, joint_model_ref=jm)
