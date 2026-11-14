from pathlib import Path
import json, subprocess, re, io, concurrent.futures
from PIL import Image,ImageOps,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2]; W=R/'剪辑工作区_横屏_v01'; A=W/'01_素材分析'; O=W/'07_素材命名'; O.mkdir(exist_ok=True)
vs=json.loads((A/'视频音频清单.json').read_text('utf-8-sig')); ps=json.loads((A/'图片清单.json').read_text('utf-8-sig')); known={x['path'] for x in vs+ps}
new=sorted(p for p in R.iterdir() if p.is_file() and str(p) not in known and p.suffix.lower()=='.mp4')
def probe(p):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)],encoding='utf8'))
 return {'path':str(p),'name':p.name,'probe':d,'duration':float(d['format'].get('duration',0))}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: nv=list(ex.map(probe,new))
for i,v in enumerate(nv,33):v['id']=f'V{i:02}'
(O/'新增视频清单.json').write_text(json.dumps(nv,ensure_ascii=False,indent=2),encoding='utf8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
canvas=Image.new('RGB',(1000,len(nv)*220),'#eeeeee'); draw=ImageDraw.Draw(canvas)
for j,v in enumerate(nv):
 draw.text((10,j*220+2),f"{v['id']} {v['name']} {v['duration']:.1f}s",font=font,fill='black')
 for k,ratio in enumerate([.12,.5,.85]):
  r=subprocess.run(['ffmpeg','-v','error','-ss',str(v['duration']*ratio),'-i',v['path'],'-frames:v','1','-vf','scale=320:180:force_original_aspect_ratio=decrease','-f','image2pipe','-vcodec','mjpeg','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if r.stdout:
   im=Image.open(io.BytesIO(r.stdout)); canvas.paste(im,(k*330+5,j*220+35))
canvas.save(O/'新增视频画面索引.jpg')
photos=sorted(p for p in R.iterdir() if p.suffix.lower() in ['.jpg','.png','.jpeg'])
pr=[]
for i,p in enumerate(photos,1):
 old=next((x for x in ps if x['path']==str(p)),None); ident=old['id'] if old else f'N{i:02}'
 with Image.open(p) as im:
  exif={str(k):str(v) for k,v in im.getexif().items() if k in [306,36867,36868]}
 pr.append({'id':ident,'path':str(p),'exif':exif})
for start in range(0,len(pr),15):
 chunk=pr[start:start+15]; c=Image.new('RGB',(1200,((len(chunk)+2)//3)*260),'#eeeeee'); d=ImageDraw.Draw(c)
 for j,p in enumerate(chunk):
  with Image.open(p['path']) as im:im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((390,220)); c.paste(im,((j%3)*400,(j//3)*260+35))
  d.text(((j%3)*400+5,(j//3)*260+5),p['id']+' '+Path(p['path']).name[:20],font=font,fill='black')
 c.save(O/f'照片索引_{start//15+1}.jpg')
(O/'照片命名清单.json').write_text(json.dumps(pr,ensure_ascii=False,indent=2),encoding='utf8')
print('new videos',len(nv),'photos',len(pr),'output',O)
