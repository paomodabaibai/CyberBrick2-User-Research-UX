"""Open, offset mount for the fist mechanism. Units: mm.

This is a fit-check prototype. The collar stays centred on Otto while the
mechanism moves 22 mm rearwards. Do not use the combined preview STL as a
printable assembly.
"""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "队友拳头模块_2026-09-28_增量审阅" / "04_结构与硬件" / "Otto_CB1出拳头部_v01"
OUT = ROOT / "开放式底座_v01_试装"
OUT.mkdir(exist_ok=True)

spec = importlib.util.spec_from_file_location("punch_source", SOURCE / "build_punch_head.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cq = module.cq

params = json.loads((SOURCE / "parameters.json").read_text(encoding="utf-8"))
head = module.Head(params)
offset = -22.0
outer = params["frame_outer_mm"]
ear_x = outer / 2 + 2.5

# An accessible window on the front part of the shifted platform. The motor
# cradle is retained; its mounting slots, guide posts and beams remain intact.
base = head.parts["01_mount_and_guides"]
front_window = module.box(19, 28, 3.2, 25.5, 0, -0.1)
base = base.cut(front_window).translate((offset, 0, 0))

# Keep the collar located on the already-printed Otto body. Its two X-facing
# central fastening zones remain intact. Open the Y walls for cables/access.
collar = head.parts["09_body_collar"]
for side in (-1, 1):
    collar = collar.cut(module.box(28, 12, 10, 0, side * (outer / 2), -9))

# Two side rails bridge the old and new ear positions above the Otto shell.
# This version is one structural print: a rail underneath Z0 would collide
# with the shell, while a separate rail at deck height would overlap the deck.
adapter = collar.union(base)
rail_x_min = offset - ear_x
rail_x_max = ear_x
rail_length = rail_x_max - rail_x_min + 9
rail_cx = (rail_x_min + rail_x_max) / 2
for y in (-24, 24):
    adapter = adapter.union(module.box(rail_length, 9, 3, rail_cx, y, 0))
    for x in (-ear_x, ear_x, offset - ear_x, offset + ear_x):
        adapter = adapter.cut(module.cyl(1.65, 13, x, y, -9))

for name, part in (("开放一体底座_后移22mm_试装", adapter),):
    cq.exporters.export(part, str(OUT / (name + ".step")))
    cq.exporters.export(part, str(OUT / (name + ".stl")))

(OUT / "试装说明.md").write_text(
    "# 开放式底座 v01（试装件）\n\n"
    "攻击机构相对 Otto 后移 22 mm；套环仍以 Otto 身体为中心。"
    "两侧连接梁把套环和后移后的底板合成一个结构件，不再将错位孔硬拧在一起。\n\n"
    "底板前方开 19×28 mm 操作窗口；套环前后侧开放 28 mm 宽的走线/接口窗口。"
    "主控板可从未被后移模块覆盖的身体前部及这些窗口接近。"
    "原电机托架、导杆座和机械连接保留。\n\n"
    "先在切片软件检查一体底座的桥接/支撑，再试套身体。"
    "需要实物确认 USB、开关、线束方位及螺钉长度；此文件不等于装机验证。"
    "不要直接打印整机比例预览 STL。\n",
    encoding="utf-8",
)
print(OUT)
