// 实拍段动效（现行 v08，用户已认可）：小火花 / 冲击帧 + 赛璐璐爆炸 + 冲击波折射 + 干净大字。底片是达芬奇导出的无字幕成片（out/plates/全片帧号.jpg），render(n) 是纯函数，n 为全片帧号。
// 完整打击结构（soft 的两下不走这条，只留小火花）：蓄力压暗 → 第 1 帧黑剪影白底 → 第 2 帧反相队色 → 第 3 帧起彩色爆炸、径向模糊、色散逐帧衰减。
// 文字只放在字幕安全区 X 60–900、Y 220–1440 内，不碰字幕行（Y 约 1398）。v06 旧版在 stage_v06旧版.js。
import { EASE, clamp01, lerp, rng, prog } from '../engine/math.js';
import { initGL } from './fx_gl.js';

export const FPS = 30, W = 1080, H = 1920;
const out = document.getElementById('cv'); out.width = W; out.height = H; const octx = out.getContext('2d');
const base = document.createElement('canvas'); base.width = W; base.height = H; const ctx = base.getContext('2d');
const TE = 'Tech', OR = 'Orb', RED = '#ff3a2c', BLUE = '#3d7bff', YEL = '#ffd400', NAVY = '#0d1226';
const CUT_HOOK = 83 / 30, CUT_END = 1373 / 30, BALL_F = 1504;
let gl, track;

// 打中的瞬间定帧（帧号, 多停几帧），后面跳过同样帧数，总长不变，配音不错位
const HOLD = [[19, 2], [100, 2], [581, 3], [BALL_F, 3]];
const plateOf = n => { for (const [f, k] of HOLD) if (n >= f && n < f + k) return f; return n; };

// 大打击：帧号 f、位置、爆炸半径 R、队 team（0 蓝 1 红）、蓄力帧数 pre、方向 dir（镜头被顶开的方向）。soft = 片头两下，用户要求看得清动作：小火花、不进冲击帧、不做全屏模糊
const BIG = [
  { f: 19, x: 648, y: 929, R: 150, team: 0, seed: 3, pre: 3, life: 10, dir: [1, -0.2], soft: 1 },
  { f: 100, x: 600, y: 850, R: 170, team: 1, seed: 5, pre: 3, life: 11, dir: [0.6, 0.5], soft: 1 },
  { f: 581, x: 400, y: 590, R: 430, team: 1, seed: 1, pre: 3, life: 17, dir: [-0.4, -0.7] },
  { f: BALL_F, x: 297, y: 868, R: 520, team: 1, seed: 6, pre: 6, life: 20, dir: [-0.8, 0.5] },
];
// 小打击：只震屏推镜
const HITS = [
  { t: CUT_HOOK, a: 16, z: 0.08, c: [540, 900] }, { t: 3.6, a: 14, z: 0.03, c: [600, 850] }, { t: 3.8, a: 12, z: 0.03, c: [600, 850] },
  { t: 14.833, a: 14, z: 0.06, c: [540, 900] }, { t: 15.33, a: 16, z: 0.03, c: [380, 850] }, { t: 15.83, a: 14, z: 0.03, c: [560, 840] }, { t: 17.13, a: 24, z: 0.06, c: [600, 900] },
  { t: 18.2, a: 18, z: 0.05, c: [600, 600] }, { t: 18.76, a: 22, z: 0.05, c: [400, 480] }, { t: 19.02, a: 22, z: 0.05, c: [300, 520] }, { t: 19.24, a: 16, z: 0.04, c: [420, 560] },
  { t: 20.3, a: 28, z: 0.08, c: [390, 240] }, { t: 40.3, a: 10, z: 0.03, c: [540, 900] }, { t: CUT_END, a: 22, z: 0.06, c: [540, 800] },
];
const SOFT_FLASH = [[CUT_HOOK, 0.1, 0.4], [14.833, 0.1, 0.35], [40.3, 0.14, 0.45], [CUT_END, 0.12, 0.45]];
const DRIFT = [[0, 19 / 30, 1, 1.05], [19 / 30, CUT_HOOK, 1, 1.03], [CUT_HOOK, 100 / 30, 1, 1.06], [100 / 30, 5.334, 1.02, 1.05], [40.3, CUT_END, 1, 1.04], [CUT_END, BALL_F / 30, 1, 1.09]];

