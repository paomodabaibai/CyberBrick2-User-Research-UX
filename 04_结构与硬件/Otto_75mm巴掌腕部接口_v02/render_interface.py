from pathlib import Path
import numpy as np,trimesh,vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;A=R/'装配坐标_勿直接打印'
palm=trimesh.load_mesh(A/'04_完整手掌75mm_带接口.stl');adapter=trimesh.load_mesh(A/'02_插入连接块.stl');rod=trimesh.load_mesh(A/'05_完整连接杆_杆距51mm.stl')
def actor(m,col):
 poly=vtk.vtkPolyData();pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.ascontiguousarray(m.vertices),deep=True));poly.SetPoints(pts)
 faces=np.column_stack([np.full(len(m.faces),3),m.faces]).astype(np.int64).ravel();cells=vtk.vtkCellArray();cells.SetCells(len(m.faces),numpy_to_vtkIdTypeArray(faces,deep=True));poly.SetPolys(cells)
 normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.SetFeatureAngle(45);normals.ConsistencyOn();normals.AutoOrientNormalsOn();normals.Update()
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*col);a.GetProperty().SetInterpolationToPhong();a.GetProperty().SetAmbient(.3);a.GetProperty().SetDiffuse(.7);return a

def render(items,focus,scale):
 ren=vtk.vtkRenderer();ren.SetBackground(.965,.972,.982)
 for m,col in items:ren.AddActor(actor(m,col))
 cam=ren.GetActiveCamera();cam.SetPosition(focus[0]-45,-150,focus[2]+70);cam.SetFocalPoint(*focus);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(900,650);win.SetMultiSamples(4);win.AddRenderer(ren);ren.ResetCameraClippingRange();win.Render()
 cap=vtk.vtkWindowToImageFilter();cap.SetInput(win);cap.ReadFrontBufferOff();cap.Update();arr=vtk_to_numpy(cap.GetOutput().GetPointData().GetScalars()).reshape(650,900,-1);im=Image.fromarray(np.flipud(arr)[:,:,:3]);win.Finalize();return im
cols=[(.72,.85,.96),(.96,.64,.2),(.15,.56,.64)]
full=render(list(zip([palm,adapter,rod],cols)),(62,0,7),50)
pp=palm.copy();pp.apply_translation([23,0,0]);aa=adapter.copy();aa.apply_translation([0,0,14]);expl=render(list(zip([pp,aa,rod],cols)),(76,0,10),54)
# Section is display-only; clip at y=0 and cap with manifold box.
cutbox=trimesh.creation.box([200,60,120]);cutbox.apply_translation([70,30,0]);section=trimesh.boolean.intersection([palm,cutbox],engine='manifold');cut=render(list(zip([section,adapter,rod],cols)),(58,0,6),23)
canvas=Image.new('RGB',(2700,790),'white');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',30);small=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',23)
for i,(im,title) in enumerate([(full,'装配：75 mm 手掌 / 51 mm 杆距'),(expl,'拆解：手掌 → 连接块 → 连接杆'),(cut,'腕部剖视：插槽与螺钉通路')]):canvas.paste(im,(i*900,65));draw.text((i*900+30,18),title,font=font,fill='#172638')
draw.text((30,735),'蓝色：手掌；橙色：可拆连接块；青色：连接杆。螺钉未绘出。先打印腕部小样，不是已验证的对战成品。',font=small,fill='#344458')
canvas.save(R/'腕部连接_装配拆解剖视.png')
print('rendered')
# Full robot context, actual original meshes and the updated interface.
import cadquery as cq
REF=R.parents[1]/'01_研究参考';V1=R.parent/'Otto_PG001顶部巴掌模块_v01'
def fromcq(obj):
 v,f=obj.val().tessellate(.1,.12);m=trimesh.Trimesh([p.toTuple() for p in v],f,process=True);m.fix_normals();return m
robot=[];stls=REF/'robot-battle-reference'/'Otto-V9'/'3Dprint'
robot.append((trimesh.load_mesh(stls/'OttoDIY_body_V9.stl'),(.78,.82,.87)))
for nm in ['Leg','foot']:
 m=trimesh.load_mesh(stls/f'OttoDIY_{nm}_V9.stl');robot.append((m,(.78,.82,.87)));mir=m.copy();mir.apply_transform(np.diag([-1,1,1,1]));robot.append((mir,(.78,.82,.87)))
for nm in ['03_body_mount_frame','04_servo_bridge']:robot.append((fromcq(cq.importers.importStep(str(V1/'STEP_可编辑实体'/(nm+'.step')))),(.15,.56,.64)))
sp=next((REF/'CyberBrick1迁移研究').glob('*Protection-PG002-PG001.stp'));servo=cq.importers.importStep(str(sp)).solids().vals()[0];servo=cq.Workplane('XY').newObject([servo]).translate((-11.35,-5.9,0)).rotate((0,0,0),(1,0,0),180).translate((0,0,25));robot.append((fromcq(servo),(.24,.28,.33)))
hp=next((REF/'CyberBrick1迁移研究').glob('*half arm*.stp'));horn=cq.importers.importStep(str(hp)).translate((5.34,-20,38.42));robot.append((fromcq(horn),(.82,.84,.87)))
for m,col in zip([palm,adapter,rod],cols):
 n=m.copy();n.apply_translation([5.34,0,39.97]);robot.append((n,col))
view=render(robot,(32,0,-5),100);view.save(R/'整机总装_v02.png')
sc=trimesh.Scene()
for i,(m,col) in enumerate(robot):
 n=m.copy();n.visual.vertex_colors=np.array([*[int(c*255) for c in col],255],dtype=np.uint8);sc.add_geometry(n,node_name=f'part_{i}')
sc.export(R/'整机总装_v02.glb')
