# 配音 06–10 的字级时间，输出 assets/vo_words.json（秒相对于各自 wav 开头），动效卡点用
import json, pathlib
from faster_whisper import WhisperModel

ROOT = pathlib.Path(__file__).resolve().parents[1]
C = ROOT.parent / '配音_v05' / '去闷试听' / 'C_单声道加EQ'
TXT = {'06': '规则很简单，红蓝同时出发，谁先打掉自己颜色的球，谁就赢。', '07': '如果半路撞上，也可以先打一架。', '08': '操纵简单，一分钟就能上手。',
       '09': '而且它是可以DIY的，身体模块和武器模块能够拆开。', '10': '你可以自己设计更厉害的攻击模块，3D打印出来，获得独属于自己的机器人。'}
m = WhisperModel('large-v3', device='cpu', compute_type='int8', cpu_threads=4, local_files_only=True)
out = {}
for k, txt in TXT.items():
    segs, _ = m.transcribe(str(C / f'{k}.wav'), language='zh', word_timestamps=True, beam_size=5, condition_on_previous_text=False, initial_prompt=txt)
    words = [(round(w.start, 2), round(w.end, 2), w.word) for s in segs for w in s.words]
    out[k] = words
    print(k, ' '.join(f'{w[2]}@{w[0]}' for w in words))
(ROOT / 'assets' / 'vo_words.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
