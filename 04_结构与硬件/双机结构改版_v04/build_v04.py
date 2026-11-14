"""Offline CAD review build. No serial, network, firmware or original-file writes."""
from pathlib import Path
import json,math,importlib.util
import numpy as np
import cadquery as cq
import trimesh

OUT=Path(__file__).resolve().parent
H=OUT.parent; ROOT=H.parent; REF=ROOT/'01_研究参考'
P=json.loads((OUT/'parameters_v04.json').read_text(encoding='utf-8-sig'))
T=P['deck_z_mm']; W=P['body_outer_mm']; WALL=P['body_wall_mm']
for d in ['STEP_审阅模型','STL_审阅勿批量打印','装配网格','预览']:(OUT/d).mkdir(exist_ok=True)
report={'status':'CAD review only, not print released','parameters':P,'parts':{},'checks':{},'unverified':['actual SG90 fit','physical USB plug envelope','switch version','wiring bending radius','mass/CG and dynamic stability','actual charging hardware']}
objects=[]; shapes={}; meshparts={}

def box(x,y,z,cx=0,cy=0,z0=0):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((cx,cy,z0))
def cyl(r,h,x=0,y=0,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def rounded(x,y,z,cx=0,cy=0,z0=0,r=3):return box(x,y,z,cx,cy,z0).edges('|Z').fillet(r)
def nut(x,y,z,af=5.8,h=2.8):return cq.Workplane('XY').polygon(6,af/math.cos(math.pi/6)).extrude(h).translate((x,y,z))
def mesh(obj):
 v,f=obj.val().tessellate(.14)
 return trimesh.Trimesh(np.array([a.toTuple() for a in v]),np.array(f),process=True)
def addmesh(name,m,color,group='common',kind='part'):
 m=m.copy();m.export(OUT/'装配网格'/(name+'.stl'))
 objects.append({'name':name,'file':name+'.stl','color':color,'group':group,'kind':kind})
 meshparts[name]=m
def add(name,obj,color,group='common',kind='part'):
 shapes[name]=obj
 addmesh(name,mesh(obj),color,group,kind)
 if kind=='part':
  assert obj.val().isValid(),name
  count=len(obj.solids().vals());assert count==1,(name,count)
  cq.exporters.export(obj,str(OUT/'STEP_审阅模型'/(name+'.step')))
  m=meshparts[name];assert m.is_volume,(name,'not closed positive mesh')
  pr=m.copy();pr.apply_translation((0,0,-pr.bounds[0,2]));pr.export(OUT/'STL_审阅勿批量打印'/(name+'.stl'))
  report['parts'][name]={'solid_count':count,'valid':True,'watertight':bool(m.is_watertight),'bounds_mm':m.bounds.tolist(),'volume_mm3':float(m.volume)}
def overlap(a,b):
 q=a.intersect(b);return sum(s.Volume() for s in q.solids().vals())

# Preserve the exact original lower mesh and all leg/hip mounting geometry.
old=trimesh.load_mesh(REF/'robot-battle-reference/Otto-V9/3Dprint/OttoDIY_body_V9.stl')
old.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,0,1]))
lower=trimesh.boolean.intersection([old,mesh(box(150,150,30,z0=-54))],engine='manifold')
shell=rounded(W,W,T+25,z0=-25,r=5).cut(rounded(W-2*WALL,W-2*WALL,T+27,z0=-26,r=3))
transition=rounded(W,W,2,z0=-25.5,r=5).cut(rounded(65,65,4,z0=-26.5,r=3))
shell=shell.union(transition)
# Rear USB access: larger than metal connector, recessed access for plug body.
shell=shell.cut(box(14,20,14,-36,0,-21.5))
# Side-rear switch pocket: removable panel; charge maintenance hatch at rear-left.
shell=shell.cut(box(34,12,24,7,36,-11))
shell=shell.cut(box(12,18,14,-36,-23,0))
shell=shell.cut(box(14,14,12,-36,-18,T-9))
for x in (-13,27):
 support=box(7,7,9,x,32.5,-.5)
 bore=cq.Workplane('XZ',origin=(x,40,4)).circle(1.7).extrude(14)
 pocket=cq.Workplane('XZ',origin=(x,31,4)).polygon(6,5.8/math.cos(math.pi/6)).extrude(3)
 shell=shell.union(support).cut(bore).cut(pocket)
