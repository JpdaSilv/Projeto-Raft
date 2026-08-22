import streamlit as st
import pandas as pd
from db_utils import query_df, carregar_bobinas_fisicas
from theme import aplicar_tema
from auth import exigir_login, mostrar_usuario_logado

st.set_page_config(page_title="Kardex da Bobina", page_icon="📖", layout="wide")
aplicar_tema()
exigir_login()
mostrar_usuario_logado()

st.title("📖 Kardex da Bobina")
st.caption("Histórico completo de uma bobina física: toda vez que foi consumida ou pesada, em ordem cronológica.")

bobinas = carregar_bobinas_fisicas()
if bobinas.empty:
    st.warning("Nenhuma bobina cadastrada.")
    st.stop()

lote_label = st.selectbox(
    "Bobina (lote)",
    options=list(bobinas["lote"] + " — " + bobinas["desc_curta"].fillna("")),
)
lote = lote_label.split(" — ")[0]
info = bobinas[bobinas["lote"] == lote].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Código de especificação", info["codigo_spec"] or "—")
c2.metric("Peso específico", f'{info["peso_especifico"]:.2f} kg/m' if info["peso_especifico"] else "—")
c3.metric("Peso cadastrado (Excel)", f'{info["peso_real"]:.0f} kg' if info["peso_real"] else "—")

consumos = query_df(
    "SELECT data, criado_em, 'CONSUMO' AS evento, pedido, produto_codigo, mt_produzida AS metragem, "
    "cons_bob AS peso_evento, usuario, status FROM fact_movimentacao WHERE bobina_lote = ?",
    (lote,),
)
pesagens = query_df(
    "SELECT data, criado_em, 'PESAGEM' AS evento, NULL AS pedido, NULL AS produto_codigo, "
    "NULL AS metragem, peso_atual AS peso_evento, usuario, NULL AS status "
    "FROM fact_controle_utilizacao WHERE bobina_lote = ?",
    (lote,),
)

kardex = pd.concat([consumos, pesagens], ignore_index=True)
if kardex.empty:
    c4.metric("Consumo total registrado", "0 kg")
    st.info("Essa bobina ainda não tem nenhum evento registrado no sistema (nem consumo, nem pesagem).")
else:
    kardex = kardex.sort_values("criado_em")
    total_consumido = consumos["peso_evento"].sum() if not consumos.empty else 0
    c4.metric("Consumo total registrado", f"{total_consumido:.1f} kg")

    if info["peso_real"]:
        saldo_estimado = info["peso_real"] - total_consumido
        st.metric("Saldo RAFT estimado (peso cadastrado − consumido)", f"{saldo_estimado:.1f} kg")

    st.divider()
    st.dataframe(
        kardex[["criado_em", "evento", "pedido", "produto_codigo", "metragem", "peso_evento", "usuario", "status"]],
        use_container_width=True, hide_index=True,
        column_config={
            "criado_em": "Quando",
            "evento": "Evento",
            "pedido": "Pedido",
            "produto_codigo": "Produto",
            "metragem": "Metragem (m)",
            "peso_evento": "Peso (kg)",
            "usuario": "Usuário",
            "status": "Status",
        },
    )
