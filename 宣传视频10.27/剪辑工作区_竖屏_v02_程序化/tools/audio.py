# 声音：按 film.js 的变速段拼原声（慢动作段降调，定格/照片段静音）+ 程序合成音效 → out/声音.wav
# 用法：python audio.py [输出路径]
import json, subprocess, pathlib, sys
sys.path.insert(0, r'E:/AI视频/通用制作方法/工具/onetake/pydeps')
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT.parent / '已命名素材'
SR = 48000
rng = np.random.default_rng(7)

def find(id_):
    return [p for p in SRC.iterdir() if p.stem.split('__')[-1] == id_][0]

def grab(f, a, b, v):
    af = f'asetrate={int(SR * v)},aresample={SR}' if v != 1 else 'anull'
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', str(f), '-af', af,
                          '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

def fade(x, ms=8):
    n = min(len(x) // 2, int(SR * ms / 1000))
    if n: r = np.linspace(0, 1, n)[:, None]; x[:n] *= r; x[-n:] *= r[::-1]
    return x

def lp(x, fc):   # 一阶低通
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s = (1 - a) * v + a * s; y[i] = s
    return y

def env(n, att, dec):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(att, 1e-4)) * np.exp(-t / dec)

def sfx(kind):
    if kind == 'slap':   # 清脆拍击 + 一点肉感低频
        n = int(0.35 * SR); t = np.arange(n) / SR
        crack = rng.standard_normal(n) * env(n, 0.001, 0.025); crack -= lp(crack, 900)
        body = np.sin(2 * np.pi * 180 * t * (1 - 0.4 * t)) * env(n, 0.002, 0.06)
        return 0.75 * crack + 0.5 * body
    if kind == 'boom':   # 下沉重击
        n = int(0.9 * SR); t = np.arange(n) / SR
        f = 40 + 90 * np.exp(-t / 0.08); ph = 2 * np.pi * np.cumsum(f) / SR
        hit = rng.standard_normal(n) * env(n, 0.001, 0.03)
        return 0.9 * np.sin(ph) * env(n, 0.003, 0.28) + 0.35 * lp(hit, 2500)
    if kind == 'whoosh':   # 转场风声：带通噪声扫频
        n = int(0.42 * SR); t = np.arange(n) / SR
        w = rng.standard_normal(n); out = np.zeros(n); seg = 512
        for i in range(0, n, seg):
            fc = 400 + 3200 * np.sin(np.pi * min(1, i / n)) ** 2
            blk = w[i:i + seg]; out[i:i + seg] = lp(blk, fc) - lp(blk, fc * 0.35)
        return 0.9 * out * np.sin(np.pi * t / t[-1]) ** 2
    if kind == 'ding':
        n = int(0.8 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 1318.5 * t) + 0.35 * np.sin(2 * np.pi * 2637 * t)) * env(n, 0.002, 0.22) * 0.35
    if kind == 'tick':
        n = int(0.06 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * 1900 * t) * env(n, 0.0005, 0.012) * 0.45 + rng.standard_normal(n) * env(n, 0.0003, 0.004) * 0.2
    raise KeyError(kind)

film = json.loads(subprocess.run(['node', '-e', "import('./film.js').then(m=>console.log(JSON.stringify({shots:m.shots,duration:m.duration})))"],
                                 cwd=ROOT, capture_output=True, text=True, check=True).stdout)
N = int(film['duration'] * SR) + SR
bed = np.zeros((N, 2), np.float32); fx = np.zeros((N, 2), np.float32)
for s in film['shots']:
    f = find(s['src']); pos = s['start']
    for g in s['segs']:
        if g['v'] and s.get('gain', 1) > 0 and f.suffix.lower() == '.mp4':
            x = fade(grab(f, g['a'], g['b'], g['v'])) * s.get('gain', 1)
            i = int(pos * SR); x = x[:min(len(x), int(g['d'] * SR) + 1, N - i)]
            bed[i:i + len(x)] += x
        pos += g['d']
    for e in s.get('sfx', []):
        y = sfx(e['k']).astype(np.float32)
        lead = 0.22 if e['k'] == 'whoosh' else 0   # 风声提前，越过剪辑点
        i = max(0, int((s['start'] + e['t'] - lead) * SR)); y = y[:N - i]
        fx[i:i + len(y)] += y[:, None] * 0.5
# 原声做平：限制尖峰后整体归一
pk = np.percentile(np.abs(bed), 99.7) + 1e-6
bed = np.tanh(bed / pk * 0.8) * 0.5
mix = bed + fx
mix = mix / max(1, np.abs(mix).max() / 0.95)
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'out' / '声音_raw.wav')
import wave
with wave.open(str(out), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
print('写出', out)
