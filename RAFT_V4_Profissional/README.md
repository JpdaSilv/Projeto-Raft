# RAFT V4 • Controle Industrial

Sistema Streamlit para **produção, PCP, estoque/WMS, inventário físico, rastreabilidade de bobinas, integração TOTVS e exportação analítica**.

## O que mudou nesta versão

A V4 foi construída sobre o projeto enviado e mantém o domínio que já estava definido, mas corrige fragilidades e profissionaliza a experiência.

### Produto e design
- identidade visual única em todas as telas;
- navegação por áreas operacionais;
- KPIs com hierarquia visual;
- estados claros para pendente, validado, devolvido e cancelado;
- formulários e ações críticas separados;
- tela **Consultar e Editar** realmente editável, com revalidação pelo PCP;
- mensagens de erro amigáveis e código técnico para diagnóstico;
- tratamento de exceção por página, reduzindo o impacto de uma falha isolada.

### Arquitetura
- regras de negócio concentradas em `services.py`;
- acesso ao banco concentrado em `db_utils.py`;
- autenticação separada;
- runtime isolado para cada página;
- migração idempotente;
- views SQL para consultas recorrentes;
- índices para data, produto, pedido, bobina e status;
- transações `BEGIN IMMEDIATE` para operações críticas;
- índice único para sequência de utilização da bobina.

### Segurança
- novas senhas usam PBKDF2-HMAC-SHA256 com salt;
- hashes SHA-256 antigos podem ser migrados no primeiro login;
- sessão persistente guarda **somente o hash do token**;
- bloqueio temporário por tentativas inválidas;
- autorização por perfil;
- auditoria das alterações críticas;
- valores exibidos no HTML da aplicação são escapados quando apropriado.

### Banco
O modelo continua separando:

**TOTVS** → posição importada do ERP  
**RAFT** → consumo calculado pelos apontamentos  
**Físico** → contagem realizada no chão de fábrica

Views disponíveis:
- `vw_bobina_saldo`
- `vw_movimentacao_detalhada`
- `vw_estoque_consolidado`

## Estrutura

```text
RAFT_V4_Profissional/
├── app.py
├── auth.py
├── config.py
├── db_utils.py
├── page_runtime.py
├── services.py
├── theme.py
├── pages/
├── db/
│   ├── migrations/
│   ├── migrate.py
│   ├── seed_demo.py
│   ├── seed_from_excel.py
│   ├── backup_automatico.py
│   └── teste_concorrencia.py
├── banco/
├── backups/
├── tests/
└── .streamlit/
```

## Executar

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m db.migrate
python -m streamlit run app.py
```

## Base de demonstração

O ZIP já contém uma base de teste com dimensões e fatos fictícios.

Para recriar:

```bash
python -m db.migrate
python -m db.seed_demo
```

A demonstração contém:
- apontamentos de produção;
- pendências de PCP;
- utilização de bobinas;
- inventário físico;
- snapshots TOTVS;
- auditoria.

### Usuários de demonstração

| Usuário | Perfil | Senha |
|---|---|---|
| `joao` | ADMINISTRADOR | `raft12345` |
| `pcp1` | PCP | `raft12345` |
| `almox1` | ALMOXARIFADO | `raft12345` |
| `operador1` | OPERADOR | `raft12345` |

**Troque/remova esses usuários antes de qualquer uso real.**

## Importação TOTVS

Fluxo:

```text
Arquivo XLSX/CSV
      ↓
Leitura e normalização
      ↓
Prévia
      ↓
Divergências
      ↓
Confirmação
      ↓
Snapshot TOTVS
      ↓
Atualização do cadastro RAFT
```

A importação não deve apagar histórico de snapshots.

## Rastreabilidade de bobina

O **lote** é o identificador principal.

A etiqueta gera QR Code para:

```text
/Kardex da Bobina?lote=<LOTE>
```

O Kardex consolida:
- cadastro físico;
- peso inicial;
- consumo;
- saldo estimado;
- utilização/pesagens;
- linha do tempo.

## Backup

A interface usa a API de backup do SQLite para gerar uma cópia consistente.

Também existe:

```bash
python db/backup_automatico.py --db banco/raft_app.db --destino backups --manter 30
```

## Testes

```bash
python -m compileall -q .
python -m pytest -q
```

Os testes verificam bootstrap, views, índices e integridade referencial.

## Deploy Streamlit

1. Suba o conteúdo deste diretório para o repositório.
2. Configure o app para executar `app.py`.
3. Garanta `requirements.txt`.
4. Para produção, não use os usuários/senhas de demonstração.
5. Para vários usuários simultâneos em escala, migre o armazenamento para PostgreSQL.

## Próxima evolução

A arquitetura de domínio foi mantida preparada para a evolução:

**Streamlit → API/serviços → PostgreSQL → frontend dedicado**

Não é necessário fazer essa migração agora para continuar desenvolvendo o projeto.
