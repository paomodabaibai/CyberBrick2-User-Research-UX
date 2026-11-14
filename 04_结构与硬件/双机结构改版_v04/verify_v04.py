from pathlib import Path
import json, numpy as np, trimesh
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
P=Path(__file__).resolve().parent
r=json.loads((P/'几何检查报告.json').read_text(encoding='utf-8'))
checks=[]
for k,v in r['checks'].items():
 if k.endswith('_mm3') and not k.startswith('E_hip'):
  assert abs(v)<.01,(k,v);checks.append(k)
for side in (-25,25):
 assert abs(r['checks'][f'E_hip_{side}_vs_body_mm3']-r['checks'][f'E_hip_{side}_vs_original_body_baseline_mm3'])<.01
 checks.append(f'hip_{side}_no_added_intrusion_to_placeholder')
parts=[]
for f in (P/'STL_审阅勿批量打印').glob('*.stl'):
 m=trimesh.load_mesh(f);assert m.is_volume,f.name
 a=m.face_adjacency;g=sp.coo_matrix((np.ones(len(a)*2),(np.r_[a[:,0],a[:,1]],np.r_[a[:,1],a[:,0]])),shape=(len(m.faces),)*2).tocsr()
 n,_=connected_components(g,directed=False)
 assert n==1,(f.name,n)
 parts.append({'file':f.name,'closed_positive':True,'connected_components':n,'dimensions_mm':m.extents.round(3).tolist()})
result={'checked_pairs':checks,'mesh_parts':parts,'pass':True,'meaning':'Nominal CAD geometry only, no real assembly/servo fit/strength/CG verification'}
(P/'独立导出核验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(checks),'checks',len(parts),'single connected printable meshes; NOT physical validation')
