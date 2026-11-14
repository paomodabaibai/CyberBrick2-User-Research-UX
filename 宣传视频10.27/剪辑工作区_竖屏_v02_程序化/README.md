# 棋甲对决｜抖音竖屏 v02（程序化剪辑）

> **这份是 v02–v04 的旧说明。当前是最终版，看 `..\当前状态_竖屏v08交接.md`。** v05 以达芬奇时间线为准，动效在 `动效_规则段\`。

不用达芬奇。整片 = film.js 时间轴 + stage.js 逐帧绘制（方法同 美院学习平台/视频制作/23日005程序化全片/影片引擎）。

- 成片：out/棋甲对决_竖屏抖音_v04.mp4（第四轮：3D 规则动画 + 真实对局段 + 放慢节奏，72.4s；v03/v02b/v02 为前几轮）
- 口播稿与配乐方案：口播稿与配乐方案_v04.md
- 3D 规则动画 arena3d.js（three.js，engine/three.module.min.js）：真实场地 120×80 cm 按 V02 画面反算建模；相机 CAM0 由 V02 第 3 秒最小二乘解算（重投影约 7 px），时间表 AT、路线、机位都在文件顶部
- 06_游戏设计/Figma制作图与3D_v08 里的 3D 是 10-19 旧设计稿（正方形、布局不同），没有采用；地板贴图用 06_游戏设计/地板无缝纹理_v10
- 旧：out/棋甲对决_竖屏抖音_v02b.mp4（第二轮：科技字体、名牌移到顶部、VS 页整张露出机器人；v02 为第一轮）
- 字体：中文 得意黑 Smiley Sans、数字英文 Orbitron（均 OFL 免费可商用），在 fonts/
- 规格：1080×1920，30fps，39.4s，原声+合成音效，无配乐
- 改镜头入出点/推拉/变速：film.js 的 S 数组；改字/字幕/贴纸：film.js 的 overlays；画法：stage.js
- 重出：
  python tools/plates.py                      # 改了入出点才需要
  <hermes venv python> tools/render.py --out out/画面_v02.mp4    # 约 1 分钟；--stills 1.2,5 出定格
  python tools/audio.py out/声音_raw.wav
  ffmpeg -i out/画面_v02.mp4 -i out/声音_raw.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-15:TP=-1.5 -c:a aac -b:a 192k -shortest out/棋甲对决_竖屏抖音_v02.mp4
- hermes venv python：C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe（带 playwright）
- 字幕 = 口播稿，录配音后按配音时长改 overlays 里 sub 的时间
