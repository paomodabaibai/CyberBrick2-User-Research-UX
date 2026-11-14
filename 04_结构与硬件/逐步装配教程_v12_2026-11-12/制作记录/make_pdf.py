from pathlib import Path
import json,zipfile
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
P=Path(__file__).resolve().parent.parent
steps=json.loads((P/'制作记录/重点版数据.json').read_text(encoding='utf-8'))
try:pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/msyh.ttc'))
except Exception:
 from reportlab.pdfbase.cidfonts import UnicodeCIDFont
 pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));pdfmetrics.registerFontFamily('STSong-Light');
 CN='STSong-Light'
else:CN='CN'
W,H=595.28,841.89
pdf=P/'02_主板与攻击模块_逐页图解.pdf'; c=canvas.Canvas(str(pdf),pagesize=(W,H));c.setTitle('milk机器人：主板与攻击模块逐步装配');c.setAuthor('milk项目组')
checks=[]
def text(t,x,y,width=527,size=11,color='#203247',leading=None):
 leading=leading or size*1.6;c.setFont(CN,size);c.setFillColor(HexColor(color));line=''
 for ch in t:
  if ch=='\n' or pdfmetrics.stringWidth(line+ch,CN,size)>width:
   c.drawString(x,y,line);y-=leading;line='' if ch=='\n' else ch
  else:line+=ch
 if line:c.drawString(x,y,line);y-=leading
 return y

def footer(n):
 c.setStrokeColor(HexColor('#d8dee5'));c.line(34,32,W-34,32);text('v11送印件 · 2026-11-12 · 孔位按模型，实物需试装',34,19,450,8);text(str(n),W-50,19,25,8)
# Front page
text('milk 机器人',34,785,size=28);text('主板与攻击模块 · 逐步装配',34,740,size=23)
y=685
for line in ['这版只讲新主板安装和两种攻击模块；Otto腿脚按你熟悉的原版方式装。','装一台蓝机：M01–M05 → B01–B10 → Z01。','装一台红机：M01–M05 → R01–R10 → Z01。','每一步包含所需五金、真实模型孔位图、操作顺序和完成检查。','先准备身体顶部4颗、背面2颗热熔铜螺母。蓝机承重座另2颗见B01。孔位在最后两页。','铜螺母规格：M3内牙、长5.7mm、适配Ø4.0mm底孔。裸打印件上热装、冷却后再装电子件。','主板：2.5×8塑料自攻×4。开关：2.5×6塑料自攻×1。舵盘、输出轴均用匹配原配螺丝，不全部是M3。','黄色框是本步五金；红色箭头指向安装孔/操作点。拳头图中的金/绿/蓝色用于区分曲柄、连杆、滑架，实物打印可以都是红色。','来源：v11送印装配清单、修正C02托架、v10/v11几何孔位与原五金表。没有改模型或驱动机器人。新到舵机花键、紧固件实际配合需现场确认。']:
 y=text(line,34,y,size=12);y-=17
footer(1);c.showPage()
for n,s in enumerate(steps,2):
 c.bookmarkPage(s['code']);c.addOutlineEntry(s['code']+' '+s['title'],s['code'],0)
 accent='#2279b7' if s['code'][0]=='B' else '#bf444d' if s['code'][0]=='R' else '#263f57'
 y=text(s['code']+'  '+s['title'],34,803,size=18,color=accent,leading=25)
 y-=3;top=y
 # Hardware box sized to wrapped text.
 lines=[];line='';tt='本步准备：'+s['hardware']
 for ch in tt:
  if pdfmetrics.stringWidth(line+ch,CN,10.5)>507:lines.append(line);line=ch
  else:line+=ch
 lines.append(line);height=14.5*len(lines)+18
 c.setFillColor(HexColor('#fff1d4'));c.roundRect(34,y-height+10,527,height,4,fill=1,stroke=0)
 y=text(tt,44,y-3,507,10.5,leading=14.5)-12
 ih=527*1100/1600;c.drawImage(str(P/s['image']),34,y-ih,width=527,height=ih);y-=ih+21
 for i,a in enumerate(s['actions'],1):y=text(str(i)+'. '+a,34,y,size=10.5,leading=16)-6
 y-=2;y=text('装完检查：'+s['check'],34,y,size=10.5,color='#28744f',leading=16)-7
 if s['extra']:y=text('注意：'+s['extra'],34,y,size=9.5,color='#806139',leading=14)
 checks.append({'code':s['code'],'bottom_y':round(y,1)});assert y>40,(s['code'],y)
 footer(n);c.showPage()
for n,code in enumerate(['A01','A02'],len(steps)+2):
 text('准备补图：身体铜螺母位置',34,800,size=20);im=P/'图解'/f'{code}.png';ih=527*1100/1600;c.drawImage(str(im),34,375,width=527,height=ih)
 text('顶部4颗＋背面2颗，必须在裸身体上热装。已经安装好可以跳过。',34,335,size=12)
 text('规格不是只看M3：须为长5.7mm且适配Ø4.0安装底孔的型号，先试一孔。',34,285,size=12)
 footer(n);c.showPage()
c.save()
(P/'制作记录/PDF版面检查.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
readme='主板与攻击模块逐步装配\n\n电脑：打开00_逐步装配图解.html，先选主板，再选蓝色巴掌或红色拳头。\n手机/发给组员：打开02_主板与攻击模块_逐页图解.pdf。\n每台路线：主板5步＋对应攻击模块10步＋最终检查1步。\n图解里A01/A02是新版身体热熔铜螺母位置补图，不是Otto腿部教程。\n本包没有模型修改、不包含上传程序；孔位数字与螺丝方向见每页。\n'
(P/'先读我.txt').write_text(readme,encoding='utf-8-sig')
files=[P/'00_逐步装配图解.html',P/'01_逐步装配文字版.md',pdf,P/'五金总表_沿用v11.md',P/'先读我.txt']+[P/s['image'] for s in steps]+[P/'图解/A01.png',P/'图解/A02.png']
zpath=P/'主板与攻击模块_图文教程_发组员.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,f.relative_to(P).as_posix())
with zipfile.ZipFile(zpath) as z:assert z.testzip() is None
print('PDF',pdf,'PAGES',len(steps)+3,'ZIP_MB',round(zpath.stat().st_size/1048576,2),'MIN_BOTTOM',min(x['bottom_y'] for x in checks))