for y in (-31,-15):
 support=box(7,7,8,-33,y,6)
 bore=cq.Workplane('YZ',origin=(-42,y,10)).circle(1.7).extrude(16)
 pocket=cq.Workplane('YZ',origin=(-32,y,10)).polygon(6,5.8/math.cos(math.pi/6)).extrude(3)
 shell=shell.union(support).cut(bore).cut(pocket)
for x,y in P['top_mount_xy_mm']:
 boss=cyl(4.6,13,x,y,T-13).cut(cyl(1.7,15,x,y,T-14)).cut(nut(x,y,T-13))
 # Connected webs transfer impact into shell, not screw threads alone.
 boss=boss.union(box(7,7,10,x+math.copysign(3.5,x),y,T-13)).union(box(7,7,10,x,y+math.copysign(3.5,y),T-13))
 boss=boss.cut(cyl(1.7,16,x,y,T-14)).cut(nut(x,y,T-13))
 shell=shell.union(boss)
# Battery base integrated into shell; actual cell body isolated from PCB.
basket=box(55,32,2,z0=-38)
for x in (-27,27):basket=basket.union(box(2,32,6,x,z0=-37))
for y in (-15.5,15.5):
 basket=basket.union(box(55,2,6,0,y,-37))
 for x in (-17,17):basket=basket.cut(box(5,6,2,x,y,-35.5))
# Side cable anchors, clear of ankle/hip linkages. Smooth slot edges later.
for y in (-32,32):
 for x in ((-10,16) if y<0 else (-23,)):
  anchor=box(8,6,4,x,y,-5).cut(box(4,8,1.8,x,y,-4))
  shell=shell.union(anchor)
# Board carrier attachment ears, M3 clearance and captured nuts.
for y in (-29,29):
 shell=shell.union(box(10,12,6,-17,y,-18).cut(cyl(1.7,9,-17,y,-19)).cut(nut(-17,y,-18)))
# Front shallow badge and two raised eyes unambiguously identify front.
badge=box(2,26,10,37.5,0,2)
shell=shell.union(badge)
for y in (-7,7):shell=shell.union(box(1.2,4,4,39,y,6))
newbody=trimesh.boolean.union([lower,mesh(shell),mesh(basket)],engine='manifold')
assert newbody.is_volume
addmesh('01_共用身体_下部原Otto基准',newbody,'#cbd9e2',kind='body')
newbody.export(OUT/'STL_审阅勿批量打印'/'01_共用身体_下部原Otto基准.stl')
cq.exporters.export(shell.union(basket),str(OUT/'STEP_审阅模型'/'01_上部壳体_下部原网格另见STL.step'))
report['parts']['01_共用身体_下部原Otto基准']={'watertight':bool(newbody.is_watertight),'positive_volume':bool(newbody.is_volume),'preserved_below_z':-25,'note':'Body STL incorporates original lower mesh; STEP contains only newly authored upper BRep.'}
# Official complete receiver, includes core; do not double count.
board=cq.importers.importStep(str(REF/'CyberBrick1迁移研究/Remote Control Receiver-XA003-XA004.stp')).rotate((0,0,0),(1,1,1),120).translate(tuple(P['board_center_mm']))
add('R01_原厂接收组合',board,'#35886f',kind='reference')
# Peripheral carrier, open underside for core/USB. M2.5 board holes, M3 body ears.
carrier=None
for y in (-11.5,11.5):
 for x in (-29,-5):
  a=cyl(2.8,5.8,x,y,-12).cut(cyl(1.35,8,x,y,-13)).cut(nut(x,y,-12,af=4.9,h=2))
  a=a.union(box(5,8,2,x,y+math.copysign(5,y),-12))
  carrier=a if carrier is None else carrier.union(a)
