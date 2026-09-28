"""Single-step gait planner: five phases, first/alternate/same-side.

Phases for stepping with foot F (support = opposite foot). Targets are pose
offsets [left_hip, right_hip, left_ankle, right_ankle] relative to stance.
Let S = GAIT['step_sign_left'/'step_sign_right'] for the stepping side and
A_L/A_R = GAIT['ankle_sign_left'/'ankle_sign_right'] (per side: the mirrored
ankle install - S2+=toe up, S4+=toe down, observed 2026-09-23 - means one
shared sign would tilt the two feet in OPPOSITE spatial directions). lh, rh
are the CURRENT commanded hip offsets of this step's start pose (each hip
interpolates from its own value - never assume both hips are equal, e.g.
after a mid-step stop froze them apart).

1. prepare       ankles return to stance; each hip HOLDS its current value.
                 Intent: clean starting contact before any weight moves.
2. weight_shift  hips hold; LEFT ankle leans S*A_L*lean, RIGHT ankle leans
                 S*A_R*lean. Intent: transfer body weight onto the support
                 foot (the per-side signs are what make both feet tilt the
                 same spatial way on this mirrored install).
3. unload_swing  MAIN HIP SWING happens here: both hips go to S*hip_swing
                 while the stepping ankle tilts further to S*A_side*(lean+lift)
                 (support ankle holds its lean value). Intent: unload the
                 stepping foot and carry it to the step bias in one smooth
                 motion.
4. land          hips HOLD S*hip_swing (the swing is NOT repeated here);
                 both ankles return to 0. Intent: stepping foot settles
                 down onto the ground under the new hip bias.
5. stabilize     hold the whole end pose [S*hip, S*hip, 0, 0]. Intent: a
                 quiet moment that leaves the exact bias the NEXT step
                 (opposite side) will start from.

DISCLAIMER: this sequencing is a design choice for a no-knee Otto; it is
NOT proven to balance or to walk. It exists so live bench tests change one
thing at a time. Same-side repetition stays explicitly rejected: a foot
that just finished needs an extra preparation strategy that v02 does not
implement (see same_side_strategy).

Signs are configuration on purpose: the mirrored hip installation means
electrical sign and spatial direction agree only after live observation;
flip step_sign_* / ankle_sign_* in config, never the planner.
"""

import trajectory


class SameSideNotSupported(Exception):
    """Repeated same-side steps need an extra preparation strategy."""


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
        """Extension point for repeated same-side steps. v02: unsupported."""
        return 'not_supported'

    def plan_step(self, side, current_pose, last_foot, jm=None):
        """Build the five-phase Trajectory from the actual current pose."""
        if side not in ('left', 'right'):
            raise ValueError(side)
        if side == last_foot:
            strategy = self.same_side_strategy(side, last_foot)
            if strategy == 'not_supported':
                raise SameSideNotSupported(
                    'same-side %s step needs extra preparation; not in v02'
                    % side)
        s = self.step_signs[side]
        a_side = self.ankle_signs[side]
        # Per-hip current values: never collapse both hips into one number.
        lh, rh = current_pose[0], current_pose[1]
        lean_l = s * self.ankle_signs['left'] * self.lean
        lean_r = s * self.ankle_signs['right'] * self.lean
        stepping_ankle = s * a_side * (self.lean + self.lift)
        stepping_idx = 2 if side == 'left' else 3
        swing_ankles = [lean_l, lean_r]
        swing_ankles[stepping_idx - 2] = stepping_ankle
        d = self.durations
        segments = [
            # name, duration, [left_hip, right_hip, left_ankle, right_ankle]
            ('prepare',      d['prepare'],      [lh, rh, 0.0, 0.0]),
            ('weight_shift', d['weight_shift'], [lh, rh, lean_l, lean_r]),
            ('unload_swing', d['unload_swing'], [s * self.hip, s * self.hip,
                                                 swing_ankles[0],
                                                 swing_ankles[1]]),
            ('land',         d['land'],         [s * self.hip, s * self.hip,
                                                 0.0, 0.0]),
            ('stabilize',    d['stabilize'],    [s * self.hip, s * self.hip,
                                                 0.0, 0.0]),
        ]
        return trajectory.Trajectory(segments, current_pose, joint_model_ref=jm)
