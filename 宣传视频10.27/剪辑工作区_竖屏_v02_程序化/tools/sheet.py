# 看片用联系表：python sheet.py V05 44 5 0.2  → 00_看片/V05_44.jpg（每格标源时间）
import sys, subprocess, pathlib, io
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT.parent / '已命名素材'

def find(id_):
    m = [p for p in SRC.iterdir() if p.stem.split('__')[-1] == id_]
    assert len(m) == 1, (id_, m)
    return m[0]

def sheet(id_, a, d, step, w=200, cols=8):
    f = find(id_)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a), '-t', str(d), '-i', str(f),
                          '-vf', f'fps=1/{step},scale={w}:-2', '-f', 'image2pipe', '-c:v', 'png', '-'],
                         capture_output=True).stdout
    ims, i = [], 0
    while True:   # 按 PNG 签名切分
        j = raw.find(b'\x89PNG', i + 1)
        ims.append(Image.open(io.BytesIO(raw[i:j if j > 0 else None])).convert('RGB'))
        if j < 0: break
        i = j
    W, H = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    out = Image.new('RGB', (cols * W, rows * H))
    dr = ImageDraw.Draw(out)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    for k, im in enumerate(ims):
        x, y = k % cols * W, k // cols * H
        out.paste(im, (x, y))
        dr.rectangle([x, y, x + 62, y + 22], fill=(0, 0, 0))
        dr.text((x + 3, y + 2), f'{a + k * step:.2f}', fill=(255, 230, 0), font=font)
    p = ROOT / '00_看片' / f'{id_}_{a:g}.jpg'
    p.parent.mkdir(exist_ok=True)
    out.save(p, quality=85)
    print(p)

if __name__ == '__main__':
    sheet(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), *(int(x) for x in sys.argv[5:]))
