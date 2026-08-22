"""Inicialização e migração idempotente do banco RAFT."""
import argparse, sqlite3
from pathlib import Path
from config import DB_PATH

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

# Colunas adicionadas após a primeira versão publicada.
COMPAT_COLUMNS = {
    "dim_produto": {
        "ativo": "INTEGER NOT NULL DEFAULT 1",
    },
    "dim_bobina_spec": {
        "ativo": "INTEGER NOT NULL DEFAULT 1",
    },
    "dim_bobina_fisica": {
        "status": "TEXT NOT NULL DEFAULT 'ESTOQUE'",
        "criado_em": "TEXT",
        "atualizado_em": "TEXT",
    },
    "dim_componente": {
        "ativo": "INTEGER NOT NULL DEFAULT 1",
    },
    "dim_pedido": {
        "ativo": "INTEGER NOT NULL DEFAULT 1",
    },
    "usuarios": {
        "ultimo_login": "TEXT",
    },
    "sessoes": {
        "id": "INTEGER",
        "token_hash": "TEXT",
        "revogado_em": "TEXT",
    },
    "fact_movimentacao": {
        "atualizado_em": "TEXT",
    },
    "snapshot_totvs": {
        "importacao_id": "TEXT",
        "local_fisico": "TEXT",
    },
}

def _cols(conn, table):
    return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}

def _ensure_compat_columns(conn):
    for table, columns in COMPAT_COLUMNS.items():
        existing = _cols(conn, table)
        if not existing:
            continue
        for col, ddl in columns.items():
            if col not in existing:
                # A tabela sessoes antiga possui token como PK. Não alteramos
                # esse campo; token_hash é complementar.
                conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {ddl}')
    conn.commit()

def _ensure_schema(conn):
    schema = (Path(__file__).resolve().parent / "migrations" / "0001_initial.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()

def rodar_migracoes(db_path=None):
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=15000")
    # Cria/normaliza tabelas e só depois executa os índices que dependem
    # de colunas adicionadas em versões anteriores.
    _ensure_compat_columns(conn)
    _ensure_schema(conn)
    _ensure_compat_columns(conn)
    conn.executescript(
        (MIGRATIONS_DIR / "0002_hardening.sql").read_text(encoding="utf-8")
    )
    conn.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=str(DB_PATH))
    args = p.parse_args()
    rodar_migracoes(args.db)
    print(f"Banco atualizado: {Path(args.db).resolve()}")
