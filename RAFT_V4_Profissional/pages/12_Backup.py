import streamlit as st
from datetime import datetime
from config import DB_PATH,APP_VERSION
from db_utils import query_df,backup_database_bytes,database_health
from theme import aplicar_tema,page_header,section,kpi,alert,footer
from auth import exigir_perfil,mostrar_usuario_logado
from page_runtime import run_page

def main():
    aplicar_tema(); exigir_perfil("ADMINISTRADOR"); mostrar_usuario_logado()
    page_header("Backup & integridade","Crie uma cópia consistente e verifique a saúde do banco antes de operações importantes.","SISTEMA","ADMINISTRADOR","💾")
    if not DB_PATH.exists():
        alert("Banco não encontrado.","danger"); st.stop()
    health=database_health()
    size=DB_PATH.stat().st_size/1024/1024
    a,b,c,d=st.columns(4)
    with a:kpi("Banco",f"{size:.2f} MB","arquivo local","blue")
    with b:kpi("Movimentações",int(query_df("SELECT COUNT(*) n FROM fact_movimentacao").iloc[0].n),"registros","blue")
    with c:kpi("Auditoria",int(query_df("SELECT COUNT(*) n FROM audit_log").iloc[0].n),"eventos","green")
    with d:kpi("Integridade","OK" if health["integrity"]=="ok" and health["foreign_key_errors"]==0 else "ATENÇÃO",
              f"FK: {health['foreign_key_errors']}","green" if health["foreign_key_errors"]==0 else "red")
    section("Saúde técnica","Validação rápida do SQLite")
    st.dataframe(query_df("SELECT 'SQLite' tecnologia, ? versao, ? journal_mode, ? foreign_keys, ? fk_erros",
                           (APP_VERSION,health["journal_mode"],health["foreign_keys"],health["foreign_key_errors"])),
                 use_container_width=True,hide_index=True)
    section("Backup manual","A cópia é gerada pelo mecanismo de backup do SQLite para evitar inconsistências de WAL.")
    if st.button("Preparar backup agora",type="primary",use_container_width=True):
        try:
            data=backup_database_bytes()
            nome=f"raft_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            st.download_button("Baixar backup seguro",data,nome,"application/x-sqlite3",type="primary",use_container_width=True)
            alert("Backup preparado com sucesso. Guarde-o fora do ambiente do Streamlit.","success")
        except Exception as e: st.error(f"Falha ao gerar backup: {e}")
    alert("Em produção multiusuário, o próximo salto é PostgreSQL. SQLite continua excelente para uma operação local/pequena e para prototipação.","info")
    footer()

run_page("Backup",main)
