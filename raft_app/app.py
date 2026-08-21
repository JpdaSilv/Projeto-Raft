import streamlit as st
from styles import aplicar_estilo
from db_utils import query_df

st.set_page_config(
    page_title="Raft • Controle Operacional",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_estilo()

# ============================================================
# CONSULTAS
# ============================================================
hoje_mov = query_df(
    "SELECT COUNT(*) AS n, COALESCE(SUM(mt_produzida),0) AS mt "
    "FROM fact_movimentacao "
    "WHERE data = date('now','localtime')"
)

mes_mov = query_df(
    "SELECT COUNT(*) AS n, COALESCE(SUM(mt_produzida),0) AS mt "
    "FROM fact_movimentacao "
    "WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now','localtime')"
)

bobinas_em_uso = query_df(
    "SELECT COUNT(DISTINCT bobina_lote) AS n "
    "FROM fact_controle_utilizacao "
    "WHERE data = date('now','localtime')"
)

total_lancamentos = query_df(
    "SELECT COUNT(*) AS n FROM fact_movimentacao"
)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="page-header">
    <div>
        <div class="eyebrow">Raft • Operação</div>
        <div class="page-title">Controle de Produção</div>
        <div class="page-subtitle">
            Acompanhamento das movimentações e utilização de bobinas.
        </div>
    </div>
    <div class="online-badge">● SISTEMA ONLINE</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# KPIs
# ============================================================
k1, k2, k3, k4 = st.columns(4, gap="medium")

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Movimentações hoje</div>
        <div class="kpi-value">{int(hoje_mov["n"][0])}</div>
        <div class="kpi-description">Eventos registrados no dia</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Produção hoje</div>
        <div class="kpi-value">{hoje_mov["mt"][0]:,.1f} m</div>
        <div class="kpi-description">Metragem produzida no dia</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Produção no mês</div>
        <div class="kpi-value">{mes_mov["mt"][0]:,.1f} m</div>
        <div class="kpi-description">Metragem acumulada no mês</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Bobinas usadas hoje</div>
        <div class="kpi-value">{int(bobinas_em_uso["n"][0])}</div>
        <div class="kpi-description">Lotes utilizados no dia</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# ÚLTIMOS LANÇAMENTOS
# ============================================================
st.markdown("""
<div class="section-header">
    <div>
        <div class="section-title">Últimos lançamentos</div>
        <div class="section-caption">As 10 movimentações mais recentes registradas no sistema</div>
    </div>
</div>
""", unsafe_allow_html=True)

ultimos = query_df("""
    SELECT
        id,
        data,
        op,
        pedido,
        cliente,
        produto_codigo,
        mt_produzida,
        bobina_lote,
        criado_em
    FROM fact_movimentacao
    ORDER BY id DESC
    LIMIT 10
""")

if ultimos.empty:
    st.markdown("""
    <div class="info-card">
        <div class="info-title">Nenhuma movimentação registrada</div>
        <div class="info-text">
            Utilize o menu lateral para lançar a primeira movimentação de produção.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown('<div class="table-wrapper">', unsafe_allow_html=True)
    st.dataframe(
        ultimos,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "op": st.column_config.TextColumn("OP"),
            "pedido": st.column_config.TextColumn("Pedido"),
            "cliente": st.column_config.TextColumn("Cliente"),
            "produto_codigo": st.column_config.TextColumn("Produto"),
            "mt_produzida": st.column_config.NumberColumn(
                "Produção (m)",
                format="%.1f"
            ),
            "bobina_lote": st.column_config.TextColumn("Bobina"),
            "criado_em": st.column_config.DatetimeColumn(
                "Registrado em",
                format="DD/MM/YYYY HH:mm"
            ),
        },
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("""
<div class="info-card">
    <div class="info-title">💡 Controle centralizado</div>
    <div class="info-text">
        Os lançamentos realizados pelo sistema são gravados diretamente no banco
        SQLite. O Streamlit funciona como camada operacional, enquanto o banco
        mantém os registros para consultas, tratamento e futura integração com BI.
    </div>
</div>
""", unsafe_allow_html=True)
