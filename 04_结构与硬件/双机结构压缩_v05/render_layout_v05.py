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
  if o['kind']=='envelope' and not (mode=='inside' and o['name']=='E01_侧插头与弯线预留'):continue
  name=o['name'];alpha=1
  if mode=='inside':
   if o['group']!='common' or name.startswith('R_Leg') or name.startswith('R_foot'):continue
   if o['kind']=='body':alpha=.12
   if o['kind']=='envelope':alpha=.18
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

for variant,cn in [('palm','巴掌'),('fist','拳头')]:
 im,ren,win=render(variant,'whole',(190,-240,135),(12,0,-15),98)
 d=ImageDraw.Draw(im);d.text((38,24),cn+'机器人 v05 · 原高度布局草案',font=font(31),fill='#1c3445')
 d.text((38,72),'身体39mm / 攻击高度恢复原值 / 上壳宽度仍75mm',font=font(21),fill='#5a6771')
 label(im,ren,(36,0,-22),(35,720),'前侧电池仓局部加宽')
 d.text((38,1000),'仅检验排布可行性，固定、线头与试装尚未完成，不可直接打印。',font=font(19),fill='#9a5a35')
 im.save(OUT/'预览'/(cn+'_原高整机.png'));win.Finalize()
im,ren,win=render('palm','inside',(160,-210,155),(0,0,-18),65)
d=ImageDraw.Draw(im);d.text((38,22),'原高度方案 · 竖置主板＋前置电池',font=font(31),fill='#1c3445')
label(im,ren,(-17,5,-18),(35,230),'主板竖放，插头改向侧面')
label(im,ren,(-14.5,-14.78,-18),(35,460),'侧面预留插头与弯线空间')
label(im,ren,(26,0,-21),(880,700),'电池前置立放')
label(im,ren,(-41,-19.5,-17),(870,240),'开关后置，拨杆朝外')
label(im,ren,(-35,13.5,-18),(35,820),'USB仍从后背插入')
d.text((38,1000),'原高39mm的排布候选；充电维护口、束带和具体紧固细节待完成。',font=font(19),fill='#9a5a35')
im.save(OUT/'预览/原高内部布局.png');win.Finalize()
# Same camera/scale as v04: truthful height comparison.
im,ren,win=render('palm','whole',(190,-240,135),(15,0,-3),112)
d=ImageDraw.Draw(im);d.text((42,24),'v05 原高度方案 · 身体39mm',font=font(34),fill='#1c3445');d.text((42,78),'与左图同一视角、同一比例；攻击模块整体下降26mm',font=font(21),fill='#5a6771')
d.text((42,1000),'布局草案；后背局部凸台换取高度，尚未发布打印版。',font=font(19),fill='#9a5a35')
old=Image.open(OUT.parent/'双机结构改版_v04/预览/巴掌_整机审阅.png').convert('RGB');cmp=Image.new('RGB',(2600,1050),'white');cmp.paste(old,(0,0));cmp.paste(im,(1300,0));cmp.save(OUT/'预览/v04与v05_同尺度高度对照.png');win.Finalize()
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
(OUT/'原高度结构v05_交互预览.html').write_text(template.replace('__MESHES__',json.dumps(web,ensure_ascii=False,separators=(',',':'))),encoding='utf-8')
print('PREVIEWS_COMPLETE',len(web))
