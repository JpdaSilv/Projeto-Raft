import streamlit as st
from db_utils import query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer, status
from auth import exigir_perfil, mostrar_usuario_logado

aplicar_tema(); exigir_perfil("ALMOXARIFADO","PCP","ADMINISTRADOR"); mostrar_usuario_logado()
page_header("Estoque & WMS", "Controle a posição física das bobinas separando claramente TOTVS, RAFT e localização operacional.", "ESTOQUE & RASTREABILIDADE", "VISÃO DO ALMOXARIFADO", "📦")
k=query_df("""SELECT COUNT(*) lotes,COALESCE(SUM(peso_real),0) peso_cadastrado,SUM(CASE WHEN local_fisico IS NULL OR trim(local_fisico)='' THEN 1 ELSE 0 END) sem_local,SUM(CASE WHEN status='BLOQUEADA' THEN 1 ELSE 0 END) bloqueadas FROM dim_bobina_fisica WHERE status<>'INATIVA'""").iloc[0]
a,b,c,d=st.columns(4)
with a:kpi("Lotes ativos",f"{int(k.lotes)}","bobinas","blue")
with b:kpi("Peso cadastrado",f"{float(k.peso_cadastrado):,.0f} kg","base atual","blue")
with c:kpi("Sem localização",f"{int(k.sem_local)}","endereços pendentes","amber" if k.sem_local else "green")
with d:kpi("Bloqueadas",f"{int(k.bloqueadas)}","não disponíveis","red" if k.bloqueadas else "green")
gals=query_df("SELECT DISTINCT galpao FROM dim_bobina_fisica WHERE galpao IS NOT NULL AND trim(galpao)<>'' ORDER BY galpao").galpao.tolist()
gal=st.selectbox("Filtrar galpão",["(todos)"]+gals)
where="" if gal=="(todos)" else "WHERE f.galpao=?"; params=() if not where else (gal,)
df=query_df(f"""SELECT f.lote,f.codigo_spec,s.desc_curta,f.galpao,f.local_fisico,f.peso_real,f.status,COALESCE((SELECT SUM(cons_bob) FROM fact_movimentacao m WHERE m.bobina_lote=f.lote AND m.status<>'CANCELADO'),0) consumido FROM dim_bobina_fisica f LEFT JOIN dim_bobina_spec s ON s.codigo=f.codigo_spec {where} ORDER BY f.galpao,f.local_fisico,f.lote""",params)
df["saldo_raft"]=df.peso_real.fillna(0)-df.consumido.fillna(0)
section("Mapa operacional", "Posição física e saldo estimado por lote")
st.dataframe(df,use_container_width=True,hide_index=True,column_config={"peso_real":st.column_config.NumberColumn("Peso cadastro",format="%.0f kg"),"consumido":st.column_config.NumberColumn("Consumido",format="%.1f kg"),"saldo_raft":st.column_config.NumberColumn("Saldo RAFT",format="%.1f kg")})
section("Alertas de estoque", "Exceções que precisam de ação do almoxarifado")
sem=df[df.local_fisico.isna() | (df.local_fisico=="")]; neg=df[df.saldo_raft<0]
if sem.empty and neg.empty: alert("Nenhuma exceção crítica encontrada no filtro atual.","success")
if not sem.empty: alert(f"<b>{len(sem)}</b> lote(s) sem endereço físico.","warn")
if not neg.empty: alert(f"<b>{len(neg)}</b> lote(s) com saldo RAFT negativo.","danger")
footer()
