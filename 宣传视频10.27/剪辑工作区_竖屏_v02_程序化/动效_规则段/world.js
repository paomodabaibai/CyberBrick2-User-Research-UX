// 3D 世界：真实场地布局（按实拍反算，同 ../arena3d.js）+ 项目里 10-22 之前的机器人和球靶模型。
// 巴掌机 = 04_结构与硬件/Otto_75mm巴掌腕部接口_v02/整机总装_v02.glb（09-21）；拳头机 = 拳头_整体比例预览_v03/按用户参数导出_STL/整机_收回（09-28）；球靶 = 打印脱落球靶_v09 总装 135mm（10-19）。
// 坐标：场地 X 0–120、Y 0–80（cm）→ 世界 (X-60, h, Y-40)。模型单位 mm、Z 朝上。render(t) 只由 t 决定。
import * as THREE from 'three';
import { GLTFLoader } from './vendor/GLTFLoader.js';
import { RoomEnvironment } from './vendor/RoomEnvironment.js';
import { toCreasedNormals } from './vendor/BufferGeometryUtils.js';
import { EASE, clamp, clamp01, lerp, prog, rng } from '../engine/math.js';
import { setupAct3, updateAct3, stickScreen } from './act3.js';

export const SCALE = 0.12;   // mm → cm，并放大 1.2 倍，竖屏里看得清
const P = (X, Y, h = 0) => new THREE.Vector3(X - 60, h, Y - 40);
const WALL_H = 7.5;
const WALLS = [[[21, 33.5], [21.5, 80]], [[21.5, 60.7], [53, 60.7]], [[64, 24], [94.5, 24]], [[94, 0], [95, 58]]];
const PAD = { red: [10.5, 71], blue: [103, 14.5] };
export const BALL = { red: { ball: [44.5, 71.5], base: [31, 74.8] }, blue: { ball: [71.5, 9], base: [85, 5.7] } };
const COL = { red: 0xff3a2c, blue: 0x2f6bff };
const MAT = (c, o = {}) => new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.42, clearcoat: 0.35, clearcoatRoughness: 0.45, side: THREE.DoubleSide, ...o });
const WHITE = MAT(0xf1f2f4), DARK = MAT(0x23262e, { roughness: 0.6 }), GREY = MAT(0x9aa0aa, { metalness: 0.35, roughness: 0.4 });
const REDM = MAT(0xf0241a), BLUEM = MAT(0x1f54f2), SKY = MAT(0x9fc8f2), GREENM = MAT(0x16c463);

// 部件 → 材质 / 运动分组（部件含义见 assets/models/rig.json）
const PALM = { part_0: [WHITE], part_1: [WHITE, 'legA'], part_2: [WHITE, 'legB'], part_3: [BLUEM, 'legA'], part_4: [BLUEM, 'legB'], part_5: [SKY], part_6: [SKY], part_7: [DARK], part_8: [DARK, 'arm'], part_9: [BLUEM, 'arm'], part_10: [SKY, 'arm'], part_11: [SKY, 'arm'] };
const PUNCH_MOVE = ['p32', 'p37', 'p12', 'p08', 'p11', 'p13', 'p06', 'p07'];
const PUNCH_HIDE = ['p33', 'p34', 'p35', 'p36', 'p20'];
const PUNCH_MAT = { p00: WHITE, p01: WHITE, p02: WHITE, p03: REDM, p04: REDM, p28: REDM, p31: REDM, p32: REDM, p37: REDM, p12: REDM, p29: GREY, p30: GREY, p08: WHITE, p11: GREY, p13: GREY, p21: DARK, p25: DARK, p26: DARK, p24: DARK, p17: GREY, p18: GREY };

let renderer, scene, camera, W, H, bots = {}, ribbons = {}, targets = {}, ARENA = [], ballAt = {}, ballG = {}, ROUTE = {}, ribbonsB = {}, PATH, MID, DIR, AZ_HIT;

