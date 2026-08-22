-- ============================================================
-- SCHEMA — Projeto BI Raft (App de Movimentação e Controle)
-- Substitui a entrada manual nas abas: Movimentações e Controle_Utilização
-- ============================================================

-- Tabelas de referência (dimensões) — alimentadas a partir de
-- Especificação_Produtos, Especificação_Bobinas, Especificação_Componentes.
-- São só CONSULTADAS pelo app (populate via seed_from_excel.py),
-- não editadas por formulário.

CREATE TABLE IF NOT EXISTS dim_produto (
    codigo          TEXT PRIMARY KEY,
    descricao       TEXT,
    tipo_telha      TEXT,
    fator_bobina    REAL
);

-- Catálogo de especificações de bobina (por CÓDIGO, ex: '1.167M')
CREATE TABLE IF NOT EXISTS dim_bobina_spec (
    codigo          TEXT PRIMARY KEY,
    descricao       TEXT,
    desc_curta      TEXT,
    medida          TEXT,
    espessura       TEXT,
    largura         TEXT,
    tipo            TEXT,
    cor             TEXT,
    face            TEXT,
    peso_especifico REAL,
    saldo_atual     REAL
);

-- Bobinas FÍSICAS em estoque (por LOTE, ex: 'LL39100202') — é este
-- campo que aparece em Movimentações.Bobina e Controle_Utilização.Bobina.
-- Cada lote aponta para um código de especificação.
CREATE TABLE IF NOT EXISTS dim_bobina_fisica (
    lote            TEXT PRIMARY KEY,
    codigo_spec     TEXT REFERENCES dim_bobina_spec(codigo),
    galpao          TEXT,
    local_fisico    TEXT,
    n_ref           TEXT,
    peso_real       REAL,
    data_pesagem    TEXT,
    data_validade   TEXT
);

CREATE TABLE IF NOT EXISTS dim_componente (
    codigo          TEXT PRIMARY KEY,
    descricao       TEXT,
    tipo            TEXT,
    espessura       TEXT,
    desc_curta      TEXT,
    estoque_atual   REAL
);

-- Pedidos cadastrados pelo PCP (Comercial -> PCP -> Pedido, seção 4 do RAFT V2).
-- Uma linha por item de pedido; um "Pedido" pode ter mais de uma linha
-- (mesmo número de pedido com produtos/OPs diferentes) — dado real do Excel.
CREATE TABLE IF NOT EXISTS dim_pedido (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido          TEXT NOT NULL,
    op              TEXT,
    cliente         TEXT,
    produto_codigo  TEXT,
    metragem        REAL,
    tipo_prod       TEXT,
    data            TEXT
);
CREATE INDEX IF NOT EXISTS idx_dim_pedido_numero ON dim_pedido(pedido);

-- Usuários e perfis (RAFT V2, seção 5). Senha em hash — nunca texto puro.
CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    senha_hash      TEXT NOT NULL,
    nome            TEXT NOT NULL,
    perfil          TEXT NOT NULL CHECK (perfil IN ('OPERADOR','PCP','ALMOXARIFADO','ADMINISTRADOR')),
    ativo           INTEGER NOT NULL DEFAULT 1,
    criado_em       TEXT DEFAULT (datetime('now','localtime'))
);

-- ============================================================
-- Tabelas de MOVIMENTO (as que o app realmente escreve)
-- ============================================================

