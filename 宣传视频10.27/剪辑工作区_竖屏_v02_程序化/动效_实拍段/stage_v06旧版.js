// 实拍段动效：片头打击、人物介绍、活动页。底片是达芬奇导出的无字幕成片（out/plates/全片帧号.jpg），render(n) 是纯函数，n 为全片帧号。
// 文字只放在字幕安全区 X 60–900、Y 220–1440 内，不碰字幕行（Y 约 1398）。
import { EASE, clamp01, lerp, rng, prog } from '../engine/math.js';

export const FPS = 30, W = 1080, H = 1920;
const cv = document.getElementById('cv'); cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');
const TE = 'Tech', OR = 'Orb', RED = '#ff3a2c', BLUE = '#3d7bff', YEL = '#ffd400', NAVY = '#0d1226';

// 打中的瞬间定帧（帧号, 多停几帧），后面跳过同样帧数，总长不变，配音不错位
const HOLD = [[19, 4], [100, 3], [1504, 3]];
const plateOf = n => { for (const [f, k] of HOLD) if (n >= f && n < f + k) return f; return n; };

// 打击：t 秒、震幅 a、推镜 z、中心 c
const BALL_T = 1504 / 30, CUT_HOOK = 83 / 30, CUT_END = 1373 / 30;   // 切点用帧号算，差一帧就会压到下一个镜头
const HITS = [
  { t: 0.633, a: 44, z: 0.24, c: [648, 929], split: 1 },
  { t: CUT_HOOK, a: 16, z: 0.08, c: [540, 900] },
  { t: 3.333, a: 50, z: 0.28, c: [600, 850], split: 1 },
  { t: 3.6, a: 14, z: 0.03, c: [600, 850] }, { t: 3.8, a: 12, z: 0.03, c: [600, 850] },
  { t: 14.833, a: 14, z: 0.06, c: [540, 900] },
  { t: 15.33, a: 16, z: 0.03, c: [380, 850] }, { t: 15.83, a: 14, z: 0.03, c: [560, 840] }, { t: 17.13, a: 24, z: 0.06, c: [600, 900] },
  { t: 18.2, a: 18, z: 0.05, c: [600, 600] },
  { t: 18.76, a: 22, z: 0.05, c: [400, 480] }, { t: 19.02, a: 22, z: 0.05, c: [300, 520] }, { t: 19.24, a: 16, z: 0.04, c: [420, 560] }, { t: 19.36, a: 38, z: 0.14, c: [400, 590], split: 1 },
  { t: 20.3, a: 28, z: 0.08, c: [390, 240] },
  { t: 40.3, a: 10, z: 0.03, c: [540, 900] },
  { t: CUT_END, a: 22, z: 0.06, c: [540, 800] },
  { t: BALL_T, a: 46, z: 0.24, c: [297, 868], split: 1 },
];
const FLASH = [[0.633, 0.16, 0.9], [CUT_HOOK, 0.1, 0.5], [3.333, 0.18, 0.95], [14.833, 0.1, 0.45], [19.36, 0.12, 0.7], [40.3, 0.14, 0.6], [CUT_END, 0.12, 0.6], [BALL_T, 0.16, 0.9]];
// 每段轻轻往前推，打中时松开
const DRIFT = [[0, 0.633, 1, 1.05], [0.633, CUT_HOOK, 1, 1.03], [CUT_HOOK, 3.333, 1, 1.06], [3.333, 5.334, 1.02, 1.05], [40.3, CUT_END, 1, 1.04], [CUT_END, BALL_T, 1, 1.09]];

const fade = (t, a, b, ia = 0.12, ob = 0.14) => clamp01((t - a) / ia) * (1 - clamp01((t - b) / ob));
const img = new Image(); let cur = -1, track;
async function plate(n) { if (n !== cur) { img.src = `out/plates/${String(n).padStart(5, '0')}.jpg`; await img.decode(); cur = n; } return img; }

