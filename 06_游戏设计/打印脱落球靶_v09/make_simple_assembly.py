"""One practical assembly sheet from actual nine-part CAD; no CAD edits."""
from pathlib import Path
import runpy
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
ns=runpy.run_path(str(HERE/'render_printable.py'))
parts,render,font=ns['parts'],ns['render'],ns['font']
OUT=HERE/'球靶_安装示意_给组员.png'
W,H=1800,2390
canvas=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(canvas)
ink='#203b4e';gray='#516879';teal='#32969d'
d.text((35,20),'球靶怎么装｜编号与 STL 文件名一致',font=font(36),fill=ink)
d.text((35,78),'先装架子 → 放磁铁、封小盖 → 装托座 → 合球 → 吸上去',font=font(25),fill=gray)

def panel_title(x,y,t):
    ImageDraw.Draw(canvas).text((x+20,y+10),t,font=font(27),fill=ink)
def show(items,origin,size,camera,target,scale):
    im,p,w=render(items,size,camera,target,scale);canvas.paste(im,origin)
    def project(pos):
        a,b=p(pos);return a+origin[0],b+origin[1]
    return project,w
def label(p,pos,text,xy):
    d=ImageDraw.Draw(canvas);a,b=p(pos);x,y=xy
    d.line([(x+45,y+28),(a,b)],fill='#81949d',width=3)
    d.ellipse((a-4,b-4,a+4,b+4),fill=teal)
    bb=d.textbbox(xy,text,font=font(23));d.rectangle((bb[0]-4,bb[1]-3,bb[2]+4,bb[3]+3),fill='white')
    d.text(xy,text,font=font(23),fill=ink)

# Support assembly: the top-loaded sleeve and base have independent bolts.
panel_title(0,130,'A｜01 底座＋02 立柱＋03 套筒悬臂')
items=[(parts[n],c,1) for n,c in [('01_场地固定底座','#516b7f'),('02_三档立柱','#516b7f'),('03_套筒悬臂','#38a3aa')]]
p,w=show(items,(0,190),(900,700),(-200,-320,230),(50,0,82),102)
label(p,(110,25,4),'01 底座',(330,820))
label(p,(95,0,65),'02 立柱',(650,660))
label(p,(55,0,95),'03 悬臂',(30,470))
label(p,(95,-14.3,105),'M3×30 横穿，中间档',(540,365))
label(p,(95,-14.3,12),'M3×30 横穿',(30,760))
w.Finalize()

# Ball internals: real parts spaced along Z, preserving fitted diameters.
panel_title(900,130,'B｜球、两个封盖与定位环分别在哪里')
items=[]
for n,dz,c in [('07_球上半壳',40,'#e65c50'),('08_球壳定位环',14,'#d8bd8b'),
               ('09_球内磁铁封盖',15,'#dd8c66'),('06_球下半壳_带磁铁槽',0,'#e65c50'),
               ('04_磁铁托座_D4x2',-21,'#e9b454'),('05_托座磁铁封盖',-38,'#e9b454')]:
    m=parts[n].copy();m.apply_translation((0,0,dz));items.append((m,c,1))
p,w=show(items,(900,190),(900,700),(-180,-240,205),(0,0,132),80)
for pos,text,xy in [((0,0,190),'07 上半球',(930,205)),((0,0,149),'08 接缝定位环',(930,390)),
                     ((0,0,125),'09 薄圆盖：装球里面',(930,485)),((0,0,111),'06 下半球',(930,600)),
                     ((0,0,84),'04 托座：装在悬臂前端',(930,730)),((0,0,64),'05 厚圆盖：装托座底部',(930,840))]:
    label(p,pos,text,xy)
w.Finalize()

panel_title(0,920,'C｜04 翻过来看：磁铁从底部放进去')
p,w=show([(parts['04_磁铁托座_D4x2'],'#e9b454',1)],(0,985),(900,440),(-40,-60,58),(0,0,103),19)
label(p,(0,0,104.4),'先只放中心这一孔',(30,1020))
label(p,(-14,0,100),'两侧螺丝孔不是磁铁孔',(35,1330))
w.Finalize()

panel_title(900,920,'D｜06 开口朝上：另一枚磁铁放球内底部')
p,w=show([(parts['06_球下半壳_带磁铁槽'],'#e65c50',1)],(900,985),(900,440),(-30,-45,235),(0,0,122),34)
label(p,(0,0,109.6),'放中心孔，再用09盖住',(935,1030))
w.Finalize()

d=ImageDraw.Draw(canvas)
d.line((30,1460,1770,1460),fill='#b9c6cd',width=2)
lines=[
('1  装架子','02 插进 01 方槽；03 从立柱顶端套下。两处分别用 M3×30＋螺母锁住。'),
('2  放磁铁','04 倒放，中心孔放一枚 Ø4×2 磁铁；06 从球内中心孔放另一枚。'),
('3  封小盖','先确认两枚磁铁相吸，再把 05 粘在 04 底部、09 粘在 06 内部。'),
('4  装托座','04 放到 03 前端；两颗 M3×16 从上往下拧，螺母放 03 底面六角窝。'),
('5  合成球','08 放在 06 的大开口，露出约一半；扣上 07，把接缝胶合。'),
('6  放球','球放到 04 上吸住即可。球与托座之间不要涂胶，打中后球要能掉下。'),
]
for i,(heading,text) in enumerate(lines):
    y=1500+i*115
    d.text((40,y),heading,font=font(29),fill=ink)
    d.text((40,y+45),text,font=font(26),fill=gray)
d.text((40,2210),'方向：04 翼板端部小缺口、06 球侧小孔，都朝后面的立柱。',font=font(27),fill=ink)
d.text((40,2260),'先装中间档（球心135mm）；01 底座需要固定在场地上。先不用系绳。',font=font(26),fill=gray)
d.text((40,2310),'圆片别弄反：05 是厚的小圆盖；09 是薄的大圆盖；08 是空心圆环。',font=font(26),fill=gray)
canvas.save(OUT)
print(OUT)
