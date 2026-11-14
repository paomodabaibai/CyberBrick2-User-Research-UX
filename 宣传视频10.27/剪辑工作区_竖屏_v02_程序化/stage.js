// 竖屏舞台：每帧按影片时间 t 画出素材（推拉、震屏、白闪）和叠层（大字、字幕、贴纸、落版）。
// 渲染器调用 await __film.render(t) 后截图；没有任何实时动画，同一 t 永远画出同一帧。
import { EASE, clamp01, lerp, rng } from './engine/math.js';
import { drawType } from './engine/type.js';
import { FPS, W, H, shots, overlays, duration, srcTime } from './film.js';
import { init3d, render3d, project3d, AT, SPOTS } from './arena3d.js';

const cv = document.getElementById('cv'); cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');
const manifest = await (await fetch('out/plates/manifest.json', { cache: 'no-store' })).json();

const EZ = { out: EASE.enter, in: EASE.exit, drift: EASE.drift, move: EASE.move, linear: EASE.linear };
const img = new Image(); let curUrl = '';
async function plate(url) {
  if (url === curUrl) return img;
  img.src = url; await img.decode(); curUrl = url; return img;
}

function camAt(shot, lt) {
  const K = shot.cam;
  if (lt <= K[0].t) return { z: K[0].z, c: K[0].c };
  for (let i = 1; i < K.length; i++) if (lt <= K[i].t) {
    const a = K[i - 1], b = K[i], u = (EZ[b.e] || EASE.move)(clamp01((lt - a.t) / (b.t - a.t)));
    return { z: Math.exp(lerp(Math.log(a.z), Math.log(b.z), u)), c: [lerp(a.c[0], b.c[0], u), lerp(a.c[1], b.c[1], u)] };
  }
  const k = K[K.length - 1]; return { z: k.z, c: k.c };
}
// 震屏：衰减的确定性噪声
function shakeAt(shot, lt) {
  let dx = 0, dy = 0, r = 0, amp = 0;
  for (const s of shot.fx?.shake || []) {
    const u = (lt - s.t) / s.d; if (u < 0 || u > 1) continue;
    const env = (1 - u) ** 2, f = Math.floor((lt - s.t) * FPS), R = rng(9173 + f * 31 + Math.round(s.t * 100));
    dx += (R() - 0.5) * 2 * s.a * env; dy += (R() - 0.5) * 2 * s.a * env; r += (R() - 0.5) * 0.03 * env; amp = Math.max(amp, s.a * env);
  }
  return { dx, dy, r, amp };
}
function shotAt(t) { for (const s of shots) if (t < s.start + s.dur) return s; return shots[shots.length - 1]; }

// 当前镜头的几何（叠层的 ring 用它把源坐标换成屏幕坐标）
let geo = null;
function layout(shot, lt, iw, ih) {
  const { z, c } = camAt(shot, lt), sh = shakeAt(shot, lt);
  const s = Math.max(W / iw, H / ih) * z * (1 + sh.amp / 400);
  const dw = iw * s, dh = ih * s;
  const ox = Math.min(0, Math.max(W - dw, W / 2 - c[0] * dw)), oy = Math.min(0, Math.max(H - dh, H / 2 - c[1] * dh));
  return { s, dw, dh, ox, oy, sh, iw, ih };
}

