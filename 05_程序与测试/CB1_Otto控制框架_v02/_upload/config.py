"""CB1_Otto控制框架_v02 configuration.

Pure PC-editable file. DRIVER stays 'sim' until bench wiring is verified;
'cb1_pwm' is only for the microcontroller and imports machine lazily.

Joint semantics: algorithm outputs offsets (degrees) from the calibrated
stance for joints in JOINT_ORDER. GPIO mapping, mirrored direction, center
and limits are handled ONLY here and in joint_model. Never guess a servo by
list position in test scripts; access by name or via the explicit port map.

Measured 2026-09-22 (see v01 现场调试记录): S1=left_hip(GPIO3),
S3=right_hip(GPIO1), S4=right_ankle(GPIO0). On 2026-09-23 the 360-degree
placeholder in S2(GPIO2) was swapped for a 180-degree position servo
(PG001). ALL FOUR joints were centered (90 deg horn lock) and user-
observed that same day: directions recorded in 逐关节安装记录表, +-10 deg
range sweeps done, calibrated set True after user confirmation.

ACTUATOR CAPABILITY FIELDS (per joint, drive everything; no driver-side
hardcoding):
- enabled:      channel is wired and meant to be commanded at all.
                Disabled channels NEVER get a PWM object.
- actuator:     'position' (servo angle) | 'continuous' (speed servo, which
                must never receive a position command through this stack).
- calibrated:   center/trim/direction verified on the real robot.
Enabling WALKING requires all four joints to be enabled + 'position' +
calibrated; otherwise enable() is rejected loudly. PC simulation uses the
separate virtual profile in sim_config.py and never edits these facts.
The S2 swap to PG001 was done 2026-09-23 as a config-only change
(enabled=True, actuator='position'); calibrated flips to True per joint
only after live direction/range verification.
"""

DRIVER = 'cb1_pwm'  # 'sim' | 'cb1_pwm'

JOINT_ORDER = ['left_hip', 'right_hip', 'left_ankle', 'right_ankle']

JOINTS = {
    # Calibrated 2026-09-23 evening (user present): electrical center 90 deg
    # locked by horn re-seat; directions observed; +-10 deg sweeps clean
    # 2026-09-24 evening re-sweep: S1 backward clean to -20, S3 forward
    # clean to +20 (the old -10 jam disappeared after the horn re-seat),
    # so hips run 70/115 now.
    'left_hip':    dict(port='S1', gpio=3, center=90.0, trim=0.0, direction=1,
                        min=55.0, max=125.0,
                        enabled=True, actuator='position', calibrated=True),
    'right_hip':   dict(port='S3', gpio=1, center=90.0, trim=0.0, direction=1,
                        min=55.0, max=125.0,
                        enabled=True, actuator='position', calibrated=True),
    # PG001 (180-degree position) installed and centered 2026-09-23.
    # Ankle limits widened to +-30 (60/120) after a clean live sweep to
    # +-35 on BOTH ankles (user-observed 2026-09-24; no jam/noise).
    'left_ankle':  dict(port='S2', gpio=2, center=90.0, trim=0.0, direction=1,
                        min=55.0, max=125.0,
                        enabled=True, actuator='position', calibrated=True),
    'right_ankle': dict(port='S4', gpio=0, center=90.0, trim=0.0, direction=1,
                        min=55.0, max=125.0,
                        enabled=True, actuator='position', calibrated=True),
}

JOINT_INDEX = {name: i for i, name in enumerate(JOINT_ORDER)}

# --- Remote mapping (measured 2026-09-22 on the CB1 transmitter) ---
# Official frame: [L1,L2,L3,R1,R2,R3,K1,K2,K3,K4]
REMOTE = dict(
    # 2026-09-24 evening: user confirmed the old mapping had left/right
    # SWAPPED relative to the physical transmitter - the physically LEFT
    # stick is channel 3, the RIGHT stick is channel 0. Both increase when
    # pushed forward (ch3 fwd->4072/back->0, ch0 fwd->4072/back->0).
    left_channel=3, right_channel=0,
    left_center=1797, right_center=1959,   # measured resting ADC, NOT 2048
                                            # (centers follow the channels
                                            # after the 2026-09-24 swap)
    left_span=1800, right_span=1800,
    left_direction=1, right_direction=1,
    stop_button=None,                       # K4 has NO function (user
                                            # decision 2026-09-24 evening).
                                            # Nothing reads it: no remote
                                            # button stops the walk; the
                                            # physical power switch and
                                            # link-loss protection are the
                                            # only stops.
    button_active=0,                        # pressed reads 0
    # HONEST LIMITATION: rc_slave_data() exposes no sequence number or receive
    # timestamp, so a stale cached frame cannot be distinguished from a fresh
    # one and timeout_ms CANNOT be applied without faking freshness. We do not
    # fake it: a frame of None means the link is down immediately, and we
    # never infer staleness from unchanged lever values. If a future firmware
    # exposes rx timing, wire it here.
    timeout_ms=None,
)

# --- Attack control (palm rotation on D1/GPIO21) ---
# Third stick, channel 2 (official frame L3), SELF-CENTERING (user
# confirmed 2026-09-26 - an earlier "not self-centering" note was wrong).
# Full range 0..4071; center=1860 is the 2026-09-24 reference rest value.
# Palm actuator: 360-degree CONTINUOUS rotation servo - the command is
# speed (direction + magnitude), never an angle. pulse 1500us = stop,
# 1600us verified spinning (one direction), 1400us assumed reverse.
ATTACK = dict(
    enabled=True,       # BOARD VARIANT: D1 wired, field-verified pulses
                        # after PC tests pass and D1 wiring is confirmed
    actuator='continuous',
    channel=2,
    center=1860,        # rest reference; recalibrate via neutral_us, not here
    span=1800,
    direction=1,        # flip to -1 if the user reports reversed sides
    gpio=21,            # D1 pin
    freq_hz=50,
    neutral_us=1500,    # stop pulse; calibrate if the palm crawls
    delta_us=200,       # fixed speed: 1300/1700us - VERIFIED spinning both
                        # ways on 2026-09-26 (100us was too weak to move)
    enter_deadband=0.15,  # stick past this starts the palm
    exit_deadband=0.10,   # back inside this stops it (hysteresis)
    reverse_dwell_ms=150, # neutral dwell before reversing direction
)

