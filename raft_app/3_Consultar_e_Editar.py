import streamlit as st
from db_utils import query_df, execute, log_auditoria
from theme import aplicar_tema
from auth import exigir_perfil, mostrar_usuario_logado

st.set_page_config(page_title="Consultar e Editar", page_icon="🔎", layout="wide")
aplicar_tema()
exigir_perfil("PCP", "ALMOXARIFADO", "ADMINISTRADOR")
mostrar_usuario_logado()
st.title("🔎 Consultar e Editar Lançamentos")

aba1, aba2 = st.tabs(["Movimentações", "Controle de Utilização"])

with aba1:
    c1, c2, c3 = st.columns(3)
    data_ini = c1.date_input("De", value=None, key="mov_ini")
    data_fim = c2.date_input("Até", value=None, key="mov_fim")
    produto_filtro = c3.text_input("Filtrar por código de produto (contém)")

    sql = "SELECT * FROM fact_movimentacao WHERE 1=1"
    params = []
    if data_ini:
        sql += " AND data >= ?"
        params.append(data_ini.isoformat())
    if data_fim:
        sql += " AND data <= ?"
        params.append(data_fim.isoformat())
    if produto_filtro:
        sql += " AND produto_codigo LIKE ?"
        params.append(f"%{produto_filtro}%")
    sql += " ORDER BY id DESC LIMIT 500"

    df_mov = query_df(sql, tuple(params))
    st.caption(f"{len(df_mov)} lançamento(s) encontrado(s) (máx. 500 exibidos).")
    st.dataframe(df_mov, use_container_width=True, hide_index=True)

    with st.expander("Apagar um lançamento pelo ID"):
        id_apagar = st.number_input("ID a apagar", min_value=0, step=1, key="del_mov")
        if st.button("Apagar movimentação", key="btn_del_mov"):
            if id_apagar:
                alvo = query_df("SELECT * FROM fact_movimentacao WHERE id=?", (id_apagar,))
                if alvo.empty:
                    st.error("ID não encontrado.")
                elif alvo.iloc[0]["status"] == "VALIDADO":
                    st.error("Este apontamento já foi VALIDADO pelo PCP e não pode ser apagado. "
                              "Isso protege o histórico — veja seção 2 do padrão RAFT V2.")
                else:
                    log_auditoria("fact_movimentacao", int(id_apagar), "APAGAR",
                                   st.session_state["usuario"]["nome"],
                                   valor_anterior=alvo.iloc[0].to_dict())
                    execute("DELETE FROM fact_movimentacao WHERE id = ?", (id_apagar,))
                    st.success(f"Registro {id_apagar} apagado.")
                    st.rerun()

with aba2:
    lote_filtro = st.text_input("Filtrar por lote (contém)", key="ctrl_lote")
    sql2 = "SELECT * FROM fact_controle_utilizacao WHERE 1=1"
    params2 = []
    if lote_filtro:
        sql2 += " AND bobina_lote LIKE ?"
        params2.append(f"%{lote_filtro}%")
    sql2 += " ORDER BY id DESC LIMIT 500"

    df_ctrl = query_df(sql2, tuple(params2))
    st.caption(f"{len(df_ctrl)} registro(s) encontrado(s) (máx. 500 exibidos).")
    st.dataframe(df_ctrl, use_container_width=True, hide_index=True)

    with st.expander("Apagar um registro pelo ID"):
        id_apagar2 = st.number_input("ID a apagar", min_value=0, step=1, key="del_ctrl")
        if st.button("Apagar registro", key="btn_del_ctrl"):
            if id_apagar2:
                log_auditoria("fact_controle_utilizacao", int(id_apagar2), "APAGAR",
                               st.session_state["usuario"]["nome"])
                execute("DELETE FROM fact_controle_utilizacao WHERE id = ?", (id_apagar2,))
                st.success(f"Registro {id_apagar2} apagado.")
                st.rerun()
