"""Manual REPL tools. Physically support robot before any call that moves it."""
import milk_config as C
from milk_hw import Output
from milk_core import Gait

class Bench:
    def __init__(self):
        self.out = Output()  # No PWM until explicit command.
        self.gait = Gait(C.HIP,C.LEAN,C.LIFT,C.PHASE_MS,C.LEFT_SIGN)
        self.standing = False

    def joint(self, index, offset=0):
        # Initial trim/center test, even before CALIBRATED flag.
        # Starts selected servo only. Unknown initial shaft position can jump.
        if index not in range(4) or abs(offset)>10:
            raise ValueError('Calibration: index 0..3, offset -10..10 degrees')
        self.out.joint(index, offset)
        self.standing = False

    def off(self):
        self.out.close()
        self.standing = False

    def stance(self):
        if not C.CALIBRATED:
            raise RuntimeError('Calibrate all four joints first')
        self.gait = Gait(C.HIP,C.LEAN,C.LIFT,C.PHASE_MS,C.LEFT_SIGN)
        self.out.pose(self.gait.pose)
        self.standing = True

    def step(self, side):
        import time
        if not C.CALIBRATED:
            raise RuntimeError('Calibrate all four joints first')
        if not self.standing:
            raise RuntimeError('Support robot and call stance() first')
        if not self.gait.start(side):
            print('Rejected: alternate feet, or reset supported stance after stop')
            return
        try:
            last = time.ticks_ms()
            while self.gait.busy:
                time.sleep_ms(20)
                now=time.ticks_ms()
                self.out.pose(self.gait.tick(min(40,time.ticks_diff(now,last))))
                last=now
            print('Finished',side,'pose',self.gait.pose)
        except BaseException:
            self.gait.stop()
            self.out.close()
            self.standing = False
            raise
