"""Add independently read CAD hole-axis evidence, remove stale exports, refresh handoff."""
from pathlib import Path
import json,cadquery as cq,hashlib,csv
P=Path(__file__).resolve().parent;ROOT=P.parent.parent
R=json.loads((P/'v11_装配与旋转检查.json').read_text(encoding='utf-8'))
C='12_圆肩避孔罩_v11'
src=(P/'check_v11.py').read_text(encoding='utf-8')
exec(src[src.index('def axes('):src.index("(P/'v11_装配与旋转检查.json')")])
assert R['cover_mount_coaxial']
(P/'v11_装配与旋转检查.json').write_text(json.dumps(R,ensure_ascii=False,indent=2),encoding='utf-8')
assert not R['motion_collisions'] and not R['cover_install_collisions'] and not R['hand_insert_collisions']
report=json.loads((P/'v11_改动与几何记录.json').read_text(encoding='utf-8'))
report['scope']='New cover perimeter and inward cover mounts, one-piece arm+insert, hand pin holes removed. Fist/body/switch untouched.'
(P/'v11_改动与几何记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for n in report['removed']:
 for d,e in [('装配网格','.stl'),('STEP_审阅件','.step')]:
  f=P/d/(n+e)
  if f.is_file():f.unlink()
for f in (P/'STEP_审阅件').glob('*_boundary_debug.txt'):f.unlink()
note='''> **2026-10-29 v11巴掌外观简化（当前结构预览）：** 四角贯穿刀孔改为盖子圆肩内收、身体螺丝露在罩外；盖子自身两颗固定孔及承重座固定耳同步移到X=-27/Y=±15，二者须配套使用。双凸筋填实圆润，接杆/转盘/腕部插芯合成一件，手掌取消横销孔，按用户502胶粘方案保留独立手掌。身体39mm、75mm巴掌及51mm原接口基准不变；拳头和v10开关未改。受影响静态、每5°旋转、盖子套入、胶粘插接和工具通路检查通过；实物配合/胶粘强度未验证，不作批量打印放行。入口：`04_结构与硬件/巴掌外观简化_v11/先看这里_v11巴掌简化.md`。无串口/固件/Git提交或推送。

'''
for rel in ['PROJECT_CONTEXT.md','00_项目管理/继续任务_给其他Agent.md','00_项目管理/2026-10-29_双机结构v08交接/01_当前状态与下一步.md']:
 f=ROOT/rel;t=f.read_text(encoding='utf-8')
 if not t.startswith(note):f.write_text(note+t,encoding='utf-8')
with (P/'v11文件快照_SHA256.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['path','bytes','sha256'])
 for q in sorted(P.rglob('*')):
  if q.is_file() and q.suffix in ('.stl','.step','.py','.html','.md','.json') and '__pycache__' not in q.parts:w.writerow([q.relative_to(P).as_posix(),q.stat().st_size,hashlib.sha256(q.read_bytes()).hexdigest()])
print('PASS cover/seat screw axes; handoff updated')
