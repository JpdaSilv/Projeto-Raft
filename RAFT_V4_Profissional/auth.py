"""Autenticação, sessão e autorização do RAFT V4."""
import hashlib,hmac,secrets
from datetime import datetime,timedelta
import html
import streamlit as st
from config import SESSION_DAYS
from db_utils import query_df,transaction

PBKDF2_ITER=420_000
LOCKOUT_MINUTES=10
MAX_FAILURES=6

def hash_senha(senha):
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac("sha256",senha.encode("utf-8"),salt,PBKDF2_ITER)
    return f"pbkdf2_sha256${PBKDF2_ITER}${salt.hex()}${digest.hex()}"

def verificar_hash(senha,stored):
    if not stored: return False
    try:
        prefix,it,salt_hex,digest_hex=stored.split("$",3)
        if prefix!="pbkdf2_sha256": return False
        candidate=hashlib.pbkdf2_hmac("sha256",senha.encode("utf-8"),bytes.fromhex(salt_hex),int(it))
        return hmac.compare_digest(candidate.hex(),digest_hex)
    except Exception:
        # Compatibilidade legada somente para migração; novo cadastro nunca usa isso.
        legacy=hashlib.sha256(senha.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy,stored)

def _validar_credenciais(username,senha,nome=None):
    username=username.strip().lower()
    if len(username)<3: raise ValueError("Usuário deve ter pelo menos 3 caracteres.")
    if len(senha)<8: raise ValueError("Senha deve ter pelo menos 8 caracteres.")
    if nome is not None and len(nome.strip())<2: raise ValueError("Informe o nome completo.")

def criar_usuario(username,senha,nome,perfil):
    _validar_credenciais(username,senha,nome)
    if perfil not in {"OPERADOR","PCP","ALMOXARIFADO","ADMINISTRADOR"}:
        raise ValueError("Perfil inválido.")
    with transaction() as conn:
        conn.execute("INSERT INTO usuarios(username,senha_hash,nome,perfil) VALUES(?,?,?,?)",
                     (username,hash_senha(senha),nome.strip(),perfil))

def _bloqueado(conn,username):
    row=conn.execute("""SELECT COUNT(*) FROM login_tentativas
        WHERE lower(coalesce(username,''))=? AND sucesso=0
        AND data_hora>=datetime('now','localtime',?)""",
        (username.lower(),f"-{LOCKOUT_MINUTES} minutes")).fetchone()
    return row[0]>=MAX_FAILURES

def verificar_login(username,senha):
    username=username.strip().lower()
    with transaction() as conn:
        if _bloqueado(conn,username): return None,"Conta temporariamente bloqueada por tentativas inválidas."
        row=conn.execute("SELECT id,username,senha_hash,nome,perfil FROM usuarios WHERE username=? AND ativo=1",(username,)).fetchone()
        ok=bool(row and verificar_hash(senha,row["senha_hash"]))
        conn.execute("INSERT INTO login_tentativas(username,sucesso) VALUES(?,?)",(username,int(ok)))
        if not ok: return None,"Usuário ou senha inválidos."
        if not row["senha_hash"].startswith("pbkdf2_sha256$"):
            conn.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",(hash_senha(senha),row["id"]))
        conn.execute("UPDATE usuarios SET ultimo_login=datetime('now','localtime') WHERE id=?",(row["id"],))
        return {"id":row["id"],"username":row["username"],"nome":row["nome"],"perfil":row["perfil"]},None

def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def criar_sessao(username):
    raw=secrets.token_urlsafe(48)
    expira=datetime.now()+timedelta(days=SESSION_DAYS)
    with transaction() as conn:
        conn.execute("INSERT INTO sessoes(token_hash,username,expira_em) VALUES(?,?,?)",
                     (_token_hash(raw),username,expira.isoformat(timespec="seconds")))
    return raw

def validar_sessao(raw):
    if not raw: return None
    with transaction() as conn:
        row=conn.execute("""SELECT s.username,u.nome,u.perfil,u.id
            FROM sessoes s JOIN usuarios u ON u.username=s.username
            WHERE s.token_hash=? AND s.revogado_em IS NULL
            AND s.expira_em>datetime('now','localtime') AND u.ativo=1""",
            (_token_hash(raw),)).fetchone()
        return dict(row) if row else None

def revogar_sessao(raw):
    if not raw: return
    with transaction() as conn:
        conn.execute("UPDATE sessoes SET revogado_em=datetime('now','localtime') WHERE token_hash=?",
                     (_token_hash(raw),))

def exigir_login():
    if "usuario" in st.session_state: return st.session_state["usuario"]
    raw=st.query_params.get("token")
    if raw:
        user=validar_sessao(raw)
        if user:
            st.session_state["usuario"]=user
            st.session_state["_session_token"]=raw
            st.query_params.clear()
            return user
    st.markdown("""<div class='raft-login-wrap'><div class='raft-login-card'>
      <span class='raft-login-badge'>RAFT • CONTROLE INDUSTRIAL</span>
      <div style='font-size:40px;font-weight:900;margin-top:14px;'>Operação sob controle.</div>
      <div style='font-size:14px;color:#91a0b2;margin-top:7px;'>Produção • PCP • Estoque • Rastreabilidade</div>
    </div></div>""",unsafe_allow_html=True)
    _,center,_=st.columns([1.2,1,1.2])
    with center:
        st.markdown("### Entrar")
        with st.form("login"):
            username=st.text_input("Usuário",autocomplete="username")
            senha=st.text_input("Senha",type="password",autocomplete="current-password")
            manter=st.checkbox(f"Manter conectado por {SESSION_DAYS} dias",value=True)
            entrar=st.form_submit_button("Entrar no RAFT",type="primary",use_container_width=True)
        if entrar:
            user,erro=verificar_login(username,senha)
            if user:
                st.session_state["usuario"]=user
                if manter: st.session_state["_session_token"]=criar_sessao(user["username"])
                st.rerun()
            st.error(erro)
        if not query_df("SELECT id FROM usuarios LIMIT 1").shape[0]:
            with st.expander("Primeiro acesso — criar administrador"):
                with st.form("bootstrap"):
                    n=st.text_input("Nome")
                    u=st.text_input("Usuário")
                    p=st.text_input("Senha",type="password")
                    p2=st.text_input("Confirmar senha",type="password")
                    ok=st.form_submit_button("Criar administrador")
                if ok:
                    if p!=p2: st.error("As senhas não conferem.")
                    else:
                        try: criar_usuario(u,p,n,"ADMINISTRADOR"); st.success("Administrador criado. Faça login.")
                        except Exception as e: st.error(str(e))
    st.stop()

def exigir_perfil(*perfis):
    user=exigir_login()
    if user["perfil"] not in perfis:
        st.error("Seu perfil não possui permissão para esta área.")
        st.stop()
    return user

def mostrar_usuario_logado():
    user=st.session_state.get("usuario")
    if not user: return
    with st.sidebar:
        st.markdown(f"""<div class='raft-card' style='padding:13px 14px;margin:8px 0 12px;'>
          <div style='font-size:10px;color:#738398;text-transform:uppercase;letter-spacing:.08em;'>Sessão ativa</div>
          <div style='font-weight:800;margin-top:5px;'>{html.escape(str(user['nome']))}</div>
          <div style='font-size:10px;color:#60a5fa;margin-top:3px;'>{html.escape(str(user['perfil']))}</div>
        </div>""",unsafe_allow_html=True)
        if st.button("Sair",use_container_width=True):
            revogar_sessao(st.session_state.get("_session_token"))
            st.session_state.clear(); st.query_params.clear(); st.rerun()
