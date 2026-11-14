// 规则动画 3D 版：按实拍反算的真实场地（120×80 cm，地砖 10 cm）建模；初始相机 = V02 实拍机位（最小二乘解算，重投影误差约 7 px），
// 实拍与 3D 在同一视角重合后，镜头升起转到竖屏正中，演示：同时出发 → 中间相遇对打 → 各自击球。全部由时间 lt 决定，逐帧确定。
// 世界坐标：x 向右、y 向上、z 朝向实拍机位；原点在场地中心；单位 cm。场地坐标 (X, Y) → (X - 60, Y - 40)。
import * as THREE from './engine/three.module.min.js';
import { EASE, clamp01, lerp, rng } from './engine/math.js';

const P = (X, Y) => new THREE.Vector3(X - 60, 0, Y - 40);
const WALL_H = 6.6;
const WALLS = [[[21, 33.5], [21.5, 80]], [[21.5, 60.7], [53, 60.7]], [[64, 24], [94.5, 24]], [[94, 0], [95, 58]]];
const PAD = { red: [10.5, 71], blue: [103, 14.5] };
const BALL = { red: { ball: [44.5, 71.5], base: [35.4, 74.8] }, blue: { ball: [71.5, 9], base: [80.6, 5.7] } };
const BALL_H = 10, BALL_R = 3.4;
const COL = { red: 0xff4430, blue: 0x3c78ff };
const MEET = { red: [55.5, 42.5], blue: [64.5, 37.5] };
const ROUTE_PTS = {
  red: [[[10.5, 71], [11, 27], [40, 27.5], MEET.red], [MEET.red, [62, 53], [61.5, 69.5], [50.5, 70.5]]],
  blue: [[[103, 14.5], [104.5, 65.5], [80, 63.5], MEET.blue], [MEET.blue, [58, 27.5], [57.5, 10], [65.5, 9.5]]],
};
// 实拍机位（V02 第 3 秒），竖屏中实拍按宽度完整放入时的等效竖直视场角
export const CAM0 = { pos: [11.436, 95.724, 215.241], fwd: [-0.06028, -0.379, -0.92343], up: [0.001, 0.92509, -0.37975], vfov: 67.508 };

// 时间表（镜头内秒）
export const AT = { match: 0.45, xfade: [0.45, 1.0], fly: [0.9, 2.9], spawn: 2.7, go: 3.1, meet: 5.3, clash: [5.3, 6.6], hit: { red: 8.1, blue: 8.45 }, back: [9.2, 10.4], end: 10.6 };
export const CAPS = [
  { at: 2.85, out: 5.25, n: '01', text: '红蓝同时出发' },
  { at: 5.3, out: 6.65, n: '02', text: '中间相遇，可以拦住对方' },
  { at: 6.7, out: 9.3, n: '03', text: '先打掉自己颜色的球，就赢' },
];

function route(pts, r = 6) { // 圆角折线 → 弧长参数化
  const out = [pts[0]];
  for (let i = 1; i < pts.length - 1; i++) {
    const [a, b, c] = [pts[i - 1], pts[i], pts[i + 1]];
    const d1 = Math.hypot(b[0] - a[0], b[1] - a[1]), d2 = Math.hypot(c[0] - b[0], c[1] - b[1]), k = Math.min(r, d1 / 2, d2 / 2);
    const p = [b[0] + (a[0] - b[0]) * k / d1, b[1] + (a[1] - b[1]) * k / d1], q = [b[0] + (c[0] - b[0]) * k / d2, b[1] + (c[1] - b[1]) * k / d2];
    for (let j = 0; j <= 10; j++) { const u = j / 10; out.push([(1 - u) ** 2 * p[0] + 2 * u * (1 - u) * b[0] + u * u * q[0], (1 - u) ** 2 * p[1] + 2 * u * (1 - u) * b[1] + u * u * q[1]]); }
  }
  out.push(pts[pts.length - 1]);
  const L = [0]; for (let i = 1; i < out.length; i++) L.push(L[i - 1] + Math.hypot(out[i][0] - out[i - 1][0], out[i][1] - out[i - 1][1]));
  return { pts: out, L, len: L[L.length - 1] };
}
function along(R, s) {
  s = Math.max(0, Math.min(R.len, s)); let i = 1; while (i < R.L.length - 1 && R.L[i] < s) i++;
  const u = (s - R.L[i - 1]) / Math.max(1e-6, R.L[i] - R.L[i - 1]);
  return [lerp(R.pts[i - 1][0], R.pts[i][0], u), lerp(R.pts[i - 1][1], R.pts[i][1], u)];
}
const ROUTE = Object.fromEntries(Object.entries(ROUTE_PTS).map(([k, v]) => [k, v.map(p => route(p))]));

