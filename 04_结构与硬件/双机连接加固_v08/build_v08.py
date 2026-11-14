"""v08: v07 plus a bench-assembled switch module and tool access checked in assembly order.
Trial-fit model, not batch print. Offline CAD only. No serial, network, firmware or original-file writes."""
from pathlib import Path
import math,json,importlib.util
import numpy as np,cadquery as cq,trimesh
from scipy.spatial import ConvexHull
from body_finish import remove_rear_engraving
P=Path(__file__).resolve().parent;H=P.parent;ROOT=H.parent;R=ROOT/'01_研究参考';REF=R/'CyberBrick1迁移研究'
V4=H/'双机结构改版_v04';V6=H/'双机连接加固_v06';MEAS=V4/'测量临时文件'
for d in ('装配网格','STEP_审阅件','预览'):(P/d).mkdir(exist_ok=True)
items=[];meshes={};shapes={};checks={};cx=5.34;rz=39.97
DX,DY=-6.5,4.5 # D03: switch moves rearward behind the receiver and towards +Y

def box(x,y,z,a=0,b=0,c=0):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((a,b,c))
def cyl(r,h,x=0,y=0,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def cylx(r,l,x,y,z):return cq.Workplane('YZ',origin=(x,y,z)).circle(r).extrude(l)
def nut(x,y,z):return cq.Workplane('XY').polygon(6,5.8/math.cos(math.pi/6)).extrude(2.8).translate((x,y,z))
def ring(ro,ri,z,h):return cyl(ro,h,cx,0,z).cut(cyl(ri,h+2,cx,0,z-1))
def roundbox(x,y,z,z0,r):return box(x,y,z,c=z0).edges('|Z').fillet(r)
def mesh(s,fine=False):
 v,f=s.val().tessellate(.03 if fine else .1,.05 if fine else .1)
 m=trimesh.Trimesh(np.array([a.toTuple() for a in v]),np.array(f),process=True)
 if fine:
  m.merge_vertices(digits_vertex=7);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
 return m
def add(n,m,col,g='common',k='part'):
 m.export(P/'装配网格'/(n+'.stl'));meshes[n]=m;items.append(dict(name=n,file=n+'.stl',color=col,group=g,kind=k))
def put(n,s,col,g='common',k='part'):
 assert s.val().isValid(),n
 shapes[n]=s;add(n,mesh(s,fine=n.startswith('12_')),col,g,k)
 if k=='part':
  assert len(s.solids().vals())==1,(n,len(s.solids().vals()))
  cq.exporters.export(s,str(P/'STEP_审阅件'/(n+'.step')))
def vol(a,b):return sum(s.Volume() for s in a.intersect(b).solids().vals())
def inter(a,b):
 r=trimesh.boolean.intersection([a,b],engine='manifold');return float(r.volume) if len(r.faces) else 0.0
def oldstep(stem):return cq.importers.importStep(str(V4/'STEP_审阅模型'/(stem+'.step'))).translate((0,0,-26))
v6={o['name']:o for o in json.loads((V6/'装配清单.json').read_text(encoding='utf-8'))}
def reuse(n):o=v6[n];add(n,trimesh.load_mesh(V6/'装配网格'/o['file']),o['color'],o['group'],o['kind'])

# ---------------- Body: v05 layout, v07 fastener and switch-bay changes ----------------
old=trimesh.load_mesh(R/'robot-battle-reference/Otto-V9/3Dprint/OttoDIY_body_V9.stl')
old.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,0,1]))
lower=trimesh.boolean.intersection([old,mesh(box(150,150,30,c=-54))],engine='manifold')
shell=roundbox(75,75,25,-25,5).cut(roundbox(69.8,69.8,27,-26,3))
shell=shell.union(roundbox(75,75,2,-25.5,5).cut(roundbox(65,65,4,-26.5,3)))
shell=shell.union(box(5,58,39,35,0,-39)).union(box(20,57,2.5,27.5,0,-39))
for y in (-27.4,27.4):shell=shell.union(box(18,1.6,20,26.5,y,-36.5))
# D01: all four deck screws go into M3x5.7 heat-set inserts (hole D4.0x6). Rear bosses stop at Z-8,
# above the switch bay, so no nut pocket is cut away. No loose nuts inside the 39mm body.
for x in (-30,30):
 for y in (-30,30):
  h=6 if x>0 else 8
  b=cyl(4.6,h,x,y,-h).union(box(7,7,h,x+math.copysign(3.5,x),y,-h)).union(box(7,7,h,x,y+math.copysign(3.5,y),-h))
  shell=shell.union(b.cut(cyl(1.7,h+2,x,y,-h-1)).cut(cyl(2.0,6.01,x,y,-6)))