function wallTexture() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 128; const g = c.getContext('2d');
  g.fillStyle = '#1b2c45'; g.fillRect(0, 0, 512, 128);
  g.fillStyle = '#ffd400'; for (let x = -20; x < 540; x += 28) { g.beginPath(); g.moveTo(x, 112); g.lineTo(x + 14, 112); g.lineTo(x + 2, 128); g.lineTo(x - 12, 128); g.fill(); }
  g.fillStyle = '#0d121c'; g.fillRect(0, 104, 512, 4);
  g.fillStyle = 'rgba(255,255,255,0.8)'; g.font = '700 16px Orb'; g.fillText('CYBER / ARENA', 16, 30);
  g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(16, 38, 120, 2);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}

function mkRibbon(path, col) {
  const n = path.length, pos = new Float32Array(n * 6), half = [2.1, 0.42], out = [];
  for (const [w, color, op, h] of [[half[0], col, 0.34, 0.26], [half[1], 0xffffff, 0.96, 0.3]]) {
    const pa = new Float32Array(n * 6);
    for (let i = 0; i < n; i++) {
      const a = path[Math.max(0, i - 2)], b = path[Math.min(n - 1, i + 2)]; let dx = b[0] - a[0], dy = b[1] - a[1]; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
      const p = P(path[i][0], path[i][1], h);
      pa.set([p.x - dy * w, p.y, p.z + dx * w, p.x + dy * w, p.y, p.z - dx * w], i * 6);
    }
    const idx = []; for (let i = 0; i < n - 1; i++) { const q = i * 2; idx.push(q, q + 1, q + 2, q + 1, q + 3, q + 2); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pa, 3)); g.setIndex(idx);
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: op, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, toneMapped: false }));
    m.frustumCulled = false; scene.add(m); out.push(m);
  }
  return out;
}

async function loadBot(url, side) {
  const gltf = await new GLTFLoader().loadAsync(url);
  const root = new THREE.Group();   // 世界位置 / 朝向
  const body = new THREE.Group(); root.add(body);   // 摇摆
  const model = new THREE.Group(); model.rotation.x = -Math.PI / 2; model.scale.setScalar(SCALE); model.position.y = 89 * SCALE; body.add(model);
  const mod = new THREE.Group(); model.add(mod);
  const groups = { static: model, mod };
  const mkPivot = (x, y, parent = model) => { const g = new THREE.Group(); g.position.set(x, y, 0); parent.add(g); return g; };
  if (side !== 'red') { groups.legA = mkPivot(25.5, 0); groups.legB = mkPivot(-25.5, 0); groups.arm = mkPivot(0, 0, mod); }
  else { groups.legA = mkPivot(0, 25.5); groups.legB = mkPivot(0, -25.5); groups.fist = mkPivot(0, 0, mod); }
  const BODY = side !== 'red' ? ['part_0', 'part_1', 'part_2', 'part_3', 'part_4'] : ['p00', 'p01', 'p02', 'p03', 'p04'];
  const meshes = []; gltf.scene.traverse(o => { if (o.isMesh) meshes.push(o); });
  for (const o of meshes) {
    const name = o.name.replace(/_\d+$/, ''), nm = /^p\d\d$|^part_\d+$/.test(o.name) ? o.name : (o.parent?.name || name);
    o.updateWorldMatrix(true, false);
    let geo = o.geometry.clone().applyMatrix4(o.matrixWorld);
    // 抹平身体上的刻字水印（深 0.4 mm，巴掌机 +Y 面、拳头机 -X 面）。只改动画用的副本，原模型不动
    if (nm === 'part_0' || nm === 'p00') { const pa = geo.attributes.position; for (let v = 0; v < pa.count; v++) { if (nm === 'part_0' && pa.getY(v) > 33.9) pa.setY(v, 34.5); if (nm === 'p00' && pa.getX(v) < -33.9) pa.setX(v, -34.5); } }
    geo = toCreasedNormals(geo, 0.6);   // 按折角断开法线：硬边保持锐利，曲面保持平滑
    let mat = WHITE, grp = 'static';
    if (side !== 'red') { const e = PALM[nm]; if (e) { mat = side === 'green' && e[0] === BLUEM ? GREENM : e[0]; grp = e[1] || 'static'; } }
    else {
      if (PUNCH_HIDE.includes(nm)) continue;
      mat = PUNCH_MAT[nm] || GREY;
      if (PUNCH_MOVE.includes(nm)) grp = 'fist';
      if (nm === 'p01' || nm === 'p03') grp = 'legA';
      if (nm === 'p02' || nm === 'p04') grp = 'legB';
    }
    const g = grp === 'static' ? (BODY.includes(nm) ? model : mod) : groups[grp];
    const m = new THREE.Mesh(geo, mat); m.castShadow = m.receiveShadow = true;
    if (g !== model && g !== mod) m.position.set(-g.position.x, -g.position.y, 0);
    g.add(m);
  }
  scene.add(root);
  return { root, body, groups };
}