async function drawFootage(t) {
  const shot = shotAt(t), lt = t - shot.start, m = manifest[shot.id];
  const k = m.kind === 'photo' ? 0 : Math.max(0, Math.min(m.n - 1, Math.round((srcTime(shot, lt) - m.a0) * m.fps)));
  const im = await plate(`out/plates/${shot.id}/${String(k).padStart(5, '0')}.jpg`);
  const g = layout(shot, lt, im.naturalWidth, im.naturalHeight);
  const dim = overlays.find(o => o.k === 'dim' && t >= o.at && t < o.out);
  ctx.save();
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  ctx.translate(W / 2 + g.sh.dx, H / 2 + g.sh.dy); ctx.rotate(g.sh.r); ctx.translate(-W / 2, -H / 2);
  if (shot.render === 'arena3d') {
    // 实拍（按宽度完整放入、虚化铺底）与 3D 同机位重合，交叉淡化后进入 3D
    const x = EASE.drift(clamp01((lt - AT.xfade[0]) / (AT.xfade[1] - AT.xfade[0])));
    if (x < 1) drawBand(im, 1, [0.5, 0.5], 1);
    const c3 = render3d(lt);
    if (c3 && x > 0) { ctx.globalAlpha = x; ctx.drawImage(c3, 0, 0, W, H); ctx.globalAlpha = 1; }
    geo = { shot, lt, ...g };
  } else if (shot.fit === 'band') {
    const { z, c } = camAt(shot, lt); drawBand(im, z, c, 1); geo = { shot, lt, ...g };
  } else if (shot.fit === 'contain') {
    // 横图整张放中间：背景用同一张图虚化压暗 + 左红右蓝斜分染色，前景完整露出两台机器人
    ctx.save(); ctx.filter = 'blur(28px) brightness(0.55)'; ctx.drawImage(im, g.ox - 40, g.oy - 40, g.dw + 80, g.dh + 80); ctx.restore();
    ctx.globalAlpha = 0.42;
    ctx.fillStyle = '#ff3326'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(W * 0.62, 0); ctx.lineTo(W * 0.38, H); ctx.lineTo(0, H); ctx.fill();
    ctx.fillStyle = '#2b5cff'; ctx.beginPath(); ctx.moveTo(W * 0.62, 0); ctx.lineTo(W, 0); ctx.lineTo(W, H); ctx.lineTo(W * 0.38, H); ctx.fill();
    ctx.globalAlpha = 1;
    const z = camAt(shot, lt).z, cw = (W - 60) * z, ch = cw * im.naturalHeight / im.naturalWidth, cx = (W - cw) / 2, cy = shot.cy - ch / 2;
    const bh = (W - 60) * im.naturalHeight / im.naturalWidth, by = shot.cy - bh / 2;
    ctx.save(); ctx.beginPath(); ctx.rect(30, by, W - 60, bh); ctx.clip();
    ctx.drawImage(im, cx, cy, cw, ch); ctx.restore();
    ctx.strokeStyle = 'rgba(255,255,255,0.9)'; ctx.lineWidth = 5; ctx.strokeRect(30, by, W - 60, bh);
    geo = { shot, lt, ...g, ox: cx, oy: cy, dw: cw, dh: ch, box: [30, by, W - 60, bh] };
  } else {
    if (dim) ctx.filter = `blur(${(dim.blur * EASE.drift(clamp01((t - dim.at) / 0.6))).toFixed(1)}px)`;
    ctx.drawImage(im, g.ox, g.oy, g.dw, g.dh);
    geo = { shot, lt, ...g };
  }
  ctx.restore();
  if (dim) { ctx.fillStyle = `rgba(8,10,20,${(dim.a * EASE.drift(clamp01((t - dim.at) / 0.6))).toFixed(3)})`; ctx.fillRect(0, 0, W, H); }
  for (const f of shot.fx?.flash || []) {
    const u = (lt - f.t) / f.d; if (u < 0 || u > 1) continue;
    ctx.fillStyle = `rgba(255,255,255,${(0.9 * (1 - u) ** 2).toFixed(3)})`; ctx.fillRect(0, 0, W, H);
  }
}
// 横画面放进竖屏：同一画面虚化压暗铺底，前景按宽度放入（z 放大、c 为焦点），放大到超出时自动裁切
function drawBand(im, z, c, a) {
  const iw = im.naturalWidth, ih = im.naturalHeight, bs = H / ih;
  ctx.save(); ctx.filter = 'blur(30px) brightness(0.45)'; ctx.drawImage(im, W / 2 - iw * bs / 2, 0, iw * bs, H); ctx.restore();
  const s = W / iw * z, dw = iw * s, dh = ih * s;
  const ox = Math.min(0, Math.max(W - dw, W / 2 - c[0] * dw));
  const y0 = dh > H ? Math.min(0, Math.max(H - dh, H / 2 - c[1] * dh)) : H / 2 - c[1] * dh;
  ctx.save(); ctx.globalAlpha = a; ctx.drawImage(im, ox, y0, dw, dh); ctx.restore();
}
const toScreen = (nx, ny) => [geo.ox + nx * geo.dw + geo.sh.dx, geo.oy + ny * geo.dh + geo.sh.dy];

// ---------- 叠层 ----------
// 字体：中文 Tech = 得意黑（科技斜体）；数字/英文 Orb = Orbitron。不用纯黑字，暗色只用于柔和投影
const TE = 'Tech', OR = 'Orb';
const vis = (o, t, tail = 0.6) => t >= o.at && (o.out === undefined || t < o.out + tail);
const outP = (o, t, d = 0.3) => o.out === undefined ? 0 : clamp01((t - o.out) / d);
const SHADOW = (c = 'rgba(0,0,0,0.38)', b = 16, y = 3) => { ctx.shadowColor = c; ctx.shadowBlur = b; ctx.shadowOffsetY = y; };