for y in (-19,19):carrier=carrier.union(box(36,4,2,-15,y,-12))
carrier=carrier.union(box(3,42,2,1.5,0,-12))
for y in (-24,24):carrier=carrier.union(box(8,14,2,-17,y,-12))
for y in (-29,29):carrier=carrier.cut(cyl(1.7,5,-17,y,-13))
add('02_开底主板托架_M2.5板孔',carrier,'#f2ae45')
# Battery model trimmed to cell body. 100mm rigid CAD wire is NOT the battery.
braw=cq.importers.importStep(str(OUT/'测量临时文件/14500 7.4V 800mAh Li-ion Battery-PC003.stp'))
batt=braw.intersect(box(50,51.2,40,0,25.6,-20)).rotate((0,0,0),(0,0,1),90).translate((25.6,0,P['battery_bottom_mm']+8.15))
add('R02_PC003电池本体',batt,'#547ee8',kind='reference')
# XA007 shells are for visualization only; collision uses conservative box.
swraw=cq.importers.importStep(str(OUT/'测量临时文件/Power Switch Board with 2Pin XH2.54 Connector-XA007.STEP'))
# Original +Y is the toggle/component side. Preserve +Y toward the outside.
# Original X (ear direction) maps to +Z; original Z maps to -X.
# Recess the PCB so the XH connector bodies remain inside the side wall.
sw=swraw.rotate((0,0,0),(0,1,0),-90).translate((7,22,-2))
add('R03_XA007开关_曲面参考',sw,'#444f61',kind='reference')
report['switch_orientation']={'outward_axis':'+Y','pcb_y_mm':[21.98,23.62],
 'xh_bodies_y_mm':[23.4,29.6],'toggle_tip_y_mm':37.1627,
 'note':'Original +Y preserved; recessed toggle is reachable through side window. Cable-end plugs still require physical check.'}
# Windowed side bezel: PCB ear mount separate from clip-tolerance assumptions.
bezel=box(44,2.4,34,7,38.7,-13).cut(box(34,5,20,7,38.7,-10))
for x in (-13,27):bezel=bezel.cut(cq.Workplane('XZ',origin=(x,42,4)).circle(1.7).extrude(10))
pad=box(7,15.5,5.7,7,31.75,5.4).cut(cq.Workplane('XZ',origin=(7,42,8.25)).circle(1.35).extrude(22))
bezel=bezel.union(pad)
add('03_开关可换安装面板',bezel,'#4d677a')
# Maintenance opening cover, screws normal to rear panel.
plate=box(2.4,24,20,-38.7,-23,-3)
for y in (-31,-15):plate=plate.cut(cq.Workplane('YZ',origin=(-41,y,10)).circle(1.7).extrude(8))
add('04_充电维护口盲板_待模块确认',plate,'#4d677a')
# Plug/cable reserves in display are envelopes, not actual purchased parts.
plug=box(12,20,18,-14.5,0,4.78)
add('E01_舵机插头与弯线预留',plug,'#e9b3e3',kind='envelope')
usb=box(18,16,10,-38,0,-19.5)
add('E02_USB数据线插拔预留',usb,'#6dd3da',kind='envelope')

def deck():
 s=rounded(75,75,3,z0=T,r=5).cut(rounded(61,61,5,z0=T-1,r=4))
 # Keyed locating tabs keep shear off fasteners, fits within 69.8mm inner body.
 for y in (-33,33):s=s.union(box(36,2,3,0,y,T-3))
 for x,y in P['top_mount_xy_mm']:s=s.cut(cyl(1.7,8,x,y,T-4))
 return s
# Palm frame maintains existing bridge z=22 and arm geometry relative to module.
frame=deck()
for x in (-29,29):
 post=box(8,22,19,x,0,T+3).cut(box(5.8,24,2.8,x,0,T+16))
 for y in (-6,6):post=post.cut(cyl(1.65,9,x,y,T+15))
 frame=frame.union(post)
add('10_巴掌定位底座',frame,'#358fb8','palm')
bridge=box(66,22,3,z0=T+22).cut(box(23.8,12.8,6,z0=T+21))
for x in (-13.9,13.9):bridge=bridge.cut(cyl(1.2,6,x,0,T+21))
for x in (-29,29):
 for y in (-6,6):bridge=bridge.cut(cyl(1.65,6,x,y,T+21))
for x in (-20,20):
 bridge=bridge.union(cyl(4.5,3,x,0,T+19)).cut(cyl(1.7,8,x,0,T+18)).cut(nut(x,0,T+19))
add('11_巴掌原基准舵机桥',bridge,'#358fb8','palm')
raw=cq.importers.importStep(str(REF/'CyberBrick1迁移研究/9g Servo Motor with Clutch Protection-PG002-PG001.stp'))
servo=cq.Workplane('XY').newObject([raw.solids().vals()[0]]).translate((-11.35,-5.9,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,T+25))
add('R10_巴掌舵机PG002外形参考',servo,'#434d5d','palm','reference')
# Separate snap-over shell concept with 4 clear mounting holes onto body corners.
cover=rounded(75,75,34,z0=T+3,r=5).cut(rounded(70.2,70.2,33,z0=T+2,r=3))
cover=cover.cut(cyl(10,10,5.34,0,T+32))
# Bridge ends and posts stay inside lid, accessible after cover removal.
for x,y in P['top_mount_xy_mm']:
 cover=cover.cut(cyl(3.5,40,x,y,T+1))
