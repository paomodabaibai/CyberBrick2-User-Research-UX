// 动效数学：缓动、样条、随机数。全部纯函数，确定性。
export const W = 1920, H = 1080;

// ---- cubic-bezier 缓动（与 CSS 一致） ----
export function bezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const sx = t => ((ax * t + bx) * t + cx) * t;
  const sy = t => ((ay * t + by) * t + cy) * t;
  const dx = t => (3 * ax * t + 2 * bx) * t + cx;
  return x => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    let t = x;
    for (let i = 0; i < 8; i++) { const e = sx(t) - x, d = dx(t); if (Math.abs(e) < 1e-7) break; if (Math.abs(d) < 1e-6) break; t -= e / d; }
    let lo = 0, hi = 1;
    if (Math.abs(sx(t) - x) > 1e-6) { t = x; for (let i = 0; i < 40; i++) { const v = sx(t); if (v < x) lo = t; else hi = t; t = (lo + hi) / 2; } }
    return sy(t);
  };
}

// 动效 tokens（见 09 文档 §3.1，参数不得随意改）
export const EASE = {
  move:  bezier(0.76, 0.00, 0.24, 1.00),   // 已通过基准：缓起—中段快—缓停
  long:  bezier(0.65, 0.00, 0.35, 1.00),   // >1.6s 长移动
  pull:  bezier(0.55, 0.00, 0.10, 1.00),   // 大幅拉远
  enter: bezier(0.16, 1.00, 0.30, 1.00),   // 元素出现
  exit:  bezier(0.70, 0.00, 0.84, 0.00),   // 元素离场
  accel: bezier(0.45, 0.00, 0.85, 0.45),   // 加速冲入（结束时仍有速度，交给下一段接住）
  dive:  bezier(0.30, 0.10, 0.55, 1.00),   // 点击后立刻起步的推进，末段短促收住（不拖尾，像钟摆转向）
  swing: bezier(0.32, 0.00, 0.20, 1.00),   // 钟摆另一侧：柔和起步、干脆落定，接在 dive 后面
  drift: t => 0.5 - 0.5 * Math.cos(Math.PI * clamp01(t)), // sine-in-out
  linear: t => clamp01(t),
};
export const minJerk = t => { t = clamp01(t); return t * t * t * (10 - 15 * t + 6 * t * t); };

export const clamp01 = x => x < 0 ? 0 : x > 1 ? 1 : x;
export const clamp = (x, a, b) => x < a ? a : x > b ? b : x;
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (a, b, x) => { const t = clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const prog = (t, a, b) => clamp01((t - a) / (b - a));

// ---- 种子随机（每个动作独立种子，可复现） ----
export function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
export const vary = (seed, lo = 0.92, hi = 1.08) => lo + (hi - lo) * rng(seed)();

// ---- 非均匀 Catmull-Rom（centripetal, Barry–Goldman），对任意维向量 ----
export function catmullRom(P0, P1, P2, P3, d01, d12, d23, u) {
  // d* = 段长度（已按度量计算）；alpha=0.5
  const t0 = 0, t1 = t0 + Math.sqrt(Math.max(d01, 1e-6)), t2 = t1 + Math.sqrt(Math.max(d12, 1e-6)), t3 = t2 + Math.sqrt(Math.max(d23, 1e-6));
  const t = t1 + (t2 - t1) * u;
  return P1.map((_, i) => {
    const A1 = (t1 - t) / (t1 - t0) * P0[i] + (t - t0) / (t1 - t0) * P1[i];
    const A2 = (t2 - t) / (t2 - t1) * P1[i] + (t - t1) / (t2 - t1) * P2[i];
    const A3 = (t3 - t) / (t3 - t2) * P2[i] + (t - t2) / (t3 - t2) * P3[i];
    const B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2;
    const B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3;
    return (t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2;
  });
}
