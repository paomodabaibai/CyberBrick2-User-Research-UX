"""Generate the two plans and an offline, single-level arena preview."""
from pathlib import Path
import json, math

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'arena_layouts.json').read_text(encoding='utf-8'))
BLUE='#2975a6'; RED='#ca5848'; INK='#294340'; WALL='#8b9580'
def text(x,y,s,size=17,color=INK,anchor='start'):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{s}</text>'
def poly(points,fill,stroke='none',sw=1,opacity=1):
    return f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in points)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>'
def begin(w,h,title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{title}" font-family="Microsoft YaHei,sans-serif"><title>{title}</title>'
def robot_corners(r):
    a=math.radians(r['heading_deg']); c,s=math.cos(a),math.sin(a)
    return [(r['x']+x*c-y*s,r['y']+x*s+y*c) for x,y in [(-83.935,-57),(123.273,-57),(123.273,57),(-83.935,57)]]
def flat(layout):
    o=[begin(1000,715,'单层落地墙体地图 '+layout['name']),text(50,36,layout['name']+' / 900 × 540 mm',23)]
    o.append('<g transform="translate(50 72)"><rect width="900" height="540" fill="#eef1e7" stroke="#bbc4b4"/>')
    for x in range(180,900,180):o.append(f'<path d="M{x} 0V540" stroke="#cbd3c3"/>')
    for y in (180,360):o.append(f'<path d="M0 {y}H900" stroke="#cbd3c3"/>')
    for r in D['robots']:
        col=BLUE if r['owner']=='blue' else RED;t=next(t for t in D['targets'] if t['id']==r['target'])
        o.append(f'<path d="M{r["x"]} {r["y"]}H{t["x"]}" stroke="{col}" stroke-dasharray="9 7" stroke-width="2"/>')
        o.append(poly(robot_corners(r),col,col,1.6,.16))
        direction=1 if r['heading_deg']==0 else -1
        o.append(poly([(r['x']-direction*17,r['y']-19),(r['x']+direction*36,r['y']),(r['x']-direction*17,r['y']+19)],col))
        o.append(text(r['x'],r['y']+80,r['id']+' 起点',18,col,'middle'))
    for t in D['targets']:
        col=BLUE if t['owner']=='blue' else RED
        o.append(f'<circle cx="{t["x"]}" cy="{t["y"]}" r="40" fill="{col}"/>')
        o.append(text(t['x'],t['y']+6,t['id'],19,'white','middle'))
        o.append(text(t['x'],t['y']-58,t['attacker']+' 打这枚',16,INK,'middle'))
    for w in layout['walls']:
        o.append(f'<rect x="{w["x"]-80}" y="{w["y"]-20}" width="160" height="40" rx="4" fill="{WALL}"/>')
    o.append(text(450,278,'墙',14,'white','middle') if layout['id']=='divider' else text(450,277,'中央净开口 560',17,INK,'middle'))
    o.append('</g>'+text(50,651,'墙 160 × 40 × 高60 · 靶 Ø80 × 高160 · 底面都直接接地',17)+text(50,681,'路线开局摆正，约6cm接近量为模型估算；不设置必须绕墙的任务。',16))
    return ''.join(o)+'</svg>'

def proj(x,y,z=0):return (405+(x-y)*.66,100+(x+y)*.32-z*.86)
def box(x,y,l,w,h):
    a,b,c,d=[proj(xx,yy) for xx,yy in [(x-l/2,y-w/2),(x+l/2,y-w/2),(x+l/2,y+w/2),(x-l/2,y+w/2)]]
    aa,bb,cc,dd=[proj(xx,yy,h) for xx,yy in [(x-l/2,y-w/2),(x+l/2,y-w/2),(x+l/2,y+w/2),(x-l/2,y+w/2)]]
    return poly([b,c,cc,bb],'#65725f')+poly([c,d,dd,cc],'#7c8970')+poly([aa,bb,cc,dd],'#a1ae90','#6f7c67',.5)
def tower(t):
    x,y=t['x'],t['y']; col=BLUE if t['owner']=='blue' else RED; N=40; out=[]
    # Draw only the near-facing outer half of the round, floor-standing shell.
    for i in range(N):
        a=i*math.tau/N;b=(i+1)*math.tau/N
        if math.cos((a+b)/2)+math.sin((a+b)/2)<0:continue
        pts=[proj(x+40*math.cos(q),y+40*math.sin(q),z) for q,z in [(a,0),(b,0),(b,160),(a,160)]]
        out.append(poly(pts,col,col,.35))
    outer=[proj(x+40*math.cos(i*math.tau/N),y+40*math.sin(i*math.tau/N),160) for i in range(N)]
    inner=[proj(x+39.2*math.cos(i*math.tau/N),y+39.2*math.sin(i*math.tau/N),160) for i in range(N)]
    out.append(poly(outer,col)+poly(inner,'#43554e'))
    px,py=proj(x,y,177);out.append(text(px,py,t['id']+' · '+('蓝靶' if t['owner']=='blue' else '红靶'),19,col,'middle'))
    return ''.join(out)
def iso(layout):
    o=[begin(1060,720,'单层落地墙体立体总览 '+layout['name']),text(36,35,'单层地面 · 两片落地矮墙',23)]
    for y in range(0,540,180):
        for x in range(0,900,180):
            o.append(poly([proj(x,y),proj(x+180,y),proj(x+180,y+180),proj(x,y+180)],'#edf0e5','#b9c6b2',1))
    for r in D['robots']:
        col=BLUE if r['owner']=='blue' else RED;target=next(t for t in D['targets'] if t['id']==r['target'])
        p1=proj(r['x'],r['y']);p2=proj(target['x'],target['y'])
        o.append(f'<path d="M{p1[0]} {p1[1]}L{p2[0]} {p2[1]}" stroke="{col}" stroke-width="2" stroke-dasharray="8 6"/>')
        o.append(poly([proj(x,y) for x,y in robot_corners(r)],col,col,1.5,.2))
        dir=1 if r['heading_deg']==0 else -1
        o.append(poly([proj(r['x']-dir*17,r['y']-22),proj(r['x']+dir*40,r['y']),proj(r['x']-dir*17,r['y']+22)],col))
    objects=[(w['x']+w['y'],box(w['x'],w['y'],160,40,60)) for w in layout['walls']]
    objects += [(t['x']+t['y'],tower(t)) for t in D['targets']]
    for _,s in sorted(objects):o.append(s)
    for r in D['robots']:
        col=BLUE if r['owner']=='blue' else RED
        p=proj(r['x'],r['y']+(-95 if r['id']=='A' else 87))
        o.append(text(*p,r['id']+' 起点',18,col,'middle'))
    o.append(text(36,622,'墙高 60 mm；目标从地面立起，高 160 mm。',20)+text(36,656,'机器人用平面色块表示占地；行走区全部在同一平面。',17)+text(36,688,'按尺寸绘制的构造示意；圆角和打印细节见组件文件。',15,'#637365'))
    return ''.join(o)+'</svg>'

TEMPLATE='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>落地墙体竞技场 v04</title><style>
*{box-sizing:border-box}body{margin:0;background:#faf9f3;color:#294340;font-family:"Microsoft YaHei",system-ui,sans-serif}main{max-width:1100px;padding:26px;margin:auto}.eyebrow{font-size:13px;color:#75816e}h1{font-size:clamp(25px,4vw,38px);margin:14px 0}p{font-size:15px;line-height:1.85;margin:8px 0 20px}.blue{color:#2975a6}.red{color:#ca5848}.bar{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;margin:18px 0}.group{display:flex;gap:7px}button{font:inherit;font-size:14px;color:#294340;background:transparent;border:1px solid #cbd2c3;border-radius:6px;padding:9px 14px;cursor:pointer}button[aria-pressed=true]{background:#294340;border-color:#294340;color:#faf9f3}button:focus-visible,a:focus-visible{outline:3px solid #a1b397;outline-offset:3px}.stage{border:1px solid #d8dfd0;border-radius:10px;background:#f1f3eb;overflow:auto}.stage svg{display:block;width:100%;height:auto}.caption{color:#68785f;font-size:14px;margin:12px 0 22px}.notes{display:grid;grid-template-columns:1fr 1fr 1fr;gap:22px;border-top:1px solid #d8dfd0;padding-top:20px}.notes strong{font-size:16px}.notes p{font-size:14px;margin:7px 0 0}footer{margin-top:22px;border-top:1px solid #d8dfd0;padding-top:16px;line-height:1.9;font-size:13px;color:#68785f}a{color:#3b7054;text-underline-offset:3px}.links{display:flex;gap:12px 22px;flex-wrap:wrap;margin-bottom:12px}@media(max-width:650px){main{padding:18px 14px}.notes{grid-template-columns:1fr;gap:18px}.stage svg{min-width:560px}.caption{margin-bottom:17px}.bar{margin:14px 0}.group button{padding:8px 11px}}
</style></head><body><main><div class="eyebrow">CYBERBRICK / v04 / 2026.10.12</div><h1>单层平地 · 落地墙体</h1><p><span class="blue">蓝 A 打红 TB</span>，<span class="red">红 B 打蓝 TA</span>。两片矮墙限制横向穿行，正面攻靶保持短直线；两枚竖靶也直接放在地面。</p><div class="bar"><div class="group" aria-label="墙体布局"><button data-layout="divider" aria-pressed="true">中央短墙</button><button data-layout="opening" aria-pressed="false">中央开口</button></div><div class="group" aria-label="查看方式"><button data-view="iso" aria-pressed="true">立体总览</button><button data-view="flat" aria-pressed="false">平面划区</button></div></div><div class="stage" id="stage"></div><p class="caption" id="caption"></p><section class="notes"><div><strong>只用两片落地墙</strong><p>每片160×40×60mm，换位置即可改变空间限制。行走面保持同一高度。</p></div><div><strong>一人只打一枚敌靶</strong><p>竖靶Ø80×160mm，整枚侧倒算击倒。蓝打红、红打蓝；先有效击倒者赢。</p></div><div><strong>仍然照顾转弯困难</strong><p>开局摆正，估算约6cm接近。不要求绕墙、穿窄门或反复纠偏。</p></div></section><footer><div class="links"><a href="策划与制作说明.md">策划与尺寸</a><a href="../../04_结构与硬件/落地墙体竞技场_v04/README.md">墙体与竖靶组件</a><a href="../../04_结构与硬件/落地墙体竞技场_v04/试打印组件包_v04.zip">试打印包</a><a href="地图_divider.svg">平面图</a></div>先用平桌试墙与竖靶，再决定打印完整15块地板。此版替代上一版悬挂摇摆台；全部结构接地，无架空结构。墙边净空、实际攻击高度与倒靶手感尚待实测。</footer></main><script>
const diagrams=__DIAGRAMS__,layouts=__LAYOUTS__;let activeLayout='divider',activeView='iso';function show(){document.getElementById('stage').innerHTML=diagrams[activeLayout][activeView];document.getElementById('caption').textContent=layouts.find(x=>x.id===activeLayout).description;document.querySelectorAll('[data-layout]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.layout===activeLayout)));document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===activeView)));}document.querySelectorAll('[data-layout]').forEach(b=>b.addEventListener('click',()=>{activeLayout=b.dataset.layout;show();}));document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{activeView=b.dataset.view;show();}));show();
</script></body></html>'''

if __name__=='__main__':
    drawings={l['id']:{'flat':flat(l),'iso':iso(l)} for l in D['layouts']}
    for id,views in drawings.items():(ROOT/f'地图_{id}.svg').write_text(views['flat'],encoding='utf-8')
    (ROOT/'立体总览.svg').write_text(drawings['divider']['iso'],encoding='utf-8')
    html=TEMPLATE.replace('__DIAGRAMS__',json.dumps(drawings,ensure_ascii=False)).replace('__LAYOUTS__',json.dumps(D['layouts'],ensure_ascii=False))
    (ROOT/'地图与立体预览.html').write_text(html,encoding='utf-8')
    print('Generated 3 SVGs and offline HTML.')