export async function initWorld(w, h, path) {
  W = w; H = h; PATH = path;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(W, H, false); renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.92;
  scene = new THREE.Scene(); scene.background = new THREE.Color(0x070a14); scene.fog = new THREE.Fog(0x070a14, 520, 1100);
  camera = new THREE.PerspectiveCamera(38, W / H, 2, 3000);
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.22;
  scene.add(new THREE.HemisphereLight(0xdfe9ff, 0x1a2030, 0.45));
  const sun = new THREE.DirectionalLight(0xfff6ea, 2.0); sun.position.set(-70, 170, 80); sun.castShadow = true;
  sun.shadow.mapSize.set(4096, 4096); Object.assign(sun.shadow.camera, { left: -90, right: 90, top: 70, bottom: -70, near: 10, far: 420 }); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.35; sun.shadow.radius = 5;
  scene.add(sun);
  const rimR = new THREE.PointLight(0xff3a2c, 5200, 300, 1.8); rimR.position.set(-95, 55, 50); scene.add(rimR);
  const rimB = new THREE.PointLight(0x3d7bff, 5200, 300, 1.8); rimB.position.set(95, 55, -50); scene.add(rimB);

  const tex = await new THREE.TextureLoader().loadAsync('../assets/floor_unit.png');
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(6, 4); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 16;
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(120, 80), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.78, color: 0xdfe8f2 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const table = new THREE.Mesh(new THREE.BoxGeometry(170, 3, 118), new THREE.MeshStandardMaterial({ color: 0x151922, roughness: 0.85 })); table.position.y = -1.6; table.receiveShadow = true; scene.add(table);
  const wm = MAT(0xf2f3f6, { roughness: 0.55 });
  for (const [x, z, sx, sz] of [[0, -40.8, 123.2, 1.6], [0, 40.8, 123.2, 1.6], [-60.8, 0, 1.6, 80], [60.8, 0, 1.6, 80]]) { const b = new THREE.Mesh(new THREE.BoxGeometry(sx, 8, sz), wm); b.position.set(x, 4, z); b.castShadow = b.receiveShadow = true; scene.add(b); }
  const wt = wallTexture(), wf = new THREE.MeshStandardMaterial({ map: wt, roughness: 0.5 });
  for (const [[x0, y0], [x1, y1]] of WALLS) {
    const a = P(x0, y0), b = P(x1, y1), len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.BoxGeometry(len, WALL_H, 0.6), [wm, wm, wm, wm, wf, wf]); m.position.set((a.x + b.x) / 2, WALL_H / 2, (a.z + b.z) / 2); m.rotation.y = -Math.atan2(b.z - a.z, b.x - a.x); m.castShadow = m.receiveShadow = true; scene.add(m);
  }
  for (const side of ['red', 'blue']) {
    const p = P(...PAD[side]);
    const disc = new THREE.Mesh(new THREE.CircleGeometry(8, 64), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.7 })); disc.rotation.x = -Math.PI / 2; disc.position.set(p.x, 0.06, p.z); disc.receiveShadow = true; scene.add(disc);
    const ring = new THREE.Mesh(new THREE.RingGeometry(7.2, 8, 64), new THREE.MeshBasicMaterial({ color: COL[side], toneMapped: false })); ring.rotation.x = -Math.PI / 2; ring.position.set(p.x, 0.08, p.z); scene.add(ring);
  }
  // 球靶：v09 总装（球心在原点，悬臂和立柱朝 +X），转到实拍里的朝向
  const ballGltf = await new GLTFLoader().loadAsync('assets/models/ball_v09.glb');
  for (const side of ['red', 'blue']) {
    const g = new THREE.Group(), bl = P(...BALL[side].ball), bp = P(...BALL[side].base);
    const s = ballGltf.scene.clone(true), hold = new THREE.Group(); hold.rotation.x = -Math.PI / 2; hold.scale.setScalar(0.1); hold.add(s); g.add(hold);
    s.traverse(o => { if (o.isMesh) { o.geometry = toCreasedNormals(o.geometry, 0.6); const isBall = /06_|07_|08_|09_/.test(o.name + (o.parent?.name || '')); o.material = isBall ? MAT(COL[side], { roughness: 0.3, emissive: COL[side], emissiveIntensity: 0.12 }) : WHITE; o.castShadow = o.receiveShadow = true; } });
    const yaw = Math.atan2(-(bp.z - bl.z), bp.x - bl.x);   // 模型里球在原点、立柱在 +X：让立柱朝底座，球正好落在 bl
    g.position.set(bl.x, 0, bl.z); g.rotation.y = yaw; scene.add(g); targets[side] = g;
    g.updateMatrixWorld(true); const bb = new THREE.Box3(); s.traverse(o => { if (o.isMesh && /06_|07_/.test(o.name + (o.parent?.name || ''))) bb.expandByObject(o); }); ballAt[side] = bb.getCenter(new THREE.Vector3());
    const bg = new THREE.Group(); scene.add(bg); const bm = []; s.traverse(o => { if (o.isMesh && /06_|07_|08_|09_/.test(o.name + (o.parent?.name || ''))) bm.push(o); }); bm.forEach(o => bg.attach(o)); ballG[side] = bg;
  }
  bots.red = await loadBot('assets/models/punch_parts.glb', 'red');
  bots.blue = await loadBot('assets/models/palm_parts.glb', 'blue');
  bots.green = await loadBot('assets/models/palm_parts.glb', 'green'); bots.green.root.visible = false;
  for (const [i, side] of [[0, 'red'], [1, 'blue']]) {
    ROUTE[side] = buildRoute(side, K(4.5, i));
    ribbons[side] = mkRibbon(ROUTE[side].pts, COL[side]); ribbonsB[side] = mkRibbon(PATH[i], COL[side]);
  }
  setupAct3(scene, camera, renderer, bots);
  ARENA = scene.children.filter(o => !o.isLight && o !== bots.red.root && o !== bots.blue.root && o !== bots.green.root && o !== camera && !o.userData.act3);
  // 撞击点与方向
  const a = PATH[0][182], b = PATH[1][182]; let dx = b[0] - a[0], dy = b[1] - a[1]; const L = Math.hypot(dx, dy) || 1; DIR = [dx / L, dy / L]; MID = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  AZ_HIT = Math.atan2(-DIR[1], DIR[0]) * 180 / Math.PI; if (Math.cos(AZ_HIT * Math.PI / 180) < 0) AZ_HIT += 180;   // 机位在两台连线的法线上，从场地近侧看
  return cv;
}

