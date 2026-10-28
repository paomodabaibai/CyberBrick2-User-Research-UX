"""Build a printable, map-only 80 x 120 cm CyberBrick arena package.

The source map uses X=800 mm, Z=1200 mm and Y as height.  This script
converts that presentation model to printer coordinates (X/Y bed, Z height),
splits the floor into a 3 x 5 grid, adds lower-layer tongue-and-groove seams,
and writes standard 3MF model files.  The 3MFs are printer-ready model
plates; final machine/material slicing is intentionally left to Bambu Studio
because the exact filament profile and purge tower policy belong to the
printer owner.

Only the floor, perimeter and T walls are generated.  Targets, robots,
striking mechanisms and all other gameplay hardware are excluded.
"""
from __future__ import annotations

import json
import math
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "plates"
STL = ROOT / "stl"
SEAM = 0.4
TONGUE = 7.0
FLOOR_THICK = 5.0
FLOOR_TOP_SPLIT = 2.0
PRINT_X = 300.0  # H2D dual-nozzle intersection, official nominal envelope.
PRINT_Y = 320.0
PRINT_Z = 325.0
PURGE_LANE = 25.0
SAFE_X = PRINT_X - PURGE_LANE
SAFE_Y = PRINT_Y - 10.0


@dataclass
class Mesh:
    name: str
    vertices: list[tuple[float, float, float]]
    triangles: list[tuple[int, int, int]]

    def __init__(self, name: str):
        self.name = name
        self.vertices = []
        self.triangles = []

    def merge(self, other: "Mesh") -> None:
        off = len(self.vertices)
        self.vertices.extend(other.vertices)
        self.triangles.extend((a + off, b + off, c + off) for a, b, c in other.triangles)

    def translated(self, x: float, y: float, z: float = 0.0) -> "Mesh":
        out = Mesh(self.name)
        out.vertices = [(a + x, b + y, c + z) for a, b, c in self.vertices]
        out.triangles = list(self.triangles)
        return out

    def bounds(self) -> tuple[list[float], list[float]]:
        lo = [min(v[i] for v in self.vertices) for i in range(3)]
        hi = [max(v[i] for v in self.vertices) for i in range(3)]
        return lo, hi


def _orient_faces(vertices: list[tuple[float, float, float]], faces: list[list[int]]) -> list[tuple[int, int, int]]:
    center = tuple(sum(v[i] for v in vertices) / len(vertices) for i in range(3))
    out: list[tuple[int, int, int]] = []
    for face in faces:
        a, b, c = (vertices[i] for i in face[:3])
        u = tuple(b[i] - a[i] for i in range(3))
        v = tuple(c[i] - a[i] for i in range(3))
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        fc = tuple(sum(vertices[j][i] for j in face) / len(face) for i in range(3))
        if sum(n[i] * (fc[i] - center[i]) for i in range(3)) < 0:
            face = list(reversed(face))
        for i in range(1, len(face) - 1):
            out.append((face[0], face[i], face[i + 1]))
    return out


def box(name: str, x: float, y: float, z: float, w: float, d: float, h: float) -> Mesh:
    m = Mesh(name)
    m.vertices = [(x, y, z), (x + w, y, z), (x + w, y + d, z), (x, y + d, z),
                  (x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)]
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5],
             [2, 3, 7, 6], [3, 0, 4, 7]]
    m.triangles = _orient_faces(m.vertices, faces)
    return m


def triangular_prism(name: str, u0: float, u1: float, triangle: list[tuple[float, float]]) -> Mesh:
    """Prism along local u; triangle coordinates are (v, height)."""
    m = Mesh(name)
    m.vertices = [(u0, v, h) for v, h in triangle] + [(u1, v, h) for v, h in triangle]
    faces = [[0, 1, 2], [5, 4, 3], [0, 3, 4, 1], [1, 4, 5, 2], [2, 5, 3, 0]]
    m.triangles = _orient_faces(m.vertices, faces)
    return m


