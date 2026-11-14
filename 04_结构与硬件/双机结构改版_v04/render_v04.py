from pathlib import Path
import json,numpy as np,trimesh,vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
items=json.loads((OUT/'装配清单.json').read_text(encoding='utf-8'))
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
meshes={o['name']:trimesh.load_mesh(OUT/'装配网格'/o['file']) for o in items}
# Routing illustrations: not measured cables and not electrical pin assignments.
def route(name,points,color,group='common'):
 parts=[]
 for a,b in zip(points,points[1:]):
  a=np.array(a,dtype=float);b=np.array(b,dtype=float);v=b-a
  mat=trimesh.geometry.align_vectors([0,0,1],v);mat[:3,3]=(a+b)/2
  parts.append(trimesh.creation.cylinder(radius=.75,height=np.linalg.norm(v),sections=8,transform=mat))
 meshes[name]=trimesh.util.concatenate(parts);items.append({'name':name,'color':color,'group':group,'kind':'route'})
for side in (-1,1):
 route('走线示意_腿部_'+str(side),[(3,side*25,-14),(0,side*31,-8),(-10,side*31,7),(-14,side*17,17),(-14,side*5,17),(-14,side*5,7)],'#e5a745')
route('走线示意_电池到开关',[(-25,0,-20),(-29,16,-20),(-12,26,-13),(17,24,-3)],'#dc6c62')
route('走线示意_开关到主板',[(-3,24,-3),(-24,21,7),(-27,0,7)],'#dc6c62')
route('走线示意_拳头电机',[(-54,0,34),(-54,0,23),(-54,-18,23),(-24,-18,23),(-24,-18,10),(-24,-12,7)],'#e5a745','fist')
route('走线示意_巴掌舵机',[(8,8,31),(18,21,31),(18,21,19),(-24,-18,10),(-24,-12,7)],'#e5a745','palm')
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
for variant,cn in [('palm','巴掌'),('fist','拳头')]:
 im,ren,win=render(variant,'whole',(190,-240,135),(15,0,-3),112)
 d=ImageDraw.Draw(im);d.text((42,24),cn+'机器人 v04 · 结构审阅',font=font(34),fill='#1c3445')
 d.text((42,78),'真实模型预览｜上部增高26mm；旧腿脚与攻击运动件保留',font=font(21),fill='#5a6771')
 label(im,ren,(37,0,8),(880,720),'正面辨识胸标')
 label(im,ren,(-30,-30,26),(48,500),'四点螺钉固定顶部')
 label(im,ren,(0,-34,1),(48,820),'共用理线身体')
 if variant=='palm':label(im,ren,(0,-36,55),(52,230),'可拆圆角头罩')
 else:label(im,ren,(-30,-29,40),(45,235),'轻量护罩／顶部保留运动空间')
 d.text((42,1000),'审阅模型，不是批量打印放行版本；最终供货舵机与线头需实物核对。',font=font(19),fill='#9a5a35')
 im.save(OUT/'预览'/(cn+'_整机审阅.png'));win.Finalize()
im,ren,win=render('palm','inside',(-160,-190,175),(-3,0,-4),67)
d=ImageDraw.Draw(im);d.text((38,22),'共用身体 · 内部装配与接口',font=font(34),fill='#1c3445')
label(im,ren,(-17,0,-6),(35,210),'原厂核心板＋接收扩展板')
label(im,ren,(-17,-24,-11),(30,600),'可拆开底托架')
label(im,ren,(8,0,-27),(850,840),'电池低位独立限位')
label(im,ren,(-37,0,-14.5),(35,840),'后背USB数据接口')
label(im,ren,(7,37,6),(900,250),'侧后方电源开关')
label(im,ren,(-37,-23,10),(35,430),'可换充电维护面板')
d.text((38,1000),'彩线为走线示意，非精确线束；充电面板暂封闭，尚无充电模块。',font=font(20),fill='#9a5a35')
im.save(OUT/'预览/内部装配_标注.png');win.Finalize()
im,ren,win=render('fist','wire',(-150,-160,-110),(-15,0,38),79)
d=ImageDraw.Draw(im);d.text((38,22),'拳头底座 · 隐藏走线通道（仰视）',font=font(32),fill='#1c3445')
label(im,ren,(-54,0,28),(30,270),'电机尾部入口')
label(im,ren,(-54,-18,22),(35,760),'底部封闭转向线槽')
label(im,ren,(-24,-18,23),(870,850),'从身体内部向上接线')
d.text((38,1000),'线槽避开合盖接缝；最终须检查真实插头能穿过、线束不碰运动件。',font=font(20),fill='#9a5a35')
im.save(OUT/'预览/拳头隐藏过线_标注.png');win.Finalize()
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
(OUT/'双机结构v04_交互预览.html').write_text(template.replace('__MESHES__',json.dumps(web,ensure_ascii=False,separators=(',',':'))),encoding='utf-8')
print('PREVIEWS_COMPLETE',len(web))
