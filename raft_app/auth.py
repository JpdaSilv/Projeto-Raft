"""
auth.py — login simples por usuário/senha, com perfis (RAFT V2, seção 5).

Não usa OAuth nem serviço externo — é hash + sessão do Streamlit, adequado
pro estágio atual (uso interno, poucos usuários). Trocar por algo mais robusto
(ex: streamlit-authenticator com cookies persistentes) é evolução natural
quando o número de usuários crescer.
"""
import hashlib
import streamlit as st
from db_utils import query_df, execute

PERFIS_ACIMA_DE_OPERADOR = ("PCP", "ALMOXARIFADO", "ADMINISTRADOR")


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def verificar_login(username: str, senha: str):
    df = query_df(
        "SELECT username, senha_hash, nome, perfil FROM usuarios WHERE username = ? AND ativo = 1",
        (username.strip().lower(),),
    )
    if df.empty:
        return None
    linha = df.iloc[0]
    if linha["senha_hash"] != hash_senha(senha):
        return None
    return {"username": linha["username"], "nome": linha["nome"], "perfil": linha["perfil"]}


def criar_usuario(username: str, senha: str, nome: str, perfil: str):
    execute(
        "INSERT INTO usuarios (username, senha_hash, nome, perfil) VALUES (?,?,?,?)",
        (username.strip().lower(), hash_senha(senha), nome, perfil),
    )


def exigir_login():
    """Chame no topo de cada página. Bloqueia o conteúdo até logar."""
    if "usuario" not in st.session_state:
        st.title("🔒 RAFT — Login")
        with st.form("form_login"):
            username = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if entrar:
            usuario = verificar_login(username, senha)
            if usuario:
                st.session_state["usuario"] = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.stop()  # nada abaixo desta linha roda sem login


def exigir_perfil(*perfis_permitidos: str):
    """Chame após exigir_login() em páginas restritas a certos perfis."""
    exigir_login()
    perfil_atual = st.session_state["usuario"]["perfil"]
    if perfil_atual not in perfis_permitidos:
        st.error(f"Seu perfil ({perfil_atual}) não tem acesso a esta página.")
        st.stop()


def mostrar_usuario_logado():
    u = st.session_state.get("usuario")
    if u:
        with st.sidebar:
            st.caption(f"👤 {u['nome']} · {u['perfil']}")
            if st.button("Sair", use_container_width=True):
                del st.session_state["usuario"]
                st.rerun()
