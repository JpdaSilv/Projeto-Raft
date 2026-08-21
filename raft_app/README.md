# Raft App — Movimentação e Controle (Streamlit)

App em Python puro (Streamlit) que substitui o preenchimento manual das abas
**Movimentações** e **Controle_Utilização** no Excel. Escreve direto num banco
SQLite (`banco/raft_app.db`), acessível pelo celular (mesma rede) ou publicado
de graça no Streamlit Community Cloud.

## Por que assim, e não outra coisa

- **Power BI já resolve a visualização no celular** (app nativo). Este projeto
  não tenta refazer dashboard — ele resolve o problema real, que é *lançar
  dado* sem abrir o Excel.
- Streamlit foi escolhido em vez de FastAPI+React porque mantém tudo dentro do
  que você já está estudando (Python + Pandas + SQLite), sem precisar de um
  currículo novo de frontend/API para um MVP de uso interno.

## Estrutura

```
raft_app/
├── app.py                          # Home: KPIs do dia/mês + últimos lançamentos
├── db_utils.py                     # Conexão SQLite + queries cacheadas
├── pages/
│   ├── 1_Nova_Movimentação.py      # Formulário -> fact_movimentacao
│   ├── 2_Controle_de_Utilização.py # Formulário -> fact_controle_utilizacao
│   └── 3_Consultar_e_Editar.py     # Consulta com filtros + exclusão por ID
├── db/
│   ├── schema.sql                  # DDL completo (dims + facts)
│   └── seed_from_excel.py          # Popula as dimensões a partir do Projeto.xlsm
├── banco/
│   └── raft_app.db                 # SQLite já criado e populado com seus dados reais
└── requirements.txt
```

## Modelo de dados — decisão importante

O campo **"Bobina"** que aparece em `Movimentações` (ex: `1.167M`) é o
**código de especificação** (catálogo). Já o campo **"Lote"** (ex:
`LL39100202`) é a **bobina física** em estoque, que referencia um código de
especificação. No app, você escolhe pelo **Lote** (é o que está na etiqueta
física da bobina) e o Código/Descrição/Peso Específico vêm automáticos —
elimina a redigitação e o erro de "descrição não bate com o código", que era
um risco real no preenchimento manual do Excel.

```
dim_produto           dim_bobina_spec          dim_componente
 (516 produtos)         (44 especificações)      (11 componentes)
      ▲                        ▲                        ▲
      │                        │ codigo_spec            │
      │                 dim_bobina_fisica                │
      │                  (194 lotes em estoque)           │
      │                        ▲                          │
      └──────────── fact_movimentacao ─────────────────────┘
                     fact_controle_utilizacao (usa lote)
```

## Como rodar

```bash
cd raft_app
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`. Para acessar do celular na mesma rede
Wi-Fi, use o **Network URL** que o Streamlit mostra no terminal
(algo como `http://192.168.x.x:8501`).

## Como integrar ao Projeto_BI_Raft existente

O `raft_app.db` é um banco separado de propósito — assim você não corre risco
de quebrar as `stg_*`/views que já estão em produção no `raft.db` enquanto
testa o app. Duas formas de juntar:

**Opção A — apontar o app pro banco principal (recomendado depois de testar):**
Edite `DB_PATH` em `db_utils.py` para `../banco/raft.db` (ou copie este app
para dentro de `Projeto_BI_Raft/`) e rode o seed apontando pro mesmo arquivo:

```bash
python db/seed_from_excel.py --xlsm "dados/Projeto.xlsm" --db "../banco/raft.db"
```

As tabelas `fact_movimentacao`/`fact_controle_utilizacao`/`dim_*` novas
convivem com as `stg_*` e `vw_*` existentes sem conflito de nome.

**Opção B — manter separado e unir via view:** criar em `sql/views.sql` uma
`vw_movimentacao_app` que faz `UNION ALL` entre o histórico que já veio do
Excel (`stg_movimentacoes`) e o que passa a vir do app
(`fact_movimentacao`), com uma coluna `origem` ('excel' / 'app') pra
rastreabilidade.

## Recarregar as dimensões (produtos/bobinas/componentes mudaram no Excel)

```bash
python db/seed_from_excel.py --xlsm "caminho/Projeto.xlsm" --db "banco/raft_app.db"
```
Isso só recarrega `dim_*` (referência). Os lançamentos em `fact_*` nunca são
apagados por esse script.

## Publicar de graça pra acessar de qualquer lugar (não só na mesma rede)

1. Suba esta pasta num repositório GitHub (privado, se preferir).
2. Em https://share.streamlit.io conecte o repo e aponte pra `app.py`.
3. **Atenção:** o SQLite do Streamlit Cloud não é persistente entre deploys/
   reinícios. Pra uso real (não só teste), depois trocar por um Postgres
   gerenciado (ex: Supabase/Neon, camada grátis) é o próximo passo natural —
   mas isso é uma decisão pra quando o app já estiver validado no dia a dia,
   não agora.
