"""Actual CAD concept meshes; no manufacturing or collision validation implied."""
from pathlib import Path
import json
import numpy as np
import cadquery as cq
import trimesh
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
def box(x,y,z,c):
    return cq.Workplane('XY').box(x,y,z).translate(c)
def cyl(r,h,c):
    return cq.Workplane('XY').circle(r).extrude(h).translate(c)
def mesh(s):
    v,f=s.val().tessellate(.18,.18)
    return trimesh.Trimesh([p.toTuple() for p in v],f,process=True)

# X points from target toward rear support; all dimensions are above arena surface.
ball=cq.Workplane('XY').sphere(30).translate((0,0,135))
ball=ball.intersect(box(70,70,65,(0,0,139.5))) # flat bottom at 107
ball=ball.cut(cq.Workplane('XY').sphere(28.4).translate((0,0,135)))
# The inner sphere would open the bottom; add a small closed contact pad.
ball=ball.union(cyl(12,2.5,(0,0,107)))
seat=cyl(11,5,(0,0,101)).cut(cyl(4.2,2.1,(0,0,104)))
arm=box(96,16,8,(47,0,97)).union(box(20,30,24,(95,0,103)))
post=box(18,20,157,(95,0,82.5))
post=post.cut(box(8,24,55,(95,0,105)))
base=box(85,70,4,(90,0,2))
for x in (57,123):
    for y in (-26,26): base=base.cut(cyl(2,6,(x,y,-1)))
base=base.union(box(26,28,8,(95,0,8)))
parts=[('球壳',ball,'#e35e52'),('磁吸托座',seat,'#f0b34b'),
       ('悬臂与调高滑块',arm,'#46a9af'),('后立柱',post,'#4d6577'),
       ('固定底座',base,'#60798a'),('磁铁示意',cyl(4,2,(0,0,104.5)),'#4a4b50'),
       ('钢片示意',cyl(8,.5,(0,0,107)),'#b4bbc2')]
meshes=[(n,mesh(s),c) for n,s,c in parts]
scene=trimesh.Scene()
for n,m,c in meshes:
    mm=m.copy();mm.visual.vertex_colors=[int(c[j:j+2],16) for j in (1,3,5)]+[255]
    scene.add_geometry(mm,node_name=n)
scene.export(OUT/'球靶概念总装_不可直接打印.glb')
cq.exporters.export(cq.Compound.makeCompound([s.val() for _,s,_ in parts]),str(OUT/'球靶概念总装_不可直接打印.step'))
trimesh.util.concatenate([m for _,m,_ in meshes]).export(OUT/'球靶概念总装_不可直接打印.stl')

def render(size,camera,target,scale):
    ren=vtk.vtkRenderer();ren.SetBackground(.96,.97,.98)
    for n,m,c in meshes:
        pd=vtk.vtkPolyData();pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.array(m.vertices),deep=True));pd.SetPoints(pts)
        cells=vtk.vtkCellArray();cells.SetCells(len(m.faces),numpy_to_vtkIdTypeArray(np.column_stack((np.full(len(m.faces),3),m.faces)).astype(np.int64).ravel(),deep=True));pd.SetPolys(cells)
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(pd)
        a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*[int(c[j:j+2],16)/255 for j in (1,3,5)])
        a.GetProperty().SetAmbient(.3);a.GetProperty().SetDiffuse(.7);ren.AddActor(a)
    cam=ren.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(*target);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(True);win.SetSize(*size);win.AddRenderer(ren);win.SetMultiSamples(4);ren.ResetCameraClippingRange();win.Render()
    grab=vtk.vtkWindowToImageFilter();grab.SetInput(win);grab.ReadFrontBufferOff();grab.Update()
    arr=vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars()).reshape(size[1],size[0],-1)
    im=Image.fromarray(np.flipud(arr)[:,:,:3].copy())
    def project(p):
        ren.SetWorldPoint(*p,1);ren.WorldToDisplay();a,b,_=ren.GetDisplayPoint();return int(a),int(size[1]-b)
    return im,project,win

