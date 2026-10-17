from pathlib import Path
from math import sqrt

OUT=Path(__file__).resolve().parent
INK='#263b42'; MUTED='#64777b'; LINE='#cfdbdc'; ARM='#789298'

def text(x,y,s,size=16,color=INK,weight=400,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{s}</text>'
def path(d,color=LINE,width=1.5,dash='',extra=''):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{dash}" {extra}/>'
def circle(x,y,r,fill,stroke='none',width=1):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
def defs(prefix):
    return f'''<defs><radialGradient id="{prefix}ball" cx="32%" cy="23%" r="85%"><stop offset="0" stop-color="var(--ball-light,#ff9791)"/><stop offset=".6" stop-color="var(--ball,#e75e58)"/><stop offset="1" stop-color="var(--ball-dark,#ab3536)"/></radialGradient><marker id="{prefix}arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#688e90"/></marker><marker id="{prefix}dim" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M10 0L0 5L10 10" fill="none" stroke="#668184" stroke-width="1.5"/></marker></defs>'''

def scene(hit=False,prefix='r'):
    ox,oy,scale=240,375,1.05
    def p(x,y,z): return (round(ox+scale*(.85*x+.60*y),2),round(oy+scale*(.30*x-.29*y-z),2))
    def poly(points,fill,stroke='#769098'):
        pts=' '.join(','.join(map(str,p(*q))) for q in points)
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
    def box(x,y,z,w,d,h,colors):
        X,Y,Z=x+w,y+d,z+h
        return ''.join([poly([(x,y,z),(X,y,z),(X,y,Z),(x,y,Z)],colors[0]),poly([(X,y,z),(X,Y,z),(X,Y,Z),(X,y,Z)],colors[1]),poly([(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],colors[2])])
    def line3(a,b,col='#688e90',width=2,dash='',extra=''):
        A,B=p(*a),p(*b)
        return path(f'M{A[0]} {A[1]}L{B[0]} {B[1]}',col,width,dash,extra)
    def leader(a,elbow,label,tx,ty):
        X,Y=p(*a)
        return path(f'M{X} {Y}L{elbow[0]} {elbow[1]}L{tx-8} {elbow[1]}',MUTED,1)+circle(X,Y,2.5,MUTED)+text(tx,ty,label,13)
    s=defs(prefix)
    s+=box(-125,-100,-6,250,290,6,['#dce5e3','#c9d8d6','#edf3ef'])
    # One rear mounted support; no raised base under the ball / attack frontage.
    s+=box(-18,125,0,36,50,7,['#68838a','#5d777f','#8da3a5'])
    s+=box(-8,140,7,16,20,223,['#617f88','#496873','#90a8ad'])
    s+=box(-10,-10,180,20,170,10,['#68848a','#516e78','#a2b8b8'])
    # top open tray on arm: shallow visual guide, not a closed cable box.
    s+=box(-8,48,190,16,48,2,['#9bafb0','#839b9e','#d5e0dc'])
    s+=box(-6,-6,170,12,12,10,['#cbb169','#a38b4f','#ebd79b'])
    gx,gy=p(0,40,190)
    s+=f'<ellipse cx="{gx}" cy="{gy}" rx="4.5" ry="2.5" fill="#405a64"/>'
    if hit:
        by,bz=40,55
        s+=line3((0,40,180),(0,by,bz+35),'#957744',2.5)
        s+=circle(gx,gy-2,4,'#957744')
        # Original sphere ghost makes absence visible.
        hx,hy=p(0,0,135)
        s+=circle(hx,hy,35*scale,'none','#a6b9b9',1.5)
        s+=text(hx,hy+5,'已脱离',13,MUTED,500,'middle')
        s+=line3((-55,10,128),(-55,40,60),'#668e90',2.4,'5 6',f'marker-end="url(#{prefix}arrow)"')
    else:
        by,bz=0,135
        s+=line3((0,0,170),(0,40,180),'#957744',2.5)
        c=[p(0,40,190),p(0,51,196),p(0,70,199),p(0,58,193),p(0,87,196)]
        s+=path('M'+'Q'.join([]),'#957744') if False else ''
        s+=path(f'M{c[0][0]} {c[0][1]}Q{c[1][0]-7} {c[1][1]-4} {c[2][0]} {c[2][1]}Q{c[3][0]-8} {c[3][1]-2} {c[4][0]} {c[4][1]}','#957744',2.5)
        s+=circle(c[-1][0],c[-1][1],3.5,'#957744')
    bx,by2=p(0,by,bz)
    s+=f'<ellipse cx="{p(0,by,0)[0]}" cy="{p(0,by,0)[1]}" rx="34" ry="11" fill="#53726c" opacity=".13"/>'
    s+=circle(bx,by2,35*scale,f'url(#{prefix}ball)')
    s+=f'<ellipse cx="{p(0,by,bz+34)[0]}" cy="{p(0,by,bz+34)[1]}" rx="6" ry="2.8" fill="#e5ddd3" stroke="#947e61" stroke-width="1"/>'
    # Two horizontal approach directions, shown on the walk plane.
    s+=line3((0,-115,3),(0,-50,3),'#688e90',3,'',f'marker-end="url(#{prefix}arrow)"')
    s+=line3((-120,0,3),(-51,0,3),'#688e90',3,'',f'marker-end="url(#{prefix}arrow)"')
    s+=text(103,444,'前方 / 两侧可接近；后方为支架区',13,MUTED)
    s+=leader((0,150,215),(401,80),'后置落地支柱',421,84)
    if hit:
        s+=leader((0,40,188),(377,157),'止挡结停在导孔',402,161)
        s+=leader((0,40,115),(402,250),'细绳限位',421,254)
        s+=leader((0,40,55),(384,352),'低位保留结果',405,356)
        s+=text(30,492,'球下移约 80 mm，仍被细绳留住，不滚进赛道。',14,INK)
    else:
        s+=leader((0,70,195),(377,128),'余绳在上方浅槽',405,132)
        s+=leader((0,0,173),(138,161),'包封小磁铁',28,157)
        s+=leader((0,0,135),(385,258),'Ø70 轻质软球',408,262)
        s+=text(30,492,'上磁点承担球重；限位绳有余量，不吊着球摆动。',14,INK)
    return s

def side(prefix='s'):
    # Exact orthographic proportions: side view maps Y horizontally and Z vertically.
    ox,oy,k=232,385,1.35
    def p(y,z): return round(ox+y*k,2),round(oy-z*k,2)
    def l(a,b,color='#668184',width=1,dash='',extra=''):
        A,B=p(*a),p(*b); return path(f'M{A[0]} {A[1]}L{B[0]} {B[1]}',color,width,dash,extra)
    def rect(y,z,w,h,fill):
        X,Y=p(y,z+h); return f'<rect x="{X}" y="{Y}" width="{w*k}" height="{h*k}" fill="{fill}"/>'
    def dimv(y,z1,z2,label,tx=None):
        X,Y1=p(y,z1); _,Y2=p(y,z2)
        return path(f'M{X} {Y1}V{Y2}','#668184',1,'',f'marker-start="url(#{prefix}dim)" marker-end="url(#{prefix}dim)"')+text(X-9 if tx is None else tx,(Y1+Y2)/2+5,label,13,'#45666d',500,'end')
    def dimh(z,y1,y2,label):
        X1,Y=p(y1,z); X2,_=p(y2,z)
        return path(f'M{X1} {Y}H{X2}','#668184',1,'',f'marker-start="url(#{prefix}dim)" marker-end="url(#{prefix}dim)"')+text((X1+X2)/2,Y-9,label,13,'#45666d',500,'middle')
    s=defs(prefix)
    s+=text(26,34,'03 / 侧视尺寸 · 参考初样',21,INK,650)
    s+=text(26,59,'全部单位 mm；Z = 0 为行走面，6 mm 地板不计入 H。',13,MUTED)
    s+=rect(-105,-6,320,6,'#d1ded9')+l((-105,0),(215,0),INK,1.5)
    s+=rect(140,0,20,230,ARM)+rect(-10,180,170,10,'#91a7a9')+rect(-6,170,12,10,'#cbb169')
    s+=rect(48,190,48,2,'#c9d8d0')
    X,Y=p(0,135); s+=circle(X,Y,35*k,f'url(#{prefix}ball)')
    X2,Y2=p(40,55); s+=circle(X2,Y2,35*k,'#e75e58'+'18' if False else '#f5d6d3','#c98179',1.2)
    s+=text(X2,Y2+4,'命中后',12,'#b3635c',500,'middle')
    s+=l((0,170),(40,180),'#957744',2.5)+l((40,180),(40,90),'#957744',2,'5 4')
    gx,gy=p(40,190); s+=circle(gx,gy,3,'#405a64')
    s+=path(f'M{gx} {gy}q13 -11 31 -3t30 -1','#957744',2.2)+circle(gx+61,gy-4,3,'#957744')
    s+=l((-87,0),(-35,0),LINE)+l((-87,135),(0,135),LINE,'1','4 4')
    s+=dimv(-85,0,135,'H = 135')
    s+=l((-65,170),(0,170),LINE,'1','4 4')+l((-65,180),(-10,180),LINE,'1','4 4')
    s+=text(22,105,'磁点接触高 170',13,'#45666d')+path('M138 101L184 155','#9db2b3',1)
    s+=text(22,126,'挑臂底高 180',13,'#45666d')+path('M138 123L215 142','#9db2b3',1)
    s+=dimv(95,55,135,'降 80',p(95,0)[0]-8)
    s+=l((0,135),(95,135),LINE,'1','4 4')+l((40,55),(95,55),LINE,'1','4 4')
    s+=dimv(114,0,20,'20',p(114,0)[0]+30)+l((40,20),(114,20),LINE,'1','4 4')
    s+=dimv(197,0,230,'支柱 230',p(197,0)[0]+88)
    s+=dimh(-28,0,150,'球心 → 支柱中心 150')+l((0,0),(0,-32),LINE)+l((150,0),(150,-32),LINE)
    s+=text(26,464,'球 Ø70 · 支柱截面示意 16 × 20 · 挑臂宽 20 / 厚 10',13,MUTED)
    s+=text(26,488,'导孔下口 (Y40, Z180) → 低位球顶 (Y40, Z90)：有效绳长 90',13,MUTED)
    s+=text(26,512,'待击直线段 ≈41.2；上方余绳 ≈48.8，须自由抽出且不打结。',13,MUTED)
    return s

def svg(w,h,body): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" style="font-family:Microsoft YaHei,PingFang SC,Arial,sans-serif">{body}</svg>'

ready=svg(660,515,scene(False,'r')); hit=svg(660,515,scene(True,'h')); detail=svg(680,540,side())
combined=defs('all')+'<rect width="1440" height="1250" fill="#f4f6f2"/>'
combined+=text(48,52,'CYBERBRICK / TARGET STUDY 06',14,MUTED,600)
combined+=text(48,99,'磁吸脱落球靶',34,INK,700)+text(1392,92,'构造方案 · 未实测 / 未生成新 STL',15,'#98693b',500,'end')
combined+=text(48,132,'命中判定：球脱离上磁点、落入低位。单纯晃动不算；人工挂回即可复位。',17,INK)
for x,title,body in [(38,'01 / 待击 · 球挂在高位',scene(False,'cr')),(742,'02 / 命中后 · 球留在低位',scene(True,'ch'))]:
    combined+=f'<rect x="{x}" y="167" width="660" height="558" rx="18" fill="white" stroke="{LINE}"/>'
    combined+=text(x+26,203,title,21,INK,650)+f'<g transform="translate({x} 211)">{body}</g>'
combined+=f'<rect x="38" y="745" width="760" height="455" rx="18" fill="white" stroke="{LINE}"/><g transform="translate(50 745) scale(.83)">{side("cs")}</g>'
combined+=text(845,786,'04 / 制作与调校边界',23,INK,650)
notes=[('轻球外购，支架可混合制作','软球顶部硬帽 + 钢片；磁铁包封留在挑臂。'),('磁力从弱到强逐级试打','薄纸垫调整磁隙；左右球质量与间隙一致。'),('135 是演示高度，110–170 为初样调节意向','挑臂须高于实测攻击最高点并留余量。'),('改高度后重新核对导孔、绳长与落差','满足 H − 落差 − 半径 ≥ 20；H110 时落差 ≤55。'),('旧地图保留，新模块需实机打样','旧 v05 筒靶 CAD 不适用；不保证任意命中必脱落。')]
for i,(a,b) in enumerate(notes): combined+=text(845,827+i*72,a,16,INK,650)+text(845,851+i*72,b,14,MUTED)
combined+=text(48,1230,'2026.10.13 · 红方打红球，蓝方打蓝球 · 本图是构造说明，接口、打印拆分与触发力尚未定型',14,MUTED)
(OUT/'target_detail.svg').write_text(svg(1440,1250,combined),encoding='utf-8')

html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>磁吸脱落球靶 · V06 构造说明</title><style>
:root{--ink:#263b42;--muted:#64777b;--line:#cfdbdc;--ball:#e75e58;--ball-light:#ff9791;--ball-dark:#ab3536}*{box-sizing:border-box}body{margin:0;background:#f4f6f2;color:var(--ink);font:15px/1.65 'Microsoft YaHei','PingFang SC',system-ui,sans-serif}.wrap{max-width:1480px;margin:auto;padding:30px 38px}header{display:flex;align-items:flex-end;justify-content:space-between;gap:24px}.eyebrow{font-size:11px;letter-spacing:2px;color:var(--muted);font-weight:650}h1{font-size:36px;line-height:1.3;letter-spacing:-1px;margin:9px 0 10px}p{margin:0}.subtitle{font-size:15px;color:var(--muted)}.badge{text-align:right;color:#98693b;font-size:13px;flex-shrink:0}.badge b{display:block;font-size:15px;margin-bottom:3px}.rule{border:1px solid #c4d9d5;background:#e9f1ec;padding:15px 19px;border-radius:10px;margin:22px 0 17px;display:flex;gap:13px;align-items:baseline}.rule b{white-space:nowrap}.rule span{font-size:14px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:15px;margin:18px 0}.group{display:flex;align-items:center;gap:7px;flex-wrap:wrap}.group>span{font-size:12px;color:var(--muted);margin-right:4px}button,a.download{font:inherit;font-size:13px;border:1px solid #bacccc;background:#fff;color:var(--ink);padding:7px 13px;border-radius:7px;cursor:pointer;text-decoration:none}button.active{background:#2c525a;color:#fff;border-color:#2c525a}button:focus-visible,a:focus-visible{outline:3px solid #b59460;outline-offset:3px}.color-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}.scenes{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{background:#fff;border:1px solid var(--line);border-radius:15px;overflow:hidden}.card h2{margin:21px 26px 0;font-size:20px;letter-spacing:-.3px}.card h2 span{font-size:12px;font-weight:400;color:var(--muted);margin-left:8px}.scene svg{display:block;width:100%;height:auto}.scene.single{grid-column:1/-1;max-width:900px;width:100%;margin:auto}.scenes.single-mode{grid-template-columns:1fr}.scene.hidden{display:none}.lower{display:grid;grid-template-columns:1.16fr 1fr;gap:22px;margin-top:22px}.drawing svg{width:100%;display:block}.notes{padding:23px 26px}.notes h2{margin:0 0 15px;font-size:21px}.notes dl{margin:0}.notes dt{font-size:14px;font-weight:700;margin-top:14px}.notes dd{font-size:13px;margin:4px 0 0;color:var(--muted)}.notes dt:first-child{margin-top:0}.spec{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:17px 0;margin-top:22px;gap:20px}.spec div{font-size:11px;color:var(--muted)}.spec b{display:block;font-size:21px;color:var(--ink);font-weight:650}.spec small{font-size:11px;font-weight:400}.foot{display:flex;justify-content:space-between;gap:22px;margin:20px 0 4px;font-size:12px;color:var(--muted)}.hint{font-size:12px;color:var(--muted);margin-top:14px}.steps{display:flex;gap:20px;padding:18px 0 0}.steps p{flex:1;font-size:13px}.steps b{display:block;margin-bottom:4px}.steps span{color:var(--muted)}@media(max-width:940px){.wrap{padding:22px}.scenes,.lower{grid-template-columns:1fr}header{display:block}.badge{text-align:left;margin-top:14px}.spec{grid-template-columns:1fr 1fr}.toolbar{align-items:flex-start;flex-direction:column}.foot{display:block}.scene.single{max-width:none}}@media(max-width:560px){h1{font-size:29px}.wrap{padding:18px 12px}.rule{display:block}.rule b{display:block;margin-bottom:5px}.steps{display:block}.steps p{margin-bottom:13px}.card h2{font-size:16px;margin:17px 17px 0}.card h2 span{display:block;margin-left:0}.notes{padding:19px}button,a.download{font-size:12px;padding:7px 10px}}@media print{.toolbar{display:none}.wrap{padding:10px}.scenes{grid-template-columns:1fr 1fr}.lower{grid-template-columns:1.16fr 1fr}.card{break-inside:avoid}body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style></head><body><main class="wrap"><header><div><div class="eyebrow">CYBERBRICK / TARGET STUDY 06 / 2026.10.13</div><h1>磁吸脱落球靶</h1><p class="subtitle">打中后从高位落到低位，结果一直保留到人工复位。</p></div><div class="badge"><b>构造方案 · 先做两套样机</b>未实测触发力 / 尚未生成新 STL</div></header><div class="rule"><b>判定只看结果</b><span>球脱离上方磁点，并落入低位，计为击倒。<b>单纯晃动不算。</b>红方打红球，蓝方打蓝球。</span></div><div class="toolbar"><div class="group"><span>显示</span><button class="active" data-state="both" aria-pressed="true">两态对照</button><button data-state="ready" aria-pressed="false">待击</button><button data-state="hit" aria-pressed="false">命中后</button></div><div class="group"><span>球色</span><button class="active" data-color="red" aria-pressed="true"><i class="color-dot" style="background:#e75e58"></i>红靶</button><button data-color="blue" aria-pressed="false"><i class="color-dot" style="background:#3c8dde"></i>蓝靶</button><a class="download" href="target_detail.svg" download>下载尺寸详图 SVG</a></div></div><section class="scenes" id="scenes"><article class="card scene" id="ready"><h2>01 / 待击 <span>磁点承担球重，细绳保留余量</span></h2>__READY__</article><article class="card scene" id="hit"><h2>02 / 命中后 <span>脱离磁点，由细绳留在低位</span></h2>__HIT__</article></section><p class="hint">轴测示意可看清构造；前方与左右侧开放，后方为支架区。箭头表示水平进攻方向，不代表机器人实际攻击高度或可达范围。</p><section class="spec"><div>球形 / 外购轻质软球<b>Ø70 <small>mm · 初样参考</small></b></div><div>参考待击球心高<b>135 <small>mm · 非实测</small></b></div><div>参考状态高低差<b>80 <small>mm · 本示例</small></b></div><div>示例低位球底离地<b>20 <small>mm</small></b></div></section><section class="lower"><article class="card drawing">__DETAIL__</article><article class="card notes"><h2>04 / 零件与调校</h2><dl><dt>轻球 + 顶部硬帽 + 小钢片</dt><dd>红、蓝使用同规格软球与硬帽。钢片固定在硬帽上；磁铁包封在支架内，脱落时留在上方。</dd><dt>后置支柱 + 挑臂 + 导孔</dt><dd>支架可用木条、金属条与少量打印件组合。固定点位于球后方；球前不设置凸起底座。图中截面只作构造示意，稳定性与固定接口待样机确认。</dd><dt>细绳 + 止挡结 + 上方开放浅槽</dt><dd>细绳一端连球顶，另一端穿导孔并打止挡结。待击时约 48.8 mm 余绳放在挑臂上方浅槽，须能自由抽出、不打结；不要在球旁留松绳环。</dd><dt>小磁铁 + 薄纸垫：调整释放难度</dt><dd>增加纸垫厚度可减弱吸力。先从弱吸力试起，兼顾正常行走振动不误脱与两种攻击可触发；不能保证任意命中都脱落。</dd><dt>高度与扫掠范围必须实测</dt><dd>135 mm 仅为模型参考；110–170 mm 是初样调节意向。挑臂底须高于实测攻击最高点并留设计余量，不能仅凭球顶高度推定安全。必要时升高挑臂，用短硬连接下探磁点；硬连接也须检查扫掠干涉。</dd></dl></article></section><section class="steps"><p><b>① 两种攻击分别试</b><span>旋转巴掌与往复出拳各从可达方向测试，再统一两靶释放难度。</span></p><p><b>② 调高度后复核绳长与落差</b><span>重新核对导孔高度、有效绳长与落差，满足 H − 落差 − 球半径 ≥ 20 mm。H = 110 时落差应 ≤55，不能照搬 80。</span></p><p><b>③ 装好再量有效绳段</b><span>90 mm 指导孔下口到球顶的止挡有效长，不含挑臂穿孔段、打结、硬帽连接与绕行补偿。</span></p></section><footer class="foot"><span>本轮明确靶模块形态；旧地图文件保留。旧 v05 筒靶 CAD 不适用本方案。</span><span>构造说明 / 尺寸假设待实测</span></footer></main><script>
document.querySelectorAll('[data-state]').forEach(b=>b.addEventListener('click',()=>{const state=b.dataset.state;document.querySelectorAll('[data-state]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b)});document.getElementById('scenes').classList.toggle('single-mode',state!=='both');['ready','hit'].forEach(id=>{document.getElementById(id).classList.toggle('hidden',state!=='both'&&state!==id);document.getElementById(id).classList.toggle('single',state!=='both')})}));document.querySelectorAll('[data-color]').forEach(b=>b.addEventListener('click',()=>{const c=b.dataset.color==='blue'?['#3c8dde','#9fcaff','#235b91']:['#e75e58','#ff9791','#ab3536'];['--ball','--ball-light','--ball-dark'].forEach((k,i)=>document.documentElement.style.setProperty(k,c[i]));document.querySelectorAll('[data-color]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b)})}));
</script></body></html>'''.replace('__READY__',ready).replace('__HIT__',hit).replace('__DETAIL__',detail)
(OUT/'index.html').write_text(html,encoding='utf-8')
print('Created index.html and target_detail.svg')
