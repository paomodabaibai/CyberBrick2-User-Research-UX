from pathlib import Path
import csv,hashlib,zipfile
P=Path(__file__).resolve().parent.parent
source=(P/'制作记录/finalize_pack.py').read_text(encoding='utf-8')
tail=source[source.index("with (P/'制作记录/文件校验_SHA256.csv')"):source.index("print('VERIFIED'")]
exec(tail)
print('ARCHIVE_REFRESHED',round(P.with_suffix('.zip').stat().st_size/1024**2,1),'MB')
