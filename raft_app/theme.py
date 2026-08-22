"""
theme.py — CSS customizado compartilhado por todas as páginas.
Chame aplicar_tema() logo após st.set_page_config() em cada página.
"""
import streamlit as st

CSS = """
<style>
/* esconde o rodapé "Made with Streamlit" e o menu de hambúrguer padrão */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

/* título com ícone mais compacto, sem o peso visual padrão */
h1 {
    font-size: 26px !important;
    font-weight: 600 !important;
    padding-top: 0.5rem !important;
}

/* cards das métricas (st.metric) com fundo próprio, em vez de "boiar" */
div[data-testid="stMetric"] {
    background: #1A1D24;
    border: 1px solid #2A2E38;
    border-radius: 10px;
    padding: 14px 16px;
}
div[data-testid="stMetricLabel"] { font-size: 13px; opacity: 0.75; }
div[data-testid="stMetricValue"] { font-size: 22px; }

/* botão principal (submit do formulário) com mais destaque */
button[kind="primaryFormSubmit"], button[kind="primary"] {
    background-color: #D85A30 !important;
    border: none !important;
    font-weight: 600 !important;
}
button[kind="primaryFormSubmit"]:hover, button[kind="primary"]:hover {
    background-color: #B84B27 !important;
}

/* inputs com cantos mais suaves e borda mais discreta */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-baseweb="select"] > div {
    border-radius: 8px !important;
}

/* menos espaço em branco vertical entre os widgets (formulário fica mais denso) */
div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {
    margin-bottom: -6px;
}

/* sidebar com fundo levemente diferente da área de conteúdo */
section[data-testid="stSidebar"] {
    background: #14161C;
    border-right: 1px solid #2A2E38;
}
</style>
"""


def aplicar_tema():
    st.markdown(CSS, unsafe_allow_html=True)
