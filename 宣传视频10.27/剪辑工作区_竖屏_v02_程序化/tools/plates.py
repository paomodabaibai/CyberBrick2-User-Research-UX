# 按 film.js 抽出每个镜头要用的源帧（已按手机旋转信息摆正）→ out/plates/<镜头>/00000.jpg …，并写 manifest.json
# 改了镜头入出点后重跑即可；已存在且范围相同的镜头跳过。
import json, subprocess, pathlib, sys
from fractions import Fraction
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT.parent / '已命名素材'
OUT = ROOT / 'out' / 'plates'

def find(id_):
    m = [p for p in SRC.iterdir() if p.stem.split('__')[-1] == id_]
    assert len(m) == 1, (id_, m)
    return m[0]

shots = json.loads(subprocess.run(['node', '-e', "import('./film.js').then(m=>console.log(JSON.stringify(m.shots)))"],
                                  cwd=ROOT, capture_output=True, text=True, check=True).stdout)
OUT.mkdir(parents=True, exist_ok=True)
mf_path = OUT / 'manifest.json'
old = json.loads(mf_path.read_text()) if mf_path.exists() else {}
manifest = {}
for s in shots:
    f, d = find(s['src']), OUT / s['id']
    if f.suffix.lower() in ('.jpg', '.png'):
        manifest[s['id']] = {'kind': 'photo', 'src': s['src']}
        if not (d / '00000.jpg').exists():
            d.mkdir(exist_ok=True)
            im = ImageOps.exif_transpose(Image.open(f)).convert('RGB'); im.thumbnail((2400, 2400), Image.LANCZOS)
            im.save(d / '00000.jpg', quality=92)
        continue
    a0 = max(0, min(g['a'] for g in s['segs']) - 0.1)
    b = max(g['b'] for g in s['segs']) + 0.15
    fps = float(Fraction(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
                                         '-of', 'csv=p=0', str(f)], capture_output=True, text=True).stdout.strip().split(',')[0]))
    info = {'kind': 'video', 'src': s['src'], 'a0': round(a0, 4), 'b': round(b, 4), 'fps': fps}
    prev = old.get(s['id'])
    if prev and all(prev.get(k) == v for k, v in info.items()) and d.exists():
        manifest[s['id']] = prev; print('跳过', s['id']); continue
    d.mkdir(exist_ok=True)
    for p in d.glob('*.jpg'): p.unlink()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a0:.3f}', '-i', str(f), '-t', f'{b - a0:.3f}',
                    '-q:v', '2', '-start_number', '0', str(d / '%05d.jpg')], check=True)
    info['n'] = len(list(d.glob('*.jpg')))
    manifest[s['id']] = info
    print(s['id'], s['src'], info['n'], '帧')
mf_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
