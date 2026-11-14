"""实拍段动效渲染。hermes venv 的 python 运行。
  render.py --plates                 从无字幕成片抽底片
  render.py --stills 19,100,560      出定格（全片帧号）到 out/st
  render.py --all                    渲三段 ProRes 到 out/
"""
import argparse, asyncio, base64, functools, http.server, pathlib, subprocess, sys, threading, time, urllib.parse
from playwright.async_api import async_playwright
FX = pathlib.Path(__file__).resolve().parents[1]; ROOT = FX.parent
SRC = ROOT / 'out' / '棋甲对决_竖屏抖音_v09e_全片_无字幕.mp4'
SEGS = {'A片头': (0, 160), 'B人物': (445, 627), 'C活动': (1209, 1537)}

def plates():
    d = FX / 'out' / 'plates'; d.mkdir(parents=True, exist_ok=True)
    for a, b in SEGS.values():
        sel = f"select='between(n,{a},{b - 1})'"
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(SRC), '-vf', sel, '-vsync', '0', '-q:v', '1', '-start_number', str(a), str(d / '%05d.jpg')], check=True)
    print('底片', len(list(d.glob('*.jpg'))))

def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def end_headers(self): self.send_header('Cache-Control', 'no-store'); super().end_headers()
        def guess_type(self, path): return 'text/javascript' if str(path).endswith('.js') else super().guess_type(path)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv.server_address[1]

async def main(a):
    port = serve()
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--force-color-profile=srgb', '--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'])
        pg = await (await b.new_context(viewport={'width': 1080, 'height': 1920})).new_page()
        pg.on('pageerror', lambda e: print('[页面错误]', e, file=sys.stderr))
        pg.on('console', lambda m: print('[console]', m.text, file=sys.stderr) if m.type == 'error' else None)
        await pg.goto(f'http://127.0.0.1:{port}/{urllib.parse.quote(FX.name)}/stage.html')
        await pg.wait_for_function('window.__film && document.body.dataset.ready', timeout=60000)
        await pg.evaluate('__film.ready()')
        if a.stills:
            d = FX / 'out' / 'st'; d.mkdir(parents=True, exist_ok=True)
            for n in [int(x) for x in a.stills.split(',')]:
                await pg.evaluate('n=>__film.render(n)', n)
                (d / f'{n:05d}.png').write_bytes(base64.b64decode((await pg.evaluate('__film.png()')).split(',')[1]))
            print('定格', d)
        else:
            for name, (s, e) in SEGS.items():
                if a.only and a.only not in name: continue
                out = FX / 'out' / f'实拍段_{name}.mov'; t0 = time.time()
                ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'png', '-i', '-', '-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', '-vendor', 'apl0', str(out)], stdin=subprocess.PIPE)
                for n in range(s, e):
                    await pg.evaluate('n=>__film.render(n)', n)
                    ff.stdin.write(base64.b64decode((await pg.evaluate('__film.png()')).split(',')[1]))
                ff.stdin.close(); ff.wait(); print(name, e - s, '帧', round(time.time() - t0), '秒', flush=True)
        await b.close()

ap = argparse.ArgumentParser(); ap.add_argument('--plates', action='store_true'); ap.add_argument('--stills', default=''); ap.add_argument('--all', action='store_true'); ap.add_argument('--only', default='')
A = ap.parse_args()
if A.plates: plates()
if A.stills or A.all: asyncio.run(main(A))
