import argparse, shutil
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser()
p.add_argument("--db",required=True); p.add_argument("--destino",required=True); p.add_argument("--manter",type=int,default=30)
a=p.parse_args(); db=Path(a.db); dest=Path(a.destino); dest.mkdir(parents=True,exist_ok=True)
if not db.exists(): raise SystemExit("Banco não encontrado.")
out=dest/f"raft_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2(db,out)
files=sorted(dest.glob("raft_backup_*.db"),key=lambda x:x.stat().st_mtime,reverse=True)
for old in files[a.manter:]: old.unlink()
print(out)
