# 把达芬奇当前工程媒体池里来自「已命名素材」的片段，替换成「已命名素材_达芬奇转码」里的 .mov
# 用法：python relink_transcoded_resolve.py [V05 V28 ...]   不带参数=能换的全换。先导出 .drp 备份。
import sys, time, pathlib
sys.path.insert(0, r'E:\Agent工作坊\tools\davinci-resolve-mcp')
from src.utils.resolve_bridge_client import connect
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT.parent / '已命名素材').resolve(); DST = ROOT.parent / '已命名素材_达芬奇转码'
only = set(sys.argv[1:])

resolve = connect(require_enabled=False, timeout=60)
pm = resolve.GetProjectManager(); proj = pm.GetCurrentProject(); mp = proj.GetMediaPool()
bak = ROOT / '达芬奇交接' / f'{proj.GetName()}_换转码前备份_{time.strftime("%m%d_%H%M")}.drp'
print('工程', proj.GetName(), '备份', pm.ExportProject(proj.GetName(), str(bak)), bak.name)

def walk(folder):
    yield from folder.GetClipList()
    for sub in folder.GetSubFolderList(): yield from walk(sub)

done, skip = [], []
for clip in walk(mp.GetRootFolder()):
    path = clip.GetClipProperty('File Path') or ''
    if not path: continue
    p = pathlib.Path(path)
    if p.parent.resolve() != SRC: continue
    vid = p.stem.split('__')[-1]
    if only and vid not in only: continue
    new = DST / (p.stem + '.mov')
    if not new.exists(): skip.append(vid); continue
    ok = clip.ReplaceClip(str(new))
    (done if ok else skip).append(vid if ok else vid + '(失败)')
print('已替换', len(done), sorted(done)); print('未替换', sorted(skip))
print('保存', pm.SaveProject())
