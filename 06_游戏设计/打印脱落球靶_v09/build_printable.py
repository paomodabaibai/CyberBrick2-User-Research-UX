"""Manufacturing prototype, millimetres. Deterministic CAD + clearance report.
Run in the project's cad_runtime. No original parts are modified.
"""
from pathlib import Path
import json, math
import cadquery as cq
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'制造初样_v01'
for d in ('01_先打小样','02_一套正式件_STL','03_可编辑STEP','04_总装与检查'):
    (OUT/d).mkdir(parents=True,exist_ok=True)

def box(w,d,h,x=0,y=0,z=0):
    return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z))
def cyl(r,h,x=0,y=0,z=0):
    return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def along_y(obj,x,y,z):
    return obj.rotate((0,0,0),(1,0,0),-90).translate((x,y,z))
def hole_y(r,length,x,y,z): return along_y(cyl(r,length),x,y,z)
def hex_z(af,h,x=0,y=0,z=0):
    return cq.Workplane('XY').polygon(6,af/math.cos(math.pi/6)).extrude(h).translate((x,y,z))
def nut_y(af,length,x,y,z): return along_y(hex_z(af,length),x,y,z)
def ring(ro,ri,h,z=0): return cyl(ro,h,z=z).cut(cyl(ri,h+.2,z=z-.1))
def volume(s): return float(s.val().Volume())
def intersection(a,b):
    return sum(s.Volume() for s in a.intersect(b).solids().vals())
def to_mesh(s):
    v,f=s.val().tessellate(.07,.12)
    m=trimesh.Trimesh(np.asarray([p.toTuple() for p in v]),np.asarray(f),process=True)
    m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices();m.merge_vertices(digits_vertex=6);m.fix_normals()
    return m

# Base and pillar. 0.3 mm clearance on each side; no press-fitting.
base=box(100,80,4,x=95).edges('|Z').fillet(4)
base=base.union(box(26.6,28.6,18,x=95,z=4))
base=base.cut(box(18.6,20.6,20,x=95,z=4.3))
base=base.cut(hole_y(1.7,40,95,-20,12)).cut(nut_y(5.8,2.7,95,11.7,12))
for x in (54,136):
    for y in (-31,31): base=base.cut(cyl(1.7,6,x,y,-1))
post=box(18,20,160.7,x=95,z=4.3)
for z in (12,95,105,115): post=post.cut(hole_y(1.7,24,95,-12,z))
# Shallow level marks on the rear face, not through the load-bearing section.
for z,n in ((95,1),(105,2),(115,3)):
    for i in range(n): post=post.cut(box(.7,3,.65,x=103.8,y=-4+i*4,z=z-.325))

# Sleeve and beam have the same bottom plane so they print upright without
# large under-beam support. Through-bore remains open at both ends.
sleeve=box(26.6,28.6,40,x=95,z=87).cut(box(18.6,20.6,42,x=95,z=86))
sleeve=sleeve.cut(hole_y(1.7,40,95,-20,105)).cut(nut_y(5.8,2.7,95,11.7,105))
beam=box(103.5,22,12,x=30.25,z=87)  # -21.5 .. 82, overlaps sleeve wall .3
arm=sleeve.union(beam)
for x in (-14,14):
    arm=arm.cut(cyl(1.7,14,x,0,86)).cut(hex_z(5.8,2.7,x,0,86.9))

# Removable magnet seat. Magnets load from underside; bottom plug is glued
# before the seat is bolted on. No exposed magnets at the impact interface.
seat=box(40,18,3,z=99).union(cyl(11,8,z=99))
seat=seat.cut(box(1.4,4,4,x=20,z=98.5))  # rear orientation notch
seat=seat.cut(cyl(9.3,5.5,z=98.9))
mag_positions=[(0,0)]+[(5.5*math.cos(a),5.5*math.sin(a)) for a in (0,2*math.pi/3,4*math.pi/3)]
for x,y in mag_positions: seat=seat.cut(cyl(2.15,2.2,x,y,104.4))
for x in (-14,14): seat=seat.cut(cyl(1.7,4,x,0,98.9))
seat_lid=cyl(9,4.2,z=100)

