"""Build the map-only 800 x 1200 mm arena as glTF/GLB and OBJ.

Source parameters are millimetres; all exported geometry uses metres and Y up.
The original 1260 mm square layout is adapted for presentation, not measured
from the completed physical partitions. No texture pixels are modified.
"""
from pathlib import Path
import collections
import hashlib
import json
import math
import struct

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source'
MODEL = ROOT / 'model'
PARAMS = SOURCE / 'layout_parameters.json'


def defaults():
    walls = []
    for i, (x, h) in enumerate(zip((20, 135, 250, 365), (60, 80, 100, 80)), 1):
        walls.append(dict(id=f'front_main_{i}', x_mm=x, z_mm=320,
                          length_mm=115, height_mm=h, axis='X'))
    walls.append(dict(id='front_T_branch', x_mm=320, z_mm=360,
                      length_mm=120, height_mm=80, axis='Z'))
    for i, (x, h) in enumerate(zip((665, 550, 435, 320), (60, 80, 100, 80)), 1):
        walls.append(dict(id=f'back_main_{i}', x_mm=x, z_mm=840,
                          length_mm=115, height_mm=h, axis='X'))
    walls.append(dict(id='back_T_branch', x_mm=440, z_mm=720,
                      length_mm=120, height_mm=80, axis='Z'))
    return {
        'version': 'v11-map-only', 'source_units': 'mm',
        'export_units': 'metres', 'export_axes': 'X width; Y up; Z length',
        'floor_width_mm': 800, 'floor_length_mm': 1200, 'floor_thickness_mm': 5,
        'floor_top_y_mm': 0, 'floor_texture_repeat_mm': 200,
        'perimeter_width_mm': 20, 'perimeter_height_mm': 30,
        'wall_panel_thickness_mm': 5, 'wall_foot_width_mm': 40,
        'wall_foot_thickness_mm': 5,
        'brace_thickness_mm': 5, 'brace_depth_mm': 15, 'brace_height_mm': 30,
        'walls': walls,
        'confirmed_by_user': [
            'Floor footprint 800 x 1200 mm.',
            'Two staggered T-shaped wall groups.',
            'Main walls parallel to the 800 mm width.',
            'Map only, without striking apparatus.'
        ],
        'assumed_not_physically_measured': [
            'Main wall length 460 mm per group, divided into four 115 mm sections.',
            'Main wall foot Z intervals 320..360 mm and 840..880 mm.',
            'T branches are 120 mm long, positioned at X320..360 and X440..480 mm.',
            'Inherited v08 foot-to-foot T junction: foot bases meet, while the branch panel starts 17.5 mm beyond the main panel face. This is a presentation layout, not a physical partition replica.',
            '60/80/100/80 mm wall heights, 5 mm panel thickness and 40 mm feet retain previous design values.',
            '20 x 30 mm perimeter rails and a one-piece 5 mm base are visualization assumptions.'
        ],
        'physical_measurements_verified': False,
        'textures': {
            'floor': 'textures/floor_tile_200mm.png',
            'wall_115_h55': 'textures/wall_115_h55.png',
            'wall_115_h75': 'textures/wall_115_h75.png',
            'wall_115_h95': 'textures/wall_115_h95.png',
            'wall_120_h75': 'textures/wall_120_h75.png'
        }
    }


