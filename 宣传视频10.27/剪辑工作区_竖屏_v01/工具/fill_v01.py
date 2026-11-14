# 横拍/照片在竖屏里填满：16:9 缩放3.16，4:3 缩放2.37；P07团队合影保留更多人物
import sys
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect
FIX = {'V04': (3.16, 60), 'V01': (2.2, 0), 'P09': (2.37, 0), 'P07': (1.25, 0)}
resolve = connect(require_enabled=False, timeout=30)
proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline()
for it in tl.GetItemListInTrack('video', 1):
    key = it.GetName().rsplit('__', 1)[-1].split('.')[0]
    if key in FIX:
        z, pan = FIX[key]
        print(key, it.SetProperty('ZoomX', z), it.SetProperty('ZoomY', z), it.SetProperty('Pan', pan), it.GetProperty('ZoomX'), it.GetProperty('Pan'))
print(resolve.GetProjectManager().SaveProject())