const fade = (t, a, b, ia = 0.12, ob = 0.14) => clamp01((t - a) / ia) * (1 - clamp01((t - b) / ob));
const img = new Image(); let cur = -1;
async function plate(n) { if (n !== cur) { img.src = `out/plates/${String(n).padStart(5, '0')}.jpg`; await img.decode(); cur = n; } return img; }

function camera(t, n) {
  let z = 1, cx = W / 2, cy = H / 2, dx = 0, dy = 0, r = 0, amp = 0, best = 0;
  for (const [a, b, z0, z1] of DRIFT) if (t >= a && t < b) z *= lerp(z0, z1, (t - a) / (b - a));
  const shake = (at, a, zz, c, bump) => {
    const d = t - at; if (d < 0 || d > 1) return;
    const k = Math.exp(-d * 8), R = rng(4242 + n * 17 + Math.round(at * 100)), tr = Math.exp(-d * 3.6), e = a * tr * tr;   // 震幅按平方衰减，轻的几乎不动、重的才狠
    dx += (R() - 0.5) * 2 * e + (bump ? bump[0] * 60 * Math.exp(-d * 14) : 0); dy += (R() - 0.5) * 2 * e + (bump ? bump[1] * 60 * Math.exp(-d * 14) : 0);
    r += (R() - 0.5) * 0.03 * e / 40; amp = Math.max(amp, e);
    if (zz * k > best) { best = zz * k; cx = c[0]; cy = c[1]; }
    z *= 1 + zz * k;
  };
  for (const h of HITS) shake(h.t, h.a, h.z, h.c);
  for (const b of BIG) shake(b.f / FPS, b.soft ? 20 : 56, b.soft ? 0.06 : 0.26, [b.x, b.y], b.soft ? null : b.dir);
  return { z: z * (1 + amp / 400 + 0.03 * (Math.abs(dx) + Math.abs(dy) > 40 ? 1 : 0)), cx, cy, dx, dy, r };
}
function drawPlate(im, c) {
  ctx.save(); ctx.translate(W / 2 + c.dx, H / 2 + c.dy); ctx.rotate(c.r); ctx.translate(-W / 2, -H / 2);
  ctx.translate(c.cx, c.cy); ctx.scale(c.z, c.z); ctx.translate(-c.cx, -c.cy);
  ctx.drawImage(im, 0, 0, W, H); ctx.restore();
}

// ---------- 大字：和规则段“先打一架”同一手法（得意黑、Orbitron，砸下 + 残影 + 回弹），浅色底上加一圈细描边保证可读 ----------
function slam(s, x, y, font, fill, t, at, end, o = {}) {
  const d = t - at, ex = o.exit ?? 0.14; if (d < 0 || t > end + ex) return;
  const dur = o.dur ?? 0.11, from = o.from ?? 2.3, q = clamp01((t - end) / ex), e = EASE.enter(clamp01(d / dur));
  let k = lerp(from, 1, e); if (d > dur) k = 1 + 0.035 * Math.exp(-(d - dur) * 12) * Math.cos((d - dur) * 34);
  k *= 1 + q * 0.14; const a = clamp01(d / 0.035) * (1 - q);
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0);
  if (d < dur * 1.4) for (let i = 3; i >= 1; i--) { const ss = lerp(k, from, i * 0.07); ctx.save(); ctx.scale(ss, ss); ctx.globalAlpha = a * 0.16; txt(s, 0, 0, font, fill); ctx.restore(); }
  ctx.scale(k, k); ctx.globalAlpha = a;
  ctx.shadowColor = o.glow ?? 'rgba(0,0,0,0.4)'; ctx.shadowBlur = o.blur ?? 22; ctx.shadowOffsetY = 3;
  txt(s, 0, 0, font, fill, { stroke: o.stroke, lw: o.lw });
  ctx.shadowColor = 'transparent'; ctx.shadowOffsetY = 0; txt(s, 0, 0, font, fill);
  ctx.restore();
}