// ---------- 第一幕路线：出发 → 经过路中间 → 走到自己的球前打掉（设计路线，绕开真实隔墙）----------
export const BALL_HIT = { red: 3.88, blue: 4.08 };
const GO = 1.02, ARRIVE = { red: 3.76, blue: 3.95 }, REW = [4.28, 4.5];
const WAY = { red: [[[10.5, 71], [11, 27], [40, 22]], [[65, 53], [60, 70]]], blue: [[[103, 14.5], [104.5, 65]], [[80, 63], [83, 38], [72, 30], [60, 28], [56, 10]]] };
function round(pts, r = 6) {
  const out = [pts[0]];
  for (let i = 1; i < pts.length - 1; i++) {
    const [a, b, c] = [pts[i - 1], pts[i], pts[i + 1]], d1 = Math.hypot(b[0] - a[0], b[1] - a[1]), d2 = Math.hypot(c[0] - b[0], c[1] - b[1]), k = Math.min(r, d1 / 2, d2 / 2);
    const p = [b[0] + (a[0] - b[0]) * k / d1, b[1] + (a[1] - b[1]) * k / d1], q = [b[0] + (c[0] - b[0]) * k / d2, b[1] + (c[1] - b[1]) * k / d2];
    for (let j = 0; j <= 10; j++) { const u = j / 10; out.push([(1 - u) ** 2 * p[0] + 2 * u * (1 - u) * b[0] + u * u * q[0], (1 - u) ** 2 * p[1] + 2 * u * (1 - u) * b[1] + u * u * q[1]]); }
  }
  out.push(pts[pts.length - 1]); return out;
}
function buildRoute(side, mid) {
  const dense = [...round([...WAY[side][0], mid]), ...round([mid, ...WAY[side][1]]).slice(1)], pts = [dense[0]];
  for (let i = 1; i < dense.length; i++) { const a = dense[i - 1], b = dense[i], L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.round(L / 0.8)); for (let j = 1; j <= n; j++) pts.push([lerp(a[0], b[0], j / n), lerp(a[1], b[1], j / n)]); }
  const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  let im = 0, best = 1e9; pts.forEach((q, i) => { const d = Math.hypot(q[0] - mid[0], q[1] - mid[1]); if (d < best) { best = d; im = i; } });
  return { pts, L, len: L[L.length - 1], sMid: L[im] };
}
const along = (R, sv) => { sv = clamp(sv, 0, R.len); let i = 1; while (i < R.L.length - 1 && R.L[i] < sv) i++; const u = (sv - R.L[i - 1]) / Math.max(1e-6, R.L[i] - R.L[i - 1]); return [lerp(R.pts[i - 1][0], R.pts[i][0], u), lerp(R.pts[i - 1][1], R.pts[i][1], u)]; };
const walkEase = u => { u = clamp01(u); const a = 0.07; return u < a ? u * u / (2 * a * (1 - a)) : u > 1 - a ? 1 - (1 - u) ** 2 / (2 * a * (1 - a)) : (u - a / 2) / (1 - a); };
const sAt = (side, ta) => ROUTE[side].len * walkEase((ta - GO) / (ARRIVE[side] - GO));
function tAofS(side, sv) { let a = GO, b = ARRIVE[side]; for (let i = 0; i < 40; i++) { const m = (a + b) / 2; if (sAt(side, m) < sv) a = m; else b = m; } return (a + b) / 2; }
// 倒带：t 走到 4.28 后时间往回走，机器人退回路中间（正好接第二幕）
function tA(side, t) { if (t <= REW[0]) return t; const u = EASE.drift(prog(t, REW[0], REW[1])); return lerp(REW[0], tAofS(side, ROUTE[side].sMid), u); }
function tBall(side, t) { if (t <= REW[0]) return t; return lerp(REW[0], BALL_HIT[side] - 0.02, EASE.drift(prog(t, REW[0], REW[1] - 0.04))); }
export const rewinding = t => t > REW[0] && t < REW[1] ? Math.sin(prog(t, REW[0], REW[1]) * Math.PI) : 0;
function poseA(side, t) {
  const ta = tA(side, t), R = ROUTE[side], sv = sAt(side, ta), [X, Y] = along(R, sv), q0 = along(R, sv - 3), q1 = along(R, sv + 3);
  const yawOf = (ax, ay) => side === 'red' ? Math.atan2(-ay, ax) : Math.atan2(-ax, -ay);
  let yaw = yawOf(q1[0] - q0[0], q1[1] - q0[1]);
  const ball = BALL[side].ball, f = EASE.long(prog(ta, ARRIVE[side] - 0.3, ARRIVE[side]));
  yaw = angLerp(yaw, Math.atan2(-(ball[1] - Y), ball[0] - X), f);
  if (t > 4.38) yaw = angLerp(yaw, poseB(side, 4.5).yaw, prog(t, 4.38, 4.5));
  const moving = ta > GO && ta < ARRIVE[side];
  return { X, Y, yaw, roll: 0, tilt: 0, lift: 0, phase: sv * Math.PI * 2 / 8 + (side === 'red' ? 0 : 1.3), walking: moving ? 1 - prog(ta, ARRIVE[side] - 0.08, ARRIVE[side]) : 0, ta };
}
function ballState(side, t) {
  const dt = tBall(side, t) - BALL_HIT[side]; if (dt <= 0) return [0, 0, 0];
  const R = ROUTE[side], end = along(R, R.len), b = BALL[side].ball, L = Math.hypot(b[0] - end[0], b[1] - end[1]), dx = (b[0] - end[0]) / L, dy = (b[1] - end[1]) / L;
  const m = Math.min(dt, 0.9), d = 30 * m * (1 - 0.3 * m), g = 980, h = 10.5, t1 = Math.sqrt(2 * h / g);
  let y; if (dt < t1) y = h - 0.5 * g * dt * dt; else { const k = dt - t1, v1 = g * t1 * 0.45, t2 = 2 * v1 / g; y = k < t2 ? v1 * k - 0.5 * g * k * k : Math.max(0, v1 * 0.4 * (k - t2) - 0.5 * g * (k - t2) ** 2); }
  return [dx * d, Math.max(0, y) - h, dy * d];
}

