"""Focused v09 rebuild and independent check of the modified switch mount only."""
from pathlib import Path
import json,math,hashlib
import numpy as np,cadquery as cq,trimesh
P=Path(__file__).resolve().parent
source=(P/'build_v09.py').read_text(encoding='utf-8')
# Reuse the canonical generator definitions, then rebuild only the modified switch module.
exec(source.split('# ---------------- Body:')[0])
block=source[source.index("swraw=cq.importers"):source.index('# D-eyes:')]
block='\n'.join(line for line in block.splitlines() if not line.startswith("put('R03_"))
exec(block)
manifest=json.loads((P/'装配清单.json').read_text(encoding='utf-8'))
M={o['name']:trimesh.load_mesh(P/'装配网格'/o['file']) for o in manifest}
MOD='03_开关模块面板_v09_安装耳对中';old=P.parent/'双机连接加固_v08'
report={'scope':'Only switch mounting-ear hole and affected paths rechecked. Unchanged checks inherited, not rerun.','holes':{},'checks_mm3':{},'paths':{}}
oldstep=cq.importers.importStep(str(old/'STEP_审阅件/03_开关模块面板_v08.step'))
newstep=cq.importers.importStep(str(P/'STEP_审阅件'/(MOD+'.step')))
def axis_from_part(s,radius):
 out=[]
 for f in s.val().Faces():
  if f.geomType()=='CYLINDER':
   c=f._geomAdaptor().Cylinder();a=c.Axis();v=a.Direction();q=a.Location()
   if abs(c.Radius()-radius)<1e-6 and abs(v.X())>.99999:out.append([q.Y(),q.Z()])
 assert out
 return out[0]
for version,s in [('v08',oldstep),('v09',newstep)]:
 yz=axis_from_part(s,1.05);err=float(np.linalg.norm(np.array(yz)-[EY,EZ]));report['holes'][version]={'pilot_center_YZ':yz,'PCB_hole_center_YZ':[EY,EZ],'offset_mm':err}
assert report['holes']['v08']['offset_mm']>.8
assert report['holes']['v09']['offset_mm']<1e-6
# A 2.5mm nominal screw must pass through the actual 2.7mm PCB hole.
pcbm=mesh(cq.Workplane('XY').newObject([pcb]),fine=True)
for version in ['v08','v09']:
 y,z=report['holes'][version]['pilot_center_YZ'];pin=mesh(cylx(1.25,pb_.xlen+.2,pb_.xmin-.1,y,z),fine=True)
 vv=inter(pin,pcbm);report['checks_mm3'][version+'_M2.5_shaft_vs_PCB']=vv
assert report['checks_mm3']['v08_M2.5_shaft_vs_PCB']>.01
assert report['checks_mm3']['v09_M2.5_shaft_vs_PCB']<.001
# Component references use same conservative closures/bboxes as v08, disclosed in report.
board=cq.importers.importStep(str(REF/'Remote Control Receiver-XA003-XA004.stp')).rotate((0,0,0),(1,1,1),120).rotate((0,0,0),(1,0,0),90).translate((-17,5,-18))
bc=[]
for sh in board.solids().vals():
 mm=mesh(cq.Workplane('XY').newObject([sh]))
 if not mm.is_volume:
  b=sh.BoundingBox();mm=mesh(box(b.xlen,b.ylen,b.zlen,(b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,b.zmin))
 bc.append(mm)
boardm=trimesh.boolean.union(bc,engine='manifold')
swsol=[mesh(switch_pose(cq.Workplane('XY').newObject([cq.Solid.makeSolid(swraw.shells().vals()[i])])),fine=True) for i in (0,15,17,19)]
SW=trimesh.boolean.union(swsol,engine='manifold')
obstacles={n:M[n] for n in ['01_原高身体_v08','02_竖置主板托架_布局草案','R02_前置立放电池','E02_USB数据线插拔预留','E01_侧插头与弯线预留','10_巴掌定位底座_v07电池限位','20_拳头底座_v07尾部入线','21_拳头护罩_共用螺丝敞口']}
obstacles['receiver_conservative']=boardm;obstacles['switch_closed_solids']=SW
for name,m in obstacles.items():report['checks_mm3']['module_vs_'+name]=inter(M[MOD],m)
assert max(v for k,v in report['checks_mm3'].items() if k.startswith('module_vs_'))<.001
# Bench screwdriver corridor and actual PCB screw head envelope (no full purchased screw spec claim).
tool=mesh(cylx(2.5,60,EX+1.7,EY,EZ),fine=True)
report['checks_mm3']['bench_driver_vs_module']=inter(tool,M[MOD]);report['checks_mm3']['bench_driver_vs_switch']=inter(tool,SW)
assert report['checks_mm3']['bench_driver_vs_module']<.001 and report['checks_mm3']['bench_driver_vs_switch']<.001
# Insertion: check altered module, and complete module+switch, against the installed assembly.
cart=trimesh.boolean.union([M[MOD],SW],engine='manifold');targets={k:m for k,m in obstacles.items() if k!='switch_closed_solids'}
collisions={}
for d in np.arange(0,18.001,.5):
 moving=cart.copy();moving.apply_translation([-d,0,0])
 for name,m in targets.items():
  vv=inter(moving,m)
  if vv>.001:collisions.setdefault(name,[]).append([float(d),vv])
report['paths']['rear_insertion_0_to_18mm_step_0.5']=collisions
assert not collisions,collisions
# Verify unchanged outer two bolt axes from STEP, distinct from the corrected middle PCB hole.
report['outer_panel_M3_axes_YZ']=sorted([ [f._geomAdaptor().Cylinder().Axis().Location().Y(),f._geomAdaptor().Cylinder().Axis().Location().Z()] for f in newstep.val().Faces() if f.geomType()=='CYLINDER' and abs(f._geomAdaptor().Cylinder().Radius()-1.7)<1e-6])
assert np.allclose(report['outer_panel_M3_axes_YZ'],[[-33.5,-28.5],[2.5,-28.5]],atol=1e-6)
mm=M[MOD];report['mesh']={'watertight':bool(mm.is_watertight),'positive_volume':bool(mm.is_volume),'CAD_solids':len(newstep.solids().vals())};assert mm.is_volume and len(newstep.solids().vals())==1
changed=[]
for o in manifest:
 if o['name']==MOD:continue
 prev=old/'装配网格'/o['file'];now=P/'装配网格'/o['file']
 if hashlib.sha256(prev.read_bytes()).digest()!=hashlib.sha256(now.read_bytes()).digest():changed.append(o['name'])
report['unexpected_other_mesh_changes']=changed;assert not changed
report['note']='Screw pilot intentionally smaller than M2.5 for self tapping. Interference in plastic pilot is intended; PCB hole must clear shank. Physical thread strength remains untested.'
(P/'v09_开关安装孔与装配复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2));print('FOCUSED_CHECK_PASS')
