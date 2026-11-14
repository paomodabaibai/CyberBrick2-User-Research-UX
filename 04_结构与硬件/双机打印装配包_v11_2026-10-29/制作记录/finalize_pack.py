from pathlib import Path
import html,re,json,csv,hashlib,zipfile
import numpy as np,trimesh,cadquery as cq
P=Path(__file__).resolve().parent.parent;ROOT=P.parent.parent;SRC=P.parent/'巴掌外观简化_v11'
rows=json.loads((P/'制作记录/打印件与来源.json').read_text(encoding='utf-8'))
result={'required_files':len(rows),'robots':{},'failures':[],'board_axes_actual_CAD':[],'slicer_run':False,'physical_fit':False}
for robot in ('palm','fist'):result['robots'][robot]=sum(r['robot']==robot for r in rows)
assert result['robots']=={'palm':17,'fist':15}
for r in rows:
 f=P/r['file'];m=trimesh.load_mesh(f);assert m.is_volume and abs(m.bounds[0,2])<.001 and m.volume>0
 assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256']
 # Rigid transformation only; restored bounds and volume must match source geometry.
 restored=m.copy();restored.apply_translation(-np.array(r['bed_translation']));restored.apply_transform(np.linalg.inv(np.array(r['rotation_matrix'])))
 src=(P/'制作记录/主板托架_装配坐标.stl') if r['id']=='C02' else SRC/'装配网格'/(r['source_name']+'.stl')
 orig=trimesh.load_mesh(src)
 assert np.allclose(restored.bounds,orig.bounds,atol=.001),(r['name'],'bounds changed')
 assert abs(restored.volume-orig.volume)<max(.08,orig.volume*.00002),(r['name'],'volume changed')
# Read official receiver PCB hole axis and stack to verify the small screw starts at PCB, not at the post.
ref=ROOT/'01_研究参考/CyberBrick1迁移研究/Remote Control Receiver-XA003-XA004.stp'
board=cq.importers.importStep(str(ref)).rotate((0,0,0),(1,1,1),120).rotate((0,0,0),(1,0,0),90).translate((-17,5,-18))
for f in board.faces().vals():
 if f.geomType()!='CYLINDER':continue
 c=f._geomAdaptor().Cylinder();a=c.Axis();q=a.Location();v=a.Direction()
 if abs(v.Y())>.999 and abs(c.Radius()-1.35)<.01 and any(abs(q.X()-x)<.01 and abs(q.Z()-z)<.01 for x in (-29,-5) for z in (-29.5,-6.5)):
  b=f.BoundingBox();result['board_axes_actual_CAD'].append({'x':q.X(),'z':q.Z(),'y_min':b.ymin,'y_max':b.ymax,'radius':c.Radius()})
assert len(result['board_axes_actual_CAD'])>=4,'receiver hole check missing'
(P/'制作记录/打包验收.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
# Minimal offline HTML manual, generated from the editable Markdown originals.
def inline(s):
 s=html.escape(s)
 s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s);s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 return s
def md(text):
 out=[];table=False
 for line in text.splitlines():
  s=line.strip()
  if s.startswith('|'):
   if not table:out.append('<div class="scroll"><table>');table=True
   cells=s.strip('|').split('|')
   if all(re.fullmatch(r'\s*:?-+:?\s*',c) for c in cells):continue
   out.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in cells)+'</tr>');continue
  if table:out.append('</table></div>');table=False
  if not s:continue
  if s.startswith('#'):
   n=min(len(s)-len(s.lstrip('#')),3);out.append(f'<h{n}>'+inline(s[n:].strip())+f'</h{n}>')
  else:out.append('<p>'+inline(s)+'</p>')
 if table:out.append('</table></div>')
 return '\n'.join(out)
