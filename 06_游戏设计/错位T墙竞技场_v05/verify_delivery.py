"""Cross-artifact consistency checks; not a physical acceptance test."""
from pathlib import Path
import json,re,math,csv,hashlib,zipfile,shutil
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
HW=ROOT/'04_结构与硬件'/'错位T墙竞技场_v05'
scene=json.loads((HW/'scene.json').read_text(encoding='utf-8'))
geo=json.loads((HW/'geometry_report.json').read_text(encoding='utf-8'))
draw=json.loads((HERE/'drawing_parameters.json').read_text(encoding='utf-8'))
html=(HERE/'viewer.html').read_text(encoding='utf-8')
view=json.loads(re.search(r'<script id="scene-data" type="application/json">(.*?)</script>',html,re.S).group(1))
byid={p['id']:p for p in scene['instances']}
for w in draw['walls']:
    o=byid[w['id']]
    assert o['bounds_xy_mm']==[w['x'],w['y'],w['x']+w['l'],w['y']+w['b']],w['id']
    assert o['height_mm']==w['h']
    assert (('B' not in o['variants'])==w['optional'])
for k,(x,y,_,name,_) in enumerate(draw['targets']):
    assert scene['gameplay']['targets'][k]['center_xy_mm']==[x,y]
assert view['parts']==scene['parts']
for i in view['instances']:assert i==byid[i['id']],i['id']
assert view['gameplay']==scene['gameplay']
assert len(scene['variants']['A']['include_ids'])==173
assert len(scene['variants']['B']['include_ids'])==167
for _,p in scene['parts'].items():
    for key in ('stl','step'): assert (HW/p[key]).is_file()
assert len(list((HW/'stl').glob('*.stl')))==12
assert len(list((HW/'step').glob('*.step')))==12
for key,p in geo['parts'].items():
    assert p['cad_valid'] and p['cad_solids']==1 and p['mesh_watertight'] and p['mesh_winding_consistent']
    assert p['connected_meshes']==1 and p['fits_200_cube_with_8mm_brim_per_side']
# Check ±30 target variations against all fixed obstacle AABBs (conservative for rounded ends).
clear=[]
obstacles=[i for i in scene['instances'] if i['part_id'].startswith(('W','E'))]
for delta in (-30,0,30):
    for (x,y),change in [((260,650),delta),((1000,610),-delta)]:
        y+=change
        distances=[]
        for ob in obstacles:
            a,b,c,d=ob['bounds_xy_mm'];dx=max(a-x,0,x-c);dy=max(b-y,0,y-d)
            distances.append(math.hypot(dx,dy))
        nearest=min(distances)
        assert nearest>=230, (x,y,nearest)
        clear.append({'xy':[x,y],'nearest_fixed_obstacle_mm':nearest})
pdf=HERE/'output/pdf/错位T墙竞技场_v05_尺寸与打印图册.pdf'
r=PdfReader(str(pdf));assert len(r.pages)==6
for p in r.pages:assert len(p.extract_text())>300
for n in range(1,7):assert (HERE/f'output/pdf/page-{n}.png').is_file()
report={'date':'2026-10-13','pdf_pages':6,'stl_types':12,'step_part_types':12,
 'assembly_instances':{'A':173,'B':167},'diagram_scene_viewer_match':True,
 'target_variation_clearance':clear,'physical_tested':False,'slicer_tested':False,
 'scope':'Cross-artifact consistency, saved CAD/mesh reports, PDF text and rendered pages; no robot actions.'}
(HERE/'delivery_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    # Preserve the project's 04/06 structure so relative links work after extraction.
    package=HERE/'错位T墙竞技场_v05_完整交付.zip'
    files=[]
    for base in (HW,HERE):
        for p in base.rglob('*'):
            if p.is_file() and p.suffix not in ('.zip','.pyc') and '__pycache__' not in p.parts:
                files.append(p)
    manifest={str(f.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(files):z.write(f,str(f.relative_to(ROOT)))
        z.writestr('START_HERE.md','# 错位T墙竞技场 v05\n\n先打开 [离线3D](06_游戏设计/错位T墙竞技场_v05/viewer.html)，再看同目录 output/pdf 下的6页尺寸图册。\n\n[制作说明](06_游戏设计/错位T墙竞技场_v05/README.md) · [制造零件](04_结构与硬件/错位T墙竞技场_v05/制造README.md)\n\nSTL可直接导入切片器；装配STEP仅供编辑。图纸尺寸是试打印设计，未做实机验收。场地1260方形，桌面建议1320方形，批量打印前请核实。\n\n再运行CAD脚本需要CadQuery与trimesh；这些第三方运行库没有打入交付包。尺寸图册脚本需reportlab、pypdf和微软雅黑字体。')
        z.writestr('SHA256_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    print('ZIP_OK',package.stat().st_size,len(files))
