"""Read-only image/PDF QA. Does not edit image pixels."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1]
temp=Path(r'E:\CodexData\Scratch\cyber-floor-20261019')
tile=Image.open(root/'地板循环单元_20x20cm_2400px.png')
a=np.array(tile).astype(np.int16)
b=np.array(Image.open(temp/'proof_400mm.png')).astype(np.int16)
assert a.shape==(2400,2400,3)
assert b.shape==(4800,4800,3)
lr=int(np.max(np.abs(a[:,0]-a[:,-1])))
tb=int(np.max(np.abs(a[0]-a[-1])))
assert lr==0 and tb==0
# Every tile edge is entirely contained in the solid periodic seam, even for
# 0.5 mm inward cutting error (=6 pixels at 12 px/mm). This is a digital guard
# region check, not a claim that manually trimmed joins have been physically tested.
base=np.array([40,73,85],dtype=np.int16)
for edge in [a[:6,:,:],a[-6:,:,:],a[:,:6,:],a[:,-6:,:]]:
    assert np.max(np.abs(edge-base))==0
stats=[]
for y in (0,2400):
    for x in (0,2400):
        d=np.abs(a-b[y:y+2400,x:x+2400])
        stats.append({'x':x,'y':y,'max_channel_difference':int(d.max()),'mean_channel_difference':float(d.mean()),'fraction_above_4':float((d.max(axis=2)>4).mean())})
        assert d.mean()<.2
        assert (d.max(axis=2)>4).mean()<.003
pdfs=[]
expected=[(420,297),(210,297),(800,1200)]
for f,size in zip(sorted((root/'print').glob('*.pdf')),expected):
    reader=PdfReader(f);assert len(reader.pages)==1
    page=reader.pages[0]
    actual=[float(page.mediabox.width)*25.4/72,float(page.mediabox.height)*25.4/72]
    assert all(abs(v-e)<.001 for v,e in zip(actual,size))
    pdfs.append({'file':f.name,'pages':1,'page_mm':actual})
report={'result':'PASS','pdfs':pdfs,'tile_px':tile.size,'png_dpi_metadata':tile.info.get('dpi'),'edge_max_difference':{'left_right':lr,'top_bottom':tb},'seam_guard_band_mm':.5,'four_tile_render_comparison':stats,'native_material_effective_ppi':round(1254/98*25.4,2),'validation_scope':'Digital size, opposite-edge equality, periodic rendering comparison and visual PDF proofs; physical printing and paper color not tested.'}
(root/'source'/'数字校验结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
