import streamlit as st
from datetime import date
from db_utils import query_df, execute, carregar_bobinas_fisicas
from theme import aplicar_tema
from auth import exigir_perfil, mostrar_usuario_logado

st.set_page_config(page_title="Inventário Físico", page_icon="📋", layout="wide")
aplicar_tema()
exigir_perfil("ALMOXARIFADO", "ADMINISTRADOR")
mostrar_usuario_logado()

st.title("📋 Inventário Físico")
st.caption(
    "Contagem manual do que está de fato no chão de fábrica — terceira fonte de saldo, "
    "nunca misturada com TOTVS ou RAFT (seção 110). Serve pra achar divergência, não pra corrigir sozinha."
)

aba1, aba2 = st.tabs(["Registrar contagem", "Reconciliação (TOTVS × RAFT × FÍSICO)"])

with aba1:
    bobinas = carregar_bobinas_fisicas()
    if bobinas.empty:
        st.warning("Nenhuma bobina cadastrada.")
        st.stop()

    with st.form("form_inventario", clear_on_submit=True):
        lote_label = st.selectbox(
            "Bobina (lote) contada",
            options=list(bobinas["lote"] + " — " + bobinas["desc_curta"].fillna("")),
        )
        c1, c2 = st.columns(2)
        peso_fisico = c1.number_input("Peso contado fisicamente (kg)", min_value=0.0, step=1.0)
        data_contagem = c2.date_input("Data da contagem", value=date.today())
        local_contado = st.text_input("Local onde foi encontrada (opcional, se divergir do cadastro)")
        obs = st.text_area("Observação (opcional)")
        enviar = st.form_submit_button("Registrar contagem", type="primary", use_container_width=True)

    if enviar:
        lote = lote_label.split(" — ")[0]
        execute(
            "INSERT INTO fact_inventario_fisico (lote, peso_fisico, local_contado, data_contagem, usuario, obs) "
            "VALUES (?,?,?,?,?,?)",
            (lote, peso_fisico, local_contado or None, data_contagem.isoformat(),
             st.session_state["usuario"]["nome"], obs or None),
        )
        st.success(f"Contagem registrada para o lote {lote}.")

with aba2:
    st.subheader("Reconciliação de saldo")

    bobinas = carregar_bobinas_fisicas()
    consumido = query_df(
        "SELECT bobina_lote AS lote, COALESCE(SUM(cons_bob),0) AS consumido "
        "FROM fact_movimentacao WHERE bobina_lote IS NOT NULL GROUP BY bobina_lote"
    )
    ultima_contagem = query_df("""
        SELECT lote, peso_fisico, data_contagem
        FROM fact_inventario_fisico f1
        WHERE data_contagem = (SELECT MAX(data_contagem) FROM fact_inventario_fisico f2 WHERE f2.lote = f1.lote)
    """)

    df = bobinas.merge(consumido, on="lote", how="left").merge(ultima_contagem, on="lote", how="left")
    df["consumido"] = df["consumido"].fillna(0)
    df["saldo_raft"] = df["peso_real"].fillna(0) - df["consumido"]
    df = df.rename(columns={"peso_real": "totvs", "peso_fisico": "fisico"})

    df["diff_totvs_raft"] = df["totvs"].fillna(0) - df["saldo_raft"]
    df["diff_raft_fisico"] = df["saldo_raft"] - df["fisico"]
    df["diff_totvs_fisico"] = df["totvs"].fillna(0) - df["fisico"]

    com_contagem = df[df["fisico"].notna()].copy()

    if com_contagem.empty:
        st.info("Nenhuma bobina com contagem física registrada ainda. Vá na aba 'Registrar contagem'.")
    else:
        limite = st.slider("Destacar divergências acima de (kg)", min_value=0, max_value=500, value=50, step=10)
        divergentes = com_contagem[com_contagem["diff_totvs_fisico"].abs() > limite]

        c1, c2 = st.columns(2)
        c1.metric("Lotes com inventário registrado", len(com_contagem))
        c2.metric(f"Divergências acima de {limite}kg (TOTVS × FÍSICO)", len(divergentes))

        st.dataframe(
            com_contagem[["lote", "codigo_spec", "totvs", "saldo_raft", "fisico",
                           "diff_totvs_raft", "diff_raft_fisico", "diff_totvs_fisico", "data_contagem"]]
            .sort_values("diff_totvs_fisico", key=abs, ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                "lote": "Lote", "codigo_spec": "Código",
                "totvs": "TOTVS (kg)", "saldo_raft": "RAFT (kg)", "fisico": "FÍSICO (kg)",
                "diff_totvs_raft": "TOTVS − RAFT", "diff_raft_fisico": "RAFT − FÍSICO",
                "diff_totvs_fisico": "TOTVS − FÍSICO", "data_contagem": "Última contagem",
            },
        )