# D09: floor posts become solid locating pins; the bracket is clamped from above by the top module.
for x in (-22,0):shell=shell.union(cyl(3.8,7.5,x,14,-39)).union(cyl(1.45,2.3,x,14,-31.5))
shell=shell.union(box(35,7,2,-14.5,15,-39))
# D03: rear switch housing widened to Y+6.5 so both XH plugs have room.
shell=shell.union(box(4,44.5,27,-39.5,-15.75,-32))
body=trimesh.boolean.union([lower,mesh(shell)],engine='manifold')
body=remove_rear_engraving(body)
cut_front=box(17.2,53,36.6,26.6,0,-36.5) # v08: runs out through the deck so the battery drops straight in (v05 left a 1mm lip)
cut_usb=box(14,13,17,-36,13.5,-26.5)
bay1=box(22,30,23,-33,-21,-31) # X-44..-22 Y-36..-6: side wall now 2mm (D04)
bay2=box(11.5,12.5,23,-38.25,0.25,-31) # X-44..-32.5 Y-6..6.5: behind the receiver
cut_duct=box(14,14,10,-36,-18,-9)
for q in (cut_front,cut_usb,bay1,bay2,cut_duct):body=trimesh.boolean.difference([body,mesh(q)],engine='manifold')
# The switch is carried by the rear panel (bench assembled) and slides in from behind; the bay stays empty.
# Floor plate closes the bay bottom; two insert bosses take the panel screws.
fill=box(3.1,42.5,1,-36.05,-14.75,-32)
pboss=[cylx(3.5,6.2,-41.5,yb,-28.5) for yb in (-33.5,2.5)]
for piece in [fill]+pboss:
 pm=mesh(piece,fine=True);assert pm.is_volume
 body=trimesh.boolean.union([body,pm],engine='manifold')
