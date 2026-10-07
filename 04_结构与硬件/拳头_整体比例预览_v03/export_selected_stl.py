"""Export the user's chosen fist proportions as editable mesh references.

Assemblies are multi-shell STL placement references, not printable solids.
"""
from pathlib import Path
import json
import math
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT = HERE / '按用户参数导出_STL'
OUTPUT.mkdir(exist_ok=True)
ASSEMBLY = ROOT / '04_结构与硬件/队友拳头模块_2026-09-28_增量审阅/04_结构与硬件/Otto_CB1出拳头部_v01/output'
FIST = ROOT / '04_结构与硬件/拳头_3D生成参考/红色拳头_AI原始模型_v01.stl'

PARAMS = {
    'fist_height_mm': 46,
    'module_offset_mm': -22,
    'fist_yaw_deg': 14,
    'wrist_extension_mm': 38,
    'fist_x_mm': 0,
    'fist_y_mm': 0,
    'fist_pitch_deg': 0,
    'fist_roll_deg': 0,
    'crank_radius_mm': 10,
    'rod_centres_mm': 34,
    'design_stroke_mm': 20,
    'preview_wrist_anchor_z_mm': 45.8,
    'original_fist_wrist_center': [0.14354, 0.492645323, 0.473214],
    'coordinate_axes': 'X=forward, Y=robot left, Z=up; body top Z=0',
}

def original_fist_at(slider_x):
    m = trimesh.load(FIST, force='mesh', process=False)
    v = m.vertices.copy()
    # Source Y points toward the wrist; convert that direction to -X.
    v = np.column_stack((0.492645323 - v[:, 1], v[:, 0] - 0.14354, v[:, 2] - 0.473214))
    v *= PARAMS['fist_height_mm']
    for axis, angle in (([1, 0, 0], PARAMS['fist_roll_deg']),
                        ([0, 1, 0], PARAMS['fist_pitch_deg']),
                        ([0, 0, 1], PARAMS['fist_yaw_deg'])):
        if angle:
            v = trimesh.transform_points(v, trimesh.transformations.rotation_matrix(math.radians(angle), axis))
    v += np.array([slider_x + 10 + PARAMS['wrist_extension_mm'] + PARAMS['fist_x_mm'] + PARAMS['module_offset_mm'],
                   PARAMS['fist_y_mm'], PARAMS['preview_wrist_anchor_z_mm']])
    m.vertices = v
    return m

def extender_at(slider_x):
    # The reference preview used an 8x10 rectangular placeholder. This is
    # deliberately not fused to the printed carriage or source fist mesh.
    length = PARAMS['wrist_extension_mm'] + PARAMS['fist_x_mm']
    if length <= 0:
        return None
    m = trimesh.creation.box([length, 10, 8])
    m.apply_translation([slider_x + 10 + length / 2 + PARAMS['module_offset_mm'],
                         PARAMS['fist_y_mm'] / 2, PARAMS['preview_wrist_anchor_z_mm']])
    return m

def load_mechanism(angle):
    source = ASSEMBLY / f'assembly_{angle:03d}deg.glb'
    scene = trimesh.load(source, force='scene')
    parts = []
    for name in scene.graph.nodes_geometry:
        if name in {'glove', 'sensor_bracket'}:
            continue
        transform, geometry_name = scene.graph[name]
        m = scene.geometry[geometry_name].copy()
        m.apply_transform(transform)
        if name != 'body_collar':
            m.apply_translation([PARAMS['module_offset_mm'], 0, 0])
        parts.append((name, m))
    # In the source mechanism, retracted slider center X=30; extended X=50.
    slider_x = 30 if angle == 180 else 50
    return parts, slider_x

def load_otto():
    source = ROOT / '01_研究参考/robot-battle-reference/Otto-V9/3Dprint'
    rotate = trimesh.transformations.rotation_matrix(math.pi / 2, [0, 0, 1])
    parts = []
    for part in ('body', 'Leg', 'foot'):
        m = trimesh.load(source / f'OttoDIY_{part}_V9.stl', force='mesh')
        copies = [m]
        if part != 'body':
            mirrored = m.copy()
            mirrored.apply_transform(np.diag([-1, 1, 1, 1]))
            copies.append(mirrored)
        for index, copy in enumerate(copies):
            copy.apply_transform(rotate)
            parts.append((f'otto_{part}_{index}', copy))
    return parts

def save_combined(path, named_meshes):
    combined = trimesh.util.concatenate([m for _, m in named_meshes])
    combined.export(path)
    return {'file': path.name, 'bytes': path.stat().st_size,
            'triangles': len(combined.faces), 'bounds_mm': np.round(combined.bounds, 3).tolist(),
            'separate_shells_expected': True}

metadata = {'chosen_parameters': PARAMS, 'source_fist_watertight': False, 'exports': []}
otto = load_otto()
for angle, state in ((180, '收回'), (0, '打出')):
    mechanism, slider_x = load_mechanism(angle)
    fist = original_fist_at(slider_x)
    extension = extender_at(slider_x)
    module = mechanism + [('新拳头', fist)]
    if extension is not None:
        module.append(('腕部延长示意', extension))
    overall = otto + module
    metadata['exports'].append(save_combined(OUTPUT / f'整机_{state}_参数预览.stl', overall))
    metadata['exports'].append(save_combined(OUTPUT / f'攻击模块_{state}_参数预览.stl', module))
    if angle == 180:
        fist.export(OUTPUT / '新拳头_已缩放旋转定位.stl')
        if extension is not None:
            extension.export(OUTPUT / '腕部延长_尺寸示意_不可直接打印.stl')
        metadata['assembly_component_names'] = [name for name, _ in overall]
(OUTPUT / '所选参数与导出信息.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
for entry in metadata['exports']:
    print(entry['file'], entry['bytes'], entry['triangles'], entry['bounds_mm'])
