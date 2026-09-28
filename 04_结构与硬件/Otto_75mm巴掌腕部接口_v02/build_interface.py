from pathlib import Path
import json, numpy as np, trimesh, cadquery as cq
OUT=Path(__file__).resolve().parent
SRC=OUT.parent/'巴掌_Tripo网格与尺寸调整'
PRINT=OUT/'STL_打印件';CAD=OUT/'STEP_结构件';ASM=OUT/'装配坐标_勿直接打印'
for d in (PRINT,CAD,ASM):d.mkdir(exist_ok=True)
P={'palm_longest_mm':75.,'rod_reach_mm':51.,'rod_total_mm':63.5,'fit_clearance_per_side_mm':.25,'cross_bolt_x_mm':59.,'cross_bolt_z_mm':6.,'cross_bolt_seat_y_mm':11.}
(OUT/'接口参数.json').write_text(json.dumps(P,indent=2),encoding='utf-8')

def box(x,y,z,cx=0,cy=0,z0=0):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((cx,cy,z0))
def cylz(r,h,x,y,z):return cq.Workplane('XY').center(x,y).circle(r).extrude(h).translate((0,0,z))
def cyly(r,length,x,y,z):return cylz(r,length,0,0,0).rotate((0,0,0),(1,0,0),-90).translate((x,y,z))
def hexy(af,length,x,y,z):return cq.Workplane('XY').polygon(6,af/np.cos(np.pi/6)).extrude(length).rotate((0,0,0),(1,0,0),-90).translate((x,y,z))
def meshof(s):
 v,f=s.val().tessellate(.03,.12);m=trimesh.Trimesh(np.array([v.toTuple() for v in v]),np.array(f),process=True);m.fix_normals();assert m.is_watertight;return m

def diff(m, cutters):return trimesh.boolean.difference([m]+cutters,engine='manifold',check_volume=True)
def intersect(a,b):return trimesh.boolean.intersection([a,b],engine='manifold',check_volume=True)
raw=trimesh.load_mesh(SRC/'巴掌_Tripo原始.stl');palm=max(raw.split(only_watertight=False),key=lambda m:len(m.faces));palm.apply_scale(75/palm.extents.max())
wristz=float(palm.vertices[palm.vertices[:,0]>34.5,2].mean());palm.vertices[:,0]=37.5-palm.vertices[:,0]+51;palm.vertices[:,1]*=-1;palm.vertices[:,2]+=3.03-wristz
assert palm.is_volume
# Rectangular keyed connector and captive nuts. Upper nut access before inserting the palm.
adapter=box(23,12,6,55,z0=3)
for x in (48.5,53.5):
 adapter=adapter.cut(cylz(1.2,10,x,0,2))
 nut=cq.Workplane('XY').polygon(6,4.2/np.cos(np.pi/6)).extrude(3).rotate((0,0,0),(0,0,1),30).translate((x,0,6.0))
 adapter=adapter.cut(nut)
adapter=adapter.cut(cyly(1.2,20,59,-10,6))
# Cavity for connector. Rear mouth through organic surface, blind front end.
cutters=[meshof(box(30,12.5,6.5,51.75,z0=2.75)),
         meshof(box(25,10.5,5.75,46.25,z0=-2.5)),
         meshof(cyly(1.2,50,59,-25,6)),
         meshof(hexy(4.2,14,59,11,6)),meshof(cyly(3,14,59,-25,6))]
# Screw-tip clearance above rear connector M2 screw, so M2x10 does not touch the palm.
# M2x8 root screws remain entirely inside the connector envelope.
full=diff(palm,cutters)
# Wrist-only sample: cut plane x=70 leaves blind cavity front wall intact.
wrist=intersect(full,meshof(box(50,100,100,45,z0=-40)))
rod=cq.importers.importStep(str(SRC/'输出_手掌75mm_杆距51mm'/'连接杆_孔组中心距51mm.step'))
end_coupon=rod.intersect(box(15,20,5,51,z0=-1))
parts={'01_腕部局部试装件':wrist,'02_插入连接块':meshof(adapter),'03_杆末端试装片':meshof(end_coupon),'04_完整手掌75mm_带接口':full,'05_完整连接杆_杆距51mm':meshof(rod)}
report={'parameters':P,'parts':{},'checks':{},'reference_wrist_z_before_shift':wristz}
for name,m in parts.items():
 assert m.is_volume,(name,m.is_watertight,m.volume)
 comps=m.split(only_watertight=False);assert len(comps)==1,(name,len(comps))
 m.export(ASM/(name+'.stl'))
 pr=m.copy()
 if name.startswith('01'):pr.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]))
 if name.startswith('04'):pr.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
 pr.apply_translation(-pr.bounds[0]);pr.export(PRINT/(name+'.stl'))
 report['parts'][name]={'watertight':bool(m.is_watertight),'positive_volume':bool(m.is_volume),'components':len(comps),'faces':len(m.faces),'volume_mm3':float(m.volume),'assembly_bounds_mm':m.bounds.tolist(),'print_extents_mm':pr.extents.tolist()}
for name,obj in [('02_插入连接块',adapter),('03_杆末端试装片',end_coupon),('05_完整连接杆_杆距51mm',rod)]:
 assert obj.val().isValid();cq.exporters.export(obj,str(CAD/(name+'.step')))
for label,a,b in [('palm_adapter',full,parts['02_插入连接块']),('palm_rod',full,parts['05_完整连接杆_杆距51mm']),('adapter_rod',parts['02_插入连接块'],parts['05_完整连接杆_杆距51mm'])]:
 it=intersect(a,b);report['checks'][label+'_overlap_mm3']=float(it.volume);assert abs(it.volume)<.001,(label,it.volume)
# Can the palm slide off? Move palm forwards relative to the fixed rod and connector.
for dx in (1,5,10,16):
 moved=full.copy();moved.apply_translation([dx,0,0]);it=intersect(moved,parts['02_插入连接块']);report['checks'][f'palm_withdraw_{dx}mm_overlap_mm3']=float(it.volume);assert abs(it.volume)<.001
for dx in (1,2,5,10,16):
 moved=full.copy();moved.apply_translation([dx,0,0])
 for label,test in [('root_shank',cylz(1,8,53.5,0,0)),('root_head',cylz(2,2,53.5,0,-2))]:
  it=intersect(moved,meshof(test));report['checks'][f'withdraw_{dx}mm_{label}_overlap_mm3']=float(it.volume);assert abs(it.volume)<.001,(dx,label,it.volume)
# Screw shanks pass through the connector/hand. External head/nut seats also have clear space.
for label,test in [('cross_shank',cyly(1,25,59,-12,6)),('cross_head',cyly(2,1.5,59,-13,6)),('cross_nut_envelope',hexy(4.0,1.6,59,11.4,6)),('root_screw_tip',cylz(1,8,53.5,0,0)),('root_screw_head',cylz(2,2,53.5,0,-2))]:
 it=intersect(full,meshof(test));report['checks'][label+'_palm_overlap_mm3']=float(it.volume);assert abs(it.volume)<.001,(label,it.volume)
# Preserve full quality coloured scene, all in axis-local assembly coordinates.
scene=trimesh.Scene()
for name,m in [('palm',full),('connector',parts['02_插入连接块']),('rod',parts['05_完整连接杆_杆距51mm'])]:
 mm=m.copy();mm.visual.vertex_colors={'palm':[210,231,248,255],'connector':[239,170,66,255],'rod':[47,155,174,255]}[name];scene.add_geometry(mm,node_name=name)
scene.export(OUT/'腕部连接装配_75mm_51mm.glb')
(OUT/'几何验证报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))


