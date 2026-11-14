"""Otto-faithful continuous gait generator (pure math, board-safe).

Otto firmware (OttoDIYLib Otto.cpp walk/turn): both hips get the SAME sine
(mirrored installs turn it into scissor legs), both ankles get the SAME
sine lagging the hips by 90 degrees plus a small per-side bias - that phase
relation IS the weight shift. Direction is chosen purely by the ankle
phase sign (+90 lag = forward, -90 = backward); turning by ASYMMETRIC hip
amplitudes (30/10 in Otto), never by different phases.

    hip_l =  (HIP - turn_split*max(0,turn))  * scale * sin(phase)
    hip_r =  (HIP - turn_split*max(0,-turn)) * scale * sin(phase)
    ankle_l = ANKLE * scale * sin(phase - dir*90deg) + BIAS * scale
    ankle_r = ANKLE * scale * sin(phase - dir*90deg) - BIAS * scale

dir = +1 forward, -1 backward. scale ramps 0..1 (drive strength); the
whole waveform - including the bias - scales with it, so scale 0 is the
calibrated flat stance. Amplitudes never get per-point clipped: the turn
split is additive on the hip amplitudes and sized to stay inside limits.

Angles are offsets from stance (degrees); the mirrored install lives in
the servo mapping, NOT here.
"""
import math


def pose_offsets(phase_rad, scale, hip_amp, ankle_amp, bias,
                 turn=0.0, turn_split=5.0, direction=1.0, yaw_trim=0.0):
    """One sample of the four-joint offset pose at continuous phase.

    turn in [-1, 1]: the amplitudes split DOWNWARD from hip_amp - the
    scissor makes BOTH hips hit the backward extreme, so hip_amp must be
    the backward limit (70 deg => 20); turning subtracts from one side
    (Otto 30/10 style: both sides at or below max). turn=+1 shrinks the
    LEFT amplitude; which physical way that curves is empirical - flip the
    session's turn sign if it arcs the wrong way.
    direction: +1 forward (ankle lags hip 90 deg), -1 backward (leads 90).
    """
    # yaw_trim biases the amplitude split (straight-line yaw correction)
    # but NEVER touches the ankle flip: the flip follows the user's raw
    # differential only - feeding a small trim into the flip made straight
    # walks run backwards (2026-09-24 late regression).
    split_turn = max(-1.0, min(1.0, turn + yaw_trim))
    hip_l = (hip_amp - turn_split * max(0.0, split_turn)) * scale * math.sin(phase_rad)
    hip_r = (hip_amp - turn_split * max(0.0, -split_turn)) * scale * math.sin(phase_rad)
    # Ankle coordination is IDENTICAL for both turn directions - Otto
    # turn only swaps the hip amplitudes (30/10 vs 10/30) and keeps the
    # same -90 deg ankle lag. A 180-deg ankle flip added when turn>0
    # (removed 2026-09-25) silently turned one side's gait into the
    # BACKWARD ankle waveform, so both turn commands yawed the same way.
    ankle = ankle_amp * scale * math.sin(phase_rad -
                                         direction * math.pi / 2.0)
    return [hip_l, hip_r, ankle + bias * scale, ankle - bias * scale]
