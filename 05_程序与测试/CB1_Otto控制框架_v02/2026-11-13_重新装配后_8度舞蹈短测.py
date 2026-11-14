import machine,time,os
from robot_remote import DanceMotion
assert machine.unique_id()==bytes([128,241,178,30,179,108]), 'Wrong board'
assert machine.Pin(10,machine.Pin.IN,None).value()==0, 'Not receiver'
assert 'commissioning_hold' in os.listdir('/'), 'Hold missing'
assert '_assembly_hold_pwms' in globals() and len(_assembly_hold_pwms)==4, 'Expected assembly hold'
for p in _assembly_hold_pwms:
 assert abs(p.duty_ns()-1500000)<10000, 'Joint not at 90; stop'
_dance_trial_pwms=[_assembly_hold_pwms[i] for i in (0,2,1,3)]
_dance_last=(0,0,0,0)
def _dance_write(pose):
 global _dance_last
 assert all(-8.001<=v<=8.001 for v in pose), 'Dance limit'
 for p,v in zip(_dance_trial_pwms,pose):
  p.duty_ns(int(500+(90+v)*2000/180)*1000)
 _dance_last=tuple(pose)
try:
 start=time.ticks_ms()
 dance=DanceMotion(start)
 dance.LIMITS=(8,8,8,8)
 print('DANCE 2s MAX +/-8 DEG; ALL CENTRES 90')
 while time.ticks_diff(time.ticks_ms(),start)<2000:
  _dance_write(dance.pose(time.ticks_ms()))
  time.sleep_ms(20)
 before=_dance_last
 for i in range(1,26):
  _dance_write(tuple(v*(1-i/25) for v in before))
  time.sleep_ms(20)
 print('DONE: S1 S2 S3 S4 HOLD 90; D2 UNTOUCHED')
except BaseException:
 for p in _dance_trial_pwms:
  try: p.deinit()
  except Exception: pass
 print('ABORT: LEG PWM RELEASED')
 raise