"""
migrate.py — aplica migrações de schema em ordem, uma única vez cada.

Cada arquivo em db/migrations/NNNN_nome.sql roda uma vez só. O controle de
"o que já rodou" fica na tabela schema_migrations, dentro do próprio banco.
Isso resolve o problema de editar schema.sql direto: se você editar um
arquivo já aplicado, ele NÃO roda de novo — crie um arquivo novo (0002, 0003...)
com o ALTER TABLE / CREATE TABLE necessário.

Uso:
    python db/migrate.py --db banco/raft_app.db
"""
import argparse
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def garantir_tabela_controle(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo TEXT UNIQUE NOT NULL,
            aplicado_em TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.commit()


def aplicadas(conn: sqlite3.Connection) -> set:
    return {row[0] for row in conn.execute("SELECT arquivo FROM schema_migrations")}


def aplicar(conn: sqlite3.Connection, arquivo: Path):
    sql = arquivo.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.execute("INSERT INTO schema_migrations (arquivo) VALUES (?)", (arquivo.name,))
    conn.commit()


def rodar_migracoes(db_path: str):
    conn = sqlite3.connect(db_path)
    garantir_tabela_controle(conn)
    ja_aplicadas = aplicadas(conn)

    arquivos = sorted(MIGRATIONS_DIR.glob("*.sql"))
    pendentes = [a for a in arquivos if a.name not in ja_aplicadas]

    if not pendentes:
        print("Nenhuma migração pendente. Banco já está atualizado.")
    for arquivo in pendentes:
        print(f"Aplicando {arquivo.name}...")
        aplicar(conn, arquivo)
        print(f"  OK.")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="banco/raft_app.db")
    args = parser.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    rodar_migracoes(args.db)
