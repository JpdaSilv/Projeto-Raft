"""Backup automático consistente do SQLite."""
import argparse,sqlite3
from pathlib import Path
from datetime import datetime

p=argparse.ArgumentParser()
p.add_argument("--db",required=True); p.add_argument("--destino",required=True); p.add_argument("--manter",type=int,default=30)
a=p.parse_args(); db=Path(a.db); dest=Path(a.destino); dest.mkdir(parents=True,exist_ok=True)
if not db.exists(): raise SystemExit("Banco não encontrado.")
out=dest/f"raft_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
src=sqlite3.connect(db); dst=sqlite3.connect(out)
try: src.backup(dst)
finally: dst.close(); src.close()
files=sorted(dest.glob("raft_backup_*.db"),key=lambda x:x.stat().st_mtime,reverse=True)
for old in files[max(a.manter,0):]: old.unlink()
print(out)
