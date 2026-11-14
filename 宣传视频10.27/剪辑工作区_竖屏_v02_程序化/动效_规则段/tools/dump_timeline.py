import json, sys, time
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect

resolve = connect(require_enabled=False, timeout=60)
pm = resolve.GetProjectManager()
p = pm.GetCurrentProject()
print('工程', p.GetName(), '时间线数', p.GetTimelineCount(), '已保存时间', time.strftime('%H:%M'))
for i in range(1, p.GetTimelineCount() + 1):
    t = p.GetTimelineByIndex(i)
    print(' TL', i, t.GetName(), t.GetStartFrame(), t.GetEndFrame())
tl = p.GetCurrentTimeline()
t0 = tl.GetStartFrame()
fps = float(tl.GetSetting('timelineFrameRate'))
print('当前', tl.GetName(), 'fps', fps, '起', t0, '止', tl.GetEndFrame(), '分辨率', tl.GetSetting('timelineResolutionWidth'), tl.GetSetting('timelineResolutionHeight'), '播放头', tl.GetCurrentTimecode())
sec = lambda f: round((f - t0) / fps, 2)
out = {'project': p.GetName(), 'timeline': tl.GetName(), 'fps': fps, 'start': t0, 'end': tl.GetEndFrame(), 'tracks': {}}
for kind in ('video', 'audio', 'subtitle'):
    for n in range(1, tl.GetTrackCount(kind) + 1):
        items = tl.GetItemListInTrack(kind, n) or []
        name = tl.GetTrackName(kind, n)
        print(f'\n== {kind}{n} 「{name}」 {len(items)} 条 启用={tl.GetIsTrackEnabled(kind, n)}')
        rows = []
        for x in items:
            row = {'name': x.GetName(), 'start': x.GetStart(), 'end': x.GetEnd(), 't0': sec(x.GetStart()), 't1': sec(x.GetEnd()), 'dur': round(x.GetDuration() / fps, 2)}
            if kind != 'subtitle':
                mpi = x.GetMediaPoolItem()
                row['path'] = mpi.GetClipProperty('File Path') if mpi else None
                row['in'], row['out'] = x.GetSourceStartFrame(), x.GetSourceEndFrame()
                row['clip_fps'] = mpi.GetClipProperty('FPS') if mpi else None
            if kind == 'video':
                row['enabled'] = x.GetClipEnabled()
                row['speed'] = x.GetProperty('Speed') if False else None
                row['zoom'] = x.GetProperty('ZoomX'); row['pan'] = x.GetProperty('Pan'); row['tilt'] = x.GetProperty('Tilt')
                row['color'] = x.GetClipColor()
                row['markers'] = {str(k): v.get('name') for k, v in (x.GetMarkers() or {}).items()}
            if kind == 'audio':
                row['volume'] = x.GetProperty('Volume')
            rows.append(row)
            base = (row.get('path') or '').split('\\')[-1][-34:]
            if kind == 'subtitle':
                print(f"{row['t0']:7.2f} {row['t1']:7.2f} {row['name']}")
            else:
                print(f"{row['t0']:7.2f} {row['t1']:7.2f} ({row['dur']:6.2f}) in={row['in']} out={row['out']} {row['name'][:40]} | {base} {row.get('markers') or ''} {'zoom=%.2f pan=%.0f tilt=%.0f' % (row['zoom'], row['pan'], row['tilt']) if kind == 'video' and row['zoom'] is not None else ''} {'' if kind != 'video' or row['enabled'] else 'DISABLED'}")
        out['tracks'][f'{kind}{n}'] = {'name': name, 'items': rows}
tm = tl.GetMarkers() or {}
print('\n时间线标记', {sec(t0 + int(k)): (v.get('name'), v.get('note')) for k, v in tm.items()})
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
