from pathlib import Path
import math,json,csv,hashlib,shutil
import cadquery as cq,numpy as np,trimesh
P=Path(__file__).resolve().parent.parent;H=P.parent;SRC=H/'巴掌外观简化_v11';ROOT=H.parent
for d in ['00_先读说明','03_装配图','04_可选件_不用全部打印','制作记录']:(P/d).mkdir(parents=True,exist_ok=True)
items=json.loads((SRC/'装配清单.json').read_text(encoding='utf-8'))
M={o['name']:trimesh.load_mesh(SRC/'装配网格'/o['file']) for o in items}
def box(x,y,z,a=0,b=0,c=0):return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((a,b,c))
def cyl(r,h,x=0,y=0,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z))
def mesh(s):
 v,f=s.val().tessellate(.03,.05);m=trimesh.Trimesh(np.array([a.toTuple() for a in v]),np.array(f),process=True)
 m.merge_vertices(digits_vertex=7);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();assert m.is_volume
 return m
# Exact inherited frame outline; close the old clearance holes and cut controlled pilot holes.
carrier=box(33,2,1.5,-14.5,12,-31.5).union(box(33,2,2,-14.5,12,-4)).union(box(2,2,29.5,1,12,-31.5))
for x in (-29,-5):
 for z in (-29.5,-6.5):
  post=cq.Workplane('XZ',origin=(x,11,z)).circle(2.8).extrude(5.8)
  carrier=carrier.union(post).union(box(5,2,5,x,12,(-31 if z<-18 else -7)))
for x in (-22,0):
 foot=box(7,7,2.5,x,14,-31.5).cut(box(10,3.5,2,x,11.75,-30))
 carrier=carrier.union(foot).cut(cyl(1.7,6,x,14,-33))
for x in (-29,-5):
 for z in (-29.5,-6.5):carrier=carrier.cut(cq.Workplane('XZ',origin=(x,13.1,z)).circle(1.05).extrude(8.2))
assert carrier.val().isValid() and len(carrier.solids().vals())==1
cm=mesh(carrier);cn='02_竖置主板托架_布局草案';old=M[cn];M[cn]=cm
cq.exporters.export(carrier,str(P/'制作记录/主板托架_2p1自攻底孔.step'));cm.export(P/'制作记录/主板托架_装配坐标.stl')
assert np.allclose(cm.bounds,old.bounds,atol=.001)
shaftaxes=[]
for face in carrier.val().Faces():
 if face.geomType()=='CYLINDER':
  c=face._geomAdaptor().Cylinder();a=c.Axis();v=a.Direction();q=a.Location()
  if abs(c.Radius()-1.05)<1e-6 and abs(v.Y())>.999:shaftaxes.append([q.X(),q.Z()])
