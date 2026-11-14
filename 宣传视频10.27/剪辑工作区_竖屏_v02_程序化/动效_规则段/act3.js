// 第三幕（t ≥ 7，相对时间线 20.90）：操纵简单 → DIY 拆模块 → 自己设计 + 3D 打印 → 绿色机器人。
// 手柄按 CyberBrick Official Standard Remote（MakerWorld 1395991）的造型重建：长圆外壳、两个环形摇杆座、中间翻盖、顶部黑色按键带；颜色取实拍的紫色外壳。
// “攻击杆在顶部”是按官方造型和通道表推定的。设计稿里的 8 种模块都是概念示意，不是做出来的模块。render 只由 t 决定。
import * as THREE from 'three';
import { EASE, clamp01, lerp, prog, rng } from '../engine/math.js';
import { toCreasedNormals } from './vendor/BufferGeometryUtils.js';

const GREEN = 0x16c463, DARK = 0x1a1d24, CYAN = 0x6fd8ff;
export const A3 = { start: 7.0, pad: 6.97, walk: [7.25, 7.95], atk: [7.95, 8.2], yi: 8.19, shou: 8.93, diy: 10.24, shen: 11.0, wu: 11.58, kai: 12.44, you: 13.5, she: 14.1, geng: 14.58, gong: 15.14, print: 16.08, printEnd: 17.18, fly: 17.18, snap: 17.5, ji: 18.3, end: 19.4 };

let S = {}, pad, sticks = [], stageG, designs = [], hammerSolid, hammerGlow, supports, bedG, rail, carriage, tip, ring, sparks, filament, uLayer = { value: 0 };
const mat = (c, o = {}) => new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.42, clearcoat: 0.35, clearcoatRoughness: 0.45, side: THREE.DoubleSide, ...o });
const shadow = o => { o.castShadow = o.receiveShadow = true; return o; };
const box = (w, h, d, m, x = 0, y = 0, z = 0) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); return shadow(o); };
const cyl = (r0, r1, h, m, x = 0, y = 0, z = 0, seg = 32) => { const o = new THREE.Mesh(new THREE.CylinderGeometry(r0, r1, h, seg), m); o.position.set(x, y, z); return shadow(o); };
const cylZ = (r, h, m, x, y, z, seg = 48) => { const o = cyl(r, r, h, m, x, y, z, seg); o.rotation.x = Math.PI / 2; return o; };
const cylX = (r, h, m, x, y, z, seg = 32) => { const o = cyl(r, r, h, m, x, y, z, seg); o.rotation.z = Math.PI / 2; return o; };

function rounded(w, h, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r); s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h); s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r); s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
  return s;
}
const slab = (w, h, depth, r, m, bevel = 0.2) => shadow(new THREE.Mesh(new THREE.ExtrudeGeometry(rounded(w, h, r), { depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 4, curveSegments: 16 }), m));

