"""
db_utils.py — conexão e queries compartilhadas pelo app Streamlit.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "banco" / "raft_app.db"


def get_conn() -> sqlite3.Connection:
    """Conexão nova a cada chamada — evita problemas de thread do Streamlit."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute(sql: str, params: tuple = ()) -> int:
    """Executa INSERT/UPDATE/DELETE e retorna o lastrowid (ou rowcount)."""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


@st.cache_data(ttl=60)
def carregar_produtos() -> pd.DataFrame:
    return query_df("SELECT codigo, descricao, fator_bobina FROM dim_produto ORDER BY descricao")


@st.cache_data(ttl=60)
def carregar_bobinas_fisicas() -> pd.DataFrame:
    sql = """
        SELECT f.lote, f.codigo_spec, s.desc_curta, s.peso_especifico, f.peso_real, f.local_fisico
        FROM dim_bobina_fisica f
        LEFT JOIN dim_bobina_spec s ON s.codigo = f.codigo_spec
        ORDER BY f.lote
    """
    return query_df(sql)


@st.cache_data(ttl=60)
def carregar_componentes() -> pd.DataFrame:
    return query_df("SELECT codigo, descricao, desc_curta, tipo FROM dim_componente ORDER BY descricao")


def trimestre_de(mes: int) -> str:
    return f"T{((mes - 1) // 3) + 1}"


MESES_PT = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
}


def derivar_data(data) -> dict:
    """A partir de uma data, deriva Ano / Trimestre / Mês — como as colunas calculadas do Excel."""
    return {
        "ano": data.year,
        "trimestre": trimestre_de(data.month),
        "mes": MESES_PT[data.month],
    }
