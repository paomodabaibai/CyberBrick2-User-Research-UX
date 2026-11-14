// 规则段动效（时间线 20.90 起，t = 0）。贴着实拍追踪数据画：光轨、名牌、球的透镜都跟真实机器人走，实拍是一场真实对局。
// ?mode=alpha 只出叠层（透明，放视频 2 轨）；?mode=preview 带实拍和示意字幕，给审片用。render(t) 是纯函数。
import { EASE, clamp01, clamp, lerp, rng, prog } from '../engine/math.js';
import { mountGlass } from './glass_v.js';

export const FPS = 30, W = 1080, H = 1920;
const MODE = new URLSearchParams(location.search).get('mode') || 'preview';
const cv = document.getElementById('cv'); cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');
const TE = 'Tech', OR = 'Orb';
const RED = '#ff3a2c', BLUE = '#3d7bff', YEL = '#ffd400';
const S0 = W / 1920, BAND_Y = (H - 1080 * S0) / 2;   // 横拍按宽度放入竖屏
const sx = x => x * S0, sy = y => y * S0 + BAND_Y;

// 卡点（秒，相对 20.90）。06 配音从 0 开始，07 配音从 4.50 开始（字级时间见 assets/vo_words.json）
const B = { rule: 0, red: 1.02, tong: 1.34, chu: 1.62, shui: 2.24, da: 2.40, ziji: 2.72, qiu: 3.30, ying: 3.88, ban: 4.90, zhuang: 5.20, xian: 5.90, hit: 6.08, yi: 6.28, jia: 6.42, end: 7.0 };
const RAMP0 = 5.82, SRC0 = 3094, SRC_HIT = 3153;   // 接管实拍：V22 源帧，巴掌扇中约在第 3153 帧
const FOCUS = [1040, 600];

let track, glass, band, bctx;
const imgs = new Map();
async function load(url) {
  if (imgs.has(url)) return imgs.get(url);
  const im = new Image(); im.src = url; await im.decode();
  if (imgs.size > 8) imgs.delete(imgs.keys().next().value);
  imgs.set(url, im); return im;
}
const pad5 = n => String(n).padStart(5, '0');

// 场地 → 帧像素
const H3 = (fr, X, Y) => { const h = fr.H, w = h[6] * X + h[7] * Y + h[8]; return [(h[0] * X + h[1] * Y + h[2]) / w, (h[3] * X + h[4] * Y + h[5]) / w]; };
const floor = (fr, X, Y) => { const [x, y] = H3(fr, X, Y); return [sx(x), sy(y)]; };
const pxPerCm = (fr, X, Y) => { const a = floor(fr, X, Y), b = floor(fr, X + 5, Y); return Math.hypot(a[0] - b[0], a[1] - b[1]) / 5; };

function gaussPath(c) {
  // 10 倍速下脚底点会抖，光轨按约 0.2 秒平滑，避免把抖动画成闪电
  const n = track.frames.length, r = 15, sig = 6, w = [];
  for (let i = -r; i <= r; i++) w.push(Math.exp(-i * i / (2 * sig * sig)));
  const out = [];
  for (let i = 0; i < n; i++) {
    let X = 0, Y = 0, S = 0;
    for (let j = -r; j <= r; j++) { const f = track.frames[clamp(i + j, 0, n - 1)][c].field, g = w[j + r]; X += f[0] * g; Y += f[1] * g; S += g; }
    out.push([X / S, Y / S]);
  }
  return out;
}
let PATH;

const fade = (t, a, b, ia = 0.2, ob = 0.2) => clamp01((t - a) / ia) * (1 - clamp01((t - b) / ob));