// ---------- 第二幕：半路撞上（已通过，不要动）----------
export const HIT = 6.08, RAMP0 = 5.82;
const FPS = 30, K = (t, i) => { const f = clamp(t * FPS, 0, PATH[i].length - 1.001), a = Math.floor(f), u = f - a; return [lerp(PATH[i][a][0], PATH[i][a + 1][0], u), lerp(PATH[i][a][1], PATH[i][a + 1][1], u)]; };
const angLerp = (a, b, u) => { let d = (b - a) % (Math.PI * 2); if (d > Math.PI) d -= Math.PI * 2; if (d < -Math.PI) d += Math.PI * 2; return a + d * u; };
// 沿路线累计的步伐相位
function dist(t, i) { let s = 0, last = K(0, i); for (let q = 1 / FPS; q <= t; q += 1 / FPS) { const p = K(q, i); s += Math.hypot(p[0] - last[0], p[1] - last[1]); last = p; } return s; }
export const pose = (side, t) => t < REW[1] ? poseA(side, t) : poseB(side, t);
function poseB(side, t) {
  const i = side === 'red' ? 0 : 1, sign = side === 'red' ? -1 : 1, D = 24;
  const tt = Math.min(t, 6.0);
  let [X, Y] = K(tt, i);
  const q0 = K(tt - 0.25, i), q1 = K(tt + 0.25, i); let dx = q1[0] - q0[0], dy = q1[1] - q0[1];
  if (Math.hypot(dx, dy) < 0.6) { dx = side === 'red' ? 1 : -1; dy = side === 'red' ? -0.4 : 0.4; }
  // 朝向：沿路线走；巴掌机的“前”是模型 +Y（世界 -Z），拳头机是模型 +X
  const yawOf = (ax, ay) => side === 'red' ? Math.atan2(-ay, ax) : Math.atan2(-ax, -ay);
  let yaw = yawOf(dx, dy);
  const u = EASE.long(prog(t, 5.0, HIT));
  const tgX = MID[0] + sign * DIR[0] * D / 2, tgY = MID[1] + sign * DIR[1] * D / 2;
  X = lerp(X, tgX, u); Y = lerp(Y, tgY, u);
  const faceX = -sign * DIR[0], faceY = -sign * DIR[1];
  // 打架时拳头机正对对手；巴掌机把伸手的那一侧（模型 +X）转向对手
  const yawFace = Math.atan2(-faceY, faceX);
  yaw = angLerp(yaw, yawFace, u);
  let roll = 0, tilt = 0, lift = 0;
  if (t > HIT + 0.1) {   // 慢动作：被打的往后退，打人的跟进
    const s = EASE.enter(prog(t, HIT + 0.1, 7.0));
    if (side === 'red') { X += sign * DIR[0] * 3.6 * s; Y += sign * DIR[1] * 3.6 * s; tilt = 0.22 * s; lift = 0.7 * Math.sin(s * Math.PI); }
    else { X += DIR[0] * -1.4 * s; Y += DIR[1] * -1.4 * s; }
  }
  const phase = dist(Math.min(t, 5.9), i) * Math.PI * 2 / 8 + (side === 'red' ? 0 : 1.3);
  const walking = 1 - u;
  return { X, Y, yaw, roll, tilt, lift, phase, walking };
}
export const contact = () => [MID[0] + DIR[0] * 0.8, MID[1] + DIR[1] * 0.8, 16.5];
export const gap = t => { const a = K(Math.min(t, 6), 0), b = K(Math.min(t, 6), 1); return Math.max(0, Math.hypot(a[0] - b[0], a[1] - b[1]) - 13); };

