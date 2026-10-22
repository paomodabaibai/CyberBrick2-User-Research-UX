"""Annotated manufacturing assembly renders from exported geometry."""
from pathlib import Path
import json
import numpy as np
import trimesh,vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent/'制造初样_v01'
OUT=ROOT/'04_总装与检查'
s=trimesh.load(OUT/'总装135mm_仅预览.glb',force='scene')
report=json.loads((OUT/'几何检查报告.json').read_text(encoding='utf-8'))
parts={}
for n in s.graph.nodes_geometry:
    t,g=s.graph[n];m=s.geometry[g].copy();m.apply_transform(t)
    parts[n]=m
def cylinder(r,l,pos,axis=(0,0,1)):
    m=trimesh.creation.cylinder(radius=r,height=l,sections=24)
    m.apply_transform(trimesh.geometry.align_vectors([0,0,1],axis));m.apply_translation(pos);return m
hardware=[]
for z in (12,105):
    hardware.extend([(cylinder(1.5,30,(95,.2,z),(0,1,0)),'#c1c7ce',1),
                     (cylinder(2.85,3,(95,-15.8,z),(0,1,0)),'#c1c7ce',1),
                     (cylinder(3,2.4,(95,13,z),(0,1,0)),'#c1c7ce',1)])
for x in (-14,14):hardware.extend([(cylinder(1.5,16,(x,0,94)),'#c1c7ce',1),(cylinder(2.85,3,(x,0,103.5)),'#c1c7ce',1)])
objects=[(m,report['parts'][n]['color'],1) for n,m in parts.items()]+hardware
def render(items,size,camera,target,scale):
    ren=vtk.vtkRenderer();ren.SetBackground(.961,.973,.98)
    for m,c,opacity in items:
        pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.asarray(m.vertices),deep=True))
        pd=vtk.vtkPolyData();pd.SetPoints(pts)
        cells=vtk.vtkCellArray();cells.SetCells(len(m.faces),numpy_to_vtkIdTypeArray(np.column_stack((np.full(len(m.faces),3),m.faces)).astype(np.int64).ravel(),deep=True));pd.SetPolys(cells)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(pd);a=vtk.vtkActor();a.SetMapper(mapper)
        a.GetProperty().SetColor(*[int(c[j:j+2],16)/255 for j in (1,3,5)]);a.GetProperty().SetOpacity(opacity);a.GetProperty().SetAmbient(.3);a.GetProperty().SetDiffuse(.7)
        ren.AddActor(a)
    cam=ren.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(*target);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(True);win.SetSize(*size);win.AddRenderer(ren);win.SetMultiSamples(4);ren.ResetCameraClippingRange();win.Render()
    grab=vtk.vtkWindowToImageFilter();grab.SetInput(win);grab.ReadFrontBufferOff();grab.Update()
    data=vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars()).reshape(size[1],size[0],-1)
    im=Image.fromarray(np.flipud(data)[:,:,:3].copy())
    def project(point):
        ren.SetWorldPoint(*point,1);ren.WorldToDisplay();x,y,_=ren.GetDisplayPoint();return int(x),int(size[1]-y)
    return im,project,win
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
def title(canvas,main,sub):
    d=ImageDraw.Draw(canvas);d.text((35,20),main,font=font(34),fill='#203b4e');d.text((35,73),sub,font=font(22),fill='#627482')
def label(d,p,pos,text,xy,offset=(0,120)):
    x,y=p(pos);x+=offset[0];y+=offset[1];ax,ay=xy
    d.line([(ax+40,ay+27),(x,y)],fill='#8a9da9',width=2);d.ellipse((x-3,y-3,x+3,y+3),fill='#203b4e')
    bbox=d.textbbox(xy,text,font=font(22));d.rectangle((bbox[0]-4,bbox[1]-3,bbox[2]+4,bbox[3]+3),fill='#f5f8fa');d.text(xy,text,font=font(22),fill='#203b4e')

