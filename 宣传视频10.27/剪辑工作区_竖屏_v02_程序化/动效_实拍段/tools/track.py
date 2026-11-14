# 从无字幕成片里追踪掌掌的蓝手套、拳拳的红拳头（颜色阈值），给拖尾和准星用。py -3.12 运行。
import json, pathlib, subprocess, sys
import numpy as np
FX = pathlib.Path(__file__).resolve().parents[1]
src = str(FX.parent / 'out' / '棋甲对决_竖屏抖音_v09e_全片_无字幕.mp4')
W, H = 270, 480
def frames(a, b):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{a / 30:.4f}', '-i', src, '-frames:v', str(b - a), '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(p, 'u1').reshape(-1, H, W, 3).astype(int)
def smooth(rows, r=2):
    out = []
    for i, row in enumerate(rows):
        pts = [x for x in rows[max(0, i - r):i + r + 1] if x[1] is not None]
        out.append([row[0], round(float(np.mean([p[1] for p in pts])), 1), round(float(np.mean([p[2] for p in pts])), 1), row[3]] if pts and row[1] is not None else row)
    return out
palm = []
for i, f in enumerate(frames(445, 526)):
    R, G, B = f[..., 0], f[..., 1], f[..., 2]
    m = (B > 200) & (G > 130) & (R < 120) & (B - R > 90)   # 手套比底座亮
    m[295:] = False                                         # 底座和地圈在画面下方
    n = int(m.sum())
    if n < 40: palm.append([445 + i, None, None, 0]); continue
    y, x = np.nonzero(m)
    cx, cy = np.median(x), np.median(y)
    for _ in range(4):                                       # 收到最大一团，避开零散亮蓝点
        k = (x - cx) ** 2 + (y - cy) ** 2 < 45 ** 2
        if k.sum() < 10: break
        cx, cy = x[k].mean(), y[k].mean()
    palm.append([445 + i, round(float(cx) * 4), round(float(cy) * 4), n])
fist = []
for i, f in enumerate(frames(546, 627)):
    R, G, B = f[..., 0], f[..., 1], f[..., 2]
    m = (R > 150) & (G < 75) & (B < 85)
    y, x = np.nonzero(m)
    if len(y) < 60: fist.append([546 + i, None, None, 0]); continue
    # 拳头在机器人最靠上的一端：取最靠上 18% 的红色像素
    cut = np.quantile(y, 0.18); k = y <= cut
    fist.append([546 + i, round(float(x[k].mean()) * 4), round(float(y[k].mean()) * 4), len(y)])
json.dump({'palm': smooth(palm), 'fist': smooth(fist)}, open(FX / 'assets' / 'track.json', 'w'))
for name, rows in (('palm', smooth(palm)), ('fist', smooth(fist))):
    print(name); prev = None
    for r in rows[::3]:
        sp = None if prev is None or r[1] is None or prev[1] is None else round(((r[1] - prev[1]) ** 2 + (r[2] - prev[2]) ** 2) ** 0.5)
        print(f'  {r[0] / 30:.2f} {r[1]} {r[2]} n={r[3]} v={sp}'); prev = r
