"""Dimensioned vector drawing set, mm model units; PDF points used for paper.
Run using the Codex bundled Python (reportlab, Pillow, pypdf).
"""
from pathlib import Path
import math,json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

HERE=Path(__file__).resolve().parent
OUT=HERE/'output'/'pdf'; OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('yh',r'C:\Windows\Fonts\msyh.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('yhb',r'C:\Windows\Fonts\msyhbd.ttc',subfontIndex=0))
W,H=1190.55,841.89
INK='#20394a'; MUTED='#617582'; LINE='#c8d2d6'; BLUE='#287ce4'; RED='#ed554d'; WALL='#667c82'; BG='#f5f7f7'
C=canvas.Canvas(str(OUT/'错位T墙竞技场_v05_尺寸与打印图册.pdf'),pagesize=(W,H))
C.setTitle('错位T墙竞技场 v05 | 尺寸、装配与打印分区');C.setAuthor('CyberBrick / milk')

def txt(x,y,s,size=10,color=INK,bold=False,align='left'):
    C.setFillColor(HexColor(color));C.setFont('yhb' if bold else 'yh',size)
    {'left':C.drawString,'center':C.drawCentredString,'right':C.drawRightString}[align](x,y,str(s))
def line(x1,y1,x2,y2,col=LINE,w=1,dash=None):
    C.setStrokeColor(HexColor(col));C.setLineWidth(w);C.setDash(dash or []);C.line(x1,y1,x2,y2);C.setDash([])
def rect(x,y,w,h,fill=None,stroke=LINE,sw=1):
    C.setFillColor(HexColor(fill or '#ffffff'));C.setStrokeColor(HexColor(stroke));C.setLineWidth(sw);C.rect(x,y,w,h,fill=bool(fill),stroke=1)
def poly(pts,fill=None,stroke=None,sw=1):
    p=C.beginPath();p.moveTo(*pts[0]);
    for pt in pts[1:]:p.lineTo(*pt)
    p.close();C.setLineWidth(sw)
    if fill:C.setFillColor(HexColor(fill))
    if stroke:C.setStrokeColor(HexColor(stroke))
    C.drawPath(p,fill=bool(fill),stroke=bool(stroke))
def circle(x,y,r,fill=None,stroke=LINE,sw=1,dash=None):
    C.setFillColor(HexColor(fill or '#ffffff'));C.setStrokeColor(HexColor(stroke));C.setLineWidth(sw);C.setDash(dash or []);C.circle(x,y,r,fill=bool(fill),stroke=1);C.setDash([])
def arrow(x1,y1,x2,y2,col=INK,w=1.5):
    line(x1,y1,x2,y2,col,w); a=math.atan2(y2-y1,x2-x1);d=7
    poly([(x2,y2),(x2-d*math.cos(a-.43),y2-d*math.sin(a-.43)),(x2-d*math.cos(a+.43),y2-d*math.sin(a+.43))],col)
def dim(x1,y1,x2,y2,label,offset=0,color=MUTED,size=10):
    dx,dy=x2-x1,y2-y1;length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
    a=(x1+nx*offset,y1+ny*offset);b=(x2+nx*offset,y2+ny*offset)
    line(x1,y1,a[0]+nx*5,a[1]+ny*5,color,.6);line(x2,y2,b[0]+nx*5,b[1]+ny*5,color,.6)
    line(*a,*b,color,.7)
    for p in (a,b):line(p[0]-3,p[1]-3,p[0]+3,p[1]+3,color,.7)
    mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
    C.saveState();C.translate(mx+nx*6,my+ny*6);C.rotate(math.degrees(math.atan2(dy,dx)));txt(0,0,label,size,color,align='center');C.restoreState()
def header(n,title,sub):
    C.setFillColor(HexColor('#ffffff'));C.rect(0,0,W,H,fill=1,stroke=0)
    txt(38,H-35,'CYBERBRICK / MILK  ·  V05',11,MUTED,True)
    txt(38,H-73,title,25,INK,True);txt(38,H-96,sub,11,MUTED)
    line(38,48,W-38,48,LINE,.7)
    txt(38,29,'2026-10-13  |  单位 mm  |  数字设计与试打印交付；未切片、未打印、未实机验收',9,MUTED)
    txt(W-38,29,f'{n:02d} / 06',10,MUTED,align='right')
def note(x,y,title,body,width=355):
    txt(x,y,title,13,INK,True); yy=y-23
    for s in body:
        txt(x,yy,s,10.5,MUTED); yy-=18
    return yy-20

walls=[]
for i,h in enumerate((60,80,100,80)):
    walls.append(dict(id=f'LH{i+1}',x=20+180*i,y=340,l=180,b=40,h=h,optional=i<3))
walls.append(dict(id='LS',x=500,y=380,l=40,b=120,h=80,optional=False))
for z in list(walls):
    walls.append(dict(z,id=z['id'].replace('L','R'),x=1260-z['x']-z['l'],y=1260-z['y']-z['b']))
targets=[(260,650,RED,'TR','红攻 / 蓝守'),(1000,610,BLUE,'TB','蓝攻 / 红守')]
spawns=[(260,180,RED,'SR'),(1000,1080,BLUE,'SB')]

def plan(x0,y0,s,variant='A',grid=True,ids=True,routes=True,fall=False):
    def p(x,y):return x0+x*s,y0+y*s
    rect(x0,y0,1260*s,1260*s,'#f6f8f8')
    if grid:
        for i in range(1,7):line(*p(i*180,0),*p(i*180,1260),LINE,.5);line(*p(0,i*180),*p(1260,i*180),LINE,.5)
    for a,b,w,h in [(0,0,1260,20),(0,1240,1260,20),(0,20,20,1220),(1240,20,20,1220)]:
        rect(*p(a,b),w*s,h*s,'#8a9b9f','#8a9b9f')
    for z in walls:
        if variant=='B' and z['optional']:
            C.setDash([3,3]);rect(*p(z['x'],z['y']),z['l']*s,z['b']*s,None,'#c5cccc',.6);C.setDash([])
            continue
        rect(*p(z['x'],z['y']),z['l']*s,z['b']*s,WALL,WALL)
        if ids:txt(*p(z['x']+z['l']/2,z['y']+z['b']/2-8),z['id'],8,'#ffffff',align='center')
    for x,y,col,name,owner in targets:
        if fall:circle(*p(x,y),230*s,None,col,.6,[3,3])
        circle(*p(x,y),45*s,col,col)
        txt(*p(x,y-9),name,9,'#ffffff',True,'center')
        txt(*p(x,y+65),owner,9,col,align='center')
    for x,y,col,name in spawns:
        circle(*p(x,y),90*s,None,col,2)
        heading=(0 if col==RED else 180) if variant=='A' else (90 if col==RED else 270)
        a=math.radians(heading);ux,uy=math.cos(a),math.sin(a)
        body=[]
        for u,v in [(-100,-45),(100,-45),(100,45),(-100,45)]:body.append(p(x+u*ux-v*uy,y+u*uy+v*ux))
        poly(body,None,col,.8);arrow(*p(x,y),*p(x+75*ux,y+75*uy),col,1.4)
        txt(*p(x,y-130),name+' 出生',9,col,align='center')
    if routes and variant=='B':
        arrow(*p(260,285),*p(260,480),RED,2);arrow(*p(1000,975),*p(1000,780),BLUE,2)
        txt(*p(285,420),'主路线',9,RED);txt(*p(865,845),'主路线',9,BLUE)
    if routes and variant=='A':
        # Coarse waypoints show the topology, not a claimed robot trajectory.
        path=[(370,180),(900,180),(900,430),(630,630),(450,690)]
        for mirror,col in [(False,RED),(True,BLUE)]:
            pts=[(1260-x,1260-y) if mirror else (x,y) for x,y in path]
            for a,b in zip(pts[:-1],pts[1:]):
                line(*p(*a),*p(*b),col,1.7,[6,4])
            arrow(*p(*pts[-2]),*p(*pts[-1]),col,1.7)
        txt(*p(580,105),'虚线：绕行方向示意',9,MUTED,align='center')
    dim(*p(0,1260),*p(1260,1260),'1260 名义分块尺寸',25)
    dim(*p(0,0),*p(0,1260),'1260',28)
    return p

header(1,'01  /  原图布局 A · 平面划区','保留左下 / 右上出生、两组错位 T 墙与两侧目标；为操作和倒伏净空调整墙长、支墙位置和靶位。')
p=plan(77,106,.455,'A',True,True,True,True)
dim(*p(20,445),*p(500,445),'靶侧横向净宽 480',0,size=9)
dim(*p(740,335),*p(1240,335),'墙端通路 500',-23,size=9)
dim(*p(1040,20),*p(1040,340),'出生通行带 320',0,size=9)
txt(*p(0,-48),'O (0,0) 左下；X 向右 / Y 向上；地板底 Z=0，行走面 Z=6',9,MUTED)
y=H-153
y=note(735,y,'看颜色判断攻击目标',['红圈出发 → 红 TR；该目标由蓝方守护。','蓝圈出发 → 蓝 TB；该目标由红方守护。','颜色表示“谁来攻击”，避免沿用旧版反色规则。'])
y=note(735,y,'这张图的通行代价',['完整墙布局必须绕横墙，并在接近目标时转向。','虚线只表达大方向，不是已验证的连续步态轨迹。','A 用于还原与比较；转弯困难时优先采用 B。'])
y=note(735,y,'坐标 / 面向（俯视，角度从 +X 起）',['SR 红出生：(260,180)，0°；SB：(1000,1080)，180°。','TR 红目标：(260,650)；TB 蓝目标：(1000,610)。','圆环直径180是出生标记，非机器人限制边界。','虚线圆半径230为靶倒伏预留，不是靶座。'])
y=note(735,y,'通道尺寸含义',['320：外围内侧到横墙外侧的出生带净宽。','500：横墙自由端到对侧护沿内侧净宽。','480：靶侧护沿内侧到支墙侧面的横向净距。','中央墙端对角316.23；以上均非实测转弯直径。'])
note(735,y,'场地边界',['名义 1260 × 1260；地板实物外缘 1259.6 × 1259.6。','外围护沿名义包络1260；落地位置允许0.2边缘差。','桌面建议至少1320 × 1320，并全幅平整承托。'])
C.showPage()

header(2,'02  /  低转向布局 B · 常玩起步版','同一套零件：移走 6 段横墙，保留 4 段落地墙；主目标和出生点不变，只改变出生朝向。')
p=plan(77,106,.455,'B',True,True,True,False)
dim(*p(20,370),*p(500,370),'入口净宽 480',-32,size=10)
dim(*p(760,860),*p(1240,860),'入口净宽 480',0,size=10)
circle(*p(260,460),150*.455,None,RED,.7,[3,3]);txt(*p(80,495),'Ø300 设计净空',9,RED)
txt(*p(0,-48),'灰虚线位置 = 移除的墙；不放任何凸出的孔塞、连接片或标牌。',9,MUTED)
y=H-153
y=note(735,y,'只改装配，不增加机关',['移走 LH1 / LH2 / LH3，以及 RH1 / RH2 / RH3。','LH4、LS 与 RH4、RS 保留，仍限制横向活动范围。','红出生改朝 +Y（90°），蓝出生改朝 −Y（270°）。','双方沿宽入口短直进，停步后攻击各自颜色目标。'])
y=note(735,y,'为什么适合先玩',['出生中心至目标中心470；有效接近量需实测。','路线无需规定急转或反复纠偏。','两条直线进攻带分离，墙保留分区作用。','此版侧重击靶竞速；不宣称已验证拦截策略。'])
y=note(735,y,'一条胜负规则',['谁先用攻击机构把指定目标整体击倒，谁赢。','目标侧壁落地且不自行直立即算；仅滑走不算。','身体或脚推倒、误碰、桌面震动误倒：暂停复位。','看不清先后则平局；试用每局60秒，到时未倒平局。'])
y=note(735,y,'复玩方式：保留同样的简单规则',['① 交换操作者或机器人，再按各机实测范围摆正。','② 两个目标沿 Y 同步反向平移最多 ±30。','   红 Y=620～680；蓝 Y=640～580；X 保持不变。','③ B 熟悉后试 A；比较重摆次数和实际转弯负担。'])
note(735,y,'机械留量',['Ø300 是动态净空设计假设；巴掌 CAD 扫掠约Ø254。','实测扫掠或摆脚更大时扩大空间；不靠提高精度补偿。','墙高60～100只阻行走，不保证挡住上方攻击机构。'])
C.showPage()

def project(x,y,z=0):return (414+(x-y)*.30,660-(x+y)*.175+z*.3464)
def boxfaces(x,y,l,b,z,h,top='#d9e3e4',side='#a9b9be'):
    pp=lambda a,b,c:project(a,b,c)
    # view from the positive X,+Y quadrant
    return [([(x+l,y,z),(x+l,y+b,z),(x+l,y+b,z+h),(x+l,y,z+h)],side),
      ([(x,y+b,z),(x+l,y+b,z),(x+l,y+b,z+h),(x,y+b,z+h)],'#91a7ae' if top==WALL else side),
      ([(x,y,z+h),(x+l,y,z+h),(x+l,y+b,z+h),(x,y+b,z+h)],top)]
def drawiso():
    for j in range(7):
      for i in range(7):
        for pts,col in boxfaces(i*180+.2,j*180+.2,179.6,179.6,0,6,'#edf2f3','#c9d6db'):poly([project(*p) for p in pts],col,'#bccdd1',.35)
    # flat spawn outlines
    for x,y,col,name in spawns:
      pts=[project(x+90*math.cos(t*math.tau/60),y+90*math.sin(t*math.tau/60),6) for t in range(60)]
      poly(pts,None,col,2)
      a=1 if col==RED else -1
      arrow(*project(x-50*a,y,6),*project(x+65*a,y,6),col,1.8)
    objects=[]
    for z in walls:objects.append((z['x']+z['y']+(z['l']+z['b'])/2,'box',z))
    for x,y,l,b in [(0,0,1260,20),(0,1240,1260,20),(0,20,20,1220),(1240,20,20,1220)]:objects.append((x+y+(l+b)/2,'box',dict(x=x,y=y,l=l,b=b,h=35,id='')))
    for t in targets:objects.append((t[0]+t[1],'target',t))
    for depth,typ,z in sorted(objects,key=lambda a:a[0]):
      if typ=='box':
        for pts,col in boxfaces(z['x'],z['y'],z['l'],z['b'],6,z['h'],WALL,'#49606b'):poly([project(*p) for p in pts],col,'#49606b',.35)
      else:
        x,y,col,nam,_=z;N=48
        for k in range(N):
          a,b=k*math.tau/N,(k+1)*math.tau/N
          if math.cos((a+b)/2)+math.sin((a+b)/2)<0:continue
          pts=[project(x+45*math.cos(t),y+45*math.sin(t),zz) for t,zz in [(a,6),(b,6),(b,166),(a,166)]]
          poly(pts,col,col,.2)
        pts=[project(x+45*math.cos(t*math.tau/N),y+45*math.sin(t*math.tau/N),166) for t in range(N)]
        poly(pts,col,col,.3)
        inner=[project(x+44.2*math.cos(t*math.tau/N),y+44.2*math.sin(t*math.tau/N),166) for t in range(N)]
        poly(inner,'#243e56')
        txt(*project(x,y,183),nam,11,col,True,'center')
    dim(*project(0,1260,0),*project(1260,1260,0),'1260',-28,size=12)
    dim(*project(1260,1260,0),*project(1260,0,0),'1260',-28,size=12)

header(3,'03  /  单层 3D 总装 · 原图布局 A','所有墙和目标均落在同一地面。图中出生圆环和文字为印刷 / 贴膜示意，不计入打印几何。')
drawiso()
y=H-153
y=note(862,y,'高度层级',['地板厚：6。','外围护沿高：35（从行走面起）。','横墙高度依次：60 / 80 / 100 / 80。','支墙高度：80。','目标高：160；外径90。'])
y=note(862,y,'落地与拆换',['主墙10段，可逐段拆换。','护沿28段，直接落在地板上。','目标整枚直立，击倒后人工复位。','墙脚可用薄可移胶固定。','目标底部不粘，不设悬挂或支架。'])
y=note(862,y,'模型查看',['viewer.html 可离线旋转、缩放、俯视。','支持 A / B、地块编号与分解查看。','装配 STEP 用于编辑和核对摆位。','单件 STL 才用于切片。'])
note(862,y,'制造状态',['尺寸已定义，连接需先试配。','图示未模拟机构运动、撞击或跌落。','护沿不是经验证的抗冲出装置。'])
txt(65,111,'地板 49 块 × 179.6 × 179.6 × 6  /  下方由桌面完整承托',12,INK,True)
txt(65,86,'各打印件的尺寸和装配位置见第 4、5 页；倒靶与攻击高度留待实际机器人验证。',10,MUTED)
C.showPage()

header(4,'04  /  地板打印分区与平缝连接','7 列 × 7 行；所有地板同一几何，A1～G7 为装配位置编号，打印时无需分别建模。')
gx,gy,gs=76,132,.425
for j in range(7):
  for i in range(7):
    rect(gx+i*180*gs,gy+j*180*gs,179.6*gs,179.6*gs,'#eaf0f2' if (i+j)%2 else '#f8fafb')
    txt(gx+(i*180+90)*gs,gy+(j*180+83)*gs,f'{chr(65+j)}{i+1}',15,INK,True,'center')
for j in range(7):
  for i in range(7):
    if i<6:rect(gx+((i+1)*180-22)*gs,gy+(j*180+81)*gs,44*gs,18*gs,'#9bb6c3','#9bb6c3')
    if j<6:rect(gx+(i*180+81)*gs,gy+((j+1)*180-22)*gs,18*gs,44*gs,'#9bb6c3','#9bb6c3')
dim(gx,gy+1260*gs,gx+1260*gs,gy+1260*gs,'7 × 180 = 1260（节距）',25)
txt(gx,gy-64,'蓝灰短条 = 底面连接片投影；不会暴露在行走面。',10,MUTED)
dim(gx,gy,gx+180*gs,gy,'单块节距180',-28)
txt(735,685,'拼缝剖面 / 非等比例示意',14,INK,True)
sx,sy=735,530
rect(sx,sy,150,80,'#dce8ed');rect(sx+164,sy,150,80,'#dce8ed')
rect(sx+112,sy,38,28,'#ffffff','#ffffff');rect(sx+164,sy,38,28,'#ffffff','#ffffff')
rect(sx+115,sy+3,84,19,'#809ea9','#809ea9')
line(sx,sy+80,sx+314,sy+80,INK,1.5)
txt(sx,sy+96,'连续行走面：无凸榫、无螺钉头',11,INK,True)
txt(sx+157,sy+50,'缝',8,MUTED,align='center');txt(sx+157,sy+34,'0.4',8,MUTED,align='center')
txt(sx,sy-25,'地板6；底槽深2.4；桥片厚2；上层连续厚3.6。',10,MUTED)
txt(sx,sy-44,'桥片坐落桌面 Z=0，留0.4高度间隙，不垫高地板。',10,MUTED)
y=435
y=note(735,y,'数量与接口',['49块地板；84片桥片（左右42 + 上下42）。','桥片44 × 18 × 2，颈部形状与底槽匹配。','槽对连接片每侧留0.3；样片先确认松紧。','接口只定位，背面薄胶带锁定；不靠桥片抬整场。'])
y=note(735,y,'打印朝向与余量',['地板行走面朝打印台、底槽朝上；用时翻回。','179.6 + 两侧各8 brim = 195.6，小于200。','这是名义幅面核对，仍需核对实际可用热床范围。','桥片平放；打印后去象脚，检查翘曲和接缝。'])
note(735,y,'交付验收目标（非实测结果）',['接缝名义0.4，建议实测≤0.5；高差建议≤0.2。','平整和摩擦需同时检查，两机跨缝各试10次。','若脚打滑，使用全场同厚表层，再重新验证接缝。'])
C.showPage()

header(5,'05  /  打印拆件与目标尺寸','以 200 × 200 × 200 小机保守设计。所有单件建议各留8 mm裙边空间；无需使用300 mm大机。')
rows=[('F01','通用地板','179.6 × 179.6 × 6','49','49','行走面朝下'),('J01','底部连接片','44 × 18 × 2','84','84','平放'),('W01','横墙60','180 × 40 × 60','2','0','墙底朝下'),('W02','横墙80','180 × 40 × 80','4','2','墙底朝下'),('W03','横墙100','180 × 40 × 100','2','0','墙底朝下'),('W04','支墙80','120 × 40 × 80','2','2','墙底朝下'),('E01','长护沿','180 × 20 × 35','26','26','底面朝下'),('E02','短护沿','140 × 20 × 35','2','2','底面朝下'),('T01','开口落地靶','Ø90 × 160；壁0.8 / 底1.2','2','2','底朝下、口朝上'),('C01/02','拼缝样片','各39.8 × 40 × 6','各1试配','共用','行走面朝下')]
cols=[40,103,234,482,535,594,710]
for k,s in enumerate(['编号','零件','外包络 / mm','A用量','B用量','摆放']):txt(cols[k]+5,681,s,10,INK,True)
line(40,670,705,670,INK,1)
for r,row in enumerate(rows):
    yy=646-r*34
    if r%2==0:rect(40,yy-12,665,32,'#f1f5f6','#f1f5f6')
    for k,v in enumerate(row):txt(cols[k]+5,yy,v,9.5,INK)
txt(40,283,'完整 A：173件（不计样片）；B装场167件，移除件保留备用。',10,INK,True)
txt(40,263,'最小验证：2片样片 + 1桥片 + 1支墙 + 2靶；确认配合与击倒手感后再整场打印。',10,MUTED)
txt(40,222,'建议切片起点（需按设备校正）',14,INK,True)
for j,s in enumerate(['地板 / 墙：层高0.20，喷嘴0.4，3圈壁，顶底≥1.0；填充15%～20%作为初始值。','目标：按CAD薄壁保留0.8，禁用花瓶模式；检查两道连续壁和1.2底层，内部不加填充。','两靶同材料、同切片、同方向，打印后称重配对；最终重量和抗倾倒阈值靠试打确定。','几何外形不等于材料消耗；总耗材、工时、支撑需由切片结果填写，未在此虚构。']):txt(40,195-j*23,s,10.5,MUTED)
tx,ty=855,411
rect(tx,ty,160,250,'#f4e3df',RED,1)
rect(tx+3,ty+3,154,247,'#ffffff','#ffffff')
line(tx,ty+250,tx+3,ty+250,RED,1);line(tx+157,ty+250,tx+160,ty+250,RED,1)
dim(tx,ty+250,tx+160,ty+250,'Ø90 外径',22)
dim(tx+160,ty,tx+160,ty+250,'160',-22)
txt(tx-12,ty-27,'目标剖面示意 / 薄壁开口筒',11,INK,True)
txt(790,335,'壁厚0.8；底厚1.2；内径88.4。',11,MUTED)
txt(790,311,'直接放在行走面；整个目标倒下。',11,MUTED)
txt(790,287,'没有独立靶座，不加磁铁或配重。',11,MUTED)
txt(790,245,'倒伏净空：每靶保守半径230',12,INK,True)
txt(790,220,'包络估算：45 + √(160² + 90²) ≈ 229。',10,MUTED)
txt(790,198,'A与B的标定靶位均不与固定墙相交。',10,MUTED)
txt(790,176,'只覆盖几何倾倒，不覆盖撞飞或滚动。',10,MUTED)
txt(790,135,'160是试打尺寸，不是已确认攻击高度。',11,RED,True)
C.showPage()

header(6,'06  /  约束、依据与装配验收','先验证关键组件再批量打印；本页明确设计事实与尚未获得的实测数据。')
y=685
y=note(45,y,'用户已确认',['单层平地；纵向结构仅落地墙和障碍；无架空平台或悬挂目标。','机器人含攻击机构约200 × 90，转弯困难；蓝从蓝圈打蓝靶，红同理。','分块打印、拆换墙体与目标、上表面平缝；桌面尺寸未确认。'])
y=note(45,y,'本版设计假设',['1260方形场地；49块180节距地板；地板6厚；外围20厚 / 35高。','480入口、320出生带、500墙端通路；Ø300动作预留仅供首轮验证。','目标Ø90 × 160；160高、0.8壁厚、230倒伏半径、±30靶位变化均属本版选值。'])
y=note(45,y,'资料能支持到哪里',['巴掌掌长75、轴心至杆孔组中心51；按装配CAD外包络，整圆扫掠上界约Ø254。','拳头CAD约187.2～207.2长 × 114宽 × 159.0高，不能代替本次实物量测。','约134.8 = CAD身体顶面至脚底89 + 腕部锚点45.8；只是腕部参考高度。','2026-10-06仅确认第二台落地前进与M1独立运转；未验收遥控并发对战。'])
note(45,y,'资料索引（相对项目根目录）',['04_结构与硬件/Otto_75mm巴掌腕部接口_v02/设计与实施记录.md','同目录/几何验证报告.json（掌包围盒X=51～126，Y=±14.892）','04_结构与硬件/拳头_整体比例预览_v03/按用户参数导出_STL/','  所选参数与导出信息.json','05_程序与测试/CB1_Otto控制框架_v02/','  2026-10-06_第二台机器人实测记录.md'])
y=685
y=note(705,y,'最少实测清单',['1. 桌面有效面积与平整度；不能直接缩小全部模型适配。','2. 两机含攻击件最大长宽高、摆脚与摇摆宽度。','3. 两机地面至有效接触区间、巴掌整圆扫掠半径。','4. 前进停止距离、90° / 180°转弯实际轨迹。','5. 两靶实际质量、静置稳定、两种攻击有效击倒次数。','6. 接缝高差 / 翘边、跨缝行走和墙脚抗滑移。'])
y=note(705,y,'装配顺序',['① 打印样片与桥片，试配底部槽口。','② 在平桌临时摆墙靶，按B测攻击与停止位置。','③ 打印地板，倒置排A1～G7，嵌84片桥片。','④ 底面胶带定位，分区翻回并逐缝检查；不悬空搬整场。','⑤ 装28段护沿和墙；平面薄标记出生点、靶位。','⑥ 摆靶、核对进攻颜色；确认两机控制后试玩。'])
y=note(705,y,'同一套零件的复用原则',['低转向B先各机5次接近试打；建议至少4次无需人工摆正。','这是验收目标，当前没有成绩；失败则调整空间或靶参数。','变更靶位 / 墙位后重查倒伏净空；两靶参数同步修改。','墙移动、目标误倒时停局复位；异常控制先排障。'])
note(705,y,'当前交付的边界',['STL / STEP与网格检查用于几何与制造准备。','未做切片仿真、结构受力验证、实物打印或实机比赛。','桌面、转弯轨迹和攻击高度确认后才能签收实体定版。'])
C.showPage();C.save()
(HERE/'drawing_parameters.json').write_text(json.dumps(dict(units='mm',arena=1260,tile_pitch=180,walls=walls,targets=targets,spawns=spawns),ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT/'错位T墙竞技场_v05_尺寸与打印图册.pdf')
