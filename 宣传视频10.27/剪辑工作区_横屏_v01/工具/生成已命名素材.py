from pathlib import Path
import json,re,os,csv,math,html
R=Path(__file__).resolve().parents[2]; W=R/'剪辑工作区_横屏_v01'; A=W/'01_素材分析'; O=W/'07_素材命名'; D=R/'已命名素材'; D.mkdir(exist_ok=True)
vs=json.loads((A/'视频音频清单.json').read_text('utf-8-sig'))+json.loads((O/'新增视频清单.json').read_text('utf8'))
ps=json.loads((O/'照片命名清单.json').read_text('utf8'))
summary=(W/'逐个素材内容摘要.md').read_text('utf-8-sig')
vt=dict(re.findall(r'^## (V\d+) (.+)$',summary,re.M))
vt.update(dict(zip([f'V{i}' for i in range(33,52)],[
'红脚机器人遥控联调','巴掌机器人场地近景','手动检查巴掌与连接杆','红脚机器人桌面舵机检查','桌面遥控行走联调','巴掌机器人与手柄演示','机器人内部接线与遥控调试','代码终端与机器人联调','红蓝攻击模块桌面对照','红脚机器人桌面动作检查','拳头机器人场地近景','巴掌连接结构手动检查','三维模型比例调整录屏','巴掌机器人场地展示','巴掌模块手工装配','巴掌机器人与遥控器场地展示','机器人电脑旁联调','桌面遥控行走联调补充机位','拳头机器人与球靶场地近景'])))
pt=dict(zip([f'P{i:02}' for i in range(1,35)],[
'机器人身体与主板装配','球靶结构与装配说明图','红色拳头机构装配','拳头打印件与打印瑕疵','电机与减速机构桌面实物','紫色遥控器装配成品','团队与竞技场合影','机器人电脑旁代码调试','红蓝双机成品合照','主控板与机器人内部接线','机器人身体腿部接线','遥控器内部接线','竞技场与双机布置','红蓝球靶球壳打印件','球靶立柱与球壳零件','团队竞技场合影另一张','机器人身体与螺丝配件','团队自拍与竞技场','拳头模块打印零件摆放','课堂竞技场试玩交流','巴掌机与红脚机桌面对照','团队自拍另一张','AI概念图_红蓝双机对战','巴掌机器人场地俯视','磁吸球靶装配实物','参考图_Punchy拳头机构','AI概念图_红蓝双机擂台','AI概念图_双机产品外观','AI概念图_双人机器人对战场景','巴掌机器人结构模型方案','巴掌机器人结构模型方案另一版','遥控器打印零件','Otto身体与腿部打印零件','拳头机器人结构模型预览']))
def clean(s):return re.sub(r'[\\/:*?"<>|\r\n]','-',s).strip().strip('.')
def time_label(p,probe=None,exif=None):
 # Do not use filesystem copy time as capture time or assume the user's current timezone.
 m=re.search(r'DJI_(\d{8})(\d{6})',p.name)
 if m:
  a,b=m.groups();return f'{a[:4]}-{a[4:6]}-{a[6:]}_{b[:2]}-{b[2:4]}-{b[4:]}_相机文件时间','相机原文件名时间（未作时区转换）'
 if exif:
  t=exif.get('36867') or exif.get('36868') or exif.get('306')
  if t:return clean(t.replace(':','-',2).replace(' ','_').replace(':','-'))+'_EXIF时间','图片EXIF记录时间（不保证原始拍摄时间）'
 tags=(probe or {}).get('format',{}).get('tags',{})
 t=tags.get('creation_time')
 if not t:
  for s in (probe or {}).get('streams',[]):
   if s.get('tags',{}).get('creation_time'):t=s['tags']['creation_time'];break
 if t:
  return t[:19].replace('T','_').replace(':','-')+'_元数据UTC','媒体creation_time原值UTC（可能为导出时间，不保证拍摄时间）'
 m=re.search(r'(2026)[-_]?(\d{2})[-_]?(\d{2})[_-]?(\d{2})(\d{2})(\d{2})',p.name)
 if m:
  y,mo,d,h,mi,s=m.groups();return f'{y}-{mo}-{d}_{h}-{mi}-{s}_微信文件时间','微信文件名记录时间，非已核实拍摄时间'
 if '10月22日' in p.name:return '2026-10-22_10-03_文件标注时间','原文件名标注日期与时间'
 return '时间未核实','无可靠时间记录；未采用文件复制或修改时间'