// ---------- 文字 ----------
function glowText(text, x, y, font, fill, align = 'center') {
  ctx.font = font; ctx.textAlign = align; ctx.textBaseline = 'alphabetic'; ctx.fillStyle = fill;
  ctx.fillText(text, x, y);
}
// 砸下：从大到小，带几层运动残影；落定后极小的回弹
function slam(text, x, y, font, fill, t, at, out, o = {}) {
  const d = t - at; if (d < 0 || t > out + (o.exit ?? 0.14)) return;
  const dur = o.dur ?? 0.13, from = o.from ?? 2.3, q = clamp01((t - out) / (o.exit ?? 0.14));
  const e = EASE.enter(clamp01(d / dur));
  let s = lerp(from, 1, e);
  if (d > dur) s = 1 + 0.035 * Math.exp(-(d - dur) * 12) * Math.cos((d - dur) * 34);
  s *= 1 + q * 0.14;
  const a = clamp01(d / 0.035) * (1 - q);
  ctx.save(); ctx.translate(x + (o.dx ? o.dx * (1 - e) : 0), y); ctx.rotate(o.rot || 0);
  if (d < dur * 1.4) for (let i = 3; i >= 1; i--) {
    const ss = lerp(s, from, i * 0.07); ctx.save(); ctx.scale(ss, ss); ctx.globalAlpha = a * 0.16; glowText(text, 0, 0, font, fill, o.align); ctx.restore();
  }
  ctx.scale(s, s); ctx.globalAlpha = a;
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.blur ?? 34; }
  glowText(text, 0, 0, font, fill, o.align);
  ctx.restore();
}
// 从一侧飞入（同时 ← → 出发）
function fly(text, x, y, font, fill, t, at, out, dir, o = {}) {
  const d = t - at; if (d < 0 || t > out + 0.14) return;
  const e = EASE.enter(clamp01(d / 0.2)), q = EASE.exit(clamp01((t - out) / 0.14));
  ctx.save(); ctx.globalAlpha = clamp01(d / 0.05) * (1 - q);
  const off = dir * ((1 - e) * 620 + q * 80);
  if (d < 0.14) for (let i = 3; i >= 1; i--) { ctx.save(); ctx.globalAlpha *= 0.14; glowText(text, x + off + dir * i * 46, y, font, fill, o.align); ctx.restore(); }
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = 30; }
  glowText(text, x + off, y, font, fill, o.align); ctx.restore();
}

// ---------- 场地扫描 ----------
function drawScan(t, fr) {
  const u = prog(t, 0.0, 0.8); if (u <= 0) return;
  const a = fade(t, 0, 1.25, 0.05, 0.35); if (a <= 0) return;
  const wave = EASE.long(u) * 110 - 10;   // 波前（场地 Y，远 → 近）
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
  const line = (P, Q, br) => { ctx.strokeStyle = `rgba(190,225,255,${(br * a).toFixed(3)})`; ctx.beginPath(); ctx.moveTo(...P); ctx.lineTo(...Q); ctx.stroke(); };
  ctx.lineWidth = 1.6;
  for (let X = 0; X <= 120; X += 10) {
    const y1 = Math.min(80, Math.max(0, wave)); if (y1 <= 0) continue;
    line(floor(fr, X, Math.max(0, y1 - 26)), floor(fr, X, y1), 0.5);
  }
  for (let Y = 0; Y <= 80; Y += 10) {
    const dd = wave - Y; if (dd < 0) continue;
    line(floor(fr, 0, Y), floor(fr, 120, Y), 0.75 * Math.exp(-dd / 16));
  }
  // 波前亮带
  if (wave > 0 && wave < 80) {
    const P = floor(fr, 0, wave), Q = floor(fr, 120, wave);
    ctx.shadowColor = '#bfe2ff'; ctx.shadowBlur = 30; ctx.lineWidth = 5; ctx.strokeStyle = `rgba(255,255,255,${(0.95 * a).toFixed(3)})`;
    ctx.beginPath(); ctx.moveTo(...P); ctx.lineTo(...Q); ctx.stroke();
  }
  ctx.restore();
}
// 四角卡尺（跟随实拍）
function drawBrackets(t, fr) {
  const a = fade(t, 0.1, RAMP0 - 0.1, 0.25, 0.1); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a * 0.9; ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.lineCap = 'square';
  const L = 7 * EASE.enter(prog(t, 0.1, 0.45));
  for (const [X, Y, dx, dy] of [[0, 0, 1, 1], [120, 0, -1, 1], [120, 80, -1, -1], [0, 80, 1, -1]]) {
    const P = floor(fr, X, Y), A = floor(fr, X + dx * L, Y), C = floor(fr, X, Y + dy * L);
    ctx.beginPath(); ctx.moveTo(...A); ctx.lineTo(...P); ctx.lineTo(...C); ctx.stroke();
  }
  ctx.restore();
}