let renderer, scene, camera, bots = {}, balls = {}, trails = {}, sparks, ready = false, W, H;

function wallTexture() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 128; const g = c.getContext('2d');
  g.fillStyle = '#2a3a56'; g.fillRect(0, 0, 512, 128);
  g.fillStyle = '#ffd400'; for (let x = -20; x < 540; x += 28) { g.beginPath(); g.moveTo(x, 112); g.lineTo(x + 14, 112); g.lineTo(x + 2, 128); g.lineTo(x - 12, 128); g.fill(); }
  g.fillStyle = '#0d121c'; g.fillRect(0, 104, 512, 4);
  g.fillStyle = 'rgba(255,255,255,0.75)'; g.font = '700 16px Orb'; g.fillText('CYBER / ARENA', 16, 30);
  g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(16, 38, 120, 2);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}

function makeBot(side) {
  const g = new THREE.Group(), col = COL[side];
  const white = new THREE.MeshStandardMaterial({ color: 0xf2f4f8, roughness: 0.55 });
  const cm = new THREE.MeshStandardMaterial({ color: col, roughness: 0.45, emissive: col, emissiveIntensity: 0.12 });
  const body = new THREE.Mesh(new THREE.BoxGeometry(5.6, 5.0, 4.6), white); body.position.y = 7.2; body.castShadow = true; g.add(body);
  const legs = [], feet = [];
  for (const s of [-1, 1]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(1.5, 3.4, 1.8), white); leg.position.set(0, 3.2, s * 1.5); leg.castShadow = true; g.add(leg); legs.push(leg);
    const foot = new THREE.Mesh(new THREE.BoxGeometry(4.0, 1.2, 2.2), cm); foot.position.set(0.4, 0.6, s * 1.5); foot.castShadow = true; g.add(foot); feet.push(foot);
  }
  const top = new THREE.Group(); top.position.y = 9.7; g.add(top);
  const arm = new THREE.Group(); top.add(arm);
  if (side === 'red') {
    const frame = new THREE.Mesh(new THREE.BoxGeometry(5.0, 2.6, 4.2), cm); frame.position.y = 1.3; frame.castShadow = true; top.add(frame);
    const rod = new THREE.Mesh(new THREE.BoxGeometry(5, 0.9, 0.9), white); rod.position.set(3.5, 1.6, 0); arm.add(rod);
    const fist = new THREE.Mesh(new THREE.SphereGeometry(2.0, 24, 16), cm); fist.scale.set(1, 0.95, 1.1); fist.position.set(6.6, 1.6, 0); fist.castShadow = true; arm.add(fist);
  } else {
    const frame = new THREE.Mesh(new THREE.BoxGeometry(5.0, 2.2, 4.2), new THREE.MeshStandardMaterial({ color: 0xcfe0ff, roughness: 0.4, transparent: true, opacity: 0.92 })); frame.position.y = 1.1; frame.castShadow = true; top.add(frame);
    const rod = new THREE.Mesh(new THREE.BoxGeometry(5, 0.7, 0.7), white); rod.position.set(3.2, 2.6, 0); arm.add(rod);
    const palm = new THREE.Group(); palm.position.set(6.4, 3.6, 0); arm.add(palm);
    const pm = new THREE.Mesh(new THREE.BoxGeometry(1.0, 3.2, 3.4), cm); pm.castShadow = true; palm.add(pm);
    for (let i = 0; i < 4; i++) { const f = new THREE.Mesh(new THREE.BoxGeometry(0.9, 2.4, 0.7), cm); f.position.set(0, 2.6, -1.25 + i * 0.83); f.castShadow = true; palm.add(f); }
  }
  g.scale.setScalar(1.35); // 实物约 12 cm 高，放大 1.35 倍以便在竖屏里看清
  g.userData = { legs, feet, arm, top };
  return g;
}

