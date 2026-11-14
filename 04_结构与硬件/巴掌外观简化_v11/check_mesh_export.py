from pathlib import Path
import trimesh,numpy as np,cadquery as cq
p=Path(__file__).resolve().parent/'STEP_审阅件'
for stem in ['13_承重座_v11内收盖耳','12_圆肩避孔罩_v11']:
 s=cq.importers.importStep(str(p/(stem+'.step'))).val()
 print(stem,s.isValid(),len(s.Solids()),s.Volume(),flush=True)
 for tol in [.03,.01]:
  v,f=s.tessellate(tol,.05)
  for digits in [7,6,5,4]:
   m=trimesh.Trimesh(np.array([a.toTuple() for a in v]),np.array(f),process=True)
   m.merge_vertices(digits_vertex=digits);m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
   print(tol,digits,m.is_volume,len(m.faces),flush=True)
  edges,counts=np.unique(np.sort(m.edges,axis=1),axis=0,return_counts=True)
  b=m.vertices[edges[counts!=2]]
  print('bad edges',len(b),'bounds',b.min(axis=(0,1)),b.max(axis=(0,1)),flush=True)
  np.savetxt(p/(stem+'_boundary_debug.txt'),b.reshape(-1,6))
