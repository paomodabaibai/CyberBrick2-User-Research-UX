from pathlib import Path
import json
import cadquery as cq
import trimesh
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
REF=ROOT/'01_研究参考'
STL=OUT/'STL_打印件';STEP=OUT/'STEP_可编辑实体'
STL.mkdir(exist_ok=True);STEP.mkdir(exist_ok=True)
# mm; assembly body rim z=0; long servo dimension along X.
P=dict(body_outer=69.0,body_clearance_per_side=0.4,frame_outer=75.0,
       skirt_depth=8.0,lip_thickness=3.0,lip_opening=64.0,
       bridge_bottom=22.0,bridge_thickness=3.0,
       servo_opening_x=23.8,servo_opening_y=12.8,servo_ear_pitch=27.8,
       body_mount_hole=3.2,servo_mount_hole=2.4,shaft_offset_x=5.34)
cfg=OUT/'parameters.json'
if cfg.exists(): P.update(json.loads(cfg.read_text(encoding='utf-8-sig')))
cfg.write_text(json.dumps(P,indent=2),encoding='utf-8')

def box(x,y,z,cx=0,cy=0,z0=0):
 return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((cx,cy,z0))
def hole(r,h,x=0,y=0,z=0):
 return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def ear_holes(s,z,h):
 for x in (-P['servo_ear_pitch']/2,P['servo_ear_pitch']/2):
  s=s.cut(hole(P['servo_mount_hole']/2,h,x,0,z))
 return s

gap=P['body_outer']+2*P['body_clearance_per_side']
frame=box(P['frame_outer'],P['frame_outer'],P['skirt_depth']+P['lip_thickness'],z0=-P['skirt_depth']).cut(box(gap,gap,P['skirt_depth']+.01,z0=-P['skirt_depth']-.01)).cut(box(P['lip_opening'],P['lip_opening'],P['lip_thickness']+.1,z0=0))
# Two outer pillars; M3 nuts slide in from front/rear, two per pillar.
for x in (-33.5,33.5):
 post=box(8,22,P['bridge_bottom']-P['lip_thickness'],x,z0=P['lip_thickness'])
 post=post.cut(box(5.8,24,2.8,x,z0=16))
 for y in (-6,6):post=post.cut(hole(1.65,8,x,y,15))
 frame=frame.union(post)
# Side mounting screws along X, centred 4mm below body rim.
side_bore=cq.Workplane('YZ',origin=(-40,0,-4)).circle(1.6).extrude(80)
frame=frame.cut(side_bore)
bridge=box(P['frame_outer'],22,P['bridge_thickness'],z0=P['bridge_bottom']).cut(box(P['servo_opening_x'],P['servo_opening_y'],40,z0=0))
bridge=ear_holes(bridge,21,5)
for x in (-33.5,33.5):
 for y in (-6,6):bridge=bridge.cut(hole(1.65,5,x,y,21))
# Low-cost gauges, independent of full frame.
gauge=box(P['frame_outer'],P['frame_outer'],3).cut(box(gap,gap,5,z0=-1))
servo_gauge=ear_holes(box(38,22,3).cut(box(P['servo_opening_x'],P['servo_opening_y'],5,z0=-1)),-1,5)
# Prototype horn adapter: uses half-arm hole centres +6.75 and +12.75.
arm=box(50,10,3,20).edges('|Z').fillet(1.0).cut(hole(4.1,5,z=-1))
for x in (6.75,12.75):arm=arm.cut(hole(.8,5,x,0,-1))
for x in (35,40):arm=arm.cut(hole(1.1,5,x,0,-1))
# Upright small palm, horizontal fingers; detachable from radial arm.
palm=box(14,10,3,38,z0=3)
palm=palm.union(box(12,3,23,49,z0=3))
for z in (7,12,17,22):palm=palm.union(box(8,3,3,58,z0=z))
palm=palm.union(box(7,3,4,41.5,z0=7))
for x in (35,40):palm=palm.cut(hole(1.1,5,x,0,2))
parts={'01_body_fit_gauge':gauge,'02_servo_fit_gauge':servo_gauge,
       '03_body_mount_frame':frame,'04_servo_bridge':bridge,
       '05_horn_arm_trial':arm,'06_palm_trial':palm}
report={'parameters':P,'parts':{},'checks':{}}
for name,obj in parts.items():
 shape=obj.val();assert shape.isValid(),name
 assert len(obj.solids().vals())==1,(name,len(obj.solids().vals()))
 cq.exporters.export(obj,str(STEP/(name+'.step')))
 # Put printing parts on z=0. Palm printed on side, bridge flat.
 pr=obj
 if name=='06_palm_trial':pr=pr.rotate((0,0,0),(1,0,0),90)
 bb=pr.val().BoundingBox();pr=pr.translate((0,0,-bb.zmin))
 dest=STL/(name+'.stl');cq.exporters.export(pr,str(dest),tolerance=.04,angularTolerance=.12)
 mesh=trimesh.load_mesh(dest)
 assert mesh.is_watertight,name
 report['parts'][name]={'valid':True,'watertight':bool(mesh.is_watertight),
  'solid_count':1,'print_bounds_mm':mesh.extents.tolist(),'volume_mm3':shape.Volume()}