export async function init3d(w, h) {
  W = w; H = h;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true, alpha: false });
  renderer.setSize(W, H, false); renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.3;
  scene = new THREE.Scene(); scene.background = new THREE.Color(0x0a0e1a); scene.fog = new THREE.Fog(0x0a0e1a, 300, 700);
  camera = new THREE.PerspectiveCamera(CAM0.vfov, W / H, 1, 3000);

  scene.add(new THREE.HemisphereLight(0xeef3ff, 0x2a3040, 1.6));
  const sun = new THREE.DirectionalLight(0xffffff, 2.2); sun.position.set(-60, 160, 90); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -90, right: 90, top: 70, bottom: -70, near: 10, far: 400 }); sun.shadow.bias = -0.0004; sun.shadow.radius = 4;
  scene.add(sun);

  // 地板：v10 明亮科技版循环单元（20 cm），与实场一致
  const tex = await new THREE.TextureLoader().loadAsync('assets/floor_unit.png');
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(6, 4); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(120, 80), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.7, color: 0xffffff }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  // 桌面
  const table = new THREE.Mesh(new THREE.BoxGeometry(150, 3, 104), new THREE.MeshStandardMaterial({ color: 0x1a1e27, roughness: 0.95 })); table.position.y = -1.6; table.receiveShadow = true; scene.add(table);
  // 白色围边
  const wm = new THREE.MeshStandardMaterial({ color: 0xf4f5f7, roughness: 0.6 });
  for (const [x, z, sx, sz] of [[0, -40.8, 123.2, 1.6], [0, 40.8, 123.2, 1.6], [-60.8, 0, 1.6, 80], [60.8, 0, 1.6, 80]]) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(sx, 9, sz), wm); b.position.set(x, 4.5, z); b.castShadow = b.receiveShadow = true; scene.add(b);
  }
  // 隔墙
  const wt = wallTexture();
  for (const [[x0, y0], [x1, y1]] of WALLS) {
    const a = P(x0, y0), b = P(x1, y1), len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.BoxGeometry(len, WALL_H, 0.6), [wm, wm, wm, wm, new THREE.MeshStandardMaterial({ map: wt, roughness: 0.5 }), new THREE.MeshStandardMaterial({ map: wt, roughness: 0.5 })]);
    m.position.set((a.x + b.x) / 2, WALL_H / 2, (a.z + b.z) / 2); m.rotation.y = -Math.atan2(b.z - a.z, b.x - a.x); m.castShadow = m.receiveShadow = true; scene.add(m);
    const cap = new THREE.Mesh(new THREE.BoxGeometry(len + 0.2, 0.35, 0.8), wm); cap.position.copy(m.position); cap.position.y = WALL_H + 0.17; cap.rotation.y = m.rotation.y; scene.add(cap);
  }
  // 出生圈
  for (const side of ['red', 'blue']) {
    const p = P(...PAD[side]);
    const disc = new THREE.Mesh(new THREE.CircleGeometry(7.5, 64), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.7 })); disc.rotation.x = -Math.PI / 2; disc.position.set(p.x, 0.06, p.z); disc.receiveShadow = true; scene.add(disc);
    const ring = new THREE.Mesh(new THREE.RingGeometry(6.8, 7.6, 64), new THREE.MeshBasicMaterial({ color: COL[side] })); ring.rotation.x = -Math.PI / 2; ring.position.set(p.x, 0.08, p.z); scene.add(ring);
  }
  // 球靶：底座 + 立柱 + 横臂 + 磁吸球
  for (const side of ['red', 'blue']) {
    const bp = P(...BALL[side].base), bl = P(...BALL[side].ball);
    const base = new THREE.Mesh(new THREE.BoxGeometry(6, 0.5, 6), wm); base.position.set(bp.x, 0.25, bp.z); base.castShadow = true; scene.add(base);
    const col = new THREE.Mesh(new THREE.BoxGeometry(1.8, 16, 1.8), wm); col.position.set(bp.x, 8, bp.z); col.castShadow = true; scene.add(col);
    const dx = bl.x - bp.x, dz = bl.z - bp.z, d = Math.hypot(dx, dz);
    const arm = new THREE.Mesh(new THREE.BoxGeometry(d, 1.4, 1.4), wm); arm.position.set((bp.x + bl.x) / 2, BALL_H + BALL_R + 0.4, (bp.z + bl.z) / 2); arm.rotation.y = -Math.atan2(dz, dx); arm.castShadow = true; scene.add(arm);
    const ball = new THREE.Mesh(new THREE.SphereGeometry(BALL_R, 32, 24), new THREE.MeshStandardMaterial({ color: COL[side], roughness: 0.35, emissive: COL[side], emissiveIntensity: 0.15 }));
    ball.position.set(bl.x, BALL_H, bl.z); ball.castShadow = true; scene.add(ball);
    const halo = new THREE.Mesh(new THREE.RingGeometry(5, 5.8, 48), new THREE.MeshBasicMaterial({ color: COL[side], transparent: true, opacity: 0 })); halo.rotation.x = -Math.PI / 2; halo.position.set(bl.x, 0.12, bl.z); scene.add(halo);
    balls[side] = { ball, halo, home: bl.clone() };
  }
  // 路线：地面发光带（整条淡显预告 + 走过的部分高亮）
  for (const side of ['red', 'blue']) {
    trails[side] = ROUTE[side].map(R => {
      const pts = R.pts.map(([x, y]) => { const v = P(x, y); v.y = 0.2; return v; });
      const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
      const geo = new THREE.TubeGeometry(curve, 240, 0.55, 8, false);
      const ghost = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: COL[side], transparent: true, opacity: 0 })); scene.add(ghost);
      const lit = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: COL[side] })); lit.geometry = geo.clone(); scene.add(lit);
      return { R, ghost, lit, count: lit.geometry.index.count };
    });
  }
  for (const side of ['red', 'blue']) { bots[side] = makeBot(side); scene.add(bots[side]); }
  // 对打火花
  sparks = new THREE.Group(); scene.add(sparks);
  for (let i = 0; i < 26; i++) sparks.add(new THREE.Mesh(new THREE.SphereGeometry(0.35, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffd400 })));
  ready = true;
  return renderer.domElement;
}

