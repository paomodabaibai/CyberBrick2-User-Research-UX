"""Ground-only arena prototypes; run with D:/python/python.exe. Dimensions: mm."""
from pathlib import Path
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'cad_runtime' / 'Lib' / 'site-packages'))
import cadquery as cq
import trimesh


def box(x, y, z, cx=0, cy=0, bottom=0):
    return cq.Workplane('XY').box(x, y, z, centered=(True, True, False)).translate((cx, cy, bottom))


def bridge(p, clearance=0, height=None, bottom=0):
    c = p['connector']
    half_neck = c['neck_length'] / 2
    lobe_length = (c['length'] - c['neck_length']) / 2
    lobe_center = half_neck + lobe_length / 2
    h = c['thickness'] if height is None else height
    shape = box(c['neck_length'] + 2 * clearance, c['neck_width'] + 2 * clearance, h, bottom=bottom)
    for sign in (-1, 1):
        shape = shape.union(box(lobe_length + 2 * clearance, c['width'] + 2 * clearance,
                                h, cx=sign*lobe_center, bottom=bottom))
    return shape


def make_parts(p):
    f, w, t = p['floor'], p['wall'], p['target']
    connector = bridge(p)
    # Cut from just below the underside, finishing at z=2.4. Walking top stays flat.
    cutter = bridge(p, f['pocket_side_clearance'], f['pocket_depth'] + 0.01, -0.01)
    floor = box(f['side'], f['side'], f['thickness'])
    for angle in (0, 90, 180, 270):
        cut = cutter.translate((f['pitch']/2, 0, 0)).rotate((0, 0, 0), (0, 0, 1), angle)
        floor = floor.cut(cut)
    half_gap = (f['pitch'] - f['side']) / 2
    coupon_width = 40 - half_gap
    left = box(coupon_width, 40, f['thickness'], cx=-(40+half_gap)/2).cut(cutter)
    right = box(coupon_width, 40, f['thickness'], cx=(40+half_gap)/2).cut(cutter)
    wall = box(w['length'], w['width'], w['height']).edges('|Z').fillet(w['vertical_edge_radius'])
    target = cq.Workplane('XY').circle(t['diameter']/2).extrude(t['height'])
    hollow = cq.Workplane('XY').circle(t['diameter']/2-t['wall']).extrude(t['height']).translate((0, 0, t['bottom']))
    target = target.cut(hollow)
    parts = {
        '01_wall_160x40x60': wall,
        '02_ground_target_80x160': target,
        '03_floor_tile_179p6': floor,
        '04_bridge_connector': connector,
        # Keep coupon pair at its assembled XY coordinates for exact checking.
        '05_seam_coupon_left': left,
        '06_seam_coupon_right': right,
    }
    check = {
        'coupon_gap_mm': 2*half_gap,
        'connector_left_intersection_mm3': connector.intersect(left).val().Volume(),
        'connector_right_intersection_mm3': connector.intersect(right).val().Volume(),
        'floor_top_mm': f['thickness'],
        'pocket_ceiling_mm': f['pocket_depth'],
        'connector_top_mm': p['connector']['thickness'],
        'physical_fit_tested': False,
    }
    return parts, check


def main():
    p = json.loads((ROOT/'parameters.json').read_text(encoding='utf-8'))
    out = ROOT/'stl'
    out.mkdir(exist_ok=True)
    parts, join_check = make_parts(p)
    report = {'version': p['version'], 'units': 'mm', 'physical_tested': False,
              'scope': 'Digital solid and mesh checks only; no slicer or printing validation.',
              'join_check': join_check, 'parts': {}}
    for name, part in parts.items():
        dest = out/(name+'.stl')
        cq.exporters.export(part, str(dest), tolerance=0.06, angularTolerance=0.15)
        mesh = trimesh.load(str(dest), force='mesh')
        extents = mesh.extents.tolist()
        fit = all(extents[i] + 2*p['brim_each_side'] <= p['printer_nominal'][i]+1e-6 for i in (0, 1)) and extents[2] <= 180+1e-6
        item = {'dimensions_mm': [round(x, 4) for x in extents],
                'cad_valid': part.val().isValid(), 'cad_solids': len(part.solids().vals()),
                'mesh_watertight': bool(mesh.is_watertight), 'mesh_winding_consistent': bool(mesh.is_winding_consistent),
                'connected_meshes': len(mesh.split(only_watertight=False)),
                'cad_volume_mm3': round(part.val().Volume(), 3),
                'mesh_volume_mm3': round(float(mesh.volume), 3),
                'solid_mass_estimate_g_at_1p24': round(part.val().Volume()/1000*p['density_assumption_g_cm3'], 2),
                'fits_200_xy_with_8mm_brim_and_180_z': bool(fit)}
        assert item['cad_valid'] and item['cad_solids']==1 and item['mesh_watertight'] and item['mesh_winding_consistent']
        assert item['connected_meshes']==1 and item['mesh_volume_mm3']>0 and fit
        report['parts'][name] = item
    assert abs(join_check['connector_left_intersection_mm3']) < 1e-6
    assert abs(join_check['connector_right_intersection_mm3']) < 1e-6
    (ROOT/'geometry_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with zipfile.ZipFile(ROOT/'试打印组件包_v04.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.glob('*.stl')):
            z.write(f, 'stl/'+f.name)
        for name in ['README.md', 'parameters.json', 'geometry_report.json', 'build_components.py']:
            z.write(ROOT/name, name)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
