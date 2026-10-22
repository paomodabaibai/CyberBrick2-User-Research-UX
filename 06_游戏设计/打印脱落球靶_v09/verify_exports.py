from pathlib import Path
import json,hashlib
import trimesh

r=Path(__file__).resolve().parent/'制造初样_v01'
report=json.loads((r/'04_总装与检查/几何检查报告.json').read_text(encoding='utf-8'))
results=[]
for p in sorted(r.rglob('*.stl')):
    m=trimesh.load(p,force='mesh',process=True)
    assert m.is_watertight and m.is_volume,(p.name,'not closed positive volume')
    assert m.body_count==1,(p.name,'multiple connected bodies',m.body_count)
    assert abs(m.bounds[0,2])<1e-4,(p.name,'not on bed')
    ref=report['parts'][p.stem]
    error=abs(m.volume-ref['volume_mm3'])/ref['volume_mm3']
    assert error<.02,(p.name,'mesh volume deviation',error)
    results.append({'file':p.relative_to(r).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                    'closed_single_body':True,'on_bed':True,'relative_volume_error':error})
assert len(results)==16,len(results)
(r/'04_总装与检查/STL导出复核.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(results)} exported STLs reopened: watertight, positive volume, single body, bed Z=0, BREP volume error <2%')
