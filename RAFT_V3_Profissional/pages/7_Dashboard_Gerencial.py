import streamlit as st
from datetime import date
from db_utils import query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_perfil, mostrar_usuario_logado

aplicar_tema(); exigir_perfil("PCP","ALMOXARIFADO","ADMINISTRADOR"); mostrar_usuario_logado()
ano=st.number_input("Ano de análise",min_value=2020,max_value=2100,value=date.today().year,step=1)
page_header("Dashboard gerencial", "Indicadores para entender volume, consumo, pendências e concentração da operação.", "GESTÃO", f"ANO {ano}", "📊")
k=query_df("""SELECT COUNT(*) total,SUM(status='PENDENTE') pendentes,SUM(status='VALIDADO') validados,SUM(status='DEVOLVIDO') devolvidos,COALESCE(SUM(CASE WHEN status<>'CANCELADO' THEN mt_produzida ELSE 0 END),0) mt,COALESCE(SUM(CASE WHEN status<>'CANCELADO' THEN cons_bob ELSE 0 END),0) kg FROM fact_movimentacao WHERE ano=?""",(ano,)).iloc[0]
a,b,c,d,e=st.columns(5)
with a:kpi("Apontamentos",f"{int(k.total)}","total no ano","blue")
with b:kpi("Pendentes",f"{int(k.pendentes)}","fila PCP","amber" if k.pendentes else "green")
with c:kpi("Validados",f"{int(k.validados)}","aprovados","green")
with d:kpi("Metragem",f"{float(k.mt):,.0f} m","produção válida","blue")
with e:kpi("Consumo",f"{float(k.kg):,.0f} kg","bobina","amber")
mensal=query_df("""SELECT mes_num,CASE mes_num WHEN 1 THEN 'Jan' WHEN 2 THEN 'Fev' WHEN 3 THEN 'Mar' WHEN 4 THEN 'Abr' WHEN 5 THEN 'Mai' WHEN 6 THEN 'Jun' WHEN 7 THEN 'Jul' WHEN 8 THEN 'Ago' WHEN 9 THEN 'Set' WHEN 10 THEN 'Out' WHEN 11 THEN 'Nov' ELSE 'Dez' END mes,SUM(CASE WHEN status='CANCELADO' THEN 0 ELSE COALESCE(mt_produzida,0) END) metragem,SUM(CASE WHEN status='CANCELADO' THEN 0 ELSE COALESCE(cons_bob,0) END) consumo FROM (SELECT CAST(strftime('%m',data) AS INTEGER) mes_num,status,mt_produzida,cons_bob FROM fact_movimentacao WHERE ano=?) GROUP BY mes_num ORDER BY mes_num""",(ano,))
section("Evolução mensal", "Produção e consumo por mês")
if mensal.empty: alert("Ainda não existem dados para o ano selecionado.","info")
else:
    c1,c2=st.columns(2)
    with c1: st.caption("Metragem produzida"); st.bar_chart(mensal.set_index("mes")["metragem"],height=260)
    with c2: st.caption("Consumo de bobina (kg)"); st.bar_chart(mensal.set_index("mes")["consumo"],height=260)
section("Concentração da operação", "Onde estão os maiores volumes")
c1,c2=st.columns(2)
with c1:
    st.markdown("**Top 10 produtos por metragem**")
    df=query_df("SELECT produto_codigo,SUM(mt_produzida) metragem FROM fact_movimentacao WHERE ano=? AND status<>'CANCELADO' GROUP BY produto_codigo ORDER BY metragem DESC LIMIT 10",(ano,)); st.dataframe(df,use_container_width=True,hide_index=True)
with c2:
    st.markdown("**Top 10 clientes por metragem**")
    df2=query_df("SELECT cliente,SUM(mt_produzida) metragem FROM fact_movimentacao WHERE ano=? AND status<>'CANCELADO' GROUP BY cliente ORDER BY metragem DESC LIMIT 10",(ano,)); st.dataframe(df2,use_container_width=True,hide_index=True)
footer()
