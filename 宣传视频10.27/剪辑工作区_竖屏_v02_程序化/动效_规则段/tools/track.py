# 追踪实拍：① 每帧相对参考帧的单应（ORB + RANSAC，平滑）→ 场地 4 角；② 红/蓝球；③ 红/蓝机器人脚底点与包围框。输出 assets/track.json
# 场地坐标：X 0–120（左→右）、Y 0–80（远→近），单位 cm，和 ../arena3d.js 一致。
import json, pathlib, sys
sys.path.insert(0, r'C:\Users\Administrator\AppData\Local\Temp\claude\C--Users-Administrator\226f244b-41b6-4b0a-8934-41361d3c2ec5\scratchpad\pylibs')
import cv2
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
FR = ROOT / 'assets' / 'frames'
files = sorted(FR.glob('*.jpg'))
rd = lambda p: cv2.imdecode(np.frombuffer(p.read_bytes(), np.uint8), cv2.IMREAD_COLOR)

# 参考帧（k=0，V22 第 1270 帧）上量的场地内角：左上、右上、右下、左下
CORNERS = np.float32([[408, 432], [1503, 428], [1745, 826], [148, 830]])
FIELD = np.float32([[0, 0], [120, 0], [120, 80], [0, 80]])
F2R = cv2.getPerspectiveTransform(FIELD, CORNERS)      # 场地 → 参考帧
BALL_R = {'red': (743, 652), 'blue': (1098, 361)}       # 参考帧上的球心

orb = cv2.ORB_create(6000, fastThreshold=10)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
ref = rd(files[0])
# 机器人和人手会动，特征只取场地边框、围墙、台面（遮掉两台机器人起点附近和上方人手区）
def mask_of(shape):
    m = np.full(shape[:2], 255, np.uint8)
    m[:260, :] = 0
    return m
kpR, deR = orb.detectAndCompute(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), mask_of(ref.shape))

def estimate(gray):
    kp, de = orb.detectAndCompute(gray, mask_of(gray.shape))
    ms = bf.match(deR, de)
    ms = sorted(ms, key=lambda m: m.distance)[:900]
    a = np.float32([kpR[m.queryIdx].pt for m in ms]); b = np.float32([kp[m.trainIdx].pt for m in ms])
    H, inl = cv2.findHomography(a, b, cv2.RANSAC, 2.5, maxIters=5000, confidence=0.999)
    return H, int(inl.sum())

Hs, inls = [], []
for i, f in enumerate(files):
    H, n = estimate(cv2.cvtColor(rd(f), cv2.COLOR_BGR2GRAY))
    Hs.append(H / H[2, 2]); inls.append(n)
print('内点 最少/中位', min(inls), int(np.median(inls)), '最差帧', int(np.argmin(inls)))

# 用场地 4 角的轨迹做平滑（中值去跳变 + 高斯），再反解单应
def proj(H, pts):
    p = np.c_[pts, np.ones(len(pts))] @ H.T
    return p[:, :2] / p[:, 2:]
