import streamlit as st
from datetime import date, datetime
from db_utils import carregar_bobinas_fisicas, query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_login, mostrar_usuario_logado
from services import registrar_utilizacao

aplicar_tema(); user=exigir_login(); mostrar_usuario_logado()
page_header("Controle de utilização", "Registre cada pesagem ou uso da bobina. A sequência de utilização é calculada automaticamente.", "OPERAÇÃO", "RASTREABILIDADE", "⚖️")
bob=carregar_bobinas_fisicas()
if bob.empty: alert("Nenhuma bobina cadastrada.","warn"); st.stop()

section("Registrar evento", "Cada registro cria uma nova linha no histórico da bobina")
labels=(bob.lote+" — "+bob.desc_curta.fillna("")).tolist()
with st.form("uso",clear_on_submit=True):
    label=st.selectbox("Bobina (lote)",labels)
    lote=label.split(" — ",1)[0]
    info=bob[bob.lote==lote].iloc[0]
    a,b=st.columns(2)
    peso=a.number_input("Peso atual (kg)",min_value=0.0,step=1.0,format="%.2f")
    obs=b.text_input("Observação / etiqueta",placeholder="Opcional")
    c,d=st.columns(2)
    data_=c.date_input("Data",date.today()); hora=d.time_input("Hora",datetime.now().time())
    ok=st.form_submit_button("Registrar utilização",type="primary",use_container_width=True)
if ok:
    try:
        seq=registrar_utilizacao(lote,peso,user["nome"],data_,hora,obs or None)
        alert(f"Utilização <b>#{seq}</b> registrada para o lote <b>{lote}</b>.","success")
        st.rerun()
    except Exception as e: st.error(str(e))

section("Últimos eventos", f"Lote selecionado: {lote}")
hist=query_df("SELECT utilizacao,data,hora,peso_atual,usuario,criado_em FROM fact_controle_utilizacao WHERE bobina_lote=? ORDER BY data DESC,hora DESC",(lote,))
if hist.empty: alert("Ainda não há pesagens para este lote.","info")
else: st.dataframe(hist,use_container_width=True,hide_index=True)
footer()