# Hollow ball, split at equator. Lower flat plane Z=107 -> centre 135.
shell=cq.Workplane('XY').sphere(30).translate((0,0,135))
shell=shell.cut(cq.Workplane('XY').sphere(28.4).translate((0,0,135)))
lower=shell.intersect(box(70,70,28,z=107))
lower=lower.union(cyl(11,2.6,z=107))
for x,y in mag_positions: lower=lower.cut(cyl(2.15,2.3,x,y,107.4))
# Small rear eye for an OPTIONAL slack retention cord; not a weight support.
eye=hole_y(4,3,30,-1.5,128).cut(hole_y(1.5,5,30,-2.5,128))
lower=lower.union(eye)
upper=shell.intersect(box(70,70,31,z=135))
seam_ring=ring(28.05,26.85,4,z=133)
ball_lid=cyl(11,1.6,z=109.6)

parts={
 '01_场地固定底座':base,'02_三档立柱':post,'03_套筒悬臂':arm,
 '04_磁铁托座_D4x2':seat,'05_托座磁铁封盖':seat_lid,
 '06_球下半壳_带磁铁槽':lower,'07_球上半壳':upper,
 '08_球壳定位环':seam_ring,'09_球内磁铁封盖':ball_lid,
}
colors=['#516b7f','#516b7f','#38a3aa','#e9b454','#e9b454','#e65c50','#e65c50','#d8bd8b','#dd8c66']
report={'status':'CAD verified prototype; print fit and impact tests pending',
 'units':'mm','ball_diameter':60,'ball_center_heights':[125,135,145],
 'magnet_spec':'CyberBrick B-CA001, diameter 4 x thickness 2 mm',
 'magnet_source':'https://asia.store.bambulab.com/en/products/cyberbrick-hardware-kit',
 'clearance_per_side':.3,'magnet_hole_diameter':4.3,'nut_pocket_af':5.8,
 'skin_each_side':.4,'nominal_magnetic_face_separation':1.0,
 'magnet_positions_xy':mag_positions,'magnet_load_modes':'central 1 pair OR outer equilateral 3 pairs',
 'parts':{},'checks':{},'physical_tested':False}

def export_part(name,s,color,folder='02_一套正式件_STL',rotate=None):
    assert s.val().isValid(),name+' invalid BREP'
    assert len(s.solids().vals())==1,(name,'not single solid',len(s.solids().vals()))
    m=to_mesh(s)
    assert m.is_watertight and m.is_volume,(name,'nonwatertight mesh')
    pr=m.copy()
    if rotate:
        pr.apply_transform(trimesh.transformations.rotation_matrix(math.radians(rotate[0]),rotate[1]))
    pr.apply_translation(-pr.bounds[0])
    pr.export(OUT/folder/(name+'.stl'))
    cq.exporters.export(s,str(OUT/'03_可编辑STEP'/(name+'.step')))
    report['parts'][name]={'solid_count':1,'watertight':True,'volume_mm3':volume(s),
        'print_extents_mm':pr.extents.round(3).tolist(),'assembly_bounds':m.bounds.round(3).tolist(),
        'print_rotation':rotate,'color':color,'file':folder+'/'+name+'.stl'}
    return m

meshes={}
for (n,s),color in zip(parts.items(),colors):
    rot=(90,[1,0,0]) if n.startswith('02') else ((180,[1,0,0]) if n.startswith(('04','06')) else None)
    meshes[n]=export_part(n,s,color,rotate=rot)

# Independent reusable gauges: three sleeve clearances and a magnet/nut coupon.
for gap in (.2,.3,.4):
    coupon=box(26,28,8).cut(box(18+2*gap,20+2*gap,10,z=-1))
    export_part(f'小样_套筒_单边{gap:.1f}mm',coupon,'#38a3aa','01_先打小样')
