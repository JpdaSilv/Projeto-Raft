-- Compatibilidade com bancos da versão anterior.
-- SQLite não permite ADD COLUMN IF NOT EXISTS; a migração Python completa
-- as colunas faltantes de forma idempotente antes/depois desta etapa.

CREATE INDEX IF NOT EXISTS idx_mov_criado ON fact_movimentacao(criado_em);
CREATE INDEX IF NOT EXISTS idx_mov_pedido ON fact_movimentacao(pedido);
CREATE INDEX IF NOT EXISTS idx_bobina_local ON dim_bobina_fisica(local_fisico);
CREATE INDEX IF NOT EXISTS idx_bobina_galpao ON dim_bobina_fisica(galpao);
