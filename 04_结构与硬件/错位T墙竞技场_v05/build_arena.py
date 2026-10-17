"""Parametric ground-only arena v0.5. Run with D:/python/python.exe.

Units: mm. CAD/STEP local XY is centered; bottom is Z=0. Floor/coupon STL
is rotated 180 degrees about X, then translated so walking face is at Z=0.
Scene transforms always address the unrotated CAD/STEP part coordinates.
"""
from pathlib import Path
import csv
import json
import math
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'cad_runtime' / 'Lib' / 'site-packages'))
import cadquery as cq
import trimesh

P = {
    'version': '0.5', 'date': '2026-10-13', 'units': 'mm',
    'design_status': 'dimensioned fabrication candidate; physical measurements pending',
    'physical_tested': False,
    'printer_nominal_mm': [200, 200, 200], 'brim_each_side_mm': 8,
    'arena_nominal_mm': [1260,1260],
    'floor': {'count_x':7, 'count_y':7, 'pitch':180, 'side':179.6, 'thickness':6,
              'pocket_depth':2.4, 'pocket_side_clearance':0.3, 'seam':0.4},
    'connector': {'length':44, 'width':18, 'thickness':2, 'neck_length':12, 'neck_width':8},
    'walls': {'width':40, 'vertical_corner_radius':2, 'horizontal_segment_length':180,
              'horizontal_heights':[60,80,100,80], 'stem_length':120, 'stem_height':80,
              'left_horizontal_x_bounds':[20,200,380,560,740], 'left_horizontal_y_bounds':[340,380],
              'left_stem_x_bounds':[500,540], 'left_stem_y_bounds':[380,500]},
    'perimeter': {'width':20, 'height':35, 'long_length':180, 'short_length':140,
                  'long_count':26, 'short_count':2, 'vertical_corner_radius':0},
    'target': {'diameter':90, 'height':160, 'wall':0.8, 'bottom':1.2,
               'reference_hit_height':135, 'reference_only_not_measured':True,
               'red_center':[260,650], 'blue_center':[1000,610]},
    'bom_full_A': {'floor':49,'bridge':84,'main_wall':10,'perimeter':28,'target':2},
    'bom_B_installed': {'floor':49,'bridge':84,'main_wall':4,'perimeter':28,'target':2},
    'density_assumption_g_cm3':1.24,
    'assembly_retention': 'thin removable adhesive under walls and rails; dimensions exclude adhesive thickness',
    'verification_limits': ['No physical fit, load, gait, attack sweep, edge containment or slicing validation',
        'Target and obstacle heights are parametric assumptions pending measured robot envelopes',
        'Table size and supporting flatness are unconfirmed'],
}

# Existing parameters.json is the editable parameter input. Do not silently
# overwrite user edits. Layout changes require corresponding scene/drawing edits.
if (ROOT/'parameters.json').exists():
    P = json.loads((ROOT/'parameters.json').read_text(encoding='utf-8'))
assert P['floor']['count_x']==7 and P['floor']['count_y']==7
assert P['floor']['pitch']==180 and P['floor']['side']==179.6 and P['floor']['thickness']==6
assert P['arena_nominal_mm']==[1260,1260]
assert P['walls']['width']==40 and P['walls']['horizontal_segment_length']==180 and P['walls']['stem_length']==120
assert len(P['walls']['horizontal_heights'])==4
assert P['walls']['horizontal_heights'][1]==P['walls']['horizontal_heights'][3], 'W02 uses one common height'

