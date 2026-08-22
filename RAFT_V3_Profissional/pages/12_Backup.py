import io
from datetime import datetime
import streamlit as st
from config import DB_PATH
from db_utils import query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_perfil, mostrar_usuario_logado

aplicar_tema(); exigir_perfil("ADMINISTRADOR"); mostrar_usuario_logado()
page_header("Backup & integridade", "Gere uma cópia consistente do banco e acompanhe o volume dos principais registros.", "SISTEMA", "ADMINISTRADOR", "💾")
if not DB_PATH.exists(): alert("Banco não encontrado.","danger"); st.stop()
a,b,c,d=st.columns(4)
with a:kpi("Tamanho do banco",f"{DB_PATH.stat().st_size/1024/1024:.2f} MB","arquivo atual","blue")
with b:kpi("Movimentações",f"{int(query_df('SELECT COUNT(*) n FROM fact_movimentacao').iloc[0].n)}","registros","blue")
with c:kpi("Auditoria",f"{int(query_df('SELECT COUNT(*) n FROM audit_log').iloc[0].n)}","eventos","green")
with d:kpi("Snapshots TOTVS",f"{int(query_df('SELECT COUNT(*) n FROM snapshot_totvs').iloc[0].n)}","histórico","blue")
section("Backup manual", "O download é feito diretamente a partir do banco atual")
if st.button("Preparar backup agora",type="primary"):
    data=DB_PATH.read_bytes(); nome=f"raft_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"; st.download_button("Baixar backup",data,nome,"application/octet-stream",type="primary")
alert("Para produção em nuvem, trate SQLite como armazenamento local e mantenha cópia externa. Para operação multiusuário em escala, o próximo passo natural é PostgreSQL.","info")
footer()
