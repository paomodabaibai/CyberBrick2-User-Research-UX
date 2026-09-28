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

DRIVER = 'sim'  # 'sim' | 'cb1_pwm'

JOINT_ORDER = ['left_hip', 'right_hip', 'left_ankle', 'right_ankle']

JOINTS = {
    # Calibrated 2026-09-23 evening (user present): electrical center 90 deg
    # locked by horn re-seat; directions observed; +-10 deg sweeps clean
    # EXCEPT left_hip backward jams at -10 -> min pinned to 82 (-8, the
    # largest swing the gait commands).
    'left_hip':    dict(port='S1', gpio=3, center=90.0, trim=0.0, direction=1,
                        min=82.0, max=115.0,
                        enabled=True, actuator='position', calibrated=True),
    'right_hip':   dict(port='S3', gpio=1, center=90.0, trim=0.0, direction=1,
                        min=65.0, max=115.0,
                        enabled=True, actuator='position', calibrated=True),
    # PG001 (180-degree position) installed and centered 2026-09-23.
    'left_ankle':  dict(port='S2', gpio=2, center=90.0, trim=0.0, direction=1,
                        min=65.0, max=115.0,
                        enabled=True, actuator='position', calibrated=True),
    'right_ankle': dict(port='S4', gpio=0, center=90.0, trim=0.0, direction=1,
                        min=65.0, max=115.0,
                        enabled=True, actuator='position', calibrated=True),
}

JOINT_INDEX = {name: i for i, name in enumerate(JOINT_ORDER)}

# --- Remote mapping (measured 2026-09-22 on the CB1 transmitter) ---
# Official frame: [L1,L2,L3,R1,R2,R3,K1,K2,K3,K4]
REMOTE = dict(
    left_channel=0, right_channel=3,
    left_center=1959, right_center=1797,   # measured resting ADC, NOT 2048
    left_span=1800, right_span=1800,
    left_direction=1, right_direction=1,
    stop_button=3,                          # K4 = 4th button; from_rc adds the
                                            # button base offset 6 -> frame[9].
                                            # Stop ONLY: never enables/attacks.
    button_active=0,                        # pressed reads 0
    # HONEST LIMITATION: rc_slave_data() exposes no sequence number or receive
    # timestamp, so a stale cached frame cannot be distinguished from a fresh
    # one and timeout_ms CANNOT be applied without faking freshness. We do not
    # fake it: a frame of None means the link is down immediately, and we
    # never infer staleness from unchanged lever values. If a future firmware
    # exposes rx timing, wire it here.
    timeout_ms=None,
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
    hip_swing=8.0,        # hip offset magnitude, degrees
    lean=7.0,             # weight-shift ankle lean, degrees
    lift=3.0,             # extra unload tilt on the stepping ankle
    phase_prepare_ms=250,
    phase_weight_shift_ms=450,
    phase_unload_swing_ms=450,
    phase_land_ms=350,
    phase_stabilize_ms=300,
    step_sign_left=1.0,   # hip swing direction for a LEFT step (matches the
                          # 2026-09-23 observation: S1+=left leg forward)
    step_sign_right=-1.0, # matches S3+=right leg BACKWARD (mirrored install)
    # Mirrored ankle install (S2+=toe up, S4+=toe down, both observed
    # 2026-09-23) means one shared ankle sign can never tilt both feet the
    # same spatial way: per-side electrical signs, tuned live.
    ankle_sign_left=1.0,
    ankle_sign_right=1.0,
)

LOOP_MS = 20
PULSE_AT_0_US = 500
PULSE_AT_180_US = 2500
