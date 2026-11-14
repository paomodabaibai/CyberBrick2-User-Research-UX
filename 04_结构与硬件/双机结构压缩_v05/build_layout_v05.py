"""Same-height packing study; no firmware or original model edits. Not print release."""
from pathlib import Path
import json,math
import cadquery as cq,numpy as np,trimesh
P=Path(__file__).resolve().parent;H=P.parent;R=H.parent/'01_研究参考';V=H/'双机结构改版_v04'
for d in ['装配网格','预览']:(P/d).mkdir(exist_ok=True)
items=[];M={};checks={}
def box(x,y,z,cx=0,cy=0,z0=0):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((cx,cy,z0))
def roundbox(x,y,z,z0,r=4):return box(x,y,z,z0=z0).edges('|Z').fillet(r)
def cyl(r,h,x,y,z):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def nut(x,y,z):return cq.Workplane('XY').polygon(6,5.8/math.cos(math.pi/6)).extrude(2.8).translate((x,y,z))
def mesh(s):
 v,f=s.val().tessellate(.12);return trimesh.Trimesh(np.array([a.toTuple() for a in v]),np.array(f),process=True)
def add(n,m,color,group='common',kind='part'):
 m=m.copy();m.export(P/'装配网格'/(n+'.stl'));M[n]=m;items.append(dict(name=n,file=n+'.stl',color=color,group=group,kind=kind))
def put(n,s,color,kind='part'):
 add(n,mesh(s),color,kind=kind)
def inter(a,b):return float(trimesh.boolean.intersection([a,b],engine='manifold').volume)
# Preserve leg mounting region. Front-wall relief is entirely forward of hip envelopes.
old=trimesh.load_mesh(R/'robot-battle-reference/Otto-V9/3Dprint/OttoDIY_body_V9.stl')
old.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,0,1]))
lower=trimesh.boolean.intersection([old,mesh(box(150,150,30,z0=-54))],engine='manifold')
shell=roundbox(75,75,25,-25,5).cut(roundbox(69.8,69.8,27,-26,3))
shell=shell.union(roundbox(75,75,2,-25.5,5).cut(roundbox(65,65,4,-26.5,3)))
# Local front pocket keeps height unchanged; no hip mounting cut at X<=17.
shell=shell.union(box(5,58,39,35,0,-39)).union(box(20,57,2.5,27.5,0,-39))
for y in (-27.4,27.4):shell=shell.union(box(18,1.6,20,26.5,y,-36.5))
# Front bolts shorter, above the battery; keep old deck hole coordinates.
for x in (-30,30):
 for y in (-30,30):
  h=6 if x>0 else 13
  b=cyl(4.6,h,x,y,-h).union(box(7,7,h,x+math.copysign(3.5,x),y,-h)).union(box(7,7,h,x,y+math.copysign(3.5,y),-h))
  shell=shell.union(b.cut(cyl(1.7,h+2,x,y,-h-1)).cut(nut(x,y,-h)))
