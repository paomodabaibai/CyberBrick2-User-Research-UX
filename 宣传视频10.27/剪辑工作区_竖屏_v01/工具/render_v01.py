# 导出竖屏初剪预览 MP4 + DRT + DRP
import sys, time, os
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect
W = r'E:\课程作业\大三上\张茫 用户研究与体验设计\宣传视频10.27\剪辑工作区_竖屏_v01'
resolve = connect(require_enabled=False, timeout=60)
pm = resolve.GetProjectManager()
proj = pm.GetCurrentProject()
tl = proj.GetCurrentTimeline()
resolve.OpenPage('deliver')
print('fmt', proj.SetCurrentRenderFormatAndCodec('mp4', 'H264'))
print('set', proj.SetRenderSettings({'SelectAllFrames': True, 'TargetDir': os.path.join(W, '06_预览'),
      'CustomName': '棋甲对决_竖屏抖音_初剪v01', 'FormatWidth': 1080, 'FormatHeight': 1920, 'FrameRate': 30.0,
      'ExportVideo': True, 'ExportAudio': True}))
job = proj.AddRenderJob()
print('job', job, proj.StartRendering([job]))
while proj.IsRenderingInProgress():
    time.sleep(2)
print(proj.GetRenderJobStatus(job))
print('drt', tl.Export(os.path.join(W, '04_达芬奇工程', '棋甲对决_竖屏抖音_初剪v01.drt'), resolve.EXPORT_DRT))
pm.SaveProject()
print('drp', pm.ExportProject(proj.GetName(), os.path.join(W, '04_达芬奇工程', '棋甲对决_竖屏抖音_v01.drp')))
resolve.OpenPage('edit')
