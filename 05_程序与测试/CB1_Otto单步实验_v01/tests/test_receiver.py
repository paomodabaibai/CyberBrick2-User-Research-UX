import sys, pathlib, unittest, types
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'board'))
import milk_receiver as R
import milk_config as C
from milk_hw import Attack

class FakeOutput:
    def __init__(self): self.poses=[]; self.pulses=[]; self.closed=False
    def pose(self,p): self.poses.append(p[:])
    def pulse(self,pin,us): self.pulses.append((pin,us))
    def close(self): self.closed=True

class Integration(unittest.TestCase):
    def execute(self,frames,calibrated=True):
        output=FakeOutput()
        clock=types.SimpleNamespace(now=0)
        def sleep(ms): clock.now+=ms
        clock.sleep_ms=sleep
        clock.ticks_ms=lambda:clock.now
        clock.ticks_diff=lambda a,b:a-b
        it=iter(frames)
        def read():
            try:return next(it)
            except StopIteration:raise KeyboardInterrupt()
        rc=types.SimpleNamespace(rc_slave_init=lambda:True,rc_slave_data=read)
        with patch.dict(sys.modules,{'time':clock,'rc_module':rc}), patch.object(R,'Output',lambda:output), patch.object(C,'CALIBRATED',calibrated), patch.object(C,'REMOTE_MAPPING_VERIFIED',True):
            with self.assertRaises(KeyboardInterrupt if calibrated else RuntimeError): R.run()
        return output

    def test_unverified_no_pwm(self):
        self.assertEqual(self.execute([],False).poses,[])

    def test_no_enable_no_pwm(self):
        out=self.execute([[2048]*6+[1,1,1,1]]*60)
        self.assertEqual(out.poses,[])
        self.assertTrue(out.closed)

    def test_loss_latches_and_reconnection_cannot_resume(self):
        # Build frames from the live config: single button layout, K4 enables.
        buttons=[1,1,1,1]
        if C.ENABLE_BUTTON is not None:
            buttons[C.ENABLE_BUTTON-6]=C.BUTTON_ACTIVE
        arm=[2048]*6+buttons
        left=arm[:];left[C.LEFT_CHANNEL]=4095
        # 50 neutral frames arm, left begins step, then link loss.
        out=self.execute([arm]*50+[left]*10+[None]*20+[arm]*60+[left]*100)
        self.assertEqual(len(out.poses),12) # initial stance plus 11 armed ticks
        self.assertTrue(out.closed)

    def test_continuous_release_and_time_limit(self):
        out=FakeOutput();a=Attack(out)
        with patch.object(C,'ATTACK_ENABLED',True),patch.object(C,'ATTACK_MODE','continuous'):
            a.update(False,True,20)
            a.update(True,True,20)
            self.assertTrue(a.busy)
            a.update(False,True,20)
            self.assertFalse(a.busy)
            self.assertEqual(out.pulses[-1][1],C.ATTACK_STOP_US)
            a.update(True,True,20)
            for _ in range(100):a.update(True,True,20)
            self.assertFalse(a.busy)

if __name__=='__main__':unittest.main()