post_coupon=box(18,20,20).cut(hole_y(1.7,24,0,-12,10))
export_part('小样_方柱与M3通孔',post_coupon,'#516b7f','01_先打小样')
mag_coupon=box(34,22,4)
for x,d in ((-10,4.2),(0,4.3),(10,4.4)):mag_coupon=mag_coupon.cut(cyl(d/2,2.2,x,-5,1.8))
for x,af in ((-10,5.7),(0,5.8),(10,5.9)):
    mag_coupon=mag_coupon.cut(hex_z(af,2.7,x,5,1.3)).cut(cyl(1.7,5,x,5,-.5))
export_part('小样_磁铁孔4p2_4p3_4p4_螺母孔5p7_5p8_5p9',mag_coupon,'#e9b454','01_先打小样')
for h in (.4,.8):
    shim=cyl(11,h).union(box(12,4,h,x=13))
    export_part(f'可选_减磁垫片_{h:.1f}mm',shim,'#dadfe3','01_先打小样')

# Geometry verification includes all three heights, removal/installation, and
# simplified hardware envelopes. Mathematical checks are not strength tests.
moving=[n for n in parts if not n.startswith(('01','02'))]
for dz in (-10,0,10):
    positioned={n:(s.translate((0,0,dz)) if n in moving else s) for n,s in parts.items()}
    collisions=[]
    keys=list(positioned)
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            overlap=intersection(positioned[a],positioned[b])
            if overlap>1e-4: collisions.append([a,b,overlap])
    report['checks'][f'height_{135+dz}_overlap']=collisions
    assert not collisions,collisions

# Passing a longer rod through each y bore must intersect no printed material.
for z,objects in [(12,[base,post]),(105,[arm,post])]:
    shaft=hole_y(1.5,35,95,-16,z)
    for obj in objects:assert intersection(shaft,obj)<1e-5
    nut=nut_y(5.5,2.4,95,11.8,z)
    assert intersection(nut,objects[0])<1e-5
report['checks']['M3_post_and_sleeve_bolt_nut_clear']=True
for x in (-14,14):
    bolt=cyl(1.5,16,x,0,86).union(cyl(2.85,3,x,0,102))
    nut=hex_z(5.5,2.4,x,0,87.1)
    for obj in (arm,seat,lower): assert intersection(obj,bolt)<1e-4
    assert intersection(arm,nut)<1e-4
report['checks']['M3x16_seat_screws_clear_ball']=True

for x,y in mag_positions:
    for magnet,holder in [(cyl(2,2,x,y,104.4),seat),(cyl(2,2,x,y,107.4),lower)]:
        assert intersection(magnet,holder)<1e-5
report['checks']['eight_D4x2_magnet_envelopes_clear']=True
# Inserting sleeve from pillar top (default arm rises first, then drops to hole).
for dz in (0,10,30,60,90):assert intersection(arm.translate((0,0,dz)),post)<1e-5
report['checks']['sleeve_slides_from_top_clear']=True
# Lower/upper hemispheres, ring and cap assembled with glue; positive radial gap.
report['checks']['seam_ring_min_radial_clearance']=round(math.sqrt(28.4**2-2**2)-28.05,4)
report['checks']['ball_shell_nominal_thickness']=1.6

assembly=trimesh.Scene()
for n,m in meshes.items():
    c=report['parts'][n]['color'];m=m.copy();m.visual.vertex_colors=[int(c[j:j+2],16) for j in (1,3,5)]+[255]
    assembly.add_geometry(m,node_name=n)
assembly.export(OUT/'04_总装与检查/总装135mm_仅预览.glb')
cq.exporters.export(cq.Compound.makeCompound([s.val() for s in parts.values()]),str(OUT/'04_总装与检查/总装135mm_仅预览.step'))
report['total_print_solid_volume_mm3']=sum(report['parts'][n]['volume_mm3'] for n in parts)
report['ball_shell_and_glue_ring_volume_mm3']=sum(volume(parts[n]) for n in parts if n.startswith(('06','07','08','09')))
report['ball_plastic_mass_estimate_g_at_1p24']=report['ball_shell_and_glue_ring_volume_mm3']*.00124
(OUT/'04_总装与检查/几何检查报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'parts':len(parts),'all_checks_passed':True,'ball_plastic_mass_estimate_g':report['ball_plastic_mass_estimate_g_at_1p24']},ensure_ascii=False))
