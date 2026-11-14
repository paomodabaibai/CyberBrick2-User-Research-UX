// 棋甲对决｜抖音竖屏 v04：程序化剪辑时间轴（纯数据，浏览器和 node 都能 import）
// 镜头 shots：src = 素材 ID；seg = 变速段 [源入点, 源出点, 速度] 或定格 [源时间, 源时间, 0, 时长]
// cam：镜头内推拉 {t: 镜头内秒, z: 相对铺满的缩放, c: [源画面焦点 x, y 归一化], e: 缓动}
// fx：shake 震屏 / flash 白闪；overlays 用全片绝对时间
import { AT, CAPS } from './arena3d.js';
export const FPS = 30, W = 1080, H = 1920;

const S = [
  // ---- 0 钩子：扇巴掌 → 扑倒 → 全场笑 ----
  { id: 'hook_slap', src: 'V05', seg: [[44.30, 44.63, 1], [44.63, 44.63, 0, 0.32], [44.63, 45.02, 1]],
    cam: [{ t: 0, z: 1.12, c: [0.5, 0.5] }, { t: 0.33, z: 1.2, c: [0.5, 0.45] }, { t: 0.36, z: 1.45, c: [0.5, 0.42], e: 'out' }, { t: 0.66, z: 1.5, c: [0.5, 0.42] }, { t: 0.7, z: 1.15, c: [0.5, 0.5], e: 'out' }],
    fx: { flash: [{ t: 0.33, d: 0.18 }], shake: [{ t: 0.33, a: 34, d: 0.4 }] }, sfx: [{ t: 0.33, k: 'slap' }], gain: 1.0 },
  { id: 'hook_ko', src: 'V05', seg: [[78.22, 78.55, 1], [78.55, 79.15, 0.5], [79.15, 79.45, 1]],
    cam: [{ t: 0, z: 1.25, c: [0.42, 0.58] }, { t: 0.33, z: 1.32, c: [0.46, 0.6] }, { t: 1.4, z: 1.6, c: [0.52, 0.62] }, { t: 1.83, z: 1.66, c: [0.52, 0.62] }],
    fx: { shake: [{ t: 0.9, a: 26, d: 0.45 }], flash: [{ t: 0.9, d: 0.12 }] }, sfx: [{ t: 0, k: 'whoosh' }, { t: 0.9, k: 'boom' }], gain: 1.0 },
  { id: 'hook_laugh', src: 'V28', seg: [[48.45, 50.1, 1]],
    cam: [{ t: 0, z: 1.5, c: [0.42, 0.3] }, { t: 1.65, z: 1.22, c: [0.45, 0.36], e: 'drift' }], gain: 1.25 },

  // ---- 1 介绍：接过手柄 → 近身对打 ----
  { id: 'intro_pad', src: 'V32', seg: [[0.2, 4.0, 1]],
    cam: [{ t: 0, z: 1.18, c: [0.3, 0.32] }, { t: 3.8, z: 1.04, c: [0.35, 0.38], e: 'drift' }], sfx: [{ t: 0, k: 'whoosh' }], gain: 0.7 },
  { id: 'intro_fight', src: 'V05', seg: [[70.2, 75.0, 1]],
    cam: [{ t: 0, z: 1.05, c: [0.5, 0.55] }, { t: 4.8, z: 1.3, c: [0.55, 0.6], e: 'drift' }], gain: 0.8 },

  // ---- 2 角色：蓝巴掌 → 红拳头怼镜头 → VS ----
  { id: 'blue', src: 'V03', seg: [[1.6, 5.8, 1]],
    cam: [{ t: 0, z: 1.0, c: [0.5, 0.5] }, { t: 4.2, z: 1.18, c: [0.5, 0.42], e: 'drift' }], sfx: [{ t: 0, k: 'whoosh' }], gain: 0.8 },
  { id: 'red', src: 'V07', seg: [[14.6, 17.2, 1], [17.2, 17.75, 0.7]],
    cam: [{ t: 0, z: 1.0, c: [0.5, 0.5] }, { t: 3.39, z: 1.3, c: [0.52, 0.5], e: 'in' }],
    fx: { shake: [{ t: 3.25, a: 30, d: 0.3 }] }, sfx: [{ t: 3.3, k: 'boom' }], gain: 0.8 },
  { id: 'vs', src: 'P09', fit: 'contain', cy: 820, seg: [[0, 0, 0, 2.2]],
    cam: [{ t: 0, z: 1.08, c: [0.5, 0.52] }, { t: 2.2, z: 1.18, c: [0.5, 0.52], e: 'drift' }],
    fx: { flash: [{ t: 0, d: 0.22 }], shake: [{ t: 0.28, a: 22, d: 0.35 }] }, sfx: [{ t: 0.28, k: 'boom' }], gain: 0 },

  // ---- 3 玩法：3D 规则动画（从实拍机位起飞、落回实拍机位）→ 真实对局 → 中间开打 → 一拳打掉球 → 围观反应 ----
  { id: 'map', src: 'V02', render: 'arena3d', seg: [[2.5, 2.95, 1], [2.95, 2.95, 0, AT.end - 0.45]], cam: [{ t: 0, z: 1, c: [0.5, 0.5] }],
    fx: { flash: [{ t: AT.end - 0.14, d: 0.14 }] },
    sfx: [{ t: AT.fly[0] + 0.3, k: 'whoosh' }, { t: AT.spawn, k: 'tick' }, { t: AT.spawn + 0.12, k: 'tick' }, { t: AT.meet, k: 'boom' }, { t: AT.hit.red, k: 'ding' }, { t: AT.hit.blue, k: 'tick' }, { t: AT.back[0] + 0.2, k: 'whoosh' }], gain: 0.4 },
  { id: 'real', src: 'V02', fit: 'band', seg: [[38.0, 44.5, 1]],
    cam: [{ t: 0, z: 1.0, c: [0.5, 0.5] }, { t: 1.0, z: 1.0, c: [0.5, 0.5] }, { t: 6.5, z: 2.3, c: [0.48, 0.47], e: 'drift' }],
    fx: { flash: [{ t: 0, d: 0.3 }] }, gain: 0.9 },
  { id: 'clash', src: 'V06', seg: [[10.6, 15.0, 1]],
    cam: [{ t: 0, z: 1.35, c: [0.45, 0.42] }, { t: 4.4, z: 1.6, c: [0.47, 0.42], e: 'drift' }], sfx: [{ t: 0, k: 'whoosh' }], gain: 0.9 },
  { id: 'ball', src: 'V04', seg: [[67.9, 70.38, 1], [70.38, 70.78, 0.32], [70.78, 71.4, 1]],
    cam: [{ t: 0, z: 1.0, c: [0.47, 0.5] }, { t: 2.48, z: 1.2, c: [0.45, 0.52] }, { t: 3.7, z: 1.38, c: [0.43, 0.62], e: 'out' }, { t: 4.35, z: 1.4, c: [0.43, 0.62] }],
    fx: { shake: [{ t: 2.5, a: 18, d: 0.3 }] }, sfx: [{ t: 0, k: 'whoosh' }, { t: 2.5, k: 'ding' }], gain: 0.8 },
  { id: 'react', src: 'V30', seg: [[80.0, 85.5, 1]],
    cam: [{ t: 0, z: 1.0, c: [0.45, 0.4] }, { t: 5.5, z: 1.12, c: [0.47, 0.38], e: 'drift' }], gain: 1.1 },

  // ---- 4 制作：手里的巴掌 → 打印件快切 → 装配 ----
  { id: 'palm', src: 'V35', seg: [[0.1, 2.3, 1]],
    cam: [{ t: 0, z: 1.05, c: [0.45, 0.5] }, { t: 2.2, z: 1.18, c: [0.45, 0.45], e: 'drift' }], sfx: [{ t: 0, k: 'whoosh' }], gain: 0.5 },
  { id: 'p19', src: 'P19', seg: [[0, 0, 0, 0.62]], cam: [{ t: 0, z: 1.2, c: [0.5, 0.5] }, { t: 0.62, z: 1.08, c: [0.5, 0.5] }], sfx: [{ t: 0, k: 'tick' }], gain: 0 },
  { id: 'p32', src: 'P32', seg: [[0, 0, 0, 0.62]], cam: [{ t: 0, z: 1.2, c: [0.55, 0.5] }, { t: 0.62, z: 1.08, c: [0.55, 0.5] }], sfx: [{ t: 0, k: 'tick' }], gain: 0 },
  { id: 'p33', src: 'P33', seg: [[0, 0, 0, 0.62]], cam: [{ t: 0, z: 1.2, c: [0.45, 0.5] }, { t: 0.62, z: 1.08, c: [0.45, 0.5] }], sfx: [{ t: 0, k: 'tick' }], gain: 0 },
  { id: 'p14', src: 'P14', seg: [[0, 0, 0, 0.7]], cam: [{ t: 0, z: 1.2, c: [0.55, 0.5] }, { t: 0.7, z: 1.08, c: [0.55, 0.5] }], sfx: [{ t: 0, k: 'tick' }], gain: 0 },
  { id: 'build', src: 'V47', seg: [[3.6, 5.8, 1]],
    cam: [{ t: 0, z: 1.1, c: [0.6, 0.62] }, { t: 2.2, z: 1.22, c: [0.62, 0.62], e: 'drift' }], sfx: [{ t: 0, k: 'tick' }], gain: 0.5 },

  // ---- 5 活动：大家围着玩 → 落版 ----
  { id: 'crowd', src: 'V28', seg: [[74.0, 79.0, 1]],
    cam: [{ t: 0, z: 1.0, c: [0.5, 0.5] }, { t: 5.0, z: 1.14, c: [0.5, 0.45], e: 'drift' }], sfx: [{ t: 0, k: 'whoosh' }], gain: 0.9 },
  { id: 'end', src: 'P07', seg: [[0, 0, 0, 6.0]],
    cam: [{ t: 0, z: 1.0, c: [0.5, 0.5] }, { t: 6.0, z: 1.08, c: [0.5, 0.5], e: 'drift' }], fx: { flash: [{ t: 0, d: 0.2 }] }, sfx: [{ t: 0.15, k: 'boom' }, { t: 0.95, k: 'ding' }], gain: 0 },
];