function camera(t, n) {
  let z = 1, cx = W / 2, cy = H / 2, dx = 0, dy = 0, r = 0, amp = 0, best = 0, sp = 0;
  for (const [a, b, z0, z1] of DRIFT) if (t >= a && t < b) z *= lerp(z0, z1, (t - a) / (b - a));
  for (const h of HITS) {
    const d = t - h.t; if (d < 0 || d > 1) continue;
    const k = Math.exp(-d * 8), R = rng(4242 + n * 17 + Math.round(h.t * 100)), e = h.a * Math.exp(-d * 6.5);
    dx += (R() - 0.5) * 2 * e; dy += (R() - 0.5) * 2 * e; r += (R() - 0.5) * 0.03 * e / 40; amp = Math.max(amp, e);
    if (h.z * k > best) { best = h.z * k; cx = h.c[0]; cy = h.c[1]; }
    z *= 1 + h.z * k;
    if (h.split && d < 0.28) sp = Math.max(sp, 34 * (1 - d / 0.28) ** 1.5);
  }
  return { z: z * (1 + amp / 450), cx, cy, dx, dy, r, sp };
}
function drawPlate(im, c) {
  ctx.save(); ctx.translate(W / 2 + c.dx, H / 2 + c.dy); ctx.rotate(c.r); ctx.translate(-W / 2, -H / 2);
  ctx.translate(c.cx, c.cy); ctx.scale(c.z, c.z); ctx.translate(-c.cx, -c.cy);
  ctx.drawImage(im, 0, 0, W, H);
  if (c.sp > 0) {
    ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.22 * c.sp / 34;
    ctx.filter = 'sepia(1) hue-rotate(-50deg) saturate(6)'; ctx.drawImage(im, -c.sp, 0, W, H);
    ctx.filter = 'sepia(1) hue-rotate(180deg) saturate(6)'; ctx.drawImage(im, c.sp, 0, W, H);
    ctx.filter = 'none';
  }
  ctx.restore();
}