PARTS = {
    'F01': {'name':'floor_179p6', 'cn':'地板', 'size_mm':[179.6,179.6,6], 'qty_A':49,'qty_B':49,'spare_or_test_qty':0},
    'J01': {'name':'bridge_44x18x2', 'cn':'底面桥片', 'size_mm':[44,18,2], 'qty_A':84,'qty_B':84,'spare_or_test_qty':0},
    'W01': {'name':'wall_180x40x60', 'cn':'横墙低段', 'size_mm':[180,40,60], 'qty_A':2,'qty_B':0,'spare_or_test_qty':0},
    'W02': {'name':'wall_180x40x80', 'cn':'横墙中段与末段', 'size_mm':[180,40,80], 'qty_A':4,'qty_B':2,'spare_or_test_qty':0},
    'W03': {'name':'wall_180x40x100', 'cn':'横墙高段', 'size_mm':[180,40,100], 'qty_A':2,'qty_B':0,'spare_or_test_qty':0},
    'W04': {'name':'wall_120x40x80', 'cn':'支墙', 'size_mm':[120,40,80], 'qty_A':2,'qty_B':2,'spare_or_test_qty':0},
    'E01': {'name':'edge_180x20x35', 'cn':'护沿长段', 'size_mm':[180,20,35], 'qty_A':26,'qty_B':26,'spare_or_test_qty':0},
    'E02': {'name':'edge_140x20x35', 'cn':'护沿短段', 'size_mm':[140,20,35], 'qty_A':2,'qty_B':2,'spare_or_test_qty':0},
    'T01': {'name':'target_open_cup_D90_H160', 'cn':'开口筒靶', 'size_mm':[90,90,160], 'qty_A':2,'qty_B':2,'spare_or_test_qty':0},
    'C01': {'name':'seam_coupon_left', 'cn':'接缝样片左', 'size_mm':[39.8,40,6], 'qty_A':0,'qty_B':0,'spare_or_test_qty':1},
    'C02': {'name':'seam_coupon_right', 'cn':'接缝样片右', 'size_mm':[39.8,40,6], 'qty_A':0,'qty_B':0,'spare_or_test_qty':1},
    'T02': {'name':'target_test_D90_H80', 'cn':'半高筒靶试样', 'size_mm':[90,90,80], 'qty_A':0,'qty_B':0,'spare_or_test_qty':1},
}
for pid,index in [('W01',0),('W02',1),('W03',2)]:
    h=P['walls']['horizontal_heights'][index]
    PARTS[pid]['size_mm'][2]=h
    PARTS[pid]['name']=f'wall_180x40x{h}'
PARTS['W04']['size_mm'][2]=P['walls']['stem_height']
PARTS['W04']['name']=f'wall_120x40x{P["walls"]["stem_height"]}'
for pid,h in [('T01',P['target']['height']),('T02',80)]:
    d=P['target']['diameter']
    PARTS[pid]['size_mm']=[d,d,h]
    PARTS[pid]['name']=f'target_{"open_cup" if pid=="T01" else "test"}_D{d}_H{h}'