// ---------- CyberBrick 官方标准遥控器 ----------
function buildPad() {
  const g = new THREE.Group();
  const shell = mat(0x5238e6, { roughness: 0.3, iridescence: 1, iridescenceIOR: 1.6, iridescenceThicknessRange: [180, 420], clearcoat: 0.7 }), rim = mat(0x6b52f2, { roughness: 0.34 }), black = mat(0x15171d, { roughness: 0.55 });
  const body = slab(26, 11.4, 3.6, 5, shell, 0.55); body.position.z = -4.1; g.add(body);
  const face = slab(23.6, 9.2, 0.25, 3.8, rim, 0.08); face.position.z = 0; g.add(face);
  const strip = slab(19.5, 1.9, 2.4, 0.8, black, 0.1); strip.position.set(0, 5.75, -2.6); g.add(strip);
  const lid = slab(5.4, 5, 0.5, 1.1, rim, 0.16); lid.position.set(0, 2.3, 0.28); g.add(lid);
  g.add(box(2, 0.24, 0.3, black, 0, -0.1, 0.42));
  for (const x of [-7.9, 7.9]) {
    const torus = shadow(new THREE.Mesh(new THREE.TorusGeometry(2.55, 0.3, 14, 48), rim)); torus.position.set(x, -0.85, 0.32); g.add(torus);
    g.add(cylZ(2.42, 0.08, mat(0x2a1d90), x, -0.85, 0.27));
    for (const a of [0.8, 2.4, 3.9, 5.5]) g.add(box(0.5, 0.5, 0.26, rim, x + Math.cos(a) * 2.75, -0.85 + Math.sin(a) * 2.75, 0.34));
    const piv = new THREE.Group(); piv.position.set(x, -0.85, 0.3); g.add(piv);
    const ball = shadow(new THREE.Mesh(new THREE.SphereGeometry(1.25, 28, 18), rim)); ball.scale.z = 0.7; piv.add(ball);
    piv.add(cylZ(0.28, 1.9, black, 0, 0, 1.3, 16), cylZ(0.62, 0.55, mat(0xe9eaf0), 0, 0, 2.35, 24));
    sticks.push(piv);
  }
  // 顶部按键带：两根拨杆（攻击在左）、中间滑块、圆按钮（K4）
  const lev = new THREE.Group(); lev.position.set(-8.6, 6.6, -1.4); g.add(lev);
  lev.add(box(0.75, 1.5, 0.75, black, 0, 0.75, 0)); sticks.push(lev);
  g.add(box(0.75, 1.5, 0.75, black, 8.6, 7.35, -1.4));
  const sw = slab(3, 0.9, 0.5, 0.25, rim, 0.05); sw.position.set(0, 6.85, -1.9); g.add(sw);
  const k4 = new THREE.Group(); k4.position.set(-4.6, 6.9, -1.4); k4.add(cyl(0.72, 0.72, 0.6, rim, 0, 0, 0)); g.add(k4); sticks.push(k4);
  return g;
}

