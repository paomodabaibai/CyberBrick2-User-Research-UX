from pathlib import Path
import numpy as np,trimesh,cadquery as cq,json
R=Path(__file__).resolve().parent;REF=R.parents[1]/'01_研究参考';V1=R.parent/'Otto_PG001顶部巴掌模块_v01'
def simp(m,step):
 target=8000 if step<.1 else 2000
 m=m.copy();m.merge_vertices();m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
 if len(m.faces)>target:m=m.simplify_quadric_decimation(face_count=target)
 return m
def cqmesh(obj):
 v,f=obj.val().tessellate(.15);return trimesh.Trimesh([p.toTuple() for p in v],f,process=False)
objs=[]
def add(name,m,step=1,kind='fixed',color='body'):
 m=simp(m,step);objs.append(dict(name=name,v=np.round(m.vertices,3).tolist(),f=m.faces.tolist(),kind=kind,color=color))
stls=REF/'robot-battle-reference'/'Otto-V9'/'3Dprint'
add('body',trimesh.load_mesh(stls/'OttoDIY_body_V9.stl'))
for nm in ['Leg','foot']:
 m=trimesh.load_mesh(stls/f'OttoDIY_{nm}_V9.stl');add(nm+'_right',m,.8)
 n=m.copy();n.apply_transform(np.diag([-1,1,1,1]));add(nm+'_left',n,.8)
for nm,col in [('03_body_mount_frame','frame'),('04_servo_bridge','frame')]:add(nm,cqmesh(cq.importers.importStep(str(V1/'STEP_可编辑实体'/(nm+'.step')))),.6,color=col)
p=next((REF/'CyberBrick1迁移研究').glob('*Protection-PG002-PG001.stp'));s=cq.importers.importStep(str(p)).solids().vals()[0];s=cq.Workplane('XY').newObject([s]).translate((-11.35,-5.9,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,25));add('servo',cqmesh(s),.65,color='servo')
m=trimesh.load_mesh(R/'巴掌_Tripo原始.stl');m=max(m.split(only_watertight=False),key=lambda x:len(x.faces));m.apply_scale(1/m.extents[0]);wrist_z=float(np.mean(m.vertices[m.vertices[:,0]>.46,2]));print('wrist_z',wrist_z)
m.vertices[:,0]=.5-m.vertices[:,0];m.vertices[:,1]*=-1;m.vertices[:,2]-=wrist_z
add('palm',m,.017,kind='palm',color='palm')
(R/'比例预览数据.json').write_text(json.dumps(objs,separators=(',',':')),encoding='utf-8');print([(o['name'],len(o['f'])) for o in objs])
# Three honest CAD-mesh previews using same limits/camera, not generated artwork.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.font_manager import FontProperties
font=FontProperties(fname=r'C:\Windows\Fonts\msyh.ttc');fig=plt.figure(figsize=(15,7),dpi=140)
colors={'body':'#d8dde3','frame':'#41a2b0','servo':'#454f60','palm':'#b0d9ff'}
for k,(size,reach) in enumerate([(40,27.5),(50,37.5),(60,47.5)]):
 ax=fig.add_subplot(1,3,k+1,projection='3d')
 for o in objs:
  v=np.array(o['v']);f=np.array(o['f']);
  if o['kind']=='palm':v=v*size+np.array([reach+5.34,0,43])
  c=Poly3DCollection(v[f],facecolors=colors[o['color']],edgecolor='none',shade=True,lightsource=matplotlib.colors.LightSource(azdeg=225,altdeg=45));ax.add_collection3d(c)
 arm=cq.Workplane('XY').box(reach+12.5,10,3).translate(((reach+2.5)/2+5.34,0,41.47));mm=cqmesh(arm);ax.add_collection3d(Poly3DCollection(mm.triangles,facecolors='#41a2b0',shade=True,lightsource=matplotlib.colors.LightSource()))
 ax.set_xlim(-62,123);ax.set_ylim(-55,55);ax.set_zlim(-90,95);ax.set_box_aspect((185,110,185));ax.view_init(12,-75);ax.set_axis_off();ax.set_title(f'{chr(65+k)}  手掌 {size} mm\n杆距 {reach} mm',fontproperties=font,fontsize=16)
fig.suptitle('同一比例尺：原版 Otto 身体、双腿双脚 ＋ 新巴掌',fontproperties=font,fontsize=19)
fig.text(.5,.04,'手掌为最长边；杆距为转轴到末端孔组中心。腕部为比例示意放置，尚未设计连接接口。',ha='center',fontproperties=font,fontsize=12)
fig.subplots_adjust(left=.01,right=.99,top=.85,bottom=.08,wspace=.02);fig.savefig(R/'整机比例三方案.png');print('done')



