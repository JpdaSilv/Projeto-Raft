import streamlit as st
from datetime import date,timedelta
from db_utils import query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_perfil, mostrar_usuario_logado
from page_runtime import run_page


def main():

    aplicar_tema(); exigir_perfil("PCP","ADMINISTRADOR"); mostrar_usuario_logado()
    page_header("Auditoria", "Veja quem criou, validou, devolveu, cancelou, contou ou importou dados.", "SISTEMA", "TRILHA DE EVENTOS", "🧾")
    c1,c2,c3=st.columns(3)
    de=c1.date_input("De",date.today()-timedelta(days=30)); ate=c2.date_input("Até",date.today()); acao=c3.multiselect("Ação",["CRIAR","VALIDAR","DEVOLVER","CANCELAR","CONTAR","IMPORTAR"],default=[])
    where=["date(data_hora) BETWEEN ? AND ?"]; p=[de.isoformat(),ate.isoformat()]
    if acao: where.append("acao IN ("+",".join(["?"]*len(acao))+")"); p+=acao
    df=query_df(f"SELECT id,data_hora,usuario,tabela,registro_id,acao,campo,valor_anterior,valor_novo,motivo FROM audit_log WHERE {' AND '.join(where)} ORDER BY id DESC LIMIT 2000",tuple(p))
    a,b,c=st.columns(3)
    with a:kpi("Eventos",str(len(df)),"no período","blue")
    with b:kpi("Usuários",str(df.usuario.nunique() if not df.empty else 0),"com atividade","green")
    with c:kpi("Ações",str(df.acao.nunique() if not df.empty else 0),"tipos diferentes","blue")
    section("Linha de auditoria", "Registro imutável das ações críticas")
    if df.empty: alert("Nenhum evento encontrado no período.","info")
    else: st.dataframe(df,use_container_width=True,hide_index=True)
    footer()

run_page('14_Auditoria', main)
