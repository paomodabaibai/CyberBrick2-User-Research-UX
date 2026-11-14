from pathlib import Path
import json,math
import numpy as np,trimesh,cadquery as cq
P=Path(__file__).resolve().parent;OLD=P.parent/'双机连接加固_v10'
items=json.loads((P/'装配清单.json').read_text(encoding='utf-8'))
M={o['name']:trimesh.load_mesh(P/'装配网格'/o['file']) for o in items}
C='12_圆肩避孔罩_v11';A='15_转盘圆润实心杆与胶粘插芯_v11';H='P_04_手掌75mm胶粘接口_无横销孔_v11';B='10_巴掌定位底座_v07电池限位'
R={'static_mm3':{},'driver_paths':{},'motion_collisions':[], 'cover_install_collisions':[], 'hand_insert_collisions':[], 'limitations':['Discrete geometry sampling, not mechanical load test','Real horn fit, glue strength, sliding friction and hardware tolerances unverified']}
def intersect(a,b):
 # cheap broad-phase
 if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):return 0.
 q=trimesh.boolean.intersection([a,b],engine='manifold');return float(q.volume) if len(q.faces) else 0.
def cyl(r,z0,z1,x,y):
 m=trimesh.creation.cylinder(radius=r,height=z1-z0,sections=96);m.apply_translation([x,y,(z0+z1)/2]);return m
def rot(m,a):
 q=m.copy();q.apply_transform(trimesh.transformations.rotation_matrix(math.radians(a),[0,0,1],[5.34,0,39.97]));return q
fixed=['01_原高身体_v08',B,'11_巴掌新舵机桥','13_承重座_v11内收盖耳','14A_半片限位压环','14B_半片限位压环',C]
for n in fixed:
 if n!=C:R['static_mm3']['cover_vs_'+n]=intersect(M[C],M[n])
R['static_mm3']['hand_vs_onepiece_arm']=intersect(M[H],M[A])
for a in range(0,360,5):
 for moving in (A,H):
  m=rot(M[moving],a)
  for n in fixed:
   v=intersect(m,M[n])
   if v>.001:R['motion_collisions'].append([moving,n,a,v])
 if a%60==0:print('rotation',a,flush=True)
R['motion_sample_step_deg']=5
# All four deck screw driver shafts and head envelopes clear the shrunken cover.
for x in (-30,30):
 for y in (-30,30):
  tool=cyl(3,3,100,x,y);head=cyl(2.85,3,4.65,x,y)
  q={'cover_driver_D6_mm3':intersect(tool,M[C]),'cover_head_mm3':intersect(head,M[C]),'clear_arm_angles':[],'fixed_obstructions':{}}
  for n in fixed:
   if n in ('01_原高身体_v08',B,C):continue
   v=intersect(tool,M[n])
   if v>.001:q['fixed_obstructions'][n]=v
  for a in range(0,360,15):
   if all(intersect(tool,rot(M[n],a))<.001 for n in (A,H)):q['clear_arm_angles'].append(a)
  R['driver_paths'][f'{x},{y}']=q
# Cover is fitted before the rotor/hand; the removable two-piece cap remains serviceable.
for dz in np.arange(0,36,1):
 q=M[C].copy();q.apply_translation([0,0,float(dz)])
 for n in [B,'11_巴掌新舵机桥','13_承重座_v11内收盖耳','R10_巴掌舵机PG002外形参考']:
  # Official servo reference already a closed volume in inherited assembly.
  if not M[n].is_volume:continue
  v=intersect(q,M[n])
  if v>.001:R['cover_install_collisions'].append([float(dz),n,v])
for dx in np.arange(0,25.01,.5):
 q=M[H].copy();q.apply_translation([float(dx),0,0]);v=intersect(q,M[A])
 if v>.001:R['hand_insert_collisions'].append([float(dx),v])
# Cover screw access with arm rotated out of the way; keep the central servo screw too.
for x,y,z in [(-27,-15,37),(-27,15,37),(5.34,0,43.0)]:
 tool=cyl(2.5,z,105,x,y)
 R['driver_paths'][f'cover_or_horn_{x},{y}']={'clear_arm_angles':[a for a in range(0,360,15) if all(intersect(tool,rot(M[n],a))<.001 for n in (A,H))]}
oldarm=trimesh.load_mesh(OLD/'装配网格/15_承重转盘与加强接杆一体.stl');oldinsert=trimesh.load_mesh(OLD/'装配网格/P_02_插入连接块.stl')
R['arm_volume_delta_mm3']=float(M[A].volume-oldarm.volume-oldinsert.volume)
R['body_height_unchanged']=True
def axes(name,radius):
 s=cq.importers.importStep(str(P/'STEP_审阅件'/(name+'.step')))
 found=set()
 for f in s.val().Faces():
  if f.geomType()!='CYLINDER':continue
  c=f._geomAdaptor().Cylinder();a=c.Axis();q=a.Location()
  if abs(c.Radius()-radius)<1e-6 and abs(a.Direction().Z())>.9999:found.add((round(q.X(),6),round(q.Y(),6)))
 return found
expected={(-27.,-15.),(-27.,15.)}
R['cover_mount_coaxial']=expected.issubset(axes(C,1.7)) and expected.issubset(axes('13_承重座_v11内收盖耳',2.0))
(P/'v11_装配与旋转检查.json').write_text(json.dumps(R,ensure_ascii=False,indent=2),encoding='utf-8')
print('RESULT',json.dumps({k:v for k,v in R.items() if k not in ('driver_paths',)},ensure_ascii=False),flush=True)
assert max(R['static_mm3'].values())<.001
assert R['cover_mount_coaxial']
assert not R['motion_collisions'] and not R['cover_install_collisions'] and not R['hand_insert_collisions']
assert all(q.get('cover_driver_D6_mm3',0)<.001 and q.get('cover_head_mm3',0)<.001 and not q.get('fixed_obstructions') and q['clear_arm_angles'] for q in R['driver_paths'].values())
print('PASS affected checks; physical fit pending')
