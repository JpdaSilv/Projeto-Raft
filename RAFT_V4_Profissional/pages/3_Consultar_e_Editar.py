import streamlit as st
from datetime import date,timedelta
from db_utils import query_df
from theme import aplicar_tema,page_header,section,kpi,alert,footer,status
from auth import exigir_perfil,mostrar_usuario_logado
from services import cancelar_apontamento,editar_apontamento
from page_runtime import run_page

def main():
    aplicar_tema(); user=exigir_perfil("PCP","ALMOXARIFADO","ADMINISTRADOR"); mostrar_usuario_logado()
    page_header("Consultar e editar","Pesquise, abra o registro, ajuste dados permitidos e mantenha toda alteração auditada.","CONTROLE","EDIÇÃO CONTROLADA","🔎")

    c1,c2,c3,c4,c5=st.columns([1,1,1.2,1.2,1.1])
    de=c1.date_input("De",date.today()-timedelta(days=7)); ate=c2.date_input("Até",date.today())
    if de>ate:
        alert("A data inicial não pode ser maior que a data final.","danger"); st.stop()
    status_f=c3.multiselect("Status",["PENDENTE","VALIDADO","DEVOLVIDO","CANCELADO"])
    produto=c4.text_input("Produto contém",placeholder="TL040...")
    lote=c5.text_input("Bobina / lote",placeholder="Lote")
    where=["date(data) BETWEEN ? AND ?"]; params=[de.isoformat(),ate.isoformat()]
    if status_f: where.append("status IN ("+ ",".join(["?"]*len(status_f))+")"); params.extend(status_f)
    if produto: where.append("produto_codigo LIKE ?"); params.append(f"%{produto.strip()}%")
    if lote: where.append("bobina_lote LIKE ?"); params.append(f"%{lote.strip()}%")
    df=query_df(f"""SELECT id,data,op,pedido,cliente,produto_codigo,tipo,mt_produzida,
        bobina_lote,cons_bob,status,usuario,criado_em FROM fact_movimentacao
        WHERE {' AND '.join(where)} ORDER BY id DESC LIMIT 1000""",tuple(params))

    a,b,c,d=st.columns(4)
    with a:kpi("Encontrados",len(df),"lançamentos","blue")
    with b:kpi("Pendentes",int((df.status=="PENDENTE").sum()) if not df.empty else 0,"fila PCP","amber")
    with c:kpi("Validados",int((df.status=="VALIDADO").sum()) if not df.empty else 0,"aprovados","green")
    with d:kpi("Metragem",f"{df.mt_produzida.fillna(0).sum():,.1f} m" if not df.empty else "0 m","resultado do filtro","blue")

    section("Resultados","Selecione um ID abaixo para abrir o registro completo.")
    if df.empty:
        alert("Nenhum lançamento encontrado para os filtros informados.","info")
    else:
        st.dataframe(df,use_container_width=True,hide_index=True,
                     column_config={"mt_produzida":st.column_config.NumberColumn("Metragem",format="%.2f m"),
                                    "cons_bob":st.column_config.NumberColumn("Consumo",format="%.2f kg")})
        ids=df.id.astype(int).tolist()
        rid=st.selectbox("Registro para detalhar",ids,format_func=lambda x:f"#{x} • {next((r.produto_codigo for _,r in df.iterrows() if int(r.id)==x),'—')}")
        row=df[df.id==rid].iloc[0]
        with st.container(border=True):
            x1,x2,x3=st.columns(3)
            x1.markdown(f'**Pedido** — {row.pedido or "—"}')
            x2.markdown(f'**Cliente** — {row.cliente or "—"}')
            x3.markdown(f'**Bobina** — {row.bobina_lote or "—"}')
            st.markdown(status(str(row.status),{"VALIDADO":"ok","PENDENTE":"warn","DEVOLVIDO":"info","CANCELADO":"bad"}.get(row.status,"neutral")),unsafe_allow_html=True)

    section("Edição controlada","Somente metragem e tipo podem ser alterados; a alteração volta para PENDENTE e gera auditoria.")
    if df.empty:
        st.caption("Nenhum registro disponível para edição.")
    else:
        with st.form("editar_registro"):
            e1,e2=st.columns(2)
            nova_mt=e1.number_input("Nova metragem (m)",min_value=0.01,value=float(row.mt_produzida or 0),step=0.1,format="%.2f")
            novo_tipo=e2.selectbox("Novo tipo",["PRODUÇÃO","2°","SUCATA"],index=["PRODUÇÃO","2°","SUCATA"].index(row.tipo) if row.tipo in ["PRODUÇÃO","2°","SUCATA"] else 0)
            confirmar=st.checkbox("Entendi que a edição reinicia a validação do PCP.")
            salvar=st.form_submit_button("Salvar alteração",type="primary",use_container_width=True)
        if salvar:
            if not confirmar: st.error("Confirme a regra de revalidação.")
            else:
                try:
                    consumo=editar_apontamento(int(row.id),nova_mt,novo_tipo,user["nome"])
                    alert(f"Registro <b>#{int(row.id)}</b> atualizado. Novo consumo: <b>{consumo:.2f} kg</b>.","success")
                    st.rerun()
                except Exception as e: st.error(str(e))

    section("Cancelamento administrativo","Cancelamento não apaga o registro e permanece na trilha de auditoria.")
    if df.empty: st.caption("Nenhum registro disponível.")
    else:
        with st.expander(f"Cancelar registro #{int(row.id)}"):
            motivo=st.text_area("Motivo",placeholder="Explique o motivo do cancelamento.")
            if st.button("Confirmar cancelamento",type="primary"):
                try:
                    cancelar_apontamento(int(row.id),motivo,user["nome"])
                    alert("Registro cancelado e auditado.","success"); st.rerun()
                except Exception as e: st.error(str(e))
    footer()

run_page("Consultar e Editar",main)
