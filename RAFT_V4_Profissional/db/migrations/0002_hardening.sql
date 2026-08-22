-- V4: índices e objetos derivados são idempotentes.
CREATE INDEX IF NOT EXISTS idx_mov_data_status ON fact_movimentacao(data,status);
CREATE INDEX IF NOT EXISTS idx_mov_produto_status ON fact_movimentacao(produto_codigo,status);
CREATE INDEX IF NOT EXISTS idx_mov_bobina_status ON fact_movimentacao(bobina_lote,status);
CREATE INDEX IF NOT EXISTS idx_pedido_produto ON dim_pedido(produto_codigo);
CREATE INDEX IF NOT EXISTS idx_snapshot_lote_data ON snapshot_totvs(lote,importado_em);
CREATE INDEX IF NOT EXISTS idx_audit_usuario_data ON audit_log(usuario,data_hora);