def floor_cells(n: int, total: float) -> list[tuple[float, float]]:
    pitch = total / n
    # Each returned pair is a *solid* cell interval.  Internal boundaries have
    # a 0.4 mm air seam: the first/last cell lose half a seam and the middle
    # cells lose a full seam.  The outer footprint remains exactly 800 x 1200.
    cells = []
    for i in range(n):
        start = 0.0 if i == 0 else i * pitch + SEAM / 2
        end = total if i == n - 1 else (i + 1) * pitch - SEAM / 2
        cells.append((start, end))
    return cells


X_CELLS = floor_cells(3, 800.0)
Y_CELLS = floor_cells(5, 1200.0)


def floor_tile(row: int, col: int) -> Mesh:
    x0, x1 = X_CELLS[col]
    y0, y1 = Y_CELLS[row]
    w, d = x1 - x0, y1 - y0
    m = Mesh(f"floor_R{row + 1}C{col + 1}")
    # A full 3 mm walking slab plus a 2 mm lower layer.  The lower layer is
    # recessed 7 mm on female west/south edges; neighboring male tongues slide
    # into those recesses while the top surface remains flat.
    m.merge(box(m.name, 0, 0, FLOOR_TOP_SPLIT, w, d, FLOOR_THICK - FLOOR_TOP_SPLIT))
    rx = TONGUE if col > 0 else 0.0
    ry = TONGUE if row > 0 else 0.0
    m.merge(box(m.name, rx, ry, 0, w - rx, d - ry, FLOOR_TOP_SPLIT))
    if col < 2:
        m.merge(box(m.name, w, ry, 0, TONGUE, d - ry, FLOOR_TOP_SPLIT))
    if row < 4:
        m.merge(box(m.name, rx, d, 0, w - rx, TONGUE, FLOOR_TOP_SPLIT))
    return m


def rail_x(name: str, length: float) -> Mesh:
    return box(name, 0, 0, 0, length, 20.0, 30.0)


def rail_y(name: str, length: float) -> Mesh:
    return box(name, 0, 0, 0, 20.0, length, 30.0)


def wall_local(name: str, length: float, height: float, width: float = 40.0, thickness: float = 5.0) -> Mesh:
    """A wall assembly standing on its 40 mm foot, in local u/v coordinates."""
    foot = 5.0
    panel_v = (width - thickness) / 2.0
    m = Mesh(name)
    m.merge(box(name, 0, 0, 0, length, width, foot))
    m.merge(box(name, 0, panel_v, foot, length, thickness, height - foot))
    # Two small triangular braces make a vertical panel printable without a
    # support tree and keep the part rigid after assembly.
    m.merge(triangular_prism(name, 20.0, 25.0,
                             [(panel_v, foot), (max(0.0, panel_v - 15.0), foot), (panel_v, foot + 30.0)]))
    m.merge(triangular_prism(name, length - 25.0, length - 20.0,
                             [(panel_v + thickness, foot), (min(width, panel_v + thickness + 15.0), foot),
                              (panel_v + thickness, foot + 30.0)]))
    return m


WALLS = [
    ("front_main_1", 20.0, 320.0, 115.0, 60.0, "X"),
    ("front_main_2", 135.0, 320.0, 115.0, 80.0, "X"),
    ("front_main_3", 250.0, 320.0, 115.0, 100.0, "X"),
    ("front_main_4", 365.0, 320.0, 115.0, 80.0, "X"),
    ("front_T_branch", 320.0, 360.0, 120.0, 80.0, "Y"),
    ("back_main_1", 665.0, 840.0, 115.0, 60.0, "X"),
    ("back_main_2", 550.0, 840.0, 115.0, 80.0, "X"),
    ("back_main_3", 435.0, 840.0, 115.0, 100.0, "X"),
    ("back_main_4", 320.0, 840.0, 115.0, 80.0, "X"),
    ("back_T_branch", 440.0, 720.0, 120.0, 80.0, "Y"),
]


def wall_mesh(spec: tuple[str, float, float, float, float, str]) -> Mesh:
    name, x, y, length, height, axis = spec
    local = wall_local(name, length, height)
    out = Mesh(name)
    for vx, vy, vz in local.vertices:
        if axis == "X":
            out.vertices.append((x + vx, y + vy, vz))
        else:
            # Source-map branch transform: local u maps to +map-Y, local v to
            # -map-X.  The 40 mm foot remains within x..x+40.
            out.vertices.append((x + 40.0 - vy, y + vx, vz))
    out.triangles = list(local.triangles)
    return out


