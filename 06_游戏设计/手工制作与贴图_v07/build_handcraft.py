"""Hand-built arena guide + true-size A4/A3 artwork. All layout units mm.
Run with Codex bundled Python (reportlab,pypdf). No 3D print required.
"""
from pathlib import Path
import json,math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from pypdf import PdfReader,PdfWriter,PageObject,Transformation

HERE=Path(__file__).resolve().parent;OUT=HERE/'output'/'pdf';OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('yh',r'C:\Windows\Fonts\msyh.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('yhb',r'C:\Windows\Fonts\msyhbd.ttc',subfontIndex=0))
INK='#173c47';MUTED='#5e727a';PALE='#edf3f2';LINE='#cad8db';BLUE='#2379cf';RED='#d74f48';YELLOW='#f0be50'
C=None;PW=210;PH=297
def text(x,y,s,size=9,color=INK,bold=False,align='left'):
 C.setFillColor(HexColor(color));C.setFont('yhb' if bold else 'yh',size)
 getattr(C,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(x*mm,y*mm,str(s))
def line(x,y,a,b,color=LINE,w=.6,dash=None):
 C.setStrokeColor(HexColor(color));C.setLineWidth(w);C.setDash(dash or []);C.line(x*mm,y*mm,a*mm,b*mm);C.setDash([])
def rect(x,y,w,h,fill=None,stroke=LINE,sw=.6):
 C.setStrokeColor(HexColor(stroke));C.setFillColor(HexColor(fill or '#ffffff'));C.setLineWidth(sw);C.rect(x*mm,y*mm,w*mm,h*mm,fill=bool(fill),stroke=1)
def circle(x,y,r,fill=None,stroke=LINE,sw=1):
 C.setFillColor(HexColor(fill or '#ffffff'));C.setStrokeColor(HexColor(stroke));C.setLineWidth(sw);C.circle(x*mm,y*mm,r*mm,fill=bool(fill),stroke=1)
def poly(pts,fill,stroke=None):
 p=C.beginPath();p.moveTo(pts[0][0]*mm,pts[0][1]*mm)
 for a,b in pts[1:]:p.lineTo(a*mm,b*mm)
 p.close();C.setFillColor(HexColor(fill));C.setStrokeColor(HexColor(stroke or fill));C.drawPath(p,fill=1,stroke=bool(stroke))
def arrow(x,y,a,b,color=INK):
 line(x,y,a,b,color,1.4);ang=math.atan2(b-y,a-x);r=3
 poly([(a,b),(a-r*math.cos(ang-.4),b-r*math.sin(ang-.4)),(a-r*math.cos(ang+.4),b-r*math.sin(ang+.4))],color)
def dim(x,y,a,b,label,off=0,size=8):
 dx,dy=a-x,b-y;l=math.hypot(dx,dy);nx,ny=-dy/l,dx/l
 x1,y1=x+off*nx,y+off*ny;x2,y2=a+off*nx,b+off*ny
 line(x,y,x1+nx*2,y1+ny*2);line(a,b,x2+nx*2,y2+ny*2);line(x1,y1,x2,y2,MUTED,.6)
 for xx,yy in [(x1,y1),(x2,y2)]:line(xx-1,yy-1,xx+1,yy+1,MUTED,.7)
 C.saveState();C.translate((x1+x2)/2*mm,(y1+y2)/2*mm);C.rotate(math.degrees(math.atan2(dy,dx)));text(0,2,label,size,MUTED,align='center');C.restoreState()
def title(n,h,sub):
 text(14,282,'CYBERBRICK / 手工制作 V07 / 2026.10.17',8,MUTED,True)
 text(14,268,h,19,INK,True);text(14,258,sub,8.6,MUTED)
 line(14,15,196,15);text(14,9,'单位 mm；人工装配初样，机器人适配与触发力待试打。',7,MUTED);text(196,9,f'{n}/7',8,MUTED,align='right')
def lines(x,y,arr,size=9,step=6,color=MUTED):
 for s in arr:text(x,y,s,size,color);y-=step
 return y
def section(x,y,head,arr,size=9):
 text(x,y,head,12,INK,True);return lines(x,y-8,arr,size)-6
def table(y,headers,rows,widths,x=14,rowh=12,sz=8):
 xx=x
 for head,w in zip(headers,widths):text(xx+2,y,head,sz,INK,True);xx+=w
 line(x,y-4,x+sum(widths),y-4,INK,.8);y-=rowh
 for i,row in enumerate(rows):
  if i%2==0:rect(x,y-3,sum(widths),rowh,PALE,PALE)
  xx=x
  for cell,w in zip(row,widths):text(xx+2,y,str(cell),sz);xx+=w
  y-=rowh
 return y

wall_modules=[('LH1',180,60),('LH2',180,80),('LH3',180,100),('LH4',180,80),('LS',120,80),('RH1',180,60),('RH2',180,80),('RH3',180,100),('RH4',180,80),('RS',120,80)]
cuts=[('F','底板',420,630,6),('W60','高60竖片',180,55,2),('W80','高80竖片',180,75,4),('W100','高100竖片',180,95,2),('WS','支墙竖片',120,75,2),('B180','横墙底脚',180,40,8),('B120','支墙底脚',120,40,2),('TBASE','靶座',160,120,2)]

# Guide, A4 portrait.
C=canvas.Canvas(str(OUT/'01_材料尺寸与手搓说明_A4.pdf'),pagesize=(210*mm,297*mm))
C.setTitle('1260手工竞技场：材料、裁切、装配与打印说明')
title(1,'采购清单 · 不用 3D 打印','1260 × 1260 场地已确认能放下；6块底板，墙可拆换，目标保留明显掉落状态。')
table(243,['买什么','推荐规格与总量','用途'],[
 ('PVC发泡雪弗板','1220 × 2440 × 5，1张','底板＋主墙＋靶座'),
 ('外围实木条','截面20 × 30；1.2 m × 5根','10段护沿'),
 ('靶架实木条','截面20 × 20；1 m × 1根','两套立柱和挑臂'),
 ('轻质泡棉/海绵球','同款 Ø70，红蓝各1','命中球'),
 ('小磁铁','Ø8 × 2，4枚（含2备用）','固定于挑臂端'),
 ('普通钢垫圈','外径12～16 / 孔3～4，2枚','球顶磁吸面'),
 ('棉织带 / 光滑绳','织带宽10共1.5 m；绳约Ø1共1 m','球兜 / 下落限位'),
 ('L形小角码','40 × 40约15宽 ×4；20 ×20 ×4','柱脚 / 臂柱固定'),
 ('小木螺钉','3 × 10，约24枚','木架角码'),
 ('止挡珠或垫片','外径≥10，2个；孔适配细绳','绳止挡'),
 ('硬PET片或硬卡纸','20 × 20约1厚，2片','布带顶部承片'),
 ('薄双面胶 / 布基胶带','高粘双面胶约10 m；布基胶带约10 m','靶座固定和加固'),
 ('板材结构胶','PVC发泡板兼容胶，1支/瓶','竖片、底脚、加强片'),
 ('透明胶带 / 薄纸边料','薄透明封箱胶带1卷；留打印边料','背面拼缝 / 磁点'),
 ('贴图纸','哑面背胶纸；页数见第7页','墙面、标识'),
 ],[39,100,43],rowh=10.1,sz=7.7)
section(14,83,'带去买料时这样说',[
 '“一张5毫米PVC发泡雪弗板，请按第2页代切；不是纸面KT板。”',
 '厚5 mm的长边和木条优先让店家切，现场只粘合、贴图和装靶。',
 '墙面适合用哑面背胶；地面不必满铺纸，以免多出翘边与摩擦差异。',
 '工具：钢尺、铅笔、剪刀、美工刀/垫板、砂纸、小钻、螺丝刀。',
 '钻头：木螺钉预孔约1.5～2；绳导孔3～4。柱现场裁短需小手锯和夹具。',
 '最省事：先量球高和磁点厚度，再请商家直接裁最终柱长。'],8.7)
text(14,29,'采购量为整套A+B共用一套；不需要把两种布局各做一套。',9,INK,True)
C.showPage()

title(2,'给店家的裁切单','全部雪弗板切件厚5；只需28片矩形，另可加20片小三角加强片。')
table(242,['编号 / 部件','长 × 宽','数量','拼好后的作用'],[(f'{id} {name}',f'{w} × {h}',n,'见第3页' if id.startswith('W') else ('3列 × 2行' if id=='F' else '')) for id,name,w,h,n in cuts],[67,43,19,53],rowh=13,sz=9)
section(14,113,'可选加强片',[
 '直角三角形两直角边15 × 30，20片（每面墙2片）。',
 '可先裁15 × 30矩形10片，再沿对角切。切缝误差不影响加强用途。',
 '边长15横贴底脚，30竖贴墙；竖片放40宽底脚正中，两边各17.5。'],8.8)
table(76,['木条截面','成品长度与数量','采购 / 排料'],[
 ('20 × 30护沿','420 × 6；610 × 4','5根1.2 m或7根1 m'),
 ('20 × 20靶架','200 × 2；220毛坯 × 2','1根1 m够，柱现场裁短')],[40,69,73],rowh=13,sz=8.7)
lines(14,34,['护沿30朝上、20占地；四根1.2 m各裁610＋420，第五根裁420＋420。',
 '不要买6根1 m：虽然总长够，但排不下所需定长件。板厚有偏差时按实厚调整竖片高。'],8.1,5)
C.showPage()

title(3,'墙体做法与整板排料','保留原地图40宽主墙占地；实体结构改为“T形竖片＋底脚”，不粘空心盒。')
# T wall axonometric x,y,z in model, projection with scale .4.
def p3(x,y,z):return 38+.44*x+.22*y,185+.13*x-.13*y+.44*z
def bx(x,y,z,a,b,h,col):
 pts=[[(x,y,z),(x+a,y,z),(x+a,y,z+h),(x,y,z+h)],[(x+a,y,z),(x+a,y+b,z),(x+a,y+b,z+h),(x+a,y,z+h)],[(x,y,z+h),(x+a,y,z+h),(x+a,y+b,z+h),(x,y+b,z+h)]]
 for i,ps in enumerate(pts):poly([p3(*q) for q in ps],[col,'#607f89','#b4cbd0'][i],INK)
bx(0,0,0,180,40,5,'#7c9ba3');bx(0,17.5,5,180,5,75,'#d6e4e5')
poly([p3(35,2.5,5),p3(35,17.5,5),p3(35,17.5,35)],'#91abb0',INK)
dim(*p3(0,0,0),*p3(180,0,0),'180',-10)
text(134,231,'示例：总高80',10,INK,True)
lines(134,221,['竖片180 × 75 × 5','底脚180 × 40 × 5','75 + 5 = 80','两侧各17.5宽','三角加强不超脚座'],8.5,7)
lines(14,161,['先贴墙面，剪开加强片胶位露出板材；结构胶按店家推荐，先用余料试粘。',
 '竖片与底脚用板材胶粘牢；每面一片加强三角。脚座用薄双面胶固定。',
 '40宽脚座属于障碍，通道净宽量到脚座边。护沿木条也用胶固定，不能只靠自重。'],8.6,6)
# One-board schematic with 3mm kerf
sx,sy,sc=15,26,.044
rect(sx,sy,1220*sc,2440*sc,'#f5f7f6')
for colx in [0,423]:
 for j in range(3):rect(sx+colx*sc,sy+j*633*sc,420*sc,630*sc,'#dce9e9');text(sx+(colx+210)*sc,sy+(j*633+300)*sc,'420×630',6.8,align='center')
rect(sx+846*sc,sy,374*sc,768*sc,'#e7cf97');text(sx+1033*sc,sy+385*sc,'小件',8,align='center')
text(85,127,'一张整板够用，另有大量余料',11,INK,True)
lines(85,117,['1220宽先切：420 + 3刀缝 + 420',
 '+ 3刀缝 + 374余条。',
 '两根420宽条各裁3段630，得6底板。',
 '小件都能放进374余条前约770长度。',
 '本排料按3 mm锯缝估算；店家依刀具调整。',
 '成品总面积约1.824 m²，占整板约61%。',
 '有余料不等于可以少买底板：请按完整裁切单。',
 '地板背面用≤0.1厚透明胶跨缝，不叠厚胶。',
 '拼缝建议≤0.5，高差≤0.2，均需手工检查。',
 '底板必须由桌面全幅承托，不能悬空跨缝承重。'],8.5,8)
C.showPage()

def drawmap(x0,y0,scale,variant):
 def p(x,y):return x0+x*scale,y0+y*scale
 rect(x0,y0,1260*scale,1260*scale,'#f5f8f7')
 for x in (420,840):line(*p(x,0),*p(x,1260),LINE,.6)
 line(*p(0,630),*p(1260,630),LINE,.6)
 for j in range(2):
  for i in range(3):text(*p(i*420+32,j*630+38),f'F{j*3+i+1}',6,MUTED)
 for x,y,a,b in [(0,0,1260,20),(0,1240,1260,20),(0,20,20,1220),(1240,20,20,1220)]:rect(*p(x,y),a*scale,b*scale,'#8b9c9f','#8b9c9f')
 ws=[(20+i*180,340,180,40,f'LH{i+1}',i<3) for i in range(4)]+[(500,380,40,120,'LS',False)]
 ws+= [(1260-x-a,1260-y-b,a,b,nam.replace('L','R'),omit) for x,y,a,b,nam,omit in ws[:]]
 for x,y,a,b,nam,omit in ws:
  if variant=='B' and omit:continue
  rect(*p(x,y),a*scale,b*scale,'#536f78','#536f78');text(*p(x+a/2,y+b/2-8),nam,5.4,'#ffffff',align='center')
 for x,y,col,sgn in [(260,180,RED,1),(1000,1080,BLUE,-1)]:
  circle(*p(x,y),90*scale,None,col,1.4)
  if variant=='B':arrow(*p(x,y-35*sgn),*p(x,y+75*sgn),col)
  else:arrow(*p(x-35*sgn,y),*p(x+75*sgn,y),col)
 for x,y,col,sgn in [(260,650,RED,1),(1000,610,BLUE,-1)]:
  circle(*p(x,y),35*scale,col,col)
  yy=y+150*sgn;rect(*p(x-80,yy-60),160*scale,120*scale,None,col,.6)
  line(*p(x,y),*p(x,yy),col,.6)
 return p
title(4,'摆位尺寸 · 沿用原图 A / 低转向 B','原点左下，X向右、Y向上；尺寸量到障碍底脚。红方打红球，蓝方打蓝球。')
drawmap(16,152,.064,'A');drawmap(112,152,.064,'B')
text(56,242,'A / 原图完整墙',11,INK,True,'center');text(152,242,'B / 拆6段横墙',11,INK,True,'center')
text(56,143,'10段主墙；需绕行与转向',8,MUTED,align='center');text(152,143,'4段主墙；优先试用',8,MUTED,align='center')
table(130,['对象','坐标 / 外边界','备注'],[
 ('左横墙LH1～4','X20～740；Y340～380','各180，依次高60/80/100/80'),
 ('左支墙LS','X500～540；Y380～500','120长，高80'),
 ('右横墙RH1～4','上述绕(630,630)旋转180°','右端起依次RH1～4'),
 ('右支墙RS','X720～760；Y760～880','120长，高80'),
 ('红 / 蓝出生','(260,180) / (1000,1080)','B朝+Y / −Y；A朝+X / −X'),
 ('红 / 蓝球投影','(260,650) / (1000,610)','后柱(260,800)/(1000,460)'),
 ('B移除件','LH1、LH2、LH3及RH1、RH2、RH3','脚座一起移走')],[36,80,66],rowh=12,sz=7.6)
lines(14,33,['B入口净宽480；出生通道320；横墙端部通路500。尺寸未变，仍需实机试走。',
 '护沿：南北各420×3；东西内侧各610×2，接在南北护沿之间，四角不重叠。'],8.2,6)
C.showPage()

title(5,'手工球靶 · 两套同样做','现成轻球＋木条架＋磁铁；脱开磁点后落到低位，人工挂回复位。')
# Side view exact relative geometry, example H135 t8 ->U178, post173
x0,y0,sc=56,153,.36
def sp(y,z):return x0+y*sc,y0+z*sc
rect(*sp(90,0),120*sc,5*sc,'#adc2c6');rect(*sp(140,5),20*sc,173*sc,'#a88e6e');rect(*sp(-20,178),200*sc,20*sc,'#b49d7c')
rect(*sp(-5,170),10*sc,8*sc,'#beaa68')
circle(*sp(0,135),35*sc,RED,RED);circle(*sp(40,55),35*sc,None,RED,.7)
line(*sp(0,170),*sp(40,178),'#886f48',1.4);line(*sp(40,178),*sp(40,90),'#886f48',1,[3,3])
line(*sp(40,198),*sp(87.2,198),'#886f48',1.2);circle(*sp(87.2,200),1,'#886f48')
line(*sp(-70,0),*sp(230,0),INK,.8)
dim(*sp(0,0),*sp(150,0),'球投影 → 后柱中心150',-8)
text(14,239,'侧视示例',11,INK,True);lines(143,233,['臂：20×20×200','柱：示例173长','底座：160×120×5','球：Ø70','待击球心135','低位球心55','低位球底20'],8.3,8)
text(14,133,'先测高度，再裁柱长；135不是实测值',11,RED,True)
lines(14,123,['先做球顶组合，量 t＝木臂底面到裸球顶的总下探距离。',
 't包含磁铁、封胶、纸垫、钢圈、硬帽及织带，不只量磁铁厚度。',
 '木臂底高 U＝实测需要的球心高H＋35＋t；木柱长度＝U−5。',
 '例如H135、实测t8：U178，柱切173；每根220柱毛坯可现场裁短。',
 '臂前端在球前20，磁点距前端20；Ø3～4导孔距前端60。',
 '臂从球前20延伸至球后180，柱中心后150；臂坐在柱顶，用角码固定。',
 '柱左右各1个40角码；臂柱前后各1个20角码。螺钉勿穿出木条。',
 '160×120底座全部在球后90～210，柱居中；球前不做凸起脚座。',
 '柱底角码贴底板并跨压布基胶带；整块靶座用高粘双面胶＋胶带固定。',
 '以t8计，本毛坯建议配H95～182；超范围先改架子，不照搬柱长和绳长。'],8.7,7)
section(14,48,'必须检查的实际空间',[
 '挑臂与细绳不能扫到巴掌；臂高不足就升高并重新调整磁点，不强行套135。',
 '后柱150只是初样；命中后立即停机，检查球不缠柱。静态不碰≠全摆幅不碰。'],8.3)
C.showPage()

title(6,'球兜、磁点与绳长 · 不需要打印件','两颗球、帽、磁铁和胶带做法一致；命中只看“脱开上磁点并降到低位”。')
y=241
y=section(14,y,'1 / 布带兜球，磁片别直接粘泡棉',[
 '每球两段10宽×260长棉织带，分别绕球闭成两个正交圈。',
 'Ø70球周长约220，顶部留约40重叠；布基胶带包牢重叠与底部交叉处。',
 '20×20硬帽粘到顶部布带，钢圈粘帽并用胶带跨压边缘；绳绑帽旁织带。',
 '先人工轻拉，确认承重的是整圈布兜，不会只扯掉钢圈。'],8.9)
y=section(14,y,'2 / 小磁铁留在架上，先用薄纸调力',[
 '磁铁固定并包封在臂底，接触面覆盖薄胶带；普通钢垫圈跟球一起落下。',
 '磁铁太强就逐层增加薄纸垫；要能承球，又能被两种攻击正常触发。',
 'Ø8×2只是采购试样，不保证触发力。禁止把“能吸住”当作“可玩”。',
 '球色用本色或少量色带；不把整颗软球裹成厚硬纸壳。'],8.9)
y=section(14,y,'3 / 最省事定绳法：低位球底垫到20',[
 '每套先裁300绳，穿圆滑导孔；珠外径大于木孔，绳尾结须大于珠自身孔。',
 '暂时把球底垫高20，让止挡珠抵住孔上口，调好绳再锁结。',
 '这一步直接决定低位，不用纠结裁绳总长等于多少。',
 '示例U178、球顶系点近似裸球顶：孔下有效L88；孔内还另有20。',
 '球重新吸回时，多余绳段收在臂顶部浅纸槽，让绳能顺畅抽出。',
 '珠在臂上、结在珠上。球旁不留松绳圈；改高度后重新复核低位和绳路。'],8.9)
y=section(14,y,'4 / 快速验收后再开局',[
 '两机分别正常走近：脚或身体应不先撞底座，正常走动不导致球误脱。',
 '巴掌、出拳各试数次：要打中后能脱球、清楚停在低位、不挂绳。',
 '只晃动不计；身体撞架或手碰误脱则复位。先有效命中指定球者胜。',
 '如果两种攻击难度差很大，调整共同球/磁组件，暂不增加其他规则。'],8.9)
text(14,25,'制作顺序：先做1套靶试打，再复制第2套；最后贴装饰。',10,INK,True)
C.showPage()

# Sticker A4 layout is built after guide first 6 pages, then guide page7 finalized.
G=C
art=canvas.Canvas(str(OUT/'02_贴图与模板_A4_实际尺寸.pdf'),pagesize=(210*mm,297*mm))
art.setTitle('竞技场贴图与模板 A4 / 100%实际尺寸')
C=art
manifest=[];page_num=0
def arthead(label):
 global page_num
 page_num+=1;text(12,286,f'{page_num:02d}  {label}',8,INK,True)
 text(198,286,'A4 / 100% / 关闭适合页面',7,MUTED,align='right')
 line(12,12,112,12,INK,.8)
 for xx in (12,62,112):line(xx,10.5,xx,13.5,INK,.7)
 text(62,6.8,'此线应量得100 mm',6.5,MUTED,align='center')
 text(198,6.8,'先量尺，再裁切；单面打印',6.5,MUTED,align='right')
def crops(x,y,w,h):
 for xx,yy,ax,ay in [(x,y,-1,-1),(x+w,y,1,-1),(x,y+h,-1,1),(x+w,y+h,1,1)]:
  line(xx+ax*.7,yy,xx+ax*2.2,yy,MUTED,.4);line(xx,yy+ay*.7,xx,yy+ay*2.2,MUTED,.4)
def face(x,y,w,h,ident,short=False):
 rect(x,y,w,h,'#284955','#284955')
 # subtle engineering grid with clipped pattern
 C.saveState();cp=C.beginPath();cp.rect(x*mm,y*mm,w*mm,h*mm);C.clipPath(cp,stroke=0,fill=0)
 for xx in range(0,int(w)+15,15):line(x+xx,y+7,x+xx,y+h,'#3b5e68',.35)
 for yy in range(15,int(h),15):line(x,y+yy,x+w,y+yy,'#3b5e68',.35)
 rect(x,y,w,7,YELLOW,YELLOW)
 for xx in range(-10,int(w)+10,16):poly([(x+xx,y),(x+xx+6,y),(x+xx+13,y+7),(x+xx+7,y+7)],'#263d44')
 C.restoreState()
 text(x+8,y+h-12,'CYBER / ARENA',15 if w>150 else 13,'#ffffff',True)
 text(x+8,y+h-20,'机器人对战场',8,'#b7dce2')
 line(x+8,y+14,x+w-8,y+14,'#8bbdc5',.7)
 text(x+w-8,y+18,'BATTLE FIELD',8,'#cfe7e8',align='right')
 crops(x,y,w,h)
 text(x,y+h+2.2,f'{ident} 贴面 {w} × {h}；切实线框；加强片胶位剪开露板',6.5,MUTED)

# Group same size faces into sheets for easy quantities.
groups=[('高60墙：4片双面贴图',177,52,[f'{id}-{side}' for id in ('LH1','RH1') for side in ('正','背')],4),
 ('高80横墙：8片双面贴图',177,72,[f'{id}-{side}' for id in ('LH2','LH4','RH2','RH4') for side in ('正','背')],3),
 ('高100墙：4片双面贴图',177,92,[f'{id}-{side}' for id in ('LH3','RH3') for side in ('正','背')],2),
 ('支墙：4片双面贴图',117,72,[f'{id}-{side}' for id in ('LS','RS') for side in ('正','背')],3)]
for label,w,h,ids,n in groups:
 for start in range(0,len(ids),n):
  arthead(label);entries=[]
  for k,id in enumerate(ids[start:start+n]):
   x=16.5;y=271-(k+1)*(h+8)+3
   face(x,y,w,h,id);entries.append({'id':id,'size_mm':[w,h],'xy_mm':[x,y]})
  manifest.append({'page':page_num,'type':'wall_faces','items':entries});C.showPage()

# Spawn circle templates (not continuous floor paper): one per page.
for col,team in [(RED,'红'),(BLUE,'蓝')]:
 arthead(team+'方出生圆 / 优先作描线模板')
 cx,cy,r=105,166,90
 ring=C.beginPath();ring.circle(cx*mm,cy*mm,r*mm);ring.circle(cx*mm,cy*mm,82*mm)
 C.setFillColor(HexColor(col));C.drawPath(ring,stroke=0,fill=1,fillMode=0)
 arrow(105,147,105,202,col)
 text(105,127,team+'方出生',21,col,True,'center')
 text(105,114,team+'方攻击'+team+'球',11,col,align='center')
 text(105,60,'外径180；内径164。薄贴或按圆描线，不做凸起圆环。',8,MUTED,align='center')
 text(105,50,'B朝向：红向上 / 蓝向下；摆放时旋转此页方向。',8,MUTED,align='center')
 text(105,40,'A朝向：红向右 / 蓝向左；箭头朝向随布局转动。',8,MUTED,align='center')
 manifest.append({'page':page_num,'type':'spawn_template','team':team,'diameter_mm':180,'center_mm':[105,166]});C.showPage()

# Target signs fit on rear base. Scores for persistent state printed on support, not ball.
arthead('靶座标牌 / 底板背面编号')
for idx,(col,team,enemy) in enumerate([(RED,'红','蓝'),(BLUE,'蓝','红')]):
 x,y=20,214-idx*62;w,h=150,50
 rect(x,y,w,h,col,col);text(x+8,y+33,team+'方打这颗球',20,'#ffffff',True)
 text(x+8,y+20,enemy+'方守护  /  脱开磁点并落到低位才计分',8,'#ffffff')
 text(x+8,y+8,'摇晃不算 · 人工挂回复位',9,'#ffffff',True);crops(x,y,w,h)
 text(x,y+h+2,'贴在靶座后方或外侧立面；不要贴到球上',6.5,MUTED)
for i in range(6):
 x=20+(i%3)*52;y=104-(i//3)*26
 rect(x,y,46,20,'#e7eff0');text(x+23,y+11,f'F{i+1}',13,INK,True,'center');text(x+23,y+3,'底板背面编号',6,MUTED,align='center');crops(x,y,46,20)
text(20,51,'F1 F2 F3 为南排；F4 F5 F6 为北排，从西向东排列。',8,MUTED)
manifest.append({'page':page_num,'type':'target_signs_and_base_ids','sign_size_mm':[150,50],'base_id_size_mm':[46,20]});C.showPage()
art.save();N=page_num

# Real-size A3 imposition: two untouched A4 portrait pages beside each other.
reader=PdfReader(str(OUT/'02_贴图与模板_A4_实际尺寸.pdf'));writer=PdfWriter()
for i in range(0,N,2):
 pg=PageObject.create_blank_page(width=420*mm,height=297*mm)
 pg.merge_transformed_page(reader.pages[i],Transformation().translate(tx=0,ty=0))
 if i+1<N:pg.merge_transformed_page(reader.pages[i+1],Transformation().translate(tx=210*mm,ty=0))
 writer.add_page(pg)
with (OUT/'03_贴图与模板_A3_实际尺寸.pdf').open('wb') as f:writer.write(f)

C=G;title(7,'装配顺序与打印单','贴图两套内容相同、尺寸相同；选A3或A4一套，切勿两套都印。')
text(14,240,f'A4版共{N}页；A3横向版共{math.ceil(N/2)}页',16,INK,True)
lines(14,228,['A4：210 × 297，纵向；A3：420 × 297，横向。',
 '打印设置：100% / 实际大小；关闭“适合页面”和“缩放到可打印区域”。',
 'A3版已经双拼，不再选“每张两页”；单面、彩色、哑面背胶优先。',
 '每页有100 mm校准线。先打一页量尺，正确后再打印其余页。'],9,7)
table(188,['图案','完成后的裁切尺寸','数量'],[
 ('高60墙双面贴图','177 × 52','4片'),('高80横墙双面贴图','177 × 72','8片'),
 ('高100墙双面贴图','177 × 92','4片'),('支墙双面贴图','117 × 72','4片'),
 ('红蓝出生点模板','外径180 / 内径164','各1'),('红蓝靶座标牌','150 × 50','各1'),('底板背面编号','46 × 20','6片')],[74,77,31],rowh=10,sz=8.6)
y=section(14,101,'最省工装配顺序',[
 '① 先做一套球靶试打；同时让商家裁板和木条。',
 '② 六底板排成3列2行，背面用薄透明胶连接，逐缝检查并放平桌面。',
 '③ 竖墙贴图、底脚胶合、加三角；护沿和墙脚按第4页坐标固定。',
 '④ 安装两套球靶，确认身体不先撞架、两机可触发、细绳不缠绕。',
 '⑤ 描出生圈、贴后方标牌；先玩B，时间够再装上其余6段墙试A。'],8.7)
lines(14,45,['材料依据：Palram PALIGHT官方加工说明；3A Composites FOREX官方产品页。',
 'PVC发泡板适合裁切/贴膜；5 mm整板建议店家代切。',
 '来源链接和完整说明在同目录README；无需指定购买某个品牌。'],7.7,5)
G.save()

data={'version':'v07','date':'2026-10-17','units':'mm','arena_confirmed_mm':[1260,1260],
 'sheet_purchase':[1220,2440,5],'floor_grid':[3,2],'floor_tile':[420,630,5],
 'pvc_cut_list':[{'id':a,'name':b,'width':c,'height':d,'quantity':e,'thickness':5} for a,b,c,d,e in cuts],
 'optional_braces':{'legs':[15,30],'thickness':5,'quantity':20},
 'floor_seam':{'suggested_gap_max':0.5,'suggested_step_max':0.2,'underside_tape_max_thickness':0.1,'full_table_support':True},
 'perimeter':{'section':[20,30],'cut_lengths':[{'length':420,'quantity':6},{'length':610,'quantity':4}],'purchase':'5 pieces 1200 long OR 7 pieces 1000 long'},
 'target_wood':{'section':[20,20],'arms':[200,2],'post_blanks':[220,2],'post_example_only':173},
 'target_height_example':{'H':135,'t_measured_assumption':8,'U':178,'post':173,'ball_diameter':70,'released_bottom':20,'cord_below_guide_if_q0':88},
 'stickers':manifest,'A4_page_count':N,'A3_page_count':math.ceil(N/2),'physical_tested':False}
(HERE/'制作与打印清单.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PDFS: guide=7; artwork A4={N}; artwork A3={math.ceil(N/2)}')
