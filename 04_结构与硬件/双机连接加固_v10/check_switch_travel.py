from pathlib import Path
import json,numpy as np,cadquery as cq,trimesh
P=Path(__file__).resolve().parent;H=P.parent
raw=cq.importers.importStep(str(H/'双机结构改版_v04/测量临时文件/Power Switch Board with 2Pin XH2.54 Connector-XA007.STEP'))
s=cq.Workplane('XY').newObject([cq.Solid.makeSolid(raw.shells().vals()[15])]).rotate((0,0,0),(0,0,1),90).rotate((0,0,0),(1,0,0),-90).translate((-32.6,-15,-17))
# Only the protruding actuator that can contact the cover; internal switch travel is not simulated.
q=s.intersect(cq.Workplane('XY').box(30,50,50).translate((-56.51,-15,-17)))
v,f=q.val().tessellate(.03,.05);lever=trimesh.Trimesh([x.toTuple() for x in v],f,process=True);assert lever.is_volume
old=trimesh.load_mesh(H/'双机连接加固_v09/装配网格/03_开关模块面板_v09_安装耳对中.stl')
manifest=json.loads((P/'装配清单.json').read_text(encoding='utf-8'));M={o['name']:trimesh.load_mesh(P/'装配网格'/o['file']) for o in manifest}
name='03_开关模块面板_v10_敞口拨动槽';new=M[name]
def inter(a,b):
 r=trimesh.boolean.intersection([a,b],engine='manifold');return float(r.volume) if len(r.faces) else 0.
report={'assumptions':'Official STEP has one static pose, no documented travel. Translate protruding block along Z by +/-4mm as a design stress envelope, not a measured specification. Internals excluded.', 'lever_static_bounds_mm':lever.bounds.tolist(),'v09_static_vertical_clearance_mm':{'down':float(lever.bounds[0,2]+19),'up':float(-11.5-lever.bounds[1,2])},'sampling_step_mm':.25,'v09_collisions':[],'v10_collisions':[]}
obstacles={n:M[n] for n in ['01_原高身体_v08','10_巴掌定位底座_v07电池限位','20_拳头底座_v07尾部入线','21_拳头护罩_共用螺丝敞口',name]}
for dz in np.arange(-4,4.001,.25):
 m=lever.copy();m.apply_translation((0,0,dz));vol=inter(m,old)
 if vol>.001:report['v09_collisions'].append({'dz':float(dz),'mm3':vol})
 for n,o in obstacles.items():
  vol=inter(m,o)
  if vol>.001:report['v10_collisions'].append({'dz':float(dz),'part':n,'mm3':vol})
assert report['v09_collisions'] and not report['v10_collisions'],report
report['v10_slot']={'width_mm':10.5,'bottom_z':-23.5,'open_at_top_z':-8.2,'bottom_corner_radius_mm':2.0,'back_panel_thickness_mm':2.4}
report['pass_within_assumed_envelope']=True
(P/'v10_拨杆活动包络检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lever.export(P/'预览/拨杆外露部分_检查参考勿打印.stl')
print('Static margins:',report['v09_static_vertical_clearance_mm']);print('v09 collisions:',len(report['v09_collisions']));print('v10 collisions:',len(report['v10_collisions']))
