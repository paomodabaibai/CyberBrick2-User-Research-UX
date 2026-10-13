"""Read-only punch stick probe for the second CB1 receiver."""
import time
import rc_module


def run(seconds=12):
    if rc_module.rc_slave_init() is False:
        raise RuntimeError('radio init failed')
    start = time.ticks_ms()
    low = 4096
    high = -1
    frames = 0
    k4_low = 0
    print('ATTACK_PROBE_START: first 2s neutral, then move punch stick')
    while time.ticks_diff(time.ticks_ms(), start) < seconds * 1000:
        raw = rc_module.rc_slave_data()
        if raw is not None and len(raw) == 10:
            value = raw[2]
            low = min(low, value)
            high = max(high, value)
            frames += 1
            if raw[9] == 0:
                k4_low += 1
        time.sleep_ms(20)
    print('ATTACK_PROBE_RESULT', frames, low, high, k4_low)
