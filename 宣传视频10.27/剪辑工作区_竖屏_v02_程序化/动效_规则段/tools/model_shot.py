# 给候选模型出检查图：python model_shot.py <输出目录>
import asyncio, base64, functools, http.server, json, pathlib, sys, threading, urllib.parse
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
JOBS = [  # 名字, 文件, 上色, yaw, pitch, Z 轴朝上
    ('巴掌整机_v02_0921', 'palm_v02.glb', True, 35, 18, True),
    ('巴掌整机_v02_0921_背', 'palm_v02.glb', True, 215, 18, True),
    ('拳头头部_v01_1007', 'punch_head.glb', True, 35, 18, True),
    ('拳头整机_收回_0928', 'punch_whole.stl', False, 35, 18, True),
    ('拳头整机_打出_0928', 'punch_whole_out.stl', False, 35, 18, True),
    ('拳头微调_0929', 'punch_tuned.stl', False, 35, 18, True),
    ('场地_v11_1021', 'arena_v11.glb', False, 25, 38, False),
    ('球靶_v09_1019', 'ball_v09.glb', True, 35, 15, True),
]

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def guess_type(self, path): return 'text/javascript' if str(path).endswith('.js') else super().guess_type(path)

async def main(out):
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); port = srv.server_address[1]
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 900, 'height': 900})
        pg.on('pageerror', lambda e: print('[页面错误]', e))
        await pg.goto(f'http://127.0.0.1:{port}/tools/model_shot.html')
        await pg.wait_for_function('document.body.dataset.ready', timeout=60000)
        for name, f, tint, yaw, pitch, upz in JOBS:
            r = await pg.evaluate('a=>shot(...a)', [f'/assets/models/{f}', tint, yaw, pitch, upz])
            (out / f'{name}.png').write_bytes(base64.b64decode(r['png'].split(',')[1]))
            print(name, '尺寸', r['size'], '部件', len(r['names']), r['names'][:30], flush=True)
        await b.close()

asyncio.run(main(sys.argv[1]))
