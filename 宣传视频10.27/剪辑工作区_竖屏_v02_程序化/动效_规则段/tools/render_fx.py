"""规则段动效渲染。hermes venv 的 python（带 playwright）运行。
  --stills 0.3,1.7   出定格 PNG（--mode preview 带实拍）
  --mode preview --out out/样片.mp4        审片版（实拍 + 叠层 + 示意字幕）
  --mode alpha   --out out/叠层.mov        透明叠层（ProRes 4444），放达芬奇视频 2 轨
"""
import argparse, asyncio, base64, functools, http.server, pathlib, subprocess, sys, threading, time, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
FX = pathlib.Path(__file__).resolve().parents[1]


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
                browser = await p.chromium.launch(args=['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'], **extra); break
            except Exception as e:
                last = e
        if browser is None: raise last
        ctx = await browser.new_context(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        page = await ctx.new_page()
        page.on('pageerror', lambda e: print('[页面错误]', e, file=sys.stderr))
        page.on('console', lambda m: print('[console]', m.text, file=sys.stderr) if m.type in ('error', 'warning') else None)
        url = f'http://127.0.0.1:{port}/{urllib.parse.quote(FX.name)}/stage.html?mode={a.mode}'
        await page.goto(url)
        await page.wait_for_function('window.__film && document.body.dataset.ready', timeout=60000)
        await page.evaluate('__film.ready()')
        fps, dur = await page.evaluate('[__film.fps, __film.duration]')
        out = pathlib.Path(a.out)
        cdp = await ctx.new_cdp_session(page)
        if a.stills:
            out.mkdir(parents=True, exist_ok=True)
            for t in [float(x) for x in a.stills.split(',')]:
                await page.evaluate('t=>__film.render(t)', t)
                data = await page.evaluate('__film.png()')
                (out / f'still_{t:06.2f}s.png').write_bytes(base64.b64decode(data.split(',')[1]))
            print('定格已出：', out); await browser.close(); return
        out.parent.mkdir(parents=True, exist_ok=True)
        if a.mode == 'alpha':
            enc = ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-vendor', 'apl0', '-qscale:v', '9']
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(fps), '-c:v', 'png', '-i', '-', *enc, str(out)], stdin=subprocess.PIPE)
        else:
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(fps), '-c:v', 'png', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-bf', '0', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(out)], stdin=subprocess.PIPE)
        t0 = time.time()
        for n in range(int(round(a.start * fps)), int(round((a.end or dur) * fps))):
            await page.evaluate('t=>__film.render(t)', n / fps)
            data = await page.evaluate('__film.png()')
            ff.stdin.write(base64.b64decode(data.split(',')[1]))
            if n % fps == 0: print(f'{n / fps:5.1f}s  {time.time() - t0:4.0f}s', flush=True)
        ff.stdin.close(); ff.wait()
        print(f'完成：{out}  用时 {time.time() - t0:.0f}s')
        await browser.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='out/样片.mp4')
    ap.add_argument('--mode', default='preview')
    ap.add_argument('--start', type=float, default=0)
    ap.add_argument('--end', type=float, default=None)
    ap.add_argument('--stills', default='')
    asyncio.run(main(ap.parse_args()))
