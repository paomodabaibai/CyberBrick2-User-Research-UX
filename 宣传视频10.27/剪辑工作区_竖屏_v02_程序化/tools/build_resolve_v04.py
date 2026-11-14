# 把 v04 剪辑骨架（达芬奇交接/v04_剪辑骨架.json）搭成达芬奇可编辑时间线：独立新工程，1080×1920@30，
# 每个镜头一段 100% 速度素材，片段上打标记（名称 = 镜头编号，备注 = 原有特效），时间线标记写口播稿。
# 需要达芬奇里先运行 工作区 → 脚本 → Utility → resolve_bridge。
import sys, json, pathlib
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect

ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT / '达芬奇交接'
PROJECT, TIMELINE, FPS = '棋甲对决_竖屏抖音_v04_可编辑', '棋甲对决 竖屏 v04 可编辑', 30
data = json.loads((OUT / 'v04_剪辑骨架.json').read_text(encoding='utf-8'))
COLORS = {'hook': 'Red', 'intro': 'Blue', 'blue': 'Cyan', 'red': 'Cyan', 'vs': 'Cyan', 'map': 'Yellow', 'real': 'Yellow', 'clash': 'Yellow', 'ball': 'Yellow', 'react': 'Yellow',
          'palm': 'Green', 'p19': 'Green', 'p32': 'Green', 'p33': 'Green', 'p14': 'Green', 'build': 'Green', 'crowd': 'Purple', 'end': 'Purple'}
color = lambda i: COLORS.get(i, COLORS.get(i.split('_')[0], 'Blue'))

resolve = connect(require_enabled=False, timeout=60)
pm = resolve.GetProjectManager()
cur = pm.GetCurrentProject(); print('保存当前工程', cur.GetName(), pm.SaveProject())
proj = pm.CreateProject(PROJECT) or pm.LoadProject(PROJECT); assert proj, '建工程失败'
for k, v in [('timelineFrameRate', str(FPS)), ('timelineResolutionWidth', '1080'), ('timelineResolutionHeight', '1920'),
             ('timelinePlaybackFrameRate', str(FPS)), ('timelineInputResMismatchBehavior', 'scaleFullFrameWithCrop')]:
    print(k, proj.SetSetting(k, v), proj.GetSetting(k))
mp = proj.GetMediaPool()
items = {}
for path in dict.fromkeys(c['path'] for c in data['clips']):
    name = pathlib.Path(path).name
    old = [c for c in mp.GetRootFolder().GetClipList() if c.GetName() == name]
    r = old or mp.ImportMedia([path]); assert r, path
    items[path] = r[0]
for i in range(proj.GetTimelineCount(), 0, -1):
    t = proj.GetTimelineByIndex(i)
    if t.GetName() == TIMELINE: mp.DeleteTimelines([t])
tl = mp.CreateEmptyTimeline(TIMELINE); proj.SetCurrentTimeline(tl)
t0 = tl.GetStartFrame(); rec = t0; log = []
# 先算好每个镜头在新时间线上的位置（100% 速度，帧数 = 源出点 - 源入点）
pos = 0
for c in data['clips']:
    c['sf'], c['ef'] = int(round(c['a'] * c['fps'])), int(round(c['b'] * c['fps']))
    c['new_start'], c['new_dur'] = pos / FPS, (c['ef'] - c['sf']) / FPS; pos += c['ef'] - c['sf']
# 字幕：v04 的时间按所在镜头换算到新时间线（去掉了慢动作/定格，镜头变短了）
def remap(t):
    for c in data['clips']:
        if c['v04_start'] <= t < c['v04_start'] + c['v04_dur'] + 1e-6:
            return c['new_start'] + (t - c['v04_start']) * c['new_dur'] / c['v04_dur']
    return t
ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round(x % 1 * 1000)) % 1000:03d}"
srt = []
for k, s in enumerate(sorted(data['subs'], key=lambda s: s['at']), 1):
    a, b = remap(s['at']), remap(min(s['out'], s['at'] + 30))
    srt.append(f"{k}\n{ts(a)} --> {ts(max(b, a + 0.5))}\n{s['text']}\n")
srt_path = OUT / '口播字幕_v04可编辑.srt'; srt_path.write_text('\n'.join(srt), encoding='utf-8-sig')
# 字幕必须在空时间线上先放（达芬奇会把字幕接在时间线末尾，忽略指定起点）
tl.AddTrack('subtitle')
old = [c for c in mp.GetRootFolder().GetClipList() if c.GetName() == srt_path.name]
if old: mp.DeleteClips(old)
si = mp.ImportMedia([str(srt_path)]); print('导入字幕', bool(si))
if si: print('字幕上轨', bool(mp.AppendToTimeline([{'mediaPoolItem': si[0]}])))
for c in data['clips']:
    sf, ef = c['sf'], c['ef']
    out = mp.AppendToTimeline([{'mediaPoolItem': items[c['path']], 'startFrame': sf, 'endFrame': ef, 'recordFrame': rec, 'trackIndex': 1}])
    assert out, c['id']
    v = [x for x in out if x.GetTrackTypeAndIndex()[0] == 'video'][0]
    v.AddMarker(0, color(c['id']), c['id'], c['note'], 1)
    v.SetClipColor({'Red': 'Orange', 'Blue': 'Blue', 'Cyan': 'Teal', 'Yellow': 'Yellow', 'Green': 'Green', 'Purple': 'Purple'}[color(c['id'])])
    log.append((c['id'], v.GetStart() - t0, v.GetDuration(), ef - sf))
    if c.get('cover'):   # 横拍素材放大铺满竖屏（达芬奇默认按宽度放入，上下黑边）
        z = 1920 / 1080 / (1080 / 1920); v.SetProperty('ZoomX', z); v.SetProperty('ZoomY', z); v.SetProperty('Pan', (0.5 - c['cx']) * 1080 * z)
    rec = v.GetEnd()
sub_items = tl.GetItemListInTrack('subtitle', 1) or []
print('字幕条数', len(sub_items), '首条起点', (sub_items[0].GetStart() - t0) / FPS if sub_items else None)
gaps = [(log[i][0], log[i + 1][1] - log[i][1] - log[i][2]) for i in range(len(log) - 1) if log[i + 1][1] != log[i][1] + log[i][2]]
for row in log: print(*row)
print('总长', (tl.GetEndFrame() - t0) / FPS, '秒；缝隙', gaps)
print('保存', pm.SaveProject())
print('DRP', pm.ExportProject(PROJECT, str(OUT / f'{PROJECT}.drp')))
print('DRT', tl.Export(str(OUT / f'{TIMELINE}.drt'), resolve.EXPORT_DRT))
