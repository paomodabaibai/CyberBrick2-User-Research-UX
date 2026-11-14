from pathlib import Path
import json,subprocess,xml.etree.ElementTree as ET,concurrent.futures
W=Path(__file__).resolve().parents[1]
shots=json.loads((W/'03_剪辑方案/横屏60秒_剪辑清单.json').read_text(encoding='utf8'))
videos=json.loads((W/'01_素材分析/视频音频清单.json').read_text(encoding='utf8'))
NATIVE=W/'04_达芬奇工程'
def lua(v):
 if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
 if isinstance(v,bool):return 'true' if v else 'false'
 if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
 if isinstance(v,dict):return '{'+','.join('['+lua(k)+']='+lua(x) for k,x in v.items())+'}'
 return str(v)
script='''-- Run inside Resolve, not in an external Python session.
local logPath = "C:/Users/Administrator/AppData/Local/Temp/milk_resolve_import_status.txt"
local log = assert(io.open(logPath,"w"))
local function note(s) log:write(tostring(s).."\\n");log:flush();print(s) end
local function main()
 local r = Resolve()
 assert(r,"Resolve internal object unavailable")
 local pm = r:GetProjectManager()
 local p = pm:GetCurrentProject()
 assert(p,"Open a project first")
 note("PROJECT="..p:GetName())
 if p:GetTimelineCount()==0 then
  p:SetSetting("timelineFrameRate","30")
  p:SetSetting("timelineResolutionWidth","1920")
  p:SetSetting("timelineResolutionHeight","1080")
 end
 local mp=p:GetMediaPool()
 local root=mp:GetRootFolder()
 local bin=assert(mp:AddSubFolder(root,"milk 10.27 editable draft "..os.date("%H%M%S")))
 local originals=assert(mp:AddSubFolder(bin,"01 Originals - preserve source"))
 local cuts=assert(mp:AddSubFolder(bin,"02 Selected clips with handles"))
 local graphics=assert(mp:AddSubFolder(bin,"03 Editable text sources"))
 mp:SetCurrentFolder(originals)
 local original_count=0
 for _,path in ipairs(rawPaths) do
  local imported=mp:ImportMedia({path})
  if imported and #imported>0 then original_count=original_count+#imported end
 end
 note("ORIGINALS_IMPORTED="..original_count)
 mp:SetCurrentFolder(cuts)
 local media={}
 for i,s in ipairs(shots) do
  local imported=mp:ImportMedia({s.media_path})
  assert(imported and imported[1],"Media import failed: "..s.media_path)
  media[i]=imported[1]
 end
 local tl=assert(mp:CreateEmptyTimeline("Landscape selects - structure reference 60s "..os.date("%H%M%S")))
 p:SetCurrentTimeline(tl)
 tl:SetStartTimecode("00:00:00:00")
 tl:SetSetting("timelineResolutionWidth","1920")
 tl:SetSetting("timelineResolutionHeight","1080")
 while tl:GetTrackCount("video")<2 do tl:AddTrack("video") end
 if tl:GetTrackCount("audio")==0 then tl:AddTrack("audio","stereo") end
 tl:SetTrackName("video",1,"01 Picture - independently editable")
 tl:SetTrackName("video",2,"02 Titles - editable Fusion Text+")
 tl:SetTrackName("audio",1,"01 Location sound")
 mp:SetCurrentFolder(graphics)
 local blank=mp:ImportMedia({blankPath})
 assert(blank and blank[1],"Transparent title source import failed")
 local base=tl:GetStartFrame()
 local text_count=0
 for i,s in ipairs(shots) do
  local rec=base+math.floor(s.record_in*30+0.5)
  local finish=s.media_in_frames+s.frames-1
  local v=mp:AppendToTimeline({{mediaPoolItem=media[i],startFrame=s.media_in_frames,endFrame=finish,mediaType=1,trackIndex=1,recordFrame=rec}})
  assert(v and v[1],"Picture append failed at "..i)
  v[1]:SetName(string.format("%02d %s | %s",i,s.source_id,s.title))
  local a=mp:AppendToTimeline({{mediaPoolItem=media[i],startFrame=s.media_in_frames,endFrame=finish,mediaType=2,trackIndex=1,recordFrame=rec}})
  if a and a[1] then pcall(function() a[1]:SetProperty("AudioVolume",-16) end) end
  tl:AddMarker(math.floor(s.record_in*30+0.5),"Blue",s.title,s.source_id.." original in "..s.source_in.." seconds; duration provisional",s.frames)
  local title=mp:AppendToTimeline({{mediaPoolItem=blank[1],startFrame=0,endFrame=s.frames-1,mediaType=1,trackIndex=2,recordFrame=rec}})
  assert(title and title[1],"Title append failed")
  title[1]:SetName("TITLE "..s.title)
  local comp=title[1]:AddFusionComp()
  if comp then
   comp:Lock()
   local big=comp:AddTool("TextPlus")
   local small=comp:AddTool("TextPlus")
   local merge=comp:AddTool("Merge")
   local output=comp:FindTool("MediaOut1")
   if not output then output=comp:AddTool("MediaOut") end
   big:SetInput("StyledText",s.title)
   big:SetInput("Font","Microsoft YaHei")
   big:SetInput("Style","Bold")
   big:SetInput("Size",0.055)
   small:SetInput("StyledText",s.subtitle)
   small:SetInput("Font","Microsoft YaHei")
   small:SetInput("Size",0.030)
   if s.portrait then
    big:SetInput("Center",{0.73,0.58})
    small:SetInput("Center",{0.73,0.46})
   else
    big:SetInput("Center",{0.50,0.15})
    small:SetInput("Center",{0.50,0.075})
   end
   merge:ConnectInput("Background",small)
   merge:ConnectInput("Foreground",big)
   output:ConnectInput("Input",merge)
   comp:Unlock()
   text_count=text_count+1
  end
 end
 pm:SaveProject()
 r:OpenPage("edit")
 tl:SetCurrentTimecode("00:00:00:00")
 local stamp=os.date("%Y%m%d_%H%M%S")
 local drp=exportDir.."/milk_landscape_selects_"..stamp..".drp"
 local export_ok=pm:ExportProject(p:GetName(),drp)
 pcall(function() tl:Export(exportDir.."/milk_landscape_selects_"..stamp..".drt",r.EXPORT_DRT) end)
 note("TIMELINE="..tl:GetName())
 note("PICTURE_ITEMS="..#tl:GetItemListInTrack("video",1))
 note("TITLE_ITEMS="..#tl:GetItemListInTrack("video",2))
 note("AUDIO_ITEMS="..#tl:GetItemListInTrack("audio",1))
 note("FUSION_TITLES="..text_count)
 note("DURATION_FRAMES="..(tl:GetEndFrame()-tl:GetStartFrame()))
 note("PROJECT_EXPORT="..tostring(export_ok).." "..drp)
 note("SUCCESS")
end
local ok,err=pcall(main)
if not ok then note("ERROR="..tostring(err)) end
log:close()
'''
script='local shots='+lua(shots)+'\nlocal rawPaths='+lua([r['path'].replace('\\','/') for r in videos if not r.get('duplicate_of')])+'\nlocal blankPath='+lua(str(W/'05_音频与兼容素材/透明文字底.mov').replace('\\','/'))+'\nlocal exportDir='+lua(str(NATIVE).replace('\\','/'))+'\n'+script
(NATIVE/'milk_ARENA_20261027_v01.lua').write_text(script,encoding='utf8')
menu=Path.home()/'AppData/Roaming/Blackmagic Design/DaVinci Resolve/Support/Fusion/Scripts/Utility'
menu.mkdir(parents=True,exist_ok=True)
(menu/'milk_ARENA_20261027_v01.lua').write_text(script,encoding='utf8')

