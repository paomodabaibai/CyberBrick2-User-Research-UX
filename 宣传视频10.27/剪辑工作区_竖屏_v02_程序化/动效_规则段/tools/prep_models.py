# 把 10-22 之前的机器人模型整理成可动画的部件：拳头 STL 按连通域拆开并减面、对比“收回/打出”找出运动件；巴掌 GLB 打印各部件包围盒。
# 输出 assets/models/punch_parts.glb 和 assets/models/rig.json。单位 mm，Z 朝上（和原模型一致）。
import json, pathlib, sys
sys.path.insert(0, r'C:\Users\Administrator\AppData\Local\Temp\claude\C--Users-Administrator\226f244b-41b6-4b0a-8934-41361d3c2ec5\scratchpad\pylibs')
import numpy as np
import trimesh

M = pathlib.Path(__file__).resolve().parents[1] / 'assets' / 'models'
palm = trimesh.load(M / 'palm_v02.glb')
print('== 巴掌', list(palm.geometry)[:3])
rig = {'palm': {}, 'punch': {}}
ps = trimesh.Scene()
for name in palm.graph.nodes_geometry:
    T, g = palm.graph[name]
    m = palm.geometry[g].copy(); m.apply_transform(T)
    b = m.bounds.round(1).tolist()
    rig['palm'][name] = b
    print(name, b, len(m.faces))
    if len(m.faces) > 160000: m = m.simplify_quadric_decimation(face_count=150000, aggression=2)
    ps.add_geometry(m, node_name=name, geom_name=name)
ps.export(M / 'palm_parts.glb')

a = trimesh.load(M / 'punch_whole.stl'); c = trimesh.load(M / 'punch_whole_out.stl')
print('== 拳头 面数', len(a.faces), len(c.faces), '界', a.bounds.round(1).tolist())
pa = a.split(only_watertight=False); pc = c.split(only_watertight=False)
print('连通域', len(pa), len(pc))
key = lambda m: (len(m.faces),)
used = set(); scene = trimesh.Scene()
for i, m in sorted(enumerate(pa), key=lambda x: -len(x[1].faces)):
    # 在“打出”里找同面数、形状最接近的件，算位移
    best, bd = None, 1e9
    for j, n in enumerate(pc):
        if j in used or len(n.faces) != len(m.faces): continue
        d = np.abs((n.bounds[1] - n.bounds[0]) - (m.bounds[1] - m.bounds[0])).sum() + 0.02 * np.linalg.norm(n.centroid - m.centroid)
        if d < bd: best, bd = j, d
    delta = [0, 0, 0]
    if best is not None:
        used.add(best); delta = (pc[best].bounds[0] - m.bounds[0]).round(2).tolist()
    faces = len(m.faces)
    out = m
    if faces > 160000:
        out = m.simplify_quadric_decimation(face_count=150000, aggression=2)
    name = f'p{i:02d}'
    scene.add_geometry(out, node_name=name, geom_name=name)
    rig['punch'][name] = {'bounds': m.bounds.round(1).tolist(), 'faces': faces, 'kept': len(out.faces), 'delta_out': delta}
    print(name, 'faces', faces, '→', len(out.faces), 'bounds', m.bounds.round(1).tolist(), 'out', delta)
scene.export(M / 'punch_parts.glb')
(M / 'rig.json').write_text(json.dumps(rig, ensure_ascii=False, indent=1), encoding='utf-8')
