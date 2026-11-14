// 动态大字（画布绘制，逐字可控）。风格：rise 遮罩升起 / slam 放大落定 / track 字距收拢 / fade
// 新增（参考 GSAP SplitText、Motion、Framer Split Reveal）：blur 模糊升起 / hinge 门轴翻起 / scatter 散开汇聚；shine 落定后光泽扫过
// 退场：rise 向上遮罩退出 / blowout 放大消散 / fade。另有 swap 原位换词、highlight 下划线或色块扫过、count 数字滚动。
import { EASE, clamp01, lerp, rng } from './math.js';

export const INK = '#171a2f', PURPLE = '#6554e8', LIME = '#d8f845';
const FAM = { sc: 'FilmSC', latin: 'FilmLatin', tech: 'Tech', orb: 'Orb' };

function lineFont(L) { return `${L.weight || 900} ${L.size}px ${FAM[L.font || 'sc']}`; }

function layoutLines(ctx, lines, x, y, align) {
  let base = y;
  return lines.map((L, li) => {
    if (li > 0) base += L.dy ?? Math.round(L.size * 1.12);
    ctx.font = lineFont(L);
    const tr = (L.tracking ?? (L.font === 'latin' ? 0.02 : 0.01)) * L.size;
    const chars = [...L.text]; let cx = 0;
    const g = chars.map(ch => { const w = ctx.measureText(ch).width; const o = { ch, x: cx, w }; cx += w + tr; return o; });
    const width = cx - tr;
    const x0 = align === 'right' ? x - width : align === 'center' ? x - width / 2 : x;
    return { L, base, x0, width, g, tr };
  });
}

// spec: {at, out, x, y, align, lines:[{text,size,weight,font,color,tracking,dy}], style, stagger, dur,
//        exit, exitDur, swap:{at, lines}, highlight:[{line, from, to, at, mode:'under'|'pill', color}]}
export function drawType(ctx, spec, t) {
  if (t < spec.at - 0.001) return;
  const exitDur = spec.exitDur ?? 0.45;
  if (spec.out !== undefined && t > spec.out + exitDur + 0.5) return;
  const swapT = spec.swap ? spec.swap.at : Infinity;
  drawSet(ctx, spec, spec.lines, t, spec.at, Math.min(spec.out ?? Infinity, swapT), spec.swap ? 'rise' : (spec.exit || 'rise'), spec.swap ? 0.38 : exitDur, spec.style || 'rise');
  if (spec.swap && t >= swapT) drawSet(ctx, spec, spec.swap.lines, t, swapT + 0.06, spec.out ?? Infinity, spec.exit || 'rise', exitDur, 'rise', true);
}