// ---------- 文字 ----------
function txt(s, x, y, font, fill, o = {}) {
  ctx.font = font; ctx.textAlign = o.align ?? 'center'; ctx.textBaseline = o.base ?? 'alphabetic'; ctx.lineJoin = 'round';
  if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lw ?? 14; ctx.strokeText(s, x, y); }
  ctx.fillStyle = fill; ctx.fillText(s, x, y);
}
function slam(s, x, y, font, fill, t, at, out, o = {}) {
  const d = t - at, ex = o.exit ?? 0.14; if (d < 0 || t > out + ex) return;
  const dur = o.dur ?? 0.11, from = o.from ?? 2.4, q = clamp01((t - out) / ex), e = EASE.enter(clamp01(d / dur));
  let s0 = lerp(from, 1, e); if (d > dur) s0 = 1 + 0.035 * Math.exp(-(d - dur) * 12) * Math.cos((d - dur) * 34);
  s0 *= 1 + q * 0.14; const a = clamp01(d / 0.035) * (1 - q);
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0);
  if (d < dur * 1.4) for (let i = 3; i >= 1; i--) { const ss = lerp(s0, from, i * 0.07); ctx.save(); ctx.scale(ss, ss); ctx.globalAlpha = a * 0.16; txt(s, 0, 0, font, fill, { align: o.align }); ctx.restore(); }
  ctx.scale(s0, s0); ctx.globalAlpha = a;
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.blur ?? 30; }
  txt(s, 0, 0, font, fill, { align: o.align, stroke: o.stroke, lw: o.lw }); ctx.shadowColor = 'transparent'; txt(s, 0, 0, font, fill, { align: o.align });
  ctx.restore();
}
function burst(s, x, y, R, col, t, at, out) {
  const d = t - at, q = clamp01((t - out) / 0.16); if (d < 0 || q >= 1) return;
  const pop = d < 0.1 ? lerp(0.3, 1.25, EASE.enter(d / 0.1)) : lerp(1.25, 1, EASE.enter(clamp01((d - 0.1) / 0.2)));
  ctx.save(); ctx.translate(x + (d < 0.3 ? Math.sin(d * 90) * 5 * (1 - d / 0.3) : 0), y); ctx.rotate(-0.16); ctx.scale(pop * (1 + q * 0.3), pop * (1 + q * 0.3)); ctx.globalAlpha = 1 - q;
  ctx.beginPath(); for (let i = 0; i < 28; i++) { const a = i / 28 * Math.PI * 2, rr = i % 2 ? R * 0.68 : R * (1 + 0.12 * Math.sin(i * 2.3)); ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr * 0.82); } ctx.closePath();
  ctx.fillStyle = '#fff'; ctx.strokeStyle = col; ctx.lineWidth = 9; ctx.lineJoin = 'round'; ctx.shadowColor = 'rgba(0,0,0,0.3)'; ctx.shadowBlur = 20; ctx.fill(); ctx.shadowColor = 'transparent'; ctx.stroke();
  txt(s, 0, 4, `${Math.round(R * 0.7)}px ${TE}`, col, { base: 'middle' }); ctx.restore();
}
function chip(s, x, y, col, t, at, out, size = 46) {
  const a = fade(t, at, out); if (a <= 0) return; const e = EASE.enter(prog(t, at, at + 0.18));
  ctx.save(); ctx.globalAlpha = a; ctx.font = `${size}px ${TE}`; const w = ctx.measureText(s).width + size, h = size * 1.4, k = h * 0.2;
  ctx.translate(x, y); ctx.scale(lerp(0.8, 1, e), lerp(0.8, 1, e));
  ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(-w / 2 + k, -h / 2); ctx.lineTo(w / 2 + k, -h / 2); ctx.lineTo(w / 2 - k, h / 2); ctx.lineTo(-w / 2 - k, h / 2); ctx.closePath(); ctx.fill();
  txt(s, 0, 2, `${size}px ${TE}`, '#fff', { base: 'middle' }); ctx.restore();
}

// ---------- 冲击 ----------
function impact(t, at, x, y, o = {}) {
  const d = t - at; if (d < 0 || d > 0.7) return;
  const col = o.col ?? YEL, line = o.line ?? 'rgba(13,18,38,', k = o.k ?? 1, R = rng(o.seed ?? 777);
  ctx.save(); ctx.translate(x, y);
  const lv = Math.exp(-d * 4.6);
  for (let i = 0; i < 46; i++) {
    const q = R() * 6.283, r0 = (300 + R() * 240 + d * 420) * k, len = 260 + R() * 620, w = 3 + R() * 12;
    ctx.save(); ctx.rotate(q); ctx.fillStyle = `${line}${(0.72 * lv).toFixed(3)})`; ctx.beginPath(); ctx.moveTo(r0, -w * 0.2); ctx.lineTo(r0 + len, -w); ctx.lineTo(r0 + len, w); ctx.lineTo(r0, w * 0.2); ctx.fill(); ctx.restore();
  }
  const u = clamp01(d / 0.24);
  if (u < 1) for (const [c, m] of [[col, 1], ['#fff', 0.62]]) {
    const sz = lerp(130, 310, EASE.enter(u)) * k * m;
    ctx.save(); ctx.rotate(0.3); ctx.globalAlpha = (1 - u) ** 1.2; ctx.fillStyle = c; ctx.beginPath();
    for (let i = 0; i < 24; i++) { const q = i / 24 * 6.283, rr = (i % 2 ? 0.46 : 1 + 0.2 * Math.sin(i * 2.7)) * sz; ctx.lineTo(Math.cos(q) * rr, Math.sin(q) * rr); } ctx.closePath(); ctx.fill(); ctx.restore();
  }
  const v = d / 0.45; if (v < 1) { ctx.save(); ctx.globalAlpha = (1 - v) ** 1.4; ctx.strokeStyle = '#fff'; ctx.lineWidth = 14 * (1 - v) + 1; ctx.beginPath(); ctx.arc(0, 0, lerp(40, 420 * k, EASE.enter(v)), 0, 7); ctx.stroke(); ctx.restore(); }
  const G = rng((o.seed ?? 777) + 132);
  for (let i = 0; i < 34; i++) {
    const q = G() * 6.283, sp = 700 + G() * 1400, sz = 5 + G() * 15, c = i % 3 === 0 ? RED : i % 3 === 1 ? BLUE : col, spin = G() * 12;
    ctx.save(); ctx.translate(Math.cos(q) * sp * d * Math.exp(-d * 1.1), Math.sin(q) * sp * d * Math.exp(-d * 1.1) + 620 * d * d); ctx.rotate(spin * d + q); ctx.globalAlpha = clamp01(1.3 - d * 1.9); ctx.fillStyle = c; ctx.fillRect(-sz, -sz * 0.45, sz * 2, sz * 0.9); ctx.restore();
  }
  ctx.restore();
}