for yb in (-33.5,2.5):body=trimesh.boolean.difference([body,mesh(cylx(2.0,6.1,-41.6,yb,-28.5))],engine='manifold')
add('01_原高身体_v08',body,'#cbd9e2',k='body')
for n in ('R01_竖置原厂接收组合','R02_前置立放电池','02_竖置主板托架_布局草案','E01_侧插头与弯线预留','E02_USB数据线插拔预留'):reuse(n)
swraw=cq.importers.importStep(str(MEAS/'Power Switch Board with 2Pin XH2.54 Connector-XA007.STEP'))
def switch_pose(w):return w.rotate((0,0,0),(0,0,1),90).rotate((0,0,0),(1,0,0),-90).translate((-26.1+DX,-19.5+DY,-17))
put('R03_后置开关_v08模块',switch_pose(swraw),'#444f61',k='reference')
# XA007 has one factory mounting ear at the PCB bottom centre (D2.7 hole). Measure it from the official CAD.
pcb=switch_pose(cq.Workplane('XY').newObject([cq.Solid.makeSolid(swraw.shells().vals()[0])])).val()
pb_=pcb.BoundingBox();EX=pb_.xmin # ear/PCB rear face
hole=[f.Center() for f in pcb.Faces() if f.geomType()=='CYLINDER' and abs(f.BoundingBox().xlen-pb_.xlen)<.05 and 1.2<f.BoundingBox().zlen/2<1.5]
EY,EZ=hole[0].y,hole[0].z
pm=mesh(cq.Workplane('XY').newObject([pcb]));sec=trimesh.intersections.mesh_plane(pm,[0,0,1],[0,0,EZ])
ey0,ey1=float(sec[:,:,1].min()),float(sec[:,:,1].max())
# Switch module = rear panel + standoff to the ear. Bench order: lever through window, ear on standoff,
# one M2.5x6 self-tapping screw from the PCB front (open on the bench), plug both XH leads, then slide in.
bezel=box(2.4,44.5,23.8,-42.7,-15.75,-32) # top Z-8.2: slides in under the fist cable trough
bezel=bezel.cut(box(5,8.3,7.5,-42.7,-14.95,-19)) # lever window
for yb in (-33.5,2.5):bezel=bezel.cut(cylx(1.7,8,-46,yb,-28.5))
stand=cylx(3,EX+41.5,-41.5,EY,EZ)
pad=box(1.2,ey1-ey0+1.9,5.6,EX-.6,(ey0+ey1)/2,-30.2) # wider seat behind the ear
lips=[box(1.2,.8,4.6,EX+.4,ey0-.55,-30.2),box(1.2,.8,4.6,EX+.4,ey1+.55,-30.2)] # stop the PCB turning about one screw
module=bezel.union(stand).union(pad).union(lips[0]).union(lips[1]).cut(cylx(1.05,6.5,EX-6.4,EY,EZ))
put('03_开关模块面板_v08',module,'#4d677a')
checks['switch_ear']={'hole_Y':round(EY,2),'hole_Z':round(EZ,2),'ear_Y':[round(ey0,2),round(ey1,2)],'ear_rear_X':round(EX,2)}
# D-eyes: flat-backed oval eyes as v06, with a flush 0.6mm highlight inlay (AMS second colour or paint).
for side,y in [('左',13),('右',-13)]:
 eye=cq.Workplane('YZ').ellipse(5,7.5).extrude(2.4).edges('>X').fillet(1.1).translate((37.5,y,-13))
 hi=cylx(1.3,0.6,39.3,y+1.5,-13+2.6)
 put('04_'+side+'椭圆眼睛_平背粘贴',eye.cut(hi),'#273744')
 put('05_'+side+'眼高光_白色嵌件',hi,'#f4f6f8')
for n in v6:
 if n.startswith(('R_Leg','R_foot','E_hip')):reuse(n)

# ---------------- Shared top-module additions ----------------
def retainer(s):
 # The palm base is only a 6mm perimeter frame, so everything hangs from a cross beam tied into the side frame.
 # D10: battery rear stop (0.3mm gap) under the beam; press bars run forward to the front frame (0.3mm above battery).
 s=s.union(box(3.9,69,3.3,15.95,0,-3)).union(box(2,28,19,16.9,0,-22))
 for y in (-17.5,17.5):s=s.union(box(14.4,3,7.1,25.1,y,-6.8))
 # D09: two arms from the right frame press the board bracket's top rail and tabs (0.2mm gap).
 for x in (-22,-6):s=s.union(box(4,23.5,2.1,x,22.75,-1.8))
 return s

# ---------------- Palm ----------------
put('10_巴掌定位底座_v07电池限位',retainer(oldstep('10_巴掌定位底座')),'#358fb8','palm')
for n in ('R10_巴掌舵机PG002外形参考','P_04_完整手掌75mm_带接口','P_02_插入连接块'):reuse(n)
bridge=box(66,22,3,c=22).cut(box(23.8,12.8,6,c=21))
for x in (-13.9,13.9):bridge=bridge.cut(cyl(1.2,6,x,0,21))
for x in (-29,29):
 for y in (-6,6):bridge=bridge.cut(cyl(1.7,6,x,y,21))
put('11_巴掌新舵机桥',bridge,'#358fb8','palm')
seat=ring(27,17,31.5,2).union(ring(27,24.3,33.5,2.9))
for x in (-29,29):
 seat=seat.union(box(8,20,6.5,x,0,25)).union(box(20,18,2,(-22 if x<0 else 24),0,31.5))
 for y in (-6,6):seat=seat.cut(cyl(1.7,12,x,y,24))
