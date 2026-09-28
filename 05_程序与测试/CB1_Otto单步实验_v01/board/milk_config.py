# Edit on PC, then re-upload. Defaults intentionally forbid gait PWM.
CALIBRATED = False
# 2026-09-22 jog session verified: levers drive S1/S4 via milk_jog.py.
REMOTE_MAPPING_VERIFIED = True
# Supply and pin order must be checked separately from the program.
# 2026-09-22 live mapping (user confirmed): S1=left_hip, S2=left_ankle,
# S3=right_hip, S4=right_ankle. ALL FOUR SERVOS ARE FUNCTIONAL. S2 currently
# holds a 360-degree CONTINUOUS servo: never send it non-center pulses until
# a 180-degree PG001 is installed there (center pulse = stop, not guaranteed
# without calibration). Test scripts must skip joint index 2 entirely.
JOINTS = [
    dict(name='left_hip', pin=3, center=90, trim=0, direction=1, min=65, max=115),
    dict(name='right_hip', pin=1, center=90, trim=0, direction=1, min=65, max=115),
    dict(name='left_ankle', pin=2, center=90, trim=0, direction=1, min=65, max=115),
    dict(name='right_ankle', pin=0, center=90, trim=0, direction=1, min=65, max=115),
]
PULSE_AT_0_US = 500
PULSE_AT_180_US = 2500
HIP = 8
LEAN = 7
LIFT = 3
PHASE_MS = 450
LEFT_SIGN = 1  # Determine with supported, small-angle weight-shift test.
# Official rc tuple: L1,L2,L3,R1,R2,R3,K1,K2,K3,K4
# 2026-09-22 measured: left lever=L1 rest~1959, right lever=R1 rest~1797,
# only one physical button wired to K4, pressed reads 0. L2 stuck at 0 (unused).
LEFT_CHANNEL = 0   # Measured: left lever
RIGHT_CHANNEL = 3  # Measured: right lever (full sweep 0..4073 observed)
LEFT_CENTER = 1959
RIGHT_CENTER = 1797
LEFT_SPAN = 1800
RIGHT_SPAN = 1800
LEFT_DIRECTION = 1
RIGHT_DIRECTION = 1
ATTACK_BUTTON = 9  # K4 is the only physical button on this transmitter.
ENABLE_BUTTON = 9  # Same button doubles as enable until more buttons exist.
STOP_BUTTON = None  # No dedicated stop button; link loss disarms. Never a
                    # shared index while ENABLE uses the same button, or a
                    # hold-to-enable would instantly stop/disarm itself.
BUTTON_ACTIVE = 0  # Measured: pressed button reads 0.
LINK_TIMEOUT_MS = 250
LOOP_MS = 20
# Never enable until wiring, servo type, stop pulse and clearance verified.
ATTACK_ENABLED = False
ATTACK_PIN = 21    # D1 signal candidate; not a power pin.
ATTACK_MODE = 'position'  # 'position' PG001; 'continuous' only verified type.
ATTACK_REST_US = 1500
ATTACK_HIT_US = 1650
ATTACK_STOP_US = 1500
ATTACK_RUN_US = 1580
ATTACK_MAX_MS = 700
