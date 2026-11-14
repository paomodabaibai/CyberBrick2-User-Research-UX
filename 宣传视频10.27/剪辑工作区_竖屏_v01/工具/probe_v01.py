# 尝试把时间线改为裁切填满，并逐镜导出中点静帧检查旋转/构图
import sys, os
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect
OUT = sys.argv[1]
resolve = connect(require_enabled=False, timeout=30)
proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline()
print(proj.GetName(), tl.GetName())
print('custom', tl.SetSetting('useCustomSettings', '1'))
print('mismatch', tl.SetSetting('timelineInputResMismatchBehavior', 'scaleFullFrameWithCrop'), tl.GetSetting('timelineInputResMismatchBehavior'))
print('pb', proj.SetSetting('timelinePlaybackFrameRate', '30'), proj.GetSetting('timelinePlaybackFrameRate'))
resolve.OpenPage('edit')
fps = 30
items = tl.GetItemListInTrack('video', 1)
for i, it in enumerate(items):
    mid = (it.GetStart() + it.GetEnd()) // 2 - tl.GetStartFrame()
    f = mid
    tc = '%02d:%02d:%02d:%02d' % (1 + f // (3600*fps), (f // (60*fps)) % 60, (f // fps) % 60, f % fps)
    tl.SetCurrentTimecode(tc)
    p = os.path.join(OUT, '%02d_%s.png' % (i, it.GetName()[-7:-4]))
    print(i, it.GetName()[-12:], tc, proj.ExportCurrentFrameAsStill(p))
