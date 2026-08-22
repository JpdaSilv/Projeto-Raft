import io
import pandas as pd
import streamlit as st
from db_utils import query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_perfil, mostrar_usuario_logado

aplicar_tema(); exigir_perfil("PCP","ALMOXARIFADO","ADMINISTRADOR"); mostrar_usuario_logado()
page_header("Exportar para Power BI", "Extraia fatos, dimensões, snapshots e auditoria em um Excel estável para o modelo analítico.", "GESTÃO", "XLSX • POWER BI", "📤")
tables={"Movimentacoes":"SELECT * FROM fact_movimentacao","Controle_Utilizacao":"SELECT * FROM fact_controle_utilizacao","Inventario_Fisico":"SELECT * FROM fact_inventario_fisico","Produtos":"SELECT * FROM dim_produto","Bobinas_Spec":"SELECT * FROM dim_bobina_spec","Bobinas_Fisicas":"SELECT * FROM dim_bobina_fisica","Componentes":"SELECT * FROM dim_componente","Pedidos":"SELECT * FROM dim_pedido","Snapshot_TOTVS":"SELECT * FROM snapshot_totvs","Auditoria":"SELECT * FROM audit_log"}
section("Conjunto de dados", "Escolha as tabelas que farão parte da extração")
sel=st.multiselect("Tabelas",list(tables),default=list(tables))
with st.container(border=True):
    st.markdown(f"**{len(sel)} tabela(s)** selecionada(s)")
if st.button("Gerar Excel",type="primary",disabled=not sel):
    out=io.BytesIO(); resumo=[]
    with pd.ExcelWriter(out,engine="openpyxl") as writer:
        for name in sel:
            df=query_df(tables[name]); df.to_excel(writer,sheet_name=name[:31],index=False); resumo.append({"tabela":name,"linhas":len(df)})
        pd.DataFrame(resumo).to_excel(writer,sheet_name="Resumo",index=False)
    out.seek(0); alert("Arquivo analítico preparado. Confira o resumo antes de baixar.","success")
    st.dataframe(pd.DataFrame(resumo),use_container_width=True,hide_index=True)
    st.download_button("Baixar raft_powerbi.xlsx",out.getvalue(),"raft_powerbi.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary")
footer()