// 时间轴位置
export const shots = []; export const T = {};
let at = 0;
for (const s of S) {
  const segs = s.seg.map(([a, b, v, d]) => ({ a, b, v, d: v ? (b - a) / v : d }));
  const dur = segs.reduce((x, g) => x + g.d, 0);
  shots.push({ ...s, segs, start: at, dur });
  T[s.id] = at; at += dur;
}
export const duration = at;

// 镜头内时间 → 源时间
export function srcTime(shot, lt) {
  let acc = 0;
  for (const g of shot.segs) {
    if (lt < acc + g.d || g === shot.segs[shot.segs.length - 1]) return g.v ? Math.min(g.b, g.a + (lt - acc) * g.v) : g.a;
    acc += g.d;
  }
}

const sub = (a, b, text) => ({ k: 'sub', at: a, out: b, text });
// 叠层（全片时间）。字幕 = 口播稿，录配音时对着字幕念；没有配音时它就是字幕
export const overlays = [
  // 钩子
  { k: 'title', at: 0.12, out: T.intro_pad - 0.25, x: 80, y: 360, style: 'rise', lines: [{ text: '我们上课做的机器人', size: 76, font: 'tech', color: '#fff' }, { text: '打起来了', size: 180, font: 'tech', color: '#ffd400', dy: 190 }] },
  { k: 'burst', at: T.hook_slap + 0.33, out: T.hook_slap + 1.0, text: '啪！', x: 700, y: 980, r: 150, rot: -0.18 },
  { k: 'ko', at: T.hook_ko + 0.9, out: T.hook_laugh + 0.05, x: 540, y: 1180 },

  // 介绍
  sub(T.intro_pad + 0.2, T.intro_pad + 3.6, '大家好，我们做了一个格斗机器人'),
  sub(T.intro_fight + 0.2, T.intro_fight + 4.4, '拉上朋友，就能一对一开打'),
  { k: 'tag', at: T.intro_fight + 0.3, out: T.blue - 0.15, x: 80, y: 360, text: '一对一 · 真人手柄操控' },

  // 角色
  { k: 'banner', at: T.blue + 0.15, out: T.red - 0.05, side: 'blue', en: 'BLUE', title: '巴掌', sub: '舵机驱动 · 抡圆了扇' },
  { k: 'banner', at: T.red + 0.1, out: T.vs - 0.02, side: 'red', en: 'RED', title: '拳头', sub: '电机驱动 · 往复直拳' },
  sub(T.blue + 0.1, T.red - 0.1, '我们是清华的一个课程小组'),
  sub(T.red + 0.1, T.vs + 2.0, '蓝色是巴掌，红色是拳头'),
  { k: 'vs', at: T.vs, out: T.map - 0.02 },

  // 规则动画的分步标题
  ...CAPS.map(c => ({ k: 'step', at: T.map + c.at, out: T.map + c.out, n: c.n, text: c.text })),
  { k: 'label3d', at: T.map + AT.spawn, out: T.map + AT.go + 0.9, spot: 'pad', side: 'red', text: '红方起点' },
  { k: 'label3d', at: T.map + AT.spawn, out: T.map + AT.go + 0.9, spot: 'pad', side: 'blue', text: '蓝方起点' },
  { k: 'label3d', at: T.map + AT.clash[1] - 0.1, out: T.map + AT.hit.red - 0.35, spot: 'ball', side: 'red', text: '红方打红球' },
  { k: 'label3d', at: T.map + AT.clash[1] - 0.1, out: T.map + AT.hit.blue, spot: 'ball', side: 'blue', text: '蓝方打蓝球' },
  { k: 'label3d', at: T.map + AT.hit.red + 0.05, out: T.map + AT.back[0], spot: 'ball', side: 'red', text: '击中！', big: true },

  // 玩法
  { k: 'ring', at: T.ball + 2.0, out: T.ball + 3.9, shot: 'ball', pts: [[2.0, 0.425, 0.44], [2.48, 0.42, 0.47], [2.7, 0.40, 0.65], [3.17, 0.385, 0.67], [3.64, 0.40, 0.72], [3.9, 0.42, 0.74]] },
  { k: 'burst', at: T.ball + 2.55, out: T.ball + 3.6, text: '打掉！', x: 770, y: 700, r: 140, rot: 0.14, color: '#ffd400' },
  sub(T.ball + 0.1, T.ball + 4.2, '一拳下去，球掉了！'),
  sub(T.real + 0.4, T.real + 6.2, '这是一局真实的对战'),
  { k: 'tag', at: T.real + 0.5, out: T.real + 6.2, x: 80, y: 360, text: '实战 · 无剪辑加速' },
  sub(T.clash + 0.2, T.clash + 4.4, '中间撞上了，就先打一架'),

  // 制作
  { k: 'title', at: T.p19 - 0.05, out: T.crowd - 0.3, x: 80, y: 420, style: 'slam', lines: [{ text: '全身', size: 100, font: 'tech', color: '#fff' }, { text: '3D 打印', size: 190, font: 'tech', color: '#fff', dy: 200 }], highlight: [{ line: 1, from: 0, to: 4, at: T.p19 + 0.35, mode: 'under', color: '#ffd400' }], shadow: true },
  sub(T.palm + 0.2, T.p14, '身上几乎每个零件'),
  sub(T.p14, T.crowd - 0.1, '都是我们自己 3D 打印出来的'),

  // 活动
  sub(T.crowd + 0.2, T.crowd + 4.6, '11月12号，北京拓竹线下旗舰店'),
  { k: 'dim', at: T.end, out: T.end + 6.0, a: 0.62, blur: 14 },
  { k: 'end', at: T.end + 0.15 },
];
