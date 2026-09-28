import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'board'))
from milk_core import Trigger, Gait, servo_angle, RemoteGate
from milk_receiver import valid_frame, axis
import milk_config as C

class Tests(unittest.TestCase):
    def test_arm_and_link_loss(self):
        gate=RemoteGate()
        self.assertFalse(gate.update(True,False,True,False,1000))
        for _ in range(49): self.assertFalse(gate.update(True,True,True,False,20))
        self.assertTrue(gate.update(True,True,True,False,20))
        self.assertFalse(gate.update(False,True,True,False,20))
        self.assertFalse(gate.update(True,True,True,False,20))
    def test_stop_dominates_enable(self):
        gate=RemoteGate()
        self.assertFalse(gate.update(True,True,True,True,2000))
    def test_frames(self):
        for frame in (None,[],[0]*10,[1]*9,[5000]*6+[1]*4,[2048]*6+[2]*4):
            self.assertFalse(valid_frame(frame))
        self.assertTrue(valid_frame([2048]*6+[1]*4))
    def test_default_config_no_activation(self):
        self.assertFalse(C.CALIBRATED)
        # Remote mapping was verified on hardware 2026-09-22; gait must stay locked.
        self.assertTrue(C.REMOTE_MAPPING_VERIFIED)
        self.assertFalse(C.ATTACK_ENABLED)
    def test_axis_reversal_and_saturation(self):
        self.assertEqual(axis(4095,2048,1800,-1),-1)
        self.assertEqual(axis(2048,2048,1800,1),0)
    def test_actual_config_entire_gait(self):
        g=Gait(C.HIP,C.LEAN,C.LIFT,C.PHASE_MS,C.LEFT_SIGN)
        for side in ('right','left','right','left'):
            self.assertTrue(g.start(side))
            while g.busy:
                for offset,cfg in zip(g.tick(20),C.JOINTS):
                    self.assertTrue(cfg['min']<=servo_angle(offset,cfg)<=cfg['max'])
    def test_edge_and_recentre(self):
        t=Trigger()
        self.assertIsNone(t.update(1,0))
        self.assertIsNone(t.update(0,0))
        self.assertEqual(t.update(1,0),'left')
        self.assertIsNone(t.update(1,0))
        t.update(0,0)
        self.assertEqual(t.update(0,1),'right')
    def test_conflict_consumes(self):
        t=Trigger(); t.update(0,0)
        self.assertIsNone(t.update(1,1))
        self.assertIsNone(t.update(1,0))
    def test_busy_drops(self):
        t=Trigger(); t.update(0,0)
        self.assertIsNone(t.update(1,0,busy=True))
        self.assertIsNone(t.update(1,0))
    def test_limits(self):
        c={'center':90,'trim':2,'direction':-1,'min':60,'max':120}
        self.assertEqual(servo_angle(10,c),82)
        with self.assertRaises(ValueError): servo_angle(40,c)
    def test_alternate_and_retain_pose(self):
        g=Gait(); self.assertTrue(g.start('left'))
        while g.busy: g.tick(20)
        self.assertGreater(abs(g.pose[0]),0)
        self.assertFalse(g.start('left'))
        self.assertTrue(g.start('right'))
        while g.busy: g.tick(20)
        self.assertLess(g.pose[0],0)
    def test_stop_freezes_and_requires_recovery(self):
        g=Gait(); g.start('left'); g.tick(100)
        p=g.pose[:]; g.stop(); g.tick(2000)
        self.assertEqual(p,g.pose)
        self.assertFalse(g.start('right'))
    def test_motion_bounded_continuous(self):
        g=Gait(); g.start('left'); last=g.pose[:]
        while g.busy:
            p=g.tick(20)
            self.assertTrue(all(abs(x)<=12 for x in p))
            self.assertLess(max(abs(a-b) for a,b in zip(last,p)),2)
            last=p[:]

if __name__=='__main__': unittest.main()