// ---------- 片头 ----------
function drawHook(t) {
  impact(t, 0.633, 648, 929, { seed: 11, col: '#7fc0ff' });
  burst('啪！', 730, 640, 150, BLUE, t, 0.66, 1.25);
  const a = fade(t, 0.72, 2.6, 0.06, 0.1);
  if (a > 0) {
    const e = EASE.enter(prog(t, 0.72, 0.92));
    ctx.save(); ctx.globalAlpha = a; txt('我们上课做的机器人', 480 - (1 - e) * 60, 300, `66px ${TE}`, NAVY); ctx.restore();
  }
  slam('打起来了', 480, 510, `190px ${TE}`, RED, t, 0.8, 2.6, { stroke: '#fff', lw: 18, from: 2, exit: 0.1 });
  impact(t, 3.333, 600, 850, { seed: 23 });
  slam('K.O.', 480, 610, `900 215px ${OR}`, RED, t, 3.36, 4.72, { stroke: '#fff', lw: 16, from: 2.8, rot: -0.05, glow: 'rgba(255,40,40,0.5)', blur: 34, exit: 0.16 });
}

// ---------- 人物介绍 ----------
function banner(t, side, at, out, en, name, tag) {
  const blue = side === 'blue', col = blue ? BLUE : RED, dir = blue ? -1 : 1;
  const e = EASE.enter(clamp01((t - at) / 0.26)), q = EASE.exit(clamp01((t - out) / 0.16)); if (e <= 0 || q >= 1) return;
  const bw = 600, bh = 176, y = 232, off = dir * ((1 - e) + q) * (bw + 40);
  ctx.save(); ctx.translate(off, 0);
  const x0 = blue ? 0 : W, x1 = blue ? bw : W - bw, x2 = blue ? bw - 60 : W - bw + 60;
  ctx.shadowColor = 'rgba(0,0,0,0.32)'; ctx.shadowBlur = 26; ctx.shadowOffsetY = 4;
  ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.lineTo(x2, y + bh); ctx.lineTo(x0, y + bh); ctx.closePath(); ctx.fill();
  ctx.shadowColor = 'transparent'; ctx.shadowOffsetY = 0;
  // 扫光
  const sw = prog(t, at + 0.14, at + 0.5);
  if (sw > 0 && sw < 1) { ctx.save(); ctx.clip(); const X = lerp(x0, x1, sw); ctx.globalAlpha = 0.45 * Math.sin(sw * Math.PI); ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(X - 30, y); ctx.lineTo(X + 40, y); ctx.lineTo(X - 20, y + bh); ctx.lineTo(X - 90, y + bh); ctx.closePath(); ctx.fill(); ctx.restore(); }
  ctx.fillStyle = 'rgba(255,255,255,0.92)'; ctx.fillRect(Math.min(x0, x2), y + bh, bw - 60, 7);
  const tx = blue ? 70 : W - bw + 90;
  txt(en, tx + 2, y + 44, `700 28px ${OR}`, 'rgba(255,255,255,0.85)', { align: 'left' });
  const pop = EASE.enter(prog(t, at + 0.08, at + 0.26));
  ctx.save(); ctx.translate(tx, y + 150); ctx.scale(lerp(1.25, 1, pop), lerp(1.25, 1, pop)); txt(name, 0, 0, `108px ${TE}`, '#fff', { align: 'left' }); ctx.restore();
  const ta = prog(t, at + 0.34, at + 0.56);
  if (ta > 0) {
    ctx.globalAlpha = ta; ctx.font = `44px ${TE}`; const w = ctx.measureText(tag).width + 100;
    ctx.fillStyle = 'rgba(13,18,38,0.78)'; ctx.fillRect(blue ? 0 : W - bw + 60, y + bh + 14, blue ? w : bw, 70);
    txt(tag, tx, y + bh + 64, `44px ${TE}`, '#fff', { align: 'left' }); ctx.globalAlpha = 1;
  }
  ctx.restore();
}
const trackAt = (rows, n) => rows.find(r => r[0] === n);
function trail(t, n, rows, col, wide) {
  const pts = []; for (let i = 7; i >= 0; i--) { const r = trackAt(rows, n - i); if (r && r[1] != null) pts.push([r[1], r[2]]); }
  if (pts.length < 3) return;
  const sp = Math.hypot(pts[pts.length - 1][0] - pts[pts.length - 2][0], pts[pts.length - 1][1] - pts[pts.length - 2][1]);
  const a = clamp01((sp - 24) / 40); if (a <= 0) return;
  // 只画手后面的几条速度线，不压在手上
  const end = pts.length - 2; if (end < 2) return;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 14;
  for (const [off, w] of [[-wide, 7], [-wide * 0.35, 11], [wide * 0.35, 11], [wide, 7]]) {
    ctx.globalAlpha = a * 0.75; ctx.lineWidth = w; ctx.beginPath();
    for (let i = 0; i <= end; i++) {
      const A = pts[Math.max(0, i - 1)], Z = pts[Math.min(pts.length - 1, i + 1)], L = Math.hypot(Z[0] - A[0], Z[1] - A[1]) || 1;
      const X = pts[i][0] - (Z[1] - A[1]) / L * off, Y = pts[i][1] + (Z[0] - A[0]) / L * off;
      i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y);
    }
    ctx.stroke();
  }
  ctx.restore();
}
function reticle(x, y, r, t, at, a, col) {
  const e = EASE.enter(prog(t, at, at + 0.24)), R = lerp(r * 2.6, r, e);
  ctx.save(); ctx.translate(x, y); ctx.rotate((t - at) * 1.2 + (1 - e) * 1.6); ctx.globalAlpha = a; ctx.strokeStyle = '#fff'; ctx.lineWidth = 6; ctx.shadowColor = col; ctx.shadowBlur = 22;
  for (let i = 0; i < 4; i++) { const q = i * Math.PI / 2; ctx.beginPath(); ctx.arc(0, 0, R, q + 0.28, q + Math.PI / 2 - 0.28); ctx.stroke(); }
  ctx.restore();
}
function drawIntro(t, n) {
  const P = track.palm, Fi = track.fist;
  trail(t, n, P, '#58a6ff', 120);
  banner(t, 'blue', 14.87, 17.42, 'BLUE', '掌掌', '舵机驱动 · 抡圆了扇');
  const p = trackAt(P, n);
  if (p && p[1] != null && t > 16.2 && t < 16.68) {
    const a = fade(t, 16.2, 16.56, 0.08, 0.12);
    reticle(p[1], p[2], 170, t, 16.2, a, BLUE);
    chip('大巴掌', Math.min(p[1], 760), Math.max(p[2] + 240, 560), BLUE, t, 16.26, 16.56, 60);
  }
  // 横扫：跟手从右往左压过去
  const sw = EASE.enter(prog(t, 16.8, 17.0));
  if (t >= 16.8 && t < 17.53) {
    const a = 1 - clamp01((t - 17.4) / 0.13);
    ctx.save(); ctx.globalAlpha = a * clamp01((t - 16.8) / 0.04); ctx.translate(lerp(420, 0, sw), 0);
    txt('横扫', 480, 1190, `250px ${TE}`, '#fff', { stroke: BLUE, lw: 20 }); txt('横扫', 480, 1190, `250px ${TE}`, '#fff');
    ctx.restore();
  }
  // 蓝换红的斜切转场
  const wp = prog(t, 17.46, 17.64);
  if (wp > 0 && wp < 1) { const X = lerp(W + 500, -700, wp); ctx.save(); ctx.fillStyle = RED; ctx.beginPath(); ctx.moveTo(X, 0); ctx.lineTo(X + 620, 0); ctx.lineTo(X + 320, H); ctx.lineTo(X - 300, H); ctx.closePath(); ctx.fill(); ctx.restore(); }

  trail(t, n, Fi, '#ff5a4d', 130);
  banner(t, 'red', 18.2, 20.72, 'RED', '拳拳', '电机驱动 · 往复直拳');
  const f = trackAt(Fi, n);
  if (f && f[1] != null && t > 18.42 && t < 18.78) reticle(f[1], f[2], 150, t, 18.42, fade(t, 18.42, 18.66, 0.06, 0.1), RED);
  // 拳 拳 到 肉：一字一砸，和前面“先打一架”同手法
  for (const [ch, x, at, big] of [['拳', 150, 18.76, 0], ['拳', 360, 19.02, 0], ['到', 570, 19.24, 0], ['肉', 785, 19.36, 1]])
    slam(ch, x, 1230 + (big ? 12 : 0), `${big ? 270 : 220}px ${TE}`, big ? RED : '#fff', t, at, 20.1, { stroke: big ? '#fff' : NAVY, lw: 18, from: big ? 2.8 : 2.2, dur: 0.09, rot: big ? -0.06 : 0, glow: 'rgba(0,0,0,0.45)', blur: 24, exit: 0.12 });
  impact(t, 19.36, 400, 590, { seed: 41, k: 0.9, line: 'rgba(255,255,255,' });
}

