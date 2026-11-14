# 把达芬奇复合片段「完整一场」按时间线节奏还原成逐帧图：V22 第 1270 帧起 3380 帧 + V02 第 1214 帧起 2703 帧，压进 582 帧（约 10.45 倍速）
# 用法：py -3.12 extract_frames.py 0 216  → assets/frames/00000.jpg …（k = 时间线帧号，0 = 时间线 20.90 秒）
#       py -3.12 extract_frames.py slow 3120 3240 → assets/slow/03120.jpg …（V22 原速片段，帧号 = V22 源帧）
import pathlib, sys
sys.path.insert(0, r'C:\Users\Administrator\AppData\Local\Temp\claude\C--Users-Administrator\226f244b-41b6-4b0a-8934-41361d3c2ec5\scratchpad\pylibs')
import cv2

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = pathlib.Path(r'E:\课程作业\大三上\张茫 用户研究与体验设计\宣传视频10.27\已命名素材_达芬奇转码')
V22 = next(SRC.glob('*V22.mov')); V02 = next(SRC.glob('*V02.mov'))
RATIO = 6081 / 582


def src_of(k):
    cf = k * RATIO
    return (V22, 1270 + round(cf)) if cf < 3380 else (V02, 1214 + round(cf - 3380))


def dump(path, wanted, outdir, name):
    outdir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(path))
    first = min(wanted)
    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    i = first; last = max(wanted); n = 0
    while i <= last:
        if not cap.grab(): raise RuntimeError(f'读帧失败 {i}')
        if i in wanted:
            ok, im = cap.retrieve()
            for key in wanted[i]:
                # cv2.imwrite 写不了中文路径（静默失败），先编码再写
                ok, buf = cv2.imencode('.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 93]); assert ok
                (outdir / f'{key:05d}.jpg').write_bytes(buf.tobytes()); n += 1
        i += 1
    cap.release()
    print(path.name[-12:], '写出', n)


if sys.argv[1] == 'slow':
    a, b = int(sys.argv[2]), int(sys.argv[3])
    dump(V22, {i: [i] for i in range(a, b)}, ROOT / 'assets' / 'slow', 'slow')
else:
    a, b = int(sys.argv[1]), int(sys.argv[2])
    by = {}
    for k in range(a, b):
        p, f = src_of(k)
        by.setdefault(p, {}).setdefault(f, []).append(k)
    for p, w in by.items():
        dump(p, w, ROOT / 'assets' / 'frames', 'frames')
