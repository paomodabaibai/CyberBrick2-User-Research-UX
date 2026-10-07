"""Render annotated views from the five actual print STLs. No hardware control."""
from pathlib import Path
import numpy as np
import trimesh
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
MODEL = PROJECT / "04_结构与硬件" / "队友拳头模块_2026-09-28_增量审阅" / "04_结构与硬件" / "Otto_CB1出拳头部_v01" / "output" / "assembly_180deg.glb"
FIST_SOURCE = PROJECT / "04_结构与硬件" / "拳头_整体比例预览_v03" / "拳头微调导出.stl"
PRINTS = [next(ROOT.glob(f"{i:02d}_*.stl")) for i in range(1, 6)]
COLORS = ["#46596B", "#F5B346", "#31B3A3", "#398CC9", "#E34B4B"]
NAMES = ["01 开放式底座", "02 曲柄", "03 连杆", "04 滑架", "05 拳头＋腕杆"]
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def vtk_actor(mesh, color, opacity=1.0):
    mesh = mesh.copy()
    mesh.remove_unreferenced_vertices()
    vertices = numpy_to_vtk(np.asarray(mesh.vertices, dtype=np.float32), deep=True)
    cells = numpy_to_vtkIdTypeArray(np.column_stack((np.full(len(mesh.faces), 3), mesh.faces)).astype(np.int64).ravel(), deep=True)
    points = vtk.vtkPoints(); points.SetData(vertices)
    polys = vtk.vtkCellArray(); polys.SetCells(len(mesh.faces), cells)
    pd = vtk.vtkPolyData(); pd.SetPoints(points); pd.SetPolys(polys)
    mapper = vtk.vtkPolyDataMapper(); mapper.SetInputData(pd)
    actor = vtk.vtkActor(); actor.SetMapper(mapper)
    actor.GetProperty().SetColor(tuple(int(color[j:j+2], 16) / 255 for j in (1, 3, 5)))
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetInterpolationToFlat()
    actor.GetProperty().SetAmbient(.28); actor.GetProperty().SetDiffuse(.70)
    actor.GetProperty().SetSpecular(.13); actor.GetProperty().SetSpecularPower(24)
    return actor


def render(objects, size, camera, target, zoom=1.0):
    ren = vtk.vtkRenderer(); ren.SetBackground(0.955, 0.969, 0.978)
    ren.SetUseDepthPeeling(True)
    for mesh, color, opacity in objects:
        ren.AddActor(vtk_actor(mesh, color, opacity))
    cam = ren.GetActiveCamera(); cam.SetPosition(*camera); cam.SetFocalPoint(*target); cam.SetViewUp(0, 0, 1)
    ren.ResetCameraClippingRange(); cam.Zoom(zoom)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(True); win.SetSize(*size); win.AddRenderer(ren)
    win.SetMultiSamples(8); win.SetAlphaBitPlanes(1); win.Render()
    grab = vtk.vtkWindowToImageFilter(); grab.SetInput(win); grab.SetInputBufferTypeToRGB(); grab.ReadFrontBufferOff(); grab.Update()
    img = grab.GetOutput(); arr = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(size[1], size[0], 3)
    pil = Image.fromarray(np.flipud(arr).copy())
    return pil, ren, win


def projection(ren, point, height):
    ren.SetWorldPoint(*point, 1); ren.WorldToDisplay()
    x, y, _ = ren.GetDisplayPoint()
    return int(x), int(height - y)


scene = trimesh.load(MODEL, force="scene")
nodes = {}
for name in scene.graph.nodes_geometry:
    transform, gname = scene.graph[name]
    m = scene.geometry[gname].copy(); m.apply_transform(transform)
    if name != "body_collar": m.apply_translation((-22, 0, 0))
    nodes[name] = m

# The 05 STL is shifted to the printer bed; restore its design-space origin.
# Its Y/Z minima come from the user-adjusted fist, rather than the old preview.
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
raw = trimesh.load(FIST_SOURCE, force="mesh", process=True)
a = raw.face_adjacency
g = sp.coo_matrix((np.ones(len(a)*2, dtype=np.uint8), (np.r_[a[:,0],a[:,1]], np.r_[a[:,1],a[:,0]])), shape=(len(raw.faces),)*2).tocsr()
_, lab = connected_components(g, directed=False)
fist_piece = raw.submesh([np.flatnonzero(lab == np.argmax(np.bincount(lab)))], append=True, repair=False)