css='''body{margin:0;background:#f3f5f7;color:#233443;font:17px/1.8 "Microsoft YaHei",sans-serif}header,main{max-width:1100px;margin:auto;padding:28px}header{background:#fff}nav a{display:inline-block;padding:8px 16px;margin:4px;background:#e6f0f7;border-radius:8px;color:#176493;text-decoration:none}section{background:#fff;padding:28px;margin:20px 0;border-radius:14px}h1{font-size:28px}h2{font-size:23px;margin-top:30px}h3{font-size:19px}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;font-size:15px}td{border:1px solid #d4dce4;padding:8px}tr:first-child{background:#eaf0f5;font-weight:bold}.scroll{overflow-x:auto}code{background:#eef1f5;padding:2px 4px;overflow-wrap:anywhere}a{color:#146a9e}.pair{display:grid;grid-template-columns:1fr 1fr}.note{padding:15px;background:#fff0d8;border-radius:8px}@media(max-width:700px){.pair{grid-template-columns:1fr}header,main,section{padding:14px}}@media print{nav{display:none}body{background:white}section{break-before:page}p{break-inside:avoid}}'''
chunks=['<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>milk双机打印与安装说明</title><style>'+css+'</style><header><h1>milk 双机 · 打印与安装说明</h1><p>2026-10-29｜白色身体，蓝／红脚板与攻击模块｜先完成各一台试装</p><nav><a href="#print">怎么打印</a><a href="#hardware">缺哪些五金</a><a href="#pictures">认件与拆装图</a><a href="#assembly">逐步安装</a></nav><div class="note">需要热熔铜螺母：蓝机8颗、红机6颗。不是所有螺丝都用M3。眼睛直接胶粘。未切片、未实物试装。</div></header><main><section><div class="pair"><img src="03_装配图/蓝色巴掌机_配色.png"><img src="03_装配图/红色拳头机_配色.png"></div></section>']
for ident,file in [('print','01_打印前先看.md'),('hardware','02_五金采购与用量.md')]:chunks.append(f'<section id="{ident}">'+md((P/'00_先读说明'/file).read_text(encoding='utf-8'))+'</section>')
chunks.append('<section id="pictures"><h1>认件与安装图</h1>')
for name in ['巴掌机_文件认件图.png','拳头机_文件认件图.png','01_共用身体_分层安装.png','02_巴掌机_分层安装.png','03_拳头机_分层安装.png']:chunks.append('<img loading="lazy" src="03_装配图/'+name+'">')
chunks.append('</section><section id="assembly">'+md((P/'00_先读说明/03_一步一步安装.md').read_text(encoding='utf-8'))+'</section></main></html>')
(P/'00_打开这个安装说明.html').write_text('\n'.join(chunks),encoding='utf-8')
note='''> **2026-10-29 打印/装配包已整理：** `04_结构与硬件/双机打印装配包_v11_2026-10-29/00_打开这个安装说明.html`。蓝机17件/红机15件，按白身体短腿、蓝/红脚板攻击模块、黑眼睛分类；眼睛胶粘，白高光可用笔。热熔铜螺母巴掌8/拳头6，非全M3。打包时发现C02主板托架原Ø2.7光孔无明确锁紧，本包仅将4孔改成Ø2.1底孔配外径2.5×8mm塑料自攻，保留外形/孔轴；以本包C02为准，原v11托架保留历史。已做32件闭合/落底/刚体变换/源尺寸检查和装配图；未切片或实物试装，首套验证后再复制，不是六台批量验证。主板/开关用小自攻螺钉，输出轴/舵盘沿用原配，具体非M3项目见五金表。

'''
for rel in ['PROJECT_CONTEXT.md','00_项目管理/继续任务_给其他Agent.md']:
 f=ROOT/rel;s=f.read_text(encoding='utf-8')
 if not s.startswith(note):f.write_text(note+s,encoding='utf-8')
with (P/'制作记录/文件校验_SHA256.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['file','bytes','sha256'])
 for q in sorted(P.rglob('*')):
  if q.is_file() and q.name!='文件校验_SHA256.csv':w.writerow([q.relative_to(P).as_posix(),q.stat().st_size,hashlib.sha256(q.read_bytes()).hexdigest()])
z=P.with_suffix('.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
 for f in sorted(P.rglob('*')):
  if f.is_file():archive.write(f,P.name+'/'+f.relative_to(P).as_posix())
with zipfile.ZipFile(z) as a:assert a.testzip() is None
print('VERIFIED',result['robots'],'board_axes',result['board_axes_actual_CAD'],'ZIP_MB',round(z.stat().st_size/1024**2,1),flush=True)
