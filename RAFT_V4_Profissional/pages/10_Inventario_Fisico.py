import streamlit as st
from datetime import date
from db_utils import carregar_bobinas_fisicas, query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_perfil, mostrar_usuario_logado
from services import registrar_inventario
from page_runtime import run_page


def main():

    aplicar_tema(); user=exigir_perfil("ALMOXARIFADO","ADMINISTRADOR"); mostrar_usuario_logado()
    page_header("Inventário físico", "Registre a contagem real e compare com o saldo cadastrado e o saldo calculado pelo RAFT.", "ESTOQUE & RASTREABILIDADE", "RECONCILIAÇÃO", "📋")
    bob=carregar_bobinas_fisicas()
    if bob.empty: alert("Nenhuma bobina cadastrada.","warn"); st.stop()
    a,b=st.tabs(["Registrar contagem","Reconciliação"])
    with a:
        section("Nova contagem", "Uma contagem não altera silenciosamente o TOTVS")
        with st.form("inv",clear_on_submit=True):
            lote=st.selectbox("Lote",bob.lote.tolist()); peso=st.number_input("Peso físico (kg)",min_value=0.0,step=1.0); data_=st.date_input("Data",date.today()); local=st.text_input("Local encontrado"); obs=st.text_area("Observação")
            ok=st.form_submit_button("Registrar contagem",type="primary",use_container_width=True)
        if ok:
            try: registrar_inventario(lote,peso,local,data_,obs,user["nome"]); alert("Contagem registrada.","success"); st.rerun()
            except Exception as e: st.error(str(e))
    with b:
        consumido=query_df("SELECT bobina_lote lote,COALESCE(SUM(cons_bob),0) consumido FROM fact_movimentacao WHERE status<>'CANCELADO' GROUP BY bobina_lote")
        ult=query_df("SELECT i.lote,i.peso_fisico,i.data_contagem FROM fact_inventario_fisico i JOIN (SELECT lote,MAX(data_contagem) d FROM fact_inventario_fisico GROUP BY lote) x ON x.lote=i.lote AND x.d=i.data_contagem")
        df=bob.merge(consumido,on="lote",how="left").merge(ult,on="lote",how="left"); df["consumido"]=df.consumido.fillna(0); df["saldo_raft"]=df.peso_real.fillna(0)-df.consumido; df["dif_totvs_fisico"]=df.peso_real.fillna(0)-df.peso_fisico
        limite=st.number_input("Divergência considerada crítica (kg)",min_value=0.0,value=50.0,step=10.0)
        crit=int((df.dif_totvs_fisico.abs()>limite).sum())
        x,y,z=st.columns(3)
        with x:kpi("Lotes analisados",f"{len(df)}","base atual","blue")
        with y:kpi("Divergências",f"{crit}",f"acima de {limite:.0f} kg","red" if crit else "green")
        with z:kpi("Contagens registradas",f"{int(df.peso_fisico.notna().sum())}","última contagem por lote","green")
        st.dataframe(df[["lote","codigo_spec","peso_real","consumido","saldo_raft","peso_fisico","dif_totvs_fisico","data_contagem"]].sort_values("dif_totvs_fisico",key=lambda s:s.abs(),ascending=False),use_container_width=True,hide_index=True)
    footer()

run_page('10_Inventario_Fisico', main)