// ---------- 粒子 ----------
const SPARK = [['#ffffff', '#bfe6ff', '#4aa0ff', '#1a3fb0'], ['#ffffff', '#ffe58a', '#ff8a1f', '#d81f12']];
function sparks(t, at, x, y, n, power, team, seed) {
  const d = t - at; if (d < 0 || d > 0.8) return;
  const R = rng(seed), P = SPARK[team];
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'butt';
  for (let i = 0; i < n; i++) {
    const q = R() * 6.283, sp = power * (0.35 + R() * R() * 1.5), life = 0.22 + R() * 0.5, w0 = 2 + R() * 6, g = 500 + R() * 900; if (d > life) continue;
    const u = d / life, tt = (1 - Math.exp(-d * 5)) / 5, X = x + Math.cos(q) * sp * tt, Y = y + Math.sin(q) * sp * tt + g * d * d;
    const vx = Math.cos(q) * sp * Math.exp(-d * 5), vy = Math.sin(q) * sp * Math.exp(-d * 5) + 2 * g * d, tail = 0.045;
    const c = P[Math.min(3, Math.floor(u * 4))], px = -vy, py = vx, L = Math.hypot(px, py) || 1, wd = w0 * (1 - u * 0.7) / 2;
    ctx.globalAlpha = 1 - u * u; ctx.fillStyle = c; ctx.beginPath(); ctx.moveTo(X + px / L * wd, Y + py / L * wd); ctx.lineTo(X - px / L * wd, Y - py / L * wd); ctx.lineTo(X - vx * tail, Y - vy * tail); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}
function debris(t, at, x, y, n, team, seed) {
  const d = t - at; if (d < 0 || d > 0.9) return; const R = rng(seed), col = team ? '#ff3a2c' : '#3d7bff';
  for (let i = 0; i < n; i++) {
    const q = R() * 6.283, sp = 700 + R() * 1500, sz = 8 + R() * 26, sn = (R() - 0.5) * 18, g = 1200 + R() * 900, a0 = R() * 6, sh = [0.6 + R() * 0.6, 0.5 + R() * 0.5, 0.7 + R() * 0.5];
    const tt = (1 - Math.exp(-d * 3.2)) / 3.2;
    ctx.save(); ctx.translate(x + Math.cos(q) * sp * tt, y + Math.sin(q) * sp * tt + g * d * d); ctx.rotate(a0 + sn * d); ctx.globalAlpha = clamp01(1.5 - d * 1.9);
    ctx.fillStyle = i % 3 === 0 ? col : '#10162c'; ctx.strokeStyle = 'rgba(255,255,255,0.75)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(-sz * sh[0], -sz * 0.3); ctx.lineTo(sz * sh[1], -sz * 0.5); ctx.lineTo(sz * sh[2] * 0.7, sz * 0.5); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
  }
}
// 集中线：一拍两帧换一次，中心留空，线有粗细，避开均匀放射的廉价感
function focusLines(n, f, x, y, ink, clear) {
  const d = n - f; if (d < 0 || d > 6) return;
  const R = rng(5150 + Math.floor((n - f) / 2) * 37 + f); ctx.save(); ctx.translate(x, y); ctx.fillStyle = ink; ctx.globalAlpha = d < 4 ? 1 : (7 - d) / 3;
  for (let i = 0; i < 64; i++) {
    const q = i / 64 * 6.283 + (R() - 0.5) * 0.09, inner = clear * (0.85 + R() * 0.75) * (1 + d * 0.05), w = (R() ** 2) * 62 + 3;
    if (R() < 0.2) continue;
    ctx.save(); ctx.rotate(q); ctx.beginPath(); ctx.moveTo(inner, 0); ctx.lineTo(2400, -w); ctx.lineTo(2400, w); ctx.closePath(); ctx.fill(); ctx.restore();
  }
  ctx.restore();
}

// ---------- 片头 ----------
function drawHook(t, n) {
  slam('啪！', 500, 560, `280px ${TE}`, BLUE, t, 21 / FPS, 1.0, { from: 2.6, rot: -0.1, stroke: '#fff', lw: 10 });
  const k = fade(t, 1.1, 2.6, 0.06, 0.1);
  if (k > 0) { ctx.save(); ctx.globalAlpha = k; txt('我们上课做的机器人', 480, 290, `66px ${TE}`, NAVY); ctx.restore(); }
  slam('打起来了', 480, 500, `190px ${TE}`, RED, t, 1.1, 2.6, { from: 2, exit: 0.1 });
  slam('K.O.', 480, 610, `900 215px ${OR}`, RED, t, 3.38, 4.72, { from: 2.8, rot: -0.05, glow: 'rgba(255,40,40,0.5)', blur: 34, exit: 0.16 });
}

// ---------- 人物介绍 ----------
function txt(s, x, y, font, fill, o = {}) {
  ctx.font = font; ctx.textAlign = o.align ?? 'center'; ctx.textBaseline = o.base ?? 'alphabetic'; ctx.lineJoin = 'round';
  if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lw ?? 14; ctx.strokeText(s, x, y); }
  ctx.fillStyle = fill; ctx.fillText(s, x, y);
}
function chip(s, x, y, col, t, at, end, size = 46) {
  const a = fade(t, at, end); if (a <= 0) return; const e = EASE.enter(prog(t, at, at + 0.18));
  ctx.save(); ctx.globalAlpha = a; ctx.font = `${size}px ${TE}`; const w = ctx.measureText(s).width + size, h = size * 1.4, k = h * 0.2;
  ctx.translate(x, y); ctx.scale(lerp(0.8, 1, e), lerp(0.8, 1, e));
  ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(-w / 2 + k, -h / 2); ctx.lineTo(w / 2 + k, -h / 2); ctx.lineTo(w / 2 - k, h / 2); ctx.lineTo(-w / 2 - k, h / 2); ctx.closePath(); ctx.fill();
  txt(s, 0, 2, `${size}px ${TE}`, '#fff', { base: 'middle' }); ctx.restore();
}
function banner(t, side, at, end, en, name, tag) {
  const blue = side === 'blue', col = blue ? BLUE : RED, dir = blue ? -1 : 1;
  const e = EASE.enter(clamp01((t - at) / 0.26)), q = EASE.exit(clamp01((t - end) / 0.16)); if (e <= 0 || q >= 1) return;
  const bw = 600, bh = 176, y = 232, off = dir * ((1 - e) + q) * (bw + 40);
  ctx.save(); ctx.translate(off, 0);
  const x0 = blue ? 0 : W, x1 = blue ? bw : W - bw, x2 = blue ? bw - 60 : W - bw + 60;
  ctx.shadowColor = 'rgba(0,0,0,0.32)'; ctx.shadowBlur = 26; ctx.shadowOffsetY = 4;
  ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.lineTo(x2, y + bh); ctx.lineTo(x0, y + bh); ctx.closePath(); ctx.fill();
  ctx.shadowColor = 'transparent'; ctx.shadowOffsetY = 0;
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
  let arc = 0; for (let i = 1; i < pts.length; i++) arc += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  const chord = Math.hypot(pts[pts.length - 1][0] - pts[0][0], pts[pts.length - 1][1] - pts[0][1]);
  const a = clamp01((sp - 24) / 40) * clamp01((chord / (arc || 1) - 0.8) / 0.12); if (a <= 0) return;   // 路径打转时不画，否则线会卷成一团
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
    reticle(p[1], p[2], 170, t, 16.2, fade(t, 16.2, 16.56, 0.08, 0.12), BLUE);
    chip('大巴掌', Math.min(p[1], 760), Math.max(p[2] + 240, 560), BLUE, t, 16.26, 16.56, 60);
  }
  // 横扫：跟手从右往左压过去
  if (t >= 16.8 && t < 17.53) {
    const sw = EASE.enter(prog(t, 16.8, 17.0));
    ctx.save(); ctx.globalAlpha = (1 - clamp01((t - 17.4) / 0.13)) * clamp01((t - 16.8) / 0.04); ctx.translate(lerp(420, 0, sw), 0);
    ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 22; txt('横扫', 480, 1190, `250px ${TE}`, '#fff', { stroke: NAVY, lw: 12 }); ctx.shadowColor = 'transparent'; txt('横扫', 480, 1190, `250px ${TE}`, '#fff');
    ctx.restore();
  }
  // 蓝换红的斜切转场
  const wp = prog(t, 17.46, 17.64);
  if (wp > 0 && wp < 1) { const X = lerp(W + 500, -700, wp); ctx.save(); ctx.fillStyle = RED; ctx.beginPath(); ctx.moveTo(X, 0); ctx.lineTo(X + 620, 0); ctx.lineTo(X + 320, H); ctx.lineTo(X - 300, H); ctx.closePath(); ctx.fill(); ctx.restore(); }

  trail(t, n, Fi, '#ff5a4d', 130);
  banner(t, 'red', 18.2, 20.72, 'RED', '拳拳', '电机驱动 · 往复直拳');
  const f = trackAt(Fi, n);
  if (f && f[1] != null && t > 18.42 && t < 18.78) reticle(f[1], f[2], 150, t, 18.42, fade(t, 18.42, 18.66, 0.06, 0.1), RED);
  sparks(t, 18.76, 400, 480, 22, 1300, 1, 71); sparks(t, 19.02, 300, 520, 22, 1300, 1, 72); sparks(t, 19.24, 420, 560, 16, 1100, 1, 73);
  // 拳 拳 到 肉：一字一砸，和前面“先打一架”同手法，最后一字同样用黄色
  for (const [i, ch, x, at] of [[0, '拳', 150, 18.76], [1, '拳', 360, 19.02], [2, '到', 570, 19.24], [3, '肉', 785, 19.36]])
    slam(ch, x, 1230 + (i % 2 ? 26 : 0), `${i === 3 ? 250 : 220}px ${TE}`, i === 3 ? YEL : '#fff', t, at, 20.1, { from: i === 3 ? 2.8 : 2.2, dur: 0.09, rot: i === 3 ? -0.06 : 0, stroke: NAVY, lw: 12, glow: i === 3 ? 'rgba(255,212,0,0.6)' : 'rgba(0,0,0,0.5)', blur: 28, exit: 0.12 });
}