# D07: cover screws go into heat-set inserts in a 7mm boss under each ear.
for y in (-18,18):
 seat=seat.union(box(8,22,2,-29,math.copysign(11,y),31.5)).union(cyl(4,5,-29,y,26.5))
 seat=seat.cut(cyl(2.0,6.1,-29,y,27.5))
cap=ring(27,20.4,36.4,2)
bolts=[]
for deg in (45,135,225,315):
 a=math.radians(deg);x=cx+28.2*math.cos(a);y=28.2*math.sin(a);bolts.append((x,y))
 seat=seat.cut(cyl(4.8,3,x,y,34.4))
 seat=seat.union(cyl(4.5,4.9,x,y,29.5)).cut(cyl(1.7,10,x,y,28.5)).cut(nut(x,y,29.5))
 cap=cap.union(cyl(4.5,4,x,y,34.4)).cut(cyl(1.7,8,x,y,33)).cut(cyl(3.1,2.1,x,y,36.4))
cap=cap.cut(cyl(24.3,3,cx,0,33.4))
cap=cap.union(ring(27,20.4,36.4,2))
for x,y in bolts:cap=cap.cut(cyl(1.7,8,x,y,33)).cut(cyl(3.1,2.1,x,y,36.4))
# D06: bridge screws seat 1mm deeper (Z29.8) for ISO7380 button heads; the +X pair gets a clean notch
# through the radial ring instead of leaving 0.03-0.6mm slivers.
for x in (-29,29):
 for y in (-6,6):
  seat=seat.cut(cyl(3.2,8,x,y,29.8))
  if x>0:seat=seat.cut(box(7.2,7.2,3.1,x,y,33.4))
seat=seat.cut(cyl(24.3,5,cx,0,33.5))
rod=cq.importers.importStep(str(H/'Otto_75mm巴掌腕部接口_v02/STEP_结构件/05_完整连接杆_杆距51mm.step'))
rotor=rod.union(cyl(20,3)).union(cyl(24,2.5,z=33.5-rz).cut(cyl(17,5,z=32.5-rz)))
rotor=rotor.union(cyl(20,3.97,z=36-rz).cut(cyl(17,6,z=35-rz)))
for y in (-4,4):rotor=rotor.union(box(27,2,5,27.5,y,3))
horn=cq.importers.importStep(str(next(REF.glob('*half arm*.stp')))).translate((0,-20,-1.55))
v,_=horn.val().tessellate(.08);xy=np.unique(np.round([[a.x,a.y] for a in v],6),axis=0);xy=xy[ConvexHull(xy).vertices]
def outline(offset,z,h):return cq.Workplane('XY').polyline(xy.tolist()).close().offset2D(offset).extrude(h).translate((0,0,z))
rotor=rotor.union(outline(1.8,-2,2)).cut(outline(.3,-2.3,2.7)).cut(cyl(4.1,16,z=-10))
rotor=rotor.translate((cx,0,rz));horn=horn.translate((cx,0,rz))
put('13_独立承重座_v07',seat,'#f2ae45','palm')
cap=cap.cut(box(100,.3,20,cx,0,30))
for suffix,s in zip(('A','B'),sorted(cap.solids().vals(),key=lambda q:q.Center().y)):
 put('14'+suffix+'_半片限位压环',cq.Workplane('XY').newObject([s]),'#e9c877','palm')
put('15_承重转盘与加强接杆一体',rotor,'#418eb5','palm')
put('R11_原配舵盘_只传扭矩',horn,'#d5d9dc','palm',k='reference')
outer=box(75,75,34,c=3).edges('|Z').fillet(5).intersect(cyl(49,36,cx,0,2)).edges('>Z').fillet(5)
inner=box(70.2,70.2,33,c=2).edges('|Z').fillet(3).intersect(cyl(46.6,35,cx,0,1)).edges('>Z').fillet(3)
cover=outer.cut(inner).cut(cyl(27.5,10,cx,0,30))
for x,y in bolts:cover=cover.cut(cyl(4.9,10,x,y,30))
for y in (-18,18):
 cover=cover.union(cyl(3.6,3.5,-29,y,33.5)).cut(cyl(1.7,8,-29,y,32))
