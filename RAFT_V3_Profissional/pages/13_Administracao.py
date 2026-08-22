import streamlit as st
from db_utils import query_df
from theme import aplicar_tema, page_header, section, kpi, alert, footer
from auth import exigir_perfil, criar_usuario

aplicar_tema(); user=exigir_perfil("ADMINISTRADOR")
page_header("Administração", "Gerencie usuários e acompanhe a saúde técnica do ambiente.", "SISTEMA", "ACESSO RESTRITO", "⚙️")
aba1,aba2=st.tabs(["Usuários","Saúde do banco"])
with aba1:
    section("Novo usuário", "Senhas são armazenadas com hash forte e salt")
    with st.form("novo_user"):
        a,b=st.columns(2); nome=a.text_input("Nome"); username=b.text_input("Usuário")
        c,d=st.columns(2); senha=c.text_input("Senha",type="password"); perfil=d.selectbox("Perfil",["OPERADOR","PCP","ALMOXARIFADO","ADMINISTRADOR"])
        ok=st.form_submit_button("Criar usuário",type="primary")
    if ok:
        try: criar_usuario(username,senha,nome,perfil); alert("Usuário criado.","success"); st.rerun()
        except Exception as e: st.error(str(e))
    df=query_df("SELECT id,username,nome,perfil,ativo,criado_em,ultimo_login FROM usuarios ORDER BY id")
    a,b=st.columns(2)
    with a:kpi("Usuários",str(len(df)),"cadastrados","blue")
    with b:kpi("Ativos",str(int(df.ativo.sum()) if not df.empty else 0),"com acesso","green")
    st.dataframe(df,use_container_width=True,hide_index=True)
with aba2:
    section("Integridade", "Parâmetros técnicos do SQLite")
    st.code("SQLite • WAL • foreign_keys=ON • busy_timeout=15000")
    st.dataframe(query_df("PRAGMA database_list"),use_container_width=True,hide_index=True)
    st.dataframe(query_df("SELECT name,type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name"),use_container_width=True,hide_index=True)
footer()
