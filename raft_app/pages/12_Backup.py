import streamlit as st
from pathlib import Path
from datetime import datetime
from db_utils import DB_PATH, query_df
from theme import aplicar_tema
from auth import exigir_perfil, mostrar_usuario_logado

st.set_page_config(page_title="Backup", page_icon="💾", layout="wide")
aplicar_tema()
exigir_perfil("ADMINISTRADOR")
mostrar_usuario_logado()

st.title("💾 Backup do Banco de Dados")

if not DB_PATH.exists():
    st.error("Banco não encontrado.")
    st.stop()

tamanho_mb = DB_PATH.stat().st_size / (1024 * 1024)
totais = query_df("""
    SELECT
        (SELECT COUNT(*) FROM fact_movimentacao) AS movimentacoes,
        (SELECT COUNT(*) FROM fact_controle_utilizacao) AS controles,
        (SELECT COUNT(*) FROM fact_inventario_fisico) AS inventarios,
        (SELECT COUNT(*) FROM usuarios) AS usuarios
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Tamanho do banco", f"{tamanho_mb:.2f} MB")
c2.metric("Movimentações", int(totais["movimentacoes"]))
c3.metric("Controles de utilização", int(totais["controles"]))
c4.metric("Usuários cadastrados", int(totais["usuarios"]))

st.divider()

nome_backup = f"raft_app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
with open(DB_PATH, "rb") as f:
    dados = f.read()

st.download_button(
    "⬇️ Baixar backup agora",
    data=dados,
    file_name=nome_backup,
    mime="application/octet-stream",
    type="primary",
)

st.caption(
    "⚠️ Se o app estiver no Streamlit Community Cloud, o disco é **efêmero** — todo restart "
    "apaga qualquer arquivo salvo no servidor. Por isso o backup aqui é sempre baixado direto "
    "pro seu computador, nunca guardado no servidor. Faça isso com regularidade (toda semana, "
    "por exemplo) e guarde numa pasta local ou no Google Drive."
)

st.divider()
st.subheader("Restaurar um backup")
st.markdown("""
Pra restaurar: pare o app, substitua o arquivo `banco/raft_app.db` do seu projeto (local ou
no GitHub) pelo arquivo de backup baixado, e suba/reinicie de novo. **Cuidado:** isso troca o
banco inteiro — qualquer lançamento feito depois do backup escolhido se perde.
""")

st.divider()
st.subheader("Backup automático local (rodando fora do navegador)")
st.markdown("""
Se você roda o app localmente (não só na nuvem), pode automatizar isso com o Agendador de
Tarefas do Windows chamando o script abaixo uma vez por dia:
""")
st.code(
    'python db/backup_automatico.py --db "banco/raft_app.db" --destino "backups/"',
    language="bash",
)