canvas=Image.new('RGB',(1800,1100),'#f5f8fa')
title(canvas,'三档磁吸球靶 · 可打印初样','九件主体 / Ø60 mm / 球心 125、135、145 mm / 套件 Ø4×2 磁铁')
im,p,w=render(objects,(1020,840),(-210,-340,235),(40,0,83),108)
canvas.paste(im,(0,120));d=ImageDraw.Draw(canvas)
for text,pos,xy in [('06＋07 球壳',(0,0,145),(50,160)),('04 磁铁托座',(0,0,103),(30,510)),('03 套筒悬臂',(70,0,94),(570,510)),('02 三档立柱',(95,0,65),(650,700)),('01 固定底座',(110,25,3),(440,900))]:label(d,p,pos,text,xy)
w.Finalize()
close=[(parts['02_三档立柱'],'#516b7f',1),(parts['03_套筒悬臂'],'#38a3aa',.32)]+hardware[3:6]
im,p,w=render(close,(740,570),(170,-170,160),(95,0,108),38)
canvas.paste(im,(1040,170));d=ImageDraw.Draw(canvas)
d.text((1100,130),'透视示意：螺栓穿过套筒与立柱',font=font(23),fill='#203b4e')
d.text((1090,770),'M3×30 ＋ 普通 M3 六角螺母',font=font(25),fill='#203b4e')
d.text((1090,820),'拔出 → 移动一档 → 穿回拧紧',font=font(23),fill='#203b4e')
d.text((1090,865),'整臂从立柱顶端套入，孔距 10 mm',font=font(22),fill='#627482');w.Finalize()
d.text((35,1000),'先打小样，再打一套试装；图中银色件为金属螺丝，不是打印件。',font=font(24),fill='#526979')
canvas.save(OUT/'01_总装与调高锁紧.png')

# Ball components separated along Z, keeping true sizes.
expl=[]
offsets={'04_磁铁托座_D4x2':-20,'05_托座磁铁封盖':-35,'06_球下半壳_带磁铁槽':0,
         '09_球内磁铁封盖':20,'08_球壳定位环':12,'07_球上半壳':35}
for n,dz in offsets.items():
    m=parts[n].copy();m.apply_translation((0,0,dz));expl.append((m,report['parts'][n]['color'],1))
for x,y in report['magnet_positions_xy']:expl.append((cylinder(2,2,(x,y,119)),'#53585e',1))
canvas=Image.new('RGB',(1500,1100),'#f5f8fa')
title(canvas,'球壳与磁吸座 · 拆解装配','两侧磁铁相吸；先试装极性与吸力，再封盖、合球')
im,p,w=render(expl,(900,880),(-180,-230,200),(0,0,133),75)
canvas.paste(im,(0,120));d=ImageDraw.Draw(canvas)
for text,pos,xy in [('07 上半球',(0,0,190),(40,170)),('08 定位环',(0,0,148),(40,370)),('09 球内封盖',(0,0,130),(40,510)),('06 下半球',(0,0,110),(40,660)),('04 托座',(0,0,83),(40,800)),('05 托座底盖',(0,0,67),(40,940))]:label(d,p,pos,text,xy)
w.Finalize()
d.text((950,200),'磁铁：Ø4×2 mm',font=font(27),fill='#203b4e')
for i,line in enumerate(['从中间 1 对开始（共 2 枚）','仍太松：改外圈三角形 3 对','太紧：接触面加 0.4 / 0.8 mm 垫片','','磁铁全部藏在塑料里面','球壳接缝用定位环胶合','后侧小孔可备用系绳','','先确认磁极相吸，再粘封盖','不要把球粘到磁铁托座上']):
    d.text((950,270+i*50),line,font=font(22),fill='#526979')
canvas.save(OUT/'02_球壳与磁铁座拆解.png')

# Contact sheet of print-ready orientations, numbered identically to files.
canvas=Image.new('RGB',(1800,1400),'#f5f8fa');title(canvas,'一套需要打印的九个零件','文件已经摆成建议打印朝向；两个球靶各一套。小样与减磁垫片另放在 01_先打小样。')
for i,n in enumerate(sorted(parts)):
    m=trimesh.load(ROOT/report['parts'][n]['file'],force='mesh');center=m.bounds.mean(axis=0);scale=max(m.extents)*.7+5
    im,p,w=render([(m,report['parts'][n]['color'],1)],(570,345),center+np.array([140,-180,150]),center,scale)
    x=15+(i%3)*595;y=135+(i//3)*415;canvas.paste(im,(x,y));d=ImageDraw.Draw(canvas)
    d.text((x+15,y+348),n,font=font(24),fill='#203b4e');w.Finalize()
canvas.save(OUT/'03_九件打印清单.png')
print('Rendered assembly, exploded magnet interface, and nine-part contact sheet')
