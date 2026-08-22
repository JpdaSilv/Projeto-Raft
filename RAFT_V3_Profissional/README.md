# RAFT V3 • Controle Industrial

Aplicação Streamlit para controle de produção, PCP, rastreabilidade de bobinas, estoque/WMS, inventário físico e integração controlada com relatórios TOTVS.

## V3.1 — Redesign profissional

Esta versão foi remodelada com foco em duas frentes:

1. **Produto:** navegação por áreas, dashboard operacional, estados visuais, hierarquia de informação e identidade visual consistente.
2. **Arquitetura:** SQLite/WAL, foreign keys, transações, auditoria, autenticação forte, importação TOTVS em duas etapas e separação entre TOTVS, RAFT e físico.

### Estrutura visual

- 🏠 **Visão Geral** — central operacional e ações rápidas.
- 🏭 **Operação** — apontamento e controle de utilização.
- 📋 **Controle** — consulta/edição e fila PCP.
- 📦 **Estoque & Rastreabilidade** — Kardex, WMS, inventário e etiqueta QR.
- 📊 **Gestão** — dashboard, importação TOTVS e exportação Power BI.
- ⚙️ **Sistema** — backup, administração e auditoria.

## Rodar localmente

```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python -m db.migrate
python -m streamlit run app.py
```

## Base de demonstração

A base entregue no ZIP é uma **base de testes**, sem valor operacional. Ela mantém as dimensões importadas e contém fatos fictícios para que todas as telas possam ser avaliadas imediatamente.

Para recriá-la:

```bash
python -m db.migrate
python -m db.seed_demo
```

O cenário de demonstração inclui:

- 36 apontamentos;
- 3 pendências de PCP;
- eventos de utilização de bobina;
- 18 contagens de inventário;
- snapshot TOTVS;
- eventos de auditoria.

## Migrações

O migrador é idempotente e foi reforçado para bancos antigos que não possuem colunas adicionadas em versões posteriores.

```bash
python -m db.migrate --db caminho/do/banco.db
```

## Segurança

- PBKDF2-HMAC-SHA256 com salt para novas senhas;
- migração automática de hashes SHA-256 antigos no primeiro login;
- sessão persistente usando token aleatório e hash no banco;
- bloqueio temporário após tentativas inválidas;
- autorização por perfil;
- auditoria das ações críticas.

## Regra central de estoque

O RAFT não trata todas as fontes como se fossem a mesma coisa:

- **TOTVS:** posição importada do ERP;
- **RAFT:** consumo calculado a partir dos apontamentos;
- **Físico:** contagem realizada no chão de fábrica.

A diferença entre essas fontes é informação operacional, não algo que deve ser escondido.

## QR Code

Cada etiqueta pode abrir o Kardex de uma bobina pelo lote. O lote permanece como identificador principal da rastreabilidade.

## Power BI

A exportação gera um Excel com fatos, dimensões, snapshots e auditoria, preservando nomes estáveis para facilitar o modelo analítico.

## Testes

```bash
python -m compileall -q .
python -m pytest -q
```

O teste de fumaça valida o bootstrap do banco e a presença das tabelas centrais.

## Próxima evolução arquitetural

Para uma operação com múltiplos usuários simultâneos em escala, integrações externas e disponibilidade contínua, a evolução recomendada é:

**Streamlit → FastAPI → PostgreSQL → React**, mantendo o mesmo domínio de dados e as mesmas regras de negócio.

## Usuários da base de demonstração

Todos os usuários de teste usam a senha **`raft12345`**:

| Usuário | Perfil |
|---|---|
| `joao` | ADMINISTRADOR |
| `pcp1` | PCP |
| `almox1` | ALMOXARIFADO |
| `operador1` | OPERADOR |

**Troque/remova esses usuários antes de qualquer uso real.**
