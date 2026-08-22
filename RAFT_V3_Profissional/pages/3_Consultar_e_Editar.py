import streamlit as st
from datetime import date, timedelta
from db_utils import query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_perfil, mostrar_usuario_logado
from services import cancelar_apontamento

aplicar_tema(); user=exigir_perfil("PCP","ALMOXARIFADO","ADMINISTRADOR"); mostrar_usuario_logado()
page_header("Consultar e editar", "Pesquise lançamentos sem perder rastreabilidade. Cancelamentos ficam registrados na auditoria.", "CONTROLE", "ATÉ 1.000 REGISTROS", "🔎")

c1,c2,c3,c4=st.columns([1,1,1.2,1.2])
de=c1.date_input("De",date.today()-timedelta(days=7)); ate=c2.date_input("Até",date.today())
status_f=c3.multiselect("Status",["PENDENTE","VALIDADO","DEVOLVIDO","CANCELADO"],default=[])
produto=c4.text_input("Produto contém",placeholder="TL040...")
where=["data BETWEEN ? AND ?"]; params=[de.isoformat(),ate.isoformat()]
if status_f: where.append("status IN ("+",".join(["?"]*len(status_f))+")"); params+=status_f
if produto: where.append("produto_codigo LIKE ?"); params.append(f"%{produto}%")
df=query_df(f"SELECT id,data,op,pedido,cliente,produto_codigo,tipo,mt_produzida,bobina_lote,cons_bob,status,usuario FROM fact_movimentacao WHERE {' AND '.join(where)} ORDER BY id DESC LIMIT 1000",tuple(params))

v1,v2,v3=st.columns(3)
with v1: kpi("Encontrados",f"{len(df)}","lançamentos no filtro","blue")
with v2: kpi("Pendentes",f"{int((df.status=='PENDENTE').sum()) if not df.empty else 0}","aguardando PCP","amber")
with v3: kpi("Metragem",f"{df.mt_produzida.fillna(0).sum():,.1f} m" if not df.empty else "0 m","resultado do filtro","green")
section("Resultados", "Use os filtros acima para reduzir a lista")
if df.empty: alert("Nenhum lançamento encontrado para os filtros informados.","info")
else: st.dataframe(df,use_container_width=True,hide_index=True,column_config={"mt_produzida":st.column_config.NumberColumn("Metragem",format="%.2f m"),"cons_bob":st.column_config.NumberColumn("Consumo",format="%.2f kg")})

section("Ação administrativa", "Cancelamento exige perfil autorizado e deixa registro de auditoria")
with st.expander("Cancelar lançamento"):
    rid=st.number_input("ID do lançamento",min_value=1,step=1); motivo=st.text_area("Motivo",placeholder="Informe por que o lançamento deve ser cancelado.")
    if st.button("Cancelar lançamento",type="primary"):
        try: cancelar_apontamento(int(rid),motivo,user["nome"]); alert("Lançamento cancelado e auditado.","success"); st.rerun()
        except Exception as e: st.error(str(e))
footer()
