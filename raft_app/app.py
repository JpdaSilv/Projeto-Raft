import streamlit as st
from db_utils import query_df

st.set_page_config(page_title="Raft • Setor Telha", page_icon="🏭", layout="wide")

st.title("🏭 Controle de Produção — Setor Telha")
st.caption("Substitui o preenchimento manual das abas *Movimentações* e *Controle_Utilização* no Excel.")

st.markdown("Use o menu à esquerda para lançar uma movimentação, registrar o uso/pesagem de uma "
            "bobina, ou consultar/editar os lançamentos já feitos.")

col1, col2, col3, col4 = st.columns(4)

hoje_mov = query_df(
    "SELECT COUNT(*) AS n, COALESCE(SUM(mt_produzida),0) AS mt FROM fact_movimentacao "
    "WHERE data = date('now','localtime')"
)
mes_mov = query_df(
    "SELECT COUNT(*) AS n, COALESCE(SUM(mt_produzida),0) AS mt FROM fact_movimentacao "
    "WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now','localtime')"
)
bobinas_em_uso = query_df(
    "SELECT COUNT(DISTINCT bobina_lote) AS n FROM fact_controle_utilizacao "
    "WHERE data = date('now','localtime')"
)
total_lancamentos = query_df("SELECT COUNT(*) AS n FROM fact_movimentacao")

col1.metric("Movimentações hoje", int(hoje_mov["n"][0]))
col2.metric("Metragem produzida hoje", f'{hoje_mov["mt"][0]:.1f} m')
col3.metric("Metragem produzida no mês", f'{mes_mov["mt"][0]:.1f} m')
col4.metric("Bobinas usadas hoje", int(bobinas_em_uso["n"][0]))

st.divider()
st.subheader("Últimos lançamentos")
ultimos = query_df("""
    SELECT id, data, op, pedido, cliente, produto_codigo, mt_produzida, bobina_lote, criado_em
    FROM fact_movimentacao
    ORDER BY id DESC
    LIMIT 10
""")
if ultimos.empty:
    st.info("Nenhuma movimentação lançada ainda. Vá em **Nova Movimentação** no menu ao lado.")
else:
    st.dataframe(ultimos, use_container_width=True, hide_index=True)
