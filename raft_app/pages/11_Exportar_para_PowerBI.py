import streamlit as st
import pandas as pd
import io
from db_utils import query_df
from theme import aplicar_tema
from auth import exigir_perfil, mostrar_usuario_logado

st.set_page_config(page_title="Exportar para Power BI", page_icon="📤", layout="wide")
aplicar_tema()
exigir_perfil("PCP", "ALMOXARIFADO", "ADMINISTRADOR")
mostrar_usuario_logado()

st.title("📤 Exportar para Power BI")
st.caption(
    "Fecha o fluxo original do seu projeto: SQLite → Excel → Power BI. Gera um .xlsx com "
    "uma aba por tabela, pronto pra conectar como fonte de dados no Power BI Desktop."
)

TABELAS = {
    "Movimentações (fato)": "SELECT * FROM fact_movimentacao",
    "Controle de Utilização (fato)": "SELECT * FROM fact_controle_utilizacao",
    "Inventário Físico (fato)": "SELECT * FROM fact_inventario_fisico",
    "Produtos (dimensão)": "SELECT * FROM dim_produto",
    "Bobinas - Especificação (dimensão)": "SELECT * FROM dim_bobina_spec",
    "Bobinas - Físicas (dimensão)": "SELECT * FROM dim_bobina_fisica",
    "Componentes (dimensão)": "SELECT * FROM dim_componente",
    "Pedidos (dimensão)": "SELECT * FROM dim_pedido",
}

selecionadas = st.multiselect("Tabelas a exportar", options=list(TABELAS.keys()), default=list(TABELAS.keys()))

if st.button("Gerar arquivo Excel", type="primary", disabled=not selecionadas):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        resumo = []
        for nome in selecionadas:
            df = query_df(TABELAS[nome])
            aba = nome.split(" (")[0][:31]  # limite de 31 caracteres do Excel pra nome de aba
            df.to_excel(writer, sheet_name=aba, index=False)
            resumo.append({"Tabela": nome, "Linhas": len(df)})
        pd.DataFrame(resumo).to_excel(writer, sheet_name="Resumo", index=False)
    buffer.seek(0)

    st.success("Arquivo gerado.")
    st.dataframe(pd.DataFrame(resumo), use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Baixar raft_export.xlsx",
        data=buffer,
        file_name="raft_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

st.divider()
st.subheader("Como conectar no Power BI")
st.markdown("""
1. Abra o Power BI Desktop → **Obter Dados** → **Pasta de Trabalho do Excel**.
2. Selecione o `raft_export.xlsx` baixado acima.
3. Marque as abas que quer carregar (cada aba vira uma tabela no Power BI).
4. No **Editor poder Query**, relacione `fact_movimentacao.produto_codigo` com
   `Produtos.codigo`, e `fact_movimentacao.bobina_lote` com `Bobinas - Físicas.lote`
   — mesma lógica de relacionamento que você já usa no pipeline ETL principal.
5. Pra manter atualizado, repita a exportação e clique em **Atualizar** no Power BI
   (ou, se publicar num servidor com acesso à internet, dá pra automatizar via
   Power BI Gateway — passo mais avançado, fica pra quando isso for prioridade).
""")
