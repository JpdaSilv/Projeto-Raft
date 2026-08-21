import streamlit as st
from db_utils import query_df

st.set_page_config(
    page_title="Raft • Controle Operacional",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS — VISUAL DO SISTEMA
# ============================================================
st.markdown("""
<style>
    /* ---------- BASE ---------- */
    .stApp {
        background: #f4f7fb;
    }

    .main .block-container {
        max-width: 1500px;
        padding: 2rem 3rem 3rem 3rem;
    }

    /* ---------- SIDEBAR ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1f3a 0%, #102b50 100%);
        border-right: 1px solid rgba(255,255,255,.08);
    }

    [data-testid="stSidebar"] * {
        color: #eaf2fb;
    }

    .sidebar-brand {
        padding: 8px 8px 28px 8px;
        border-bottom: 1px solid rgba(255,255,255,.10);
        margin-bottom: 24px;
    }

    .sidebar-brand .logo {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .sidebar-brand .subtitle {
        color: #9fb5cf;
        font-size: 12px;
        margin-top: 4px;
    }

    .sidebar-section {
        color: #6f8aaa !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-size: 10px;
        font-weight: 700;
        margin: 18px 8px 8px 8px;
    }

    .sidebar-status {
        margin-top: 35px;
        padding: 12px;
        border-radius: 10px;
        background: rgba(255,255,255,.06);
        border: 1px solid rgba(255,255,255,.08);
        font-size: 12px;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #28c76f;
        border-radius: 50%;
        margin-right: 7px;
    }

    /* ---------- HEADER ---------- */
    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 20px;
        margin-bottom: 26px;
    }

    .eyebrow {
        color: #4775a8;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 11px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .page-title {
        color: #10233f;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -1px;
        margin: 0;
    }

    .page-subtitle {
        color: #708197;
        font-size: 14px;
        margin-top: 6px;
    }

    .online-badge {
        background: #e8f8ef;
        color: #1f9253;
        border: 1px solid #c8ecd8;
        border-radius: 999px;
        padding: 8px 13px;
        font-size: 12px;
        font-weight: 700;
        white-space: nowrap;
    }

    /* ---------- KPI CARDS ---------- */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e5ebf2;
        border-radius: 14px;
        padding: 20px 21px;
        min-height: 125px;
        box-shadow: 0 3px 14px rgba(16,35,63,.045);
        position: relative;
        overflow: hidden;
    }

    .kpi-card::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: #1769aa;
    }

    .kpi-label {
        color: #7a899c;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
    }

    .kpi-value {
        color: #122b4a;
        font-size: 27px;
        font-weight: 800;
        margin-top: 11px;
        letter-spacing: -.6px;
    }

    .kpi-description {
        color: #9aa7b6;
        font-size: 11px;
        margin-top: 5px;
    }

    /* ---------- SECTION ---------- */
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 30px 0 12px 0;
    }

    .section-title {
        color: #162d4b;
        font-size: 17px;
        font-weight: 800;
    }

    .section-caption {
        color: #8795a6;
        font-size: 12px;
    }

    /* ---------- TABLE WRAPPER ---------- */
    .table-wrapper {
        background: #ffffff;
        border: 1px solid #e5ebf2;
        border-radius: 14px;
        padding: 8px;
        box-shadow: 0 3px 14px rgba(16,35,63,.04);
    }

    /* ---------- INFO CARD ---------- */
    .info-card {
        background: linear-gradient(135deg, #102b50, #174a7c);
        color: white;
        border-radius: 15px;
        padding: 20px 24px;
        margin-top: 22px;
        box-shadow: 0 8px 25px rgba(16,43,80,.15);
    }

    .info-title {
        font-size: 14px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .info-text {
        color: #c7d8ea;
        font-size: 12px;
        line-height: 1.6;
    }

    /* ---------- STREAMLIT COMPONENT TUNING ---------- */
    div[data-testid="stMetric"] {
        background: transparent;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }

    hr {
        border: none;
        border-top: 1px solid #e4eaf1;
        margin: 24px 0;
    }

    @media (max-width: 900px) {
        .main .block-container {
            padding: 1.2rem 1rem 2rem 1rem;
        }

        .page-title {
            font-size: 25px;
        }

        .online-badge {
            display: none;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo">🏭 RAFT</div>
        <div class="subtitle">Controle Operacional • Setor Telha</div>
    </div>

    <div class="sidebar-section">Operação</div>
    """, unsafe_allow_html=True)

    st.page_link("app.py", label="▣  Visão Geral")
    st.page_link("pages/1_Nova_Movimentação.py", label="📝  Nova Movimentação")
    st.page_link("pages/2_Controle_de_Utilização.py", label="⚖️  Controle de Utilização")
    st.page_link("pages/3_Consultar_e_Editar.py", label="🔎  Consultar / Editar")

    st.markdown("""
    <div class="sidebar-section">Sistema</div>

    <div class="sidebar-status">
        <span class="status-dot"></span>
        Banco de dados conectado
    </div>
    """, unsafe_allow_html=True)

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
