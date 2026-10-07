from pathlib import Path
p = Path(__file__).resolve().parent
html = (p/'preview_template.html').read_text(encoding='utf-8').replace('__MESH_DATA__', (p/'preview_meshes.json').read_text(encoding='utf-8'))
dest = Path(r'C:\Users\Administrator\.codex\visualizations\2026\09\14\01a09d93-5828-7951-8f50-b4e4bdacf50a\otto-fist-proportions.html')
dest.write_text(html, encoding='utf-8')
assert dest.stat().st_size < 1024*1024
print(dest.stat().st_size)
