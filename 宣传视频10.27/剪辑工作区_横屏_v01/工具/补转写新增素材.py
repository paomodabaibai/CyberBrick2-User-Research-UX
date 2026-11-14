from pathlib import Path
import json,subprocess,time
from faster_whisper import WhisperModel
W=Path(__file__).resolve().parents[1];rows=json.loads((W/'07_素材命名/新增视频清单.json').read_text('utf8'))
modelpath=Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots/536b0662742c02347bc0e980a01041f333bce120'
model=WhisperModel(str(modelpath),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1)
def tc(t):
 n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
for v in rows:
 out=W/'02_逐段转写'/v['id']
 if out.with_suffix('.json').exists() or out.with_suffix('.txt').exists():continue
 if not any(s['codec_type']=='audio' for s in v['probe']['streams']):
  out.with_suffix('.txt').write_text('原素材无音轨，无讲话可转写。',encoding='utf8');print('NO_AUDIO',v['id'],flush=True);continue
 wav=W/'05_音频与兼容素材'/f"{v['id']}_16k.wav"
 subprocess.run(['ffmpeg','-v','error','-i',v['path'],'-vn','-ar','16000','-ac','1','-y',str(wav)],check=True)
 segments,info=model.transcribe(str(wav),language='zh',beam_size=3,temperature=0,condition_on_previous_text=False,vad_filter=True)
 records=[{'start':round(s.start,3),'end':round(s.end,3),'text':s.text.strip()} for s in segments]
 out.with_suffix('.json').write_text(json.dumps({'id':v['id'],'source':v['path'],'status':'机器转写，未逐字听校','segments':records},ensure_ascii=False,indent=2),encoding='utf8')
 out.with_suffix('.txt').write_text('机器转写，未逐字听校。\n'+v['name']+'\n'+'\n'.join(f"[{tc(s['start'])} --> {tc(s['end'])}] {s['text']}" for s in records)+( '\n未识别出可靠讲话。' if not records else ''),encoding='utf8')
 out.with_suffix('.srt').write_text('\n\n'.join(f"{i}\n{tc(s['start'])} --> {tc(s['end'])}\n{s['text']}" for i,s in enumerate(records,1)),encoding='utf8')
 print('DONE',v['id'],len(records),flush=True)
