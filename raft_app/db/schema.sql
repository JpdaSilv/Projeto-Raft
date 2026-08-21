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