# Board bracket attaches to two floor posts; exact screw stack remains trial-fit work.
for x in (-22,0):shell=shell.union(cyl(3.8,7.5,x,14,-39).cut(cyl(1.7,9,x,14,-40)))
shell=shell.union(box(35,7,2,-14.5,15,-39))
shell=shell.union(box(4,37,27,-39.5,-19.5,-32))
# Switch vertical rear-side: inward pins, outward toggle, ear points towards rear.
# A small side opening plus removable cover gives access to switch terminals.
cut_front=box(17.2,53,35.5,26.6,0,-36.5)
cut_usb=box(14,13,17,-36,13.5,-26.5)
cut_switch=box(22,34,23,-33,-19.5,-31)
cut_switch_ear=box(4,9,8,-23.4,-18,-31)
cut_duct=box(14,14,10,-36,-18,-9)
body=trimesh.boolean.union([lower,mesh(shell)],engine='manifold')
for q in (cut_front,cut_usb,cut_switch,cut_switch_ear,cut_duct):body=trimesh.boolean.difference([body,mesh(q)],engine='manifold')
add('01_原高身体_前电池仓布局草案',body,'#cbd9e2',kind='body')
# Standing receiver. USB still points rear(-X); pins point sideways(-Y).
board=cq.importers.importStep(str(R/'CyberBrick1迁移研究/Remote Control Receiver-XA003-XA004.stp')).rotate((0,0,0),(1,1,1),120).rotate((0,0,0),(1,0,0),90).translate((-17,5,-18))
put('R01_竖置原厂接收组合',board,'#35886f','reference')
# Long axis battery -> Y, narrow thickness -> X, 28.4mm side -> Z.
braw=cq.importers.importStep(str(V/'测量临时文件/14500 7.4V 800mAh Li-ion Battery-PC003.stp'))
bat=braw.intersect(box(50,51.2,40,0,25.6,-20)).translate((0,-25.6,0)).rotate((0,0,0),(0,1,0),90).translate((26.35,0,-21.3))
put('R02_前置立放电池',bat,'#547ee8','reference')
# C-frame bracket avoids USB/core underside; actual fixation detail not released.
carrier=box(33,2,1.5,-14.5,12,-31.5).union(box(33,2,2,-14.5,12,-4)).union(box(2,2,29.5,1,12,-31.5))
for x in (-29,-5):
 for z in (-29.5,-6.5):
  post=cq.Workplane('XZ',origin=(x,11,z)).circle(2.8).circle(1.35).extrude(5.8)
  tab=box(5,2,5,x,12,(-31 if z<-18 else -7))
  carrier=carrier.union(post).union(tab)
for x in (-22,0):
 foot=box(7,7,2.5,x,14,-31.5).cut(box(10,3.5,2,x,11.75,-30))
 carrier=carrier.union(foot).cut(cyl(1.7,6,x,14,-33))
put('02_竖置主板托架_布局草案',carrier,'#f2ae45')
swraw=cq.importers.importStep(str(V/'测量临时文件/Power Switch Board with 2Pin XH2.54 Connector-XA007.STEP'))
def switch_pose(w):return w.rotate((0,0,0),(0,0,1),90).rotate((0,0,0),(1,0,0),-90).translate((-26.1,-19.5,-17))
sw=switch_pose(swraw)
put('R03_后置开关拨杆朝外',sw,'#444f61','reference')
# Panel concept only: actual removal/access/bosses to complete after layout review.
bezel=box(2.4,37,27,-42.7,-19.5,-32).cut(box(5,31,18,-42.7,-19.5,-26))
bezel=bezel.cut(box(6,14,10,-42.7,-18,-9))
for y in (-36,-3):bezel=bezel.cut(cq.Workplane('YZ',origin=(-46,y,-29)).circle(1.7).extrude(8))
put('03_后置开关面板_布局草案',bezel,'#4d677a')
# Conservative 10mm plug + 8mm bend reserved sideways, original 20mm span.
plug=box(12,18,20,-14.5,-14.78,-28)
put('E01_侧插头与弯线预留',plug,'#e9b3e3','envelope')
put('E02_USB数据线插拔预留',box(18,12,16,-39,13.5,-26),'#6dd3da','envelope')
# Existing two attack assemblies moved as units back to old deck Z=0.
for o in json.loads((V/'装配清单.json').read_text(encoding='utf-8')):
 if o['group']!='common' or o['name'].startswith(('R_Leg','R_foot','E_hip')):
  m=trimesh.load_mesh(V/'装配网格'/o['file'])
  if o['group']!='common':m.apply_translation((0,0,-26))
  add(o['name'],m,o['color'],o['group'],o['kind'])
# Exact packing checks. Switch only its closed and valid source shells.
swsol=[]
for i in (0,15,17,19):
 a=cq.Solid.makeSolid(swraw.shells().vals()[i]);assert a.isValid()
 w=switch_pose(cq.Workplane('XY').newObject([a]))
 swsol.append(mesh(w))
