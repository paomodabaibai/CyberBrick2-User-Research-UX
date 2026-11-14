# 给达芬奇导出的无字幕成片加字幕：每句渲染成透明 PNG（版式见 subs.html），用 ffmpeg 叠上去。hermes venv 的 python 运行。
# 用法：python burn_subs.py <无字幕.mp4> <字幕.srt> <输出.mp4>
import asyncio, base64, functools, http.server, pathlib, re, subprocess, sys, tempfile, threading, urllib.parse
from playwright.async_api import async_playwright

FX = pathlib.Path(__file__).resolve().parents[1]
src, srt, out = sys.argv[1:4]

def sec(s):
    h, m, r = s.split(':'); a, b = r.split(',')
    return int(h) * 3600 + int(m) * 60 + int(a) + int(b) / 1000
rows = [(sec(a), sec(b), t.strip()) for a, b, t in re.findall(r'(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})\n(.+)', pathlib.Path(srt).read_text(encoding='utf-8-sig'))]
assert rows, '没读到字幕'

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

async def pngs(tmp):
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(FX.parent)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome')
        pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/{urllib.parse.quote(FX.name)}/subs.html')
        await pg.wait_for_function('document.body.dataset.ready')
        await pg.evaluate('ready()')
        for i, (a, b2, t) in enumerate(rows):
            r = await pg.evaluate('t=>draw(t)', t)
            (tmp / f's{i:03d}.png').write_bytes(base64.b64decode(r['png'].split(',')[1]))
            print(f'{a:6.2f}-{b2:6.2f} 宽 {r["width"]:5.0f} 字号 {r["size"]} {t}')
        await b.close()

with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    asyncio.run(pngs(tmp))
    args = ['ffmpeg', '-y', '-v', 'error', '-i', src]
    for i in range(len(rows)): args += ['-i', str(tmp / f's{i:03d}.png')]
    chain, last = [], '0:v'
    for i, (a, b, _) in enumerate(rows):
        chain.append(f"[{last}][{i + 1}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{i}]"); last = f'v{i}'
    subprocess.run(args + ['-filter_complex', ';'.join(chain), '-map', f'[{last}]', '-map', '0:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-bf', '0', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', out], check=True)
print('完成', out)