// ---------- 攻击模块（共用接口 + 8 种武器），单位 cm ----------
function arm(m, len = 8) {
  const s = rounded(len, 2.1, 0.7);
  for (let i = 0; i < Math.floor(len / 2); i++) { const h = new THREE.Path(); h.absarc(-len / 2 + 1.2 + i * 2, 0, 0.42, 0, Math.PI * 2, true); s.holes.push(h); }
  const o = shadow(new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.8, bevelEnabled: true, bevelThickness: 0.1, bevelSize: 0.1, bevelSegments: 2, curveSegments: 14 }), m));
  o.rotation.x = -Math.PI / 2; o.position.set(len / 2 + 0.8, 3.15, 0); return o;
}
function mountBase(g, m, dark, steel) {
  const plate = slab(9, 9, 0.6, 1.2, m, 0.14); plate.rotation.x = -Math.PI / 2; plate.position.y = 0.05; g.add(plate);
  for (const [x, z] of [[-3.5, -3.5], [3.5, -3.5], [3.5, 3.5], [-3.5, 3.5]]) g.add(cyl(0.34, 0.34, 0.2, steel, x, 0.85, z, 12));
  const pts = [[0, 0], [2.7, 0], [2.7, 0.4], [2.3, 0.6], [2.3, 1.8], [1.5, 2.2], [1.1, 2.7], [1.1, 3.2], [0, 3.2]].map(p => new THREE.Vector2(p[0], p[1]));
  const col = shadow(new THREE.Mesh(new THREE.LatheGeometry(pts, 40), dark)); col.position.y = 0.75; g.add(col);
}
function weapon(kind, m = mat(0x7fdcff), dark = mat(0x24272f), steel = mat(0xc9ced8, { metalness: 0.65, roughness: 0.3 })) {
  const g = new THREE.Group(), add = (...a) => a.forEach(o => g.add(o));
  mountBase(g, m, dark, steel);
  const baseCount = g.children.length, Y = 3.55;
  if (kind === 'hammer') {
    add(arm(m, 9.2));
    const pts = [[0, -5.4], [2.6, -5.4], [3, -5.1], [3, -4.6], [3.6, -4.3], [3.6, -3.3], [3.9, -3.1], [3.9, -2.2], [3.5, -2], [3.5, 2], [3.9, 2.2], [3.9, 3.1], [3.6, 3.3], [3.6, 4.3], [3, 4.6], [3, 5.1], [2.6, 5.4], [0, 5.4]].map(p => new THREE.Vector2(p[0], p[1]));
    const head = shadow(new THREE.Mesh(new THREE.LatheGeometry(pts, 56), m)); head.rotation.x = Math.PI / 2; head.position.set(13.2, Y, 0); add(head);
    add(cylZ(3.92, 0.5, dark, 13.2, Y, 2.65), cylZ(3.92, 0.5, dark, 13.2, Y, -2.65), cylZ(2.5, 0.12, steel, 13.2, Y, 5.42), cylZ(2.5, 0.12, steel, 13.2, Y, -5.42));
    for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2; for (const z of [3.8, -3.8]) { const b = shadow(new THREE.Mesh(new THREE.SphereGeometry(0.2, 10, 8), steel)); b.position.set(13.2 + Math.cos(a) * 3.6, Y + Math.sin(a) * 3.6, z); add(b); } }
    add(cylX(1.15, 2, dark, 9.4, Y, 0), cylX(0.85, 2.6, steel, 9.9, Y, 0));
    add(box(2.2, 0.5, 2.6, dark, 13.2, Y + 3.45, 0), box(2.2, 0.5, 2.6, dark, 13.2, Y - 3.45, 0));
  } else if (kind === 'drill') {
    add(arm(m, 5.4), cylX(1.6, 2.2, dark, 7.4, Y, 0));
    const pts = []; for (let i = 0; i <= 12; i++) pts.push(new THREE.Vector2(i === 12 ? 0.02 : 3.3 * (1 - i / 12), i * 0.85));
    const cone = shadow(new THREE.Mesh(new THREE.LatheGeometry(pts, 24), steel)); cone.rotation.z = -Math.PI / 2; cone.position.set(8.5, Y, 0); add(cone);
    for (let i = 0; i < 5; i++) { const t = shadow(new THREE.Mesh(new THREE.TorusGeometry(3.05 - i * 0.58, 0.14, 6, 36), m)); t.rotation.y = Math.PI / 2 + 0.2; t.position.set(9.3 + i * 1.5, Y, 0); add(t); }
  } else if (kind === 'saw') {
    add(arm(m, 7.4));
    const s = new THREE.Shape(), N = 18; for (let i = 0; i < N * 2; i++) { const r = i % 2 ? 4.3 : 5.5, a = i / (N * 2) * Math.PI * 2; i ? s.lineTo(Math.cos(a) * r, Math.sin(a) * r) : s.moveTo(Math.cos(a) * r, Math.sin(a) * r); } s.closePath();
    const blade = shadow(new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.2, bevelEnabled: false }), steel)); blade.rotation.x = -Math.PI / 2; blade.position.set(12, Y + 0.2, 0); add(blade);
    add(cyl(1.4, 1.4, 0.9, dark, 12, Y + 0.2, 0, 20));
  } else if (kind === 'claw') {
    add(arm(m, 5), box(3.4, 2.4, 3.4, dark, 6.9, Y, 0));
    for (const s of [1, -1]) {
      add(box(5.5, 1, 1, m, 10.2, Y, s * 2.3)); const seg = box(4, 1, 1, m, 14.2, Y, s * 1.3); seg.rotation.y = s * 0.55; add(seg);
      const t = box(1.5, 1.1, 1, steel, 15.9, Y, s * 0.35); t.rotation.y = s * 0.3; add(t);
    }
  } else if (kind === 'mace') {
    add(arm(m, 7.5), cylX(0.7, 1.5, steel, 9, Y, 0));
    const ball = shadow(new THREE.Mesh(new THREE.IcosahedronGeometry(3.2, 2), dark)); ball.position.set(12.8, Y, 0); add(ball);
    const ico = new THREE.IcosahedronGeometry(3.2, 0).attributes.position, seen = new Set();
    for (let i = 0; i < ico.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(ico, i), k = v.toArray().map(x => x.toFixed(2)).join(); if (seen.has(k)) continue; seen.add(k); const spike = cyl(0.04, 0.8, 2.1, steel, 0, 0, 0, 10); spike.position.copy(v.clone().multiplyScalar(1.22)).add(ball.position); spike.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.clone().normalize()); add(spike); }
  } else if (kind === 'spring') {
    add(arm(m, 3.4));
    for (let i = 0; i < 9; i++) { const c = shadow(new THREE.Mesh(new THREE.TorusGeometry(1.45, 0.2, 8, 28), steel)); c.rotation.y = Math.PI / 2 + 0.16; c.position.set(5.6 + i * 0.75, Y, 0); add(c); }
    const glove = shadow(new THREE.Mesh(new THREE.SphereGeometry(3.3, 28, 20), m)); glove.scale.set(1.15, 0.95, 1); glove.position.set(14.8, Y, 0); add(glove);
    const th = shadow(new THREE.Mesh(new THREE.SphereGeometry(1.2, 14, 12), m)); th.position.set(13.7, Y + 0.3, 3.1); add(th);
  } else if (kind === 'axe') {
    add(arm(m, 8));
    const s = new THREE.Shape(); s.moveTo(0, -1.3); s.lineTo(0, 1.3); s.quadraticCurveTo(2.5, 2, 4.8, 5.4); s.quadraticCurveTo(7, 0, 4.8, -5.4); s.quadraticCurveTo(2.5, -2, 0, -1.3);
    const bl = shadow(new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth: 0.5, bevelEnabled: true, bevelThickness: 0.2, bevelSize: 0.12, bevelSegments: 2, curveSegments: 16 }), steel)); bl.position.set(9.4, Y, -0.3); add(bl);
    add(box(2.2, 3.2, 1.8, dark, 9.6, Y, 0));
  } else if (kind === 'cannon') {
    add(arm(m, 3.8), box(4.2, 3.6, 4.2, dark, 5.8, Y, 0));
    const pts = [[1.9, 0], [1.9, 4], [1.45, 4.3], [1.45, 8], [2, 8.3], [2, 9.4], [1.1, 9.4], [1.1, 0]].map(p => new THREE.Vector2(p[0], p[1]));
    const bar = shadow(new THREE.Mesh(new THREE.LatheGeometry(pts, 36), m)); bar.rotation.z = -Math.PI / 2; bar.position.set(7.7, Y, 0); add(bar);
    for (const x of [10, 11.2, 12.4]) add(cylX(1.72, 0.3, steel, x, Y, 0));
  }
  // 底盘和接口固定，其余（转轴以上）装进 rotor，只有 rotor 转
  const rotor = new THREE.Group(); rotor.name = 'rotor';
  [...g.children].slice(baseCount).forEach(o => rotor.add(o)); g.add(rotor); g.userData.rotor = rotor;
  g.traverse(o => { if (o.isMesh) o.geometry = toCreasedNormals(o.geometry, 0.6); });
  return g;
}
const DESIGN_ORDER = [['drill', '钻头'], ['saw', '圆锯'], ['claw', '夹爪'], ['mace', '流星锤'], ['spring', '弹簧拳'], ['axe', '战斧'], ['cannon', '小炮'], ['hammer', '大锤']];
const DESIGN_T = [13.66, 13.98, 14.26, 14.5, 14.7, 14.87, 15.0, 15.1];
export const designNow = t => { if (t < DESIGN_T[0] || t >= A3.print) return null; let i = 0; while (i < 7 && t >= DESIGN_T[i + 1]) i++; return { i, name: DESIGN_ORDER[i][1], n: i + 1, age: t - DESIGN_T[i] }; };