// ---------- 真实走位光轨 ----------
function drawTrails(t, fr, k) {
  const k0 = Math.round(B.red * FPS) - 8; if (k < k0) return;
  const a = fade(t, B.red - 0.1, RAMP0 + 0.05, 0.1, 0.12); if (a <= 0) return;
  const dim = t > 2.2 && t < 4.5 ? 0.6 : 1;
  for (const [c, col] of [['red', RED], ['blue', BLUE]]) {
    const P = PATH[c === 'red' ? 0 : 1];
    const pts = []; for (let i = 0; i <= k; i++) pts.push(floor(fr, P[i][0], P[i][1]));
    const scale = pxPerCm(fr, P[k][0], P[k][1]);
    ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.globalAlpha = a * dim;
    ctx.globalCompositeOperation = 'lighter';
    ctx.shadowColor = col; ctx.shadowBlur = 28; ctx.strokeStyle = col; ctx.lineWidth = scale * 1.7;
    ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.stroke();
    ctx.shadowBlur = 0; ctx.strokeStyle = 'rgba(255,255,255,0.9)'; ctx.lineWidth = Math.max(2, scale * 0.42); ctx.stroke();
    // 流动光点
    const n = pts.length; for (let i = (k * 3) % 9; i < n; i += 9) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(pts[i][0], pts[i][1], 2.2 + 2 * (i / n), 0, 7); ctx.fill(); }
    // 头部
    const h = pts[n - 1]; ctx.shadowColor = col; ctx.shadowBlur = 36; ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(h[0], h[1], scale * 1.9, scale * 1.1, 0, 0, 7); ctx.fill();
    ctx.restore();
  }
}
// 起点地圈：出发那一下炸开
function drawPads(t, fr) {
  for (const [c, col, X, Y] of [['red', RED, 11, 72], ['blue', BLUE, 104, 14.5]]) {
    for (const off of [0, 0.14]) {
      const u = prog(t, B.red + off, B.red + off + 0.7); if (u <= 0 || u >= 1) continue;
      const r = lerp(6, 26, EASE.enter(u));
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = (1 - u) ** 1.4; ctx.strokeStyle = col; ctx.lineWidth = 7 * (1 - u) + 1.5; ctx.shadowColor = col; ctx.shadowBlur = 24;
      ctx.beginPath(); for (let i = 0; i <= 48; i++) { const q = i / 48 * Math.PI * 2, p = floor(fr, X + Math.cos(q) * r, Y + Math.sin(q) * r); i ? ctx.lineTo(...p) : ctx.moveTo(...p); } ctx.closePath(); ctx.stroke();
      ctx.restore();
    }
  }
}
// 名牌：挂在机器人头顶，跟着走
function tagPos(fr, k, c) {
  const p = PATH[c === 'red' ? 0 : 1][k], f = floor(fr, p[0], p[1]), s = pxPerCm(fr, p[0], p[1]);
  return [f[0], f[1] - s * 25];
}
function drawTags(t, fr, k) {
  const a = fade(t, B.red + 0.06, RAMP0 - 0.05, 0.16, 0.08); if (a <= 0) return;
  const R = tagPos(fr, k, 'red'), Bl = tagPos(fr, k, 'blue');
  const close = clamp01(1 - (Math.hypot(R[0] - Bl[0], R[1] - Bl[1]) - 90) / 90);   // 靠近时各往外让
  const side = R[0] < Bl[0] ? -1 : 1;
  for (const [[x, y], name, col, dir] of [[R, '拳拳', RED, side], [Bl, '掌掌', BLUE, -side]]) {
    const X = x + dir * close * 50, e = EASE.enter(prog(t, B.red + 0.06, B.red + 0.3));
    ctx.save(); ctx.globalAlpha = a; ctx.translate(X, y - (1 - e) * 26);
    ctx.font = `38px ${TE}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const w = ctx.measureText(name).width + 34;
    ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(-w / 2 + 8, -24); ctx.lineTo(w / 2 + 8, -24); ctx.lineTo(w / 2 - 8, 24); ctx.lineTo(-w / 2 - 8, 24); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-9, 24); ctx.lineTo(9, 24); ctx.lineTo(0, 37); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.fillText(name, 0, 3);
    ctx.restore();
  }
}

// ---------- 球：准星 + 透镜 + 目标弧线 ----------
const ballScr = (fr, c) => { const b = fr[`ball_${c}`]; return [sx(b[0]), sy(b[1])]; };
function drawBallLock(t, fr, k) {
  const T0 = { red: B.da, blue: B.da + 0.08 };
  for (const [c, col] of [['red', RED], ['blue', BLUE]]) {
    const a = fade(t, T0[c], 4.42, 0.1, 0.16); if (a <= 0) continue;
    const [x, y] = ballScr(fr, c), e = EASE.enter(prog(t, T0[c], T0[c] + 0.28));
    const r = lerp(190, lensR(t, c) + 22, e), rot = (t - T0[c]) * 1.1 + (1 - e) * 1.6;
    // 四段准星
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.globalAlpha = a; ctx.strokeStyle = '#fff'; ctx.lineWidth = 4; ctx.shadowColor = col; ctx.shadowBlur = 20;
    for (let i = 0; i < 4; i++) { const q = i * Math.PI / 2; ctx.beginPath(); ctx.arc(0, 0, r, q + 0.28, q + Math.PI / 2 - 0.28); ctx.stroke(); }
    ctx.restore();
    // 赢：一圈冲击
    const v = prog(t, B.ying, B.ying + 0.5);
    if (v > 0 && v < 1) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = (1 - v) ** 1.5; ctx.strokeStyle = YEL; ctx.lineWidth = 10 * (1 - v) + 1; ctx.shadowColor = YEL; ctx.shadowBlur = 30; ctx.beginPath(); ctx.arc(x, y, lerp(lensR(t, c), 240, EASE.enter(v)), 0, 7); ctx.stroke(); ctx.restore(); }
    // 目标弧线：机器人 → 自己颜色的球
    const p = PATH[c === 'red' ? 0 : 1][k], f = floor(fr, p[0], p[1]), hd = [f[0], f[1] - pxPerCm(fr, p[0], p[1]) * 10];
    const dx = x - hd[0], dy = y - hd[1], L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L, bend = Math.min(150, L * 0.32) * (dx > 0 ? -1 : 1);
    const cp = [(x + hd[0]) / 2 + nx * bend, (y + hd[1]) / 2 + ny * bend];
    const dr = EASE.enter(prog(t, T0[c], T0[c] + 0.42));
    const stop = 1 - (lensR(t, c) + 22) / Math.max(L, 1);
    ctx.save(); ctx.globalAlpha = a; ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = col; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.shadowColor = col; ctx.shadowBlur = 18;
    ctx.setLineDash([18, 16]); ctx.lineDashOffset = -t * 170;
    ctx.beginPath(); const steps = 40; for (let i = 0; i <= steps * dr * stop; i++) { const u = i / steps, X = (1 - u) ** 2 * hd[0] + 2 * u * (1 - u) * cp[0] + u * u * x, Y = (1 - u) ** 2 * hd[1] + 2 * u * (1 - u) * cp[1] + u * u * y; i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); } ctx.stroke();
    ctx.restore();
  }
}
const LENS_T = { red: B.ziji, blue: B.ziji + 0.12 };
function lensR(t, c) {
  const d = t - LENS_T[c]; if (d < 0) return 0;
  const R = c === 'red' ? 70 : 60;
  const pop = d < 0.3 ? lerp(0, 1, EASE.enter(d / 0.3)) * (1 + 0.14 * Math.sin(clamp01(d / 0.3) * Math.PI)) : 1;
  const beat = 1 + 0.12 * Math.exp(-Math.max(0, t - B.ying) * 7) * (t > B.ying ? 1 : 0);
  const out = 1 - EASE.exit(prog(t, 4.3, 4.5));
  return R * pop * beat * out;
}

// ---------- 顶部对战条：两边往中间顶，距离来自实拍 ----------
const gapOf = k => { const a = PATH[0][k], b = PATH[1][k]; return Math.max(0, Math.hypot(a[0] - b[0], a[1] - b[1]) - 13); };
function drawHUD(t, k) {
  const e = t - 0.06; if (e < 0) return;
  const q = EASE.exit(prog(t, B.hit - 0.02, B.hit + 0.12));
  const inE = EASE.enter(clamp01(e / 0.3));
  const gap0 = 78;
  const closeU = EASE.long(prog(t, 4.5, B.hit));
  const gap = lerp(gap0, 4, closeU);
  const y = 158, h = 118, sk = 34;
  ctx.save(); ctx.textBaseline = 'alphabetic';
  for (const [side, col, name, en] of [[-1, RED, '拳拳', 'RED'], [1, BLUE, '掌掌', 'BLUE']]) {
    const off = side * ((1 - inE) * 640 + q * 700);
    ctx.save(); ctx.translate(540 + off, 0);
    const a = side * gap, b = side * 540;
    ctx.beginPath(); ctx.moveTo(a + (side > 0 ? sk : 0), y); ctx.lineTo(b, y); ctx.lineTo(b, y + h - 30); ctx.lineTo(a + side * 120 + (side > 0 ? 0 : 0), y + h - 30); ctx.lineTo(a + (side > 0 ? 0 : -sk) + side * 96, y + h); ctx.lineTo(a + (side > 0 ? 0 : -sk), y + h); ctx.closePath();
    const g = ctx.createLinearGradient(a, 0, b, 0); g.addColorStop(0, col); g.addColorStop(1, col + 'cc'); ctx.fillStyle = g; ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.92)'; ctx.fillRect(Math.min(a + side * 150, b), y + h - 22, Math.abs(b - (a + side * 150)), 6);
    const tx = side * 500, al = side < 0 ? 'left' : 'right';
    glowText(name, tx, y + 76, `86px ${TE}`, '#fff', al);
    ctx.globalAlpha = 0.85; glowText(en, side * 300 + side * 0, y + 72, `700 30px ${OR}`, '#fff', al);
    ctx.restore();
  }
  // 中心 VS：贴近时被挤掉
  const vs = (1 - closeU) * inE * (1 - q);
  if (vs > 0.01) {
    const v = t - 0.2; const sc = v < 0 ? 0 : (v < 0.14 ? lerp(2.4, 1, EASE.enter(v / 0.14)) : 1) * lerp(0.4, 1, 1 - closeU);
    ctx.save(); ctx.translate(540, y + h / 2 + 2); ctx.scale(sc, sc); ctx.rotate(-0.02); ctx.globalAlpha = clamp01(v / 0.04) * vs; ctx.shadowColor = YEL; ctx.shadowBlur = 26;
    ctx.textBaseline = 'middle'; glowText('VS', 0, 0, `900 74px ${OR}`, YEL); ctx.restore();
  }
  ctx.restore();
}

// ---------- 上方大字 ----------
function drawKicker(t, k) {
  // 规则
  slam('规则', 540, 568, `200px ${TE}`, '#fff', t, 0.08, 0.92, { from: 2.1, glow: 'rgba(255,255,255,0.35)' });
  // 同时 ← → 出发
  fly('同时', 530, 566, `176px ${TE}`, '#ff5a4d', t, B.tong - 0.1, 2.12, -1, { align: 'right', glow: RED });
  fly('出发', 550, 566, `176px ${TE}`, '#6b9bff', t, B.chu - 0.1, 2.12, 1, { align: 'left', glow: BLUE });
  // 打掉 / 自己颜色的球
  slam('打掉', 540, 438, `118px ${TE}`, '#fff', t, B.da, 3.6, { from: 1.9 });
  if (t >= B.ziji - 0.02 && t <= 3.74) {
    const d = t - B.ziji + 0.02, e = EASE.enter(clamp01(d / 0.2)), q = EASE.exit(prog(t, 3.6, 3.74));
    ctx.save(); ctx.globalAlpha = clamp01(d / 0.05) * (1 - q); ctx.font = `128px ${TE}`; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    const s = '自己颜色的球', w = ctx.measureText(s).width;
    const g = ctx.createLinearGradient(540 - w / 2, 0, 540 + w / 2, 0); g.addColorStop(0, '#ff5a4d'); g.addColorStop(0.62, '#7aa6ff'); g.addColorStop(0.63, '#fff'); g.addColorStop(1, '#fff');
    ctx.fillStyle = g; ctx.translate(540, 590); ctx.scale(lerp(1.2, 1, e), lerp(1.2, 1, e)); ctx.fillText(s, 0, 0); ctx.restore();
  }
  // WIN
  const win = t - B.ying;
  if (win >= -0.02 && t < 4.45) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; const v = fade(t, B.ying, 4.32, 0.05, 0.12);
    ctx.translate(540, 500); ctx.rotate((t - B.ying) * 0.35);
    for (let i = 0; i < 18; i++) { ctx.rotate(Math.PI * 2 / 18); const R = rng(100 + i)(), L = lerp(240, 560, R) * EASE.enter(clamp01((win + 0.02) / 0.2)); ctx.fillStyle = `rgba(255,212,0,${(0.12 * v).toFixed(3)})`; ctx.beginPath(); ctx.moveTo(40, -6); ctx.lineTo(L, -26); ctx.lineTo(L, 26); ctx.lineTo(40, 6); ctx.fill(); }
    ctx.restore();
    slam('WIN', 540, 590, `900 250px ${OR}`, YEL, t, B.ying, 4.3, { from: 2.6, glow: 'rgba(255,212,0,0.7)', blur: 46 });
  }
  // 半路撞上 + 实时距离
  fly('半路撞上', 70, 450, `108px ${TE}`, '#fff', t, B.ban - 0.04, 5.7, -1, { align: 'left' });
  const da = fade(t, 4.5, 5.72, 0.14, 0.1);
  if (da > 0) {
    const n = Math.round(gapOf(k)), pulse = t > B.zhuang ? 1 + 0.08 * Math.exp(-(t - B.zhuang) * 9) : 1;
    ctx.save(); ctx.globalAlpha = da; ctx.textBaseline = 'alphabetic'; ctx.translate(1010, 610); ctx.scale(pulse, pulse);
    ctx.shadowColor = YEL; ctx.shadowBlur = 24; glowText(String(n), -92, 0, `900 176px ${OR}`, YEL, 'right');
    ctx.shadowBlur = 0; glowText('CM', 0, 0, `700 58px ${OR}`, '#fff', 'right');
    ctx.restore();
    ctx.save(); ctx.globalAlpha = da * 0.9; ctx.textBaseline = 'alphabetic'; glowText('两台机器人的距离', 70, 610, `46px ${TE}`, 'rgba(255,255,255,0.86)', 'left'); ctx.restore();
  }
}
// 下方：一句话对照
function drawPairs(t) {
  const a = fade(t, B.ziji + 0.12, 4.36, 0.2, 0.14); if (a <= 0) return;
  const y = 1420;
  for (const [x, side, col, text, at] of [[272, -1, RED, '红方打红球', B.ziji + 0.12], [808, 1, BLUE, '蓝方打蓝球', B.ziji + 0.24]]) {
    const e = EASE.enter(prog(t, at, at + 0.26));
    ctx.save(); ctx.globalAlpha = a * clamp01((t - at) / 0.08); ctx.translate(x + side * (1 - e) * 70, y);
    ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(-222, -46); ctx.lineTo(236, -46); ctx.lineTo(222, 46); ctx.lineTo(-236, 46); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; glowText(text, 0, 4, `70px ${TE}`, '#fff');
    ctx.restore();
  }
}
// 实拍说明：诚实标注加速
function drawTag(t) {
  const a = fade(t, 0.25, RAMP0 - 0.05, 0.25, 0.1); if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a * 0.88; ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = RED; ctx.beginPath(); ctx.arc(34, 1303, 8 * (0.7 + 0.3 * Math.sin(t * 9)), 0, 7); ctx.fill();
  glowText('REAL MATCH  ×10', 54, 1314, `700 30px ${OR}`, '#fff', 'left'); ctx.restore();
}

// ---------- 撞击：接管实拍 ----------
function srcAt(t) {
  if (t < B.hit) { const u = prog(t, RAMP0, B.hit); return lerp(SRC0, SRC_HIT, 1 - (1 - u) ** 2); }
  if (t < B.hit + 0.1) return SRC_HIT;
  return SRC_HIT + (t - B.hit - 0.1) * FPS * 1.1;
}
function camHit(t) {
  const FULL = H / 1080;
  let s;
  if (t < B.hit) s = lerp(S0, FULL * 1.14, prog(t, RAMP0, B.hit) ** 2.2);
  else { const d = t - B.hit; s = FULL * (1.04 + 0.1 * Math.exp(-d * 11) + d * 0.075); }
  const u = EASE.drift(prog(t, RAMP0, B.hit));
  const fx = lerp(960, FOCUS[0], u), fy = lerp(540, FOCUS[1], u);
  const scrY = lerp(H / 2, 1120, u);
  let ox = W / 2 - fx * s, oy = scrY - fy * s;
  if (t >= B.hit) { ox = Math.min(0, Math.max(W - 1920 * s, ox)); oy = Math.min(0, Math.max(H - 1080 * s, oy)); }
  return { s, ox, oy };
}
async function drawHit(t) {
  if (t < RAMP0 || t >= B.end) return;
  const n = clamp(Math.round(srcAt(t)), 3090, 3209);
  const im = await load(`assets/slow/${pad5(n)}.jpg`);
  const { s, ox, oy } = camHit(t);
  const d = t - B.hit, f = Math.floor(d * FPS), R = rng(4242 + f * 17);
  const amp = d > 0 ? 42 * Math.exp(-d * 6.5) : 0;
  const dx = (R() - 0.5) * 2 * amp, dy = (R() - 0.5) * 2 * amp, rr = (R() - 0.5) * 0.045 * Math.exp(-Math.max(d, 0) * 7) * (d > 0 ? 1 : 0);
  const out = clamp01((t - 6.88) / 0.12);
  ctx.save(); ctx.globalAlpha = 1 - out;
  ctx.translate(W / 2 + dx, H / 2 + dy); ctx.rotate(rr); ctx.translate(-W / 2, -H / 2);
  ctx.drawImage(im, ox, oy, 1920 * s, 1080 * s);
  // 打中的几帧：红蓝通道错位
  if (d > 0 && d < 0.3) {
    const sp = 34 * (1 - d / 0.3) ** 1.5;
    ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.26 * (1 - d / 0.3);
    ctx.filter = 'sepia(1) hue-rotate(-50deg) saturate(6)'; ctx.drawImage(im, ox - sp, oy, 1920 * s, 1080 * s);
    ctx.filter = 'sepia(1) hue-rotate(180deg) saturate(6)'; ctx.drawImage(im, ox + sp, oy, 1920 * s, 1080 * s);
    ctx.filter = 'none';
  }
  ctx.restore();
  const cx = FOCUS[0] * s + ox + dx, cy = FOCUS[1] * s + oy + dy;
  drawImpact(t, cx, cy);
  if (d > 0 && d < 0.14) { ctx.fillStyle = `rgba(255,255,255,${(0.92 * (1 - d / 0.14) ** 1.6).toFixed(3)})`; ctx.fillRect(0, 0, W, H); }
  if (out > 0) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = `rgba(255,255,255,${(0.75 * Math.sin(out * Math.PI)).toFixed(3)})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
}
function drawImpact(t, cx, cy) {
  const d = t - B.hit; if (d < 0 || d > 0.75) return;
  const R = rng(777);
  // 放射速度线（只在外围，不挡机器人）
  ctx.save(); ctx.translate(cx, cy);
  const lv = Math.exp(-d * 4.2);
  for (let i = 0; i < 46; i++) {
    const q = R() * Math.PI * 2, r0 = 330 + R() * 240 + d * 420, len = 260 + R() * 620, w = 3 + R() * 12;
    ctx.save(); ctx.rotate(q); ctx.fillStyle = `rgba(255,255,255,${(0.75 * lv).toFixed(3)})`; ctx.beginPath(); ctx.moveTo(r0, -w * 0.2); ctx.lineTo(r0 + len, -w); ctx.lineTo(r0 + len, w); ctx.lineTo(r0, w * 0.2); ctx.fill(); ctx.restore();
  }
  // 冲击星：黄白两层，只在前 0.28 秒
  const u = clamp01(d / 0.28);
  if (u < 1) {
    const sz = lerp(150, 330, EASE.enter(u)), a = (1 - u) ** 1.2;
    for (const [col, k] of [[YEL, 1], ['#fff', 0.62]]) {
      ctx.save(); ctx.rotate(0.3); ctx.globalAlpha = a; ctx.fillStyle = col; ctx.beginPath();
      for (let i = 0; i < 24; i++) { const q = i / 24 * Math.PI * 2, rr = (i % 2 ? 0.46 : 1 + 0.2 * Math.sin(i * 2.7)) * sz * k; ctx.lineTo(Math.cos(q) * rr, Math.sin(q) * rr); }
      ctx.closePath(); ctx.fill(); ctx.restore();
    }
  }
  // 碎屑
  const G = rng(909);
  for (let i = 0; i < 40; i++) {
    const q = G() * Math.PI * 2, v = 700 + G() * 1500, sz = 5 + G() * 16, col = i % 3 === 0 ? RED : i % 3 === 1 ? BLUE : YEL, spin = G() * 12;
    const X = Math.cos(q) * v * d * Math.exp(-d * 1.1), Y = Math.sin(q) * v * d * Math.exp(-d * 1.1) + 620 * d * d;
    ctx.save(); ctx.translate(X, Y); ctx.rotate(spin * d + q); ctx.globalAlpha = clamp01(1.3 - d * 1.8); ctx.fillStyle = col; ctx.fillRect(-sz, -sz * 0.45, sz * 2, sz * 0.9); ctx.restore();
  }
  ctx.restore();
}
function drawBrawlText(t) {
  // 先 打 一 架：一字一砸，压在机器人上方
  const y = 500, S = `250px ${TE}`;
  const XS = [168, 408, 672, 912];
  for (const [i, ch, at] of [[0, '先', B.xian], [1, '打', B.hit], [2, '一', B.yi], [3, '架', B.jia]]) {
    slam(ch, XS[i], y + (i % 2 ? 26 : 0), S, i === 3 ? YEL : '#fff', t, at, 6.86, { from: i === 1 ? 2.8 : 2.2, dur: 0.09, rot: i === 3 ? -0.06 : 0, glow: i === 3 ? 'rgba(255,212,0,0.75)' : 'rgba(0,0,0,0.55)', blur: 30, exit: 0.12 });
  }
}
// 审片用：示意字幕（实际字幕在达芬奇字幕轨）
const SUBS = [[0, 4.23, '规则很简单，红蓝同时出发，谁先打掉自己颜色的球，谁就赢'], [4.5, 6.7, '如果半路撞上，也可以先打一架']];
function drawPreviewSub(t) {
  const s = SUBS.find(x => t >= x[0] && t < x[1]); if (!s) return;
  ctx.save(); ctx.font = '700 44px FilmSC'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#fff'; ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 8;
  const t1 = s[2]; if (ctx.measureText(t1).width > 960) { const m = t1.indexOf('，', 12) + 1; ctx.fillText(t1.slice(0, m), 540, 1660); ctx.fillText(t1.slice(m), 540, 1722); } else ctx.fillText(t1, 540, 1700);
  ctx.restore();
}

window.__film = {
  fps: FPS, duration: B.end,
  async ready() {
    await Promise.all([`40px ${TE}`, `700 40px ${OR}`, `900 40px ${OR}`, '700 40px FilmSC'].map(f => document.fonts.load(f, '棋甲A1')));
    track = await (await fetch('assets/track.json', { cache: 'no-store' })).json();
    PATH = [gaussPath('red'), gaussPath('blue')];
    band = document.createElement('canvas'); band.width = W; band.height = H; bctx = band.getContext('2d');
    glass = mountGlass(band);
    return true;
  },
  async render(t) {
    const k = clamp(Math.round(t * FPS), 0, track.frames.length - 1), fr = track.frames[k];
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H);
    const im = await load(`assets/frames/${pad5(k)}.jpg`);
    if (MODE === 'preview') { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.drawImage(im, 0, BAND_Y, W, 1080 * S0); }
    const live = t < RAMP0 + 0.02;
    if (live) {
      drawScan(t, fr); drawBrackets(t, fr); drawPads(t, fr); drawTrails(t, fr, k);
      // 透镜：折射实拍（含光轨以下的原始画面）
      const lr = lensR(t, 'red'), lb = lensR(t, 'blue');
      if (lr > 1 || lb > 1) {
        bctx.clearRect(0, 0, W, H); bctx.fillStyle = '#000'; bctx.fillRect(0, 0, W, H); bctx.drawImage(im, 0, BAND_Y, W, 1080 * S0);
        const [rx, ry] = ballScr(fr, 'red'), [bx, by] = ballScr(fr, 'blue');
        const g = glass([{ x: rx, y: ry, r: lr, hue: 0, mag: 1.9 }, { x: bx, y: by, r: lb, hue: 1, mag: 2.1 }], t);
        if (g) ctx.drawImage(g, 0, 0);
      }
      drawBallLock(t, fr, k); drawTags(t, fr, k); drawTag(t); drawPairs(t);
    }
    await drawHit(t);
    drawHUD(t, k); drawKicker(t, k); drawBrawlText(t);
    if (MODE === 'preview') drawPreviewSub(t);
    return true;
  },
  png() { return cv.toDataURL('image/png'); },
};
document.body.dataset.ready = '1';
