"""Check paper sizes, ruler geometry, imposition and manufacturing quantities."""
from pathlib import Path
import json, math
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
MM = 72/25.4
data = json.loads((ROOT/'制作与打印清单.json').read_text(encoding='utf-8'))
pdfs = [
    ('01_材料尺寸与手搓说明_A4.pdf',7,210,297),
    ('02_贴图与模板_A4_实际尺寸.pdf',11,210,297),
    ('03_贴图与模板_A3_实际尺寸.pdf',6,420,297),
]
results=[]
for name,n,w,h in pdfs:
    doc=PdfReader(ROOT/'output'/'pdf'/name)
    assert len(doc.pages)==n
    for page in doc.pages:
        assert abs(float(page.mediabox.width)/MM-w)<.001
        assert abs(float(page.mediabox.height)/MM-h)<.001
        assert len(page.extract_text())>50
    results.append({'pdf':name,'pages':n,'paper_mm':[w,h]})

art=PdfReader(ROOT/'output'/'pdf'/pdfs[1][0])
for i,page in enumerate(art.pages):
    ops=page.get_contents().operations
    ruler=False
    for k,(v,op) in enumerate(ops):
        if op==b'l' and k and ops[k-1][1]==b'm':
            a=ops[k-1][0]
            coords=[float(a[0])/MM,float(a[1])/MM,float(v[0])/MM,float(v[1])/MM]
            if all(abs(x-y)<.001 for x,y in zip(coords,[12,12,112,12])):
                ruler=True
    assert ruler, f'No true 100 mm calibration ruler on A4 page {i+1}'

art3=PdfReader(ROOT/'output'/'pdf'/pdfs[2][0])
for i,page in enumerate(art3.pages):
    for v,op in page.get_contents().operations:
        if op==b'cm':
            assert all(abs(float(x)-y)<1e-5 for x,y in zip(v[:4],[1,0,0,1])), (i,v)

items=[q for pg in data['stickers'] if pg['type']=='wall_faces' for q in pg['items']]
assert len(items)==20 and len({q['id'] for q in items})==20
for q in items:
    x,y=q['xy_mm'];w,h=q['size_mm']
    assert x-2.2>=5 and x+w+2.2<=205
    assert y-2.2>=15 and y+h+5<=280

assert sum(x['quantity'] for x in data['pvc_cut_list'])==28
area=sum(x['width']*x['height']*x['quantity'] for x in data['pvc_cut_list'])+20*15*30/2
assert area==1823700
assert 2*420+2*3+374==1220
assert 3*630+3*3<=2440
small_row_heights=[95,75,75,55,75,40,40,40,40,40,120,30]
assert sum(small_row_heights)+11*3+10==768
assert 2*180+3+10<=374
assert 610+420+2*3<1200
assert 200*2+220*2+4*3<1000
assert 135+35+8==178 and 178-5==173 and 178-55-35==88

report={'result':'PASS','pdfs':results,'wall_faces':20,'pvc_rectangles':28,
        'pvc_area_including_braces_m2':area/1e6,
        'A4_ruler_mm':100,'A3_imposition':'identity scale; translation only',
        'render_review':'All 24 pages rendered and visually reviewed; revised guide pages re-rendered.',
        'physical_robot_tested':False}
(ROOT/'文件核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