cover=cover.cut(seat)
# Four D7 driver holes over the deck screws: the palm head is assembled on the bench and bolted on as one unit.
for x in (-30,30):
 for y in (-30,30):cover=cover.cut(cyl(3.5,40,x,y,3))
put('12_承重转盘罩_v08四角刀孔',cover,'#61b5e4','palm')

# ---------------- Fist ----------------
base=cq.importers.importStep(str(V6/'STEP_审阅件/20_拳头底座_清理废弃孔耳.step'))
# D02: cable entry moved behind the motor tail (X-64.2..-58.5, 9mm wide); wire drops in before the guard wall.
base=base.union(box(6.6,12,11,-62.3,0,-8)).cut(box(5.7,9,13,-61.35,0,-7))
put('20_拳头底座_v07尾部入线',retainer(base),'#b9494b','fist')
for n in v6:
 if n.startswith('F_'):reuse(n)
guard=box(84,61,22,-26.5,0,3).edges('|Z').fillet(5).cut(box(87,56,24,-26.5,0,2).edges('|Z').fillet(3))
guard=guard.union(box(2.4,57,22,-67,0,3))
for y in (-30,30):
 guard=guard.union(cyl(6,2,-30,y,3)).cut(cyl(4.2,25,-30,y,5)).cut(cyl(1.7,6,-30,y,2))
put('21_拳头护罩_共用螺丝敞口',guard,'#da696b','fist')

