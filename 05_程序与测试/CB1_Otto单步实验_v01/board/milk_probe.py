"""Read-only firmware / remote diagnosis. Never creates PWM."""
def info():
    import sys, os
    print(sys.implementation)
    print(os.uname())
    print('Root files:', os.listdir('/'))
    try:
        import rc_module
        print('RC APIs:', dir(rc_module))
        print('Pair index:', rc_module.rc_index())
    except ImportError:
        print('rc_module unavailable: preserve CB1 firmware; do not flash generic firmware.')

def monitor(seconds=15):
    import rc_module, time
    if rc_module.rc_slave_init() is False:
        raise RuntimeError('RC init failed')
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < seconds*1000:
        print(rc_module.rc_slave_data())
        time.sleep_ms(100)

