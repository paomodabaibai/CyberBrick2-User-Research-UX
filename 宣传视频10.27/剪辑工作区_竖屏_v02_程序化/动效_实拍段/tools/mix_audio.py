# 全片混音：无人声轨 + 人声 + 实拍段音效 + 片头 vine boom + 配乐（配音开口后进，遇配音自动压低）。py -3.12 mix_audio.py 配乐文件名 输出名 人声版本(A/B/C/D)
import pathlib, subprocess, sys
FX = pathlib.Path(__file__).resolve().parents[1]; ROOT = FX.parent; BGM = ROOT / '配乐'
base = FX / 'out' / '分轨_无人声.wav'; voice = FX / 'out' / f'人声_{sys.argv[3]}.wav'
DUR = 1537 / 30
BOOM_AT = 19 / 30 - 0.085     # 第 19 帧巴掌打中；文件开头有 0.085 秒空白
BOOM_GAIN = 1.0
# 不做过载、EQ：用户要听到下载的原音色
DUCK_EXPR = "1-0.875*min(clip((t-0.60)/0.03,0,1),clip((1.90-t)/0.50,0,1))"   # boom 响的时候把现场原声压低约 18 dB，让它露出来
MUSIC_AT, MUSIC_FADE = 4.9, 1.0   # 跟“大家好啊”一起淡入
MUSIC_GAIN = -7               # dB；手机外放低频弱，太小会听不见
music, out = BGM / sys.argv[1], FX / 'out' / sys.argv[2]
ms = lambda s: int(round(s * 1000))
chain = [
    f"[0:a]aresample=48000,volume='{DUCK_EXPR}':eval=frame[b0];[4:a]aresample=48000,pan=stereo|c0=c0|c1=c0[vo];[b0][vo]amix=inputs=2:duration=first:normalize=0,asplit[base][key]",
    '[1:a]aresample=48000[fx]',
    f'[2:a]aresample=48000,volume={BOOM_GAIN},adelay={ms(BOOM_AT)}:all=1[boom]',
    f'[3:a]aresample=48000,highpass=f=35,volume={MUSIC_GAIN}dB,atrim=0:{DUR - MUSIC_AT:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={MUSIC_FADE},afade=t=out:st={DUR - MUSIC_AT - 1.2:.3f}:d=1.2,adelay={ms(MUSIC_AT)}:all=1[m]',
    '[m][key]sidechaincompress=threshold=0.05:ratio=3:attack=30:release=400:makeup=1[bgm]',
    '[base][fx][boom][bgm]amix=inputs=4:duration=first:normalize=0,alimiter=limit=0.89:level=false,volume=-1dB[a]',   # 限幅器会略过冲，再退 1 dB 防手机破音
]
args = ['ffmpeg', '-y', '-v', 'error', '-i', str(base), '-i', str(FX / 'out' / '音效_实拍段.wav'), '-i', str(BGM / 'vine-boom.mp3'), '-i', str(music), '-i', str(voice)]
subprocess.run(args + ['-filter_complex', ';'.join(chain), '-map', '[a]', '-t', f'{DUR:.3f}', '-c:a', 'pcm_s16le', str(out)], check=True)
print('完成', out)