# ================= Checks =================
M=meshes
board=cq.importers.importStep(str(REF/'Remote Control Receiver-XA003-XA004.stp')).rotate((0,0,0),(1,1,1),120).rotate((0,0,0),(1,0,0),90).translate((-17,5,-18))
bc=[]
for s in board.solids().vals():
 m=mesh(cq.Workplane('XY').newObject([s]))
 if not m.is_volume:
  b=s.BoundingBox();m=mesh(box(b.xlen,b.ylen,b.zlen,(b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,b.zmin))
 bc.append(m)
boardm=trimesh.boolean.union(bc,engine='manifold')
swsol=[mesh(switch_pose(cq.Workplane('XY').newObject([cq.Solid.makeSolid(swraw.shells().vals()[i])]))) for i in (0,15,17,19)]
BODY='01_原高身体_v08';PALMB='10_巴掌定位底座_v07电池限位';FISTB='20_拳头底座_v07尾部入线';COVER='12_承重转盘罩_v08四角刀孔';MOD='03_开关模块面板_v08'
checks['body_components']=len(body.split(only_watertight=False));checks['body_is_volume']=bool(body.is_volume)
static={'body':M[BODY],'panel':M[MOD],'board':boardm,'tray':M['02_竖置主板托架_布局草案'],'battery':M['R02_前置立放电池'],
 'usb_env':M['E02_USB数据线插拔预留'],'plug_env':M['E01_侧插头与弯线预留'],'hip-':M['E_hip_-25'],'hip+':M['E_hip_25'],'palm_base':M[PALMB],'fist_base':M[FISTB],'guard':M['21_拳头护罩_共用螺丝敞口']}
for i,s in enumerate(swsol):
 for n,m in static.items():checks[f'switch{i}_vs_{n}']=inter(s,m)
for top in ('palm_base','fist_base'):
 for n in ('body','board','tray','battery','hip-','hip+','plug_env','usb_env','panel'):checks[f'{top}_vs_{n}']=inter(static[top],static[n])
for n in ('board','tray','battery','panel','hip-','hip+','plug_env','usb_env'):checks[f'body_vs_{n}']=inter(static['body'],static[n])
checks['panel_vs_board']=inter(static['panel'],boardm)
def moved(m,t):m=m.copy();m.apply_translation(t);return m
for top in ('palm_base','fist_base'):
 checks[f'battery_back0.5_hits_{top}']=inter(moved(static['battery'],(-.5,0,0)),static[top])>0
 checks[f'battery_up0.5_hits_{top}']=inter(moved(static['battery'],(0,0,.5)),static[top])>0
 checks[f'tray_up0.4_hits_{top}']=inter(moved(static['tray'],(0,0,.4)),static[top])>0
checks['tray_slide_x0.5_hits_body_pins']=inter(moved(static['tray'],(.5,0,0)),static['body'])>0
# XH plug space ahead of each mouth: 6x7mm probe until it meets body/panel/board/USB envelope.
def free(y0,dirn):
 for d in np.arange(0,15,.25):
  c=trimesh.creation.box(extents=[6.2,.25,7]);c.apply_translation([-30.6+DX,y0+dirn*(d+.125),-16.2])
  for n in ('body','panel','board','usb_env','tray'):
   if inter(c,static[n])>1e-4:return round(float(d),2),n
 return 15,None
checks['XH_plusY_free_mm']=free(-4+DY,1);checks['XH_minusY_free_mm']=free(-35+DY,-1)
checks['panel_hole_edge_min_mm']=min(-33.5-1.7+38,6.5-2.5-1.7,-28.5-1.7+32)
# Palm: rotor sweep, servo, screw heads.
servo_raw=cq.importers.importStep(str(next(REF.glob('*Protection-PG002-PG001.stp'))))
servo=cq.Workplane('XY').newObject([servo_raw.solids().vals()[0]]).translate((-11.35,-5.9,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,25))
for name,a,b in [('seat_bridge',seat,bridge),('seat_cap',seat,cap),('rotor_seat',rotor,seat),('rotor_cap',rotor,cap),('rotor_horn',rotor,horn),('cover_seat',cover,seat),('cover_cap',cover,cap)]:checks[name]=vol(a,b)
for n in ('13_独立承重座_v07',COVER):checks[n+'_vs_servo']=vol(shapes[n],servo)
pb=shapes[PALMB]
checks['seat_vs_palm_base']=vol(seat,pb);checks['bridge_vs_palm_base']=vol(bridge,pb);checks['servo_vs_palm_base_mm3']=vol(servo,pb)
worst=0;where=None
for ang in range(0,360,10):
 r=rotor.rotate((cx,0,0),(cx,0,1),ang)
 for n,s in [('seat',seat),('cap',cap),('cover',cover),('bridge',bridge)]:
  vv=vol(r,s)
  if vv>worst:worst=vv;where=(ang,n)
checks['rotor_sweep_max_mm3']=worst;checks['rotor_sweep_worst']=where
heads=[]
for x in (-29,29):
 for y in (-6,6):heads.append(cyl(2.85,1.65,x,y,29.8))
hd=heads[0]
for h in heads[1:]:hd=hd.union(h)
checks['bridge_screw_ISO7380_vs_rotor_mm3']=max(vol(hd,rotor.rotate((cx,0,0),(cx,0,1),a)) for a in range(0,360,15))
checks['bridge_screw_ISO7380_head_top_gap_to_rotor_mm']=round(33.5-(29.8+1.65),2)
# Fist: motor/gearbox refs vs base, driver corridors, full crank cycle.
fixed_refs=[n for n in M if n.startswith('F_ref')]
checks['fist_base_vs_motor_refs_mm3']=sum(inter(M[FISTB],M[n]) for n in fixed_refs if M[n].is_volume)
checks['fist_base_v06_vs_motor_refs_mm3']=sum(inter(trimesh.load_mesh(V6/'装配网格/20_拳头底座_清理废弃孔耳.stl'),M[n]) for n in fixed_refs if M[n].is_volume)
for x in (-30,30):
 for y in (-30,30):
  z=5 if x<0 else 3;tool=cyl(3,80,x,y,z)
  checks[f'driver_{x}_{y}']=vol(tool,guard)+vol(tool,shapes[FISTB])
src=H/'队友拳头模块_2026-09-28_增量审阅/04_结构与硬件/Otto_CB1出拳头部_v01'
spec=importlib.util.spec_from_file_location('pg',src/'build_punch_head.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
head=mod.Head(json.loads((src/'parameters.json').read_text(encoding='utf-8')))
# Place the teammate model by a fixed motor part (the reused F_crank mesh was exported at 180deg).
off=M['F_ref_00'].bounds[0]-mesh(head.hardware['ref_00']).bounds[0]
checks['fist_cycle_offset']=np.round(off,3).tolist()
checks['fist_cycle_offset_consistent_ref07']=bool(np.allclose(mesh(head.hardware['ref_07']).bounds[0]+off,M['F_ref_07'].bounds[0],atol=.05))
fc={}
for ang in range(0,360,10):
 mv=head.moving(float(ang))
 for n in ('crank','link','carriage','glove','pin_A','pin_B','washer_A','washer_B'):
  if n not in mv:continue
  m=moved(mesh(mv[n]),off)
  for g in (FISTB,'21_拳头护罩_共用螺丝敞口'):
   vv=inter(m,M[g])
   if vv>1e-3:fc.setdefault(n+'_vs_'+g,[]).append((ang,round(vv,3)))
checks['fist_cycle_collisions']=fc

# ================= Assembly order: insertion paths and tool corridors =================
# Each step is checked against only the parts already present at that step.
A={}
def tz(x,y,z0,z1,r=3):c=trimesh.creation.cylinder(radius=r,height=z1-z0,sections=32);c.apply_translation([x,y,(z0+z1)/2]);return c
def tx(x0,x1,y,z,r=3):c=trimesh.creation.cylinder(radius=r,height=x1-x0,sections=32);c.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]));c.apply_translation([(x0+x1)/2,y,z]);return c
def ty(y0,y1,x,z,r=3):c=trimesh.creation.cylinder(radius=r,height=y1-y0,sections=32);c.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]));c.apply_translation([x,(y0+y1)/2,z]);return c
def hits(m,names):return {n:round(v,3) for n in names if (v:=inter(m,M[n] if isinstance(n,str) and n in M else static[n]))>1e-3}
def sweep(m,dirv,dist,names,step=.5):
 w={}
 for d in np.arange(step,dist+1e-6,step):
  for n,v in hits(moved(m,np.array(dirv)*d),names).items():w[n]=max(w.get(n,0),v)
 return w
