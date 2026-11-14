# 把规则段成片放进达芬奇：画面放视频 2 轨、音效放音频 3 轨，起点对齐「完整一场」。不动已有片段；放之前先导出 .drp 备份。
# 需要达芬奇开着工程，并运行 工作区 → 脚本 → resolve_bridge。用法：python place_final.py
import pathlib, subprocess, sys, time
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect

FX = pathlib.Path(__file__).resolve().parents[1]
ROOT = FX.parent
MOV, WAV = FX / 'out' / '规则段_v6.mov', FX / 'out' / '音效_规则段.wav'
NAME = '棋甲对决_竖屏抖音_v04_可编辑'
resolve = connect(require_enabled=False, timeout=60)
pm = resolve.GetProjectManager()
p = pm.GetCurrentProject()
assert p and p.GetName() == NAME, f'当前工程不是 {NAME}'
tl = p.GetCurrentTimeline()
mp = p.GetMediaPool()
big = next((x for x in tl.GetItemListInTrack('video', 1) if x.GetName() == '完整一场'), None)
assert big, '时间线上找不到「完整一场」'
start, dur = big.GetStart(), big.GetDuration()
print('完整一场', start, dur, '起点秒', (start - tl.GetStartFrame()) / 30)
assert dur == 582, f'「完整一场」时长变了（{dur} 帧），动效按 582 帧做的，先确认'
bak = ROOT / '达芬奇交接' / f'{NAME}_放规则段前备份_{time.strftime("%m%d_%H%M")}.drp'
print('保存', pm.SaveProject(), '备份', pm.ExportProject(NAME, str(bak)), bak.name)

cur = mp.GetCurrentFolder(); head = tl.GetCurrentTimecode(); root = mp.GetRootFolder()
b = next((f for f in root.GetSubFolderList() if f.GetName() == '动效_规则段'), None) or mp.AddSubFolder(root, '动效_规则段')
mp.SetCurrentFolder(b)
mi = mp.ImportMedia([str(MOV)]); wi = mp.ImportMedia([str(WAV)])
assert mi and wi, '导入失败'
for kind, want in (('video', 2), ('audio', 3)):
    while tl.GetTrackCount(kind) < want: assert tl.AddTrack(kind, 'stereo' if kind == 'audio' else None)
    busy = [x for x in (tl.GetItemListInTrack(kind, want) or []) if x.GetStart() < start + dur and x.GetEnd() > start]
    assert not busy, f'{kind}{want} 这段时间已有片段：{[x.GetName() for x in busy]}'
v = mp.AppendToTimeline([{'mediaPoolItem': mi[0], 'recordFrame': start, 'trackIndex': 2, 'mediaType': 1, 'startFrame': 0, 'endFrame': dur}])
a = mp.AppendToTimeline([{'mediaPoolItem': wi[0], 'recordFrame': start, 'trackIndex': 3, 'mediaType': 2, 'startFrame': 0, 'endFrame': dur}])
assert v and a, '上轨失败'
tl.SetTrackName('video', 2, '规则段动效'); tl.SetTrackName('audio', 3, '规则段音效')
mp.SetCurrentFolder(cur); tl.SetCurrentTimecode(head)
print('V2', [(x.GetName(), x.GetStart(), x.GetDuration()) for x in tl.GetItemListInTrack('video', 2)])
print('A3', [(x.GetName(), x.GetStart(), x.GetDuration()) for x in tl.GetItemListInTrack('audio', 3)])
print('保存', pm.SaveProject())