// ---------- 活动页 ----------
function eventBand(t) {
  const at = 40.32, out = CUT_END; if (t < at || t >= out) return;
  const e = EASE.enter(prog(t, at, at + 0.2)), y = 650, h = 462, sk = 44;
  ctx.save(); ctx.translate((1 - e) * -W, 0);
  ctx.fillStyle = 'rgba(13,18,38,0.88)'; ctx.fillRect(0, y, W, h);
  for (const yy of [y - 10, y + h]) { ctx.fillStyle = RED; ctx.fillRect(0, yy, W / 2 + sk, 10); ctx.fillStyle = BLUE; ctx.fillRect(W / 2 + sk, yy, W / 2 - sk, 10); }
  ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.rect(0, y, W, h); ctx.clip();
  const ka = prog(t, at + 0.1, at + 0.28); ctx.globalAlpha = ka; txt('棋甲对决 · 线下活动', 480, y + 62, `46px ${TE}`, 'rgba(255,255,255,0.82)'); ctx.globalAlpha = 1;
  slam('11.14', 480, y + 244, `900 196px ${OR}`, '#fff', t, 40.46, 46, { from: 2.2, glow: 'rgba(120,170,255,0.55)', exit: 0.01 });
  const be = EASE.enter(prog(t, 41.54, 41.76));
  if (be > 0) { ctx.save(); ctx.globalAlpha = clamp01((t - 41.54) / 0.08); ctx.translate((1 - be) * 60, 0); txt('北京 · 拓竹旗舰店', 480, y + 340, `78px ${TE}`, '#fff'); ctx.restore(); }
  chip('欢迎大家一起来玩', 480, y + 408, RED, t, 43.9, 46, 54);
  ctx.restore();
}
function eventStrip(t) {
  const at = CUT_END; if (t < at) return;
  const e = EASE.enter(prog(t, at, at + 0.2)), y = 232, h = 280;
  ctx.save(); ctx.translate(0, (e - 1) * (y + h + 20));
  ctx.fillStyle = 'rgba(13,18,38,0.86)'; ctx.fillRect(0, y, W, h);
  ctx.fillStyle = RED; ctx.fillRect(0, y + h, W / 2 + 44, 9); ctx.fillStyle = BLUE; ctx.fillRect(W / 2 + 44, y + h, W / 2 - 44, 9);
  txt('11.14', 480, y + 158, `900 142px ${OR}`, '#fff');
  txt('北京 · 拓竹旗舰店', 480, y + 244, `70px ${TE}`, '#fff');
  ctx.restore();
}
// 球的位置（人工取点，相机在动）
const BALL = [[1473, 498, 759], [1484, 376, 735], [1495, 376, 747], [1504, 297, 868]];
function ballAt(n) { for (let i = 1; i < BALL.length; i++) if (n <= BALL[i][0]) { const a = BALL[i - 1], b = BALL[i], u = clamp01((n - a[0]) / (b[0] - a[0])); return [lerp(a[1], b[1], u), lerp(a[2], b[2], u)]; } return BALL[BALL.length - 1].slice(1); }
function drawEvent(t, n) {
  eventBand(t); eventStrip(t);
  const h = BALL_T;
  if (n >= 1473 && n < 1504) { const [x, y] = ballAt(n); reticle(x, y, 118, t, 1473 / 30, 0.95, RED); }
  impact(t, h, 297, 868, { seed: 61, line: 'rgba(255,255,255,' });
  if (t > h) {
    const v = fade(t, h, 60, 0.05, 0.1);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(540, 700); ctx.rotate((t - h) * 0.35);
    for (let i = 0; i < 18; i++) { ctx.rotate(6.283 / 18); const R = rng(100 + i)(), L = lerp(240, 560, R) * EASE.enter(clamp01((t - h) / 0.2)); ctx.fillStyle = `rgba(255,212,0,${(0.12 * v).toFixed(3)})`; ctx.beginPath(); ctx.moveTo(40, -6); ctx.lineTo(L, -26); ctx.lineTo(L, 26); ctx.lineTo(40, 6); ctx.fill(); }
    ctx.restore();
    slam('WIN', 560, 760, `900 200px ${OR}`, YEL, t, h, 60, { from: 2.6, stroke: NAVY, lw: 14, glow: 'rgba(255,212,0,0.7)', blur: 40 });
  }
}

window.__film = {
  fps: FPS,
  async ready() {
    await Promise.all([`40px ${TE}`, `700 40px ${OR}`, `900 40px ${OR}`].map(f => document.fonts.load(f, '棋甲A1')));
    track = await (await fetch('assets/track.json', { cache: 'no-store' })).json();
    return true;
  },
  async render(n) {
    const t = n / FPS, im = await plate(plateOf(n)), c = camera(t, n);
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    drawPlate(im, c);
    if (t < 5.4) drawHook(t);
    else if (t < 21) drawIntro(t, n);
    else drawEvent(t, n);
    for (const [a, d, v] of FLASH) { const u = (t - a) / d; if (u >= 0 && u <= 1) { ctx.fillStyle = `rgba(255,255,255,${(v * (1 - u) ** 1.6).toFixed(3)})`; ctx.fillRect(0, 0, W, H); } }
    return true;
  },
  png() { return cv.toDataURL('image/png'); },
};
document.body.dataset.ready = '1';