for x in (-20,20):cover=cover.union(cyl(3.6,12,x,0,T+25)).cut(cyl(1.7,16,x,0,T+24))
for y in (-20,-10,10,20):cover=cover.cut(box(12,3,5,-19,y,T+33))
add('12_巴掌可拆圆角头罩',cover,'#61b5e4','palm')
# Existing palm/rod/connector in verified axis-local assembly coordinates.
for name,color in [('04_完整手掌75mm_带接口','#64bafa'),('05_完整连接杆_杆距51mm','#418eb5'),('02_插入连接块','#f2b35f')]:
 m=trimesh.load_mesh(H/'Otto_75mm巴掌腕部接口_v02/装配坐标_勿直接打印'/(name+'.stl'))
 m.apply_translation((5.34,0,T+39.97));addmesh('P_'+name,m,color,'palm','reuse')
# Fist uses the existing complete assembly and preserved mechanism source.
src=H/'队友拳头模块_2026-09-28_增量审阅/04_结构与硬件/Otto_CB1出拳头部_v01'
spec=importlib.util.spec_from_file_location('punch_geometry',src/'build_punch_head.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
head=mod.Head(json.loads((src/'parameters.json').read_text(encoding='utf-8')))
base=head.parts['01_mount_and_guides'].translate((-22,0,T))
# Remove nonfunctional old outboard fastening ears, retain motor cradle and guides.
for x in (-62,18):
 for y in (-24,24):base=base.cut(cyl(4.6,3.2,x,y,T-.1))
base=base.union(deck())
for y in (-24,24):base=base.union(box(70,7,3,-16,y,T))
# Under-motor hidden dogleg channel: tail -> side of board -> body entry.
duct_outer=box(16,29,10,-54,-9,T-8).union(box(39,12,10,-38,-18,T-8))
duct_void=box(10,24,9,-54,-9,T-6).union(box(34,8,9,-38,-18,T-6))
base=base.union(duct_outer).cut(duct_void)
base=base.cut(box(10,10,20,-54,0,T-7)).cut(box(10,10,20,-24,-18,T-10))
for x,y in P['top_mount_xy_mm']:base=base.cut(cyl(1.7,20,x,y,T-10))
for y in (-28.5,28.5):
 base=base.union(cyl(4,3,-46,y,T-3)).cut(cyl(1.7,9,-46,y,T-4)).cut(nut(-46,y,T-3))
# Clear front old solid deck; bridge paths and rear cradle remain.
base=base.cut(box(20,24,5,23,0,T-1))
add('20_拳头固定底座_含隐藏过线槽',base,'#b9494b','fist')
for name,obj in head.hardware.items():add('F_'+name,obj.translate((-22,0,T)),'#828d97','fist','reference')
for name,obj in head.fixed.items():
 if name.startswith('guide_rod'):add('F_'+name,obj.translate((-22,0,T)),'#a9b6bd','fist','reference')
for name,obj in head.moving(180).items():
 if name in ('crank','link','carriage'):add('F_'+name,obj.translate((-22,0,T)),{'crank':'#e6ac43','link':'#48ac93','carriage':'#508ac9'}[name],'fist','reuse')
# Fist actual positioned print mesh: minimum restoration from old assembly guide.
fprint=trimesh.load_mesh(next((H/'拳头_全套打印包_2026-09-29').glob('05_*.stl')))
# connector min=(16,-8,39.8); actual STL preserves min-normalized fist extents.
# Locate exact restoration from original user's largest component via scipy, no pose guesses.
rawf=trimesh.load_mesh(H/'拳头_整体比例预览_v03/拳头微调导出.stl')
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
a=rawf.face_adjacency;g=sp.coo_matrix((np.ones(len(a)*2),(np.r_[a[:,0],a[:,1]],np.r_[a[:,1],a[:,0]])),shape=(len(rawf.faces),)*2).tocsr()
_,lab=connected_components(g,directed=False);ids=np.flatnonzero(lab==np.argmax(np.bincount(lab))); fm=rawf.submesh([ids],append=True,repair=False)
fprint.apply_translation((16,fm.bounds[0,1],fm.bounds[0,2]+T));addmesh('F_实际拳头腕杆',fprint,'#e35858','fist','reuse')
# Lower side guards only, leaving crank and slider swept envelope open.
guard=rounded(84,61,22,-26.5,0,T+3,r=5).cut(rounded(87,56,24,-26.5,0,T+2,r=3))
# closed transverse back joins the two cheeks, open front for moving members
guard=guard.union(box(2.4,57,22,-67,0,T+3))
for y in (-28.5,28.5):
 guard=guard.union(box(10,9,3,-46,y,T+3))
 guard=guard.cut(cyl(1.7,9,-46,y,T+2))
add('21_拳头轻量侧护罩',guard,'#da696b','fist')
# Exact old legs/feet, rotated with body; neither mesh nor servo axis changed.
for stem in ('Leg','foot'):
 m=trimesh.load_mesh(REF/f'robot-battle-reference/Otto-V9/3Dprint/OttoDIY_{stem}_V9.stl')
 for side in (1,-1):
  q=m.copy()
  if side<0:q.apply_transform(np.diag([-1,1,1,1]))
  q.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,0,1]))
  addmesh(f'R_{stem}_{side}',q,'#90a9bd',kind='reuse')