tr = np.stack([proj(H, CORNERS) for H in Hs])          # (n,4,2)
def smooth(a, med=5, sig=2.0):
    n = len(a); out = a.copy()
    for i in range(n):
        out[i] = np.median(a[max(0, i - med // 2):i + med // 2 + 1], axis=0)
    r = int(sig * 3); w = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sig * sig)); w /= w.sum()
    pad = np.concatenate([out[:1].repeat(r, 0), out, out[-1:].repeat(r, 0)])
    return np.apply_along_axis(lambda x: np.convolve(x, w, 'valid'), 0, pad)
print('角点抖动（平滑前，相邻帧残差 px 中位）', float(np.median(np.abs(np.diff(tr, 2, axis=0)))))
tr_s = smooth(tr.reshape(len(tr), -1)).reshape(tr.shape)
FH = [cv2.getPerspectiveTransform(FIELD, c.astype(np.float32)) for c in tr_s]   # 场地 → 当前帧
RH = [cv2.getPerspectiveTransform(CORNERS, c.astype(np.float32)) for c in tr_s] # 参考帧 → 当前帧

def blobs(mask):
    n, lab, st, ce = cv2.connectedComponentsWithStats(mask, 8)
    return [(st[i], ce[i], i) for i in range(1, n)], lab

out = {'n': len(files), 'frames': []}
last = {'red': None, 'blue': None}
for i, f in enumerate(files):
    im = rd(f)
    hsv = cv2.cvtColor(cv2.GaussianBlur(im, (5, 5), 0), cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    M = {'red': (((h < 8) | (h > 172)) & (s > 150) & (v > 90)).astype(np.uint8) * 255,
         'blue': (((h > 104) & (h < 124)) & (s > 165) & (v > 70)).astype(np.uint8) * 255}
    fr = {'corners': tr_s[i].round(2).tolist(), 'H': FH[i].flatten().round(6).tolist()}
    # 只看场地内外扩的区域，排除人手（手柄是黄的，但衣物可能带色）
    poly = np.zeros(im.shape[:2], np.uint8)
    q = tr_s[i].copy(); q[:2, 1] -= 150
    cv2.fillConvexPoly(poly, q.astype(np.int32), 255)
    for c in ('red', 'blue'):
        m = cv2.bitwise_and(M[c], poly)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        # 球：预测位置附近找圆块
        px = proj(RH[i], np.float32([BALL_R[c]]))[0]
        bl, lab = blobs(m)
        ball, bd = None, 1e9
        for st, ce, idx in bl:
            d = np.hypot(*(ce - px))
            ar = st[2] / max(1, st[3])
            if st[4] > 900 and d < 90 and d < bd and 0.65 < ar < 1.45: ball, bd = (st, ce, idx), d
        if ball is not None:
            fr[f'ball_{c}'] = [round(float(ball[1][0]), 1), round(float(ball[1][1]), 1), round(float(max(ball[0][2], ball[0][3]) / 2), 1)]
            m[lab == ball[2]] = 0
        else:
            fr[f'ball_{c}'] = [round(float(px[0]), 1), round(float(px[1]), 1), 40.0]
        # 机器人：把同色块按距离聚类，取最大的那团
        m2 = cv2.dilate(m, np.ones((45, 45), np.uint8))
        bl2, lab2 = blobs(m2)
        cand = [(int((m[lab2 == idx] > 0).sum()), idx) for st, ce, idx in bl2 if st[4] > 2500]
        if cand:
            area, idx = max(cand)
            ys, xs = np.nonzero((lab2 == idx) & (m > 0))
            y1 = np.percentile(ys, 99); low = ys > y1 - (y1 - ys.min()) * 0.16
            foot = [float(xs[low].mean()), float(np.percentile(ys, 98))]
            fr[c] = {'foot': [round(foot[0], 1), round(foot[1], 1)], 'box': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], 'area': area}
            last[c] = fr[c]
        else:
            fr[c] = dict(last[c], lost=True) if last[c] else None
    out['frames'].append(fr)

# 脚底点平滑后换算到场地坐标（光轨用）
for c in ('red', 'blue'):
    a = np.array([fr[c]['foot'] for fr in out['frames']], np.float32)
    a_s = smooth(a, med=7, sig=1.6)
    for i, fr in enumerate(out['frames']):
        fr[c]['foot_s'] = a_s[i].round(1).tolist()
        p = cv2.perspectiveTransform(a_s[i].reshape(1, 1, 2).astype(np.float32), np.linalg.inv(FH[i]))[0, 0]
        fr[c]['field'] = [round(float(p[0]), 2), round(float(p[1]), 2)]
    print(c, '丢失帧', sum(1 for fr in out['frames'] if fr[c].get('lost')), '起点场地坐标', out['frames'][0][c]['field'], '终点', out['frames'][-1][c]['field'])
(ROOT / 'assets' / 'track.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')

# 检查图
idx = np.linspace(0, len(files) - 1, 12).astype(int)
sheet = []
for i in idx:
    im = rd(files[i]); fr = out['frames'][i]
    cv2.polylines(im, [np.int32(fr['corners'])], True, (0, 255, 255), 3)
    for x in range(10, 120, 10):
        a = cv2.perspectiveTransform(np.float32([[[x, 0], [x, 80]]]), FH[i])[0]; cv2.line(im, tuple(np.int32(a[0])), tuple(np.int32(a[1])), (255, 255, 255), 1)
    for y in range(10, 80, 10):
        a = cv2.perspectiveTransform(np.float32([[[0, y], [120, y]]]), FH[i])[0]; cv2.line(im, tuple(np.int32(a[0])), tuple(np.int32(a[1])), (255, 255, 255), 1)
    for c, col in (('red', (0, 0, 255)), ('blue', (255, 80, 0))):
        x, y = fr[c]['foot_s']; cv2.drawMarker(im, (int(x), int(y)), (0, 255, 0), cv2.MARKER_CROSS, 50, 5)
        b = fr[c]['box']; cv2.rectangle(im, (b[0], b[1]), (b[2], b[3]), col, 3)
        bx = fr[f'ball_{c}']; cv2.circle(im, (int(bx[0]), int(bx[1])), int(bx[2]), (0, 255, 0), 3)
    sheet.append(cv2.resize(im, (640, 360)))
grid = np.vstack([np.hstack(sheet[r * 3:r * 3 + 3]) for r in range(4)])
ok, buf = cv2.imencode('.jpg', grid, [cv2.IMWRITE_JPEG_QUALITY, 88])
pathlib.Path(sys.argv[1]).write_bytes(buf.tobytes())
print('完成')
