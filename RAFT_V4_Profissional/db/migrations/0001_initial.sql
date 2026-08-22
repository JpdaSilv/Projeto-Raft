PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS schema_migrations(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 arquivo TEXT UNIQUE NOT NULL,
 aplicado_em TEXT NOT NULL DEFAULT(datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS dim_produto(
 codigo TEXT PRIMARY KEY, descricao TEXT, tipo_telha TEXT, fator_bobina REAL,
 ativo INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN(0,1))
);

CREATE TABLE IF NOT EXISTS dim_bobina_spec(
 codigo TEXT PRIMARY KEY, descricao TEXT, desc_curta TEXT, medida TEXT, espessura TEXT,
 largura TEXT, tipo TEXT, cor TEXT, face TEXT, peso_especifico REAL, saldo_atual REAL,
 ativo INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN(0,1))
);

CREATE TABLE IF NOT EXISTS dim_bobina_fisica(
 lote TEXT PRIMARY KEY, codigo_spec TEXT REFERENCES dim_bobina_spec(codigo),
 galpao TEXT, local_fisico TEXT, n_ref TEXT, peso_real REAL CHECK(peso_real IS NULL OR peso_real>=0),
 data_pesagem TEXT, data_validade TEXT,
 status TEXT NOT NULL DEFAULT 'ESTOQUE' CHECK(status IN('ESTOQUE','CONSUMIDA','BLOQUEADA','INATIVA')),
 criado_em TEXT NOT NULL DEFAULT(datetime('now','localtime')),
 atualizado_em TEXT NOT NULL DEFAULT(datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS dim_componente(
 codigo TEXT PRIMARY KEY, descricao TEXT, tipo TEXT, espessura TEXT, desc_curta TEXT,
 estoque_atual REAL, ativo INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN(0,1))
);

CREATE TABLE IF NOT EXISTS dim_pedido(
 id INTEGER PRIMARY KEY AUTOINCREMENT, pedido TEXT NOT NULL, op TEXT, cliente TEXT,
 produto_codigo TEXT REFERENCES dim_produto(codigo), metragem REAL, tipo_prod TEXT, data TEXT,
 ativo INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN(0,1))
);

CREATE TABLE IF NOT EXISTS usuarios(
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL COLLATE NOCASE,
 senha_hash TEXT NOT NULL, nome TEXT NOT NULL, perfil TEXT NOT NULL
 CHECK(perfil IN('OPERADOR','PCP','ALMOXARIFADO','ADMINISTRADOR')),
 ativo INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN(0,1)),
 criado_em TEXT NOT NULL DEFAULT(datetime('now','localtime')), ultimo_login TEXT
);

CREATE TABLE IF NOT EXISTS sessoes(
 id INTEGER PRIMARY KEY AUTOINCREMENT, token_hash TEXT UNIQUE NOT NULL,
 username TEXT NOT NULL REFERENCES usuarios(username), criado_em TEXT NOT NULL DEFAULT(datetime('now','localtime')),
 expira_em TEXT NOT NULL, revogado_em TEXT
);

