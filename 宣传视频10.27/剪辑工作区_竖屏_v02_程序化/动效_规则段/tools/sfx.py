# 规则段音效：只给真正的落点发声，用片中物件的“材质”合成（硬壳撞击、玻璃透镜、巴掌）。输出 out/音效_样片.wav（48k，与叠层同长）
# 用法：py -3.12 sfx.py 7.0 out/音效_样片.wav
import sys, wave
import numpy as np

SR = 48000
rs = np.random.RandomState(7)
dur, path = float(sys.argv[1]), sys.argv[2]
mix = np.zeros(int(dur * SR) + SR)

def put(sig, at, gain):
    i = int(at * SR); mix[i:i + len(sig)] += sig[:len(mix) - i] * gain

def env(n, a=0.002, tau=0.1):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / tau)

def lp(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')

def thump(f0=70, tau=0.16):      # 硬壳落地：下滑低音 + 一点壳体噪声
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.5 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, tau) + lp(rs.randn(n), 8) * env(n, 0.0005, 0.018) * 0.7

def glass(f=1680):               # 玻璃珠：非整数倍泛音，成对微失谐
    n = int(0.9 * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for r, g, tau in ((1, 1, 0.22), (1.006, 0.6, 0.22), (2.76, 0.42, 0.11), (5.4, 0.18, 0.05)):
        out += g * np.sin(2 * np.pi * f * r * t) * np.exp(-t / tau)
    return out * np.minimum(t / 0.0015, 1) * 0.5

def slap():                      # 巴掌：宽带脆响 + 掌心闷响
    n = int(0.45 * SR); t = np.arange(n) / SR
    crack = (rs.randn(n) - np.roll(rs.randn(n), 1)) * env(n, 0.0004, 0.012)
    body = lp(rs.randn(n), 22) * env(n, 0.0008, 0.05) * 2.4
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.8
    return crack * 0.9 + body + tone

def win():                       # WIN：三个玻璃音叠起（A–E–升C 动机）
    out = np.zeros(int(1.2 * SR))
    for f, at in ((880, 0), (1318.5, 0.05), (2217.5, 0.1)):
        g = glass(f); i = int(at * SR); out[i:i + len(g)] += g
    return out

put(thump(62, 0.2), 0.08, 0.5)    # 规则 / 对战条砸入
put(thump(82, 0.12), 1.34, 0.32)  # 同时
put(thump(70, 0.14), 1.62, 0.42)  # 出发
put(glass(1680), 2.72, 0.2)       # 红透镜
put(glass(2240), 2.84, 0.17)      # 蓝透镜
put(win(), B_ying := 3.88, 0.26)
put(thump(58, 0.1), 3.88, 0.32)
put(thump(74, 0.1), 4.08, 0.3)    # 蓝球
_n = int(0.22 * SR); _rw = lp(rs.randn(_n), 6) * np.linspace(0, 1, _n) ** 2 * np.linspace(1, 0.2, _n)  # 倒带
put(_rw, 4.28, 0.22)
put(slap(), 6.08, 0.62)           # 巴掌扇中
put(thump(46, 0.42), 6.08, 0.72)
put(thump(90, 0.08), 6.28, 0.22)
put(thump(64, 0.18), 6.42, 0.4)   # 架

# 第三幕
put(thump(62, 0.16), 6.97, 0.4)    # 手柄砸入
put(thump(80, 0.08), 7.25, 0.18); put(thump(70, 0.1), 7.98, 0.25)
put(glass(1760), 8.93, 0.24); put(thump(60, 0.12), 8.93, 0.26)  # 上手
put(thump(52, 0.22), 10.24, 0.5)   # DIY
put(glass(1320), 11.0, 0.13); put(glass(1980), 11.58, 0.13)
put(thump(44, 0.3), 12.44, 0.55); put(slap(), 12.44, 0.18)   # 拆开
for _i, _t in enumerate((13.66, 13.98, 14.26, 14.5, 14.7, 14.87, 15.0)): put(glass(1500 + _i * 170), _t, 0.09)
put(thump(58, 0.14), 15.14, 0.34)
_step = np.sin(2 * np.pi * 1900 * np.arange(int(1.1 * SR)) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 18 * np.arange(int(1.1 * SR)) / SR))) * np.linspace(0.8, 1, int(1.1 * SR))
put(_step, 16.08, 0.035)            # 打印步进声
put(thump(70, 0.1), 16.08, 0.28)
put(slap(), 17.5, 0.42); put(thump(46, 0.36), 17.5, 0.62)    # 归位
put(win(), 18.3, 0.24)
mix = mix[:int(dur * SR)]
peak = np.abs(mix).max(); mix = mix * min(1, 0.71 / peak)
print('峰值 dBFS', round(20 * np.log10(np.abs(mix).max()), 1))
with wave.open(path, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    d = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    w.writeframes(np.c_[d, d].tobytes())