function applyBot(side, t) {
  const b = bots[side], p = pose(side, t), v = P(p.X, p.Y);
  b.root.position.set(v.x, p.lift, v.z); b.root.rotation.y = p.yaw;
  const sw = Math.sin(p.phase), wk = p.walking;
  b.body.rotation.set(0, 0, 0); b.body.position.y = Math.abs(sw) * 0.55 * wk;
  // 摇摆轴：垂直于前进方向
  if (side === 'red') { b.body.rotation.x = 0.1 * sw * wk; b.body.rotation.z = p.tilt; }
  else { b.body.rotation.z = 0.1 * sw * wk; b.body.rotation.x = 0; }
  const hip = 0.32 * sw * wk;
  b.groups.legA.rotation.z = hip; b.groups.legB.rotation.z = -hip;
  b.groups.legA.position.z = Math.max(0, sw) * 1.4 * wk / SCALE * 0.1; b.groups.legB.position.z = Math.max(0, -sw) * 1.4 * wk / SCALE * 0.1;
  if (side === 'red') {
    // 走路时拳头偶尔试探；撞击前蓄力、撞击时打出（真实行程 20 mm）
    const jab = Math.max(0, Math.sin(p.phase * 0.55)) * 0.5 * wk;
    const e = t < HIT - 0.06 ? 0 : EASE.enter(prog(t, HIT - 0.06, HIT));
    const eA = t < REW[1] ? EASE.enter(prog(p.ta, BALL_HIT.red - 0.07, BALL_HIT.red)) * (1 - EASE.drift(prog(p.ta, BALL_HIT.red + 0.08, BALL_HIT.red + 0.3))) : 0;
    b.groups.fist.position.x = 20 * Math.max(jab, e, eA);
  } else {
    // 巴掌：走路时小幅摆，撞击前后拉到 -95°，撞击瞬间横扫到 0°，慢动作继续扫过去
    const idle = 0.45 * Math.sin(p.phase * 0.5) * wk;
    const wind = EASE.long(prog(t, 5.3, 5.86)), hit = prog(t, 5.86, HIT) ** 2, after = EASE.enter(prog(t, HIT + 0.1, 7.0));
    const base = lerp(idle, -1.66, wind);
    if (t < REW[1]) {
      const H = BALL_HIT.blue, w = EASE.long(prog(p.ta, H - 0.42, H - 0.14)), h = prog(p.ta, H - 0.14, H) ** 2, af = EASE.enter(prog(p.ta, H, H + 0.2));
      b.groups.arm.rotation.z = lerp(lerp(idle, -1.66, w), 0, h) + af * 0.6;
    } else b.groups.arm.rotation.z = lerp(base, 0, hit) + after * 0.75;
  }
}