function progress(side, lt) {
  const [A, B] = ROUTE[side];
  if (lt < AT.go) return { R: A, s: 0, moving: 0, leg: 0 };
  if (lt < AT.meet) return { R: A, s: A.len * EASE.drift((lt - AT.go) / (AT.meet - AT.go)), moving: 1, leg: 0 };
  if (lt < AT.clash[1]) return { R: B, s: 0, moving: 0, leg: 1 };
  const u = clamp01((lt - AT.clash[1]) / (AT.hit[side] - 0.2 - AT.clash[1]));
  return { R: B, s: B.len * EASE.move(u), moving: u < 1 ? 1 : 0, leg: 1 };
}

// 相机：实拍机位 → 竖屏英雄机位（红方在下、蓝方在上，俯角约 56°）→ 对打时推近 → 收尾回到实拍机位
const HERO = { tg: [0, 0, 0], dist: 200, az: -90, el: 58, vfov: 44 };
function sph(tg, dist, az, el) { const a = az * Math.PI / 180, e = el * Math.PI / 180; return [tg[0] + dist * Math.cos(e) * Math.sin(a), tg[1] + dist * Math.sin(e), tg[2] + dist * Math.cos(e) * Math.cos(a)]; }
const C0 = (() => { // 实拍机位的球坐标形式（以视线落地点为目标）
  const [px, py, pz] = CAM0.pos, [fx, fy, fz] = CAM0.fwd, s = -py / fy, tg = [px + s * fx, 0, pz + s * fz];
  const dx = px - tg[0], dy = py, dz = pz - tg[2], dist = Math.hypot(dx, dy, dz);
  return { tg, dist, az: Math.atan2(dx, dz) * 180 / Math.PI, el: Math.asin(dy / dist) * 180 / Math.PI, vfov: CAM0.vfov };
})();
function camState(lt) {
  const mix = (a, b, u) => ({ tg: a.tg.map((v, i) => lerp(v, b.tg[i], u)), dist: Math.exp(lerp(Math.log(a.dist), Math.log(b.dist), u)), az: lerp(a.az, b.az, u), el: lerp(a.el, b.el, u), vfov: lerp(a.vfov, b.vfov, u) });
  let s = C0;
  if (lt > AT.fly[0]) s = mix(C0, HERO, EASE.move(clamp01((lt - AT.fly[0]) / (AT.fly[1] - AT.fly[0]))));
  // 相遇推近：目标移到交会点、拉近、稍微绕一点
  const zc = EASE.drift(clamp01((lt - AT.meet + 0.5) / 0.6)) * (1 - EASE.drift(clamp01((lt - AT.clash[1] + 0.1) / 0.7)));
  if (zc > 0) { const m = P((MEET.red[0] + MEET.blue[0]) / 2, (MEET.red[1] + MEET.blue[1]) / 2); s = mix(s, { tg: [m.x, 5, m.z], dist: 155, az: -74, el: 50, vfov: 44 }, zc); }
  // 操作员手感：极慢漂移
  s.az += 1.2 * Math.sin(lt * 0.7); s.el += 0.6 * Math.sin(lt * 0.53 + 1);
  if (lt > AT.back[0]) s = mix(s, C0, EASE.move(clamp01((lt - AT.back[0]) / (AT.back[1] - AT.back[0]))));
  return s;
}

