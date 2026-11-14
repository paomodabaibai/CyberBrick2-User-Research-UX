# One-shot physical test; reuse deployed gait and dance; no radio or attack.
import machine,time,os
assert machine.unique_id()==bytes([128,241,178,30,179,108]), 'Wrong board'
assert machine.Pin(10,machine.Pin.IN,None).value()==0, 'Not receiver'
assert 'commissioning_hold' in os.listdir('/'), 'Hold missing'
from robot_remote import WalkMotion,DanceMotion,PORTS,JOINT_LIMITS
pwms=[]
last_pose=(0,0,0,0)
def write_pose(pose):
 global last_pose
 angles=[90+x for x in pose]
 for a,bounds in zip(angles,JOINT_LIMITS):
  if not bounds[0]<=a<=bounds[1]: raise ValueError('Joint limit')
 for p,a in zip(pwms,angles): p.duty_ns(int(500+a*2000/180)*1000)
 last_pose=tuple(pose)
def walking(motion,duration,engaged):
 start=time.ticks_ms()
 last=start
 while time.ticks_diff(time.ticks_ms(),start)<duration:
  now=time.ticks_ms()
  dt=time.ticks_diff(now,last)
  last=now
  write_pose(motion.step(dt,engaged,0.0,1))
  time.sleep_ms(20)
try:
 for gpio in PORTS: pwms.append(machine.PWM(machine.Pin(gpio),freq=50))
 write_pose((0,0,0,0))
 time.sleep_ms(500)
 motion=WalkMotion()
 print('FORWARD 2 SECONDS')
 walking(motion,2000,True)
 print('SETTLE')
 walking(motion,600,False)
 print('DANCE 2 SECONDS')
 start=time.ticks_ms()
 dance=DanceMotion(start,last_pose)
 while time.ticks_diff(time.ticks_ms(),start)<2000:
  write_pose(dance.pose(time.ticks_ms()))
  time.sleep_ms(20)
 print('RETURN TO CENTRE')
 before=last_pose
 for i in range(1,26):
  write_pose(tuple(x*(1-i/25) for x in before))
  time.sleep_ms(20)
 time.sleep_ms(300)
finally:
 for p in pwms:
  try:
   p.duty(0)
   p.deinit()
  except Exception:
   pass
 print('ALL LEG PWM OFF; D2 UNTOUCHED; INSTALL HOLD RETAINED')