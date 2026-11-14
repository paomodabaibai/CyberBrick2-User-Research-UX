"""Blue palm 2.0: D2/GPIO20. Existing D1 profile remains unchanged.

2026-11-13: dual-axis sticks use L3/R3 Y only; attack R1; held dance K1.
Centres measured with user-confirmed released sticks (79/80 frames).
Import creates no outputs. Walking retains the original 90-degree stance.
"""
import robot_remote
import palm_remote_ready as original

ATTACK_KIND = 'palm'
MAPPING = dict(original.MAPPING)
MAPPING.update(left=2, right=5, attack=3, dance=6,
               left_center=2069, right_center=1924, attack_center=2132)
PALM = dict(original.PALM)
PALM.update(gpio=20, channel=3, center=2132, delta_us=600)  # 2100/900us, matching palm 1.0.
DANCE_LIMITS = (25, 25, 25, 25)  # Restored on user's request after reassembly.

def run(seconds=30, mode='both', trace=False):
    return robot_remote.run(seconds=seconds, mode=mode, mapping=MAPPING,
                            trace=trace, attack_kind=ATTACK_KIND, palm_cfg=PALM,
                            dance_limits=DANCE_LIMITS)
