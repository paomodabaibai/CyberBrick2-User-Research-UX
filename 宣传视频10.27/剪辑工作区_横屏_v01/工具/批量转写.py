from pathlib import Path
import json,time,traceback
from faster_whisper import WhisperModel
WORK=Path(__file__).resolve().parents[1]
rows=json.loads((WORK/'01_素材分析/视频音频清单.json').read_text(encoding='utf8'))
modelpath=Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots/536b0662742c02347bc0e980a01041f333bce120'
model=WhisperModel(str(modelpath),device='cpu',compute_type='int8',cpu_threads=8,num_workers=1)
def tc(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
for r in sorted(rows,key=lambda r:(r['duration']>600,r['group']!='新素材',r['duration'])):
 out=WORK/'02_逐段转写'/r['id']
 if out.with_suffix('.json').exists():continue
 if r.get('duplicate_of'):
  out.with_suffix('.txt').write_text('与'+r['duplicate_of']+'逐字节相同，复用该文件转写。',encoding='utf8');continue
 if not r['audio_codec']:
  out.with_suffix('.txt').write_text('原素材没有音轨，无讲话可转写。画面另见索引。',encoding='utf8');continue
 wav=WORK/'05_音频与兼容素材'/f"{r['id']}_16k.wav"
 for _ in range(180):
  if wav.exists():break
  time.sleep(1)
 try:
  print('START',r['id'],r['name'],flush=True);started=time.time()
  segs,info=model.transcribe(str(wav),language='zh',beam_size=3,temperature=0,condition_on_previous_text=False,vad_filter=True,vad_parameters={'min_silence_duration_ms':500},word_timestamps=False)
  records=[]
  for s in segs:
   records.append({'start':round(s.start,3),'end':round(s.end,3),'text':s.text.strip(),'avg_logprob':round(s.avg_logprob,3),'no_speech_prob':round(s.no_speech_prob,3)})
   if len(records)%35==0:print('PROGRESS',r['id'],round(s.end),flush=True)
  payload={'source':r['path'],'id':r['id'],'model':'faster-whisper-small CPU int8','status':'机器转写 未逐字听校','segments':records}
  out.with_suffix('.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
  txt=['机器转写，未逐字听校；噪声、专有名词和多人对白可能有误。',r['name'],'']
  for s in records:txt.append(f"[{tc(s['start'])} --> {tc(s['end'])}] {s['text']}")
  if not records:txt.append('未识别出可靠讲话；不等于原音轨完全静音。')
  out.with_suffix('.txt').write_text('\n'.join(txt),encoding='utf8')
  out.with_suffix('.srt').write_text('\n\n'.join(f"{i}\n{tc(s['start'])} --> {tc(s['end'])}\n{s['text']}" for i,s in enumerate(records,1)),encoding='utf8')
  print('DONE',r['id'],len(records),'segments',round(time.time()-started,1),'s',flush=True)
 except Exception:
  out.with_suffix('.error.txt').write_text(traceback.format_exc(),encoding='utf8');print('FAILED',r['id'],flush=True)
