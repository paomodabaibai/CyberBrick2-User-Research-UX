# 出审片版：实拍已停用，整段是模型渲染。--final 同时出放进达芬奇的 MOV
param([switch]$final)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$w = Split-Path -Parent $PSScriptRoot
$py = 'C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe'
$out = Join-Path $w 'out'
$c = Join-Path (Split-Path -Parent $w) '配音_v05\去闷试听\C_单声道加EQ'
& $py "$w\tools\render_fx.py" --mode preview --out "$out\画面_审片.mp4"
py -3.12 "$w\tools\sfx.py" 19.4 "$out\音效_规则段.wav"
ffmpeg -y -v error -i "$out\画面_审片.mp4" -i "$c\06.wav" -i "$c\07.wav" -i "$c\08.wav" -i "$c\09.wav" -i "$c\10.wav" -i "$out\音效_规则段.wav" -filter_complex "[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=2.2[a1];[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=2.2,adelay=4500|4500[a2];[3:a]aresample=48000,aformat=channel_layouts=stereo,volume=2.2,adelay=6970|6970[a3];[4:a]aresample=48000,aformat=channel_layouts=stereo,volume=2.2,adelay=9600|9600[a4];[5:a]aresample=48000,aformat=channel_layouts=stereo,volume=2.2,adelay=13500|13500[a5];[a1][a2][a3][a4][a5][6:a]amix=inputs=6:normalize=0:duration=longest,alimiter=limit=0.89[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -t 19.4 -movflags +faststart "$out\棋甲对决_规则段动效_v5.mp4"
if ($final) { & $py "$w\tools\render_fx.py" --mode alpha --out "$out\规则段_v5.mov" }
ffprobe -v error -show_entries format=duration -of csv=p=0 "$out\棋甲对决_规则段动效_v5.mp4"