assert all(any(np.linalg.norm(np.array(v)-[x,z])<1e-5 for v in shaftaxes) for x in (-29,-5) for z in (-29.5,-6.5))
correction={'old_hole_mm':2.7,'new_pilot_mm':2.1,'screw':'外径2.5mm塑料自攻螺钉，建议长度8mm；非M2.5机牙螺钉','outline_bounds_unchanged':True,'axes_XZ':shaftaxes,'physical_thread_grip':'未实物验证'}
(P/'制作记录/托架固定补全.json').write_text(json.dumps(correction,ensure_ascii=False,indent=2),encoding='utf-8')
# Explicit whitelist, no PCB/motor/metal rods or motion envelopes in print folders.
common=[('C01','身体','01_原高身体_v08','白色','upright'),('C02','主板托架_自攻底孔','02_竖置主板托架_布局草案','白色','x90'),('C03','电池开关后面板','03_开关模块面板_v10_敞口拨动槽','白色','ym90'),('C04','短腿A','R_Leg_1','白色','facet'),('C05','短腿B','R_Leg_-1','白色','facet'),('C06','脚板A','R_foot_1','team','facet'),('C07','脚板B','R_foot_-1','team','facet'),('C08','左眼_平背胶粘','04_左椭圆眼睛_平背粘贴','黑色','ym90'),('C09','右眼_平背胶粘','04_右椭圆眼睛_平背粘贴','黑色','ym90')]
palm=[('B01','巴掌底座','10_巴掌定位底座_v07电池限位'),('B02','舵机桥','11_巴掌新舵机桥'),('B03','承重座_新盖耳','13_承重座_v11内收盖耳'),('B04','压环A','14A_半片限位压环'),('B05','压环B','14B_半片限位压环'),('B06','圆肩盖','12_圆肩避孔罩_v11'),('B07','转盘接杆插芯一体','15_转盘圆润实心杆与胶粘插芯_v11'),('B08','手掌_胶粘版','P_04_手掌75mm胶粘接口_无横销孔_v11')]
fist=[('R01','拳头底座_隐藏走线','20_拳头底座_v07尾部入线'),('R02','拳头护罩','21_拳头护罩_共用螺丝敞口'),('R03','曲柄','F_crank'),('R04','连杆','F_link'),('R05','滑架','F_carriage'),('R06','拳头腕杆一体','F_实际拳头腕杆')]
rows=[];mapping={};sceneitems=[]
for robot,team,folder,parts in [('palm','蓝色','01_巴掌机_每个STL打1件',palm),('fist','红色','02_拳头机_每个STL打1件',fist)]:
 plan=common+[(a,b,c,'team',('x90' if a=='B08' else 'upright')) for a,b,c in parts]
 for code,label,n,col,orient in plan:
  col=team if col=='team' else col;d=P/folder/col;d.mkdir(parents=True,exist_ok=True)
  m=M[n].copy();T=np.eye(4)
  if orient=='x90':T=trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0])
  if orient=='ym90':T=trimesh.transformations.rotation_matrix(-math.pi/2,[0,1,0])
  if orient=='facet':
   fi=int(np.argmax(m.facets_area));T=trimesh.geometry.align_vectors(m.facets_normal[fi],[0,0,-1])
  m.apply_transform(T);shift=-m.bounds[0];m.apply_translation(shift)
  assert m.is_volume and len(m.split(only_watertight=False))==1,(n,'invalid print mesh')
  out=d/(code+'_'+label+'_打印1件.stl');m.export(out)
  check=trimesh.load_mesh(out);assert check.is_volume and abs(check.volume-m.volume)<max(.05,m.volume*1e-5)
  assert np.allclose(np.sort(m.extents),np.sort(check.extents),atol=.001)
  support='检查自动支撑；孔槽与接触面尽量不留支撑疤'
  if code in ('C08','C09','R04'):support='平面朝下，通常不需要支撑'
  row={'robot':robot,'id':code,'name':label,'color':col,'quantity':1,'source_name':n,'file':out.relative_to(P).as_posix(),'mm':check.extents.round(3).tolist(),'support':support,'rotation_matrix':T.tolist(),'bed_translation':shift.tolist(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
  rows.append(row);mapping[(robot,n)]=row
  sceneitems.append({'robot':robot,'id':code,'name':label,'source_name':n,'color':{'蓝色':'#399ade','红色':'#df5357','白色':'#f2f1eb','黑色':'#28313b'}[col]})
# Optional highlights and manufacturer gearbox shells, deliberately separated.
for o in items:
 if not o['name'].startswith('05_'):continue
 d=P/'04_可选件_不用全部打印/眼睛白色高光_可直接用白漆代替';d.mkdir(parents=True,exist_ok=True)
 m=M[o['name']].copy();m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2,[0,1,0]));m.apply_translation(-m.bounds[0]);m.export(d/(o['name']+'_每台1件.stl'))
oldcase=H/'拳头_全套打印包_2026-09-29/可选_仅缺减速箱壳体时打印'
d=P/'04_可选件_不用全部打印/减速箱壳体_仅缺原壳时';d.mkdir(exist_ok=True)
for f in oldcase.glob('*.stl'):shutil.copy2(f,d/f.name)
(P/'制作记录/打印件与来源.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'制作记录/装配图对应.json').write_text(json.dumps(sceneitems,ensure_ascii=False,indent=2),encoding='utf-8')
with (P/'00_先读说明/打印清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['机型','编号','零件','颜色','每台数量','尺寸mm','文件'])
 for r in rows:w.writerow([r['robot'],r['id'],r['name'],r['color'],1,' × '.join(map(str,r['mm'])),r['file']])
print('PACK',len(rows),'required STL files; independent board pilot correction verified',flush=True)
