import streamlit as st
import pandas as pd
from db_utils import query_df, execute, log_auditoria
from theme import aplicar_tema
from auth import exigir_perfil, mostrar_usuario_logado

st.set_page_config(page_title="Importar TOTVS", page_icon="📥", layout="wide")
aplicar_tema()
exigir_perfil("PCP", "ALMOXARIFADO", "ADMINISTRADOR")
mostrar_usuario_logado()

st.title("📥 Importação de Relatório TOTVS")
st.caption(
    "Fluxo seguro (seção 112): nada é gravado direto no estoque. Toda importação vira um "
    "snapshot histórico primeiro, e só atualiza o saldo cadastrado depois da sua confirmação."
)

st.markdown("**Formato esperado do arquivo** (.xlsx ou .csv): colunas `Lote`, `Código` e `Peso Real` "
            "(mesmos nomes da aba Banco_Bobina do seu Excel).")

arquivo = st.file_uploader("Selecione o relatório exportado do TOTVS", type=["xlsx", "csv"])

if arquivo is None:
    st.info("Nenhum arquivo selecionado ainda.")
    st.stop()

# --- ANÁLISE ---
try:
    if arquivo.name.endswith(".csv"):
        novo = pd.read_csv(arquivo)
    else:
        novo = pd.read_excel(arquivo)
except Exception as e:
    st.error(f"Não consegui ler o arquivo: {e}")
    st.stop()

novo.columns = [c.strip() for c in novo.columns]
colunas_necessarias = {"Lote", "Código", "Peso Real"}

# --- VALIDAÇÃO ---
faltando = colunas_necessarias - set(novo.columns)
if faltando:
    st.error(f"Arquivo inválido: faltam as colunas {sorted(faltando)}. Importação bloqueada.")
    st.stop()

novo = novo.rename(columns={"Lote": "lote", "Código": "codigo_spec", "Peso Real": "peso_totvs"})
novo = novo.dropna(subset=["lote"])
linhas_invalidas = novo[novo["peso_totvs"].isna() | (novo["peso_totvs"] < 0)]
if not linhas_invalidas.empty:
    st.warning(f"{len(linhas_invalidas)} linha(s) com peso ausente ou negativo serão ignoradas na importação.")
novo = novo[novo["peso_totvs"].notna() & (novo["peso_totvs"] >= 0)]

if novo.empty:
    st.error("Nenhuma linha válida encontrada após a validação. Importação bloqueada.")
    st.stop()

# --- PRÉVIA (diff contra o que já está cadastrado) ---
atual = query_df("SELECT lote, codigo_spec, peso_real AS peso_atual FROM dim_bobina_fisica")
diff = novo.merge(atual, on="lote", how="left")
diff["situacao"] = "sem alteração"
diff.loc[diff["peso_atual"].isna(), "situacao"] = "LOTE NOVO"
diff.loc[(diff["peso_atual"].notna()) & (diff["peso_totvs"] != diff["peso_atual"]), "situacao"] = "PESO DIVERGENTE"
diff["diferenca"] = diff["peso_totvs"] - diff["peso_atual"]

mudancas = diff[diff["situacao"] != "sem alteração"]

st.divider()
st.subheader("Prévia da importação")
c1, c2, c3 = st.columns(3)
c1.metric("Linhas no arquivo", len(novo))
c2.metric("Lotes novos", int((diff["situacao"] == "LOTE NOVO").sum()))
c3.metric("Pesos divergentes", int((diff["situacao"] == "PESO DIVERGENTE").sum()))

if mudancas.empty:
    st.success("Nenhuma mudança detectada — o cadastro já está igual ao arquivo.")
    st.stop()

st.dataframe(
    mudancas[["lote", "codigo_spec_x", "peso_atual", "peso_totvs", "diferenca", "situacao"]],
    use_container_width=True, hide_index=True,
    column_config={"codigo_spec_x": "Código", "peso_atual": "Peso atual (RAFT)",
                    "peso_totvs": "Peso no arquivo", "diferenca": "Diferença", "situacao": "Situação"},
)

# --- CONFIRMAÇÃO ---
st.divider()
confirmar = st.checkbox("Revisei a prévia acima e confirmo a importação.")
if st.button("Confirmar e aplicar importação", type="primary", disabled=not confirmar):
    usuario = st.session_state["usuario"]["nome"]

    # SNAPSHOT primeiro (histórico imutável, seção 30)
    for _, row in novo.iterrows():
        execute(
            "INSERT INTO snapshot_totvs (lote, codigo_spec, peso_totvs, arquivo_nome, usuario) VALUES (?,?,?,?,?)",
            (row["lote"], row["codigo_spec"], row["peso_totvs"], arquivo.name, usuario),
        )

    # TRANSAÇÃO: atualiza dim_bobina_fisica só pra lotes que já existiam
    for _, row in mudancas[mudancas["situacao"] == "PESO DIVERGENTE"].iterrows():
        execute("UPDATE dim_bobina_fisica SET peso_real = ? WHERE lote = ?",
                (row["peso_totvs"], row["lote"]))
        log_auditoria("dim_bobina_fisica", 0, "EDITAR", usuario,
                       campo=f"peso_real (lote {row['lote']})",
                       valor_anterior=row["peso_atual"], valor_novo=row["peso_totvs"],
                       motivo=f"Importação TOTVS: {arquivo.name}")

    novos_lotes = mudancas[mudancas["situacao"] == "LOTE NOVO"]
    if not novos_lotes.empty:
        st.warning(
            f"{len(novos_lotes)} lote(s) novo(s) apareceram no arquivo mas NÃO foram cadastrados "
            f"automaticamente em dim_bobina_fisica (falta galpão/local físico, que o TOTVS não informa). "
            f"Cadastre-os manualmente ou peça pro Almoxarifado localizar fisicamente antes de usar."
        )

    log_auditoria("snapshot_totvs", 0, "EDITAR", usuario,
                   motivo=f"Importação de {len(novo)} linha(s) do arquivo {arquivo.name}")

    st.success(f"Importação aplicada: {len(mudancas[mudancas['situacao']=='PESO DIVERGENTE'])} peso(s) atualizado(s), "
               f"snapshot de {len(novo)} linha(s) salvo em snapshot_totvs.")
    st.cache_data.clear()