// ---------- 活动页 ----------
function eventBand(t) {
  const at = 40.32; if (t < at || t >= CUT_END) return;
  const e = EASE.enter(prog(t, at, at + 0.2)), y = 650, h = 462, sk = 44;
  ctx.save(); ctx.translate((1 - e) * -W, 0);
  ctx.fillStyle = 'rgba(13,18,38,0.88)'; ctx.fillRect(0, y, W, h);
  for (const yy of [y - 10, y + h]) { ctx.fillStyle = RED; ctx.fillRect(0, yy, W / 2 + sk, 10); ctx.fillStyle = BLUE; ctx.fillRect(W / 2 + sk, yy, W / 2 - sk, 10); }
  ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.rect(0, y, W, h); ctx.clip();
  ctx.globalAlpha = prog(t, at + 0.1, at + 0.28); txt('棋甲对决 · 线下活动', 480, y + 62, `46px ${TE}`, 'rgba(255,255,255,0.82)'); ctx.globalAlpha = 1;
  const d = t - 40.46;
  if (d >= 0) { const s = d < 0.1 ? lerp(2.4, 1, (d / 0.1) ** 2) : 1 - 0.06 * Math.exp(-(d - 0.1) * 20) * Math.cos((d - 0.1) * 40); ctx.save(); ctx.translate(480, y + 244); ctx.scale(s, s); ctx.globalAlpha = clamp01(d / 0.04); ctx.shadowColor = 'rgba(120,170,255,0.6)'; ctx.shadowBlur = 30; txt('11.14', 0, 0, `900 196px ${OR}`, '#fff'); ctx.restore(); }
  const be = EASE.enter(prog(t, 41.54, 41.76));
  if (be > 0) { ctx.save(); ctx.globalAlpha = clamp01((t - 41.54) / 0.08); ctx.translate((1 - be) * 60, 0); txt('北京 · 拓竹旗舰店', 480, y + 340, `78px ${TE}`, '#fff'); ctx.restore(); }
  chip('欢迎大家一起来玩', 480, y + 408, RED, t, 43.9, 46, 54);
  ctx.restore();
  sparks(t, 40.46, 480, y + 180, 40, 1500, 1, 91);
}
function eventStrip(t) {
  if (t < CUT_END) return;
  const e = EASE.enter(prog(t, CUT_END, CUT_END + 0.2)), y = 232, h = 280;
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
  if (n >= 1473 && n < BALL_F) { const [x, y] = ballAt(n); reticle(x, y, 118, t, 1473 / 30, 0.95, RED); }
  slam('WIN', 560, 760, `900 200px ${OR}`, YEL, t, (BALL_F + 2) / FPS, 60, { from: 2.6, stroke: NAVY, lw: 10, glow: 'rgba(255,212,0,0.7)', blur: 40 });
}