// ---------- 机位 ----------
const sph = (tg, d, az, el) => { const a = az * Math.PI / 180, e = el * Math.PI / 180; return [tg[0] + d * Math.cos(e) * Math.sin(a), tg[1] + d * Math.sin(e), tg[2] + d * Math.cos(e) * Math.cos(a)]; };
function camAt(t) {
  const hero = { tg: [0, 2, 0], d: 340, az: -12, el: 38, f: 38 };
  const top = { tg: [0, 0, 0], d: 470, az: -42, el: 74, f: 38 };
  const orbit = { tg: [0, 3, 0], d: 346, az: 9, el: 35, f: 38 };
  const mv = (a, b, u) => ({ tg: a.tg.map((v, i) => lerp(v, b.tg[i], u)), d: Math.exp(lerp(Math.log(a.d), Math.log(b.d), u)), az: lerp(a.az, b.az, u), el: lerp(a.el, b.el, u), f: lerp(a.f, b.f, u) });
  let s = mv(top, hero, EASE.pull(prog(t, 0, 1.05)));
  s = mv(s, orbit, EASE.long(prog(t, 1.0, 4.5)));
  const rb = P(...BALL.red.ball);
  const push = EASE.long(prog(t, 3.0, 3.8)) * (1 - EASE.long(prog(t, 3.98, 4.42)));
  s = mv(s, { tg: [rb.x * 0.55, 5, rb.z * 0.55], d: 262, az: s.az, el: 33, f: 38 }, push);
  const m = P(MID[0], MID[1], 6);
  const near = { tg: [m.x, 6, m.z], d: 235, az: lerp(9, AZ_HIT, 0.35), el: 31, f: 38 };
  s = mv(s, near, EASE.long(prog(t, 4.45, 5.82)));
  const c = P(...contact().slice(0, 2), 12);
  const close = { tg: [c.x, 11, c.z], d: 96, az: AZ_HIT, el: 21, f: 50 };
  s = mv(s, close, EASE.accel(prog(t, RAMP0, HIT)));
  if (t > HIT) { const d = t - HIT; s.d = 96 * (1 - 0.1 * Math.exp(-d * 10)) * (1 - d * 0.05) * (d < 0.1 ? 0.94 : 1); s.az = AZ_HIT + (d - 0.1 > 0 ? (d - 0.1) * 8 : 0); s.el = 21 - Math.max(0, d - 0.1) * 2; }
  s.az += 0.8 * Math.sin(t * 0.7); s.el += 0.4 * Math.sin(t * 0.53 + 1);
  return s;
}

