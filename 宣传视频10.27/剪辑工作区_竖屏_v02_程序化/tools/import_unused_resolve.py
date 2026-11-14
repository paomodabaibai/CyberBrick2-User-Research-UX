# 把「已命名素材」里时间线没用到的素材导入达芬奇媒体池：未使用素材/视频、照片、音频
import sys, json, pathlib
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect
ROOT = pathlib.Path(__file__).resolve().parents[1]; SRC = ROOT.parent / '已命名素材'
data = json.loads((ROOT / '达芬奇交接' / 'v04_剪辑骨架.json').read_text(encoding='utf-8'))
used = {pathlib.Path(c['path']).stem.split('__')[-1].split('_')[0] for c in data['clips']}
groups = {'视频': [], '照片': [], '音频': []}
for p in sorted(SRC.iterdir(), key=lambda p: p.stem.split('__')[-1]):
    i = p.stem.split('__')[-1]
    if i in used or not i[:1] in 'VP': continue
    ext = p.suffix.lower()
    groups['视频' if ext == '.mp4' else '照片' if ext in ('.jpg', '.png') else '音频' if ext in ('.mp3', '.wav', '.m4a') else '其他'].append(str(p))
resolve = connect(require_enabled=False, timeout=60)
proj = resolve.GetProjectManager().GetCurrentProject(); mp = proj.GetMediaPool()
print('工程', proj.GetName(), '已用', sorted(used))
root = mp.GetRootFolder()
top = next((f for f in root.GetSubFolderList() if f.GetName() == '未使用素材'), None) or mp.AddSubFolder(root, '未使用素材')
for name, files in groups.items():
    if not files: continue
    sub = next((f for f in top.GetSubFolderList() if f.GetName() == name), None) or mp.AddSubFolder(top, name)
    have = {c.GetName() for c in sub.GetClipList()}
    todo = [f for f in files if pathlib.Path(f).name not in have]
    mp.SetCurrentFolder(sub)
    got = mp.ImportMedia(todo) if todo else []
    print(name, '应导入', len(files), '本次导入', len(got or []), '文件夹内共', len(sub.GetClipList()))
mp.SetCurrentFolder(root)
print('保存', resolve.GetProjectManager().SaveProject())