# Final Cut 7 XML fallback: split picture and sound, not a flattened movie.
root=ET.Element('xmeml',version='5');seq=ET.SubElement(root,'sequence',id='sequence-1')
def e(parent,name,value=None,**kw):
 n=ET.SubElement(parent,name,**kw)
 if value is not None:n.text=str(value)
 return n
e(seq,'name','棋甲对决 横屏素材精选 结构参考60秒');e(seq,'duration',1800)
def rate(p):r=e(p,'rate');e(r,'timebase',30);e(r,'ntsc','FALSE')
rate(seq);media=e(seq,'media');video=e(media,'video');form=e(video,'format');sc=e(form,'samplecharacteristics');rate(sc);e(sc,'width',1920);e(sc,'height',1080);e(sc,'anamorphic','FALSE');e(sc,'pixelaspectratio','square');e(sc,'fielddominance','none')
vt=e(video,'track');audio=e(media,'audio');e(audio,'numOutputChannels',2);at=e(audio,'track')
for s in shots:
 for kind,track in [('video',vt),('audio',at)]:
  clip=e(track,'clipitem',id=f"{kind}-{s['index']}");e(clip,'name',f"{s['index']:02d} {s['source_id']} {s['title']}");rate(clip)
  e(clip,'start',round(s['record_in']*30));e(clip,'end',round((s['record_in']+s['duration'])*30));e(clip,'in',s['media_in_frames']);e(clip,'out',s['media_in_frames']+s['frames']);e(clip,'enabled','TRUE')
  f=e(clip,'file',id=f"{kind}-file-{s['index']}");e(f,'name',Path(s['media_path']).name);e(f,'pathurl',Path(s['media_path']).as_uri());rate(f);e(f,'duration',round(s['media_duration']*30))
  fm=e(f,'media');vv=e(fm,'video');ss=e(vv,'samplecharacteristics');rate(ss);e(ss,'width',1920);e(ss,'height',1080);aa=e(fm,'audio');e(aa,'channelcount',2)
  so=e(clip,'sourcetrack');e(so,'mediatype',kind);e(so,'trackindex',1)
