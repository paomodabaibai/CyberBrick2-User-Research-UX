from pathlib import Path
import subprocess,json,concurrent.futures
from PIL import Image,ImageDraw,ImageFont
WORK=Path(__file__).resolve().parents[1]
rows=json.loads((WORK/'01_素材分析/视频音频清单.json').read_text(encoding='utf8'))
frames=WORK/'01_素材分析/采样帧';frames.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
def one(r):
 if r.get('duplicate_of'):return
 id=r['id'];dur=r['duration'];out=frames/id;out.mkdir(exist_ok=True)
 if r['width']:
  count=6 if dur<15 else 12 if dur<240 else 24
  times=[max(0,min(dur-.15,(i+.35)*dur/count)) for i in range(count)]
  canvas=Image.new('RGB',(1440,325*((count+2)//3)+65),'#151515');draw=ImageDraw.Draw(canvas)
  draw.text((15,12),id+'  '+r['name'],font=font,fill='white')
  records=[]
  for i,t in enumerate(times):
   p=out/f'{t:08.2f}.jpg'
   if not p.exists():
    cmd=['ffmpeg','-hide_banner','-v','error','-ss',str(t),'-i',r['path'],'-frames:v','1','-vf','scale=470:270:force_original_aspect_ratio=decrease,pad=470:270:(ow-iw)/2:(oh-ih)/2','-q:v','3','-y',str(p)]
    x=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if x.returncode:continue
   im=Image.open(p).convert('RGB');x=(i%3)*480+5;y=(i//3)*325+60;canvas.paste(im,(x,y));draw.text((x,y+277),f'{int(t//60):02d}:{t%60:05.2f}',font=font,fill='white')
   records.append({'seconds':round(t,2),'path':str(p)})
  canvas.save(WORK/'01_素材分析'/f'{id}_画面索引.jpg',quality=85)
  (out/'frames.json').write_text(json.dumps(records,indent=2),encoding='utf8')
 if r['audio_codec']:
  wav=WORK/'05_音频与兼容素材'/f'{id}_16k.wav'
  if not wav.exists():
   x=subprocess.run(['ffmpeg','-hide_banner','-v','warning','-i',r['path'],'-vn','-ac','1','-ar','16000','-c:a','pcm_s16le','-y',str(wav)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   if x.stderr:(WORK/'01_素材分析'/f'{id}_音频解码日志.txt').write_bytes(x.stderr)
 print('READY',id,r['name'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(one,rows))
