
import streamlit as st

def aplicar_estilo():
    st.markdown("""
    <style>
    .stApp { background: #f4f7fb; }
    .main .block-container { max-width: 1500px; padding: 2rem 3rem 3rem; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#0b1f3a 0%,#102b50 100%);
        border-right: 1px solid rgba(255,255,255,.08);
    }
    [data-testid="stSidebar"] * { color: #eaf2fb; }

    .raft-brand { padding: 8px 8px 25px; border-bottom: 1px solid rgba(255,255,255,.1); margin-bottom: 20px; }
    .raft-logo { font-size: 29px; font-weight: 800; letter-spacing: -1px; }
    .raft-sub { color: #9fb5cf !important; font-size: 11px; margin-top: 3px; }

    .sidebar-section {
        color: #6f8aaa !important; text-transform: uppercase;
        letter-spacing: 1.2px; font-size: 10px; font-weight: 700;
        margin: 18px 8px 8px;
    }
    .sidebar-status {
        margin-top: 30px; padding: 12px; border-radius: 10px;
        background: rgba(255,255,255,.06);
        border: 1px solid rgba(255,255,255,.08);
        font-size: 11px;
    }
    .dot { display:inline-block; width:8px; height:8px; background:#28c76f; border-radius:50%; margin-right:7px; }

    .page-head { margin-bottom: 25px; }
    .eyebrow {
        color:#4775a8; text-transform:uppercase; letter-spacing:1.5px;
        font-size:10px; font-weight:800; margin-bottom:5px;
    }
    .page-title { color:#10233f; font-size:30px; font-weight:800; letter-spacing:-1px; margin:0; }
    .page-sub { color:#708197; font-size:13px; margin-top:6px; }

    .section-card {
        background:#fff; border:1px solid #e3eaf2; border-radius:14px;
        padding:20px; box-shadow:0 3px 14px rgba(16,35,63,.04);
        margin-bottom:16px;
    }
    .section-title { color:#162d4b; font-size:15px; font-weight:800; margin-bottom:3px; }
    .section-sub { color:#8795a6; font-size:11px; margin-bottom:14px; }

    .info-card {
        background:linear-gradient(135deg,#102b50,#174a7c); color:white;
        border-radius:14px; padding:18px 21px; margin:15px 0;
        box-shadow:0 7px 22px rgba(16,43,80,.12);
    }
    .info-title { font-size:14px; font-weight:800; }
    .info-text { color:#c7d8ea; font-size:11px; line-height:1.55; margin-top:4px; }

    .success-card {
        background:#eaf8f0; border:1px solid #ccebd9; color:#1c7f4b;
        border-radius:10px; padding:12px 15px; font-size:12px; font-weight:700;
    }

    .kpi {
        background:#fff; border:1px solid #e4eaf1; border-radius:13px;
        padding:17px 19px; box-shadow:0 3px 14px rgba(16,35,63,.04);
        border-left:4px solid #1769aa;
    }
    .kpi-label { color:#7a899c; font-size:10px; text-transform:uppercase; letter-spacing:1px; font-weight:700; }
    .kpi-value { color:#122b4a; font-size:25px; font-weight:800; margin-top:8px; }

    div[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }
    div[data-testid="stForm"] {
        background:#fff; border:1px solid #e3eaf2; border-radius:14px;
        padding:18px; box-shadow:0 3px 14px rgba(16,35,63,.04);
    }
    .stButton > button, div.stButton > button {
        border-radius:8px; font-weight:700;
    }

    @media (max-width:900px) {
        .main .block-container { padding:1.2rem 1rem 2rem; }
        .page-title { font-size:24px; }
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div class="raft-brand">
            <div class="raft-logo">🏭 RAFT</div>
            <div class="raft-sub">Controle Operacional • Setor Telha</div>
        </div>
        <div class="sidebar-section">Operação</div>
        """, unsafe_allow_html=True)

        st.page_link("app.py", label="▣  Visão Geral")
        st.page_link("pages/1_Nova_Movimentação.py", label="📝  Nova Movimentação")
        st.page_link("pages/2_Controle_de_Utilização.py", label="⚖️  Controle de Utilização")
        st.page_link("pages/3_Consultar_e_Editar.py", label="🔎  Consultar / Editar")

        st.markdown("""
        <div class="sidebar-section">Sistema</div>
        <div class="sidebar-status"><span class="dot"></span>Banco de dados conectado</div>
        """, unsafe_allow_html=True)

def cabecalho(titulo, subtitulo, eyebrow="RAFT • OPERAÇÃO"):
    st.markdown(f"""
    <div class="page-head">
        <div class="eyebrow">{eyebrow}</div>
        <div class="page-title">{titulo}</div>
        <div class="page-sub">{subtitulo}</div>
    </div>
    """, unsafe_allow_html=True)

def secao(titulo, subtitulo=""):
    st.markdown(f"""
    <div class="section-title">{titulo}</div>
    {f'<div class="section-sub">{subtitulo}</div>' if subtitulo else ''}
    """, unsafe_allow_html=True)
