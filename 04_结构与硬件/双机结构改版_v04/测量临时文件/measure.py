from pathlib import Path
import zipfile,json
import cadquery as cq
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REF=ROOT/'01_研究参考'/'CyberBrick1迁移研究'
for zname,terms in [('官方CAD.zip',['PC003.stp','XA007.STEP']),('官方规格.zip',['Accessories Specification.pdf'])]:
 with zipfile.ZipFile(REF/zname) as z:
  for n in z.namelist():
   if any(n.endswith(t) for t in terms):
    (HERE/Path(n).name).write_bytes(z.read(n))
files=[REF/'Multi-Function Controller Core-XA003.stp',REF/'Remote Control Receiver-XA003-XA004.stp']+list(HERE.glob('*.stp'))+list(HERE.glob('*.STEP'))
def bbox(s):
 b=s.BoundingBox();return [round(v,4) for v in (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)]
report={}
for f in files:
 w=cq.importers.importStep(str(f))
 d={'bounds':bbox(w.val()),'solids':[],'circles':[]}
 for i,s in enumerate(w.solids().vals()):
  d['solids'].append({'i':i,'vol':round(s.Volume(),3),'bounds':bbox(s)})
 for e in w.edges().vals():
  if e.geomType()=='CIRCLE':
   try:
    r=e.radius();c=e.arcCenter()
    if .9<=r<=3:
     d['circles'].append([round(c.x,4),round(c.y,4),round(c.z,4),round(r,4)])
   except:pass
 d['circles']=sorted(set(tuple(x) for x in d['circles']))
 report[f.name]=d
(HERE/'measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for name,d in report.items():
 print(name,'bounds',d['bounds'],'solids',len(d['solids']))
 print('largest',sorted(d['solids'],key=lambda s:s['vol'],reverse=True)[:12])
 print('circles',d['circles'][:100])
