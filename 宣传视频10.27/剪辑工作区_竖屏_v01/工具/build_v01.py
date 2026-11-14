# 竖屏抖音初剪 v01：新建独立工程（已存在则重建时间线） -> 1080x1920@30 -> 按剪辑表铺时间线 -> 段落标记写入口播稿
import sys, os, glob
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect

SRC = r'E:\课程作业\大三上\张茫 用户研究与体验设计\宣传视频10.27\已命名素材'
PROJECT = '棋甲对决_竖屏抖音_v01'
TIMELINE = '棋甲对决 竖屏抖音 初剪v01'
FPS = 30

# (ID, 入点秒, 出点秒, 源帧率, 横拍平移px, 说明)
EDL = [
    ('V05', 45.0, 47.2, 29.97, 0,   '钩子：巴掌扇飞小红'),
    ('V28', 46.3, 49.8, 30,    0,   '钩子：小红倒地 全场爆笑'),
    ('V32', 0.5,  3.5,  29.97, 0,   '介绍：拿起手柄'),
    ('V05', 70.5, 74.5, 29.97, 0,   '介绍：双机近身对打'),
    ('V03', 2.5,  5.5,  29.97, 0,   '角色：蓝色巴掌'),
    ('V07', 15.8, 19.2, 29.97, 0,   '角色：红色拳头怼镜头'),
    ('V04', 67.5, 71.5, 30,    60, '高光：一拳击落目标球'),
    ('V05', 77.0, 80.0, 29.97, 0,   '高光：小红扑倒小蓝'),
    ('V01', 1.0,  3.0,  29,    0,   '细节：3D打印'),
    ('V35', 0.0,  3.0,  30,    0,   '细节：打印的巴掌拿在手上'),
    ('V47', 0.5,  3.0,  30,    0,   '细节：手工装配'),
    ('V28', 76.0, 80.0, 30,    0,   '收尾：大家围着玩'),
    ('P09', 0,    3.0,  30,    0,   'CTA：红蓝双机 + 活动信息'),
    ('P07', 0,    2.0,  30,    0,   '落款：团队合影'),
]
# 段落标记：(EDL序号, 颜色, 名称, 口播)
MARKERS = [
    (0,  'Red',    '0 钩子',   '（不配口播，留原声：啪 + 爆笑）'),
    (2,  'Blue',   '1 介绍',   '大家好，我们做了一个格斗机器人，拉上朋友就能一对一开打。'),
    (4,  'Cyan',   '2 亮点',   '我们是清华的一个课程小组，两台机器人：蓝色是巴掌，红色是拳头。'),
    (6,  'Yellow', '3 玩法',   '谁先把对面的球打下来谁就赢，当然，也可以直接把对手打趴。'),
    (8,  'Green',  '4 3D打印', '身上几乎每个零件都是我们自己3D打印出来的。'),
    (11, 'Purple', '5 活动',   '11月7号，北京拓竹线下旗舰店，我们带着它们等你来打一局。'),
]

CONV = r'E:\课程作业\大三上\张茫 用户研究与体验设计\宣传视频10.27\剪辑工作区_竖屏_v01_转换素材'
# 照片先转成定长视频（达芬奇API无法设定静帧时长），横拍/照片在竖屏中的缩放与平移
STILL = {'P09': 'P09_静帧3秒.mp4', 'P07': 'P07_静帧2秒.mp4'}
FILL = {'V04': (3.16, 60), 'V01': (2.2, 0), 'P09': (2.37, 0), 'P07': (1.25, 0)}

def find(id_):
    if id_ in STILL:
        return os.path.join(CONV, STILL[id_])
    m = [f for f in os.listdir(SRC) if f.split('__')[-1].split('.')[0] == id_]
    assert len(m) == 1, (id_, m)
    return os.path.join(SRC, m[0])

resolve = connect(require_enabled=False, timeout=30)
pm = resolve.GetProjectManager()
cur = pm.GetCurrentProject()
print('save current:', cur.GetName(), pm.SaveProject())
proj = pm.CreateProject(PROJECT) or pm.LoadProject(PROJECT)
assert proj
for k, v in [('timelineFrameRate', str(FPS)), ('timelineResolutionWidth', '1080'),
             ('timelineResolutionHeight', '1920'), ('timelinePlaybackFrameRate', str(FPS)),
             ('timelineInputResMismatchBehavior', 'scaleFullFrameWithCrop')]:
    print(k, proj.SetSetting(k, v), proj.GetSetting(k))

mp = proj.GetMediaPool()
ids = sorted({e[0] for e in EDL})
items = {}
for id_ in ids:
    old = [c for c in mp.GetRootFolder().GetClipList() if c.GetName() == os.path.basename(find(id_))]
    r = old or mp.ImportMedia([find(id_)])
    assert r, id_
    items[id_] = r[0]
for i in range(proj.GetTimelineCount(), 0, -1):
    t = proj.GetTimelineByIndex(i)
    if t.GetName() == TIMELINE:
        mp.DeleteTimelines([t])
tl = mp.CreateEmptyTimeline(TIMELINE)
proj.SetCurrentTimeline(tl)

starts = []
for id_, a, b, sfps, pan, note in EDL:
    sf, ef = (0, int(round(b * FPS))) if id_ in STILL else (int(round(a * sfps)), int(round(b * sfps)))
    out = mp.AppendToTimeline([{'mediaPoolItem': items[id_], 'startFrame': sf, 'endFrame': ef}])
    v = [t for t in out if t.GetTrackTypeAndIndex()[0] == 'video'][0]
    starts.append(v.GetStart() - tl.GetStartFrame())
    if id_ in FILL:
        z, p = FILL[id_]
        v.SetProperty('ZoomX', z); v.SetProperty('ZoomY', z); v.SetProperty('Pan', p)
    print(id_, a, b, '->', starts[-1], v.GetDuration(), note)
rec = tl.GetEndFrame() - tl.GetStartFrame()

for idx, color, name, vo in MARKERS:
    print('marker', name, tl.AddMarker(starts[idx], color, name, vo, 1))
print('total sec', rec / FPS)
print('save:', pm.SaveProject())
