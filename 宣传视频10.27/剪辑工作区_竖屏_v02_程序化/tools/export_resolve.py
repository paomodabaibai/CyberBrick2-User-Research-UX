# 导出给达芬奇的剪辑骨架：每个镜头 = 一段 100% 速度的素材（去掉变速/定格/特效），照片转成竖屏定长视频
import json, subprocess, pathlib
from fractions import Fraction
from PIL import Image, ImageOps
ROOT = pathlib.Path(__file__).resolve().parents[1]; SRC = ROOT.parent / '已命名素材'; OUT = ROOT / '达芬奇交接'
film = json.loads(subprocess.run(['node', '-e', "import('./film.js').then(m=>console.log(JSON.stringify({shots:m.shots,overlays:m.overlays})))"], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True).stdout)
find = lambda i: [p for p in SRC.iterdir() if p.stem.split('__')[-1] == i][0]
def fx_note(s):
    n = []
    for g in s['segs']:
        if g['v'] == 0 and s['src'][0] == 'V': n.append(f"定格 {g['d']:.2f}s @源{g['a']:.2f}")
        elif g['v'] and g['v'] != 1: n.append(f"慢动作 {g['v']}x 源{g['a']:.2f}-{g['b']:.2f}")
    if s.get('fx', {}).get('shake'): n.append('震屏')
    if s.get('fx', {}).get('flash'): n.append('白闪')
    if len(s['cam']) > 1: n.append('推拉')
    if s.get('render') == 'arena3d': n.append('3D 规则动画占位（实拍 V02 全景）')
    if s.get('fit'): n.append(f"构图:{s['fit']}")
    return '；'.join(n) or '无'
clips = []
for s in film['shots']:
    f = find(s['src'])
    if f.suffix.lower() in ('.jpg', '.png'):
        dur = s['dur']; mp4 = OUT / '照片转视频' / f"{s['src']}_竖屏.mp4"
        if not mp4.exists():
            im = ImageOps.exif_transpose(Image.open(f)).convert('RGB'); tmp = OUT / '照片转视频' / f"{s['src']}.png"
            sc = max(1080 / im.width, 1920 / im.height); im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
            l, t = (im.width - 1080) // 2, (im.height - 1920) // 2; im.crop((l, t, l + 1080, t + 1920)).save(tmp)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-i', str(tmp), '-t', '8', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', str(mp4)], check=True); tmp.unlink()
        clips.append({'id': s['id'], 'path': str(mp4), 'fps': 30.0, 'a': 0.0, 'b': round(dur, 3), 'note': fx_note(s), 'photo': True, 'v04_start': s['start'], 'v04_dur': s['dur']})
        continue
    fps = float(Fraction(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', str(f)], capture_output=True, text=True).stdout.strip().split(',')[0]))
    a = min(g['a'] for g in s['segs']); b = max(g['b'] for g in s['segs'])
    if s.get('render') == 'arena3d': b = a + s['dur']   # 3D 段：用 V02 实拍按原长占位
    clips.append({'id': s['id'], 'path': str(f), 'fps': fps, 'a': a, 'b': b, 'note': fx_note(s), 'v04_start': s['start'], 'v04_dur': s['dur'],
                  'cover': s['src'] in ('V04', 'V30'), 'cx': s['cam'][0]['c'][0]})
subs = [{'at': o['at'], 'out': o['out'], 'text': o['text']} for o in film['overlays'] if o['k'] in ('sub', 'step')]
(OUT / 'v04_剪辑骨架.json').write_text(json.dumps({'clips': clips, 'subs': subs}, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(clips), 'clips'); print(sum(c['b'] - c['a'] for c in clips))
