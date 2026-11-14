from pathlib import Path
import json,re,hashlib,numpy as np,trimesh
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
plt.rcParams['font.sans-serif']=['Microsoft YaHei'];plt.rcParams['axes.unicode_minus']=False
P=Path(__file__).resolve().parent;V=P.parent/'双机连接加固_v08'
B=trimesh.load_mesh(V/'装配网格/01_原高身体_v08.stl');F=trimesh.load_mesh(V/'装配网格/03_开关模块面板_v08.stl')
report={'source':'actual exported v08 STL and embedded HTML geometry','holes':[]}
def fit(m,x,y,z,r):
 seg=trimesh.intersections.mesh_plane(m,[1,0,0],[x,0,0]);pts=seg[:,:,1:].reshape(-1,2)
 pts=pts[np.abs(np.linalg.norm(pts-[y,z],axis=1)-r)<.035];pts=np.unique(np.round(pts,6),axis=0)
 assert len(pts)>20,(len(pts),x,y)
 a=np.column_stack((2*pts,np.ones(len(pts))));t=np.linalg.lstsq(a,(pts**2).sum(1),rcond=None)[0]
 cy,cz=t[:2];rr=float(np.sqrt(t[2]+cy*cy+cz*cz))
 return dict(x=x,y=float(cy),z=float(cz),radius=rr,points=len(pts)),seg
fig,axes=plt.subplots(1,2,figsize=(12,6))
for ax,y in zip(axes,[-33.5,2.5]):
 fits=[]
 for m,x,color,label,r in [(F,-42.7,'#1985ba','面板 Ø3.4',1.7),(B,-40,'#e78024','身体热熔孔 Ø4.0',2.0)]:
  f,seg=fit(m,x,y,-28.5,r);fits.append(f)
  ax.add_collection(LineCollection(seg[:,:,1:],colors=color,linewidths=1.5,label=label))
 d=float(np.linalg.norm(np.array([fits[0]['y'],fits[0]['z']])-np.array([fits[1]['y'],fits[1]['z']])))
 fits2=[fit(F,-43.3,y,-28.5,1.7)[0],fit(F,-42.1,y,-28.5,1.7)[0],fit(B,-39,y,-28.5,2)[0],fit(B,-36.2,y,-28.5,2)[0]]
 axial=max(float(np.linalg.norm(np.array([f['y'],f['z']])-[y,-28.5])) for f in fits2)
 report['holes'].append(dict(expected_YZ=[y,-28.5],sections=fits+fits2,center_offset_mm=d,max_axis_drift_mm=axial))
 assert d<.005 and axial<.005
 ax.plot(y,-28.5,'k+',markersize=14);ax.set_xlim(y-5,y+5);ax.set_ylim(-33.5,-23.5);ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend();ax.set_xlabel('Y / mm');ax.set_ylabel('Z / mm');ax.set_title(f'孔中心 Y={y}，Z=-28.5\n两孔中心差 {d:.6f} mm')
fig.suptitle('v08 开关面板与身体孔位：实际 STL 剖面沿 X 轴叠合\n蓝色小孔让螺丝通过；橙色大孔安装热熔螺母，孔径不同但同轴',fontsize=13);fig.tight_layout();fig.savefig(P/'v08_开关孔位实际剖面对照.png',dpi=150)
# Pin cylinder through panel and insert seat confirms an unobstructed M3 shaft corridor.
for y in [-33.5,2.5]:
 pin=trimesh.creation.cylinder(radius=1.5,height=8.3,sections=96);pin.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]));pin.apply_translation([-39.75,y,-28.5])
 for label,m in [('body',B),('panel',F)]:
  hit=trimesh.boolean.intersection([pin,m],engine='manifold');vol=float(hit.volume) if len(hit.faces) else 0.0
  report[f'pin_{y}_{label}_overlap_mm3']=vol;assert abs(vol)<.001
# HTML embeds rounded geometry: check same triangle positions as current exported meshes.
html=(V/'双机接口v08_交互预览.html').read_text(encoding='utf-8');data=json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>',html,re.S).group(1))
for name,m in [('01_原高身体_v08',B),('03_开关模块面板_v08',F)]:
 o=next(o for o in data if o['name']==name);vv=np.array(o['v']);ff=np.array(o['f'])
 ok=vv.shape==m.vertices.shape and np.allclose(vv,np.round(m.vertices,3)) and np.array_equal(ff,m.faces)
 report[name+'_HTML_matches_STL']=bool(ok);assert ok
(P/'孔位复核结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