ET.indent(root);ET.ElementTree(root).write(NATIVE/'横屏素材精选_可导入达芬奇.xml',encoding='utf-8',xml_declaration=True)
def tc(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(NATIVE/'横屏标题_可编辑.srt').write_text('\n\n'.join(f"{i}\n{tc(s['record_in'])} --> {tc(s['record_in']+s['duration'])}\n{s['title']}\n{s['subtitle']}" for i,s in enumerate(shots,1)),encoding='utf-8')

def preview(s):
 out=W/'06_预览'/f"S{s['index']:02d}.mp4"
 if out.exists():return
 cmd=['ffmpeg','-hide_banner','-v','error','-ss',str(s['media_in_frames']/30),'-i',s['media_path'],'-loop','1','-i',str(W/'05_音频与兼容素材'/f"S{s['index']:02d}_文字参考.png"),'-filter_complex','[0:v][1:v]overlay=0:0:shortest=1,format=yuv420p[v]','-map','[v]','-map','0:a:0','-af','volume=-16dB,afade=t=in:d=0.1,afade=t=out:st='+str(s['duration']-.12)+':d=0.12','-t',str(s['duration']),'-c:v','libx264','-preset','fast','-crf','21','-c:a','aac','-b:a','128k','-threads','3','-y',str(out)]
 res=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if res.returncode:raise RuntimeError(res.stderr.decode('utf8','replace'))
 print('PREVIEW',s['index'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:list(p.map(preview,shots))
concat=W/'06_预览/concat.txt';concat.write_text('\n'.join("file '"+f"S{s['index']:02d}.mp4"+"'" for s in shots),encoding='utf8')
subprocess.run(['ffmpeg','-v','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart','-y',str(W/'06_预览/横屏结构参考_60秒_非定稿.mp4')],check=True)
print('EDITABLE_SCRIPT_READY',menu/'milk_ARENA_20261027_v01.lua',flush=True)