CREATE TABLE IF NOT EXISTS login_tentativas(
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, sucesso INTEGER NOT NULL DEFAULT 0 CHECK(sucesso IN(0,1)),
 data_hora TEXT NOT NULL DEFAULT(datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS fact_movimentacao(
 id INTEGER PRIMARY KEY AUTOINCREMENT, op TEXT, data TEXT NOT NULL, ano INTEGER, trimestre TEXT, mes TEXT,
 pedido TEXT, cliente TEXT, produto_codigo TEXT REFERENCES dim_produto(codigo), tipo TEXT,
 fator REAL, mt_prod REAL, mt_produzida REAL, tamanho TEXT,
 bobina_lote TEXT REFERENCES dim_bobina_fisica(lote), bobina_codigo TEXT REFERENCES dim_bobina_spec(codigo),
 peso_especifico REAL, cons_bob REAL, componente_codigo TEXT REFERENCES dim_componente(codigo),
 cons_comp REAL, eps_pir TEXT, cola TEXT, cons_cola REAL,
 contagem_prod1 REAL, contagem_prod2 REAL, contagem_telha2 REAL, contagem_sucata REAL,
 status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK(status IN('PENDENTE','VALIDADO','DEVOLVIDO','CANCELADO')),
 validado_por TEXT, validado_em TEXT, motivo_devolucao TEXT,
 criado_em TEXT NOT NULL DEFAULT(datetime('now','localtime')), usuario TEXT,
 atualizado_em TEXT NOT NULL DEFAULT(datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS fact_controle_utilizacao(
 id INTEGER PRIMARY KEY AUTOINCREMENT, bobina_lote TEXT NOT NULL REFERENCES dim_bobina_fisica(lote),
 utilizacao INTEGER NOT NULL, data TEXT NOT NULL, hora TEXT NOT NULL, peso_atual REAL CHECK(peso_atual IS NULL OR peso_atual>=0),
 caminho_etiqueta TEXT, criado_em TEXT NOT NULL DEFAULT(datetime('now','localtime')), usuario TEXT
);

CREATE TABLE IF NOT EXISTS fact_inventario_fisico(
 id INTEGER PRIMARY KEY AUTOINCREMENT, lote TEXT NOT NULL REFERENCES dim_bobina_fisica(lote),
 peso_fisico REAL NOT NULL CHECK(peso_fisico>=0), local_contado TEXT, data_contagem TEXT NOT NULL,
 usuario TEXT NOT NULL, obs TEXT, criado_em TEXT NOT NULL DEFAULT(datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS importacoes_totvs(
 id TEXT PRIMARY KEY, arquivo_nome TEXT NOT NULL, linhas INTEGER NOT NULL DEFAULT 0,
 novos INTEGER NOT NULL DEFAULT 0, divergentes INTEGER NOT NULL DEFAULT 0, aplicados INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL CHECK(status IN('PREVIA','APLICADA','CANCELADA','ERRO')),
 criado_em TEXT NOT NULL DEFAULT(datetime('now','localtime')), aplicado_em TEXT, usuario TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshot_totvs(
 id INTEGER PRIMARY KEY AUTOINCREMENT, importacao_id TEXT REFERENCES importacoes_totvs(id),
 lote TEXT NOT NULL, codigo_spec TEXT, peso_totvs REAL, local_fisico TEXT,
 arquivo_nome TEXT, importado_em TEXT NOT NULL DEFAULT(datetime('now','localtime')), usuario TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log(
 id INTEGER PRIMARY KEY AUTOINCREMENT, tabela TEXT NOT NULL, registro_id INTEGER NOT NULL, acao TEXT NOT NULL,
 campo TEXT, valor_anterior TEXT, valor_novo TEXT, motivo TEXT, usuario TEXT NOT NULL,
 data_hora TEXT NOT NULL DEFAULT(datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS app_config(
 chave TEXT PRIMARY KEY, valor TEXT, atualizado_em TEXT NOT NULL DEFAULT(datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_mov_data ON fact_movimentacao(data);
CREATE INDEX IF NOT EXISTS idx_mov_criado ON fact_movimentacao(criado_em);
CREATE INDEX IF NOT EXISTS idx_mov_produto ON fact_movimentacao(produto_codigo);
CREATE INDEX IF NOT EXISTS idx_mov_bobina ON fact_movimentacao(bobina_lote);
CREATE INDEX IF NOT EXISTS idx_mov_status ON fact_movimentacao(status);
CREATE INDEX IF NOT EXISTS idx_mov_pedido ON fact_movimentacao(pedido);
CREATE INDEX IF NOT EXISTS idx_pedido_numero ON dim_pedido(pedido);
CREATE INDEX IF NOT EXISTS idx_pedido_op ON dim_pedido(op);
CREATE INDEX IF NOT EXISTS idx_bobina_local ON dim_bobina_fisica(local_fisico);
CREATE INDEX IF NOT EXISTS idx_bobina_galpao ON dim_bobina_fisica(galpao);
CREATE INDEX IF NOT EXISTS idx_ctrl_bobina ON fact_controle_utilizacao(bobina_lote);
CREATE INDEX IF NOT EXISTS idx_ctrl_data ON fact_controle_utilizacao(data);
CREATE UNIQUE INDEX IF NOT EXISTS uq_ctrl_utilizacao ON fact_controle_utilizacao(bobina_lote,utilizacao);
CREATE INDEX IF NOT EXISTS idx_inv_lote ON fact_inventario_fisico(lote);
CREATE INDEX IF NOT EXISTS idx_snapshot_lote ON snapshot_totvs(lote);
CREATE INDEX IF NOT EXISTS idx_snapshot_importacao ON snapshot_totvs(importacao_id);
CREATE INDEX IF NOT EXISTS idx_audit_registro ON audit_log(tabela,registro_id);
CREATE INDEX IF NOT EXISTS idx_audit_data ON audit_log(data_hora);
CREATE INDEX IF NOT EXISTS idx_sessoes_expira ON sessoes(expira_em);
CREATE INDEX IF NOT EXISTS idx_login_tentativas ON login_tentativas(username,data_hora);

CREATE VIEW IF NOT EXISTS vw_bobina_saldo AS
SELECT f.lote,f.codigo_spec,s.desc_curta,s.descricao,f.galpao,f.local_fisico,f.n_ref,
       f.peso_real,f.status,
       COALESCE((SELECT SUM(m.cons_bob) FROM fact_movimentacao m
                 WHERE m.bobina_lote=f.lote AND m.status<>'CANCELADO'),0) AS consumido_raft,
       COALESCE(f.peso_real,0)-COALESCE((SELECT SUM(m.cons_bob) FROM fact_movimentacao m
                 WHERE m.bobina_lote=f.lote AND m.status<>'CANCELADO'),0) AS saldo_raft
FROM dim_bobina_fisica f LEFT JOIN dim_bobina_spec s ON s.codigo=f.codigo_spec;

CREATE VIEW IF NOT EXISTS vw_movimentacao_detalhada AS
SELECT m.*,s.desc_curta AS bobina_descricao,p.descricao AS produto_descricao
FROM fact_movimentacao m
LEFT JOIN dim_bobina_spec s ON s.codigo=m.bobina_codigo
LEFT JOIN dim_produto p ON p.codigo=m.produto_codigo;

CREATE VIEW IF NOT EXISTS vw_estoque_consolidado AS
SELECT codigo_spec,COUNT(*) lotes,SUM(COALESCE(peso_real,0)) peso_cadastrado,
       SUM(CASE WHEN status='BLOQUEADA' THEN 1 ELSE 0 END) bloqueadas
FROM dim_bobina_fisica WHERE status<>'INATIVA' GROUP BY codigo_spec;