# Official servo CAD has main servo + 3 wire solids. Place mounting ear underside on bridge.
sp=next((REF/'CyberBrick1迁移研究').glob('*Protection-PG002-PG001.stp'))
raw=cq.importers.importStep(str(sp));servo=cq.Workplane('XY').newObject([raw.solids().vals()[0]])
servo=servo.translate((-11.35,-5.9,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,25))
# Actual servo / frame / bridge overlaps identify flange convention errors.
for name,obj in [('frame',frame),('bridge',bridge)]:
 vol=servo.intersect(obj).val().Volume() if servo.intersect(obj).vals() else 0
 report['checks']['servo_'+name+'_intersection_mm3']=vol
# Horn sits on shaft; exact insertion depth is a nominal assembly assumption.
hp=next((REF/'CyberBrick1迁移研究').glob('*half arm*.stp'))
horn=cq.importers.importStep(str(hp)).translate((5.34,-20,38.42))
arm_pos=arm.translate((5.34,0,39.97));palm_pos=palm.translate((5.34,0,39.97))
for label,a,b in [('servo_horn',servo,horn),('servo_arm',servo,arm_pos),('horn_arm',horn,arm_pos),('arm_palm',arm_pos,palm_pos)]:
 r=a.intersect(b);report['checks'][label+'_intersection_mm3']=sum(s.Volume() for s in r.solids().vals())
assembly=cq.Assembly(name='Otto_PG001_slap_trial_v01')
for name,obj,color in [('frame',frame,(.75,.79,.82)),('bridge',bridge,(.16,.55,.75)),
 ('PG001_reference',servo,(.25,.28,.3)),('original_horn_reference',horn,(.85,.85,.85)),
 ('arm_trial',arm_pos,(.1,.6,.95)),('palm_trial',palm_pos,(.1,.6,.95))]:
 assembly.add(obj,name=name,color=cq.Color(*color))
assembly.save(str(OUT/'顶部模块装配_含参考舵机.step'))
# Body mesh geometry overlap (triangle vertices plus nominal ring gap) is visual only.
body_path=next((REF/'robot-battle-reference'/'Otto-V9').rglob('OttoDIY_body_V9.stl'))
body=trimesh.load_mesh(body_path)
report['checks']['body_bounds_mm']=body.bounds.tolist()
report['checks']['frame_bridge_intersection_mm3']=frame.intersect(bridge).val().Volume()
report['checks']['body_fit']='69.8 square sleeve vs 69 body envelope; physical tolerance and drill locations require trial'
report['checks']['horn_fit']='hole centres from official half-arm CAD; insertion depth and screw fit require trial'
(OUT/'几何检查结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

def meshof(obj):
 v,t=obj.val().tessellate(.18);return np.array([x.toTuple() for x in v]),np.array(t)
def add(ax,obj,color,alpha=1):
 if isinstance(obj,trimesh.Trimesh):v,t=obj.vertices,obj.faces
 else:v,t=meshof(obj)
 ax.add_collection3d(Poly3DCollection(v[t],facecolors=color,edgecolors='none',alpha=alpha,linewidths=0))
fig=plt.figure(figsize=(14,7),dpi=160)
for i,exploded in enumerate((False,True)):
 ax=fig.add_subplot(1,2,i+1,projection='3d')
 add(ax,body,'#bfc6ce',.30)
 add(ax,frame,'#e7e9ec')
 add(ax,bridge.translate((0,0,10 if exploded else 0)),'#36a0bc')
 add(ax,servo.translate((0,0,20 if exploded else 0)),'#454a54')
 add(ax,horn.translate((0,0,30 if exploded else 0)),'#d6d9df')
 add(ax,arm_pos.translate((0,0,37 if exploded else 0)),'#2196e8')
 add(ax,palm_pos.translate((0,0,44 if exploded else 0)),'#2196e8')
 ax.set_xlim(-43,75);ax.set_ylim(-43,43);ax.set_zlim(-40,115 if exploded else 70)
 ax.set_box_aspect((118,86,155 if exploded else 110));ax.view_init(23,-62)
 ax.set_xlabel('X / mm');ax.set_ylabel('Y / mm');ax.set_zlabel('Z / mm')
 ax.set_title('Exploded view / trial v01' if exploded else 'Assembly on original Otto V9 body')
fig.suptitle('PG001 horizontal slap module - FIT TEST PROTOTYPE',fontsize=15)
plt.tight_layout(rect=[0,0,1,.94]);fig.savefig(OUT/'装配与拆解预览.png');plt.close(fig)
print(json.dumps(report,ensure_ascii=False,indent=2))

