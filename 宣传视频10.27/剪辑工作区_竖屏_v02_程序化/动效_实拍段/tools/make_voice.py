# 按 人声摆放表.json 把 12 句配音排回时间线，出单声道人声轨。每句响度对齐到 C 版成片里的电平。py -3.12 make_voice.py A|B|C|D 增益dB
# A 原录音 / B 单声道 / C 单声道加EQ / D C 版加短房间混响。人声摆放表来自 分轨_全混.mov 减 C 版的结果。
import json, pathlib, subprocess, sys, wave
import numpy as np
FX = pathlib.Path(__file__).resolve().parents[1]; V = FX.parent / '配音_v05'; SR = 48000
ver, boost = sys.argv[1], float(sys.argv[2])
DIR = {'A': V, 'B': V / '去闷试听' / 'B_单声道', 'C': V / '去闷试听' / 'C_单声道加EQ', 'D': V / '去闷试听' / 'C_单声道加EQ'}[ver]
C = V / '去闷试听' / 'C_单声道加EQ'
def rd(p):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(p), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(b, 'f4').copy()
rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-9)
out = np.zeros(2459200 + SR, 'f4')
for c in json.load(open(FX / 'out' / '人声摆放表.json')):
    n = f"{c['k']:02d}.wav"; o, m = c['offset'], c['len']
    ref = rd(C / n)[o:o + m] * c['gain']
    x = rd(DIR / n)[o:o + m]; x = x * rms(ref) / rms(x)
    out[c['start']:c['start'] + m] += x
if ver == 'D':                 # 短房间混响：0.35 秒衰减噪声，湿声低约 15 dB，先滤掉低频和齿音避免发糊
    rs = np.random.RandomState(7); t = np.arange(int(0.45 * SR)) / SR
    ir = rs.randn(len(t)) * np.exp(-t / 0.09) * np.minimum(t / 0.004, 1); ir /= np.sqrt(np.sum(ir ** 2))
    wet = np.fft.irfft(np.fft.rfft(out, len(out) + len(ir)) * np.fft.rfft(ir, len(out) + len(ir)))[:len(out)]
    F = np.fft.rfftfreq(len(wet), 1 / SR); W = np.fft.rfft(wet); W *= (F > 200) * (F < 6000); wet = np.fft.irfft(W, len(wet))
    out = out + wet * 10 ** (-15 / 20)
out = out * 10 ** (boost / 20)
d = (np.clip(out, -1, 1) * 32767).astype('<i2')
with wave.open(str(FX / 'out' / f'人声_{ver}.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes())
print(ver, '峰值 dB', round(20 * np.log10(np.abs(out).max()), 1))