def rot(m,a):m=m.copy();m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(a),[0,0,1],[cx,0,0]));return m
swm=trimesh.boolean.union(swsol,engine='manifold');cart=trimesh.boolean.union([swm,M[MOD]],engine='manifold')
# Bench 1: switch module. M2.5 from the PCB front along -X; 5mm driver shaft.
A['B1_switch_M2.5_front_driver']=hits(tx(EX+1.7,EX+60,EY,EZ,2.5),[MOD])|{('switch' if inter(tx(EX+1.7,EX+60,EY,EZ,2.5),swm)>1e-3 else 'switch_clear'):0}
# Bench 2: receiver to bracket, M2.5 along +Y at the four posts (free length before the board is met).
fl={}
for x in (-29,-5):
 for z in (-29.5,-6.5):
  y=-40
  while y<5 and inter(ty(-40,y+.5,x,z,2.3),boardm)<1e-3:y+=.5
  fl[f'{x},{z}']=y
A['B2_board_screw_corridor_reaches_Y']=fl
# Step 1: bracket+board drop in from above onto the pins.
A['S1_tray_board_drop_40mm']=sweep(trimesh.boolean.union([M['02_竖置主板托架_布局草案'],boardm],engine='manifold'),(0,0,1),40,['body'])
# Step 2: switch module slides in from behind (with or without a top module fitted).
A['S2_switch_module_slide_18mm']=sweep(cart,(-1,0,0),18,['body','board','tray',PALMB,FISTB,'21_拳头护罩_共用螺丝敞口'])
A['S2_panel_screw_driver_from_rear']={yb:hits(tx(-90,-43.9,yb,-28.5),['body',PALMB,FISTB,'21_拳头护罩_共用螺丝敞口',COVER,'R_foot_1','R_foot_-1','R_Leg_1','R_Leg_-1']+[n for n in M if n.startswith('F_') and M[n].is_volume]) for yb in (-33.5,2.5)}
# Step 3: battery drops into the front pocket.
A['S3_battery_drop_40mm']=sweep(M['R02_前置立放电池'],(0,0,1),40,['body','board','tray'])
# Step 4: complete attack module lowered on (palm head fully assembled on the bench; fist head complete).
palm_unit=[PALMB,'11_巴掌新舵机桥','13_独立承重座_v07','14A_半片限位压环','14B_半片限位压环','15_承重转盘与加强接杆一体',COVER,'P_04_完整手掌75mm_带接口','P_02_插入连接块']
fist_unit=[FISTB,'21_拳头护罩_共用螺丝敞口']+[n for n in M if n.startswith('F_') and M[n].is_volume]
inside=['body','board','tray','battery',MOD]
for nm,unit in (('palm',palm_unit),('fist',fist_unit)):
 u=trimesh.boolean.union([M[n] for n in unit if M[n].is_volume],engine='manifold')
 A[f'S4_{nm}_module_lower_40mm']=sweep(u,(0,0,1),40,inside)
