"""Blue palm 2.0: D2/GPIO20. Existing D1 profile remains unchanged.

Other parameters inherit the working palm profile; the new remote still
needs physical calibration after assembly. Import creates no outputs.
"""
import robot_remote
import palm_remote_ready as original

ATTACK_KIND = 'palm'
MAPPING = dict(original.MAPPING)
PALM = dict(original.PALM)
PALM['gpio'] = 20

def run(seconds=30, mode='both', trace=False):
    return robot_remote.run(seconds=seconds, mode=mode, mapping=MAPPING,
                            trace=trace, attack_kind=ATTACK_KIND, palm_cfg=PALM)
