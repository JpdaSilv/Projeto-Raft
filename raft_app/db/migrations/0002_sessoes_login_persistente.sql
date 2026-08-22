-- 0002_sessoes_login_persistente.sql
-- Permite login persistir entre recarregamentos de página (F5), sem precisar
-- digitar usuário/senha de novo toda hora. Token fica na URL (?token=...),
-- validado contra esta tabela, com expiração.

CREATE TABLE IF NOT EXISTS sessoes (
    token           TEXT PRIMARY KEY,
    username        TEXT NOT NULL,
    criado_em       TEXT DEFAULT (datetime('now','localtime')),
    expira_em       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessoes_expira ON sessoes(expira_em);
