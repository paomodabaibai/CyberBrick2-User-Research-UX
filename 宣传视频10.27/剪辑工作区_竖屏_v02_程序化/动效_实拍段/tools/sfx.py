# 实拍段音效：时间都是全片秒数，和 stage.js 的打击点对齐；合成方法同 动效_规则段/tools/sfx.py。py -3.12 sfx.py out/音效_实拍段.wav
import sys, wave
import numpy as np

SR = 48000
DUR = 51.243
rs = np.random.RandomState(11)
path = sys.argv[1]
mix = np.zeros(int(DUR * SR) + SR)

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

def whoosh(d=0.24):              # 挥动：噪声先亮后暗，起落都柔
    n = int(d * SR); u = np.linspace(0, 1, n)
    return lp(rs.randn(n), 5) * np.sin(np.pi * u) ** 2

def win():                       # WIN：三个玻璃音叠起，和规则段同一动机
    out = np.zeros(int(1.2 * SR))
    for f, at in ((880, 0), (1318.5, 0.05), (2217.5, 0.1)):
        g = glass(f); i = int(at * SR); out[i:i + len(g)] += g
    return out

# 片头
put(slap(), 0.633, 0); put(thump(46, 0.3), 0.633, 0)             # 这一下只留 vine boom（mix_audio.py）；留调用是为了后面噪声序列不变
put(thump(66, 0.14), 1.1, 0.34)                                  # 打起来了
put(whoosh(0.2), 2.62, 0.3)
put(slap(), 3.333, 0.5); put(thump(42, 0.32), 3.333, 0.5)      # K.O.
put(thump(90, 0.08), 3.6, 0.2); put(thump(84, 0.08), 3.8, 0.16)  # 倒地
# 人物介绍（有配音，整体压低）
put(whoosh(0.22), 14.72, 0.24); put(thump(70, 0.1), 14.87, 0.26)
put(whoosh(0.2), 15.22, 0.14); put(whoosh(0.2), 15.74, 0.14)
put(whoosh(0.3), 16.8, 0.26); put(thump(60, 0.12), 17.13, 0.26)  # 横扫
put(whoosh(0.2), 17.42, 0.26)
put(whoosh(0.2), 18.08, 0.22); put(thump(70, 0.1), 18.2, 0.24)
put(thump(84, 0.08), 18.76, 0.26); put(thump(84, 0.08), 19.02, 0.26); put(thump(92, 0.07), 19.24, 0.22)
put(slap(), 19.36, 0.34); put(thump(46, 0.3), 19.36, 0.5)        # 肉
put(whoosh(0.22), 20.2, 0.18); put(thump(66, 0.1), 20.3, 0.24)
# 活动页
put(whoosh(0.2), 40.2, 0.2); put(thump(58, 0.16), 40.46, 0.4); put(glass(1320), 40.46, 0.12)
put(glass(1760), 41.54, 0.1); put(thump(70, 0.1), 43.9, 0.24); put(glass(2240), 43.9, 0.1)
put(thump(60, 0.14), 45.767, 0.34); put(whoosh(0.2), 45.66, 0.2)
put(glass(1680), 49.1, 0.12)                                     # 准星锁球
put(slap(), 1504 / 30, 0.56); put(thump(46, 0.42), 1504 / 30, 0.72); put(win(), 1504 / 30, 0.26)

mix = mix[:int(DUR * SR)]
peak = np.abs(mix).max(); mix = mix * min(1, 0.71 / peak)
print('峰值 dBFS', round(20 * np.log10(np.abs(mix).max()), 1))
with wave.open(path, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    d = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    w.writeframes(np.c_[d, d].tobytes())
