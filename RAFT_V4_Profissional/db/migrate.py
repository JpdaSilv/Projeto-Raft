"""Bootstrap/migração idempotente do banco RAFT V4."""
import argparse,sqlite3
from pathlib import Path
from config import DB_PATH

MIGRATIONS_DIR=Path(__file__).resolve().parent/"migrations"

def rodar_migracoes(db_path=None):
    path=Path(db_path or DB_PATH); path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path,timeout=30)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=15000")
        schema=(MIGRATIONS_DIR/"0001_initial.sql").read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()
        row=conn.execute("SELECT 1 FROM schema_migrations WHERE arquivo='0001_initial.sql'").fetchone()
        if not row:
            conn.execute("INSERT INTO schema_migrations(arquivo) VALUES('0001_initial.sql')")
        # Reaplica índices/views de hardening de forma idempotente.
        hard=(MIGRATIONS_DIR/"0002_hardening.sql").read_text(encoding="utf-8")
        conn.executescript(hard)
        if not conn.execute("SELECT 1 FROM schema_migrations WHERE arquivo='0002_hardening.sql'").fetchone():
            conn.execute("INSERT INTO schema_migrations(arquivo) VALUES('0002_hardening.sql')")
        conn.commit()
    finally: conn.close()

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--db",default=str(DB_PATH)); a=p.parse_args()
    rodar_migracoes(a.db); print(f"Banco atualizado: {Path(a.db).resolve()}")