function wire(src) {
  const g = new THREE.Group(), fill = new THREE.MeshBasicMaterial({ color: CYAN, transparent: true, opacity: 0.17, depthWrite: false, side: THREE.DoubleSide, toneMapped: false, blending: THREE.AdditiveBlending }), line = new THREE.LineBasicMaterial({ color: 0xc8f2ff, transparent: true, opacity: 0.9, toneMapped: false });
  src.updateMatrixWorld(true);
  src.traverse(o => { if (o.isMesh) {
    const part = new THREE.Group(); o.matrixWorld.decompose(part.position, part.quaternion, part.scale);
    part.add(new THREE.Mesh(o.geometry, fill), new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 28), line));
    g.add(part);
  } });
  return g;
}

const layerHook = sh => {
  sh.uniforms.uLayer = uLayer;
  sh.vertexShader = 'varying float vWY;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vWY = (modelMatrix * vec4(transformed, 1.0)).y;');
  sh.fragmentShader = 'varying float vWY; uniform float uLayer;\n' + sh.fragmentShader.replace('#include <color_fragment>', '#include <color_fragment>\n diffuseColor.rgb *= 1.0 - uLayer * 0.2 * step(0.5, fract(vWY * 3.6));');
};

export function setupAct3(scene, camera, renderer, bots) {
  S = { scene, camera, renderer, bots };
  renderer.localClippingEnabled = true;
  scene.add(camera);
  stageG = new THREE.Group(); stageG.visible = false; stageG.userData.act3 = true; scene.add(stageG);
  const disc = new THREE.Mesh(new THREE.CircleGeometry(92, 96), new THREE.MeshStandardMaterial({ color: 0x0e1420, roughness: 0.55, metalness: 0.3 })); disc.rotation.x = -Math.PI / 2; disc.receiveShadow = true; stageG.add(disc);
  const grid = new THREE.GridHelper(184, 46, 0x2c4a6e, 0x182b44); grid.position.y = 0.03; grid.material.transparent = true; grid.material.opacity = 0.55; stageG.add(grid);
  ring = new THREE.Mesh(new THREE.RingGeometry(46, 46.6, 96), new THREE.MeshBasicMaterial({ color: 0x8f7bff, transparent: true, opacity: 0.9, toneMapped: false, side: THREE.DoubleSide })); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.05; stageG.add(ring);
  pad = buildPad(); pad.visible = false; camera.add(pad);
  for (const [k] of DESIGN_ORDER) { const w = wire(weapon(k)); w.visible = false; stageG.add(w); designs.push(w); }

  // 打印件：绿色大锤（带层纹）+ 支撑 + 正在凝固的那一层
  const planeTop = new THREE.Plane(new THREE.Vector3(0, -1, 0), 0), planeLow = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  hammerSolid = weapon('hammer', mat(GREEN, { roughness: 0.46 }), mat(DARK, { roughness: 0.5 }), mat(0xd4d8df, { metalness: 0.6, roughness: 0.32 })); hammerSolid.visible = false;
  supports = new THREE.Group(); hammerSolid.add(supports);
  const supM = mat(0x9fe9c0, { roughness: 0.7 });
  for (let x = 6.5; x <= 16.5; x += 1.25) for (const z of [-3.6, -1.2, 1.2, 3.6]) { const hTop = x > 9.5 ? 3.55 - Math.sqrt(Math.max(0.1, 13.7 - (x - 13.2) ** 2)) : 3.0; if (hTop > 0.1) supports.add(box(0.18, hTop, 0.18, supM, x, hTop / 2, z)); }
  hammerSolid.traverse(o => { if (o.isMesh) { o.material = o.material.clone(); o.material.onBeforeCompile = layerHook; o.material.clippingPlanes = [planeTop]; } });
  stageG.add(hammerSolid); hammerSolid.userData.plane = planeTop;
  hammerSolid.updateMatrixWorld(true);
  hammerGlow = new THREE.Group(); hammerSolid.traverse(o => { if (o.isMesh) { const c = new THREE.Mesh(o.geometry, new THREE.MeshBasicMaterial({ color: 0xffc27a, side: THREE.DoubleSide, toneMapped: false, clippingPlanes: [planeTop, planeLow] })); o.matrixWorld.decompose(c.position, c.quaternion, c.scale); hammerGlow.add(c); } });
  hammerGlow.visible = false; stageG.add(hammerGlow); hammerGlow.userData.low = planeLow;

  // 打印机：底座、热床、龙门、喷头
  bedG = new THREE.Group(); bedG.visible = false; stageG.add(bedG);
  const fr = mat(0x2a2e38, { metalness: 0.5, roughness: 0.45 }), al = mat(0x8a909b, { metalness: 0.75, roughness: 0.3 }), line = mat(0x46506a);
  bedG.add(box(46, 1.2, 40, mat(0x14171e, { metalness: 0.3 }), 0, 0.6, 0), box(38, 0.3, 34, mat(0x2b2f3a, { roughness: 0.28, metalness: 0.65 }), 0, 1.35, 0));
  for (let i = -3; i <= 3; i++) bedG.add(box(38, 0.02, 0.06, line, 0, 1.51, i * 4.8), box(0.06, 0.02, 34, line, i * 5.4, 1.51, 0));
  rail = new THREE.Group(); bedG.add(rail);
  rail.add(box(44, 1.1, 1.1, al, 0, 0, -0.9), box(44, 1.1, 1.1, al, 0, 0, 0.9));
  carriage = new THREE.Group(); rail.add(carriage);
  carriage.add(box(4.6, 5, 4.2, mat(0xe8e9ee, { roughness: 0.4 }), 0, 0.8, 0), box(4.8, 0.5, 4.4, mat(GREEN), 0, -1.5, 0), cylZ(1.6, 0.25, mat(0x23262e), 0, 0.9, 2.2, 24));
  for (let i = 0; i < 6; i++) { const b = box(0.28, 1.3, 0.08, al, 0, 0.9, 2.35); b.rotation.z = i * Math.PI / 3; carriage.add(b); }
  carriage.add(box(2.2, 1.3, 2.2, mat(0x7a7f88, { metalness: 0.7 }), 0, -2.3, 0), cyl(0.75, 0.14, 1.3, mat(0xd8a84a, { metalness: 0.85, roughness: 0.25 }), 0, -3.6, 0, 20));
  tip = new THREE.Mesh(new THREE.SphereGeometry(0.34, 12, 10), new THREE.MeshBasicMaterial({ color: 0xffb040, toneMapped: false })); tip.position.y = -4.25; carriage.add(tip);
  filament = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.9, 8), new THREE.MeshBasicMaterial({ color: 0xffe0a0, toneMapped: false })); filament.position.y = -4.7; carriage.add(filament);
  sparks = new THREE.Group(); stageG.add(sparks);
  for (let i = 0; i < 44; i++) sparks.add(new THREE.Mesh(new THREE.SphereGeometry(0.28, 8, 6), new THREE.MeshBasicMaterial({ color: i % 3 ? GREEN : 0xffffff, toneMapped: false })));
}

