import streamlit as st
from db_utils import query_df
from theme import aplicar_tema, page_header, section, kpi, alert, status, footer
from auth import exigir_perfil, mostrar_usuario_logado
from services import validar_apontamento, devolver_apontamento
from page_runtime import run_page


def main():

    aplicar_tema(); user=exigir_perfil("PCP","ADMINISTRADOR"); mostrar_usuario_logado()
    page_header("Fila de validação PCP", "Conferência antes de transformar o apontamento operacional em dado válido.", "CONTROLE", "APROVAÇÃO MANUAL", "✅")
    pend=query_df("SELECT id,data,pedido,cliente,produto_codigo,tipo,mt_produzida,bobina_lote,bobina_codigo,peso_especifico,cons_bob,usuario FROM fact_movimentacao WHERE status='PENDENTE' ORDER BY id")
    with st.container():
        kpi("Apontamentos pendentes",str(len(pend)),"fila atual","amber" if len(pend) else "green")
    if pend.empty:
        alert("Fila limpa. Nenhum apontamento aguardando conferência.","success")
    else:
        section("Conferir lançamentos", "Valide ou devolva cada registro individualmente")
        for _,r in pend.iterrows():
            with st.container(border=True):
                a,b,c=st.columns([1.25,1.25,1])
                with a:
                    st.markdown(f"### #{int(r.id)}  •  Pedido {r.pedido}")
                    st.caption(str(r.cliente))
                    st.markdown(status("PENDENTE","warn"),unsafe_allow_html=True)
                with b:
                    st.markdown(f"**{r.produto_codigo}**  •  {r.tipo}")
                    st.caption(f"Lote {r.bobina_lote}  •  {float(r.mt_produzida or 0):.2f} m  •  {float(r.cons_bob or 0):.2f} kg")
                with c:
                    st.caption(f"Enviado por {r.usuario} em {r.data}")
                    x,y=st.columns(2)
                    if x.button("Validar",key=f"v{r.id}",type="primary"):
                        try: validar_apontamento(int(r.id),user["nome"]); st.rerun()
                        except Exception as e: st.error(str(e))
                    with y.popover("Devolver"):
                        motivo=st.text_area("Motivo",key=f"m{r.id}")
                        if st.button("Confirmar",key=f"d{r.id}"):
                            try: devolver_apontamento(int(r.id),motivo,user["nome"]); st.rerun()
                            except Exception as e: st.error(str(e))
    footer()

run_page('4_Validacao_PCP', main)