export function renderWorld(t) {
  if (t >= 7.0) {
    ARENA.forEach(o => { o.visible = false; });
    updateAct3(t);
    scene.environmentIntensity = 0.3;
    renderer.render(scene, camera);
    return renderer.domElement;
  }
  ARENA.forEach(o => { if (!o.userData.keepHidden) o.visible = true; });
  applyBot('red', t); applyBot('blue', t);
  targets.red.visible = t < HIT;   // 撞击镜头里红球靶挡在最前面，白闪那一帧收掉
  ballG.red.visible = t < HIT;
  for (const side of ['red', 'blue']) { const o = ballState(side, t); ballG[side].position.set(o[0], o[1], o[2]); }
  const k = Math.floor(t * FPS), kk = Math.min(k, 186);
  for (const [i, side] of [[0, 'red'], [1, 'blue']]) {
    const a = clamp01((t - 0.98) / 0.06) * (1 - clamp01((t - 5.86) / 0.14)), R = ROUTE[side], sv = sAt(side, tA(side, t));
    let n = 1; while (n < R.L.length - 1 && R.L[n] < sv) n++;
    ribbons[side].forEach((m, j) => { m.geometry.setDrawRange(0, Math.max(0, (n - 1) * 6)); m.visible = a > 0.01; m.material.opacity = (j ? 0.96 : 0.34) * a; });
    ribbonsB[side].forEach((m, j) => { m.geometry.setDrawRange(135 * 6, Math.max(0, (kk - 135) * 6)); m.visible = a > 0.01 && t >= REW[1]; m.material.opacity = (j ? 0.96 : 0.34) * a; });
  }
  const s = camAt(t), [x, y, z] = sph(s.tg, s.d, s.az, s.el);
  camera.fov = s.f; camera.near = t > RAMP0 ? Math.max(2, s.d - 62) : 2; camera.updateProjectionMatrix(); camera.position.set(x, y, z); camera.lookAt(...s.tg); camera.updateMatrixWorld();
  renderer.render(scene, camera);
  return renderer.domElement;
}
export const pv = v => { const q = v.clone().project(camera); return [(q.x + 1) / 2 * W, (1 - q.y) / 2 * H]; };
export const stickAt = i => stickScreen(i, pv);
export function projectBall(side) { const v = ballAt[side].clone().project(camera); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; }
export function project(X, Y, h = 0) {
  const v = P(X, Y, h).project(camera);
  return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H];
}