board_collision=[];boxed_board_solids=[]
for i,s in enumerate(board.solids().vals()):
 m=mesh(cq.Workplane('XY').newObject([s]))
 if not m.is_volume:
  b=s.BoundingBox();m=mesh(box(b.xlen,b.ylen,b.zlen,(b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,b.zmin));boxed_board_solids.append(i)
 board_collision.append(m)
board_collision=trimesh.boolean.union(board_collision,engine='manifold')
core={'board':board_collision,'battery':M['R02_前置立放电池'],'carrier':M['02_竖置主板托架_布局草案']}
# Use CQ board solids for intersection with other CAD: board assembly mesh contains internal overlaps.
def cqvol(a,b):return sum(s.Volume() for s in a.intersect(b).solids().vals())
checks['board_vs_battery']=cqvol(board,bat);checks['board_vs_carrier']=cqvol(board,carrier)
checks['battery_vs_carrier']=cqvol(bat,carrier)
for n,m in core.items():
 checks[n+'_vs_body']=inter(m,body)
 for y in (-25,25):checks[n+'_vs_hip_'+str(y)]=inter(m,M['E_hip_'+str(y)])
 for g in ('10_巴掌定位底座','20_拳头固定底座_含隐藏过线槽'):
  checks[n+'_vs_'+g]=inter(m,M[g])
 for i,s in enumerate(swsol):checks[n+'_vs_switch_'+str(i)]=inter(m,s)
for i,s in enumerate(swsol):
 checks['switch_'+str(i)+'_vs_body']=inter(s,body)
 checks['switch_'+str(i)+'_vs_panel']=inter(s,M['03_后置开关面板_布局草案'])
 for g in ('10_巴掌定位底座','20_拳头固定底座_含隐藏过线槽','E01_侧插头与弯线预留','E02_USB数据线插拔预留'):
  checks['switch_'+str(i)+'_vs_'+g]=inter(s,M[g])
 for y in (-25,25):checks['switch_'+str(i)+'_vs_hip_'+str(y)]=inter(s,M['E_hip_'+str(y)])
for n in ('R01_竖置原厂接收组合','R02_前置立放电池','02_竖置主板托架_布局草案','03_后置开关面板_布局草案','20_拳头固定底座_含隐藏过线槽','10_巴掌定位底座','E_hip_-25','E_hip_25'):
 checks['side_plug_vs_'+n]=inter(M['E01_侧插头与弯线预留'],board_collision if n=='R01_竖置原厂接收组合' else M[n])
for y in (-25,25):
 checks['hip_original_overlap_'+str(y)]=inter(old,M['E_hip_'+str(y)])
 checks['hip_compact_overlap_'+str(y)]=inter(body,M['E_hip_'+str(y)])
for n,m in [('body',body),('switch_panel',M['03_后置开关面板_布局草案'])]:
 for g in ('10_巴掌定位底座','20_拳头固定底座_含隐藏过线槽'):
  checks[n+'_vs_'+g]=inter(m,M[g])
report={'body_height_mm':39,'attack_shift_from_original_mm':0,'outer_upper_width_mm':75,'checks_mm3':checks,'board_connector_bbox_substitutions':boxed_board_solids,
 'note':'Packing study only. Front wall relief and short front mount bosses required. Hip envelopes are not exact supplied servo geometry. Charge port, strap, switch mount screw access and complete harness unfinished.',
 'bounds':{n:m.bounds.tolist() for n,m in core.items()}}
report['collisions_over_0_01_mm3']={k:v for k,v in checks.items() if not k.startswith('hip_') and abs(v)>.01}
report['hip_added_overlap_mm3']={str(y):checks['hip_compact_overlap_'+str(y)]-checks['hip_original_overlap_'+str(y)] for y in (-25,25)}
(P/'原高布局核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'装配清单.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2));print('LAYOUT_COMPLETE')