const sph = (tg, d, az, el) => { const a = az * Math.PI / 180, e = el * Math.PI / 180; return [tg[0] + d * Math.cos(e) * Math.sin(a), tg[1] + d * Math.sin(e), tg[2] + d * Math.cos(e) * Math.cos(a)]; };
const mv = (a, b, u) => ({ tg: a.tg.map((v, i) => lerp(v, b.tg[i], u)), d: Math.exp(lerp(Math.log(a.d), Math.log(b.d), u)), az: lerp(a.az, b.az, u), el: lerp(a.el, b.el, u), f: lerp(a.f, b.f, u) });
function cam3(t) {
  const c0 = { tg: [0, 0.5, 0], d: 128, az: -6, el: 8, f: 38 };
  const c1 = { tg: [0, 7, 0], d: 150, az: 16, el: 15, f: 38 };
  const c2 = { tg: [0, 12, 0], d: 150, az: -14, el: 13, f: 38 };
  const c3 = { tg: [4, 8, 0], d: 92, az: 24, el: 15, f: 38 };
  const c4a = { tg: [4, 4, 0], d: 84, az: -30, el: 22, f: 38 };   // 打印：先看全貌
  const c4b = { tg: [8, 6.5, 0], d: 70, az: 12, el: 14, f: 38 };    // 推到喷头跟前
  const c5 = { tg: [4, 11, 0], d: 92, az: 22, el: 7, f: 38 };
  const c6 = { tg: [5, 11, 0], d: 80, az: -16, el: 5, f: 38 };
  let s = c0;
  s = mv(s, c1, EASE.long(prog(t, 9.3, 10.4)));
  s = mv(s, c2, EASE.long(prog(t, 10.8, 12.5)));
  s = mv(s, c3, EASE.move(prog(t, 13.2, 14.0)));
  s = mv(s, c4a, EASE.move(prog(t, 15.62, 16.08)));
  s = mv(s, c4b, EASE.long(prog(t, 16.08, A3.printEnd)));
  s = mv(s, c5, EASE.move(prog(t, 17.14, 17.45)));
  s = mv(s, c6, EASE.drift(prog(t, 17.6, 19.4)));
  s.az += 0.8 * Math.sin(t * 0.7); s.el += 0.3 * Math.sin(t * 0.53 + 1);
  return s;
}