# Conservative hip envelopes at existing mounting locations (not actual SG90 CAD).
for y in (-25,25):add('E_hip_'+str(y),box(24,13,24,5,y,-37),'#6f7c90',kind='envelope')

checks=[('board_vs_carrier',board,carrier),('battery_vs_board',batt,board),('palm_servo_vs_bridge',servo,bridge),('palm_servo_vs_cover',servo,cover)]
for name,a,b in checks:report['checks'][name+'_mm3']=overlap(a,b)
for name,obj in [('palm_deck',frame),('fist_base',base),('switch_bezel',bezel),('charge_plate',plate)]:
 report['checks'][name+'_vs_upper_body_mm3']=overlap(obj,shell.union(basket))
report['checks']['fist_guard_vs_base_mm3']=overlap(guard,base)
report['checks']['palm_cover_vs_frame_mm3']=overlap(cover,frame)
report['checks']['palm_cover_vs_bridge_mm3']=overlap(cover,bridge)
# Mesh intersection against complete preserved body; use exact solids except switch.
for key in ('R01_原厂接收组合','R02_PC003电池本体','02_开底主板托架_M2.5板孔','E_hip_-25','E_hip_25'):
 if key=='R01_原厂接收组合':
  report['checks'][key+'_vs_body_mm3']=overlap(board,shell.union(basket))
 else:
  q=trimesh.boolean.intersection([newbody,meshparts[key]],engine='manifold');report['checks'][key+'_vs_body_mm3']=float(q.volume)
 if key.startswith('E_hip'):
  q=trimesh.boolean.intersection([old,meshparts[key]],engine='manifold');report['checks'][key+'_vs_original_body_baseline_mm3']=float(q.volume)
report['checks']['servo_plug_envelope_top_mm']=22.78
report['checks']['deck_clearance_above_plug_envelope_mm']=T-22.78
report['checks']['attack_module_height_increase_mm']=T
# Entire 360-degree mechanism scan against newly added guard; 5 degree discretization.
maximum=0; worst=None
for ang in range(0,360,5):
 for name,obj in head.moving(ang).items():
  if name in ('crank','link','carriage','pin_A','pin_B','washer_A','washer_B'):
   v=overlap(obj.translate((-22,0,T)),guard)
   if v>maximum:maximum=v;worst=[ang,name]
report['checks']['new_guard_sweep_max_overlap_mm3']=maximum;report['checks']['new_guard_sweep_worst']=worst
report['checks']['sweep_scope']='5-degree sampled original mechanism and modeled pin envelopes vs NEW guard only; actual fist, wires and every screw not included.'
(OUT/'几何检查报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'装配清单.json').write_text(json.dumps(objects,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report['checks'],ensure_ascii=False,indent=2))
# Complete editable BRep assembly excludes original mesh-only hand and body bottom.
for variant in ('palm','fist'):
 ass=cq.Assembly(name='v04_'+variant)
 for o in objects:
  if o['name'] in shapes and o['group'] in ('common',variant) and o['kind']!='envelope':
   c=o['color'];ass.add(shapes[o['name']],name=o['name'],color=cq.Color(*[int(c[i:i+2],16)/255 for i in (1,3,5)]))
 ass.save(str(OUT/'STEP_审阅模型'/('装配_'+variant+'_不含原网格件.step')))
print('BUILD_COMPLETE')
