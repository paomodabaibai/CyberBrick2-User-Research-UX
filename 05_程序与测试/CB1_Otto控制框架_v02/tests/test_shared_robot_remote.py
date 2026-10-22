"""Both deployed entry profiles must produce identical legs and held-K4 dance."""
import types
import runpy
from pathlib import Path
import unittest
from unittest.mock import patch
import robot_remote as core
from drivers import palm_pwm

MAPPING=dict(left_center=1800,right_center=2000,attack_center=1850)
PALM=dict(enabled=True,actuator='continuous',channel=2,center=1850,span=1800,
          direction=1,gpio=21,freq_hz=50,neutral_us=1500,delta_us=200,
          enter_deadband=.15,exit_deadband=.10,reverse_dwell_ms=150)

def frame(left=0,right=0,attack=0,k4=1):
    raw=[2000]*6+[1]*4
    raw[3]=int(1800+left*1700);raw[0]=int(2000+right*1700)
    raw[2]=int(1850+attack*1700);raw[9]=k4
    return raw

def sample(t):
    if t<600:return frame()
    if t<1200:return frame(1,1,1)
    if t<1800:return frame(1,1,1,k4=0)
    if t<1900:return frame()
    if t<2500:return frame(-1,0,-1)
    return None

def exercise(kind='palm', script=sample, fail_d1=False, mode='both', profile=None):
    clock,events,channels=[0],[],[]
    class Pin:
        IN=0
        def __init__(self,gpio,*args):self.gpio=gpio
        def value(self):return 0
    class PWM:
        def __init__(self,pin,freq):
            self.gpio=getattr(pin,'gpio',pin);self.off=False
            channels.append(self)
        def duty_ns(self,ns):
            events.append(('pulse',clock[0],self.gpio,ns))
            if fail_d1 and self.gpio==21 and ns==1700000:
                raise RuntimeError('injected D1 failure')
        def duty(self,value):events.append(('duty',clock[0],self.gpio,value))
        def deinit(self):self.off=True;events.append(('off',clock[0],self.gpio,0))
    class Motor:
        def stop(self,n):events.append(('motor',clock[0],n,0))
        def set_speed(self,n,speed):events.append(('motor',clock[0],n,speed))
    machine=types.ModuleType('machine');machine.Pin=Pin;machine.PWM=PWM
    rc=types.ModuleType('rc_module');rc.rc_slave_init=lambda:True
    def read():
        raw=script(clock[0])
        if raw is None or profile is None:return raw
        raw=list(raw)
        for key,old_center in (('left',1800),('right',2000),('attack',1850)):
            channel=profile.MAPPING.get(key,core.DEFAULT[key])
            raw[channel]+=profile.MAPPING[key+'_center']-old_center
        return raw
    rc.rc_slave_data=read
    motors=types.ModuleType('bbl.motors');motors.MotorsController=Motor
    modules={'machine':machine,'rc_module':rc,
             'bbl':types.ModuleType('bbl') if kind=='punch' else None,
             'bbl.motors':motors if kind=='punch' else None}
    def sleep(ms):clock[0]+=ms
    with patch.dict('sys.modules',modules),patch.object(core,'_clock',lambda:clock[0]), \
         patch.object(core,'_sleep',sleep),patch.object(palm_pwm,'_machine',machine), \
         patch('builtins.print'):
        if fail_d1:
            with unittest.TestCase().assertRaisesRegex(RuntimeError,'injected'):
                core.run(3,mode,mapping=MAPPING,attack_kind=kind,palm_cfg=PALM)
        else:
            if profile is None:
                core.run(3,mode,mapping=MAPPING,attack_kind=kind,palm_cfg=PALM)
            else:
                profile.run(3,mode)
    return events,channels

