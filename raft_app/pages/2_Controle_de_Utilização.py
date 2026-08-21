import streamlit as st
from datetime import date, datetime
from db_utils import carregar_bobinas_fisicas, execute, query_df

st.set_page_config(page_title="Controle de Utilização", page_icon="⚖️", layout="wide")
st.title("⚖️ Controle de Utilização de Bobina")
st.caption("Registro de uso/pesagem — substitui a aba Controle_Utilização.")

bobinas = carregar_bobinas_fisicas()
if bobinas.empty:
    st.warning("Nenhuma bobina cadastrada em dim_bobina_fisica. Rode o seed_from_excel.py primeiro.")
    st.stop()

with st.form("form_controle", clear_on_submit=True):
    bobina_label = st.selectbox(
        "Bobina (lote)",
        options=list(bobinas["lote"] + " — " + bobinas["desc_curta"].fillna("") +
                     " (peso real: " + bobinas["peso_real"].fillna(0).astype(str) + " kg)"),
    )
    c1, c2, c3 = st.columns(3)
    utilizacao = c1.number_input("Utilização (n° de uso)", min_value=1, step=1, value=1)
    data_ctrl = c2.date_input("Data", value=date.today())
    hora_ctrl = c3.time_input("Hora", value=datetime.now().time())
    peso_atual = st.number_input("Peso Atual (kg)", min_value=0.0, step=0.1)
    caminho_etiqueta = st.text_input("Caminho da etiqueta (PDF), opcional")

    enviado = st.form_submit_button("Registrar utilização", type="primary", use_container_width=True)

if enviado:
    bobina_lote = bobina_label.split(" — ")[0]
    execute(
        """
        INSERT INTO fact_controle_utilizacao
            (bobina_lote, utilizacao, data, hora, peso_atual, caminho_etiqueta)
        VALUES (?,?,?,?,?,?)
        """,
        (bobina_lote, utilizacao, data_ctrl.isoformat(), hora_ctrl.strftime("%H:%M:%S"),
         peso_atual, caminho_etiqueta or None),
    )
    st.success(f"Utilização registrada para a bobina {bobina_lote}.")

st.divider()
st.subheader("Histórico recente desta bobina")
if 'bobina_label' in dir() and bobinas is not None and not bobinas.empty:
    lote_filtro = st.selectbox("Ver histórico de:", options=bobinas["lote"], key="filtro_hist")
    hist = query_df(
        "SELECT utilizacao, data, hora, peso_atual, criado_em FROM fact_controle_utilizacao "
        "WHERE bobina_lote = ? ORDER BY data DESC, hora DESC",
        (lote_filtro,),
    )
    st.dataframe(hist, use_container_width=True, hide_index=True)
