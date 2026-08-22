import streamlit as st
import pandas as pd
from db_utils import query_df
from theme import aplicar_tema
from auth import exigir_perfil, mostrar_usuario_logado

st.set_page_config(page_title="Dashboard Gerencial", page_icon="📊", layout="wide")
aplicar_tema()
exigir_perfil("PCP", "ALMOXARIFADO", "ADMINISTRADOR")
mostrar_usuario_logado()

st.title("📊 Dashboard Gerencial")

# --- KPIs do topo ---
kpis = query_df("""
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN status='PENDENTE' THEN 1 ELSE 0 END) AS pendentes,
        SUM(CASE WHEN status='VALIDADO' THEN 1 ELSE 0 END) AS validados,
        SUM(CASE WHEN status='DEVOLVIDO' THEN 1 ELSE 0 END) AS devolvidos,
        COALESCE(SUM(mt_produzida),0) AS metragem_total,
        COALESCE(SUM(cons_bob),0) AS consumo_total
    FROM fact_movimentacao
""").iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Apontamentos totais", int(kpis["total"]))
c2.metric("Pendentes", int(kpis["pendentes"]))
c3.metric("Validados", int(kpis["validados"]))
c4.metric("Metragem total", f'{kpis["metragem_total"]:.0f} m')
c5.metric("Consumo total de bobina", f'{kpis["consumo_total"]:.0f} kg')

taxa_devolucao = (kpis["devolvidos"] / kpis["total"] * 100) if kpis["total"] else 0
if taxa_devolucao > 15:
    st.warning(f"⚠️ Taxa de devolução do PCP está em {taxa_devolucao:.1f}% — acima do saudável (>15%). "
               "Vale investigar se é erro recorrente de algum operador ou pedido mal cadastrado.")

st.divider()

# --- Produção por mês ---
por_mes = query_df("""
    SELECT strftime('%Y-%m', data) AS mes, SUM(mt_produzida) AS metragem, SUM(cons_bob) AS consumo
    FROM fact_movimentacao
    GROUP BY mes ORDER BY mes
""")
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Metragem produzida por mês")
    if por_mes.empty:
        st.info("Sem dados suficientes ainda.")
    else:
        st.bar_chart(por_mes.set_index("mes")["metragem"])

with col_b:
    st.subheader("Consumo de bobina por mês (kg)")
    if por_mes.empty:
        st.info("Sem dados suficientes ainda.")
    else:
        st.bar_chart(por_mes.set_index("mes")["consumo"])

st.divider()

# --- Top produtos e clientes ---
col_c, col_d = st.columns(2)
with col_c:
    st.subheader("Top 10 produtos por metragem")
    top_prod = query_df("""
        SELECT produto_codigo, SUM(mt_produzida) AS metragem
        FROM fact_movimentacao WHERE produto_codigo IS NOT NULL AND produto_codigo != '-'
        GROUP BY produto_codigo ORDER BY metragem DESC LIMIT 10
    """)
    st.dataframe(top_prod, use_container_width=True, hide_index=True,
                 column_config={"produto_codigo": "Produto", "metragem": "Metragem (m)"})

with col_d:
    st.subheader("Top 10 clientes por metragem")
    top_cli = query_df("""
        SELECT cliente, SUM(mt_produzida) AS metragem
        FROM fact_movimentacao WHERE cliente IS NOT NULL AND cliente != ''
        GROUP BY cliente ORDER BY metragem DESC LIMIT 10
    """)
    st.dataframe(top_cli, use_container_width=True, hide_index=True,
                 column_config={"cliente": "Cliente", "metragem": "Metragem (m)"})

st.divider()

# --- Comparação de períodos (mês atual vs anterior) ---
st.subheader("Comparação: mês atual vs. mês anterior")
comp = query_df("""
    SELECT
        strftime('%Y-%m', data) AS mes,
        SUM(mt_produzida) AS metragem,
        SUM(cons_bob) AS consumo
    FROM fact_movimentacao
    WHERE data >= date('now','localtime','start of month','-1 month')
    GROUP BY mes ORDER BY mes
""")
if len(comp) >= 2:
    atual, anterior = comp.iloc[-1], comp.iloc[-2]
    d1, d2 = st.columns(2)
    delta_mt = atual["metragem"] - anterior["metragem"]
    delta_cons = atual["consumo"] - anterior["consumo"]
    d1.metric("Metragem (mês atual)", f'{atual["metragem"]:.0f} m', delta=f'{delta_mt:+.0f} m')
    d2.metric("Consumo (mês atual)", f'{atual["consumo"]:.0f} kg', delta=f'{delta_cons:+.0f} kg')
else:
    st.info("Ainda não há dois meses completos de dados pra comparar.")
