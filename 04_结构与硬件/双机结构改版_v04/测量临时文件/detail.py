from pathlib import Path
import cadquery as cq,json
HERE=Path(__file__).resolve().parent
def bb(s):
 b=s.BoundingBox();return [round(v,3) for v in (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)]
b=cq.importers.importStep(str(next(HERE.glob('*PC003.stp'))))
for ymax in (50,51.2,52,60):
 cut=b.intersect(cq.Workplane('XY').box(50,ymax,40,centered=(True,False,True)))
 print('battery cropped at y',ymax,bb(cut.val()),cut.val().Volume())
s=cq.importers.importStep(str(next(HERE.glob('*XA007.STEP'))))
print('switch types',s.val().ShapeType(),'shells',len(s.shells().vals()),'faces',len(s.faces().vals()),'isvalid',s.val().isValid())
print('shell boxes',[bb(x) for x in s.shells().vals()])
for y in (0,1.6,7.6,13,16):
 pts=[]
 for v in s.vertices().vals():
  p=v.Center()
  if abs(p.y-y)<.1:pts.append((round(p.x,2),round(p.z,2)))
 print('switch vertex slice',y,pts[:50])
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
fig=plt.figure(figsize=(12,6))
for i,(name,w) in enumerate([('PC003 battery',b),('XA007 switch',s)]):
 ax=fig.add_subplot(1,2,i+1,projection='3d');v,f=w.val().tessellate(.15);v=np.array([p.toTuple() for p in v]);f=np.array(f)
 ax.add_collection3d(Poly3DCollection(v[f],facecolor='#5b9bb5',edgecolor='none'))
 mi=v.min(axis=0);ma=v.max(axis=0);ax.set_xlim(mi[0],ma[0]);ax.set_ylim(mi[1],ma[1]);ax.set_zlim(mi[2],ma[2]);ax.set_box_aspect(ma-mi);ax.set_title(name);ax.set_xlabel('X');ax.set_ylabel('Y');ax.set_zlabel('Z');ax.view_init(25,-60)
fig.savefig(HERE/'measure_visual.png',dpi=160)
