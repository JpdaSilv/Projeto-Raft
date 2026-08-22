import sqlite3
from pathlib import Path
import tempfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from db.migrate import rodar_migracoes

def test_database_bootstrap():
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/"test.db"
        rodar_migracoes(db)
        conn=sqlite3.connect(db)
        tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"usuarios","fact_movimentacao","dim_bobina_fisica","audit_log","snapshot_totvs"} <= tables
        conn.close()