function place(side, x, z, face, o = {}) {
  const b = S.bots[side];
  b.root.visible = o.visible ?? true;
  b.root.position.set(x, o.y ?? 0, z);
  const base = side === 'red' ? -Math.PI / 2 : Math.PI;
  b.root.rotation.y = base + face;
  const ph = o.phase ?? 0, w = o.walk ?? 0, sw = Math.sin(ph);
  b.body.rotation.set(0, 0, 0); b.body.position.y = Math.abs(sw) * 0.5 * w;
  if (side === 'red') b.body.rotation.x = 0.1 * sw * w; else b.body.rotation.z = 0.1 * sw * w;
  const hip = (o.hip ?? 0.32) * sw * w;
  b.groups.legA.rotation.z = hip; b.groups.legB.rotation.z = -hip;
  b.groups.legA.position.z = Math.max(0, sw) * 1.4 * w / 1.2; b.groups.legB.position.z = Math.max(0, -sw) * 1.4 * w / 1.2;
  b.groups.mod.position.z = o.lift ?? 0; b.groups.mod.rotation.z = o.spin ?? 0; b.groups.mod.visible = o.modVisible ?? true;
  if (side === 'red') b.groups.fist.position.x = 20 * (o.punch ?? 0); else b.groups.arm.rotation.z = o.arm ?? 1.1;
}

