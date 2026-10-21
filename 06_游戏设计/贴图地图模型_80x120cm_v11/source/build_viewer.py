from pathlib import Path
import json,base64
ROOT=Path(__file__).resolve().parents[1]
scene=json.loads((ROOT/'source'/'scene.json').read_text(encoding='utf-8'))
paths={m['texture'] for m in scene['materials'] if m.get('texture')}
textures={p:'data:image/png;base64,'+base64.b64encode((ROOT/p).read_bytes()).decode('ascii') for p in paths}
template=(ROOT/'source'/'viewer_template.html').read_text(encoding='utf-8')
result=template.replace('__SCENE_JSON__',json.dumps(scene,ensure_ascii=False,separators=(',',':'))).replace('__TEXTURE_JSON__',json.dumps(textures,separators=(',',':')))
(ROOT/'地图3D预览.html').write_text(result,encoding='utf-8')
print(f'Offline viewer: {len(result):,} characters; {len(paths)} embedded textures')
