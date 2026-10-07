from pathlib import Path
import json
import numpy as np
import trimesh

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SRC = ROOT / '04_结构与硬件/队友拳头模块_2026-09-28_增量审阅/04_结构与硬件/Otto_CB1出拳头部_v01/output'
meshes = []

def add(name, mesh, color, kind='fixed', target=650):
    m = mesh.copy()
    if len(m.faces) > target:
        m = m.simplify_quadric_decimation(face_count=target)
    meshes.append(dict(name=name, v=np.round(m.vertices, 4).tolist(), f=m.faces.tolist(), color=color, kind=kind))

scene = trimesh.load(SRC / 'assembly_180deg.glb', force='scene')
for name in scene.graph.nodes_geometry:
    if name == 'glove' or name == 'sensor_bracket':
        continue
    # Hidden gearbox internals omitted for preview performance only.
    if name.startswith('ref_') and name not in ('ref_07', 'ref_08', 'ref_10', 'ref_11'):
        continue
    transform, key = scene.graph[name]
    mesh = scene.geometry[key].copy()
    mesh.apply_transform(transform)
    kind = 'fixed'
    if name in ('crank', 'output_gear'): kind = 'crank'
    elif name in ('pin_A', 'washer_A'): kind = 'pinA'
    elif name == 'link': kind = 'link'
    elif name in ('carriage', 'pin_B', 'washer_B'): kind = 'slide'
    color = 'frame' if name in ('base', 'body_collar') else 'metal'
    if name == 'carriage': color = 'carriage'
    if name == 'link': color = 'link'
    if name == 'crank': color = 'crank'
    add(name, mesh, color, kind, 2300 if name == 'base' else 850 if name.startswith('ref_') else 650)

stls = ROOT / '01_研究参考/robot-battle-reference/Otto-V9/3Dprint'
rotate = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1])
for part in ('body', 'Leg', 'foot'):
    m = trimesh.load(stls / f'OttoDIY_{part}_V9.stl')
    copies = [m]
    if part != 'body':
        other = m.copy()
        other.apply_transform(np.diag([-1, 1, 1, 1]))
        copies.append(other)
    for i, cp in enumerate(copies):
        cp.apply_transform(rotate)
        add(f'otto_{part}_{i}', cp, 'body', 'body', 1000 if part == 'body' else 650)

fist = trimesh.load(OUT / 'fist_preview_mesh.ply')
v = fist.vertices.copy()
# AI model: wrist toward +Y, fingers toward -Y. Register wrist rear face
# to slider tongue entry X=slider+10; this is visual placement, not a socket.
fist.vertices = np.column_stack((0.492645323 - v[:, 1], v[:, 0] - 0.14354, v[:, 2] - 0.473214))
add('new_fist', fist, 'fist', 'fist', 6500)

data = json.dumps(meshes, separators=(',', ':'))
(OUT / 'preview_meshes.json').write_text(data, encoding='utf-8')
template = (OUT / 'preview_template.html').read_text(encoding='utf-8')
html = template.replace('__MESH_DATA__', data)
dest = Path(r'C:\Users\Administrator\.codex\visualizations\2026\09\14\01a09d93-5828-7951-8f50-b4e4bdacf50a\otto-fist-proportions.html')
dest.write_text(html, encoding='utf-8')
assert dest.stat().st_size < 1024 * 1024, dest.stat().st_size
print('Preview bytes:', dest.stat().st_size, 'triangles:', sum(len(m['f']) for m in meshes))
