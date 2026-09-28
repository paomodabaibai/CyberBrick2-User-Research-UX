"""CB1 LA024 + LA016 -> Otto head slider-crank prototype (millimetres).

Run: python build_punch_head.py
Optional: --config parameters.json --out output --angle 180 --sweep-step 5
No hardware I/O. The original manufacturer gearbox is a REFERENCE, not our design.
X = punch direction; Y = left/right; Z = up; Otto body top = Z0.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import os
import sys

HERE = Path(__file__).resolve().parent
# Reuse the project's installed packages without modifying its moved/broken venv.
try:
    import cadquery as cq
except ImportError:
    vendor = HERE.parent / 'cad_runtime' / 'Lib' / 'site-packages'
    if sys.version_info[:2] != (3, 11) or not vendor.exists():
        raise SystemExit('Use Python 3.11 with project cad_runtime packages, or install requirements.txt.')
    sys.path.insert(0, str(vendor))
    import cadquery as cq
import numpy as np
import trimesh

DEFAULTS = {
    'body_outer_mm': 69.0, 'body_fit_per_side_mm': 0.4,
    'frame_outer_mm': 75.0, 'skirt_depth_mm': 8.0,
    'crank_radius_mm': 10.0, 'rod_centres_mm': 34.0,
    'crank_axis_x_mm': 6.0, 'gearbox_z_offset_mm': 6.8,
    'shaft_socket_radial_clearance_mm': 0.15,
    'guide_rod_diameter_mm': 3.0, 'guide_y_mm': 20.0,
    'guide_running_diametral_clearance_mm': 0.45,
    'guide_fixed_diametral_clearance_mm': 0.15,
    'pivot_hole_diameter_mm': 3.2,
    'fist_socket_per_side_mm': 0.25,
    'retain_screw_clearance_mm': 2.7, 'retain_head_diameter_mm': 5.2,
}


def box(x, y, z, cx=0, cy=0, z0=0):
    return cq.Workplane('XY').box(x, y, z, centered=(True, True, False)).translate((cx, cy, z0))


def cyl(r, h, x=0, y=0, z=0):
    return cq.Workplane('XY').circle(r).extrude(h).translate((x, y, z))


def cylx(r, length, x, y, z):
    return cyl(r, length).rotate((0, 0, 0), (0, 1, 0), 90).translate((x, y, z))


def capsule(length, width, height, z):
    return (box(length, width, height, length / 2, z0=z)
            .union(cyl(width / 2, height, z=z))
            .union(cyl(width / 2, height, length, z=z)))


def shape(wp):
    return wp.val() if isinstance(wp, cq.Workplane) else wp


def mesh(wp):
    vs, fs = shape(wp).tessellate(0.08, 0.15)
    result = trimesh.Trimesh(np.array([v.toTuple() for v in vs]), np.array(fs), process=True)
    result.fix_normals()
    return result


def bounds(wp):
    b = shape(wp).BoundingBox()
    return [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]


def overlap(a, b):
    aa, bb = bounds(a), bounds(b)
    if any(min(aa[i + 3], bb[i + 3]) - max(aa[i], bb[i]) < 1e-5 for i in range(3)):
        return 0.0
    return abs(shape(a).intersect(shape(b)).Volume())


def validate_parameters(p):
    if set(p) != set(DEFAULTS):
        raise ValueError('Unknown or missing parameters: ' + str(set(p) ^ set(DEFAULTS)))
    if any(not isinstance(v, (float, int)) or not math.isfinite(v) for v in p.values()):
        raise ValueError('All dimensions must be finite numbers.')
    if not 10 <= p['crank_radius_mm'] <= 12:
        raise ValueError('This hub and bolt layout supports radius 10..12 mm (stroke 20..24 mm).')
    if not 32 <= p['rod_centres_mm'] <= 36:
        raise ValueError('Connecting rod centres must be 32..36 mm for this guide layout.')
    if not 0.05 <= p['shaft_socket_radial_clearance_mm'] <= 0.3:
        raise ValueError('Shaft socket clearance must be 0.05..0.30 mm per side.')
    if p['frame_outer_mm'] < p['body_outer_mm'] + 2 * p['body_fit_per_side_mm'] + 4:
        raise ValueError('Body skirt walls would be too thin.')
    if not 19 <= p['guide_y_mm'] <= 22:
        raise ValueError('Guide half-spacing must be 19..22 mm to clear the glove.')
    if not 2.5 <= p['guide_rod_diameter_mm'] <= 4:
        raise ValueError('Guide rod diameter must be 2.5..4 mm.')
    if not .2 <= p['guide_running_diametral_clearance_mm'] <= .8:
        raise ValueError('Guide running clearance must be .2.. .8 mm diametral.')
    if p['rod_centres_mm'] <= p['crank_radius_mm']:
        raise ValueError('Connecting rod must exceed crank radius.')
    # Keep both carriage ends away from the fixed guide towers throughout travel.
    lo = p['crank_axis_x_mm'] + p['rod_centres_mm'] - p['crank_radius_mm'] - 10
    hi = p['crank_axis_x_mm'] + p['rod_centres_mm'] + p['crank_radius_mm'] + 10
    if lo < 16 or hi > 68:
        raise ValueError('Travel exceeds guide tower clearances; change radius/rod/axis together.')


class Head:
    def __init__(self, p):
        self.p = p
        self.r, self.l = p['crank_radius_mm'], p['rod_centres_mm']
        self.cx = p['crank_axis_x_mm']
        self.gz = p['gearbox_z_offset_mm']
        self.zplate = self.gz + 22  # 28.8 default
        self.zlink = self.zplate + 6
        self.zslider = self.zlink + 6
        self.zguide = self.zslider + 5
        self.official_path = HERE / '参考资料' / '030 Micro DC Motor with SH1.0 - Reducer-LA024.stp'
        raw = cq.importers.importStep(str(self.official_path)).solids().vals()
        if len(raw) != 14:
            raise ValueError('Unexpected manufacturer STEP assembly; do not select bodies blindly.')
        b = raw[10].BoundingBox()
        assert abs(b.xlen - 22) < .01 and abs(b.zlen - 54.35) < .01
        self.raw = raw
        # Cyclic axes: original X->Y, Y->Z, Z->X. Output centre original Z=11.15.
        self.hardware = {f'ref_{i:02}': self.place_official(s) for i, s in enumerate(raw)}
        self.fixed = {}
        self.parts = {}
        self.make_base()
        self.make_crank()
        self.make_link_slider_fist()

    def place_official(self, s):
        return cq.Workplane('XY').newObject([s]).rotate((0, 0, 0), (1, 1, 1), 120).translate((self.cx - 11.15, 0, self.gz))

    def make_base(self):
        p = self.p
        outer, depth = p['frame_outer_mm'], p['skirt_depth_mm']
        inner = p['body_outer_mm'] + 2 * p['body_fit_per_side_mm']
        base = box(outer, outer, 3)
        collar = box(outer, outer, depth, z0=-depth).cut(box(inner, inner, depth + 2, z0=-depth - 1))
        # Body side fasteners, matching the existing sleeve's hole axis and height.
        collar = collar.cut(cylx(1.6, outer + 2, -outer / 2 - 1, 0, -depth / 2))
        # Separate collar avoids a 69.8 mm unsupported ceiling when printing the deck.
        for xx in (-outer / 2 - 2.5, outer / 2 + 2.5):
            for yy in (-24, 24):
                base = base.union(cyl(4.5, 3, xx, yy)).cut(cyl(1.6, 5, xx, yy, -1))
                ear = cyl(4.5, depth, xx, yy, -depth).cut(cyl(1.6, depth + 2, xx, yy, -depth - 1))
                nut = cq.Workplane('XY').polygon(6, 5.8 / math.cos(math.pi/6)).extrude(3).translate((xx, yy, -depth))
                collar = collar.union(ear.cut(nut))
        self.parts['09_body_collar'] = collar
        self.fixed['body_collar'] = collar
        # Motor wire opening towards the rear; no cut through the side fastening zones.
        base = base.cut(box(18, 8, 15, -outer / 2 + 5, z0=-2))
        # Rectangular cradle, 0.30 mm lateral clearance to official casing envelope.
        gcx = self.cx - 16.175
        floor = self.gz - 2.8
        tray = box(60, 27.6, floor + 6 - 3, gcx, z0=3)
        tray = tray.cut(box(54.95, 22.6, 8, gcx, z0=floor))
        tray = tray.cut(box(8, 12, 9, gcx - 28, z0=floor + 1))
        base = base.union(tray)
        # Through-deck strap slots: the return path is below the platform, not through the motor.
        for xx in (self.cx - 35, self.cx - 23):
            for yy in (-15.6, 15.6):
                base = base.cut(box(3.8, 3, 16, xx, yy, -1))
        gy = p['guide_y_mm']
        fixed_d = p['guide_rod_diameter_mm'] + p['guide_fixed_diametral_clearance_mm']
        for yy in (-gy, gy):
            # Cantilever beams underneath the two front stanchions.
            base = base.union(box(52, 9, 8, 52, yy, 0))
            for xx in (10, 74):
                post = box(8, 8, self.zslider + 10 - 3, xx, yy, 3)
                if xx == 10:  # blind rear socket; the rod ends at X10
                    post = post.cut(cylx(fixed_d / 2, 4.1, 10, yy, self.zguide))
                else:  # insert rods from front, then retain with a grub screw
                    post = post.cut(cylx(fixed_d / 2, 10, 69, yy, self.zguide))
                    post = post.cut(cyl(1.3, 9, xx, yy, self.zguide))
                base = base.union(post)
            self.fixed[f'guide_rod_{yy:+g}'] = cylx(p['guide_rod_diameter_mm'] / 2, 64, 10, yy, self.zguide)
        self.parts['01_mount_and_guides'] = base
        self.fixed['base'] = base
        # Universal sensor bracket with slots, deliberately not a claim of switch compatibility.
        # It mounts to the left deck, outside the moving envelope; user can add Hall/optical hardware.
        sensor = box(28, 10, 3, self.cx, -29, 3)
        for xx in (self.cx - 8, self.cx + 8):
            sensor = sensor.cut(cyl(1.6, 5, xx, -29, 2))
            base = base.cut(cyl(1.6, 7, xx, -29, -1))
        upright = box(28, 3, self.zplate + 5 - 6, self.cx, -32.5, 6)
        for xx in (self.cx - 6, self.cx + 6):
            # vertical adjustment slots in upright, opening towards Y
            slot = box(3.2, 5, 12, xx, -32.5, self.zplate - 9)
            upright = upright.cut(slot)
        sensor = sensor.union(upright)
        self.parts['01_mount_and_guides'] = base
        self.fixed['base'] = base
        self.parts['06_optional_sensor_bracket'] = sensor
        self.fixed['sensor_bracket'] = sensor
        # Body opening gauge for a low-cost fit check.
        self.parts['07_body_fit_gauge'] = box(outer, outer, 3).cut(box(inner, inner, 5, z0=-1))

    def make_crank(self):
        p = self.p
        z = self.zplate
        hub_bottom = self.gz + 16
        crank = capsule(self.r, 8, 4, z).union(cyl(6.2, z + 4 - hub_bottom, z=hub_bottom))
        # Exact double-flat profile from the supplied output shaft section; don't assume a round/D bore.
        outshaft = self.hardware['ref_04'].translate((-self.cx, 0, 0))
        wire_wp = cq.Workplane('XY', origin=(0, 0, self.gz + 20)).newObject([outshaft.val()]).section()
        ws = wire_wp.wires().vals()
        outer_wire = max(ws, key=lambda w: w.BoundingBox().xlen * w.BoundingBox().ylen)
        wire_at_zero = outer_wire.translate((0, 0, -(self.gz + 20)))
        profile = cq.Workplane('XY').newObject([wire_at_zero]).toPending().offset2D(p['shaft_socket_radial_clearance_mm'])
        cavity = profile.extrude(7.5).translate((0, 0, hub_bottom - .1))
        self.socket = cavity
        crank = crank.cut(cavity)
        crank = crank.cut(cyl(p['retain_screw_clearance_mm'] / 2, 15, z=hub_bottom))
        crank = crank.cut(cyl(p['retain_head_diameter_mm'] / 2, 2.1, z=z + 2))
        crank = crank.cut(cyl(p['pivot_hole_diameter_mm'] / 2, 6, self.r, 0, z - 1))
        self.parts['02_crank_keyed_hub'] = crank
        gauge = cyl(6.2, 6).cut(cavity.translate((0, 0, -hub_bottom)))
        self.parts['08_output_shaft_fit_gauge'] = gauge

    def make_link_slider_fist(self):
        p = self.p
        d = p['pivot_hole_diameter_mm']
        rod = capsule(self.l, 8, 4, self.zlink)
        for xx in (0, self.l):
            rod = rod.cut(cyl(d / 2, 6, xx, z=self.zlink - 1))
        self.parts['03_connecting_rod'] = rod
        gy, zs = p['guide_y_mm'], self.zslider
        slider = box(20, 2 * gy + 8, 10, z0=zs)
        for yy in (-gy, gy):
            slider = slider.cut(cylx((p['guide_rod_diameter_mm'] + p['guide_running_diametral_clearance_mm']) / 2, 22, -11, yy, self.zguide))
        slider = slider.cut(cyl(d / 2, 12, z=zs - 1))
        # Lightening windows leave a central pivot web and the two guide bearings intact.
        for yy in (-10, 10):
            slider = slider.cut(box(12, 8, 12, 0, yy, zs - 1))
        tongue = box(12, 12, 8, 16, z0=zs + 1).cut(cyl(1.6, 10, 17, 0, zs))
        slider = slider.union(tongue)
        self.parts['04_carriage_and_wrist'] = slider
        glove = box(26, 30, 26, 26, z0=zs - 8).edges('|X').fillet(5.5)
        glove = glove.union(box(12, 18, 14, 16, z0=zs - 2).edges('|X').fillet(2))
        hollow = box(18, 22, 18, 28, z0=zs - 4).edges('|X').fillet(3.5)
        glove = glove.cut(hollow)
        c = p['fist_socket_per_side_mm']
        glove = glove.cut(box(13 + 2*c, 12 + 2*c, 8 + 2*c, 15.5, z0=zs + 1 - c))
        glove = glove.cut(cyl(1.6, 20, 17, 0, zs - 4))
        # Vent / support-removal access into hollow glove, on its underside.
        glove = glove.cut(box(8, 12, 6, 30, z0=zs - 10))
        for yy in (-7.5, 0, 7.5):
            glove = glove.cut(box(1.2, .8, 12, 39, yy, zs + 1))
        self.parts['05_hollow_boxing_glove_TPU'] = glove

    def state(self, degrees):
        t = math.radians(degrees)
        ax, ay = self.cx + self.r * math.cos(t), self.r * math.sin(t)
        sx = ax + math.sqrt(self.l**2 - ay**2)
        phi = math.degrees(math.atan2(-ay, sx - ax))
        return ax, ay, sx, phi

    def moving(self, degrees):
        ax, ay, sx, phi = self.state(degrees)
        def rz(s, a): return s.rotate((0, 0, 0), (0, 0, 1), a)
        moving = {
            'crank': rz(self.parts['02_crank_keyed_hub'], degrees).translate((self.cx, 0, 0)),
            'link': rz(self.parts['03_connecting_rod'], phi).translate((ax, ay, 0)),
            'carriage': self.parts['04_carriage_and_wrist'].translate((sx, 0, 0)),
            'glove': self.parts['05_hollow_boxing_glove_TPU'].translate((sx, 0, 0)),
        }
        # Actual-size pin/head/nut envelopes. They do not include threads.
        z = self.zplate
        moving['pin_A'] = cyl(1.5, 18, ax, ay, z - 2).union(cyl(2.8, 2, ax, ay, z - 2)).union(cyl(3.2, 4, ax, ay, self.zlink + 4.6))
        moving['washer_A'] = cyl(3.0, 2, ax, ay, z + 4).cut(cyl(1.6, 3, ax, ay, z + 3.5))
        moving['pin_B'] = cyl(1.5, 27, sx, 0, self.zlink - 2).union(cyl(2.8, 2, sx, 0, self.zlink - 2)).union(cyl(3.2, 4, sx, 0, self.zslider + 10.2))
        moving['washer_B'] = cyl(3.0, 2, sx, 0, self.zlink + 4).cut(cyl(1.6, 3, sx, 0, self.zlink + 3.5))
        # Output hub and output gear are keyed and must rotate together in the collision model.
        moving['output_gear'] = self.hardware['ref_04'].rotate((self.cx, 0, 0), (self.cx, 0, 1), degrees)
        return moving


COLORS = {'base': '#596875', 'sensor_bracket': '#83919b', 'crank': '#e4a631',
          'link': '#23a89b', 'carriage': '#4f9dc5', 'glove': '#d65353',
          'output_gear': '#d9c18b'}


def color(name):
    if name in COLORS: return COLORS[name]
    if name in ('ref_10', 'ref_11'): return '#bac6cd'
    if name.startswith('ref_'): return '#999993'
    return '#777b82'


def export_parts(head, out):
    from matplotlib.colors import to_rgba
    stld, stepd = out / 'STL_打印件', out / 'STEP_可编辑实体'
    refd = out / '官方壳体_如已有则不重复打印'
    for d in (stld, stepd, refd): d.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, obj in head.parts.items():
        solids = obj.solids().vals()
        assert len(solids) == 1 and solids[0].isValid(), (name, 'invalid/multiple solids')
        m = mesh(obj)
        assert m.is_watertight and m.is_volume and len(m.split()) == 1, name
        cq.exporters.export(obj, str(stepd / f'{name}.step'))
        pr = m.copy()
        # All orientation choices still require slicer inspection/support planning.
        if name == '01_mount_and_guides':
            # Keep skirt on bed; guide holes horizontal, short bridges need slicer support.
            pass
        if name == '05_hollow_boxing_glove_TPU':
            pr.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0, 1, 0]))
        pr.apply_translation(-pr.bounds[0])
        pr.export(stld / f'{name}.stl')
        report[name] = {'solids': len(solids), 'valid_brep': True, 'watertight': True,
                        'volume_mm3': round(float(m.volume), 2),
                        'print_size_mm': np.round(pr.extents, 3).tolist()}
    for i, name in [(10, 'reference_lower_case'), (11, 'reference_upper_case')]:
        obj = head.place_official(head.raw[i])
        cq.exporters.export(obj, str(refd / f'{name}.step'))
        m = mesh(obj)
        m.apply_translation(-m.bounds[0]); m.export(refd / f'{name}.stl')
    return report


def assembly(head, angle):
    result = dict(head.fixed)
    result.update({n: s for n, s in head.hardware.items() if n != 'ref_04'})
    result.update(head.moving(angle))
    return result


def save_assembly(head, angle, out):
    from matplotlib.colors import to_rgba
    asm, scene = cq.Assembly(), trimesh.Scene()
    for n, o in assembly(head, angle).items():
        rgba = to_rgba(color(n))
        asm.add(o, name=n, color=cq.Color(*rgba[:3]))
        mm = mesh(o); mm.visual.vertex_colors = np.array(rgba) * 255
        scene.add_geometry(mm, node_name=n)
    asm.save(str(out / f'assembly_{int(angle):03d}deg.step'))
    scene.export(out / f'assembly_{int(angle):03d}deg.glb')


def verify_motion(head, out, step):
    moving_names = ['crank', 'link', 'carriage', 'glove', 'pin_A', 'pin_B', 'washer_A', 'washer_B']
    # Gear teeth/gear meshing are manufacturer reference geometry, not verified here.
    stationary = dict(head.fixed)
    stationary.update({n: head.hardware[n] for n in ('ref_07', 'ref_10', 'ref_11')})
    worst, failures, rows = {}, [], []
    angles = sorted(set([0., 90., 180., 270., 360.] + list(np.arange(0, 360, step))))
    for deg in angles:
        m = head.moving(float(deg))
        ax, ay, sx, phi = head.state(float(deg))
        residual = math.hypot(sx - ax, ay) - head.l
        assert abs(residual) < 1e-8
        rows.append([deg, ax, ay, sx, sx - (head.cx + head.l - head.r), phi])
        pairs = [(a, b, m[a], ob) for a in moving_names for b, ob in stationary.items()]
        pairs += [(a, b, m[a], m[b]) for i, a in enumerate(moving_names) for b in moving_names[i+1:]]
        # Coupling socket vs rotating shaft (synchronous). Internal reference gear mesh excluded.
        pairs.append(('crank', 'output_gear', m['crank'], m['output_gear']))
        for a, b, oa, ob in pairs:
            v = overlap(oa, ob)
            key = f'{a} / {b}'
            if v > worst.get(key, 0): worst[key] = v
            if v > .01: failures.append({'angle_deg': float(deg), 'pair': key, 'overlap_mm3': round(v, 5)})
        if int(deg) % 60 == 0:
            print(f'Motion check {deg:g} deg; collisions so far: {len(failures)}', flush=True)
    # New fixed components against the official casing/motor, not against nominal body internals.
    fixed_failures = []
    fixed_objects = dict(head.fixed)
    fixed_objects.update({n: head.hardware[n] for n in ('ref_07', 'ref_10', 'ref_11')})
    items = list(fixed_objects.items())
    for i, (a, oa) in enumerate(items):
        for b, ob in items[i+1:]:
            if a.startswith('ref_') and b.startswith('ref_'): continue
            v = overlap(oa, ob)
            if v > .01: fixed_failures.append({'pair': f'{a} / {b}', 'overlap_mm3': round(v, 5)})
    with (out / 'motion.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['angle_deg', 'crank_pin_x', 'crank_pin_y', 'slider_x', 'extension_mm', 'rod_angle_deg']);w.writerows(rows)
    return {'angle_samples': len(angles), 'step_deg': step, 'stroke_mm': 2*head.r,
            'slider_min_x_mm': head.cx+head.l-head.r, 'slider_max_x_mm': head.cx+head.l+head.r,
            'max_rod_angle_deg': math.degrees(math.asin(head.r/head.l)),
            'moving_collisions': failures, 'fixed_collisions': fixed_failures,
            'max_observed_overlap_mm3': max(worst.values(), default=0),
            'scope': 'Discrete exact-solid intersections; not continuous collision, load, friction, FEA or physical verification.'}


def draw_outputs(head, out):
    os.environ.setdefault('MPLCONFIGDIR', str(out / '.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from PIL import Image
    fig = plt.figure(figsize=(15, 9), facecolor='#f5f7fa')
    for panel, deg in enumerate((180, 0), 1):
        ax = fig.add_subplot(1, 2, panel, projection='3d', facecolor='#f5f7fa')
        triangles, face_colors = [], []
        for name, obj in assembly(head, deg).items():
            if name == 'sensor_bracket': continue  # optional, omit to expose the transmission
            if name.startswith('ref_') and name not in ('ref_07', 'ref_10', 'ref_11'): continue
            if name.startswith('pin') or name.startswith('washer'): continue
            mm = mesh(obj)
            light = np.array([-.4, -.5, 1.]); light /= np.linalg.norm(light)
            shade = .52 + .48 * np.clip(mm.face_normals @ light, 0, 1)
            fc = shade[:, None] * np.array(to_rgb(color(name)))[None, :]
            triangles.append(mm.vertices[mm.faces]); face_colors.append(fc)
        # One face-sorted collection: separate object sorting can incorrectly paint the
        # tall base's bottom plate over the linkage and gearbox.
        ax.add_collection3d(Poly3DCollection(np.concatenate(triangles), facecolor=np.concatenate(face_colors), linewidths=0, alpha=1))
        ax.set(xlim=(-65, 95), ylim=(-43, 43), zlim=(-10, 66), xlabel='X / punch (mm)', ylabel='Y (mm)', zlabel='Z (mm)')
        ax.set_proj_type('ortho')
        ax.set_box_aspect((160, 86, 76)); ax.view_init(48, -65)
        ax.set_title(('RETRACTED' if deg == 180 else 'EXTENDED') + f'  |  {deg} deg', fontsize=15, pad=16)
    fig.suptitle(f'CB1 / OTTO - PUNCH HEAD     {2*head.r:g} mm stroke', fontsize=22, fontweight='bold', y=.96)
    fig.text(.5, .12, 'LA024 + LA016  /  gold: crank  /  teal: link  /  blue: carriage  /  red: hollow glove', ha='center', fontsize=12)
    fig.text(.5, .075, 'PARAMETRIC FIT PROTOTYPE - dimensions and motion checked digitally; physical fit and load testing pending', ha='center', fontsize=10, color='#65717c')
    fig.savefig(out / 'assembly_preview.png', dpi=150, bbox_inches='tight'); plt.close(fig)
    render_depth_preview(head, out)  # VTK z-buffer avoids painter-order artifacts in tall assemblies.
    frames = []
    for deg in np.linspace(180, 540, 49)[:-1]:
        axx, ayy, sx, _ = head.state(deg)
        fig, ax = plt.subplots(figsize=(8, 4), facecolor='#f5f7fa')
        ax.set_facecolor('#f5f7fa')
        for yy in (-head.p['guide_y_mm'], head.p['guide_y_mm']): ax.plot([10, 78], [yy, yy], color='#87909b', lw=5)
        ax.add_patch(plt.Rectangle((sx-10, -head.p['guide_y_mm']-4), 20, 2*head.p['guide_y_mm']+8, facecolor='#4f9dc5', alpha=.4))
        ax.add_patch(plt.Rectangle((sx+13, -15), 26, 30, facecolor='#d65353', alpha=.85))
        ax.plot([head.cx, axx], [0, ayy], '-o', color='#d99b1b', lw=7)
        ax.plot([axx, sx], [ayy, 0], '-o', color='#189b90', lw=5)
        ax.set(xlim=(-15, 98), ylim=(-30, 31), aspect='equal', xlabel='X (mm)', ylabel='Y (mm)')
        extension = sx - (head.cx+head.l-head.r)
        ax.set_title(f'One revolution = one out-and-back cycle  |  extension {extension:4.1f} mm')
        fig.tight_layout();fig.canvas.draw()
        frames.append(Image.fromarray(np.array(fig.canvas.buffer_rgba()).copy()).convert('RGB'));plt.close(fig)
    frames[0].save(out / 'mechanism_motion.gif', save_all=True, append_images=frames[1:], duration=65, loop=0)


def render_depth_preview(head, out):
    """Optional depth-buffer render using VTK (bundled with the project's CadQuery)."""
    try:
        import vtk
        from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    except ImportError:
        return
    from matplotlib.colors import to_rgb
    from PIL import Image, ImageDraw, ImageFont
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(1800, 760)
    win.SetMultiSamples(4)
    for panel, deg in enumerate((180, 0)):
        ren = vtk.vtkRenderer();ren.SetViewport(panel/2, 0, (panel+1)/2, 1)
        ren.SetBackground(.96, .97, .98);win.AddRenderer(ren)
        for name, obj in assembly(head, deg).items():
            if name == 'sensor_bracket': continue
            if name.startswith('ref_') and name not in ('ref_07', 'ref_10', 'ref_11'): continue
            mm = mesh(obj)
            points = vtk.vtkPoints(); points.SetData(numpy_to_vtk(np.ascontiguousarray(mm.vertices), deep=True))
            cells = vtk.vtkCellArray()
            ids = np.column_stack((np.full(len(mm.faces), 3), mm.faces)).astype(np.int64).ravel()
            cells.SetCells(len(mm.faces), numpy_to_vtkIdTypeArray(ids, deep=True))
            poly = vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(cells)
            normals = vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.SetFeatureAngle(45);normals.Update()
            mapper = vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
            actor = vtk.vtkActor();actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*to_rgb(color(name)));actor.GetProperty().SetAmbient(.25)
            actor.GetProperty().SetDiffuse(.75);actor.GetProperty().SetSpecular(.12)
            ren.AddActor(actor)
        camera = ren.GetActiveCamera();camera.SetPosition(150, -215, 180)
        camera.SetFocalPoint(18, 0, 23);camera.SetViewUp(0, 0, 1)
        camera.ParallelProjectionOn();camera.SetParallelScale(71)
        ren.ResetCameraClippingRange()
    win.Render()
    capture = vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update()
    writer = vtk.vtkPNGWriter();writer.SetFileName(str(out/'assembly_preview.png'));writer.SetInputConnection(capture.GetOutputPort());writer.Write()
    win.Finalize()
    raw = Image.open(out/'assembly_preview.png').convert('RGB')
    page = Image.new('RGB', (1800, 920), '#f5f7fa');page.paste(raw, (0, 100))
    font_path = Path('C:/Windows/Fonts/arial.ttf')
    def font(size): return ImageFont.truetype(str(font_path), size) if font_path.exists() else ImageFont.load_default()
    draw = ImageDraw.Draw(page)
    draw.text((48, 20), f'CB1 / OTTO - PUNCH HEAD     {2*head.r:g} mm stroke', fill='#172634', font=font(38))
    draw.text((250, 92), 'RETRACTED / 180 deg', fill='#364958', font=font(26))
    draw.text((1170, 92), 'EXTENDED / 0 deg', fill='#364958', font=font(26))
    draw.text((48, 840), 'LA024 + LA016 | gold: crank | teal: link | blue: carriage | red: hollow glove', fill='#354b5a', font=font(23))
    draw.text((48, 882), 'Fit prototype. Digital geometry checks passed; physical fit, printing and load testing pending.', fill='#647584', font=font(20))
    page.save(out/'assembly_preview.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=HERE/'parameters.json')
    parser.add_argument('--out', type=Path, default=HERE/'output')
    parser.add_argument('--angle', type=float, default=180.)
    parser.add_argument('--sweep-step', type=float, default=5.)
    parser.add_argument('--skip-render', action='store_true')
    args = parser.parse_args()
    if not 0 < args.sweep_step <= 15: parser.error('sweep-step must be >0 and <=15 degrees')
    p = dict(DEFAULTS)
    if args.config.exists():
        overrides = json.loads(args.config.read_text(encoding='utf-8-sig'))
        if set(overrides) - set(p): raise ValueError('Unknown keys: '+str(set(overrides)-set(p)))
        p.update(overrides)
    validate_parameters(p)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'parameters_used.json').write_text(json.dumps(p, indent=2), encoding='utf-8')
    head = Head(p)
    print('Geometry built; validating and exporting parts...', flush=True)
    report = {'parameters': p, 'parts': export_parts(head, args.out),
              'manufacturer_step_sha256': hashlib.sha256(head.official_path.read_bytes()).hexdigest()}
    report['motion'] = verify_motion(head, args.out, args.sweep_step)
    report['status'] = 'DIGITAL_CHECKS_PASS_PHYSICAL_UNVERIFIED' if not (report['motion']['moving_collisions'] or report['motion']['fixed_collisions']) else 'COLLISIONS_FOUND_DO_NOT_PRINT'
    (args.out/'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for deg in sorted(set([0., 180., args.angle])): save_assembly(head, deg, args.out)
    if not args.skip_render: draw_outputs(head, args.out)
    print(json.dumps({'status': report['status'], 'output': str(args.out), 'stroke_mm': 2*head.r}, ensure_ascii=False), flush=True)
    if report['status'].startswith('COLLISIONS'): raise SystemExit(2)


if __name__ == '__main__':
    main()
