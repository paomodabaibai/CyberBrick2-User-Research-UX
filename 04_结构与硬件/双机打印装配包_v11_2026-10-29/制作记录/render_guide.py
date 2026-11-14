from pathlib import Path
import json
P=Path(__file__).resolve().parent.parent;SRC=P.parent/'巴掌外观简化_v11'
exec((SRC/'render_v11.py').read_text(encoding='utf-8').split('# Full robot views.')[0].replace('OUT=Path(__file__).resolve().parent','OUT=SRC'))
rows=json.loads((P/'制作记录/装配图对应.json').read_text(encoding='utf-8'))
allitems=items[:];original={n:m.copy() for n,m in meshes.items()}
meshes['02_竖置主板托架_布局草案']=trimesh.load_mesh(P/'制作记录/主板托架_装配坐标.stl')
original['02_竖置主板托架_布局草案']=meshes['02_竖置主板托架_布局草案'].copy()
def reset():
 global items,meshes
 items=[dict(o) for o in allitems];meshes={n:m.copy() for n,m in original.items()}
def colors(robot):
 colors={r['source_name']:r['color'] for r in rows if r['robot']==robot}
 for o in items:
  if o['name'] in colors:o['color']=colors[o['name']]
def move(n,xyz):meshes[n].apply_translation(xyz)
def title(im,t,sub='编号与打印文件名前缀一致；图为装配位置，不是打印摆放方向'):
 d=ImageDraw.Draw(im);d.text((30,20),t,font=font(30),fill='#243746');d.text((30,70),sub,font=font(19),fill='#526579')
# Overall white bodies and coloured feet/heads, same camera and no geometry change.
for robot,cn in [('palm','蓝色巴掌机'),('fist','红色拳头机')]:
 reset();colors(robot);im,ren,win=render(robot,'whole',(190,-240,135),(15,0,-3),112);title(im,cn+' · 配色与成品位置');im.save(P/'03_装配图'/(cn+'_配色.png'));win.Finalize()
# Common body exploded, electronics shown for orientation only.
reset();colors('palm');items=[o for o in items if o['group']=='common' and o['kind']!='envelope' and not o['name'].startswith('05_')]
for o in items:
 n=o['name']
 if n.startswith('R_Leg'):move(n,(0,0,-15))
 if n.startswith('R_foot'):move(n,(0,0,-35))
 if n.startswith('04_'):move(n,(22,0,0))
 if n.startswith(('02_','R01_')):move(n,(0,0,45))
 if n.startswith('R02_'):move(n,(0,0,80))
 if n.startswith(('03_','R03_')):move(n,(-48,0,15))
im,ren,win=render('palm','whole',(-210,-260,155),(-5,0,-20),135);title(im,'两台共用 · 身体、腿脚、主板与开关')
for pt,pos,t in [((0,-36,-18),(30,340),'C01 白色身体'),((-15,12,25),(790,190),'C02 主板托架：先锁板再放入'),((-83,-15,-5),(30,140),'C03 开关后面板：先装开关'),((18,0,65),(805,110),'电池：前方竖直放入'),((0,-25,-65),(800,640),'C04／C05 白色短腿'),(meshes['R_foot_-1'].center_mass,(800,840),'C06／C07 红／蓝脚板'),((60,-13,-13),(805,420),'C08／C09 黑色眼睛胶粘')]:label(im,ren,pt,pos,t)
im.save(P/'03_装配图/01_共用身体_分层安装.png');win.Finalize()
# Palm exploded stack.
reset();colors('palm');items=[o for o in items if o['group']=='palm']
shifts={'10_':(0,0,0),'11_':(0,0,12),'13_':(0,0,28),'12_':(-95,0,32),'14A':(0,-22,75),'14B':(0,22,75),'15_':(0,0,50),'P_04':(35,0,50),'R10_':(0,0,12),'R11_':(0,0,50)}
for o in items:
 for pref,v in shifts.items():
  if o['name'].startswith(pref):move(o['name'],v);break