font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
canvas=Image.new('RGB',(1800,1100),'#f5f8fa');d=ImageDraw.Draw(canvas)
d.text((45,25),'打印脱落球靶 · 第一版结构粗模',font=font(36),fill='#223e50')
d.text((45,80),'球心 135 mm / 球径 60 mm / 后置支架 / 底部磁吸',font=font(24),fill='#526979')
im,p,w=render((900,760),(-220,-340,230),(40,0,85),110)
canvas.paste(im,(0,140));d=ImageDraw.Draw(canvas)
for label,pos,anchor in [('薄壁球壳',(0,0,145),(45,160)),('底部磁吸座',(0,0,105),(30,460)),('调高滑块',(95,0,112),(660,170)),('后立柱',(95,0,65),(650,550)),('固定底座',(90,0,4),(440,810))]:
    x,y=p(pos);x,y=x,y+140;ax,ay=anchor
    d.line([(ax+70,ay+30),(x,y)],fill='#718594',width=2);d.ellipse((x-4,y-4,x+4,y+4),fill='#243d4b');d.text((ax,ay),label,font=font(23),fill='#223e50')
w.Finalize()
im,p,w=render((900,760),(40,-400,85),(40,0,85),110)
canvas.paste(im,(900,140));d=ImageDraw.Draw(canvas)
for lo,hi,col,label,xworld in [(112.3,167.8,'#278aa8','巴掌 112–168',-45),(114.9,155.8,'#bd5548','拳头前端 115–156',-70)]:
    x,y1=p((xworld,0,lo));_,y2=p((xworld,0,hi));x+=900;y1+=140;y2+=140
    d.line((x,y1,x,y2),fill=col,width=7)
    d.text((x-85,y1+(50 if lo==112.3 else 15)),label,font=font(19),fill=col)
x,y=p((0,0,135));x+=900;y+=140
d.line((x,y,x+205,y),fill='#8d9ca7',width=2);d.text((x+75,y-35),'球心 135',font=font(22),fill='#223e50')
d.text((1240,160),'侧视 · 左侧为攻击方向',font=font(23),fill='#223e50')
w.Finalize()
d.text((45,950),'命中：球体从磁吸座脱离 → 原位变空 → 人工放回',font=font(27),fill='#223e50')
d.text((45,1000),'概念预览：滑块锁紧、球壳分件、磁铁封盖及防滚结构尚未细化；底座需固定到场地。',font=font(22),fill='#647784')
canvas.save(OUT/'球靶粗模_整体与高度.png')
(OUT/'粗模说明.md').write_text('''# 打印球靶粗模\n用户已授权先建模查看大概效果。\n\n本轮生成真实CAD的STEP、GLB和STL总装，以及标注预览图。均为概念模型，不是可直接制造的打印包。\n\n球径60，球心135，最低球底平面107；磁铁顶106.5，钢片下107，间隙0.5为示意。后柱中心距离球心95，底座85×70，球前无落地底盘。球壳名义壁厚1.6，但底部加厚连接区尚需细化。\n\n立柱槽为调高示意：滑块当前与立柱有几何交叠，尚未做导向孔、锁紧螺丝和限位。高度120–150目标尚未结构验算。球壳未分成两半，钢片座与封盖未定，不能直接打印总装。\n\n图中高度条是静态网格包络，不代表通过碰撞或实际命中验证。60mm球的下沿约105，实际削平至107；悬臂顶101，留在已测静态攻击范围下方，但动态倾斜仍需检查。后柱95mm偏置是初样提案，不是经过完整机器人扫掠验证的净空。\n\n脱落后的防滚/限位方案尚未纳入粗模。先审阅外形、球大小及底座布局，再细化制造。\n''',encoding='utf-8')
print('Created CAD concept and annotated preview:',OUT)

