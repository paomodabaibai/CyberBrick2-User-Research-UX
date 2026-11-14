"""One-shot trial for an immovable S3 horn, NOT a calibrated walking profile.

S3 neutral=180; clip the unavailable half of its waveform at 180.
This changes coordination and can impair displacement/turning.
No attack, no dancing, no radio; successful finish holds the aligned stance.
"""
STANCE = (90.0, 180.0, 90.0, 90.0)  # S1,S3,S2,S4
LIMITS = ((75,105),(165,180),(78,102),(78,102))

def map_pose(offsets):
    half = [v * 0.5 for v in offsets]
    angles = (90 + half[0], 180 + min(0.0, half[1]),
              90 + half[2], 90 + half[3])
    for a, (lo, hi) in zip(angles, LIMITS):
        if not lo - 0.00001 <= a <= hi + 0.00001:
            raise ValueError('limited trial angle outside bounds')
    return angles

def run():
    import machine, time, os
    from robot_remote import WalkMotion, PORTS
    assert machine.unique_id() == bytes([128,241,178,30,179,108]), 'Wrong board'
    assert machine.Pin(10,machine.Pin.IN,None).value() == 0, 'Not receiver'
    assert 'commissioning_hold' in os.listdir('/'), 'Hold missing'
    # Prior assembly hold order differs from oscillator order.
    global _limited_trial_pwms
    old = globals().get('_assembly_hold_pwms')
    if old is None or len(old) != 4:
        raise RuntimeError('Expected existing assembly hold; no motion')
    assert abs(old[2].duty_ns()-2500000)<10000, 'S3 not at 180 stance'
    pwms = [old[i] for i in (0,2,1,3)]
    _limited_trial_pwms = pwms
    def write(pose):
        for p,a in zip(pwms, map_pose(pose)):
            p.duty_ns(int(500+a*2000/180)*1000)
    def phase(motion, milliseconds, engaged, turn, direction):
        start=last=time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(),start)<milliseconds:
            now=time.ticks_ms()
            dt=time.ticks_diff(now,last)
            last=now
            write(motion.step(dt,engaged,turn,direction))
            time.sleep_ms(20)
    try:
        for label,direction,turn in (('FORWARD',1,0),('BACKWARD',-1,0),
                                     ('RIGHT_CANDIDATE',1,-1),('LEFT_CANDIDATE',1,1)):
            print('LIMITED TRIAL',label,'1.5s; S3 165..180 only')
            motion=WalkMotion()
            phase(motion,1500,True,turn,direction)
            phase(motion,600,False,turn,direction)
            write((0,0,0,0))
            time.sleep_ms(600)
        print('DONE: HOLD S1=90 S2=90 S3=180 S4=90; NO ATTACK')
    except BaseException:
        for p in pwms:
            try: p.deinit()
            except Exception: pass
        print('ABORT: ALL LEG PWM RELEASED')
        raise

if __name__ == '__main__':
    run()