class SharedRobotTests(unittest.TestCase):
    def test_common_gait_uses_the_original_palm_amplitudes(self):
        import config
        self.assertEqual(core.HIP_AMP,30.0)
        self.assertEqual(core.ANKLE_AMP,20.0)
        self.assertEqual(core.HIP_AMP,config.OTTO['hip_amp'])
        self.assertEqual(core.ANKLE_AMP,config.OTTO['ankle_amp'])
        self.assertEqual(core.TURN_SPLIT,config.OTTO['turn_split'])

    def test_real_receiver_profiles_match_leg_and_dance_PWMs_after_calibration(self):
        import palm_remote_ready
        import second_remote_ready
        a,_=exercise('palm',profile=palm_remote_ready)
        b,_=exercise('punch',profile=second_remote_ready)
        leg=lambda events:[e for e in events if e[0]=='pulse' and e[2] in core.PORTS]
        self.assertTrue(leg(a));self.assertEqual(leg(a),leg(b))

    def test_receiver_entry_files_use_the_same_forever_loop(self):
        import palm_remote_ready
        import second_remote_ready
        root=Path(core.__file__).parent
        with patch.object(core,'run_forever') as start:
            runpy.run_path(str(root/'palm_main.py'))
            runpy.run_path(str(root/'second_punch_main.py'))
        self.assertEqual([c.args[0] for c in start.call_args_list],
                         [palm_remote_ready,second_remote_ready])

    def test_forever_loop_retries_an_exception_and_preserves_continuous_mode(self):
        pin=type('Pin',(),{'IN':0,'__init__':lambda self,*a:None,'value':lambda self:0})
        machine=types.ModuleType('machine');machine.Pin=pin
        calls=[]
        def run(**kwargs):
            calls.append(kwargs)
            if len(calls)==1:raise RuntimeError('test retry')
            raise KeyboardInterrupt()
        with patch.dict('sys.modules',{'machine':machine}),patch.object(core.time,'sleep') as sleep,patch('builtins.print'):
            with self.assertRaises(KeyboardInterrupt):core.run_forever(types.SimpleNamespace(run=run))
        self.assertEqual(calls,[dict(seconds=None,mode='both')]*2)
        sleep.assert_called_once_with(2)

    def test_bad_palm_configuration_is_rejected_before_hardware_import(self):
        for change in ({'gpio':3},{'channel':0},{'center':2048},{'enabled':False},
                       {'actuator':'position'},{'delta_us':2000}):
            cfg=dict(PALM);cfg.update(change)
            with self.subTest(change=change),patch.dict('sys.modules',{'machine':None,'rc_module':None}):
                with self.assertRaises(ValueError):
                    core.run(1,mapping=MAPPING,attack_kind='palm',palm_cfg=cfg)

    def test_both_attack_kinds_have_identical_leg_pwm_including_dance(self):
        palm,_=exercise('palm');punch,_=exercise('punch')
        leg=lambda events:[e for e in events if e[0]=='pulse' and e[2] in core.PORTS]
        self.assertTrue(leg(palm))
        self.assertEqual(leg(palm),leg(punch))

    def test_palm_rotates_both_ways_and_stops_during_K4(self):
        events,_=exercise()
        d1=[e for e in events if e[0]=='pulse' and e[2]==21]
        self.assertTrue(any(600<=t<1200 and ns==1700000 for _,t,_,ns in d1))
        self.assertTrue(any(1900<=t<2500 and ns==1300000 for _,t,_,ns in d1))
        self.assertTrue(any(1200<=t<1800 and ns==1500000 for _,t,_,ns in d1))
        self.assertFalse(any(1200<=t<1800 and ns!=1500000 for _,t,_,ns in d1))

    def test_K4_release_restores_walk_and_palm_after_neutral(self):
        events,_=exercise()
        self.assertTrue(any(e[0]=='pulse' and e[2] in core.PORTS and e[1]>=1900 for e in events))
        self.assertTrue(any(e[0]=='pulse' and e[2]==21 and e[1]>=1900 and e[3]==1300000 for e in events))

    def test_link_loss_releases_palm_and_legs(self):
        events,channels=exercise()
        self.assertTrue(all(c.off for c in channels))
        self.assertFalse(any(e[0]=='pulse' and e[1]>=2500 and
                             (e[2] in core.PORTS or e[3]!=1500000) for e in events))
        self.assertTrue(any(e[0]=='off' and e[1]==2500 and e[2]==21 for e in events))

    def test_d1_exception_releases_all_outputs(self):
        _,channels=exercise(fail_d1=True)
        self.assertTrue(channels)
        self.assertTrue(all(c.off for c in channels))

    def test_palm_mode_never_constructs_motor_or_uses_M1(self):
        events,_=exercise()
        self.assertFalse(any(e[0]=='motor' or e[2] in (4,5) for e in events))

    def test_held_attack_at_boot_never_creates_PWM(self):
        events,channels=exercise(script=lambda t:frame(attack=1))
        self.assertEqual(events,[])
        self.assertEqual(channels,[])

    def test_palm_attack_only_never_creates_leg_pwm(self):
        events,_=exercise(mode='attack')
        self.assertFalse(any(e[0]=='pulse' and e[2] in core.PORTS for e in events))

    def test_after_dance_held_attack_requires_neutral(self):
        def script(t):
            if t<600:return frame()
            if t<1000:return frame(attack=1,k4=0)
            if t<1500:return frame(attack=1)
            if t<1600:return frame()
            return frame(attack=-1)
        events,_=exercise(script=script)
        self.assertFalse(any(e[0]=='pulse' and e[2]==21 and e[3]!=1500000 and e[1]<1600 for e in events))
        self.assertTrue(any(e[0]=='pulse' and e[2]==21 and e[3]==1300000 and e[1]>=1600 for e in events))

if __name__=='__main__':unittest.main()
