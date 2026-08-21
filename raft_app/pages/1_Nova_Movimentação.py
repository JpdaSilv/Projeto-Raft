import streamlit as st
from datetime import date
from db_utils import (
    carregar_produtos, carregar_bobinas_fisicas, carregar_componentes,
    derivar_data, execute,
)

st.set_page_config(page_title="Nova Movimentação", page_icon="📝", layout="wide")
st.title("📝 Nova Movimentação")
st.caption("Um registro por evento de produção — igual a uma linha nova na aba Movimentações.")

produtos = carregar_produtos()
bobinas = carregar_bobinas_fisicas()
componentes = carregar_componentes()

if produtos.empty:
    st.warning("Nenhum produto cadastrado em dim_produto. Rode o seed_from_excel.py primeiro.")
    st.stop()

with st.form("form_movimentacao", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        data_mov = st.date_input("Data", value=date.today())
        op = st.text_input("OP")
        pedido = st.text_input("Pedido")
        cliente = st.text_input("Cliente")
    with c2:
        tipo = st.selectbox("Tipo", ["Produção", "Retrabalho", "Sucata", "Histórico"])
        produto_label = st.selectbox(
            "Produto",
            options=produtos["codigo"] + " — " + produtos["descricao"].fillna(""),
        )
        fator = st.number_input("Fator", value=1.0, step=1.0)
        mt_prod = st.number_input("Mt. Prod. (planejado)", min_value=0.0, step=1.0)
        mt_produzida = st.number_input("Mt. Produzida (real)", min_value=0.0, step=1.0)
    with c3:
        tamanho = st.text_input("Tamanho")
        bobina_label = st.selectbox(
            "Bobina (lote físico)",
            options=["(nenhuma)"] + list(
                bobinas["lote"] + " — " + bobinas["desc_curta"].fillna("")
            ),
        )
        componente_label = st.selectbox(
            "Componente",
            options=["(nenhum)"] + list(
                componentes["codigo"] + " — " + componentes["descricao"].fillna("")
            ),
        )

    st.markdown("**Consumos**")
    d1, d2, d3, d4 = st.columns(4)
    cons_bob = d1.number_input("Cons. Bobina", min_value=0.0, step=0.1)
    cons_comp = d2.number_input("Cons. Componente", min_value=0.0, step=0.1)
    cola = d3.text_input("Cola")
    cons_cola = d4.number_input("Cons. Cola", min_value=0.0, step=0.1)
    eps_pir = st.text_input("EPS/PIR")

    with st.expander("Contagens acumuladas (opcional)"):
        e1, e2, e3, e4 = st.columns(4)
        cont_prod1 = e1.number_input("Contagem PROD1", min_value=0.0, step=1.0)
        cont_prod2 = e2.number_input("Contagem PROD2", min_value=0.0, step=1.0)
        cont_t2 = e3.number_input("Contagem Telha 2°", min_value=0.0, step=1.0)
        cont_sucata = e4.number_input("Contagem Sucata", min_value=0.0, step=1.0)

    usuario = st.text_input("Seu nome/usuário", value=st.session_state.get("usuario", ""))
    enviado = st.form_submit_button("Salvar movimentação", type="primary", use_container_width=True)

if enviado:
    if not op.strip():
        st.error("Informe a OP antes de salvar.")
        st.stop()

    st.session_state["usuario"] = usuario
    derivado = derivar_data(data_mov)
    produto_codigo = produto_label.split(" — ")[0]

    bobina_lote = None
    bobina_codigo = None
    peso_especifico = None
    if bobina_label != "(nenhuma)":
        bobina_lote = bobina_label.split(" — ")[0]
        linha = bobinas[bobinas["lote"] == bobina_lote].iloc[0]
        bobina_codigo = linha["codigo_spec"]
        peso_especifico = linha["peso_especifico"]

    componente_codigo = None if componente_label == "(nenhum)" else componente_label.split(" — ")[0]

    execute(
        """
        INSERT INTO fact_movimentacao (
            op, data, ano, trimestre, mes, pedido, cliente, produto_codigo, tipo, fator,
            mt_prod, mt_produzida, tamanho, bobina_lote, bobina_codigo, peso_especifico,
            cons_bob, componente_codigo, cons_comp, eps_pir, cola, cons_cola,
            contagem_prod1, contagem_prod2, contagem_telha2, contagem_sucata, usuario
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            op, data_mov.isoformat(), derivado["ano"], derivado["trimestre"], derivado["mes"],
            pedido, cliente, produto_codigo, tipo, fator, mt_prod, mt_produzida, tamanho,
            bobina_lote, bobina_codigo, peso_especifico, cons_bob, componente_codigo,
            cons_comp, eps_pir, cola, cons_cola, cont_prod1, cont_prod2, cont_t2, cont_sucata,
            usuario,
        ),
    )
    st.success(f"Movimentação da OP {op} salva com sucesso!")
    st.balloons()
