import sqlite3
from pathlib import Path
import tempfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from db.migrate import rodar_migracoes

def test_views_and_indexes():
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/"test.db"; rodar_migracoes(db)
        conn=sqlite3.connect(db)
        views={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view'")}
        assert {"vw_bobina_saldo","vw_movimentacao_detalhada","vw_estoque_consolidado"} <= views
        indexes={r[1] for r in conn.execute("PRAGMA index_list('fact_controle_utilizacao')")}
        assert "uq_ctrl_utilizacao" in indexes
        conn.close()

def test_foreign_keys_are_enabled():
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/"test.db"; rodar_migracoes(db)
        conn=sqlite3.connect(db); conn.execute("PRAGMA foreign_keys=ON")
        try:
            conn.execute("INSERT INTO fact_controle_utilizacao(bobina_lote,utilizacao,data,hora,usuario) VALUES('X',1,'2026-01-01','10:00','t')")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("FK deveria impedir bobina inexistente")
        conn.close()
