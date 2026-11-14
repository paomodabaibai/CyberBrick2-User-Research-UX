from pathlib import Path
import json,subprocess,concurrent.futures
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[1]
videos={r['id']:r for r in json.loads((W/'01_素材分析/视频音频清单.json').read_text(encoding='utf8'))}
photos={r['id']:r for r in json.loads((W/'01_素材分析/图片清单.json').read_text(encoding='utf8'))}
# Fully real-world footage; no AI concept scene is represented as a user trial.
spec=[
 ('V22',136,3,'棋甲对决','桌面双足机器人对战系统'),
 ('P09',0,3,'两种战斗风格','蓝色巴掌 × 红色拳头'),
 ('V30',0,4,'双人桌面对战','把遥控器交给朋友，现场开一局'),
 ('V22',3,4,'穿过障碍，争夺目标','在同一张地图里走位与对抗'),
 ('V04',24,4,'操控它，走进竞技场','双足行走 · 实体遥控'),
 ('V03',2.5,4,'巴掌横扫','摇杆控制正反转\n松手回中停止'),
 ('V07',14,4,'拳头往复','持续推杆，连续出拳\n上推慢，下推快'),
 ('V04',68.5,5,'命中！目标脱落','真实击球片段'),
 ('V22',137,4,'近身交锋','走位、阻拦，再找机会出手'),
 ('V05',72,4,'再来一段战舞','对战之外，也有意外的乐趣'),
 ('V30',82,4,'围观，也会想上手','真实课堂试玩'),
 ('V32',0,4,'换个人，再开一局','把操作的乐趣传给下一个人'),
 ('V19',0,2,'从装配开始','打印 · 组装 · 调试'),
 ('P03',0,2,'把零件，变成动作','拳头机构实物'),
 ('P07',0,4,'把作品，带上桌面','milk 组 · 课程项目'),
 ('P09',0,5,'棋甲对决','把创造，带上擂台')]
fps=30;shots=[];cursor=0
for i,(id,source,duration,title,sub) in enumerate(spec,1):
 r=videos.get(id) or photos[id];p=Path(r['path']);portrait=False
 if id.startswith('V'):
  wi,he=r['width'],r['height']
  if abs(r.get('rotation',0))%180==90:wi,he=he,wi
  portrait=he>wi
  extract=max(0,source-1);offset=round((source-extract)*fps)
  media_duration=min(r['duration']-extract,duration+(source-extract)+1)
 else:
  im=Image.open(p);portrait=im.height>im.width
  extract=0;offset=30;media_duration=duration+2
 shot={'index':i,'source_id':id,'source_path':str(p),'source_in':source,'duration':duration,'record_in':cursor,'frames':round(duration*fps),'media_in_frames':offset,'extract_start':extract,'media_duration':media_duration,'portrait':portrait,'title':title,'subtitle':sub,'media_path':str(W/'05_音频与兼容素材'/f'S{i:02d}_{id}_可调片段.mov')}
 shots.append(shot);cursor+=duration
assert cursor==60
(W/'03_剪辑方案/横屏60秒_剪辑清单.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2),encoding='utf8')
font='C:/Windows/Fonts/msyh.ttc';bold='C:/Windows/Fonts/msyhbd.ttc'
titlefont=ImageFont.truetype(bold,58);subfont=ImageFont.truetype(font,32);tagfont=ImageFont.truetype(bold,24)
def prepare(s):
 out=Path(s['media_path'])
 if not out.exists():
  cmd=['ffmpeg','-hide_banner','-v','error']
  if s['source_id'].startswith('P'):cmd+=['-loop','1','-i',s['source_path']]
  else:cmd+=['-ss',str(s['extract_start']),'-i',s['source_path']]
  r=videos.get(s['source_id'])
  if not r or not r.get('audio_codec'):cmd+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
  if s['portrait']:
   vf='scale=1000:1000:force_original_aspect_ratio=decrease,pad=1920:1080:170:40:color=0x101925,setsar=1,fps=30'
  else:vf='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x101925,setsar=1,fps=30'
  cmd+=['-map','0:v:0','-map','0:a:0' if r and r.get('audio_codec') else '1:a:0','-vf',vf,'-t',str(s['media_duration']),'-c:v','dnxhd','-profile:v','dnxhr_lb','-pix_fmt','yuv422p','-c:a','pcm_s16le','-ar','48000','-ac','2','-threads','3','-map_metadata','-1','-y',str(out)]
  res=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if res.returncode:raise RuntimeError(res.stderr.decode('utf8','replace'))
 # Preview graphics remain separate in the edit; native Fusion text is created by Lua.
 overlay=Image.new('RGBA',(1920,1080),(0,0,0,0));d=ImageDraw.Draw(overlay)
 if s['portrait']:
  d.text((870,340),'MILK / PROJECT DEMO',font=tagfont,fill='#56d4e8')
  d.text((865,420),s['title'],font=titlefont,fill='white')
  d.multiline_text((870,520),s['subtitle'],font=subfont,fill='#d7e2ee',spacing=18)
  d.line((870,640,1060,640),fill='#f2a67f',width=4)
 else:
  d.rectangle((0,855,1920,1080),fill=(10,17,29,170))
  d.text((90,880),s['title'],font=titlefont,fill='white')
  d.text((95,965),s['subtitle'].replace('\n',' / '),font=subfont,fill='#d7e2ee')
 overlay.save(W/'05_音频与兼容素材'/f"S{s['index']:02d}_文字参考.png")
 print('MEDIA',s['index'],s['source_id'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:list(p.map(prepare,shots))
Image.new('RGBA',(1920,1080),(0,0,0,0)).save(W/'05_音频与兼容素材/透明底.png')
subprocess.run(['ffmpeg','-v','error','-loop','1','-i',str(W/'05_音频与兼容素材/透明底.png'),'-t','6','-r','30','-c:v','qtrle','-pix_fmt','argb','-y',str(W/'05_音频与兼容素材/透明文字底.mov')],check=True)
print('PREPARED 16 clips; 60 seconds',flush=True)