# --- Otto continuous gait (otto_session / otto_oscillator) ---
# Amplitudes are uniformly SCALED by the drive factor (0..1), never clipped
# per-point, so the waveform shape survives at any drive level.
# hip must dominate (Otto: 30/20); our hip limits are 70/115 (+-20/+25) and
# ankles 55/125 (+-35), so hip 20 / ankle 20 / bias 4 fits everywhere.
OTTO = dict(
    hip_amp=30.0,        # backward limit is -20 (hip min 70); 19 leaves
                         # float margin. Turning splits DOWNWARD from here.
    ankle_amp=20.0,
    bias=4.0,            # electrical: left +4 (toe up), right -4 (toe up):
                         # both feet biased toward heel contact, matching
                         # the stance-feet-toe-up weight-transfer physics
    period_ms=1000,      # one full cycle = two steps (Otto default T)
    ramp_ms=500,         # drive factor 0<->1 ramp: no snap on start/stop
    drive_threshold=0.4, # stick past this (normalized) counts as engaged
    steer_trim=0.2,      # straight-walk yaw bias. The robot drifted RIGHT
                         # on straight walks (user obs 2026-09-24 late);
                         # positive trims toward the opposite side. If it
                         # now drifts left, lower/flip this number.
    turn_split=20.0,     # hip amplitude split for the arc. Otto turn uses
                         # a 30/10 (3:1) ratio - a 5-degree split was live-
                         # tested invisible (2026-09-24 late). 19/0 (pure pivot on one leg) is
                         # the strongest arc available inside the -20 deg
                         # backward hip limit.
)

# --- Command mapping ---
STEP_THRESHOLD = 0.55     # forward push past this issues one request
RECENTER_BAND = 0.20      # both levers inside this re-arms triggering
BUSY_POLICY = 'drop'      # requests during a step are dropped, never queued

# --- Loop-timing safety ---
# The loop period is 20 ms and the shortest gait phase is 250 ms. A single
# update advancing more than 500 ms means >=25 lost cycles: letting the
# time-based trajectory consume that would skip several phases and jump the
# commanded pose far along its path in one tick. So >500 ms counts as a stall
# (fault while walking, reset when idle) instead of being forwarded.
STALL_MS = 500

# --- Gait parameters (small calibration starting points, NOT walk-proven) ---
# Nothing here is claimed to balance or walk; signs are live-calibration
# knobs because the mirrored installation makes electrical sign != spatial
# direction until confirmed on the robot.
GAIT = dict(
    hip_swing=20.0,       # hip offset magnitude, degrees. Otto firmware
                          # uses 30; ours set to 20 first (S1 re-swept clean
                          # to -20 and S3 to +20 on 2026-09-24 evening after
                          # the horn re-seat killed the old -10 jam; min/max
                          # now 70/115). The hip must DOMINATE the gait -
                          # at 8 deg the ankle motion visually drowned it.
    lean=20.0,            # weight-shift ankle lean, degrees. Otto uses 20
                          # with +-4 tiptoe bias; our ankles swept clean to
                          # +-35 (limits 55/125) but the ankle is SUPPORT,
                          # not the show - hip dominates (see hip_swing).
    lift=8.0,             # extra unload tilt on the stepping ankle
                          # (Otto-style: swing side toes down ~20; kept
                          # below lean so the foot never lifts higher than
                          # the body leans)
    # v03 (2026-09-24): halved from v02 after live tests - the old 1800 ms
    # step felt disconnected from the lever push. 2026-09-24 evening: with
    # ankle amplitudes at the ceiling the 300 ms swing read "too small"
    # live (flick-by), so unload_swing/land were stretched again - the
    # perceived step size tracks phase DURATION as much as angle.
    phase_prepare_ms=150,
    phase_weight_shift_ms=250,
    phase_unload_swing_ms=450,
    phase_land_ms=300,
    phase_stabilize_ms=150,
    step_sign_left=1.0,   # hip swing direction for a LEFT step (matches the
                          # 2026-09-23 observation: S1+=left leg forward)
    step_sign_right=-1.0, # matches S3+=right leg BACKWARD (mirrored install)
    # Mirrored ankle install (S2+=toe up, S4+=toe down, both observed
    # 2026-09-23) means one shared ankle sign can never tilt both feet the
    # same spatial way: per-side electrical signs, tuned live.
    ankle_sign_left=-1.0,   # FLIPPED 2026-09-24 evening per Otto firmware
                            # physics: the STEPPING foot must tilt TOE-DOWN
                            # (unloaded/lifted) and the SUPPORT foot TOE-UP
                            # (heel contact, bears the weight). With S2+=toe
                            # up / S4+=toe down the old +1/+1 did the exact
                            # opposite - the body weight never transferred,
                            # which is why every gait variant marched in
                            # place. This was the last unverified sign knob
                            # (docs predicted a flip since 2026-09-23).
    ankle_sign_right=-1.0,
)

LOOP_MS = 20
PULSE_AT_0_US = 500
PULSE_AT_180_US = 2500
