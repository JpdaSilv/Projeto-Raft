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

# 1. Cadastre pelo menos um usuário ADMINISTRADOR (só precisa fazer isso uma vez)
python db/gerenciar_usuarios.py criar --username joao --senha "SuaSenhaForte" --nome "João Pedro" --perfil ADMINISTRADOR
python db/gerenciar_usuarios.py listar   # conferir

# 2. Rodar o app
streamlit run app.py
# (Windows sem PATH configurado: python -m streamlit run app.py)
```

Usuários de teste já cadastrados no `raft_app.db` deste zip (troque as senhas antes de usar de verdade):

| Usuário | Senha | Perfil |
|---|---|---|
| `joao` | `raft2026` | ADMINISTRADOR |
| `operador1` | `producao123` | OPERADOR |
| `pcp1` | `pcp123` | PCP |

## O que mudou na Fase 1 (RAFT V2)

Baseado no documento `RAFT_V2_Prompt_Mestre.md` — implementei só o que dá pra terminar e
testar em dias, não o sistema inteiro (React/Vite, WMS, importação TOTVS, etc. ficam
pra fases futuras, quando fizer sentido).

- **Login por usuário/senha com 4 perfis** (`auth.py`, tabela `usuarios`). Senha nunca
  fica em texto puro — só o hash SHA-256.
- **Apontamento Operacional** (`pages/1_Apontamento_Operacional.py`) substitui a antiga
  "Nova Movimentação". Segue a seção 7 do documento à risca: o operador só informa
  Pedido, Tipo, Lote e Metragem Produzida — nunca OP, código da bobina ou peso
  específico. Cliente/Produto/Metragem do pedido vêm automáticos de `dim_pedido`
  (978 linhas migradas da aba Pedidos). Consumo = peso específico × metragem, calculado
  em tempo real antes mesmo de enviar.
- **Status do apontamento** (`PENDENTE` → `VALIDADO`/`DEVOLVIDO`), com `validado_por` e
  `validado_em` gravados — rastreabilidade mínima da seção 2 e 13.
- **Validação PCP** (`pages/4_Validação_PCP.py`), acessível só a perfis PCP/ADMINISTRADOR:
  lista apontamentos pendentes, valida ou devolve com motivo.
- **Consultar e Editar** agora é restrito a PCP/ALMOXARIFADO/ADMINISTRADOR — operador não
  edita/apaga lançamento (matriz de permissões da seção 104 do documento).

**Ainda não implementado** (fica pro backlog, conforme combinamos): WMS visual tipo mapa
de prateleira, PDF/QR Code de relatório completo (só a etiqueta individual existe),
dashboard com previsão/forecast, e a reescrita em React/Vite — essa última incompatível
com tudo o resto e só entra se você decidir trocar de stack de verdade.

## Fase 3 — Importação TOTVS, Etiqueta PDF, Inventário Físico

- **Importar TOTVS** (`pages/8_Importar_TOTVS.py`): upload de planilha, validação de colunas,
  prévia com diff (lote novo / peso divergente) antes de aplicar, snapshot histórico em
  `snapshot_totvs`, atualização do saldo só depois de confirmação explícita, auditoria de cada peso alterado.
- **Etiqueta da Bobina** (`pages/9_Etiqueta_da_Bobina.py`): gera PDF com QR Code que aponta
  pro Kardex do lote — testado gerando um PDF real e validando a assinatura binária do arquivo.
- **Inventário Físico** (`pages/10_Inventário_Físico.py`): contagem manual + reconciliação
  TOTVS × RAFT × FÍSICO lado a lado, nunca misturando as três fontes (seção 110).

## Fase 4 (última) — Sessão persistente, Power BI, backup, migrações, concorrência

- **Login persistente**: marque "Manter conectado" no login e a sessão sobrevive a um F5 —
  usa um token na URL (`?token=...`) validado contra a tabela `sessoes`, expira em 7 dias.
  Testado criando, validando e revogando uma sessão de verdade.
- **Modo WAL no SQLite** (`db_utils.py`): antes, uma escrita bloqueava o banco inteiro. Agora
  leituras e escritas concorrentes não travam entre si.
- **Teste de concorrência real** (`db/teste_concorrencia.py`): simula N operadores lançando
  ao mesmo tempo e reporta sucesso/falha. Rodado com 15 operadores × 10 lançamentos = **150
  inserts simultâneos, 0 falhas, 7.3ms por insert em média** — o SQLite com WAL aguenta a
  escala de uma fábrica. Rode de novo sempre que mudar de servidor:
  ```bash
  python db/teste_concorrencia.py --db banco/raft_app.db --operadores 15 --lancamentos 10
  ```
- **Exportar para Power BI** (`pages/11_Exportar_para_PowerBI.py`): gera um `.xlsx` com uma
  aba por tabela, pronto pra conectar no Power BI Desktop — fecha o fluxo original do seu
  projeto (SQLite → Excel → Power BI).
- **Backup** (`pages/12_Backup.py`): baixa uma cópia do banco atual direto pro seu computador
  (o disco do Streamlit Cloud é efêmero — nunca conte com arquivo salvo lá). Pra automação
  local: `python db/backup_automatico.py --db banco/raft_app.db --destino backups/ --manter 30`.
- **Migrações versionadas** (`db/migrations/`): a partir de agora, mudança de schema vira um
  arquivo novo numerado (`0003_algo.sql`), nunca edição direta do `schema.sql`. O script
  `db/migrate.py` aplica só o que ainda não rodou — testado criando o banco do zero e
  confirmando que rodar de novo não duplica nada.

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