def write_json(name, obj):
    (ROOT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def box(x,y,z,cx=0,cy=0,bottom=0):
    return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate((cx,cy,bottom))

def bridge(clearance=0, height=None, bottom=0):
    c=P['connector']; half_neck=c['neck_length']/2
    lobe_length=(c['length']-c['neck_length'])/2
    lobe_center=half_neck+lobe_length/2
    h=c['thickness'] if height is None else height
    shape=box(c['neck_length']+2*clearance,c['neck_width']+2*clearance,h,bottom=bottom)
    for sign in (-1,1):
        shape=shape.union(box(lobe_length+2*clearance,c['width']+2*clearance,h,
                              cx=sign*lobe_center,bottom=bottom))
    return shape

def cup(height):
    t=P['target']; radius=t['diameter']/2
    outer=cq.Workplane('XY').circle(radius).extrude(height)
    bore=cq.Workplane('XY').circle(radius-t['wall']).extrude(height).translate((0,0,t['bottom']))
    return outer.cut(bore)

def build_parts():
    f=P['floor']; tile=box(f['side'],f['side'],f['thickness'])
    cutter=bridge(f['pocket_side_clearance'],f['pocket_depth']+0.01,-0.01)
    for angle in (0,90,180,270):
        tile=tile.cut(cutter.translate((f['pitch']/2,0,0)).rotate((0,0,0),(0,0,1),angle))
    # Samples occupy x=-40..-0.2 and +0.2..+40 at the test seam x=0.
    left=box(39.8,40,6,cx=-20.1).cut(cutter)
    right=box(39.8,40,6,cx=20.1).cut(cutter)
    geometry={'F01':tile,'J01':bridge(),'T01':cup(P['target']['height']),'T02':cup(80),
              'C01':left.translate((20.1,0,0)),'C02':right.translate((-20.1,0,0))}
    for pid in ('W01','W02','W03','W04','E01','E02'):
        q=PARTS[pid]; shape=box(*q['size_mm'])
        if pid.startswith('W'):
            shape=shape.edges('|Z').fillet(P['walls']['vertical_corner_radius'])
        geometry[pid]=shape
    join={
        'seam_width_mm':0.4, 'pocket_depth_mm':2.4,'bridge_thickness_mm':2,
        'nominal_vertical_clearance_mm':0.4,'pocket_side_clearance_mm':0.3,
        'intact_walking_surface_thickness_above_pocket_mm':3.6,
        'sample_bridge_left_intersection_mm3':bridge().intersect(left).val().Volume(),
        'sample_bridge_right_intersection_mm3':bridge().intersect(right).val().Volume(),
        'left_right_sample_intersection_mm3':left.intersect(right).val().Volume(),
        'sample_assembly_center_transforms_mm':{'C01':[-20.1,0,0],'C02':[20.1,0,0],'J01':[0,0,0]},
        'physical_fit_tested':False,
    }
    floor_left=tile.translate((-90,0,0)); floor_right=tile.translate((90,0,0))
    join['bridge_floor_left_intersection_mm3']=bridge().intersect(floor_left).val().Volume()
    join['bridge_floor_right_intersection_mm3']=bridge().intersect(floor_right).val().Volume()
    join['floor_floor_intersection_mm3']=floor_left.intersect(floor_right).val().Volume()
    for key,val in join.items():
        if key.endswith('_intersection_mm3'): assert abs(val)<1e-7, (key,val)
    return geometry,join

def make_scene():
    instances=[]
    def inst(i,pid,role,x,y,z,angle=0,color=None,variants=('A','B')):
        sx,sy,sz=PARTS[pid]['size_mm']
        a=math.radians(angle); wx=abs(sx*math.cos(a))+abs(sy*math.sin(a)); wy=abs(sx*math.sin(a))+abs(sy*math.cos(a))
        item={'id':i,'part_id':pid,'role':role,'center_xy_mm':[x,y], 'bottom_z_mm':z,
              'rotation_z_deg':angle,'bounds_xy_mm':[round(x-wx/2,4),round(y-wy/2,4),round(x+wx/2,4),round(y+wy/2,4)],
              'height_mm':sz,'color':color or '#bdc6cc','variants':list(variants)}
        instances.append(item)
    for row in range(7):
        for col in range(7):
            inst(f'F-{chr(65+row)}{col+1}','F01','floor',90+180*col,90+180*row,0,
                 color=('#eef0f2' if (row+col)%2==0 else '#e1e5e8'))
    for row in range(7):
        for joint in range(1,7):
            inst(f'J-X-{row+1}-{joint}','J01','bridge',180*joint,90+180*row,0,color='#6f7d87')
    for joint in range(1,7):
        for col in range(7):
            inst(f'J-Y-{joint}-{col+1}','J01','bridge',90+180*col,180*joint,0,90,color='#6f7d87')
    left=[('LH1','W01',110,360,0),('LH2','W02',290,360,0),('LH3','W03',470,360,0),('LH4','W02',650,360,0),('LS','W04',520,440,90)]
    for i,pid,x,y,a in left:
        active=('A',) if i in ('LH1','LH2','LH3') else ('A','B')
        inst(i,pid,'main_wall',x,y,6,a,'#4e5a67',active)
        inst(i.replace('L','R',1),pid,'main_wall',1260-x,1260-y,6,(a+180)%360,'#4e5a67',active)
    for edge,y in [('S',10),('N',1250)]:
        for col in range(7): inst(f'E-{edge}{col+1}','E01','perimeter',90+180*col,y,6,color='#76828d')
    for edge,x in [('W',10),('E',1250)]:
        for row in range(6): inst(f'E-{edge}{row+1}','E01','perimeter',x,110+180*row,6,90,'#76828d')
        inst(f'E-{edge}7','E02','perimeter',x,1170,6,90,'#76828d')
    inst('T-RED','T01','target',*P['target']['red_center'],6,color='#ed4c55')
    inst('T-BLUE','T01','target',*P['target']['blue_center'],6,color='#3989f6')
    for pid,part in PARTS.items():
        part['stl']=f'stl/{pid}_{part["name"]}.stl'
        part['step']=f'step/{pid}_{part["name"]}.step'
        part['print_orientation']=('walking_face_on_bed_pockets_up' if pid in ('F01','C01','C02') else 'bottom_on_bed')
        part['stl_from_cad_transform']={'rotation_x_deg':180,'translation_mm':[0,0,6]} if pid in ('F01','C01','C02') else {'rotation_x_deg':0,'translation_mm':[0,0,0]}
    variants={}
    for v in ('A','B'):
        include=[q['id'] for q in instances if v in q['variants']]
        variants[v]={'title':('A 原图完整墙版' if v=='A' else 'B 低转向版'),
                     'include_ids':include,'removed_wall_ids':([] if v=='A' else ['LH1','LH2','LH3','RH1','RH2','RH3']),
                     'installed_instance_count':len(include),
                     'assembly_step':f'assembly/arena_{v}_reference_only.step'}
    return {
        'version':'0.5','units':'mm',
        'coordinate_system':{'origin':'nominal arena lower-left corner, supporting table surface',
                             'x':'right','y':'up in top view','z':'upward in 3D',
                             'part_transform':'local CAD center XY and local bottom Z=0, rotate Z, then translate'},
        'arena':{'nominal_size_mm':[1260,1260],'actual_floor_bounds_xy_mm':[0.2,0.2,1259.8,1259.8],
                 'floor_top_z_mm':6,'all_obstacles_grounded_at_z_mm':6,'interior_clear_square_mm':[1220,1220],
                 'printer_nominal_mm':[200,200,200]},
        'floor_grid':{'rows':7,'cols':7,'pitch_mm':180,'tile_side_mm':179.6,'seam_mm':0.4,
                      'row_labels_bottom_to_top':['A','B','C','D','E','F','G'], 'col_labels_left_to_right':[1,2,3,4,5,6,7]},
        'parts':PARTS,'instances':instances,'variants':variants,
        'gameplay':{
            'status':'spawn positions and paths are design assumptions to validate by steering trials',
            'spawns':[{'id':'S-RED','team':'red','center_xy_mm':[260,180],'heading_deg':0,'heading_label':'+X', 'heading_by_variant':{'A':0,'B':90}},
                       {'id':'S-BLUE','team':'blue','center_xy_mm':[1000,1080],'heading_deg':180,'heading_label':'-X','heading_by_variant':{'A':180,'B':270}}],
            'targets':[{'instance_id':'T-RED','attacker':'red','defender':'blue','center_xy_mm':P['target']['red_center']},
                       {'instance_id':'T-BLUE','attacker':'blue','defender':'red','center_xy_mm':P['target']['blue_center']}],
            'clearances':[{'id':'outer_start_lane','width_mm':320,'basis':'inner perimeter y20 to lower wall y340; symmetric upper lane'},
                          {'id':'side_target_bay','width_mm':480,'basis':'inner perimeter x20 to left stem x500; mirrored right'},
                          {'id':'B_new_gate','width_mm':480,'basis':'x20 inner edge to x500 stem after removing LH1/LH2/LH3; right mirrored'},
                          {'id':'central_stem_tip_diagonal','width_mm':round(math.hypot(180,260),3),'basis':'static diagonal distance between left stem envelope corner (540,500) and right stem corner (720,760); steering and gait remain unverified'},
                          {'id':'target_fall_reservation','radius_mm':230,'basis':'conservative reserved circle around each target; not a measured fall envelope'}],
            'routes':[]
        }
    }

def transformed(part,item):
    x,y=item['center_xy_mm']
    return part.rotate((0,0,0),(0,0,1),item['rotation_z_deg']).translate((x,y,item['bottom_z_mm']))

def build():
    for folder in ('stl','step','assembly'): (ROOT/folder).mkdir(exist_ok=True)
    write_json('parameters.json',P)
    scene=make_scene(); write_json('scene.json',scene)
    print('SCENE_READY',flush=True)
    geometry,join=build_parts()
    report={'version':'0.5','units':'mm','physical_tested':False,
            'scope':'CAD BREP and exported mesh checks; no slicing, physical or robot movement tests',
            'join_check':join,'parts':{},'assemblies':{}}
    for pid,g in geometry.items():
        q=PARTS[pid]
        # Measure the analytic BREP before STL tessellation adds mesh deflection
        # margins to the OpenCascade cached bounding box.
        cb=g.val().BoundingBox()
        cq.exporters.export(g,str(ROOT/q['step']))
        printed=(g.rotate((0,0,0),(1,0,0),180).translate((0,0,6)) if pid in ('F01','C01','C02') else g)
        cq.exporters.export(printed,str(ROOT/q['stl']),tolerance=0.045,angularTolerance=0.12)
        mesh=trimesh.load(str(ROOT/q['stl']),force='mesh')
        dims=mesh.extents.tolist()
        fit=all(dims[i]+2*P['brim_each_side_mm']<=200+1e-4 for i in (0,1)) and dims[2]<=200+1e-4
        item={'nominal_dimensions_mm':q['size_mm'],
              'cad_dimensions_mm':[round(v,4) for v in (cb.xlen,cb.ylen,cb.zlen)],
              'dimensions_mm':[round(v,4) for v in dims],
              'print_bbox_min_mm':[round(float(v),4) for v in mesh.bounds[0]],
              'cad_valid':bool(g.val().isValid()), 'cad_solids':len(g.solids().vals()),
              'mesh_watertight':bool(mesh.is_watertight),'mesh_winding_consistent':bool(mesh.is_winding_consistent),
              'connected_meshes':len(mesh.split(only_watertight=False)),
              'cad_volume_mm3':round(g.val().Volume(),3),'mesh_volume_mm3':round(float(mesh.volume),3),
              'fully_solid_mass_reference_g':round(g.val().Volume()/1000*P['density_assumption_g_cm3'],2),
              'fits_200_cube_with_8mm_brim_per_side':bool(fit),
              'print_orientation':q['print_orientation']}
        assert item['cad_valid'] and item['cad_solids']==1 and item['mesh_watertight'] and item['mesh_winding_consistent'],(pid,item)
        assert item['connected_meshes']==1 and item['mesh_volume_mm3']>0 and fit,(pid,item)
        assert abs(float(mesh.bounds[0][2]))<1e-4,(pid,item)
        report['parts'][pid]=item
        print('PART_OK',pid,flush=True)
    # Collision checks only among obstacles and between bridges and floor.
    # Positive-volume overlap is prohibited; touching supports and butt joints are intentional.
    obstacle_items=[i for i in scene['instances'] if i['role'] in ('main_wall','perimeter','target')]
    checked_pairs=0; bbox_candidates=0; max_intersection=0.0
    for aindex,a in enumerate(obstacle_items):
        assert a['bottom_z_mm']==6,a
        ab=a['bounds_xy_mm']
        for b in obstacle_items[aindex+1:]:
            checked_pairs+=1; bb=b['bounds_xy_mm']
            if min(ab[2],bb[2])-max(ab[0],bb[0])>1e-6 and min(ab[3],bb[3])-max(ab[1],bb[1])>1e-6:
                bbox_candidates+=1
                vol=transformed(geometry[a['part_id']],a).intersect(transformed(geometry[b['part_id']],b)).val().Volume()
                max_intersection=max(max_intersection,vol)
                assert vol<1e-6,(a['id'],b['id'],vol)
    report['obstacle_checks']={'all_grounded_at_z_mm':6,'pair_bbox_checks':checked_pairs,
        'bbox_positive_overlap_candidates':bbox_candidates,'maximum_positive_volume_overlap_mm3':max_intersection,
        'rail_corner_overlaps':0,'nominal_rail_overhang_beyond_actual_floor_mm':0.2,
        'note':'adhesive thickness is excluded; all Z=6 placements are nominal'}
    fall_checks=[]
    fixed=[i for i in obstacle_items if i['role']!='target']
    for target in [i for i in obstacle_items if i['role']=='target']:
        x,y=target['center_xy_mm']; distances=[]
        for i in fixed:
            x0,y0,x1,y1=i['bounds_xy_mm']
            d=math.hypot(max(x0-x,0,x-x1),max(y0-y,0,y-y1))
            distances.append((d,i['id']))
        d,i=min(distances)
        fall_checks.append({'target_id':target['id'],'reserved_radius_mm':230,
             'minimum_distance_to_obstacle_bbox_mm':round(d,3),'closest_obstacle_id':i,
             'reservation_clear':d>=230,'physical_fall_envelope_tested':False})
        assert d>=230,(target['id'],d,i)
    report['target_fall_reservation_checks']=fall_checks
    report['central_stem_tip_clearance']={'diagonal_mm':round(math.hypot(180,260),3),
        'between_xy_mm':[[540,500],[720,760]],'static_envelope_clearance_only':True,
        'easy_turning_or_gait_not_verified':True}
    for version in ('A','B'):
        assembly=cq.Assembly(name=f'arena_{version}_REFERENCE_ONLY')
        subset=[i for i in scene['instances'] if version in i['variants']]
        for i in subset:
            rgb=tuple(int(i['color'][n:n+2],16)/255 for n in (1,3,5))
            assembly.add(transformed(geometry[i['part_id']],i),name=i['id'],color=cq.Color(*rgb))
        path=ROOT/scene['variants'][version]['assembly_step']
        assembly.save(str(path))
        reloaded=cq.importers.importStep(str(path))
        reload_solids=len(reloaded.solids().vals())
        assert reload_solids==len(subset),(version,reload_solids,len(subset))
        assert all(s.isValid() for s in reloaded.solids().vals())
        bb=reloaded.val().BoundingBox()
        counts=Counter(i['part_id'] for i in subset)
        for pid,q in PARTS.items(): assert counts.get(pid,0)==q[f'qty_{version}'],(version,pid,counts)
        report['assemblies'][version]={'instance_count':len(subset),'counts_by_part':dict(counts),
             'step':str(path.relative_to(ROOT)).replace('\\','/'),'exported_bytes':path.stat().st_size,
             'step_roundtrip_solid_count':reload_solids,'step_roundtrip_all_solids_valid':True,
             'step_roundtrip_bounds_mm':[round(v,4) for v in (bb.xlen,bb.ylen,bb.zlen)],
             'not_for_whole_arena_printing':True}
        print('ASSEMBLY_OK',version,len(subset),flush=True)
    write_json('geometry_report.json',report)
    fields=['part_id','name_zh','dimensions_mm','qty_A','qty_B_installed','qty_in_full_print_set','test_optional_qty','stl','step','print_orientation','notes']
    with (ROOT/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for pid,q in PARTS.items():
            notes={'F01':'49片均使用同一STL；顶面朝打印床；不用支撑',
                   'J01':'84片为在用数量；试接缝可先打印1片；连接片不承担独立托举整场载荷',
                   'W01':'B布局拆下保留','W02':'4件中B保留2末段、拆下2中段','W03':'B布局拆下保留',
                   'T01':'同款2枚，红蓝各1；0.8壁厚与1.2底厚需实测调重',
                   'T02':'只用于试切片/试壁厚；不能代替正式160高目标的击倒测试'}.get(pid,'墙体/护沿用可移胶固定；胶厚不计入模型' if pid.startswith(('W','E')) else '接口首印测试')
            w.writerow({'part_id':pid,'name_zh':q['cn'],'dimensions_mm':' × '.join(str(x) for x in q['size_mm']),
                'qty_A':q['qty_A'],'qty_B_installed':q['qty_B'],'qty_in_full_print_set':q['qty_A'],
                'test_optional_qty':q['spare_or_test_qty'],'stl':q['stl'],'step':q['step'],
                'print_orientation':q['print_orientation'],'notes':notes})
    print('COMPLETE',flush=True)

if __name__=='__main__':
    build()
