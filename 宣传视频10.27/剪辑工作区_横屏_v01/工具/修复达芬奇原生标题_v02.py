from pathlib import Path
import sys,json,time
sys.path.insert(0,r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect
W=Path(__file__).resolve().parents[1]
shots=json.loads((W/'03_剪辑方案/横屏60秒_剪辑清单.json').read_text('utf8'))
r=connect(require_enabled=False,timeout=30);pm=r.GetProjectManager();p=pm.GetCurrentProject();t=p.GetCurrentTimeline()
assert t.GetName()=='棋甲对决 横屏 v02 标题修复',t.GetName()
items=t.GetItemListInTrack('video',2);assert len(items)==len(shots)
for i,(item,s) in enumerate(zip(items,shots)):
 c=item.GetFusionCompByIndex(1) if item.GetFusionCompCount() else item.AddFusionComp(); assert c
 tools=list(c.GetToolList(False).values());mi=c.FindTool('MediaIn1');mo=c.FindTool('MediaOut1')
 texts=[x for x in tools if x.GetAttrs()['TOOLS_RegID']=='TextPlus']
 big=texts[0] if texts else c.AddTool('TextPlus');small=texts[1] if len(texts)>1 else c.AddTool('TextPlus')
 if s['portrait']:x=.73; y1=.58;y2=.46
 else:x=.5;y1=.15;y2=.075
 for tool,text,size,y in [(big,s['title'],.048,y1),(small,s['subtitle'],.026,y2)]:
  for key,value in [('StyledText',text),('Font','Microsoft YaHei'),('Style','Bold'),('Size',size),('Center',[x,y,0]),('Red1',1),('Green1',1),('Blue1',1),('Alpha1',1)]:tool.SetInput(key,value)
 # Keep MediaIn connected to the rendered graph; do not hold a composition lock across value writes.
 bg=mi
 if not s['portrait']:
  shade=c.AddTool('Background');mask=c.AddTool('RectangleMask');m0=c.AddTool('Merge')
  for key,value in [('UseFrameFormatSettings',1),('Width',1920),('Height',1080),('TopLeftRed',.025),('TopLeftGreen',.035),('TopLeftBlue',.055),('TopLeftAlpha',.60)]:shade.SetInput(key,value)
  mask.SetInput('Width',1);mask.SetInput('Height',.23);mask.SetInput('Center',[.5,.115,0]);shade.ConnectInput('EffectMask',mask)
  m0.ConnectInput('Background',mi);m0.ConnectInput('Foreground',shade);bg=m0
 m1=c.AddTool('Merge');m2=c.AddTool('Merge')
 for m in [m1,m2]:m.SetInput('UseFrameFormatSettings',1);m.SetInput('Width',1920);m.SetInput('Height',1080)
 assert m1.ConnectInput('Background',bg);assert m1.ConnectInput('Foreground',big);assert m2.ConnectInput('Background',m1);assert m2.ConnectInput('Foreground',small);assert mo.ConnectInput('Input',m2)
 print('TITLE_FIXED',i+1,s['title'],flush=True)
t.SetTrackName('video',1,'实拍画面与产品照片');t.SetTrackName('video',2,'可编辑中文标题');t.SetTrackName('audio',1,'现场原声')
print('SAVE',pm.SaveProject());r.OpenPage('edit')
for sec,label in [(1,'片头'),(16,'竖屏排版'),(27,'击球'),(52,'团队'),(57,'片尾')]:
 t.SetCurrentTimecode(f'00:00:{sec:02}:00');time.sleep(.3);print('STILL',label,p.ExportCurrentFrameAsStill(str(W/'06_预览'/f'Resolve_v02_{label}.png')),flush=True)
t.SetCurrentTimecode('00:00:00:00');pm.SaveProject()
print('EXPORT_DRP',pm.ExportProject(p.GetName(),str(W/'04_达芬奇工程/milk_横屏_v02_标题已修复.drp')))
print('EXPORT_DRT',t.Export(str(W/'04_达芬奇工程/milk_横屏_v02_标题已修复.drt'),0))
print('FORMATS',p.GetRenderFormats());print('MP4_CODECS',p.GetRenderCodecs('mp4'))
