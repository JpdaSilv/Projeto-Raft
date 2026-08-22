"""Persistência central do RAFT: conexões, transações, consultas e cache."""
from contextlib import contextmanager
from io import BytesIO
import sqlite3
import pandas as pd
import streamlit as st
from config import DB_PATH, DB_TIMEOUT

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT, check_same_thread=False)
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
        conn.execute("BEGIN IMMEDIATE")
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
    for fn in (carregar_produtos, carregar_bobinas_fisicas, carregar_componentes, carregar_pedidos):
        try: fn.clear()
        except Exception: pass

@st.cache_data(ttl=30, show_spinner=False)
def carregar_produtos():
    return query_df("SELECT codigo,descricao,tipo_telha,fator_bobina FROM dim_produto WHERE ativo=1 ORDER BY descricao,codigo")

@st.cache_data(ttl=30, show_spinner=False)
def carregar_bobinas_fisicas():
    return query_df("""
        SELECT f.lote,f.codigo_spec,s.desc_curta,s.descricao,s.peso_especifico,
               f.peso_real,f.galpao,f.local_fisico,f.n_ref,f.status
        FROM dim_bobina_fisica f
        LEFT JOIN dim_bobina_spec s ON s.codigo=f.codigo_spec
        WHERE f.status <> 'INATIVA'
        ORDER BY f.galpao,f.local_fisico,f.lote
    """ )

@st.cache_data(ttl=30, show_spinner=False)
def carregar_componentes():
    return query_df("SELECT codigo,descricao,desc_curta,tipo,estoque_atual FROM dim_componente WHERE ativo=1 ORDER BY descricao,codigo")

@st.cache_data(ttl=30, show_spinner=False)
def carregar_pedidos():
    return query_df("""
        SELECT id,pedido,op,cliente,produto_codigo,metragem,tipo_prod,data
        FROM dim_pedido WHERE ativo=1
        ORDER BY date(data) DESC, CAST(pedido AS INTEGER) DESC, id
    """ )

def registrar_auditoria(conn,tabela,registro_id,acao,usuario,campo=None,valor_anterior=None,valor_novo=None,motivo=None):
    conn.execute("""
        INSERT INTO audit_log(tabela,registro_id,acao,campo,valor_anterior,valor_novo,motivo,usuario)
        VALUES(?,?,?,?,?,?,?,?)
    """,(tabela,registro_id,acao,campo,
        None if valor_anterior is None else str(valor_anterior),
        None if valor_novo is None else str(valor_novo),motivo,usuario))

def refresh():
    clear_caches()
    st.rerun()

def derivar_data(data):
    meses=["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
    return {"ano":data.year,"trimestre":f"T{((data.month-1)//3)+1}","mes":meses[data.month-1]}

def backup_database_bytes():
    """Cria uma cópia binária consistente do banco, incluindo o conteúdo do WAL."""
    import tempfile, os
    source = get_conn()
    fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    target = sqlite3.connect(temp_path)
    try:
        source.backup(target)
        target.close()
        with open(temp_path,"rb") as fh:
            return fh.read()
    finally:
        try: target.close()
        except Exception: pass
        source.close()
        try: os.unlink(temp_path)
        except OSError: pass

def database_health():
    with get_conn() as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        foreign = conn.execute("PRAGMA foreign_key_check").fetchall()
        return {
            "integrity": integrity,
            "foreign_key_errors": len(foreign),
            "journal_mode": conn.execute("PRAGMA journal_mode").fetchone()[0],
            "foreign_keys": conn.execute("PRAGMA foreign_keys").fetchone()[0],
        }
