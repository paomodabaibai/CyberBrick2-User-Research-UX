"""Extract the user's positioned fist and add a printable wrist socket."""
from pathlib import Path
import importlib.util
import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
import trimesh

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "拳头微调导出.stl"
DEST = HERE.parent / "拳头_全套打印包_2026-09-29"
DEST.mkdir(exist_ok=True)

source_file = HERE.parent / "队友拳头模块_2026-09-28_增量审阅" / "04_结构与硬件" / "Otto_CB1出拳头部_v01" / "build_punch_head.py"
spec = importlib.util.spec_from_file_location("punch_source", source_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cq = module.cq

assembly = trimesh.load(SOURCE, force="mesh", process=True)
adj = assembly.face_adjacency
graph = sp.coo_matrix(
    (np.ones(len(adj) * 2, dtype=np.uint8),
     (np.r_[adj[:, 0], adj[:, 1]], np.r_[adj[:, 1], adj[:, 0]])),
    shape=(len(assembly.faces),) * 2,
).tocsr()
_, labels = connected_components(graph, directed=False)
fist_id = int(np.argmax(np.bincount(labels)))
fist = assembly.submesh([np.flatnonzero(labels == fist_id)], append=True, repair=False)
assert len(fist.faces) > 500000 and fist.is_watertight

# Retracted assembly coordinates: carriage tongue spans X18..30, Y+-6,
# Z41.8..49.8. A 0.3 mm side clearance socket opens towards negative X.
socket = module.box(18, 16, 12, 25, 0, 39.8)
socket = socket.cut(module.box(16, 12.6, 8.6, 23, 0, 41.5))
socket = socket.cut(module.cyl(1.65, 14, 25, 0, 38.8))
stem = module.box(37, 10, 8, 51.5, 0, 41.8)
connector = socket.union(stem)
alternative = DEST / "备选_请勿与05一体拳头同时打印"
alternative.mkdir(exist_ok=True)
connector_file = alternative / "腕部连接杆_需另行固定拳头.stl"
cq.exporters.export(connector, str(connector_file))

connector_mesh = trimesh.load(connector_file, force="mesh")
combined = trimesh.boolean.union([fist, connector_mesh], engine="manifold")
assert combined is not None and combined.is_watertight
assert combined.body_count == 1, "Fist and stem did not fuse; inspect wrist overlap"
combined.apply_translation(-combined.bounds[0])
combined.export(DEST / "05_拳头与腕部连接_一体试打印.stl")
print("fist faces", len(fist.faces), "combined faces", len(combined.faces), "bounds", combined.extents)
