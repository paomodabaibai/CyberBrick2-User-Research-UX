from pathlib import Path
import trimesh, cadquery as cq, json
ROOT=Path(__file__).resolve().parent

def generate(size=50, reach=37.5):
 if not 20<=size<=100:raise ValueError('Palm size must be 20..100 mm (geometric range only).')
 if not 25<=reach<=70:raise ValueError('Rod reach must be 25..70 mm (geometric range only).')
 mesh=trimesh.load_mesh(ROOT/'巴掌_Tripo原始.stl')
 main=max(mesh.split(only_watertight=False),key=lambda m:len(m.faces))
 assert main.is_watertight
 main.apply_scale(size/main.extents.max());main.apply_translation([0,0,-main.bounds[0,2]])
 dest=ROOT/f'输出_手掌{size:g}mm_杆距{reach:g}mm';dest.mkdir(exist_ok=True)
 main.export(dest/f'手掌_最长边{size:g}mm_尚无安装接口.stl')
 # R = servo shaft centre to midpoint of two end mounting holes.
 rod=cq.Workplane('XY').box(reach+12.5,10,3,centered=(True,True,False)).translate(((reach+2.5)/2,0,0)).edges('|Z').fillet(1)
 for x,r in [(0,4.1),(6.75,.8),(12.75,.8),(reach-2.5,1.1),(reach+2.5,1.1)]:
  rod=rod.cut(cq.Workplane('XY').center(x,0).circle(r).extrude(5).translate((0,0,-1)))
 assert rod.val().isValid()
 cq.exporters.export(rod,str(dest/f'连接杆_孔组中心距{reach:g}mm.stl'))
 cq.exporters.export(rod,str(dest/f'连接杆_孔组中心距{reach:g}mm.step'))
 rodmesh=trimesh.load_mesh(dest/f'连接杆_孔组中心距{reach:g}mm.stl');assert rodmesh.is_watertight
 result={'palm_longest_dimension_mm':size,'palm_XYZ_mm':main.extents.tolist(),'palm_faces':len(main.faces),'palm_watertight':bool(main.is_watertight),'rod_reach_mm':reach,'rod_overall_length_mm':reach+12.5,'rod_width_mm':10,'rod_thickness_mm':3,'rod_tip_hole_pitch_mm':5,'note':'Palm has no mounting interface yet. Rod and palm are NOT an assembled or tested pair. Geometric limits are not load ratings.'}
 (dest/'尺寸与状态.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(dest)
 return main
if __name__=='__main__':
 import sys
 if len(sys.argv)>1:generate(float(sys.argv[1]),float(sys.argv[2]))
 else:
  print('Palm size = longest dimension, mm. Rod reach = shaft centre to end hole group centre, mm.')
  a=input('Palm size [50]: ').strip() or '50';b=input('Rod reach [37.5]: ').strip() or '37.5'
  try:generate(float(a),float(b));print('Done. See output folder. Palm connection still needs design.')
  except Exception as e:print('Failed:',e)
  input('Press Enter to close...')
