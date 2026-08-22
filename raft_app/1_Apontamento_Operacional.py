import streamlit as st
from datetime import date
from db_utils import query_df, execute, derivar_data, carregar_bobinas_fisicas
from theme import aplicar_tema
from auth import exigir_login, mostrar_usuario_logado

st.set_page_config(page_title="Apontamento Operacional", page_icon="📝", layout="wide")
aplicar_tema()
exigir_login()
mostrar_usuario_logado()

st.title("📝 Apontamento Operacional")
st.caption("Informe só o pedido, o tipo, o lote e a metragem — o resto o sistema calcula sozinho.")

bobinas = carregar_bobinas_fisicas()
pedidos_numeros = query_df("SELECT DISTINCT pedido FROM dim_pedido ORDER BY CAST(pedido AS INTEGER) DESC")

if bobinas.empty or pedidos_numeros.empty:
    st.warning("Base de pedidos ou bobinas vazia. Rode o seed_from_excel.py primeiro.")
    st.stop()

# --- Pedido fora do form: precisa reagir na hora pra mostrar cliente/produto/metragem ---
pedido_num = st.selectbox("Pedido", options=pedidos_numeros["pedido"])
linhas_pedido = query_df(
    "SELECT id, op, cliente, produto_codigo, metragem, tipo_prod FROM dim_pedido WHERE pedido = ?",
    (pedido_num,),
)

if len(linhas_pedido) > 1:
    st.info(f"Este pedido tem {len(linhas_pedido)} itens. Selecione qual item está sendo produzido.")
    idx = st.selectbox(
        "Item do pedido",
        options=linhas_pedido.index,
        format_func=lambda i: f"{linhas_pedido.loc[i,'produto_codigo']} — {linhas_pedido.loc[i,'metragem']} m",
    )
    item = linhas_pedido.loc[idx]
else:
    item = linhas_pedido.iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("Cliente", item["cliente"] or "—")
c2.metric("Produto", item["produto_codigo"] or "—")
c3.metric("Metragem do pedido", f'{item["metragem"]:.1f} m' if item["metragem"] else "—")

st.divider()

# --- Lote fora do form também, pra calcular consumo em tempo real ---
lote_label = st.selectbox(
    "Lote da bobina",
    options=list(bobinas["lote"] + " — " + bobinas["desc_curta"].fillna("")),
)
lote = lote_label.split(" — ")[0]
linha_bobina = bobinas[bobinas["lote"] == lote].iloc[0]
peso_especifico = linha_bobina["peso_especifico"] or 0

mt_produzida_preview = st.number_input(
    "Metragem produzida (m)", min_value=0.0, step=1.0, key="mt_preview",
    help="Usada pra calcular o consumo automaticamente.",
)
consumo_calculado = round(peso_especifico * mt_produzida_preview, 2)

cc1, cc2 = st.columns(2)
cc1.metric("Peso específico do lote", f"{peso_especifico:.2f} kg/m")
cc2.metric("Consumo calculado da bobina", f"{consumo_calculado:.2f} kg")

st.divider()

with st.form("form_apontamento", clear_on_submit=True):
    tipo = st.radio("Tipo de produção", ["PRODUÇÃO", "2°", "SUCATA"], horizontal=True)
    d1, d2 = st.columns(2)
    eps_pir = d1.number_input("EPS/PIR consumido (kg)", min_value=0.0, step=0.5)
    cola = d2.number_input("Cola consumida (kg)", min_value=0.0, step=0.5)

    enviado = st.form_submit_button("Enviar apontamento", type="primary", use_container_width=True)

if enviado:
    if mt_produzida_preview <= 0:
        st.error("Informe a metragem produzida (acima) antes de enviar.")
        st.stop()

    hoje = date.today()
    derivado = derivar_data(hoje)
    usuario = st.session_state["usuario"]["nome"]

    execute(
        """
        INSERT INTO fact_movimentacao (
            op, data, ano, trimestre, mes, pedido, cliente, produto_codigo, tipo,
            mt_prod, mt_produzida, bobina_lote, bobina_codigo, peso_especifico, cons_bob,
            eps_pir, cons_cola, status, usuario
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            item["op"], hoje.isoformat(), derivado["ano"], derivado["trimestre"], derivado["mes"],
            pedido_num, item["cliente"], item["produto_codigo"], tipo, item["metragem"],
            mt_produzida_preview, lote, linha_bobina["codigo_spec"], peso_especifico,
            consumo_calculado, eps_pir, cola, "PENDENTE", usuario,
        ),
    )
    st.success(
        f"Apontamento enviado! Consumo calculado: {consumo_calculado:.2f} kg. "
        f"Status: PENDENTE — aguardando validação do PCP."
    )
    st.balloons()