export function updateAct3(t) {
  const on = t >= A3.start; stageG.visible = on; pad.visible = on && t < 9.72;
  S.bots.green.root.visible = false;
  if (!on) return null;
  const { camera } = S, s = cam3(t), [x, y, z] = sph(s.tg, s.d, s.az, s.el);
  camera.fov = s.f; camera.near = 2; camera.updateProjectionMatrix(); camera.position.set(x, y, z); camera.lookAt(...s.tg); camera.updateMatrixWorld();

  // 手柄
  const pe = EASE.enter(prog(t, A3.pad, A3.pad + 0.22)), po = EASE.exit(prog(t, 9.45, 9.72));
  const sq = t < A3.pad + 0.22 ? 1 : 1 + 0.035 * Math.exp(-(t - A3.pad - 0.22) * 9) * Math.cos((t - A3.pad - 0.22) * 28);
  pad.position.set(0, lerp(-28, -2.9, pe) - po * 18, -33); pad.scale.setScalar(0.31 * sq);
  pad.rotation.set(-0.34 + 0.04 * Math.sin(t * 1.3), 0.08 * Math.sin(t * 0.9), 0.03 * Math.sin(t * 1.1));
  const walk = EASE.enter(prog(t, A3.walk[0], A3.walk[0] + 0.1)) * (1 - EASE.drift(prog(t, A3.walk[1] - 0.1, A3.walk[1])));
  const atk = Math.sin(Math.PI * prog(t, A3.atk[0], A3.atk[1]));
  sticks[0].rotation.x = -0.42 * walk; sticks[1].rotation.x = -0.42 * walk; sticks[2].rotation.x = -0.6 * atk;
  sticks[3].position.y = 6.9 - 0.25 * (t > A3.shou && t < 9.4 ? 1 : 0);

  // 机器人
  const ph = prog(t, A3.walk[0], A3.walk[1]) * Math.PI * 5;
  const dance = t > A3.shou ? Math.min(1, (t - A3.shou) / 0.1) * (1 - prog(t, 9.3, 9.5)) : 0, dp = (t - A3.shou) * 16;
  const forward = 6 * EASE.drift(prog(t, A3.walk[0], A3.walk[1]));
  if (t < 13.5) {
    const sep = lerp(12.5, 20, EASE.long(prog(t, 9.3, 10.4))), out = EASE.move(prog(t, 13.05, 13.5));
    const liftU = EASE.enter(prog(t, A3.kai, A3.kai + 0.38)), lift = 105 * liftU + 3 * Math.sin((t - A3.kai) * 2.2) * liftU, spin = liftU * (t - A3.kai) * 0.34;
    const faceIn = lerp(0, 0.5, EASE.long(prog(t, 9.3, 10.4)));
    place('red', -sep - out * 66, forward, faceIn, { phase: dance ? dp : ph, walk: dance || walk, hip: dance ? 0.42 : 0.32, punch: atk, lift, spin });
    place('blue', sep + out * -sep, forward - out * 6, -faceIn * (1 - out), { phase: (dance ? dp : ph) + 1.3, walk: dance || walk, hip: dance ? 0.42 : 0.32, arm: 1.2 - atk * 1.1, lift: lift * 1.04, spin: -spin });
    if (t > 13.05) S.bots.blue.groups.mod.position.z = lift + out * 500;
  } else {
    S.bots.red.root.visible = false;
    const leave = EASE.move(prog(t, 15.58, 15.86));   // 打印前退到地下
    place('blue', 0, 0, 0, { modVisible: false, arm: 0, y: -26 * leave, visible: t < 15.86 });
  }

  // 设计稿：8 种一种种闪过，定在大锤
  const dn = designNow(t), TOP = 10.68;
  designs.forEach((w, i) => {
    w.visible = dn?.i === i && t < 16.06;
    if (!w.visible) return;
    const pop = EASE.enter(clamp01(dn.age / 0.12));
    w.position.set(0, TOP + 5 * (1 - EASE.drift(prog(t, 15.14, 15.5))) + (1 - pop) * 3, 0);
    w.rotation.y = -0.25 + (t - A3.you) * 0.42; w.scale.setScalar(lerp(0.72, 1, pop));
    const f = 1 - prog(t, 15.86, 16.06); w.children.forEach(c => { c.children[0].material.opacity = 0.17 * f; c.children[1].material.opacity = 0.9 * f; });
    if (t > 15.58) w.position.y = lerp(TOP, 1.55, EASE.long(prog(t, 15.58, 15.95)));
  });

  // 3D 打印
  const pr = EASE.drift(prog(t, A3.print, A3.printEnd - 0.05)), inPrint = t >= 15.62 && t < A3.fly + 0.15;
  bedG.visible = inPrint;
  const bedIn = EASE.enter(prog(t, 15.62, 15.98)), bedOut = EASE.exit(prog(t, A3.fly, A3.fly + 0.14));
  bedG.position.set(-110 * bedOut, -44 * (1 - bedIn), 0);
  const H = 9.2, bedTop = 1.5, cur = bedTop + H * pr;
  rail.position.set(-90 * (1 - EASE.enter(prog(t, 15.9, 16.08))), cur + 4.6, 0.2 + 3.6 * Math.sin(t * 29 + 1)); carriage.position.x = 6 + 8.5 * Math.sin(t * 46);
  filament.visible = t > A3.print && t < A3.printEnd - 0.05;
  hammerSolid.visible = t >= A3.print - 0.02;
  hammerGlow.visible = t >= A3.print - 0.02 && t < A3.printEnd;
  uLayer.value = 1 - prog(t, A3.fly, A3.fly + 0.28);
  supports.visible = t < A3.fly;
  if (hammerSolid.visible) {
    const f = EASE.long(prog(t, A3.fly, A3.snap));
    hammerSolid.position.set(0, lerp(bedTop, TOP, f) + Math.sin(f * Math.PI) * 13, 0);
    hammerSolid.rotation.y = Math.sin(f * Math.PI) * 1.3; hammerSolid.userData.rotor.rotation.y = t > A3.snap ? arcSwing(t) : 0;
    hammerSolid.userData.plane.constant = t < A3.fly ? cur : 1000;
    hammerGlow.position.copy(hammerSolid.position); hammerGlow.rotation.copy(hammerSolid.rotation);
    hammerGlow.userData.low.constant = -(cur - 0.32);
  }
  // 绿色机器人：打印机滑走后从地面升起
  if (t >= A3.fly + 0.13) {
    place('green', 0, 0, 0, { modVisible: false, arm: 0, y: -26 * (1 - EASE.enter(prog(t, A3.fly + 0.13, A3.snap - 0.04))) });
    const b = t > A3.ji ? Math.sin(Math.PI * prog(t, A3.ji, A3.ji + 0.42)) : 0; S.bots.green.body.position.y = b * 0.6;
  }
  const d = t - A3.snap;
  sparks.visible = d > 0 && d < 0.6;
  if (sparks.visible) sparks.children.forEach((p, i) => { const R = rng(9100 + i), a = R() * 6.283, e = R() * 1.3, v = 14 + R() * 26; p.position.set(Math.cos(a) * Math.cos(e) * v * d, 11 + Math.sin(e) * v * d - 30 * d * d, Math.sin(a) * Math.cos(e) * v * d); p.scale.setScalar(1.6 * (1 - d / 0.6)); });
  ring.material.color.setHex(t > A3.snap ? GREEN : 0x8f7bff); ring.material.opacity = t > A3.snap ? 0.95 : 0.55;
  ring.scale.setScalar(1 + (d > 0 ? 0.16 * Math.exp(-d * 5) : 0));
  return camera;
}
function arcSwing(t) { const u = prog(t, A3.ji, A3.ji + 0.32); return Math.sin(u * Math.PI) * -0.9 + (t > 18.75 ? 0.18 * Math.sin((t - 18.75) * 2.4) : 0); }
export function stickScreen(i, project) { const v = new THREE.Vector3(); sticks[i].getWorldPosition(v); return project(v); }
