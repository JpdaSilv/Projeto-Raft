import streamlit as st
from datetime import date
from config import APP_NAME,APP_VERSION
from db.migrate import rodar_migracoes
from db_utils import query_df
from theme import aplicar_tema,brand_sidebar,page_header,section,kpi,alert,footer
from auth import exigir_login,mostrar_usuario_logado
from page_runtime import run_page

st.set_page_config(page_title=APP_NAME,page_icon="🏭",layout="wide",initial_sidebar_state="expanded")
rodar_migracoes()
aplicar_tema(); brand_sidebar()

def home():
    user=exigir_login(); mostrar_usuario_logado()
    hoje=date.today().isoformat()
    k=query_df("""SELECT
      (SELECT COUNT(*) FROM fact_movimentacao WHERE data=? AND status<>'CANCELADO') mov_hoje,
      (SELECT COALESCE(SUM(mt_produzida),0) FROM fact_movimentacao WHERE data=? AND status<>'CANCELADO') mt_hoje,
      (SELECT COALESCE(SUM(cons_bob),0) FROM fact_movimentacao WHERE data=? AND status<>'CANCELADO') kg_hoje,
      (SELECT COUNT(*) FROM fact_movimentacao WHERE status='PENDENTE') pendentes,
      (SELECT COUNT(*) FROM dim_bobina_fisica WHERE status='ESTOQUE') lotes""",(hoje,hoje,hoje)).iloc[0]
    page_header("Central Operacional","Uma visão única para produção, PCP, estoque e rastreabilidade.","RAFT • VISÃO GERAL",
                f"{date.today().strftime('%d/%m/%Y')} • {user['perfil']} • V{APP_VERSION}","🏭")
    cols=st.columns(5)
    with cols[0]: kpi("Movimentações hoje",int(k.mov_hoje),"apontamentos válidos","blue")
    with cols[1]: kpi("Metragem hoje",f"{float(k.mt_hoje):,.1f} m","produção registrada","green")
    with cols[2]: kpi("Consumo hoje",f"{float(k.kg_hoje):,.0f} kg","bobina consumida","blue")
    with cols[3]: kpi("Fila PCP",int(k.pendentes),"aguardando conferência","amber" if k.pendentes else "green")
    with cols[4]: kpi("Lotes em estoque",int(k.lotes),"bobinas ativas","blue")

    section("Painel de atenção","Exceções operacionais que merecem ação.")
    a,b,c=st.columns(3)
    pend=int(k.pendentes)
    sem_local=int(query_df("SELECT COUNT(*) n FROM dim_bobina_fisica WHERE status='ESTOQUE' AND (local_fisico IS NULL OR trim(local_fisico)='')").iloc[0].n)
    neg=int(query_df("""SELECT COUNT(*) n FROM vw_bobina_saldo WHERE status='ESTOQUE' AND saldo_raft<0""").iloc[0].n)
    with a: alert(f"<b>{pend}</b> apontamento(s) aguardando PCP." if pend else "Fila do PCP está limpa.","warn" if pend else "success")
    with b: alert(f"<b>{sem_local}</b> lote(s) sem endereço físico." if sem_local else "Todos os lotes ativos possuem localização.","warn" if sem_local else "success")
    with c: alert(f"<b>{neg}</b> lote(s) com saldo RAFT negativo." if neg else "Nenhum saldo RAFT negativo.","danger" if neg else "success")

    section("Fluxo rápido","Atalhos para as rotinas mais usadas.")
    q1,q2,q3,q4=st.columns(4)
    with q1: st.page_link("pages/1_Apontamento_Operacional.py",label="Novo apontamento",icon="📝")
    with q2: st.page_link("pages/4_Validacao_PCP.py",label="Fila do PCP",icon="✅")
    with q3: st.page_link("pages/5_Kardex_da_Bobina.py",label="Kardex da bobina",icon="📖")
    with q4: st.page_link("pages/6_Estoque_e_WMS.py",label="Estoque & WMS",icon="📦")

    section("Atividade recente","Últimos lançamentos registrados.")
    recent=query_df("""SELECT id,data,pedido,cliente,produto_codigo,tipo,mt_produzida,bobina_lote,status,usuario
      FROM fact_movimentacao ORDER BY id DESC LIMIT 10""")
    if recent.empty: alert("Ainda não existem apontamentos.","info")
    else: st.dataframe(recent,use_container_width=True,hide_index=True,
                       column_config={"mt_produzida":st.column_config.NumberColumn("Metragem",format="%.2f m")})

    section("Ritmo de produção","Metragem registrada nos últimos 30 dias.")
    serie=query_df("""SELECT data,ROUND(SUM(CASE WHEN status='CANCELADO' THEN 0 ELSE COALESCE(mt_produzida,0) END),2) metragem
      FROM fact_movimentacao WHERE data>=date(?,'-30 day') GROUP BY data ORDER BY data""",(hoje,))
    if not serie.empty: st.line_chart(serie.set_index("data"),height=250)
    else: alert("O gráfico será preenchido conforme a produção for lançada.","info")
    footer()

def safe_home():
    run_page("Visão Geral",home)

pages={
 "🏠 Visão Geral":[st.Page(safe_home,title="Visão Geral",icon="🏠",url_path="inicio")],
 "🏭 Operação":[
   st.Page("pages/1_Apontamento_Operacional.py",title="Apontamento Operacional",icon="📝",url_path="apontamento"),
   st.Page("pages/2_Controle_de_Utilizacao.py",title="Controle de Utilização",icon="⚖️",url_path="utilizacao")],
 "📋 Controle":[
   st.Page("pages/3_Consultar_e_Editar.py",title="Consultar e Editar",icon="🔎",url_path="consultar"),
   st.Page("pages/4_Validacao_PCP.py",title="Validação PCP",icon="✅",url_path="pcp")],
 "📦 Estoque & Rastreabilidade":[
   st.Page("pages/5_Kardex_da_Bobina.py",title="Kardex da Bobina",icon="📖",url_path="kardex"),
   st.Page("pages/6_Estoque_e_WMS.py",title="Estoque e WMS",icon="📦",url_path="wms"),
   st.Page("pages/10_Inventario_Fisico.py",title="Inventário Físico",icon="📋",url_path="inventario"),
   st.Page("pages/9_Etiqueta_da_Bobina.py",title="Etiqueta da Bobina",icon="🏷️",url_path="etiqueta")],
 "📊 Gestão":[
   st.Page("pages/7_Dashboard_Gerencial.py",title="Dashboard Gerencial",icon="📊",url_path="dashboard"),
   st.Page("pages/8_Importar_TOTVS.py",title="Importar TOTVS",icon="📥",url_path="totvs"),
   st.Page("pages/11_Exportar_para_PowerBI.py",title="Exportar para Power BI",icon="📤",url_path="powerbi")],
 "⚙️ Sistema":[
   st.Page("pages/12_Backup.py",title="Backup & Integridade",icon="💾",url_path="backup"),
   st.Page("pages/13_Administracao.py",title="Administração",icon="⚙️",url_path="admin"),
   st.Page("pages/14_Auditoria.py",title="Auditoria",icon="🧾",url_path="auditoria")]
}
pg=st.navigation(pages,position="sidebar")
pg.run()
