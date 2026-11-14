from pathlib import Path
import json, subprocess, hashlib, csv
ROOT=Path(__file__).resolve().parents[3]
WORK=Path(__file__).resolve().parents[1]
PRIMARY=WORK.parent
def run(args):
 return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',errors='replace')
paths=[]
for p in ROOT.rglob('*'):
 if not p.is_file() or p.suffix.lower() not in ['.mp4','.mov','.mkv','.mp3','.wav']:continue
 if any(x in p.parts for x in ['Lib','node_modules','.git','cad_runtime','serial_runtime','剪辑工作区_横屏_v01','app只读副本']):continue
 if any('备份' in x for x in p.relative_to(ROOT).parts):continue
 paths.append(p)
paths.sort(key=lambda p:(0 if p.parent==PRIMARY else 1,str(p)))
rows=[]
for i,p in enumerate(paths,1):
 r=run(['ffprobe','-v','error','-print_format','json','-show_format','-show_streams',str(p)])
 if r.returncode: print('BAD',p.name,r.stderr[:120],flush=True);continue
 data=json.loads(r.stdout);v=next((s for s in data['streams'] if s['codec_type']=='video'),{});a=next((s for s in data['streams'] if s['codec_type']=='audio'),{})
 duration=float(data['format'].get('duration',0));rot=0
 for side in v.get('side_data_list',[]):rot=side.get('rotation',rot)
 row={'id':f'V{i:02d}','path':str(p),'name':p.name,'group':'新素材' if p.parent==PRIMARY else '项目补充','duration':duration,'width':v.get('width',0),'height':v.get('height',0),'fps':v.get('avg_frame_rate','0/1'),'video_codec':v.get('codec_name'),'audio_codec':a.get('codec_name'),'audio_channels':a.get('channels'),'rotation':rot,'bytes':p.stat().st_size,'probe':data}
 rows.append(row);print(row['id'],round(duration,1),'s',row['width'],row['height'],row['audio_codec'],p.name,flush=True)
# Exact duplicates are checked only in equal-size groups.
groups={}
for r in rows:groups.setdefault(r['bytes'],[]).append(r)
for g in groups.values():
 if len(g)<2:continue
 seen={}
 for r in g:
  h=hashlib.sha256()
  with open(r['path'],'rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  r['sha256']=h.hexdigest()
  if r['sha256'] in seen:r['duplicate_of']=seen[r['sha256']]
  else:seen[r['sha256']]=r['id']
(WORK/'01_素材分析/视频音频清单.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
cols=['id','name','group','duration','width','height','fps','audio_codec','rotation','bytes','duplicate_of','path']
with (WORK/'01_素材分析/视频音频清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)
print('TOTAL',len(rows),'MINUTES',round(sum(r['duration'] for r in rows)/60,2),flush=True)
