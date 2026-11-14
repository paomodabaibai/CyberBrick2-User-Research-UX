"""Focused v11 revision. Preserve v10 unchanged parts; rebuild palm cover, arm and glue-fit hand."""
from pathlib import Path
import json,shutil,math,hashlib
import numpy as np,cadquery as cq,trimesh
from scipy.spatial import ConvexHull
P=Path(__file__).resolve().parent; H=P.parent; OLD=H/'双机连接加固_v10'
for d in ('装配网格','STEP_审阅件','预览'):(P/d).mkdir(exist_ok=True)
manifest=json.loads((OLD/'装配清单.json').read_text(encoding='utf-8'))
removed={'12_承重转盘罩_v08四角刀孔','15_承重转盘与加强接杆一体','P_02_插入连接块','P_04_完整手掌75mm_带接口','13_独立承重座_v07'}
for n in removed:
 for folder,ext in [('装配网格','.stl'),('STEP_审阅件','.step')]:
  stale=P/folder/(n+ext)
  if stale.is_file():stale.unlink() # only superseded exports in this v11 folder
for o in manifest:
 if o['name'] not in removed:shutil.copy2(OLD/'装配网格'/o['file'],P/'装配网格'/o['file'])
for f in (OLD/'STEP_审阅件').glob('*.step'):
 if f.stem not in removed:shutil.copy2(f,P/'STEP_审阅件'/f.name)
# Shared helper definitions and canonical unchanged support geometry.
source=(OLD/'build_v10.py').read_text(encoding='utf-8')
helpers=source[source.index('def box('):source.index('v6={')]
helpers=helpers.replace("fine=n.startswith('12_')", "fine=n.startswith(('12_','13_','15_'))")
items=[];meshes={};shapes={};cx=5.34;rz=39.97
exec(helpers)
REF=H.parent/'01_研究参考/CyberBrick1迁移研究'
block=source[source.index('bridge=box('):source.index('outer=box(75,75,34')]
block=block.replace("for y in (-18,18):\n seat=seat.union(box(8,22,2,-29,math.copysign(11,y),31.5)).union(cyl(4,5,-29,y,26.5))\n seat=seat.cut(cyl(2.0,6.1,-29,y,27.5))", "for y in (-15,15):\n seat=seat.union(box(10,18,2,-28,math.copysign(9,y),31.5)).union(cyl(4,5,-27,y,26.5))\n seat=seat.cut(cyl(2.0,6.1,-27,y,27.5))")
block=block.replace("for y in (-4,4):rotor=rotor.union(box(27,2,5,27.5,y,3))", """# Solid, softly rounded back instead of two exposed rails.
back=box(31,10,5,29.5,0,3).edges('|Z').fillet(2).edges('>Z').fillet(1.2)
rotor=rotor.union(back)
# Fill obsolete wrist-to-rod fastener holes; preserve central horn access.
for x in (48.5,53.5):rotor=rotor.union(cyl(1.3,3.2,x,0,-.1))
insert=box(23,12,6,55,0,3).edges().fillet(.6)
rotor=rotor.union(insert)""")
# Only output changed arm; old support/servo/horn geometry stays byte-identical.
block='\n'.join(l for l in block.splitlines() if not l.startswith("put('") and not l.startswith(" put('14"))
# Remove now-empty cap export loop.
block=block.replace("for suffix,s in zip(('A','B'),sorted(cap.solids().vals(),key=lambda q:q.Center().y)):", '')
exec(block)
ARM='15_转盘圆润实心杆与胶粘插芯_v11'
put(ARM,rotor,'#418eb5','palm')
SEAT='13_承重座_v11内收盖耳'
put(SEAT,seat,'#f2ae45','palm')
# Rounded octagonal perimeter retreats from ALL four deck screw axes (±30,±30).
# It leaves the screws outside the shell rather than cutting through its roof/walls.
def shoulder(half,diagonal,z,h,vr,tr):
 a=diagonal-half
 pts=[(half,a),(a,half),(-a,half),(-half,a),(-half,-a),(-a,-half),(a,-half),(half,-a)]
 w=cq.Workplane('XY').polyline(pts).close().extrude(h).translate((0,0,z)).edges('|Z').fillet(vr)
 return w.edges('>Z').fillet(tr)
