"""Regras de negócio do RAFT V4. Telas não devem gravar SQL crítico diretamente."""
from datetime import datetime
from db_utils import transaction,registrar_auditoria,clear_caches

def _get_bobina(conn,lote):
    return conn.execute("""SELECT f.lote,f.codigo_spec,s.peso_especifico,f.peso_real,f.status
        FROM dim_bobina_fisica f LEFT JOIN dim_bobina_spec s ON s.codigo=f.codigo_spec
        WHERE f.lote=?""",(lote,)).fetchone()

def criar_apontamento(item,lote,tipo,metragem,usuario):
    if metragem<=0: raise ValueError("A metragem produzida deve ser maior que zero.")
    if not item.get("pedido") or not item.get("produto_codigo"): raise ValueError("Pedido e produto são obrigatórios.")
    if tipo not in {"PRODUÇÃO","2°","SUCATA"}: raise ValueError("Tipo de produção inválido.")
    with transaction() as conn:
        bob=_get_bobina(conn,lote)
        if not bob: raise ValueError("Lote de bobina não encontrado.")
        if bob["status"] in ("INATIVA","BLOQUEADA"): raise ValueError("A bobina está bloqueada ou inativa.")
        pe=float(bob["peso_especifico"] or 0)
        if pe<=0: raise ValueError("A bobina não possui peso específico válido.")
        consumo=round(pe*float(metragem),3)
        saldo=float(bob["peso_real"] or 0)-float(conn.execute(
            "SELECT COALESCE(SUM(cons_bob),0) FROM fact_movimentacao WHERE bobina_lote=? AND status<>'CANCELADO'",(lote,)).fetchone()[0])
        if saldo-consumo < -0.01: raise ValueError(f"Saldo insuficiente. Saldo atual: {saldo:.2f} kg; consumo: {consumo:.2f} kg.")
        now=datetime.now()
        cur=conn.execute("""INSERT INTO fact_movimentacao
          (op,data,ano,trimestre,mes,pedido,cliente,produto_codigo,tipo,fator,mt_prod,mt_produzida,
           bobina_lote,bobina_codigo,peso_especifico,cons_bob,status,usuario)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (item.get("op"),now.date().isoformat(),now.year,f"T{((now.month-1)//3)+1}",
           now.strftime("%b").lower(),str(item.get("pedido")),item.get("cliente"),item.get("produto_codigo"),
           tipo,1.0,float(item.get("metragem") or 0),float(metragem),lote,bob["codigo_spec"],pe,consumo,"PENDENTE",usuario))
        rid=cur.lastrowid
        registrar_auditoria(conn,"fact_movimentacao",rid,"CRIAR",usuario,
                            valor_novo=f"pedido={item.get('pedido')}; lote={lote}; mt={metragem}")
    clear_caches(); return rid,consumo

def validar_apontamento(id_,usuario):
    with transaction() as conn:
        row=conn.execute("SELECT status FROM fact_movimentacao WHERE id=?",(id_,)).fetchone()
        if not row: raise ValueError("Lançamento não encontrado.")
        if row["status"]!="PENDENTE": raise ValueError("Somente apontamentos pendentes podem ser validados.")
        conn.execute("UPDATE fact_movimentacao SET status='VALIDADO',validado_por=?,validado_em=datetime('now','localtime'),atualizado_em=datetime('now','localtime') WHERE id=?",(usuario,id_))
        registrar_auditoria(conn,"fact_movimentacao",id_,"VALIDAR",usuario,valor_anterior="PENDENTE",valor_novo="VALIDADO")
    clear_caches()

def devolver_apontamento(id_,motivo,usuario):
    motivo=(motivo or "").strip()
    if not motivo: raise ValueError("Informe o motivo da devolução.")
    with transaction() as conn:
        row=conn.execute("SELECT status FROM fact_movimentacao WHERE id=?",(id_,)).fetchone()
        if not row: raise ValueError("Lançamento não encontrado.")
        if row["status"]!="PENDENTE": raise ValueError("Somente apontamentos pendentes podem ser devolvidos.")
        conn.execute("UPDATE fact_movimentacao SET status='DEVOLVIDO',motivo_devolucao=?,validado_por=?,validado_em=datetime('now','localtime'),atualizado_em=datetime('now','localtime') WHERE id=?",(motivo,usuario,id_))
        registrar_auditoria(conn,"fact_movimentacao",id_,"DEVOLVER",usuario,valor_anterior="PENDENTE",valor_novo="DEVOLVIDO",motivo=motivo)
    clear_caches()

def editar_apontamento(id_,metragem,tipo,usuario):
    if metragem<=0: raise ValueError("A metragem deve ser maior que zero.")
    if tipo not in {"PRODUÇÃO","2°","SUCATA"}: raise ValueError("Tipo inválido.")
    with transaction() as conn:
        row=conn.execute("SELECT * FROM fact_movimentacao WHERE id=?",(id_,)).fetchone()
        if not row: raise ValueError("Lançamento não encontrado.")
        if row["status"]=="CANCELADO": raise ValueError("Lançamentos cancelados não podem ser editados.")
        pe=float(row["peso_especifico"] or 0)
        novo_consumo=round(pe*float(metragem),3)
        outros=float(conn.execute("""SELECT COALESCE(SUM(cons_bob),0) FROM fact_movimentacao
          WHERE bobina_lote=? AND id<>? AND status<>'CANCELADO'""",(row["bobina_lote"],id_)).fetchone()[0])
        saldo=float(conn.execute("SELECT COALESCE(peso_real,0) FROM dim_bobina_fisica WHERE lote=?",(row["bobina_lote"],)).fetchone()[0] or 0)-outros
        if saldo-novo_consumo < -0.01: raise ValueError("A alteração deixaria o saldo da bobina negativo.")
        conn.execute("""UPDATE fact_movimentacao SET mt_produzida=?,tipo=?,cons_bob=?,status='PENDENTE',
          validado_por=NULL,validado_em=NULL,atualizado_em=datetime('now','localtime') WHERE id=?""",
          (float(metragem),tipo,novo_consumo,id_))
        registrar_auditoria(conn,"fact_movimentacao",id_,"EDITAR",usuario,
                            valor_novo=f"metragem={metragem}; tipo={tipo}; consumo={novo_consumo}")
    clear_caches(); return novo_consumo

def cancelar_apontamento(id_,motivo,usuario):
    motivo=(motivo or "").strip() or "Cancelamento administrativo"
    with transaction() as conn:
        row=conn.execute("SELECT status FROM fact_movimentacao WHERE id=?",(id_,)).fetchone()
        if not row: raise ValueError("Lançamento não encontrado.")
        if row["status"]=="CANCELADO": raise ValueError("Já cancelado.")
        conn.execute("UPDATE fact_movimentacao SET status='CANCELADO',motivo_devolucao=?,atualizado_em=datetime('now','localtime') WHERE id=?",(motivo,id_))
        registrar_auditoria(conn,"fact_movimentacao",id_,"CANCELAR",usuario,valor_anterior=row["status"],valor_novo="CANCELADO",motivo=motivo)
    clear_caches()

def registrar_utilizacao(lote,peso,usuario,data_,hora,caminho=None):
    if peso<0: raise ValueError("Peso não pode ser negativo.")
    with transaction() as conn:
        if not _get_bobina(conn,lote): raise ValueError("Lote não encontrado.")
        seq=int(conn.execute("SELECT COALESCE(MAX(utilizacao),0)+1 FROM fact_controle_utilizacao WHERE bobina_lote=?",(lote,)).fetchone()[0])
        cur=conn.execute("""INSERT INTO fact_controle_utilizacao
          (bobina_lote,utilizacao,data,hora,peso_atual,caminho_etiqueta,usuario) VALUES(?,?,?,?,?,?,?)""",
          (lote,seq,data_.isoformat(),hora.strftime("%H:%M:%S"),peso,caminho,usuario))
        registrar_auditoria(conn,"fact_controle_utilizacao",cur.lastrowid,"CRIAR",usuario,
                            valor_novo=f"lote={lote}; peso={peso}; utilização={seq}")
    clear_caches(); return seq

def registrar_inventario(lote,peso,local,data_,obs,usuario):
    if peso<0: raise ValueError("Peso físico não pode ser negativo.")
    with transaction() as conn:
        if not _get_bobina(conn,lote): raise ValueError("Lote não encontrado.")
        cur=conn.execute("""INSERT INTO fact_inventario_fisico
          (lote,peso_fisico,local_contado,data_contagem,usuario,obs) VALUES(?,?,?,?,?,?)""",
          (lote,peso,local or None,data_.isoformat(),usuario,obs or None))
        registrar_auditoria(conn,"fact_inventario_fisico",cur.lastrowid,"CONTAR",usuario,valor_novo=f"lote={lote}; peso={peso}")
    clear_caches(); return cur.lastrowid