window.__film = {
  fps: FPS,
  async ready() {
    await Promise.all([`40px ${TE}`, `700 40px ${OR}`, `900 40px ${OR}`].map(f => document.fonts.load(f, '棋甲A1')));
    track = await (await fetch('assets/track.json', { cache: 'no-store' })).json();
    gl = initGL();
    return true;
  },
  async render(n) {
    const t = n / FPS, im = await plate(plateOf(n)), c = camera(t, n);
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    drawPlate(im, c);
    // 第一道：爆炸画进底片（从第 3 帧起，前两帧留给冲击帧）
    const booms = BIG.filter(b => n >= b.f + 2 && n < b.f + 2 + b.life).map(b => ({ x: b.x + c.dx * 0.6, y: b.y + c.dy * 0.6, R: b.R, age: (n - b.f - 2) / b.life, team: b.team, seed: b.seed }));
    if (booms.length) { gl.fire(base, booms); ctx.drawImage(gl.canvas, 0, 0); }
    for (const b of BIG) {
      const ink = b.team ? '#100408' : '#040820';
      if (!b.soft) focusLines(n, b.f, b.x, b.y, n - b.f < 2 ? ink : '#fff', 300);
      debris(t, b.f / FPS, b.x, b.y, b.soft ? 5 : 22, b.team, b.seed * 31); sparks(t, b.f / FPS, b.x, b.y, b.soft ? 40 : 110, b.soft ? 1300 : 2600, b.team, b.seed * 17);
    }
    if (t < 5.4) drawHook(t, n); else if (t < 21) drawIntro(t, n); else drawEvent(t, n);
    for (const [a, d, v] of SOFT_FLASH) { const u = (t - a) / d; if (u >= 0 && u <= 1) { ctx.fillStyle = `rgba(255,255,255,${(v * (1 - u) ** 1.6).toFixed(3)})`; ctx.fillRect(0, 0, W, H); } }
    // 第二道：整帧后期
    const P = { shock: [], rb: 0, ca: 0, dark: 0, mode: 0 };
    for (const b of BIG) {
      const d = n - b.f;
      if (d < 0 && d >= -b.pre) P.dark = Math.max(P.dark, 0.72 * (1 + d / b.pre) ** 2);                 // 蓄力：边缘压暗往里吸
      if (b.soft) continue;
      if (d < 0 || d > 16) continue;
      P.rc = [b.x, b.y]; P.team = b.team ? [0.95, 0.12, 0.08] : [0.12, 0.34, 1];
      if (d === 0) P.mode = 1; if (d === 1) P.mode = 2;
      if (d >= 2) { P.rb = Math.max(P.rb, 0.17 * Math.exp(-(d - 2) * 0.5)); P.ca = Math.max(P.ca, 20 * Math.exp(-(d - 2) * 0.4)); }
      P.shock.push([b.x, b.y, d * 95, 130 * (1 - d / 17) ** 1.5]);
    }
    gl.post(base, P);
    octx.drawImage(gl.canvas, 0, 0);
    return true;
  },
  png() { return out.toDataURL('image/png'); },
};
document.body.dataset.ready = '1';