outer=shoulder(37.5,55,3,34,5,2)
inner=shoulder(35.5,55-2*math.sqrt(2),2,33,3,.8)
cover=outer.cut(inner).cut(cyl(27.5,10,cx,0,30))
for x,y in bolts:cover=cover.cut(cyl(4.9,10,x,y,30))
for y in (-15,15):cover=cover.union(cyl(3.6,3.5,-27,y,33.5)).cut(cyl(1.7,8,-27,y,32))
# A 0.1mm relief above the seating surface prevents nominal face/mesh coincidence.
cover=cover.cut(seat).cut(seat.translate((0,0,.1)))
COVER='12_圆肩避孔罩_v11'
put(COVER,cover,'#61b5e4','palm')
# Regenerate hand from original organic surface: keep keyed insertion cavity,
# omit previous transverse pin/nut/head recesses. No arbitrary patch over the mesh.
SRC=H/'巴掌_Tripo网格与尺寸调整'
raw=trimesh.load_mesh(SRC/'巴掌_Tripo原始.stl')
palm=max(raw.split(only_watertight=False),key=lambda m:len(m.faces));palm.apply_scale(75/palm.extents.max())
wristz=float(palm.vertices[palm.vertices[:,0]>34.5,2].mean())
palm.vertices[:,0]=37.5-palm.vertices[:,0]+51;palm.vertices[:,1]*=-1;palm.vertices[:,2]+=3.03-wristz
palm=trimesh.boolean.difference([palm,mesh(box(30,12.5,6.5,51.75,0,2.75),True),mesh(box(25,10.5,5.75,46.25,0,-2.5),True)],engine='manifold')
palm.apply_translation((cx,0,rz))
HAND='P_04_手掌75mm胶粘接口_无横销孔_v11'
add(HAND,palm,'#64bafa','palm','part')
newitems=items[:]
items=[o for o in manifest if o['name'] not in removed]+newitems
(P/'装配清单.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print('BUILT',[(o['name'],len(meshes[o['name']].faces),meshes[o['name']].is_volume) for o in newitems],flush=True)
# Baseline, dimensions and scope evidence. Functional sweeps are in check_v11.py.
report={'changed':[o['name'] for o in newitems],'removed':sorted(removed),'unchanged_hash_mismatch':[],
 'scope':'New cover perimeter and inward cover mounts, one-piece arm+insert, hand pin holes removed. Fist/body/switch untouched.',
 'parameters':{'body_height_mm':39,'hand_longest_mm':75,'wrist_reference_reach_mm':51,'cover_top_Z':37,'deck_axes_XY':[[x,y] for x in (-30,30) for y in (-30,30)],'insert_nominal_mm':[23,12,6],'cavity_clearance_per_side_mm':.25},'parts':{}}
for o in items:
 f=P/'装配网格'/o['file']
 if o['name'] not in [p['name'] for p in newitems] and hashlib.sha256(f.read_bytes()).digest()!=hashlib.sha256((OLD/'装配网格'/o['file']).read_bytes()).digest():report['unchanged_hash_mismatch'].append(o['name'])
for o in newitems:
 m=meshes[o['name']];report['parts'][o['name']]={'watertight':bool(m.is_watertight),'volume_mm3':float(m.volume),'bounds':m.bounds.tolist(),'components':len(m.split(only_watertight=False))}
 assert m.is_volume and report['parts'][o['name']]['components']==1
assert not report['unchanged_hash_mismatch']
(P/'v11_改动与几何记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