export function render3d(lt) {
  if (!ready) return null;
  const cs = camState(lt), pos = sph(cs.tg, cs.dist, cs.az, cs.el);
  camera.fov = cs.vfov; camera.updateProjectionMatrix();
  camera.position.set(...pos);
  // 在实拍机位附近使用实拍的 up 向量（含轻微滚转），离开后过渡到世界竖直
  const w = clamp01(1 - Math.abs(cs.az - C0.az) / 20);
  camera.up.set(lerp(0, CAM0.up[0], w), lerp(1, CAM0.up[1], w), lerp(0, CAM0.up[2], w)).normalize();
  camera.lookAt(...cs.tg);

  // 路线
  for (const side of ['red', 'blue']) {
    const pr = progress(side, lt), pre = clamp01((lt - AT.spawn) / 0.5);
    trails[side].forEach((tr, k) => {
      tr.ghost.material.opacity = 0.28 * pre * (lt > AT.back[0] ? 1 - clamp01((lt - AT.back[0]) / 0.6) : 1);
      const frac = k < (pr.leg) ? 1 : k > pr.leg ? 0 : pr.s / tr.R.len;
      tr.lit.geometry.setDrawRange(0, Math.floor(tr.count * frac / 6) * 6);
      tr.lit.visible = lt < AT.back[0] + 0.6;
    });
  }
  // 机器人
  const inClash = lt >= AT.clash[0] && lt < AT.clash[1];
  for (const side of ['red', 'blue']) {
    const b = bots[side], pr = progress(side, lt), u = b.userData;
    let [x, y] = along(pr.R, pr.s); const q = along(pr.R, pr.s + 1.5), q0 = along(pr.R, Math.max(0, pr.s - 1.5));
    let heading = Math.atan2(-(q[1] - q0[1]), q[0] - q0[0]);
    if (pr.s < 0.01 && pr.leg === 0) heading = side === 'red' ? Math.PI / 2 : -Math.PI / 2;
    if (inClash) {
      const c = lt - AT.clash[0], push = Math.sin(c * 9) * 1.6 * (1 - c / 1.4);
      const d = [MEET.blue[0] - MEET.red[0], MEET.blue[1] - MEET.red[1]], n = Math.hypot(...d);
      const base = MEET[side]; x = base[0] + d[0] / n * push; y = base[1] + d[1] / n * push;
      heading = Math.atan2(-(d[1]) * (side === 'red' ? 1 : -1), d[0] * (side === 'red' ? 1 : -1));
    }
    const app = EASE.enter(clamp01((lt - AT.spawn) / 0.4));
    b.visible = app > 0.01 && lt < AT.back[0] + 0.5;
    const ph = lt * 2 * Math.PI * 2.4 + (side === 'red' ? 0 : 1.4), mv = pr.moving || inClash ? 1 : 0.15;
    const p = P(x, y);
    b.position.set(p.x, Math.abs(Math.sin(ph)) * 0.6 * mv + (1 - app) * 25, p.z);
    b.rotation.set(0, heading, 0);
    b.rotateX(0.13 * Math.sin(ph) * mv);            // 左右摇晃
    b.rotateY(0.08 * Math.sin(ph * 0.5) * mv);
    b.scale.setScalar(1.35 * lerp(0.6, 1, app));
    u.feet.forEach((f, i) => { const s = Math.sin(ph + i * Math.PI); f.position.y = 0.6 + Math.max(0, s) * 1.2 * mv; f.position.x = 0.4 + s * 0.9 * mv; });
    // 出拳：对打时连打，击球时一记
    let punch = 0;
    if (inClash) punch = Math.max(0, Math.sin((lt - AT.clash[0]) * 13 + (side === 'red' ? 0 : 1.7)));
    const hd = lt - AT.hit[side]; if (hd > -0.2 && hd < 0.35) punch = Math.sin(clamp01((hd + 0.2) / 0.55) * Math.PI);
    if (side === 'red') u.arm.position.x = punch * 3.5; else u.arm.rotation.y = -punch * 1.2;
  }
  // 球：被击中后脱落、弹跳；之前呼吸光圈
  for (const side of ['red', 'blue']) {
    const { ball, halo, home } = balls[side], hd = lt - AT.hit[side];
    halo.material.opacity = lt > AT.clash[1] && hd < 0 ? 0.5 + 0.4 * Math.sin(lt * 12) : 0;
    halo.scale.setScalar(1 + 0.12 * Math.sin(lt * 12));
    if (hd < 0) { ball.position.copy(home); ball.scale.setScalar(1); }
    else {
      const dir = side === 'red' ? [-1, 0.35] : [1, -0.35], v = 28;
      const tt = hd, x = home.x + dir[0] * v * Math.min(tt, 0.9) * (1 - 0.3 * Math.min(tt, 0.9)), z = home.z + dir[1] * v * Math.min(tt, 0.9);
      // 落地 + 两次弹跳
      const g = 980, t1 = Math.sqrt(2 * (BALL_H - BALL_R) / g);
      let yy; if (tt < t1) yy = BALL_H - 0.5 * g * tt * tt; else { const k = tt - t1, v1 = g * t1 * 0.45, t2 = 2 * v1 / g; yy = BALL_R + (k < t2 ? v1 * k - 0.5 * g * k * k : Math.max(0, v1 * 0.4 * (k - t2) - 0.5 * g * (k - t2) ** 2)); }
      ball.position.set(x, Math.max(BALL_R, yy), z);
    }
    ball.visible = lt < AT.back[0] + 0.5 || true;
    if (lt >= AT.back[1] - 0.3) { ball.position.copy(home); }
  }
  // 火花
  const sp = inClash ? 1 : 0, m = P((MEET.red[0] + MEET.blue[0]) / 2, (MEET.red[1] + MEET.blue[1]) / 2);
  sparks.children.forEach((s, i) => {
    if (!sp) { s.visible = false; return; }
    const c = lt - AT.clash[0], k = Math.floor(c * 12), R = rng(5000 + i * 97 + k * 13), life = (c * 12) % 1;
    const a = R() * 6.283, el = R() * 1.2, sp0 = 6 + R() * 10;
    s.visible = R() > 0.25; s.position.set(m.x + Math.cos(a) * Math.cos(el) * sp0 * life, 12 + Math.sin(el) * sp0 * life - 6 * life * life, m.z + Math.sin(a) * Math.cos(el) * sp0 * life);
    s.scale.setScalar(1.4 * (1 - life));
  });
  renderer.render(scene, camera);
  return renderer.domElement;
}

// 3D 点 → 屏幕坐标（给 2D 叠层定位标签）
export function project3d(X, Y, h = 0) {
  const v = P(X, Y); v.y = h; v.project(camera);
  return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H, v.z < 1];
}
export const SPOTS = { PAD, BALL, MEET };
