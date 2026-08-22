"""Regras de negócio do RAFT. Mantém SQL crítico fora das telas."""
from datetime import date, datetime
from uuid import uuid4
from db_utils import transaction, registrar_auditoria, clear_caches

def criar_apontamento(item, lote, tipo, metragem, usuario):
    if metragem <= 0:
        raise ValueError("A metragem produzida deve ser maior que zero.")
    if not lote or not item.get("produto_codigo"):
        raise ValueError("Pedido/produto e lote são obrigatórios.")
    with transaction() as conn:
        bob = conn.execute("""
            SELECT f.lote,f.codigo_spec,s.peso_especifico,f.status
            FROM dim_bobina_fisica f LEFT JOIN dim_bobina_spec s ON s.codigo=f.codigo_spec
            WHERE f.lote=?
        """,(lote,)).fetchone()
        if not bob:
            raise ValueError("Lote de bobina não encontrado.")
        if bob["status"] in ("INATIVA","BLOQUEADA"):
            raise ValueError("A bobina está bloqueada/inativa.")
        pe = float(bob["peso_especifico"] or 0)
        if pe <= 0:
            raise ValueError("Bobina sem peso específico válido.")
        consumo = round(pe * metragem, 3)
        now = datetime.now()
        cur = conn.execute("""
            INSERT INTO fact_movimentacao
            (op,data,ano,trimestre,mes,pedido,cliente,produto_codigo,tipo,
             mt_prod,mt_produzida,bobina_lote,bobina_codigo,peso_especifico,cons_bob,status,usuario)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            item.get("op"), now.date().isoformat(), now.year, f"T{((now.month-1)//3)+1}",
            now.strftime("%b").lower(), item.get("pedido"), item.get("cliente"),
            item.get("produto_codigo"), tipo, item.get("metragem"), metragem,
            lote, bob["codigo_spec"], pe, consumo, "PENDENTE", usuario
        ))
        registro = cur.lastrowid
        registrar_auditoria(conn,"fact_movimentacao",registro,"CRIAR",usuario,
                            valor_novo=f"pedido={item.get('pedido')}; lote={lote}; mt={metragem}")
    clear_caches()
    return registro, consumo

def validar_apontamento(id_, usuario):
    with transaction() as conn:
        row=conn.execute("SELECT status FROM fact_movimentacao WHERE id=?",(id_,)).fetchone()
        if not row: raise ValueError("Lançamento não encontrado.")
        if row["status"]!="PENDENTE": raise ValueError("Somente apontamentos pendentes podem ser validados.")
        conn.execute("""
            UPDATE fact_movimentacao
            SET status='VALIDADO', validado_por=?, validado_em=datetime('now','localtime'),
                atualizado_em=datetime('now','localtime')
            WHERE id=?
        """,(usuario,id_))
        registrar_auditoria(conn,"fact_movimentacao",id_,"VALIDAR",usuario,
                            valor_anterior="PENDENTE",valor_novo="VALIDADO")
    clear_caches()

def devolver_apontamento(id_, motivo, usuario):
    if not motivo.strip(): raise ValueError("Informe o motivo da devolução.")
    with transaction() as conn:
        row=conn.execute("SELECT status FROM fact_movimentacao WHERE id=?",(id_,)).fetchone()
        if not row: raise ValueError("Lançamento não encontrado.")
        if row["status"]!="PENDENTE": raise ValueError("Somente apontamentos pendentes podem ser devolvidos.")
        conn.execute("""
            UPDATE fact_movimentacao
            SET status='DEVOLVIDO', motivo_devolucao=?, validado_por=?,
                validado_em=datetime('now','localtime'), atualizado_em=datetime('now','localtime')
            WHERE id=?
        """,(motivo.strip(),usuario,id_))
        registrar_auditoria(conn,"fact_movimentacao",id_,"DEVOLVER",usuario,
                            valor_anterior="PENDENTE",valor_novo="DEVOLVIDO",motivo=motivo)
    clear_caches()

def cancelar_apontamento(id_, motivo, usuario):
    with transaction() as conn:
        row=conn.execute("SELECT status FROM fact_movimentacao WHERE id=?",(id_,)).fetchone()
        if not row: raise ValueError("Lançamento não encontrado.")
        if row["status"]=="CANCELADO": raise ValueError("Já cancelado.")
        conn.execute("""
            UPDATE fact_movimentacao SET status='CANCELADO', motivo_devolucao=?,
            atualizado_em=datetime('now','localtime') WHERE id=?
        """,(motivo.strip() or "Cancelamento administrativo",id_))
        registrar_auditoria(conn,"fact_movimentacao",id_,"CANCELAR",usuario,
                            valor_anterior=row["status"],valor_novo="CANCELADO",motivo=motivo)
    clear_caches()

def registrar_utilizacao(lote, peso, usuario, data_, hora, caminho=None):
    if peso < 0: raise ValueError("Peso não pode ser negativo.")
    with transaction() as conn:
        exists=conn.execute("SELECT 1 FROM dim_bobina_fisica WHERE lote=?",(lote,)).fetchone()
        if not exists: raise ValueError("Lote não encontrado.")
        seq=conn.execute("SELECT COALESCE(MAX(utilizacao),0)+1 FROM fact_controle_utilizacao WHERE bobina_lote=?",(lote,)).fetchone()[0]
        cur=conn.execute("""
            INSERT INTO fact_controle_utilizacao
            (bobina_lote,utilizacao,data,hora,peso_atual,caminho_etiqueta,usuario)
            VALUES(?,?,?,?,?,?,?)
        """,(lote,seq,data_.isoformat(),hora.strftime("%H:%M:%S"),peso,caminho,usuario))
        registrar_auditoria(conn,"fact_controle_utilizacao",cur.lastrowid,"CRIAR",usuario,
                            valor_novo=f"lote={lote}; peso={peso}; utilização={seq}")
    clear_caches()
    return seq

def registrar_inventario(lote,peso,local,data_,obs,usuario):
    if peso < 0: raise ValueError("Peso físico não pode ser negativo.")
    with transaction() as conn:
        cur=conn.execute("""
            INSERT INTO fact_inventario_fisico
            (lote,peso_fisico,local_contado,data_contagem,usuario,obs)
            VALUES(?,?,?,?,?,?)
        """,(lote,peso,local or None,data_.isoformat(),usuario,obs or None))
        registrar_auditoria(conn,"fact_inventario_fisico",cur.lastrowid,"CONTAR",usuario,
                            valor_novo=f"lote={lote}; peso={peso}")
    clear_caches()
    return cur.lastrowid