def hex_color(s):
    return [int(s[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def linear_channel(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


class Scene:
    def __init__(self, p):
        self.p = p
        self.materials = [
            dict(name='floor_print', color=[1, 1, 1], texture=p['textures']['floor'], roughness=.92, metallic=0),
            dict(name='pvc_base', color=hex_color('#d7e3e0'), texture=None, roughness=.88, metallic=0),
            dict(name='wall_panel_edges', color=hex_color('#466b74'), texture=None, roughness=.87, metallic=0),
            dict(name='natural_wood_rails', color=hex_color('#c7a778'), texture=None, roughness=.9, metallic=0),
        ]
        self.mat_index = {m['name']: i for i, m in enumerate(self.materials)}
        for k in ('wall_115_h55', 'wall_115_h75', 'wall_115_h95', 'wall_120_h75'):
            self.mat_index[k] = len(self.materials)
            self.materials.append(dict(name=k, color=[1, 1, 1], texture=p['textures'][k], roughness=.86, metallic=0))
        self.parts = collections.OrderedDict()
        self.objects = {}

    def face(self, name, kind, points, material, uv=None):
        # Input points are in mm; each face has independent vertices for hard normals.
        m = self.mat_index[material]
        key = (name, m)
        if key not in self.parts:
            self.parts[key] = dict(name=f'{name}__{material}', object_name=name,
                                   kind=kind, material=m, positions=[], normals=[], uvs=[], indices=[])
        self.objects[name] = kind
        out = self.parts[key]
        normal = cross(sub(points[1], points[0]), sub(points[2], points[0]))
        length = math.sqrt(dot(normal, normal))
        assert length > 1e-10, (name, points)
        normal = [v / length for v in normal]
        if uv is None:
            uv = [(0, 1), (1, 1), (1, 0), (0, 0)][:len(points)]
        start = len(out['positions']) // 3
        for point, tex in zip(points, uv):
            out['positions'].extend(round(v / 1000, 9) for v in point)
            out['normals'].extend(round(v, 9) for v in normal)
            out['uvs'].extend(round(v, 9) for v in tex)
        for i in range(1, len(points) - 1):
            out['indices'].extend((start, start + i, start + i + 1))

    def box(self, name, kind, x, y, z, w, h, d, material,
            face_mats=None, transform=None, top_uv=None):
        X, Y, Z = x + w, y + h, z + d
        faces = {
            'front': [[X, y, z], [x, y, z], [x, Y, z], [X, Y, z]],
            'back': [[x, y, Z], [X, y, Z], [X, Y, Z], [x, Y, Z]],
            'left': [[x, y, z], [x, y, Z], [x, Y, Z], [x, Y, z]],
            'right': [[X, y, Z], [X, y, z], [X, Y, z], [X, Y, Z]],
            'top': [[x, Y, Z], [X, Y, Z], [X, Y, z], [x, Y, z]],
            'bottom': [[x, y, z], [X, y, z], [X, y, Z], [x, y, Z]],
        }
        for side, ps in faces.items():
            uv = top_uv if side == 'top' and top_uv else None
            if transform:
                ps = [transform(v) for v in ps]
            self.face(name, kind, ps, (face_mats or {}).get(side, material), uv)

    def brace(self, name, x, y, z, sign, transform):
        p = self.p
        a = [[x, y, z], [x, y, z + sign * p['brace_depth_mm']],
             [x, y + p['brace_height_mm'], z]]
        b = [[xx + p['brace_thickness_mm'], yy, zz] for xx, yy, zz in a]
        center = [sum(v[i] for v in a + b) / 6 for i in range(3)]
        faces = [a, b] + [[a[i], a[(i + 1) % 3], b[(i + 1) % 3], b[i]] for i in range(3)]
        for ps in faces:
            normal = cross(sub(ps[1], ps[0]), sub(ps[2], ps[0]))
            face_center = [sum(v[i] for v in ps) / len(ps) for i in range(3)]
            if dot(normal, sub(face_center, center)) < 0:
                ps = list(reversed(ps))
            self.face(name, 'wall_brace', [transform(v) for v in ps], 'pvc_base')

    def wall(self, w):
        p = self.p
        x, z, length, height = (w[k] for k in ('x_mm', 'z_mm', 'length_mm', 'height_mm'))
        width, foot, thick = p['wall_foot_width_mm'], p['wall_foot_thickness_mm'], p['wall_panel_thickness_mm']
        front = (width - thick) / 2
        if w['axis'] == 'X':
            transform = lambda v: [x + v[0], v[1], z + v[2]]
        else:
            # Proper rotation: longitudinal local +X becomes world +Z.
            transform = lambda v: [x + width - v[2], v[1], z + v[0]]
        ident = w['id']
        self.box(ident + '_foot', 'wall_foot', 0, 0, 0, length, foot, width, 'pvc_base', transform=transform)
        # Width edits retain the nominal artwork with UV stretching. A new height
        # needs a matching source image because the stripe/text scale is intentional.
        texture_key = f'wall_{115 if w["axis"] == "X" else 120}_h{int(height - foot)}'
        if texture_key not in self.mat_index:
            raise ValueError(f'No matching wall texture for {texture_key}. Create a new texture first.')
        self.box(ident + '_panel', 'wall_panel', 0, foot, front, length, height - foot, thick,
                 'wall_panel_edges', {'front': texture_key, 'back': texture_key}, transform=transform)
        self.brace(ident + '_brace_front', 20, foot, front, -1, transform)
        self.brace(ident + '_brace_back', length - 25, foot, front + thick, 1, transform)

    def build(self):
        p = self.p
        W, L, T = p['floor_width_mm'], p['floor_length_mm'], p['floor_thickness_mm']
        repeat = p['floor_texture_repeat_mm']
        self.box('floor_base', 'floor', 0, -T, 0, W, T, L, 'pvc_base',
                 {'top': 'floor_print'}, top_uv=[(0, L / repeat), (W / repeat, L / repeat), (W / repeat, 0), (0, 0)])
        r, h = p['perimeter_width_mm'], p['perimeter_height_mm']
        self.box('perimeter_front', 'perimeter', 0, 0, 0, W, h, r, 'natural_wood_rails')
        self.box('perimeter_back', 'perimeter', 0, 0, L - r, W, h, r, 'natural_wood_rails')
        self.box('perimeter_left', 'perimeter', 0, 0, r, r, h, L - 2 * r, 'natural_wood_rails')
        self.box('perimeter_right', 'perimeter', W - r, 0, r, r, h, L - 2 * r, 'natural_wood_rails')
        for wall in p['walls']:
            self.wall(wall)
        return self

    def as_dict(self):
        meshes = list(self.parts.values())
        positions = [m['positions'][i:i + 3] for m in meshes for i in range(0, len(m['positions']), 3)]
        bounds = {'min': [min(v[i] for v in positions) for i in range(3)],
                  'max': [max(v[i] for v in positions) for i in range(3)]}
        return {'materials': self.materials, 'meshes': meshes, 'bounds_m': bounds,
                'meta': {'name': 'CyberBrick 80 x 120 cm textured map', 'version': 'v11',
                         'units': 'metres', 'up_axis': 'Y', 'width_axis': 'X', 'length_axis': 'Z',
                         'texture_uv_origin': 'top-left, matching glTF 2.0',
                         'map_only': True, 'floor_repeat_xy': [4, 6],
                         'semantic_object_counts': dict(collections.Counter(self.objects.values())),
                         'physical_measurements_verified': False,
                         'assumptions': self.p['assumed_not_physically_measured']}}


def write_glb(scene, out):
    binary = bytearray()
    gltf = {'asset': {'version': '2.0', 'generator': 'CyberBrick v11 build_model.py'},
            'scene': 0, 'scenes': [{'name': 'Map only - 800 x 1200 mm', 'nodes': []}],
            'nodes': [], 'meshes': [], 'materials': [], 'textures': [], 'images': [],
            'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}],
            'bufferViews': [], 'accessors': [], 'buffers': [],
            'extras': scene['meta']}

    def view(data, target=None):
        while len(binary) % 4:
            binary.append(0)
        idx = len(gltf['bufferViews'])
        v = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}
        if target:
            v['target'] = target
        gltf['bufferViews'].append(v)
        binary.extend(data)
        return idx

    def accessor(values, typ, component, arity, minmax=False):
        fmt = '<' + ('f' if component == 5126 else 'I') * len(values)
        idx = len(gltf['accessors'])
        acc = {'bufferView': view(struct.pack(fmt, *values), 34963 if typ == 'SCALAR' else 34962),
               'componentType': component, 'count': len(values) // arity, 'type': typ}
        if minmax:
            acc['min'] = [min(values[i::arity]) for i in range(arity)]
            acc['max'] = [max(values[i::arity]) for i in range(arity)]
        gltf['accessors'].append(acc)
        return idx

    tex_map = {}
    for mat in scene['materials']:
        m = {'name': mat['name'], 'doubleSided': False,
             'pbrMetallicRoughness': {'baseColorFactor': [linear_channel(v) for v in mat['color']] + [1],
                                     'metallicFactor': mat['metallic'], 'roughnessFactor': mat['roughness']}}
        if mat['texture']:
            if mat['texture'] not in tex_map:
                src = ROOT / mat['texture']
                img_idx = len(gltf['images'])
                gltf['images'].append({'name': src.stem, 'mimeType': 'image/png', 'bufferView': view(src.read_bytes())})
                tex_map[mat['texture']] = len(gltf['textures'])
                gltf['textures'].append({'sampler': 0, 'source': img_idx})
            m['pbrMetallicRoughness']['baseColorTexture'] = {'index': tex_map[mat['texture']]}
        gltf['materials'].append(m)

    groups = collections.OrderedDict()
    for mesh in scene['meshes']:
        groups.setdefault(mesh['object_name'], []).append(mesh)
    for name, primitives in groups.items():
        output = {'name': name, 'primitives': []}
        for mesh in primitives:
            output['primitives'].append({
                'attributes': {'POSITION': accessor(mesh['positions'], 'VEC3', 5126, 3, True),
                               'NORMAL': accessor(mesh['normals'], 'VEC3', 5126, 3),
                               'TEXCOORD_0': accessor(mesh['uvs'], 'VEC2', 5126, 2)},
                'indices': accessor(mesh['indices'], 'SCALAR', 5125, 1),
                'material': mesh['material'], 'mode': 4})
        gltf['scenes'][0]['nodes'].append(len(gltf['nodes']))
        gltf['nodes'].append({'name': name, 'mesh': len(gltf['meshes']), 'extras': {'kind': primitives[0]['kind']}})
        gltf['meshes'].append(output)
    gltf['buffers'] = [{'byteLength': len(binary)}]
    while len(binary) % 4:
        binary.append(0)
    js = json.dumps(gltf, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    js += b' ' * ((-len(js)) % 4)
    total = 12 + 8 + len(js) + 8 + len(binary)
    out.write_bytes(struct.pack('<4sII', b'glTF', 2, total) + struct.pack('<I4s', len(js), b'JSON') + js +
                    struct.pack('<I4s', len(binary), b'BIN\0') + binary)
    return gltf


def write_obj(scene, path):
    mtl = path.with_suffix('.mtl')
    lines = ['# CyberBrick 80 x 120 cm map only. Units: metres. Y up.',
             '# Floor top Y=0; width X=0..0.8; length Z=0..1.2.', 'mtllib ' + mtl.name]
    material_lines = ['# Texture paths are relative to this MTL file.']
    for mat in scene['materials']:
        rgb = ' '.join(f'{v:.7f}' for v in mat['color'])
        material_lines.extend(['newmtl ' + mat['name'], 'Ka 0.05 0.05 0.05', 'Kd ' + rgb,
                               'Ks 0.015 0.015 0.015', 'Ns 4', 'd 1', 'illum 2'])
        if mat['texture']:
            material_lines.append('map_Kd ../' + mat['texture'])
        material_lines.append('')
    vertex_offset = 1
    for mesh in scene['meshes']:
        lines.append('o ' + mesh['name'])
        lines.append('usemtl ' + scene['materials'][mesh['material']]['name'])
        lines.append('s off')
        p, n, uv = mesh['positions'], mesh['normals'], mesh['uvs']
        lines.extend('v ' + ' '.join(f'{v:.9f}' for v in p[i:i + 3]) for i in range(0, len(p), 3))
        lines.extend(f'vt {uv[i]:.9f} {1 - uv[i + 1]:.9f}' for i in range(0, len(uv), 2))
        lines.extend('vn ' + ' '.join(f'{v:.9f}' for v in n[i:i + 3]) for i in range(0, len(n), 3))
        for i in range(0, len(mesh['indices']), 3):
            indices = [k + vertex_offset for k in mesh['indices'][i:i + 3]]
            lines.append('f ' + ' '.join(f'{k}/{k}/{k}' for k in indices))
        vertex_offset += len(p) // 3
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    mtl.write_text('\n'.join(material_lines), encoding='utf-8')


def validate(scene, p, glb_path, gltf):
    assert scene['bounds_m'] == {'min': [0.0, -0.005, 0.0], 'max': [0.8, 0.1, 1.2]}
    counts = scene['meta']['semantic_object_counts']
    assert counts == {'floor': 1, 'perimeter': 4, 'wall_foot': 10, 'wall_panel': 10, 'wall_brace': 20}
    triangles = 0
    for mesh in scene['meshes']:
        for forbidden in ('target', 'robot', 'ball', 'spawn', 'magnet', 'arm', 'post', 'cord'):
            assert forbidden not in mesh['name'].lower(), mesh['name']
        ps = [mesh['positions'][i:i + 3] for i in range(0, len(mesh['positions']), 3)]
        ns = [mesh['normals'][i:i + 3] for i in range(0, len(mesh['normals']), 3)]
        assert len(ns) == len(ps) == len(mesh['uvs']) // 2
        assert all(math.isfinite(v) for v in mesh['positions'] + mesh['normals'] + mesh['uvs'])
        assert min(mesh['indices']) >= 0 and max(mesh['indices']) < len(ps)
        for j in range(0, len(mesh['indices']), 3):
            a, b, c = mesh['indices'][j:j + 3]
            face_normal = cross(sub(ps[b], ps[a]), sub(ps[c], ps[a]))
            assert dot(face_normal, ns[a]) > 1e-12, (mesh['name'], j)
            triangles += 1
    floor = next(m for m in scene['meshes'] if m['name'] == 'floor_base__floor_print')
    assert min(floor['uvs'][::2]) == 0 and max(floor['uvs'][::2]) == 4
    assert min(floor['uvs'][1::2]) == 0 and max(floor['uvs'][1::2]) == 6
    assert len(gltf['images']) == 5
    data = glb_path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    assert magic == b'glTF' and version == 2 and length == len(data)
    jslen, tag = struct.unpack_from('<I4s', data, 12)
    assert tag == b'JSON'
    reread = json.loads(data[20:20 + jslen])
    assert reread['asset']['version'] == '2.0'
    binlen, tag = struct.unpack_from('<I4s', data, 20 + jslen)
    assert tag == b'BIN\0'
    blob = data[28 + jslen:]
    assert len(blob) == binlen
    image_hashes = []
    for image in reread['images']:
        v = reread['bufferViews'][image['bufferView']]
        payload = blob[v['byteOffset']:v['byteOffset'] + v['byteLength']]
        assert payload.startswith(b'\x89PNG\r\n\x1a\n')
        source = ROOT / 'textures' / (image['name'] + '.png')
        assert payload == source.read_bytes()
        image_hashes.append({'name': image['name'], 'sha256': hashlib.sha256(payload).hexdigest()})
    for a in reread['accessors']:
        v = reread['bufferViews'][a['bufferView']]
        component_bytes = {5126: 4, 5125: 4}[a['componentType']]
        arity = {'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[a['type']]
        assert v['byteLength'] == a['count'] * component_bytes * arity
        assert v['byteOffset'] % 4 == 0 and v['byteOffset'] + v['byteLength'] <= len(blob)
    return {'result': 'PASS', 'bounds_m': scene['bounds_m'], 'floor_mm': [800, 1200, 5],
            'main_wall_axis': 'X (parallel to 800 mm width)', 'wall_groups': 2,
            'semantic_object_counts': counts, 'mesh_material_parts': len(scene['meshes']),
            'triangles': triangles, 'glb_nodes': len(gltf['nodes']), 'embedded_png_count': 5,
            'embedded_textures_match_sources': True, 'texture_hashes': image_hashes,
            'normals_match_triangle_winding': True, 'floor_texture_repetitions': [4, 6],
            'glb_bytes': len(data), 'glb_sha256': hashlib.sha256(data).hexdigest(),
            'excluded_geometry': ['striking apparatus', 'targets', 'robots', 'spawn rings'],
            'physical_measurements_verified': False,
            'inherited_T_panel_gap_mm': 17.5,
            'validation_scope': 'Geometry dimensions, UV repetition, indices, winding, GLB structure and embedded images. Layout positions are adapted assumptions, not physical measurements.'}


def main():
    MODEL.mkdir(exist_ok=True)
    if not PARAMS.exists():
        PARAMS.write_text(json.dumps(defaults(), ensure_ascii=False, indent=2), encoding='utf-8')
    params = json.loads(PARAMS.read_text(encoding='utf-8'))
    for texture in params['textures'].values():
        assert (ROOT / texture).is_file(), texture
    scene = Scene(params).build().as_dict()
    (SOURCE / 'scene.json').write_text(json.dumps(scene, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    glb_path = MODEL / 'cyber_arena_80x120_textured.glb'
    gltf = write_glb(scene, glb_path)
    write_obj(scene, MODEL / 'cyber_arena_80x120_textured.obj')
    report = validate(scene, params, glb_path, gltf)
    (SOURCE / 'model_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
