import streamlit as st
from db_utils import query_df, execute, log_auditoria
from theme import aplicar_tema
from auth import exigir_perfil, mostrar_usuario_logado

st.set_page_config(page_title="Validação PCP", page_icon="✅", layout="wide")
aplicar_tema()
exigir_perfil("PCP", "ADMINISTRADOR")
mostrar_usuario_logado()

st.title("✅ Validação de Apontamentos")
st.caption("Apontamentos enviados pelos operadores, aguardando conferência do PCP.")

pendentes = query_df("""
    SELECT id, data, pedido, cliente, produto_codigo, tipo, mt_produzida,
           bobina_lote, cons_bob, eps_pir, cons_cola, usuario, criado_em
    FROM fact_movimentacao
    WHERE status = 'PENDENTE'
    ORDER BY id ASC
""")

if pendentes.empty:
    st.success("Nenhum apontamento pendente. Tudo validado!")
    st.stop()

st.caption(f"{len(pendentes)} apontamento(s) pendente(s).")

for _, row in pendentes.iterrows():
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**Pedido {row['pedido']}** — {row['cliente']}")
        c2.markdown(f"Produto: `{row['produto_codigo']}` · {row['tipo']}")
        c3.markdown(f"Lote: `{row['bobina_lote']}` · {row['mt_produzida']:.1f} m")
        c4.markdown(f"Consumo: {row['cons_bob']:.1f} kg")
        st.caption(f"Enviado por {row['usuario']} em {row['criado_em']}")

        b1, b2, b3 = st.columns([1, 1, 3])
        if b1.button("✅ Validar", key=f"val_{row['id']}", type="primary"):
            execute(
                "UPDATE fact_movimentacao SET status='VALIDADO', validado_por=?, "
                "validado_em=datetime('now','localtime') WHERE id=?",
                (st.session_state["usuario"]["nome"], row["id"]),
            )
            log_auditoria("fact_movimentacao", int(row["id"]), "VALIDAR",
                           st.session_state["usuario"]["nome"],
                           campo="status", valor_anterior="PENDENTE", valor_novo="VALIDADO")
            st.rerun()
        if b2.button("↩️ Devolver", key=f"dev_{row['id']}"):
            st.session_state[f"devolver_{row['id']}"] = True

        if st.session_state.get(f"devolver_{row['id']}"):
            motivo = st.text_input("Motivo da devolução", key=f"motivo_{row['id']}")
            if st.button("Confirmar devolução", key=f"conf_dev_{row['id']}"):
                execute(
                    "UPDATE fact_movimentacao SET status='DEVOLVIDO', motivo_devolucao=? WHERE id=?",
                    (motivo, row["id"]),
                )
                log_auditoria("fact_movimentacao", int(row["id"]), "DEVOLVER",
                               st.session_state["usuario"]["nome"],
                               campo="status", valor_anterior="PENDENTE", valor_novo="DEVOLVIDO",
                               motivo=motivo)
                del st.session_state[f"devolver_{row['id']}"]
                st.rerun()