def mesh_xml(mesh: Mesh) -> str:
    verts = "".join(f'<vertex x="{v[0]:.5f}" y="{v[1]:.5f}" z="{v[2]:.5f}"/>' for v in mesh.vertices)
    tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.triangles)
    return f'<mesh><vertices>{verts}</vertices><triangles>{tris}</triangles></mesh>'


def write_3mf(path: Path, meshes: list[Mesh], items: list[tuple[int, float, float, float]], metadata: dict) -> None:
    resources = []
    for i, mesh in enumerate(meshes, 1):
        resources.append(f'<object id="{i}" type="model" name="{escape(mesh.name)}">{mesh_xml(mesh)}</object>')
    builds = []
    for obj, x, y, z in items:
        builds.append(f'<item objectid="{obj}" transform="1 0 0 0 1 0 0 0 1 {x:.5f} {y:.5f} {z:.5f}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<resources>' + "".join(resources) + '</resources><build>' + "".join(builds) + '</build></model>')
    content = ('<?xml version="1.0" encoding="UTF-8"?>'
               '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
               '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
               '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
               '<Default Extension="json" ContentType="application/json"/>'
               '<Override PartName="/3D/3dmodel.model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
               '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3d/2013/01/3dmodel"/>'
            '</Relationships>')
    metadata_text = json.dumps(metadata, ensure_ascii=False, indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/print_manifest.json", metadata_text)


def write_binary_stl(path: Path, mesh: Mesh) -> None:
    def normal(a, b, c):
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        mag = math.sqrt(sum(x * x for x in n)) or 1.0
        return [x / mag for x in n]
    import struct
    data = bytearray(b"CyberBrick printable map STL".ljust(80, b" "))
    data.extend(struct.pack("<I", len(mesh.triangles)))
    for ia, ib, ic in mesh.triangles:
        a, b, c = mesh.vertices[ia], mesh.vertices[ib], mesh.vertices[ic]
        n = normal(a, b, c)
        data.extend(struct.pack("<3f", *n))
        data.extend(struct.pack("<9f", *(a + b + c)))
        data.extend(struct.pack("<H", 0))
    path.write_bytes(data)


def pack_plate(name: str, meshes: list[Mesh], gap: float = 8.0) -> dict:
    """Simple row packer within the H2D dual-nozzle envelope."""
    x = y = row_h = 0.0
    positions = []
    max_x = max_y = max_z = 0.0
    for mesh in meshes:
        lo, hi = mesh.bounds()
        w, d, h = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
        if w > SAFE_X + 1e-6 or d > SAFE_Y + 1e-6 or h > PRINT_Z + 1e-6:
            raise ValueError(f"{mesh.name} exceeds H2D purge-reserved envelope: {(w, d, h)}")
        if x and x + w > SAFE_X:
            x = 0.0
            y += row_h + gap
            row_h = 0.0
        if y + d > SAFE_Y:
            raise ValueError(f"plate {name} does not fit: {mesh.name}")
        positions.append((x - lo[0], y - lo[1]))
        x += w + gap
        row_h = max(row_h, d)
        max_x = max(max_x, x - gap)
        max_y = max(max_y, y + d)
        max_z = max(max_z, h)
    items = [(i + 1, pos[0], pos[1], -min(0.0, meshes[i].bounds()[0][2])) for i, pos in enumerate(positions)]
    meta = {'plate_name': name, 'printer_family': 'Bambu Lab H series / H2D dual-nozzle intersection',
            'nominal_build_volume_mm': [PRINT_X, PRINT_Y, PRINT_Z], 'purge_tower_reserved_lane_mm': PURGE_LANE,
            'model_envelope_mm': [round(max_x, 3), round(max_y, 3), round(max_z, 3)],
            'objects': [m.name for m in meshes], 'recommended_layer_height_mm': 0.20,
            'recommended_wall_count': 3, 'recommended_infill_percent': 15,
            'supports': 'off for floor/walls/rails; enable only if slicer reports a bridge issue',
            'multi_color': 'keep a 25 mm purge-tower lane at the right edge; monochrome may use the full 300 mm width'}
    out = OUT / f"{name}.3mf"
    write_3mf(out, meshes, items, meta)
    return {'file': str(out.relative_to(ROOT)).replace('\\', '/'), **meta}


def make_clip_pack() -> Mesh:
    m = Mesh("seam_key_clip")
    # A removable underside dog-bone key. It is deliberately 2 mm thick so it
    # remains below the 5 mm walking slabs and can be printed flat.
    neck = box(m.name, 16.0, 7.0, 0, 12.0, 8.0, 2.0)
    m.merge(neck)
    m.merge(box(m.name, 0, 0, 0, 20.0, 18.0, 2.0))
    m.merge(box(m.name, 24.0, 0, 0, 20.0, 18.0, 2.0))
    return m


def assembly_meshes() -> tuple[list[Mesh], list[tuple[int, float, float, float]]]:
    meshes: list[Mesh] = []
    items: list[tuple[int, float, float, float]] = []
    for row in range(5):
        for col in range(3):
            meshes.append(floor_tile(row, col))
            items.append((len(meshes), X_CELLS[col][0], Y_CELLS[row][0], 0.0))
    # Perimeter is split at the same seams as the floor, preserving the exact
    # 800 x 1200 outer footprint while keeping every segment under 275 mm.
    for col in range(3):
        x0, x1 = X_CELLS[col]
        length = x1 - x0
        for side in ("front", "back"):
            m = rail_x(f"rail_{side}_{col + 1}", length)
            meshes.append(m)
            items.append((len(meshes), x0, 0.0 if side == "front" else 1180.0, 5.0))
    for row in range(5):
        y0, y1 = Y_CELLS[row]
        rail_y0, rail_y1 = max(20.0, y0), min(1180.0, y1)
        length = rail_y1 - rail_y0
        for side in ("left", "right"):
            m = rail_y(f"rail_{side}_{row + 1}", length)
            meshes.append(m)
            items.append((len(meshes), 0.0 if side == "left" else 780.0, rail_y0, 5.0))
    for spec in WALLS:
        meshes.append(wall_mesh(spec))
        _, x, y, _, _, axis = spec
        items.append((len(meshes), 0.0, 0.0, 5.0))
    # In the assembly reference, walls are already in map coordinates. The
    # wall_mesh function emits global coordinates, so their items have no move.
    return meshes, items


def top_svg(path: Path) -> None:
    sx, sy = 0.45, 0.45
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{800*sx+60:.1f}" height="{1200*sy+80:.1f}" viewBox="0 0 {800*sx+60:.1f} {1200*sy+80:.1f}">',
             '<rect width="100%" height="100%" fill="#101820"/>',
             f'<rect x="30" y="30" width="{800*sx:.1f}" height="{1200*sy:.1f}" fill="#d7e3e0" stroke="#ffd22e" stroke-width="2"/>']
    for i in range(1, len(X_CELLS)):
        x = (X_CELLS[i - 1][1] + X_CELLS[i][0]) / 2
        xx = 30 + x * sx
        lines.append(f'<line x1="{xx:.1f}" y1="30" x2="{xx:.1f}" y2="{30+1200*sy:.1f}" stroke="#52656e" stroke-dasharray="3 3"/>')
    for i in range(1, len(Y_CELLS)):
        y = (Y_CELLS[i - 1][1] + Y_CELLS[i][0]) / 2
        yy = 30 + y * sy
        lines.append(f'<line x1="30" y1="{yy:.1f}" x2="{30+800*sx:.1f}" y2="{yy:.1f}" stroke="#52656e" stroke-dasharray="3 3"/>')
    for name, x, y, length, height, axis in WALLS:
        if axis == "X":
            lines.append(f'<rect x="{30+x*sx:.1f}" y="{30+y*sy:.1f}" width="{length*sx:.1f}" height="18" fill="#466b74"/>')
        else:
            lines.append(f'<rect x="{30+x*sx:.1f}" y="{30+y*sy:.1f}" width="18" height="{length*sy:.1f}" fill="#466b74"/>')
    lines.append('<text x="30" y="25" fill="#fff" font-family="sans-serif" font-size="14">CyberBrick 80×120 cm · map only · 3×5 floor grid</text></svg>')
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    STL.mkdir(exist_ok=True)
    (ROOT / "previews").mkdir(exist_ok=True)

    manifest = {
        'version': 'H2D-v01', 'units': 'mm', 'map_size_mm': [800, 1200],
        'source_map': '../../贴图地图模型_80x120cm_v11/source/layout_parameters.json',
        'excluded_geometry': ['striking apparatus', 'targets', 'robots', 'spawn rings', 'attack hardware'],
        'floor_grid': {'columns': 3, 'rows': 5, 'seam_mm': SEAM, 'tongue_length_mm': TONGUE,
                       'x_cells_mm': X_CELLS, 'y_cells_mm': Y_CELLS, 'floor_thickness_mm': FLOOR_THICK},
        'printer': {'family': 'Bambu Lab H series', 'target': 'H2D dual-nozzle intersection',
                    'build_volume_mm': [PRINT_X, PRINT_Y, PRINT_Z], 'purge_lane_mm': PURGE_LANE,
                    'safe_model_width_mm': SAFE_X, 'safe_model_depth_mm': SAFE_Y},
        'physical_measurements_verified': False,
        'note': 'Digital geometry and 3MF package checks only; no physical fit, first-layer or robot collision test has been performed.'
    }
    # Floor: one plate per tile, with a 25 mm right-side purge corridor.
    plate_records = []
    for row in range(5):
        for col in range(3):
            name = f"floor_R{row + 1}C{col + 1}"
            plate_records.append(pack_plate(name, [floor_tile(row, col)]))
            write_binary_stl(STL / f"{name}.stl", floor_tile(row, col))

    # Walls: keep each wall as a named, rigid assembly; split front/back so the
    # two wall groups can be printed independently.
    for group, specs in (("walls_front", WALLS[:5]), ("walls_back", WALLS[5:])):
        meshes = [wall_mesh(s) for s in specs]
        plate_records.append(pack_plate(group, meshes))
        for mesh in meshes:
            write_binary_stl(STL / f"{mesh.name}.stl", mesh)

    # Rails: two plates per direction group. Each segment is a separate piece.
    rails_ns = [rail_x(f"rail_{side}_{col + 1}", X_CELLS[col][1] - X_CELLS[col][0]) for side in ("front", "back") for col in range(3)]
    rails_ew = [rail_y(f"rail_{side}_{row + 1}", min(1180.0, Y_CELLS[row][1]) - max(20.0, Y_CELLS[row][0])) for side in ("left", "right") for row in range(5)]
    for i, group in enumerate((rails_ns[:3], rails_ns[3:], rails_ew[:5], rails_ew[5:]), 1):
        name = ["rails_NS_A", "rails_NS_B", "rails_EW_A", "rails_EW_B"][i - 1]
        plate_records.append(pack_plate(name, group))
        for mesh in group:
            write_binary_stl(STL / f"{mesh.name}.stl", mesh)

    # Optional spare keys. The tongue-and-groove floor does the locating; keys
    # are useful for a removable underside reinforcement at high-traffic seams.
    key = make_clip_pack()
    plate_records.append(pack_plate("seam_key_pack", [key] * 12))
    write_binary_stl(STL / "seam_key_clip.stl", key)

    manifest['plates'] = plate_records
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    top_svg(ROOT / "previews" / "assembly_layout.svg")

    # Assembly reference 3MF (not itself a printer plate): a complete, map-only
    # layout for checking wall positions and the 800 x 1200 footprint.
    floor_and_items, items = assembly_meshes()
    write_3mf(ROOT / "assembly_reference_map_only.3mf", floor_and_items, items,
              {'type': 'assembly_reference_only', 'map_size_mm': [800, 1200],
               'excluded_geometry': manifest['excluded_geometry'], 'physical_measurements_verified': False})

    readme = ROOT / "README.md"
    readme.write_text("""# 80×120 cm 地图 · H 系列 3MF 打印包 v01\n\n本包基于 `06_游戏设计/贴图地图模型_80x120cm_v11` 生成，包含地板、外围护沿、两组错位 T 墙和底部加强片；**不包含击打装置、球靶、机器人或任何攻击机构**。模型尺寸为 800×1200 mm，墙段高度沿用 60/80/100/80 mm，墙板厚 5 mm，墙脚宽 40 mm。当前尺寸仍是数字设计假设，尚未做实体量测和机器人碰撞验收。\n\n## 文件\n\n- `plates/floor_R1C1.3mf` … `floor_R5C3.3mf`：15 块地板，每块单独一盘。\n- `plates/walls_front.3mf`、`walls_back.3mf`：两组各 5 件墙体总成。墙脚朝床，墙板竖直，三角加强片已建模。\n- `plates/rails_NS_A/B.3mf`、`rails_EW_A/B.3mf`：外围护沿分段。\n- `plates/seam_key_pack.3mf`：12 个可选底部桥片；地板主定位由边缘下层榫舌完成。\n- `assembly_reference_map_only.3mf`：完整 800×1200 mm 装配参考，**不能直接作为一盘打印**。\n- `manifest.json`：尺寸、板号、打印包络和验证信息。\n- `previews/assembly_layout.svg`：俯视排布。\n\n## H 系列尺寸与多色余量\n\n本包按拓竹 H2D 官方双喷嘴交集 300×320×325 mm 设计；所有打印盘在 X 方向保留 25 mm 擦料塔通道，模型安全宽度为 275 mm，深度控制在 310 mm 内。最大的地板榫舌后包络约 273.5×246.8 mm，因此可以在右侧放置小型擦料塔。若使用单色，可在切片器中关闭擦料塔并使用更宽的工作区；若使用多色，请保持右侧 25 mm 空带，不要让自动排布把模型填满整盘。官方 H2D 规格也列出单喷嘴 325×320×325 mm、双喷嘴总工作空间 350×320×325 mm；本包采用更保守的 300 mm 交集。\n\n## 拼接方式\n\n地板顶面厚 5 mm，内部接缝名义 0.4 mm。每块地板下层在西/南边留 7 mm 凹槽，在东/北边带 7 mm 榫舌；从左下角开始按行装配，先放南侧，再把相邻块沿水平方向滑入。榫舌位于下层，行走面不产生凸起。打印后清除首层象脚再装配；若桌面或材料收缩导致松动，可在底面桥片上点少量可移胶。\n\n外围护沿按同一 3×5 网格分段，前/后边各 3 段，左/右边各 5 段。墙体和护沿均以地板顶面为基准（墙/护沿底部高度 5 mm）；建议用薄可移胶固定，胶厚未计入模型。\n\n## 建议切片参数\n\nPLA/PETG 均可作为首印材料：0.20 mm 层高、3 道墙、15% 网格填充、4 层底/顶，地板与护沿关闭支撑，墙体通常关闭支撑。先用 `floor_R1C1.3mf` 和一件墙体做首层、榫舌间隙和翘曲试验，再批量打印。3MF 中包含打印盘和推荐参数元数据，但最终切片仍需在 Bambu Studio 中选择实际打印机、喷嘴、材料和擦料塔设置；本机未生成 G-code，也未声称已完成实体试印。\n\n## 验证边界\n\n脚本会检查 3MF ZIP 结构、网格三角形数量、打印包络、地图边界和排除项。验证结果只覆盖数字几何，不能代替首层、榫舌配合、墙体强度、机器人通行或实机攻击测试。\n""", encoding="utf-8")

    # Bundle for convenient transfer while retaining the unpacked editable set.
    zip_path = ROOT.parent / "CyberBrick_80x120_H2D_3MF_打印包_v01.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in ROOT.rglob("*"):
            if p == zip_path or p.is_dir():
                continue
            z.write(p, p.relative_to(ROOT.parent))

    print(json.dumps({'result': 'PASS', 'plates': len(plate_records), 'zip': str(zip_path),
                      'floor_grid': [3, 5], 'map_size_mm': [800, 1200],
                      'purge_lane_mm': PURGE_LANE}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
