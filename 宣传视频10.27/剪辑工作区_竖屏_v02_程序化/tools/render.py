"""竖屏逐帧渲染：打开 stage.html，按 t = n/fps 调 __film.render(t) 后截图，管道给 ffmpeg。
  python render.py --out out/预览.mp4               # 整片（无声）
  python render.py --start 0 --end 6 --out out/钩子.mp4
  python render.py --stills 0.4,1.5,17.2 --out out/stills
"""
import argparse, asyncio, base64, functools, http.server, pathlib, subprocess, sys, threading, time

ROOT = pathlib.Path(__file__).resolve().parents[1]


def serve(root):
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store'); super().end_headers()
        def guess_type(self, path):
            return 'text/javascript' if str(path).endswith(('.js', '.mjs')) else super().guess_type(path)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(root)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


async def main(a):
    from playwright.async_api import async_playwright
    port = serve(ROOT)
    async with async_playwright() as p:
        browser = None
        for extra in [{}, {'channel': 'chrome'}, {'channel': 'msedge'}]:
            try:
                browser = await p.chromium.launch(args=['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none'], **extra); break
            except Exception as e:
                last = e
        if browser is None: raise last
        ctx = await browser.new_context(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        page = await ctx.new_page()
        page.on('pageerror', lambda e: print('[页面错误]', e, file=sys.stderr))
        page.on('console', lambda m: print('[console]', m.text, file=sys.stderr) if m.type in ('error', 'warning') else None)
        await page.goto(f'http://127.0.0.1:{port}/stage.html')
        await page.wait_for_function('window.__film && document.body.dataset.ready', timeout=60000)
        await page.evaluate('__film.ready()')
        fps = await page.evaluate('__film.fps'); dur = await page.evaluate('__film.duration')
        t_from, t_to = a.start, (a.end if a.end is not None else dur)
        out = pathlib.Path(a.out)
        cdp = await ctx.new_cdp_session(page)
        stills = [float(x) for x in a.stills.split(',')] if a.stills else None
        if stills:
            out.mkdir(parents=True, exist_ok=True)
            for t in stills:
                await page.evaluate('t=>__film.render(t)', t)
                r = await cdp.send('Page.captureScreenshot', {'format': 'png'})
                (out / f'still_{t:06.2f}s.png').write_bytes(base64.b64decode(r['data']))
            print('定格已出：', out); await browser.close(); return
        out.parent.mkdir(parents=True, exist_ok=True)
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(fps), '-c:v', 'mjpeg', '-i', '-',
                               '-c:v', 'libx264', '-preset', a.preset, '-crf', str(a.crf), '-bf', '0', '-pix_fmt', 'yuv420p',
                               '-movflags', '+faststart', str(out)], stdin=subprocess.PIPE)
        t0 = time.time()
        n0, n1 = int(round(t_from * fps)), int(round(t_to * fps))
        for n in range(n0, n1):
            t = n / fps
            await page.evaluate('t=>__film.render(t)', t)
            r = await cdp.send('Page.captureScreenshot', {'format': 'jpeg', 'quality': a.q, 'optimizeForSpeed': True})
            ff.stdin.write(base64.b64decode(r['data']))
            if n % fps == 0: print(f'\r{t:5.1f}s / {t_to:.1f}s  {time.time() - t0:4.0f}s', end='', flush=True)
        ff.stdin.close(); ff.wait()
        print(f'\n完成：{out}  用时 {time.time() - t0:.0f}s')
        await browser.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='out/画面.mp4')
    ap.add_argument('--start', type=float, default=0)
    ap.add_argument('--end', type=float, default=None)
    ap.add_argument('--stills', default='')
    ap.add_argument('--crf', type=int, default=18)
    ap.add_argument('--q', type=int, default=92, help='截图 JPEG 质量')
    ap.add_argument('--preset', default='medium')
    asyncio.run(main(ap.parse_args()))