function strokeText(text, x, y, font, fill, stroke, lw, align = 'center') {
  ctx.font = font; ctx.textAlign = align; ctx.lineJoin = 'round'; ctx.miterLimit = 2;
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.strokeText(text, x, y); }
  ctx.fillStyle = fill; ctx.fillText(text, x, y);
}
const skewed = (x, y, k, fn) => { ctx.save(); ctx.translate(x, y); ctx.transform(1, 0, k, 1, 0, 0); fn(); ctx.restore(); };

const draw = {
  title(o, t) {
    ctx.save(); SHADOW('rgba(0,0,0,0.35)', 18, 3);
    if (!o._init) { o._init = 1; o.exit = 'rise'; }
    drawType(ctx, o, t);
    ctx.restore();
  },
  sub(o, t) {
    const a = EASE.enter(clamp01((t - o.at) / 0.16)) * (1 - outP(o, t, 0.12));
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; SHADOW('rgba(0,0,0,0.5)', 10, 2);
    strokeText(o.text, 520, 1388 + (1 - a) * 14, `64px ${TE}`, '#fff', 'rgba(20,24,40,0.55)', 6);
    ctx.restore();
  },
  tag(o, t) {
    const e = EASE.enter(clamp01((t - o.at) / 0.4)), q = EASE.exit(outP(o, t, 0.25));
    if (e <= 0 || q >= 1) return;
    ctx.save(); ctx.font = `50px ${TE}`;
    const w = ctx.measureText(o.text).width + 70, x = o.x - (1 - e) * 60 - q * 60;
    ctx.globalAlpha = Math.min(1, e * 1.5) * (1 - q);
    ctx.fillStyle = 'rgba(16,20,40,0.62)'; ctx.beginPath(); ctx.roundRect(x, o.y - 56, w, 82, 6); ctx.fill();
    ctx.fillStyle = '#ffd400'; ctx.fillRect(x, o.y - 56, 10, 82);
    ctx.fillStyle = '#fff'; ctx.textAlign = 'left'; ctx.fillText(o.text, x + 36, o.y + 4);
    ctx.restore();
  },
  burst(o, t) {
    const d = t - o.at, q = outP(o, t, 0.2);
    if (d < 0 || q >= 1) return;
    const pop = d < 0.12 ? lerp(0.3, 1.25, EASE.enter(d / 0.12)) : lerp(1.25, 1, EASE.enter(clamp01((d - 0.12) / 0.2)));
    const jit = d < 0.35 ? Math.sin(d * 90) * 4 * (1 - d / 0.35) : 0;
    ctx.save(); ctx.translate(o.x + jit, o.y); ctx.rotate(o.rot || 0); ctx.scale(pop * (1 + q * 0.3), pop * (1 + q * 0.3)); ctx.globalAlpha = 1 - q;
    const n = 14, R = o.r; ctx.beginPath();
    for (let i = 0; i < n * 2; i++) { const a = i / (n * 2) * Math.PI * 2, rr = i % 2 ? R * 0.68 : R * (1 + 0.12 * Math.sin(i * 2.3)); ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr * 0.82); }
    ctx.closePath(); ctx.fillStyle = o.color || '#fff'; ctx.strokeStyle = '#e8202a'; ctx.lineWidth = 8; ctx.lineJoin = 'round';
    SHADOW('rgba(0,0,0,0.3)', 20, 4); ctx.fill(); ctx.shadowColor = 'transparent'; ctx.stroke();
    ctx.textBaseline = 'middle'; strokeText(o.text, 0, 4, `${Math.round(R * 0.66)}px ${TE}`, '#e8202a', null, 0);
    ctx.restore();
  },
  ko(o, t) {
    const d = t - o.at, q = outP(o, t, 0.3);
    if (d < 0 || q >= 1) return;
    const sc = d < 0.16 ? lerp(2.6, 0.92, EASE.exit(d / 0.16)) : lerp(0.92, 1, EASE.enter(clamp01((d - 0.16) / 0.25)));
    ctx.save(); ctx.translate(o.x, o.y); ctx.rotate(-0.06); ctx.scale(sc * (1 + q * 0.6), sc * (1 + q * 0.6)); ctx.globalAlpha = Math.min(1, d / 0.06) * (1 - q);
    ctx.textBaseline = 'middle'; SHADOW('rgba(255,40,40,0.55)', 40, 0);
    skewed(0, 0, -0.2, () => { strokeText('K.O.', 0, 0, `900 230px ${OR}`, '#ff2a2a', '#fff', 16); ctx.shadowColor = 'transparent'; strokeText('K.O.', 0, 0, `900 230px ${OR}`, '#ff2a2a', null, 0); });
    ctx.restore();
  },
  banner(o, t) {
    // 名牌放在画面顶部（机器人在中下部），统一左对齐、从左滑入
    const e = EASE.enter(clamp01((t - o.at) / 0.42)), q = EASE.exit(outP(o, t, 0.22));
    if (e <= 0 || q >= 1) return;
    const col = o.side === 'blue' ? '#2b5cff' : '#ff3326';
    const bw = 560, bh = 168, y = 210, slide = -(1 - e) * bw - q * bw;
    ctx.save(); ctx.translate(slide, 0);
    ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(bw, y); ctx.lineTo(bw - 60, y + bh); ctx.lineTo(0, y + bh); ctx.closePath();
    SHADOW('rgba(0,0,0,0.3)', 26, 4); ctx.fill(); ctx.shadowColor = 'transparent';
    ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.fillRect(0, y + bh, bw - 60, 6);
    ctx.textBaseline = 'alphabetic';
    strokeText(o.en, 66, y + 36, `700 24px ${OR}`, 'rgba(255,255,255,0.8)', null, 0, 'left');
    strokeText(o.title, 64, y + 150, `104px ${TE}`, '#fff', null, 0, 'left');
    ctx.font = `44px ${TE}`; const sw = ctx.measureText(o.sub).width + 64;
    ctx.fillStyle = 'rgba(16,20,40,0.62)'; ctx.fillRect(0, y + bh + 14, sw, 70);
    strokeText(o.sub, 32, y + bh + 63, `44px ${TE}`, '#fff', null, 0, 'left');
    ctx.restore();
  },
  vs(o, t) {
    const d = t - o.at; if (d < 0 || t > o.out || !geo?.box) return;
    const [bx, by, bw, bh] = geo.box;
    const te = EASE.enter(clamp01((d - 0.05) / 0.4));
    ctx.save(); ctx.globalAlpha = te; ctx.textBaseline = 'alphabetic'; SHADOW();
    strokeText('棋甲对决', W / 2, by - 150 - (1 - te) * 30, `170px ${TE}`, '#fff', null, 0);
    strokeText('清华 · 课程小组作品', W / 2, by - 66 - (1 - te) * 30, `54px ${TE}`, '#ffd400', null, 0);
    ctx.restore();
    // 名字条贴在照片下沿：左红拳头，右蓝巴掌
    const le = EASE.enter(clamp01((d - 0.35) / 0.35));
    ctx.save(); ctx.globalAlpha = le; ctx.textBaseline = 'alphabetic';
    for (const [x, c, s, en, al, tx] of [[bx, '#ff3326', '拳头', 'RED', 'left', bx + 36], [bx + bw / 2, '#2b5cff', '巴掌', 'BLUE', 'right', bx + bw - 36]]) {
      ctx.fillStyle = c; ctx.fillRect(x, by + bh, bw / 2, 120);
      strokeText(en, tx, by + bh + 34, `700 22px ${OR}`, 'rgba(255,255,255,0.8)', null, 0, al);
      strokeText(s, tx, by + bh + 106, `68px ${TE}`, '#fff', null, 0, al);
    }
    ctx.restore();
    // VS 砸在两条名字条中间
    const v = d - 0.28; if (v < 0) return;
    const sc = v < 0.14 ? lerp(3, 0.9, EASE.exit(v / 0.14)) : lerp(0.9, 1, EASE.enter(clamp01((v - 0.14) / 0.25)));
    ctx.save(); ctx.translate(W / 2, by + bh + 60); ctx.scale(sc, sc); ctx.textBaseline = 'middle'; SHADOW('rgba(255,212,0,0.6)', 36, 0);
    skewed(0, 0, -0.2, () => strokeText('VS', 0, 0, `900 170px ${OR}`, '#ffd400', '#fff', 8)); ctx.restore();
  },
  step(o, t) {
    const e = EASE.enter(clamp01((t - o.at) / 0.35)), q = EASE.exit(outP(o, t, 0.2));
    if (e <= 0 || q >= 1) return;
    ctx.save(); ctx.globalAlpha = Math.min(1, e * 1.4) * (1 - q); ctx.textBaseline = 'alphabetic'; SHADOW('rgba(0,0,0,0.5)', 14, 2);
    const dx = (1 - e) * -40 + q * 40;
    strokeText(o.n, 80 + dx, 250, `900 64px ${OR}`, '#ffd400', null, 0, 'left');
    const nw = ctx.measureText(o.n).width;
    strokeText(o.text, 80 + nw + 28 + dx, 250, `68px ${TE}`, '#fff', null, 0, 'left');
    ctx.fillStyle = '#ffd400'; ctx.fillRect(80 + dx, 274, nw * e, 6);
    ctx.restore();
  },
  label3d(o, t) {
    if (!geo || geo.shot.render !== 'arena3d') return;
    const e = EASE.enter(clamp01((t - o.at) / 0.3)), q = EASE.exit(outP(o, t, 0.2)); if (e <= 0 || q >= 1) return;
    const xy = o.spot === 'pad' ? SPOTS.PAD[o.side] : SPOTS.BALL[o.side].ball;
    const [x, y] = project3d(xy[0], xy[1], o.spot === 'pad' ? 0 : 10);
    const col = o.side === 'red' ? '#ff4430' : '#3c78ff', size = o.big ? 76 : 46, lift = o.big ? 150 : 100;
    ctx.save(); ctx.globalAlpha = Math.min(1, e * 1.5) * (1 - q); ctx.textBaseline = 'alphabetic';
    ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x, y - 12); ctx.lineTo(x, y - lift * e + 10); ctx.stroke();
    ctx.font = `${size}px ${TE}`; const w = ctx.measureText(o.text).width + 40;
    ctx.fillStyle = col; SHADOW('rgba(0,0,0,0.4)', 18, 3); ctx.fillRect(x - w / 2, y - lift * e - size - 4, w, size + 18); ctx.shadowColor = 'transparent';
    strokeText(o.text, x, y - lift * e + 2, `${size}px ${TE}`, '#fff', null, 0);
    ctx.restore();
  },
  ring(o, t) {
    if (!geo || geo.shot.id !== o.shot || t < o.at || t > o.out) return;
    const lt = t - geo.shot.start, P = o.pts;
    let p = P[0];
    for (let i = 1; i < P.length; i++) if (lt <= P[i][0]) { const u = EASE.drift(clamp01((lt - P[i - 1][0]) / (P[i][0] - P[i - 1][0]))); p = [lt, lerp(P[i - 1][1], P[i][1], u), lerp(P[i - 1][2], P[i][2], u)]; break; } else p = P[i];
    const [x, y] = toScreen(p[1], p[2]), e = EASE.enter(clamp01((t - o.at) / 0.25)), q = clamp01((t - o.out + 0.25) / 0.25);
    ctx.save(); ctx.globalAlpha = e * (1 - q); ctx.strokeStyle = '#ffd400'; ctx.lineWidth = 9; SHADOW('rgba(255,212,0,0.6)', 18, 0);
    const r = 85 * geo.s / 1.8 * (1 + 0.06 * Math.sin(t * 14));
    ctx.beginPath(); ctx.arc(x, y, r * lerp(1.8, 1, e), 0, 7); ctx.stroke(); ctx.restore();
  },
  end(o, t) {
    const d = t - o.at; if (d < 0) return;
    if (!o._specs) o._specs = [
      { at: 0.0, x: W / 2, y: 820, align: 'center', style: 'slam', lines: [{ text: '11.12', size: 230, weight: 900, font: 'orb', color: '#fff', tracking: 0.04 }] },
      { at: 0.35, x: W / 2, y: 960, align: 'center', style: 'rise', lines: [{ text: '北京 · 拓竹线下旗舰店', size: 84, font: 'tech', color: '#fff' }] },
      { at: 0.8, x: W / 2, y: 1140, align: 'center', style: 'rise', lines: [{ text: '带上朋友，来打一局', size: 84, font: 'tech', color: '#fff' }], highlight: [{ line: 0, from: 0, to: 8, at: 0.95, mode: 'pill', color: '#ff3326' }] },
      { at: 1.3, x: W / 2, y: 1300, align: 'center', style: 'blur', lines: [{ text: '棋甲对决 · milk组', size: 52, font: 'tech', color: 'rgba(255,255,255,0.8)' }] },
    ];
    ctx.save(); SHADOW('rgba(0,0,0,0.3)', 16, 2); for (const s of o._specs) drawType(ctx, s, d); ctx.restore();
  },
};

window.__film = {
  fps: FPS, duration,
  async ready() {
    await Promise.all(['40px Tech', '700 40px Orb', '900 40px Orb', '700 16px Orb'].map(f => document.fonts.load(f, '棋甲A1')));
    await init3d(W, H);
    return true;
  },
  async render(t) {
    await drawFootage(t);
    for (const o of overlays) if (o.k !== 'dim' && vis(o, t)) draw[o.k](o, t);
    return true;
  },
};
document.body.dataset.ready = '1';
