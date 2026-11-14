from pathlib import Path
import json,numpy as np,trimesh,vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
items=json.loads((OUT/'装配清单.json').read_text(encoding='utf-8'))
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
meshes={o['name']:trimesh.load_mesh(OUT/'装配网格'/o['file']) for o in items}
def actor(m,c,alpha=1):
 pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.asarray(m.vertices,dtype=np.float32),deep=True))
 cells=vtk.vtkCellArray();cells.SetCells(len(m.faces),numpy_to_vtkIdTypeArray(np.column_stack((np.full(len(m.faces),3),m.faces)).astype(np.int64).ravel(),deep=True))
 poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly)
 a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*[int(c[i:i+2],16)/255 for i in (1,3,5)])
 a.GetProperty().SetOpacity(alpha);a.GetProperty().SetAmbient(.32);a.GetProperty().SetDiffuse(.68)
 return a
def render(variant,mode,camera,target,scale):
 ren=vtk.vtkRenderer();ren.SetBackground(.96,.97,.98)
 for o in items:
  if o['group'] not in ('common',variant):continue
  if o['kind']=='envelope':continue
  name=o['name'];alpha=1
  if mode=='inside':
   if o['group']!='common' or name.startswith('R_Leg') or name.startswith('R_foot'):continue
   if o['kind']=='body':alpha=.12
  if mode=='wire':
   if o['group']=='common':continue
   if name in ('F_实际拳头腕杆','21_拳头轻量侧护罩'):continue
  ren.AddActor(actor(meshes[name],o['color'],alpha))
 cam=ren.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(*target);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(True);win.SetSize(1300,1050);win.SetMultiSamples(4);win.AddRenderer(ren);win.Render()
 grab=vtk.vtkWindowToImageFilter();grab.SetInput(win);grab.ReadFrontBufferOff();grab.Update();a=vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars()).reshape(1050,1300,3)
 im=Image.fromarray(np.flipud(a).copy())
 return im,ren,win
def label(im,ren,point,pos,text,color='#243746'):
 d=ImageDraw.Draw(im);ren.SetWorldPoint(*point,1);ren.WorldToDisplay();x,y,_=ren.GetDisplayPoint();y=im.height-y
 d.line((x,y,pos[0],pos[1]+18),fill=color,width=3);d.ellipse((x-4,y-4,x+4,y+4),fill=color)
 b=d.textbbox(pos,text,font=font(23));d.rectangle((b[0]-6,b[1]-4,b[2]+6,b[3]+4),fill='white');d.text(pos,text,font=font(23),fill=color)

# Full robot views.
for variant,cn in [('palm','巴掌'),('fist','拳头')]:
 im,ren,win=render(variant,'whole',(190,-240,135),(15,0,-3),112)
 d=ImageDraw.Draw(im);d.text((38,24),cn+'机器人 v06 · 连接结构修订',font=font(31),fill='#1c3445')
 d.text((38,75),'延续原高39mm布局；接口试验模型，未发布打印版',font=font(21),fill='#5a6771')
 im.save(OUT/'预览'/(cn+'_整机.png'));win.Finalize()
# Palm exploded diagram with original horn and a split retaining cap.
saved_items=items;saved_meshes={n:m.copy() for n,m in meshes.items()}
items=[o for o in items if o['group']=='palm' and (o['name'].startswith(('11_','13_','14','15_','R10_','R11_')))]
for o in items:
 n=o['name']
 if n.startswith('15_'):meshes[n].apply_translation((0,0,20))
 if n.startswith('14A'):meshes[n].apply_translation((0,-8,43))
 if n.startswith('14B'):meshes[n].apply_translation((0,8,43))
im,ren,win=render('palm','whole',(150,-180,155),(15,0,48),62)
d=ImageDraw.Draw(im);d.text((35,20),'巴掌承重连接 · 拆解示意',font=font(32),fill='#1c3445')
label(im,ren,(5,28,80),(35,170),'两半压环：限制转盘抬起与倾斜')
label(im,ren,(5,15,57),(830,400),'转盘＋接杆一体件')
label(im,ren,(5,-22,34),(35,610),'固定承重座：托住转盘')
label(im,ren,(13,0,40),(35,810),'原配舵盘：插入槽口传动')
label(im,ren,(-29,0,23),(840,840),'舵机桥：连接原有支架')
d.text((35,1000),'拆解位置仅为说明。0.3mm径向／0.4mm轴向间隙待试配；未验证摩擦和承载。',font=font(18),fill='#9a5a35')
im.save(OUT/'预览/巴掌承重连接_拆解标注.png');win.Finalize()
items=saved_items;meshes=saved_meshes
# Fist tool corridors: show fixed parts with screws reachable from above.
items=[o for o in saved_items if o['name'].startswith(('20_','21_'))]
for x in (-30,30):
 for y in (-30,30):
  n='tool_'+str(x)+'_'+str(y);m=trimesh.creation.cylinder(radius=3,height=24,sections=24);m.apply_translation((x,y,17 if x<0 else 15));meshes[n]=m;items.append({'name':n,'group':'fist','kind':'reference','color':'#79bc85'})
im,ren,win=render('fist','whole',(-145,-170,160),(-10,0,13),79)
d=ImageDraw.Draw(im);d.text((35,20),'拳头固定螺丝 · 绿色为螺丝刀操作通道',font=font(30),fill='#1c3445')
label(im,ren,(-30,-30,10),(35,650),'围挡开U形口：后侧螺丝共用固定')
label(im,ren,(30,-30,12),(860,810),'前侧螺丝保留直达通道')
label(im,ren,(-46,28.5,3),(40,230),'取消原护罩独立孔耳')
d.text((35,1000),'四处按直径6mm工具检查；真实螺钉长度、螺母装入与手柄空间仍待确认。',font=font(19),fill='#9a5a35')
im.save(OUT/'预览/拳头螺丝通路_标注.png');win.Finalize()
items=saved_items;meshes=saved_meshes
# Export simplified web meshes ONLY for review; original export meshes are untouched.
web=[];scenes={k:trimesh.Scene() for k in ('palm','fist')}
for o in items:
 m=meshes[o['name']].copy()
 # Thin CAD walls and apertures must retain their original triangles.
 # Aggressive decimation folds thin surfaces and misrepresents the design.
 target=len(m.faces) if o['kind'] in ('body','part') else 20000
 if len(m.faces)>target:
  try:m=m.simplify_quadric_decimation(face_count=target)
  except Exception:pass
 c=o['color'];m.visual.face_colors=[int(c[i:i+2],16) for i in (1,3,5)]+[255]
 for k,scene in scenes.items():
  if o['group'] in ('common',k) and o['kind']!='envelope':scene.add_geometry(m,node_name=o['name'])
 web.append({**o,'v':np.round(m.vertices,3).tolist(),'f':m.faces.tolist()})
for k,scene in scenes.items():scene.export(OUT/'预览'/('装配_'+k+'_简化审阅.glb'))
template=(OUT/'preview_template.html').read_text(encoding='utf-8')
(OUT/'双机接口v06_交互预览.html').write_text(template.replace('__MESHES__',json.dumps(web,ensure_ascii=False,separators=(',',':'))),encoding='utf-8')
print('PREVIEWS_COMPLETE',len(web))