# Step 4b: four deck screws driven through the fitted module. Palm: through cover holes; hand may be rotated.
for x in (-30,30):
 for y in (-30,30):
  t=tz(x,y,3 if True else 3,90)
  st=hits(t,[n for n in palm_unit if not n.startswith(('15_','P_'))])
  ok=[a for a in range(0,360,15) if not any(inter(t,rot(M[n],a))>1e-3 for n in ('15_承重转盘与加强接杆一体','P_04_完整手掌75mm_带接口','P_02_插入连接块'))]
  A[f'S4_palm_deck_{x}_{y}']={'static_hits':st,'clear_hand_angles_deg':f'{len(ok)}/24'}
  z0=5 if x<0 else 3;t=tz(x,y,z0,90)
  st=hits(t,fist_unit)
  okc=[a for a in range(0,360,30) if not any(inter(t,moved(mesh(head.moving(float(a))[n]),off))>1e-3 for n in ('crank','link','carriage','glove'))]
  A[f'S4_fist_deck_{x}_{y}']={'static_hits':st,'clear_crank_angles_deg':f'{len(okc)}/12'}
# Palm bench steps: bridge screws before the rotor; cap bolts and cover screws with the hand turned away.
A['P1_bridge_screws_open_above']={f'{x},{y}':hits(tz(x,y,29.8,90,1.5),[PALMB,'11_巴掌新舵机桥','13_独立承重座_v07']) for x in (-29,29) for y in (-6,6)}
for lab,pts,z0 in (('P2_cap_bolts',bolts,38.4),('P3_cover_screws',[(-29,-18),(-29,18)],37)):
 res={}
 for x,y in pts:
  t=tz(x,y,z0,90)
  ok=[a for a in range(0,360,15) if not any(inter(t,rot(M[n],a))>1e-3 for n in ('15_承重转盘与加强接杆一体','P_04_完整手掌75mm_带接口','P_02_插入连接块'))]
  res[f'{x:.1f},{y:.1f}']={'static':hits(t,[COVER,'14A_半片限位压环','14B_半片限位压环']) if lab=='P3_cover_screws' else hits(t,[COVER]),'clear_hand_angles':f'{len(ok)}/24'}
 A[lab]=res
checks['assembly']=A
report={'checks':checks,'switch_shift_mm':[DX,DY,0],'status':'v08 trial-fit model. Inserts, plug space and sliding bearing still need one physical test build. Do not batch print.'}
(P/'接口审阅检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
(P/'装配清单.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=1,default=str));print('BUILD_COMPLETE')