-- Espelha a aba "Movimentações": um registro por evento de produção.
-- Grão = evento de produção (não a OP — uma OP pode ter várias linhas).
CREATE TABLE IF NOT EXISTS fact_movimentacao (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    op                      TEXT,
    data                    TEXT NOT NULL,          -- ISO yyyy-mm-dd
    ano                     INTEGER,                 -- derivado de 'data'
    trimestre               TEXT,                    -- derivado de 'data'
    mes                     TEXT,                    -- derivado de 'data'
    pedido                  TEXT,
    cliente                 TEXT,
    produto_codigo          TEXT REFERENCES dim_produto(codigo),
    tipo                    TEXT,                    -- Produção / Retrabalho / Sucata...
    fator                   REAL,
    mt_prod                 REAL,
    mt_produzida            REAL,
    tamanho                 TEXT,
    bobina_lote             TEXT REFERENCES dim_bobina_fisica(lote),   -- ex: 'LL39100202' (instância física)
    bobina_codigo           TEXT REFERENCES dim_bobina_spec(codigo),   -- ex: '1.167M' (derivado do lote)
    peso_especifico         REAL,        -- 'P.E' — derivado do dim_bobina_spec
    cons_bob                REAL,
    componente_codigo       TEXT REFERENCES dim_componente(codigo),
    cons_comp               REAL,
    eps_pir                 TEXT,
    cola                    TEXT,
    cons_cola               REAL,
    contagem_prod1          REAL,
    contagem_prod2          REAL,
    contagem_telha2         REAL,
    contagem_sucata         REAL,
    status                  TEXT NOT NULL DEFAULT 'PENDENTE'
                            CHECK (status IN ('PENDENTE','VALIDADO','DEVOLVIDO','CANCELADO')),
    validado_por            TEXT,
    validado_em             TEXT,
    motivo_devolucao        TEXT,
    criado_em               TEXT DEFAULT (datetime('now','localtime')),
    usuario                 TEXT
);

-- Espelha a aba "Controle_Utilização": log de uso/pesagem de bobina.
CREATE TABLE IF NOT EXISTS fact_controle_utilizacao (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bobina_lote     TEXT REFERENCES dim_bobina_fisica(lote),
    utilizacao      INTEGER NOT NULL,   -- sequência de uso da bobina (1, 2, 3...)
    data            TEXT NOT NULL,
    hora            TEXT NOT NULL,
    peso_atual      REAL,
    caminho_etiqueta TEXT,
    criado_em       TEXT DEFAULT (datetime('now','localtime')),
    usuario         TEXT
);

CREATE INDEX IF NOT EXISTS idx_mov_data ON fact_movimentacao(data);
CREATE INDEX IF NOT EXISTS idx_mov_produto ON fact_movimentacao(produto_codigo);
CREATE INDEX IF NOT EXISTS idx_mov_bobina_lote ON fact_movimentacao(bobina_lote);
CREATE INDEX IF NOT EXISTS idx_ctrl_bobina_lote ON fact_controle_utilizacao(bobina_lote);
CREATE INDEX IF NOT EXISTS idx_ctrl_data ON fact_controle_utilizacao(data);

-- Log de auditoria (seção 2 e 103 do RAFT V2): quem mudou o quê, quando, valor
-- anterior/novo. Preenchido manualmente pelas ações críticas (validar, devolver,
-- apagar) -- não é trigger de banco, é chamada explícita no código Python.
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tabela          TEXT NOT NULL,
    registro_id     INTEGER NOT NULL,
    acao            TEXT NOT NULL,      -- 'VALIDAR' / 'DEVOLVER' / 'APAGAR' / 'EDITAR'
    campo           TEXT,
    valor_anterior  TEXT,
    valor_novo      TEXT,
    motivo          TEXT,
    usuario         TEXT NOT NULL,
    data_hora       TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_audit_tabela_registro ON audit_log(tabela, registro_id);

-- ============================================================
-- Importação TOTVS (seções 27-30 e 112): nunca sobrescreve
-- direto — cada importação vira um snapshot histórico, e só
-- DEPOIS de confirmado atualiza dim_bobina_fisica.peso_real.
-- ============================================================
CREATE TABLE IF NOT EXISTS snapshot_totvs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lote            TEXT NOT NULL,
    codigo_spec     TEXT,
    peso_totvs      REAL,
    arquivo_nome    TEXT,
    importado_em    TEXT DEFAULT (datetime('now','localtime')),
    usuario         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshot_lote ON snapshot_totvs(lote);
CREATE INDEX IF NOT EXISTS idx_snapshot_data ON snapshot_totvs(importado_em);

-- ============================================================
-- Inventário Físico (seção 24): terceira fonte de saldo,
-- nunca misturada com TOTVS nem RAFT (seção 110).
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_inventario_fisico (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lote            TEXT NOT NULL,
    peso_fisico     REAL NOT NULL,
    local_contado   TEXT,
    data_contagem   TEXT NOT NULL,
    usuario         TEXT NOT NULL,
    obs             TEXT,
    criado_em       TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_inventario_lote ON fact_inventario_fisico(lote);