rows=[]
for v in vs:
 p=Path(v['path']); stamp,source=time_label(p,v.get('probe')); n=round(v['duration']); duration=f'{n//60:02}分{n%60:02}秒'
 title=vt[v['id']]
 if v['id']=='V26': title='早期遥控联调_与V25完全重复'
 if v['id']=='V31': title='遥控器操作短镜头_压缩版'
 if v['id']=='V32': title='遥控器操作短镜头_原画版'
 rows.append({'编号':v['id'],'时间依据':source,'内容':title,'时长秒':round(v['duration'],3),'原路径':str(p),'新路径':str(D/clean(f'{stamp}__{title}__{duration}__{v["id"]}{p.suffix.lower()}'))})
for p in ps:
 path=Path(p['path']); stamp,source=time_label(path,exif=p.get('exif'))
 title=pt[p['id']]
 rows.append({'编号':p['id'],'时间依据':source,'内容':title,'时长秒':'','原路径':str(path),'新路径':str(D/clean(f'{stamp}__{title}__{p["id"]}{path.suffix.lower()}'))})
assert len({r['新路径'] for r in rows})==len(rows)
for r in rows:
 src=Path(r['原路径']); dst=Path(r['新路径']); assert src.is_file(),src
 if dst.exists():assert os.path.samefile(src,dst),dst
 else:os.link(src,dst)
 assert src.stat().st_size==dst.stat().st_size
 assert os.path.samefile(src,dst)
with (D/'素材命名对照表.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
(D/'素材命名对照表.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
(D/'先看这里.txt').write_text('已命名素材：共'+str(len(rows))+'份。\n\n命名包含时间信息、关键内容、视频时长、原有素材编号。\n相机文件时间、媒体元数据UTC、微信文件时间分别标注，均不能一概当作已核实拍摄时间。没有可靠记录的标注“时间未核实”。\n本目录为原素材的NTFS硬链接：文件不重新压缩，不额外复制大视频；原路径保留，现有达芬奇工程继续可用。可以正常播放和导入剪辑。请勿直接覆盖编辑媒体文件内容，因为两个名称指向同一份数据。删除一个文件名不会删除仍被另一名称引用的数据。\n原名与新名见素材命名对照表.csv。V26为已知重复文件，保留并明确标注；AI概念图与实拍分别命名。新增19段视频的内容依据抽帧画面，不声称已完整听审。\n',encoding='utf-8-sig')
parts=['<!doctype html><meta charset="utf-8"><title>已命名素材</title><style>body{font:16px system-ui;margin:30px;background:#f4f4f4}li{padding:9px}a{color:#2455a0}</style><h1>已命名素材</h1><p>时间未核实的素材已明确标注；原有工程路径保留。</p><ul>']
for r in sorted(rows,key=lambda x:Path(x['新路径']).name):parts.append('<li><a href="'+html.escape(Path(r['新路径']).name,quote=True)+'">'+html.escape(Path(r['新路径']).name)+'</a></li>')
parts.append('</ul>'); (D/'素材目录.html').write_text('\n'.join(parts),encoding='utf8')
print(json.dumps({'total':len(rows),'video_audio':len(vs),'images':len(ps),'unverified_times':sum('时间未核实' in r['新路径'] for r in rows),'verified_samefile':len(rows),'folder':str(D)},ensure_ascii=False))

