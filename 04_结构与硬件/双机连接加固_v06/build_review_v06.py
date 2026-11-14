"""Review prototype: palm supported turntable and accessible fist fasteners. No print release."""
from pathlib import Path
import math,json
import numpy as np,cadquery as cq,trimesh
from scipy.spatial import ConvexHull
from body_finish import remove_rear_engraving
P=Path(__file__).resolve().parent;H=P.parent;ROOT=H.parent;V4=H/'双机结构改版_v04';V5=H/'双机结构压缩_v05';REF=ROOT/'01_研究参考/CyberBrick1迁移研究'
for d in ('装配网格','STEP_审阅件','预览'):(P/d).mkdir(exist_ok=True)
items=[];meshes={};shapes={};checks={};cx=5.34;rz=39.97

def box(x,y,z,a=0,b=0,c=0):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((a,b,c))
def cyl(r,h,x=0,y=0,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def nut(x,y,z):return cq.Workplane('XY').polygon(6,5.8/math.cos(math.pi/6)).extrude(2.8).translate((x,y,z))
def ring(ro,ri,z,h):return cyl(ro,h,cx,0,z).cut(cyl(ri,h+2,cx,0,z-1))
def mesh(s,fine=False):
 v,f=s.val().tessellate(.03 if fine else .1,.05 if fine else .1)
 m=trimesh.Trimesh(np.array([a.toTuple() for a in v]),np.array(f),process=True)
 if fine:
  m.merge_vertices(digits_vertex=7);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
 return m
def add(n,m,col,g='palm',k='part'):
 m.export(P/'装配网格'/(n+'.stl'));meshes[n]=m;items.append(dict(name=n,file=n+'.stl',color=col,group=g,kind=k))
def put(n,s,col,g='palm',k='part'):
 assert s.val().isValid(),n
 shapes[n]=s;add(n,mesh(s,fine=n.startswith('12_')),col,g,k)
 if k=='part':
  assert len(s.solids().vals())==1,(n,len(s.solids().vals()))
  cq.exporters.export(s,str(P/'STEP_审阅件'/(n+'.step')))
def vol(a,b):return sum(s.Volume() for s in a.intersect(b).solids().vals())
def oldstep(stem):return cq.importers.importStep(str(V4/'STEP_审阅模型'/(stem+'.step'))).translate((0,0,-26))
# Reuse all compact body/electronics, and all moving fist parts unchanged.
replace={'11_巴掌原基准舵机桥','12_巴掌可拆圆角头罩','P_05_完整连接杆_杆距51mm','20_拳头固定底座_含隐藏过线槽','21_拳头轻量侧护罩'}
for o in json.loads((V5/'装配清单.json').read_text(encoding='utf-8')):
 if o['name'] not in replace:
  reused=trimesh.load_mesh(V5/'装配网格'/o['file'])
  if o['kind']=='body':reused=remove_rear_engraving(reused)
  add(o['name'],reused,o['color'],o['group'],o['kind'])
# Raised, flat-backed oval eye appliques on common front (+X). Glue-on, no wall perforation.
for side,y in [('左',13),('右',-13)]:
 eye=cq.Workplane('YZ').ellipse(5,7.5).extrude(2.4).edges('>X').fillet(1.1).translate((37.5,y,-13))
 put('04_'+side+'椭圆眼睛_平背粘贴',eye,'#273744','common')
# Servo bridge retains mounting reference; remove obsolete old lid pillars/nut cups.
bridge=box(66,22,3,c=22).cut(box(23.8,12.8,6,c=21))
for x in (-13.9,13.9):bridge=bridge.cut(cyl(1.2,6,x,0,21))
for x in (-29,29):
 for y in (-6,6):bridge=bridge.cut(cyl(1.7,6,x,y,21))
put('11_巴掌新舵机桥',bridge,'#358fb8')
# Fixed bearing seat: all palm weight goes to this carrier and the four bridge screws.
seat=ring(27,17,31.5,2).union(ring(27,24.3,33.5,2.9))
for x in (-29,29):
 seat=seat.union(box(8,20,6.5,x,0,25)).union(box(20,18,2,(-22 if x<0 else 24),0,31.5))
 for y in (-6,6):seat=seat.cut(cyl(1.7,12,x,y,24))
# Separate lid bosses at the rear-left; non-load-bearing cover does not support the arm.
for y in (-18,18):
 seat=seat.union(box(8,22,2,-29,math.copysign(11,y),31.5))
 seat=seat.cut(cyl(1.7,5,-29,y,30.5))
# Captive top retaining ring. Recessed heads stay below the rotating arm.
cap=ring(27,20.4,36.4,2)
bolts=[]
for deg in (45,135,225,315):
 a=math.radians(deg);x=cx+28.2*math.cos(a);y=28.2*math.sin(a);bolts.append((x,y))
 seat=seat.cut(cyl(4.8,3,x,y,34.4))
 seat=seat.union(cyl(4.5,4.9,x,y,29.5)).cut(cyl(1.7,10,x,y,28.5)).cut(nut(x,y,29.5))
 cap=cap.union(cyl(4.5,4,x,y,34.4)).cut(cyl(1.7,8,x,y,33)).cut(cyl(3.1,2.1,x,y,36.4))
cap=cap.cut(cyl(24.3,3,cx,0,33.4)) # remove only lowered ear material next to rotor
# Restore annular upper lip after the lower trim.
cap=cap.union(ring(27,20.4,36.4,2))
for x,y in bolts:cap=cap.cut(cyl(1.7,8,x,y,33)).cut(cyl(3.1,2.1,x,y,36.4))
for x in (-29,29):
 for y in (-6,6):seat=seat.cut(cyl(3.2,7,x,y,30.8))
seat=seat.cut(cyl(24.3,5,cx,0,33.5))
# Arm profile preserved at wrist; root becomes an independent rotor with broad support.
rodpath=H/'Otto_75mm巴掌腕部接口_v02/STEP_结构件/05_完整连接杆_杆距51mm.step'
rod=cq.importers.importStep(str(rodpath))
rotor=rod.union(cyl(20,3)).union(cyl(24,2.5,z=33.5-rz).cut(cyl(17,5,z=32.5-rz)))
rotor=rotor.union(cyl(20,3.97,z=36-rz).cut(cyl(17,6,z=35-rz)))
# Two upper ribs stiffen the rod without changing wrist/palm height or reach.
for y in (-4,4):rotor=rotor.union(box(27,2,5,27.5,y,3))
# Original horn stays fixed to servo with its original center screw.
# A loose-bottom pocket transfers torque through side faces; it does not carry gravity.
horn=cq.importers.importStep(str(next(REF.glob('*half arm*.stp')))).translate((0,-20,-1.55))
v,_=horn.val().tessellate(.08);xy=np.unique(np.round([[a.x,a.y] for a in v],6),axis=0);xy=xy[ConvexHull(xy).vertices]
def outline(offset,z,h):return cq.Workplane('XY').polyline(xy.tolist()).close().offset2D(offset).extrude(h).translate((0,0,z))
rotor=rotor.union(outline(1.8,-2,2)).cut(outline(.3,-2.3,2.7)).cut(cyl(4.1,16,z=-10))
rotor=rotor.translate((cx,0,rz));horn=horn.translate((cx,0,rz))
put('13_独立承重座_打印滑动试验版',seat,'#f2ae45')
# Split cap assembles around the rotor neck; no need to force a closed ring over the arm.
cap=cap.cut(box(100,.3,20,cx,0,30))
for suffix,s in zip(('A','B'),sorted(cap.solids().vals(),key=lambda q:q.Center().y)):
 put('14'+suffix+'_半片限位压环',cq.Workplane('XY').newObject([s]),'#e9c877')
put('15_承重转盘与加强接杆一体',rotor,'#418eb5')
put('R11_原配舵盘_只传扭矩',horn,'#d5d9dc',k='reference')
# Cover clips distant corners to stay within radius 49mm of rotation axis.
outer=box(75,75,34,c=3).edges('|Z').fillet(5).intersect(cyl(49,36,cx,0,2)).edges('>Z').fillet(5)
inner=box(70.2,70.2,33,c=2).edges('|Z').fillet(3).intersect(cyl(46.6,35,cx,0,1)).edges('>Z').fillet(3)
cover=outer.cut(inner).cut(cyl(27.5,10,cx,0,30))
for x,y in bolts:cover=cover.cut(cyl(4.9,10,x,y,30))
for y in (-18,18):
 cover=cover.union(cyl(3.6,3.5,-29,y,33.5)).cut(cyl(1.7,8,-29,y,32))
# Clear carrier body from roof, then keep cover screw bosses.
cover=cover.cut(seat)
put('12_承重转盘配套可拆罩',cover,'#61b5e4')
# Fist fixed base: delete obsolete guard boss/nut ears, fill unused holes.
base=oldstep('20_拳头固定底座_含隐藏过线槽')
for y in (-28.5,28.5):
 base=base.cut(cyl(4.1,3.01,-46,y,-3.01)).union(cyl(1.75,3,-46,y,0))
for x in (-24,-8):base=base.union(cyl(1.65,3,x,-29,0))
put('20_拳头底座_清理废弃孔耳',base,'#b9494b','fist')
# Guard co-clamps with the existing two rear body screws; U channels leave driver access.
guard=box(84,61,22,-26.5,0,3).edges('|Z').fillet(5).cut(box(87,56,24,-26.5,0,2).edges('|Z').fillet(3))
guard=guard.union(box(2.4,57,22,-67,0,3))
for y in (-30,30):
 guard=guard.union(cyl(6,2,-30,y,3)).cut(cyl(4.2,25,-30,y,5)).cut(cyl(1.7,6,-30,y,2))
put('21_拳头护罩_共用螺丝敞口',guard,'#da696b','fist')
# Geometry evidence, not a durability or manufacturing approval.
servo_raw=cq.importers.importStep(str(next(REF.glob('*Protection-PG002-PG001.stp'))))
servo=cq.Workplane('XY').newObject([servo_raw.solids().vals()[0]]).translate((-11.35,-5.9,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,25))
for name,a,b in [('seat_bridge',seat,bridge),('seat_cap',seat,cap),('rotor_seat',rotor,seat),('rotor_cap',rotor,cap),('rotor_horn',rotor,horn),('cover_seat',cover,seat),('cover_cap',cover,cap),('fist_guard_base',guard,base)]:checks[name]=vol(a,b)
# Driver diameter 6mm, open from screw seating level upwards.
for x in (-30,30):
 for y in (-30,30):
  z=5 if x<0 else 3
  tool=cyl(3,80,x,y,z)
  checks['driver_%s_%s_guard'%(x,y)]=vol(tool,guard)
  checks['driver_%s_%s_base'%(x,y)]=vol(tool,base)
# Rotation sweep for printed rotor; hand is analytically outside R51 vs cover maxR49.
worst=0;where=None
for ang in range(0,360,10):
 r=rotor.rotate((cx,0,0),(cx,0,1),ang)
 for n,s in [('seat',seat),('cap',cap),('cover',cover),('bridge',bridge)]:
  vv=vol(r,s)
  if vv>worst:worst=vv;where=(ang,n)
checks['rotor_sweep_max_mm3']=worst
for n in ('13_独立承重座_打印滑动试验版','14A_半片限位压环','14B_半片限位压环','15_承重转盘与加强接杆一体','12_承重转盘配套可拆罩'):
 checks[n+'_servo']=vol(shapes[n],servo)
report={'checks_mm3':checks,'rotor_sweep_worst':where,'axial_float_mm':.4,'radial_running_clearance_mm':.3,'horn_side_clearance_mm':.3,'horn_axial_roof_clearance_mm':.4,'palm_height_and_reach':'unchanged; palm75,reach51,rodZ39.97','status':'Printed sliding bearing prototype; NOT friction/wear/strength validated. Do not batch print.'}
(P/'接口审阅检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'装配清单.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2));print('REVIEW_COMPLETE')
