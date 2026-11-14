# 静音被盖住的「完整一场」原声，然后从达芬奇导出全片（字幕烧录）。渲染任务只加这一个，结束后从队列移除。
import pathlib, sys, time
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'out'; NAME = '棋甲对决_竖屏抖音_v05_全片_无字幕'
resolve = connect(require_enabled=False, timeout=120)
pm = resolve.GetProjectManager(); p = pm.GetCurrentProject(); tl = p.GetCurrentTimeline()
assert p.GetName() == '棋甲对决_竖屏抖音_v04_可编辑'
big = next(x for x in tl.GetItemListInTrack('audio', 1) if x.GetName() == '完整一场')
print('静音原声', big.SetClipEnabled(False), big.GetClipEnabled())
v2 = tl.GetItemListInTrack('video', 2)[0].GetMediaPoolItem()
print('替换规则段', v2.ReplaceClip(str(ROOT / '动效_规则段' / 'out' / '规则段_v7.mov')), v2.GetClipProperty('File Path')[-16:], tl.GetItemListInTrack('video', 2)[0].GetDuration())
print('字幕轨启用', tl.GetIsTrackEnabled('subtitle', 1))
print('保存', pm.SaveProject())
s, e = tl.GetStartFrame(), tl.GetEndFrame()
print('范围', s, e, (e - s) / 30)
print('格式', p.SetCurrentRenderFormatAndCodec('mp4', 'H264'))
ok = p.SetRenderSettings({'MarkIn': s, 'MarkOut': e - 1, 'TargetDir': str(OUT), 'CustomName': NAME, 'FormatWidth': 1080, 'FormatHeight': 1920, 'FrameRate': 30, 'ExportVideo': True, 'ExportAudio': True, 'ExportSubtitle': False})
print('设置', ok); assert ok, '导出设置失败'
job = p.AddRenderJob(); print('任务', job)
assert job
print('开始', p.StartRendering([job]))
t0 = time.time()
while p.IsRenderingInProgress():
    st = p.GetRenderJobStatus(job)
    print(f"{time.time()-t0:5.0f}s {st.get('JobStatus')} {st.get('CompletionPercentage')}%", flush=True)
    time.sleep(10)
print('结束', p.GetRenderJobStatus(job))
print('移除任务', p.DeleteRenderJob(job))
