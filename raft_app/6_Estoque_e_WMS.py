import streamlit as st
from db_utils import query_df, carregar_bobinas_fisicas, carregar_componentes
from theme import aplicar_tema
from auth import exigir_login, mostrar_usuario_logado

st.set_page_config(page_title="Estoque e Mapa WMS", page_icon="🗺️", layout="wide")
aplicar_tema()
exigir_login()
mostrar_usuario_logado()

st.title("🗺️ Estoque e Localização (WMS simplificado)")
st.caption(
    "TOTVS/Cadastro = último peso registrado no Excel. RAFT = Cadastro menos o que já foi "
    "consumido pelo sistema. Sem uma fonte de inventário físico ainda, então FÍSICO não aparece — "
    "ver seção 110 do documento: nunca misturar os três."
)

aba1, aba2 = st.tabs(["Bobinas", "Componentes"])

with aba1:
    bobinas = carregar_bobinas_fisicas()
    consumido = query_df(
        "SELECT bobina_lote AS lote, COALESCE(SUM(cons_bob),0) AS consumido "
        "FROM fact_movimentacao WHERE bobina_lote IS NOT NULL GROUP BY bobina_lote"
    )
    df = bobinas.merge(consumido, on="lote", how="left")
    df["consumido"] = df["consumido"].fillna(0)
    df["saldo_raft"] = df["peso_real"].fillna(0) - df["consumido"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Lotes em estoque", len(df))
    c2.metric("Peso total cadastrado (TOTVS)", f'{df["peso_real"].fillna(0).sum():.0f} kg')
    c3.metric("Saldo RAFT estimado", f'{df["saldo_raft"].sum():.0f} kg')

    galpao_filtro = st.selectbox("Filtrar por galpão", options=["(todos)"] + sorted(df["local_fisico"].dropna().unique().tolist()))
    df_filtrado = df if galpao_filtro == "(todos)" else df[df["local_fisico"] == galpao_filtro]

    st.subheader("Distribuição por localização física")
    por_local = df_filtrado.groupby("local_fisico", dropna=False).agg(
        lotes=("lote", "count"), peso_totvs=("peso_real", "sum"), saldo_raft=("saldo_raft", "sum")
    ).reset_index().sort_values("peso_totvs", ascending=False)
    st.dataframe(por_local, use_container_width=True, hide_index=True,
                 column_config={"local_fisico": "Local físico", "lotes": "Nº de lotes",
                                 "peso_totvs": "Peso TOTVS (kg)", "saldo_raft": "Saldo RAFT (kg)"})

    st.subheader("Lotes individuais")
    st.dataframe(
        df_filtrado[["lote", "codigo_spec", "desc_curta", "local_fisico", "peso_real", "consumido", "saldo_raft"]]
        .sort_values("saldo_raft"),
        use_container_width=True, hide_index=True,
        column_config={"lote": "Lote", "codigo_spec": "Código", "desc_curta": "Descrição",
                        "local_fisico": "Local", "peso_real": "TOTVS (kg)",
                        "consumido": "Consumido (kg)", "saldo_raft": "Saldo RAFT (kg)"},
    )

with aba2:
    componentes = carregar_componentes()
    consumido_comp = query_df(
        "SELECT componente_codigo AS codigo, COALESCE(SUM(cons_comp),0) AS consumido "
        "FROM fact_movimentacao WHERE componente_codigo IS NOT NULL GROUP BY componente_codigo"
    )
    dfc = componentes.merge(consumido_comp, on="codigo", how="left")
    dfc["consumido"] = dfc["consumido"].fillna(0)
    estoque_atual_col = query_df("SELECT codigo, estoque_atual FROM dim_componente")
    dfc = dfc.merge(estoque_atual_col, on="codigo", how="left", suffixes=("", "_dup"))
    dfc["saldo_raft"] = dfc["estoque_atual"].fillna(0) - dfc["consumido"]

    st.dataframe(
        dfc[["codigo", "descricao", "estoque_atual", "consumido", "saldo_raft"]],
        use_container_width=True, hide_index=True,
        column_config={"codigo": "Código", "descricao": "Descrição", "estoque_atual": "TOTVS (un)",
                        "consumido": "Consumido (un)", "saldo_raft": "Saldo RAFT (un)"},
    )