function drawSet(ctx, spec, lines, t, at, out, exit, exitDur, style, fromSwap) {
  const key = fromSwap ? '_lay2' : '_lay';
  if (!spec[key] || lines.some(l => l.count)) spec[key] = layoutLines(ctx, lines.map(l => l.count ? { ...l, text: countText(l, t, at) } : l), spec.x, spec.y, spec.align || 'left');
  const lay = spec[key];
  const stagger = spec.stagger ?? (style === 'slam' ? 0.055 : style === 'scatter' ? 0.025 : style === 'hinge' ? 0.045 : 0.035);
  const dur = spec.dur ?? (style === 'slam' ? 0.7 : style === 'scatter' ? 0.95 : style === 'hinge' ? 0.75 : style === 'blur' ? 0.8 : 0.62);
  const seed0 = (spec.seed ?? 31) * 977 + (fromSwap ? 500 : 0);
  let idx = 0;
  ctx.save();
  ctx.textBaseline = 'alphabetic';
  lay.forEach((ln, li) => {
    const L = ln.L, S = L.size;
    ctx.font = lineFont(L);
    // 高亮（先画在字下面）
    for (const h of spec.highlight || []) if ((h.line ?? 0) === li && !fromSwap === !h.swap && t >= h.at) {
      const a = ln.g[h.from], b = ln.g[Math.min(h.to, ln.g.length - 1)];
      const u = EASE.move(clamp01((t - h.at) / (h.dur ?? 0.5)));
      const q = out < Infinity ? EASE.exit(clamp01((t - out) / exitDur)) : 0;
      ctx.fillStyle = h.color || LIME; ctx.globalAlpha = 1 - q;
      const x0 = ln.x0 + a.x - S * 0.04, x1 = ln.x0 + b.x + b.w + S * 0.04;
      if (h.mode === 'pill') ctx.fillRect(x0, ln.base - S * 0.86, (x1 - x0) * u, S * 1.02);
      else ctx.fillRect(x0, ln.base + S * 0.1, (x1 - x0) * u, Math.max(4, S * 0.1));
      ctx.globalAlpha = 1;
    }
    const clipTop = ln.base - S * 1.02, clipH = S * 1.32;
    ln.g.forEach((c, ci) => {
      const k = idx++;
      const e = EASE.enter(clamp01((t - at - k * stagger) / dur));
      const q = out < Infinity ? (exit === 'blowout' ? EASE.exit : EASE.move)(clamp01((t - out - k * 0.02) / exitDur)) : 0;
      if (e <= 0 || q >= 1) return;
      const cx = ln.x0 + c.x, cw = c.w;
      ctx.save();
      let alpha = 1, dy = 0, sc = 1, blur = 0, dx = 0, rot = 0, sy = 1, skew = 0;
      const RR = rng(seed0 + k), r1 = RR(), r2 = RR(), r3 = RR(); // 每个字独立种子：与出现顺序无关，逐帧确定
      if (style === 'rise') { dy = (1 - e) * S * 1.05; blur = (1 - e) * (1 - e) * 4; }   // 升起时带一点竖向运动模糊
      else if (style === 'blur') { dy = (1 - e) * S * 0.28; sc = lerp(1.08, 1, e); blur = (1 - e) * 11; alpha = Math.min(1, e * 1.6); }
      else if (style === 'hinge') { sy = Math.max(0.02, Math.sin(e * Math.PI / 2)); skew = (1 - e) * -0.5; dy = (1 - e) * S * 0.12; alpha = Math.min(1, e * 2.5); }
      else if (style === 'scatter') { dx = (r1 - 0.5) * S * 1.6 * (1 - e); dy = (r2 - 0.5) * S * 1.8 * (1 - e); rot = (r3 - 0.5) * 0.9 * (1 - e); blur = (1 - e) * 7; alpha = Math.min(1, e * 1.8); sc = lerp(0.7, 1, e); }
      else if (style === 'slam') { sc = lerp(1.32, 1, e); blur = (1 - e) * 14; alpha = e; }
      else if (style === 'track') { alpha = e; }
      else { alpha = e; }
      if (exit === 'rise') { dy -= q * S * 1.25; blur += q * (1 - q) * 6; alpha *= 1 - clamp01((q - 0.75) / 0.25); } // 上移要超过遮罩顶（字形底部约在基线下 0.12 字号），否则最后几帧会留下细条
      else if (exit === 'blur') { dy -= q * S * 0.3; blur += q * 12; alpha *= 1 - q; sc *= lerp(1, 1.06, q); }
      else if (exit === 'blowout') { sc *= lerp(1, 1.7, q); alpha *= 1 - q; blur += q * 16; }
      else alpha *= 1 - q;
      const masked = style === 'rise' || exit === 'rise';
      if (masked) { ctx.beginPath(); ctx.rect(cx - S * 0.2, clipTop, cw + S * 0.4, clipH); ctx.clip(); }
      let px = cx;
      if (style === 'track') px = cx + (ci - (ln.g.length - 1) / 2) * (1 - e) * S * 0.35;
      if (style === 'hinge') { ctx.translate(px + cw / 2 + dx, ln.base + dy); ctx.transform(1, 0, skew, sy, 0, 0); ctx.translate(0, -S * 0.35); ctx.scale(sc, sc); }
      else { ctx.translate(px + cw / 2 + dx, ln.base - S * 0.35 + dy); ctx.rotate(rot); ctx.scale(sc, sc); }
      ctx.globalAlpha = alpha;
      if (blur > 0.3) ctx.filter = `blur(${blur.toFixed(2)}px)`;
      ctx.fillStyle = L.color || INK;
      ctx.fillText(c.ch, -cw / 2, S * 0.35);
      ctx.restore();
    });
    // 光泽扫过：整行落定后，一道斜向高光从左到右扫过（只在字形内）
    const sh = spec.shine && (spec.shine.line ?? 1) === li && !fromSwap ? spec.shine : null;
    if (sh && out === Infinity || sh && t < out) {
      const u = clamp01((t - sh.at) / (sh.dur ?? 0.9));
      if (u > 0 && u < 1) {
        const bx = ln.x0 - S + (ln.width + 2 * S) * EASE.move(u), bw = S * 0.9;
        ctx.save(); ctx.beginPath(); ctx.moveTo(bx - bw / 2 + S * 0.35, ln.base - S); ctx.lineTo(bx + bw / 2 + S * 0.35, ln.base - S); ctx.lineTo(bx + bw / 2 - S * 0.35, ln.base + S * 0.25); ctx.lineTo(bx - bw / 2 - S * 0.35, ln.base + S * 0.25); ctx.closePath(); ctx.clip();
        const g = ctx.createLinearGradient(bx - bw / 2, 0, bx + bw / 2, 0), col = sh.color || ((L.color || INK) === '#fff' ? '216,248,69' : '143,134,232');
        g.addColorStop(0, `rgba(${col},0)`); g.addColorStop(0.5, `rgba(${col},0.95)`); g.addColorStop(1, `rgba(${col},0)`);
        ctx.fillStyle = g; ctx.font = lineFont(L);
        ln.g.forEach(c => ctx.fillText(c.ch, ln.x0 + c.x, ln.base));
        ctx.restore();
      }
    }
  });
  ctx.restore();
}

function countText(L, t, at) {
  const u = EASE.long(clamp01((t - at - (L.count.delay || 0)) / (L.count.dur || 0.9)));
  return (L.count.prefix || '') + Math.round(lerp(L.count.from || 0, L.count.to, u)) + (L.count.suffix || '');
}

// 细线擦出（版式装饰）
export function drawRule(ctx, x0, y, x1, t, at, dur = 0.8, color = 'rgba(23,26,47,0.22)', out, w = 1) {
  if (t < at) return;
  const u = EASE.move(clamp01((t - at) / dur)), q = out !== undefined ? EASE.move(clamp01((t - out) / 0.4)) : 0;
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.beginPath();
  ctx.moveTo(lerp(x0, x1, q), y); ctx.lineTo(lerp(x0, x1, u), y); ctx.stroke(); ctx.restore();
}
