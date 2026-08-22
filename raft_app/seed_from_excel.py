"""
seed_from_excel.py
-------------------
Cria banco/raft_app.db (se não existir), aplica o schema.sql e
carrega as tabelas de referência (dim_produto, dim_bobina, dim_componente)
a partir do Projeto.xlsm — exatamente como o pipeline principal
(extract.py / clean.py / load_sqlite.py) já faz para as stg_*.

Uso:
    python db/seed_from_excel.py --xlsm "caminho/para/Projeto.xlsm" --db "banco/raft_app.db"

Se você já usa banco/raft.db no projeto principal, rode apontando
--db para esse mesmo arquivo: as tabelas fact_* e dim_* são
adicionadas nele sem mexer nas stg_* existentes.
"""
import argparse
import sqlite3
from pathlib import Path
import pandas as pd


def carregar_dim_produto(xlsm_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsm_path, sheet_name="Especificação_Produtos", header=7)
    df = df.rename(columns={
        "Código": "codigo",
        "Descrição": "descricao",
        "Tipo de Telha": "tipo_telha",
        "Fator da bobina": "fator_bobina",
    })
    df = df[["codigo", "descricao", "tipo_telha", "fator_bobina"]]
    df = df.dropna(subset=["codigo"]).drop_duplicates(subset=["codigo"])
    return df


def carregar_dim_bobina_spec(xlsm_path: str) -> pd.DataFrame:
    """Catálogo de especificações de bobina (por Código, ex: '1.167M')."""
    df = pd.read_excel(xlsm_path, sheet_name="Especificação_Bobinas", header=7)
    df = df.rename(columns={
        "Código": "codigo",
        "Descrição": "descricao",
        "Desc. Curta": "desc_curta",
        "MEDIDA": "medida",
        "Esp.": "espessura",
        "Largura": "largura",
        "Tipo": "tipo",
        "Cor": "cor",
        "Face": "face",
        "Peso Específico": "peso_especifico",
        "Saldo Atual": "saldo_atual",
    })
    cols = ["codigo", "descricao", "desc_curta", "medida", "espessura",
            "largura", "tipo", "cor", "face", "peso_especifico", "saldo_atual"]
    df = df[cols]
    df = df.dropna(subset=["codigo"]).drop_duplicates(subset=["codigo"])
    return df


def carregar_dim_bobina_fisica(xlsm_path: str) -> pd.DataFrame:
    """Bobinas físicas em estoque (por Lote, ex: 'LL39100202'), aponta pro Código de especificação."""
    df = pd.read_excel(xlsm_path, sheet_name="Banco_Bobina", header=2)
    df = df.rename(columns={
        "Lote": "lote",
        "Código": "codigo_spec",
        "Galpão": "galpao",
        "Local Físico": "local_fisico",
        "N° Ref": "n_ref",
        "Peso Real": "peso_real",
        "Data Pesagem": "data_pesagem",
        "Data Validade": "data_validade",
    })
    cols = ["lote", "codigo_spec", "galpao", "local_fisico", "n_ref",
            "peso_real", "data_pesagem", "data_validade"]
    df = df[cols]
    df = df.dropna(subset=["lote"]).drop_duplicates(subset=["lote"])
    for c in ("data_pesagem", "data_validade"):
        df[c] = df[c].astype(str)
    return df


def carregar_dim_componente(xlsm_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsm_path, sheet_name="Especificação_Componentes", header=7)
    df = df.rename(columns={
        "Código": "codigo",
        "Descrição": "descricao",
        "Tipo": "tipo",
        "Esp.": "espessura",
        "Desc. Curta": "desc_curta",
        "Estoque atual": "estoque_atual",
    })
    df = df[["codigo", "descricao", "tipo", "espessura", "desc_curta", "estoque_atual"]]
    df = df.dropna(subset=["codigo"]).drop_duplicates(subset=["codigo"])
    return df


def carregar_dim_pedido(xlsm_path: str) -> pd.DataFrame:
    """Pedidos cadastrados (histórico do Excel). Uma linha por item de pedido —
    o mesmo número de Pedido pode repetir com produtos/OPs diferentes."""
    df = pd.read_excel(xlsm_path, sheet_name="Pedidos", header=1)
    df = df.rename(columns={
        "Pedido": "pedido",
        "OP": "op",
        "Cliente": "cliente",
        "Produto": "produto_codigo",
        "Metragem": "metragem",
        "Tipo Prod.": "tipo_prod",
        "Data": "data",
    })
    cols = ["pedido", "op", "cliente", "produto_codigo", "metragem", "tipo_prod", "data"]
    df = df[cols]
    df = df.dropna(subset=["pedido"])
    df["pedido"] = df["pedido"].astype(int).astype(str)
    df["op"] = df["op"].astype(str)
    df["data"] = df["data"].astype(str)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsm", required=True, help="Caminho do Projeto.xlsm")
    parser.add_argument("--db", default="banco/raft_app.db", help="Caminho do banco SQLite de destino")
    args = parser.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_path = Path(__file__).parent / "schema.sql"
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_path.read_text(encoding="utf-8"))

    print("Lendo dimensões do Excel...")
    dim_produto = carregar_dim_produto(args.xlsm)
    dim_bobina_spec = carregar_dim_bobina_spec(args.xlsm)
    dim_bobina_fisica = carregar_dim_bobina_fisica(args.xlsm)
    dim_componente = carregar_dim_componente(args.xlsm)
    dim_pedido = carregar_dim_pedido(args.xlsm)

    # IMPORTANTE: usamos DELETE + append (não to_sql(if_exists="replace")),
    # porque "replace" derruba a tabela e recria SEM a PRIMARY KEY definida
    # no schema.sql — e sem PK/UNIQUE as fact_* não conseguem referenciar
    # essas dimensões por foreign key (erro "foreign key mismatch").
    conn.execute("DELETE FROM dim_produto")
    conn.execute("DELETE FROM dim_bobina_fisica")  # depende de dim_bobina_spec -> apaga primeiro
    conn.execute("DELETE FROM dim_bobina_spec")
    conn.execute("DELETE FROM dim_componente")
    conn.execute("DELETE FROM dim_pedido")
    conn.commit()

    dim_produto.to_sql("dim_produto", conn, if_exists="append", index=False)
    dim_bobina_spec.to_sql("dim_bobina_spec", conn, if_exists="append", index=False)
    dim_bobina_fisica.to_sql("dim_bobina_fisica", conn, if_exists="append", index=False)
    dim_componente.to_sql("dim_componente", conn, if_exists="append", index=False)
    dim_pedido.to_sql("dim_pedido", conn, if_exists="append", index=False)
    conn.commit()

    print(f"OK -> {len(dim_produto)} produtos | {len(dim_bobina_spec)} specs de bobina | "
          f"{len(dim_bobina_fisica)} bobinas físicas | {len(dim_componente)} componentes | "
          f"{len(dim_pedido)} linhas de pedido")
    print(f"Banco criado/atualizado em: {db_path.resolve()}")
    conn.close()


if __name__ == "__main__":
    main()
