# 把三段实拍动效叠到达芬奇导出的底片上，配上 mix_audio.py 的混音，出成片无字幕版。不经过达芬奇，时间线没动。py -3.12 build.py
import pathlib, subprocess
FX = pathlib.Path(__file__).resolve().parents[1]; ROOT = FX.parent
base = ROOT / 'out' / '棋甲对决_竖屏抖音_v09e_全片_无字幕.mp4'
out = ROOT / 'out' / '棋甲对决_竖屏抖音_最终版_无字幕.mp4'
segs = [('实拍段_A片头.mov', 0), ('实拍段_B人物.mov', 445), ('实拍段_C活动.mov', 1209)]
args = ['ffmpeg', '-y', '-v', 'error', '-i', str(base)]
for name, f in segs: args += ['-itsoffset', f'{f / 30:.6f}', '-i', str(FX / 'out' / name)]
args += ['-i', str(FX / 'out' / '混音_v12.wav')]
chain, last = [], '0:v'
for i, _ in enumerate(segs):
    chain.append(f'[{last}][{i + 1}:v]overlay=0:0:eof_action=pass[v{i}]'); last = f'v{i}'
subprocess.run(args + ['-filter_complex', ';'.join(chain), '-map', f'[{last}]', '-map', '4:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-bf', '0', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(out)], check=True)
print('完成', out)