part_meshes = [trimesh.load(p, force="mesh") for p in PRINTS]
parts_in_place = []
for i, mesh in enumerate(part_meshes):
    m = mesh.copy()
    if i == 1:
        m.apply_translation(nodes["crank"].bounds[0] - m.bounds[0])
    elif i == 2:
        m.apply_translation(nodes["link"].bounds[0] - m.bounds[0])
    elif i == 3:
        m.apply_translation(nodes["carriage"].bounds[0] - m.bounds[0])
    elif i == 4:
        m.apply_translation((16.0, fist_piece.bounds[0,1], fist_piece.bounds[0,2]))
    parts_in_place.append(m)

# Otto V9 body is reference-only; it is already printed and not in this pack.
otto = trimesh.load(PROJECT / "01_研究参考" / "robot-battle-reference" / "Otto-V9" / "3Dprint" / "OttoDIY_body_V9.stl", force="mesh")
otto.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 0, 1)))
objects = [(otto, "#CBD2DA", .42)]
objects += [(nodes[n], "#B4B6B8", 1) for n in nodes if n.startswith("ref_")]
objects += [(nodes[n], "#AEB6BB", 1) for n in nodes if n.startswith("guide_rod")]
objects += [(m, c, 1) for m, c in zip(parts_in_place, COLORS)]
im, ren, win = render(objects, (1900, 1250), (165, -190, 155), (13, 0, 13), 1.18)
d = ImageDraw.Draw(im)
d.text((65, 35), "拳头攻击模块 · 装配位置", font=font(53), fill="#17232E")
d.text((68, 102), "颜色对应你已打印的 01–05；浅灰色为旧 Otto 身体与未打印的电机、导杆", font=font(25), fill="#495A66")
callouts = [
    ((-48, -26, 1), (180, 820), NAMES[0], COLORS[0]),
    ((-19, -1, 30), (180, 340), NAMES[1], COLORS[1]),
    ((-2, -1, 38), (165, 470), NAMES[2], COLORS[2]),
    ((9, -17, 48), (1200, 260), NAMES[3], COLORS[3]),
    ((83, -4, 54), (1260, 760), NAMES[4], COLORS[4]),
    ((-40, -3, 15), (170, 640), "电机＋减速器", "#71777C"),
    ((29, -20, 46), (1210, 420), "Ø3×64 导杆 ×2", "#838F96"),
]
for anchor, xy, label, color in callouts:
    px, py = projection(ren, anchor, im.height)
    d.line((px, py, xy[0] + 11, xy[1] + 16), fill=color, width=4)
    d.ellipse((px-7,py-7,px+7,py+7), fill=color)
    box = d.textbbox(xy, label, font=font(28))
    d.rounded_rectangle((xy[0]-10,xy[1]-6,box[2]+12,box[3]+7), radius=9, fill="#FFFFFF", outline=color, width=3)
    d.text(xy, label, font=font(28), fill="#192630")
d.text((80, 1185), "拳头向右前方伸出  ·  装配前保持断电  ·  浅灰参考件不在五件打印清单内", font=font(25), fill="#405361")
im.save(ROOT / "成品装配图_零件标注.png")
win.Finalize()

# Identity board: each object is rendered directly from its printable STL.
board = Image.new("RGB", (2600, 1420), "#F4F7F9")
bd = ImageDraw.Draw(board)
bd.text((75, 38), "这五件就是你打印的零件", font=font(57), fill="#17232E")
bd.text((76, 118), "按编号辨认：01 支撑全部机构，02→03→04 传动，05 套在 04 的方形舌头上", font=font(28), fill="#485B68")
positions = [(65, 200), (925, 200), (1785, 200), (500, 800), (1360, 800)]
for i, (m, c, pos) in enumerate(zip(part_meshes, COLORS, positions)):
    w,h = (760, 450)
    center = m.bounds.mean(axis=0)
    extent = max(m.extents)
    img, _, rw = render([(m,c,1)], (w,h), center + np.array([1.3,-1.5,1.0])*extent*1.8, center, 1.1)
    x,y = pos
    board.paste(img, (x,y))
    bd.rounded_rectangle((x,y,x+w,y+h), radius=18, outline=c, width=5)
    bd.text((x+15,y+h+14), NAMES[i], font=font(37), fill="#17232E")
    rw.Finalize()
bd.text((76, 1340), "另需：完整减速器 ×1、金属导杆 ×2、螺钉/垫片/螺母与扎带。", font=font(29), fill="#465A67")
board.save(ROOT / "五个打印件_单件对照图.png")
print(ROOT / "成品装配图_零件标注.png")
print(ROOT / "五个打印件_单件对照图.png")