im,ren,win=render('palm','whole',(190,-280,220),(10,0,60),130);title(im,'巴掌机 · B01–B08 分件位置')
for pt,pos,t in [((0,0,0),(30,915),'B01 底座：锁到身体'),((25,0,35),(820,780),'B02 舵机桥'),((-25,0,60),(30,600),'B03 新承重座（配B06）'),(meshes['14A_半片限位压环'].center_mass,(30,165),'B04／B05 两半压环'),((-95,0,55),(30,350),'B06 圆肩盖'),((36,0,94),(820,230),'B07 转盘＋接杆＋插芯一体'),((138,0,98),(800,480),'B08 手掌：干插对正后胶粘')]:label(im,ren,pt,pos,t)
im.save(P/'03_装配图/02_巴掌机_分层安装.png');win.Finalize()
# Fist exploded: gearbox references retained, no false instruction to print them all.
reset();colors('fist');items=[o for o in items if o['group']=='fist']
for o in items:
 n=o['name']
 if n.startswith('21_'):move(n,(-70,0,40))
 elif n=='F_crank':move(n,(0,0,55))
 elif n=='F_link':move(n,(0,0,80))
 elif n=='F_carriage':move(n,(0,0,40))
 elif n=='F_实际拳头腕杆':move(n,(35,0,40))
 elif n.startswith('F_ref'):move(n,(0,0,15))
im,ren,win=render('fist','whole',(180,-250,190),(-10,0,50),140);title(im,'拳头机 · R01–R06 分件位置')
for pt,pos,t in [((-10,-20,5),(30,900),'R01 底座：电机线走后端暗槽'),((-115,-28,48),(30,210),'R02 护罩：共用后两颗身体螺丝'),(meshes['F_crank'].center_mass,(30,440),'R03 曲柄：套减速输出轴'),((5,0,118),(790,170),'R04 连杆：两端活动铰接'),((8,0,85),(820,365),'R05 滑架：套两根金属导杆'),((90,0,85),(830,590),'R06 拳头腕杆：锁在滑架舌头'),((-35,0,30),(30,690),'灰色是完整电机减速箱，不是本包打印件')]:label(im,ren,pt,pos,t)
im.save(P/'03_装配图/03_拳头机_分层安装.png');win.Finalize()
import sys
if '--diagrams-only' in sys.argv:raise SystemExit('DIAGRAMS_UPDATED')
# Contact sheets use each transformed print STL, matching exactly what teammates open.
import math
printrows=json.loads((P/'制作记录/打印件与来源.json').read_text(encoding='utf-8'))
for robot,cn in [('palm','巴掌'),('fist','拳头')]:
 rr=[r for r in printrows if r['robot']==robot];sheet=Image.new('RGB',(1500,math.ceil(len(rr)/4)*310+90),'#f4f6f8');d=ImageDraw.Draw(sheet);d.text((25,20),cn+'机 · 文件认件图（每格各打1件）',font=font(30),fill='#243746')
 for i,r in enumerate(rr):
  m=trimesh.load_mesh(P/r['file']);center=m.bounds.mean(axis=0);size=max(m.extents)*.85+2
  items=[{'name':'part','group':robot,'kind':'part','color':{'白色':'#dadfe3','蓝色':'#399ade','红色':'#df5357','黑色':'#28313b'}[r['color']]}];meshes={'part':m}
  im,ren,win=render(robot,'whole',tuple(center+np.array([1,-1,1])*(size*3)),tuple(center),size)
  thumb=im.resize((340,260));x=(i%4)*375+15;y=(i//4)*310+85;sheet.paste(thumb,(x,y));d.text((x,y+262),r['id']+' '+r['name'],font=font(17),fill='#243746');win.Finalize()
 sheet.save(P/'03_装配图'/(cn+'机_文件认件图.png'))
print('ASSEMBLY_IMAGES_COMPLETE',flush=True)
