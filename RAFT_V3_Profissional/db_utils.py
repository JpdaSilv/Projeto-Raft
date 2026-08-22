"""Camada de persistência: conexões, transações, cache e consultas comuns."""
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn

@contextmanager
def transaction():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def query_df(sql, params=()):
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def scalar(sql, params=(), default=None):
    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()
        return default if row is None else row[0]

def execute(sql, params=()):
    with transaction() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid

def clear_caches():
    try:
        carregar_produtos.clear()
        carregar_bobinas_fisicas.clear()
        carregar_componentes.clear()
        carregar_pedidos.clear()
    except Exception:
        pass

@st.cache_data(ttl=30, show_spinner=False)
def carregar_produtos():
    return query_df("""
        SELECT codigo, descricao, fator_bobina
        FROM dim_produto WHERE ativo=1
        ORDER BY descricao, codigo
    """)

@st.cache_data(ttl=30, show_spinner=False)
def carregar_bobinas_fisicas():
    return query_df("""
        SELECT f.lote, f.codigo_spec, s.desc_curta, s.descricao,
               s.peso_especifico, f.peso_real, f.galpao, f.local_fisico,
               f.n_ref, f.status
        FROM dim_bobina_fisica f
        LEFT JOIN dim_bobina_spec s ON s.codigo=f.codigo_spec
        WHERE f.status <> 'INATIVA'
        ORDER BY f.lote
    """)

@st.cache_data(ttl=30, show_spinner=False)
def carregar_componentes():
    return query_df("""
        SELECT codigo, descricao, desc_curta, tipo, estoque_atual
        FROM dim_componente WHERE ativo=1
        ORDER BY descricao, codigo
    """)

@st.cache_data(ttl=30, show_spinner=False)
def carregar_pedidos():
    return query_df("""
        SELECT id, pedido, op, cliente, produto_codigo, metragem, tipo_prod, data
        FROM dim_pedido WHERE ativo=1
        ORDER BY CAST(pedido AS INTEGER) DESC, id
    """)

def registrar_auditoria(conn, tabela, registro_id, acao, usuario,
                        campo=None, valor_anterior=None, valor_novo=None, motivo=None):
    conn.execute("""
        INSERT INTO audit_log
        (tabela, registro_id, acao, campo, valor_anterior, valor_novo, motivo, usuario)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        tabela, registro_id, acao, campo,
        None if valor_anterior is None else str(valor_anterior),
        None if valor_novo is None else str(valor_novo),
        motivo, usuario
    ))

def refresh():
    clear_caches()
    st.rerun()

def derivar_data(data):
    return {
        "ano": data.year,
        "trimestre": f"T{((data.month-1)//3)+1}",
        "mes": ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"][data.month-1]
    }
