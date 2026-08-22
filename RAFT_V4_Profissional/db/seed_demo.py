"""Recria uma base de demonstração rica para avaliação visual/funcional."""
import sqlite3, random
from datetime import date
from config import DB_PATH
from auth import hash_senha
random.seed(42)
conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; conn.execute('PRAGMA foreign_keys=ON')

# Se a base estiver vazia, cria um conjunto mínimo autossuficiente para demonstração.
if conn.execute("SELECT COUNT(*) FROM dim_bobina_fisica").fetchone()[0] == 0:
    specs=[("1.168M","Bobina 1.168M","1.168M",3.62),("1.282B","Bobina 1.282B","1.282B",4.05),
           ("1.287M","Bobina 1.287M","1.287M",4.20),("1.299","Bobina 1.299","1.299",4.35)]
    for code,desc,short,pe in specs:
        conn.execute("INSERT OR IGNORE INTO dim_bobina_spec(codigo,descricao,desc_curta,peso_especifico) VALUES(?,?,?,?)",(code,desc,short,pe))
    for code,desc,tipo in [("TP40","Telha TP40","TELHA"),("TP25","Telha TP25","TELHA"),("TP100","Telha TP100","TELHA"),("TP17","Telha TP17","TELHA")]:
        conn.execute("INSERT OR IGNORE INTO dim_produto(codigo,descricao,tipo_telha,fator_bobina) VALUES(?,?,?,?)",(code,desc,tipo,1.0))
    for i in range(12):
        lote=f"DEMO-{i+1:04d}"; spec=specs[i%len(specs)][0]
        conn.execute("INSERT INTO dim_bobina_fisica(lote,codigo_spec,galpao,local_fisico,n_ref,peso_real,status) VALUES(?,?,?,?,?,?,'ESTOQUE')",(lote,spec,f"G{1+i%2}",f"R{i//4+1}-P{i%4+1}",f"REF-{i+1:04d}",6500+i*120))
    for i in range(24):
        produto=["TP40","TP25","TP100","TP17"][i%4]
        conn.execute("INSERT INTO dim_pedido(pedido,op,cliente,produto_codigo,metragem,tipo_prod,data) VALUES(?,?,?,?,?,?,date('now',?))",(f"DEM{i+1:04d}",f"OP-{i+1:04d}",f"Cliente Demo {i%6+1}",produto,20+(i%8)*5,"PRODUÇÃO",f"-{i%45} day"))
    conn.commit()

# Usuários de demonstração (somente se ainda não existirem).
for username,nome,perfil in [
    ('joao','João Demo','ADMINISTRADOR'),
    ('pcp1','PCP Demo','PCP'),
    ('almox1','Almoxarifado Demo','ALMOXARIFADO'),
    ('operador1','Operador Demo','OPERADOR'),
]:
    conn.execute("INSERT OR IGNORE INTO usuarios(username,senha_hash,nome,perfil) VALUES(?,?,?,?)",
                 (username,hash_senha('raft12345'),nome,perfil))
for t in ['audit_log','fact_controle_utilizacao','fact_inventario_fisico','fact_movimentacao','snapshot_totvs','importacoes_totvs']:
    try: conn.execute(f'DELETE FROM {t}')
    except sqlite3.OperationalError: pass
ped=conn.execute("SELECT id,pedido,op,cliente,produto_codigo,metragem,tipo_prod,data FROM dim_pedido WHERE date(data)>=date('now','-60 day') AND produto_codigo IS NOT NULL AND produto_codigo<>'-' ORDER BY date(data),id").fetchall()
bobs=conn.execute("SELECT f.lote,f.codigo_spec,f.peso_real,s.peso_especifico FROM dim_bobina_fisica f LEFT JOIN dim_bobina_spec s ON s.codigo=f.codigo_spec WHERE f.status='ESTOQUE' AND f.peso_real>0 ORDER BY f.lote").fetchall()
preferred=['LM28070102','0000000025']; bobs=sorted(bobs,key=lambda r:(0 if r['lote'] in preferred else 1,r['lote']))
for i,r in enumerate(ped[-36:]):
    d=date.fromisoformat(r['data']); bob=bobs[i % min(len(bobs),12)]; 
    try: pe=float(bob['peso_especifico'])
    except (TypeError,ValueError): pe=3.8
    try: mt=float(r['metragem'])
    except (TypeError,ValueError): mt=10.0
    if mt <= 0: mt=10.0
    tipo='PRODUÇÃO'
    if i in (5,14,25): tipo='2°'
    if i in (8,20): tipo='SUCATA'
    status='VALIDADO' if i not in (31,32,33,34) else ('PENDENTE' if i<34 else 'DEVOLVIDO')
    cons=round(pe*mt,3); created=f"{d.isoformat()} {8+(i%9):02d}:{(i*7)%60:02d}:00"
    conn.execute("""INSERT INTO fact_movimentacao (op,data,ano,trimestre,mes,pedido,cliente,produto_codigo,tipo,fator,mt_prod,mt_produzida,tamanho,bobina_lote,bobina_codigo,peso_especifico,cons_bob,status,validado_por,validado_em,motivo_devolucao,criado_em,usuario) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(r['op'],r['data'],d.year,f"T{((d.month-1)//3)+1}",d.strftime('%b').lower(),r['pedido'],r['cliente'],r['produto_codigo'],tipo,1.0,mt,mt,None,bob['lote'],bob['codigo_spec'],pe,cons,status,'PCP Teste' if status=='VALIDADO' else None,created if status=='VALIDADO' else None,'Conferir metragem' if status=='DEVOLVIDO' else None,created,'João Pedro'))
for lote in preferred:
    if conn.execute('SELECT 1 FROM dim_bobina_fisica WHERE lote=?',(lote,)).fetchone():
        base=float(conn.execute('SELECT peso_real FROM dim_bobina_fisica WHERE lote=?',(lote,)).fetchone()[0] or 0)
        for seq in range(1,4): conn.execute("INSERT INTO fact_controle_utilizacao (bobina_lote,utilizacao,data,hora,peso_atual,usuario) VALUES(?,?,?,?,?,?)",(lote,seq,date.today().isoformat(),f"{9+seq:02d}:1{seq}:00",max(0,base-seq*420),'Operador Teste'))
for i,b in enumerate(bobs[:18]):
    peso=float(b['peso_real'] or 0); peso-=135 if i==3 else 0; peso+=210 if i==9 else 0
    local=conn.execute('SELECT local_fisico FROM dim_bobina_fisica WHERE lote=?',(b['lote'],)).fetchone()[0]
    conn.execute("INSERT INTO fact_inventario_fisico (lote,peso_fisico,local_contado,data_contagem,usuario,obs) VALUES(?,?,?,?,?,?)",(b['lote'],peso,local,date.today().isoformat(),'Almoxarifado Teste','Contagem de demonstração'))
imp='DEMO-2026-08-22'; conn.execute("INSERT OR REPLACE INTO importacoes_totvs (id,arquivo_nome,linhas,novos,divergentes,aplicados,status,usuario) VALUES(?,?,?,?,?,?,?,?)",(imp,'TOTVS_DEMO_20260822.xlsx',12,2,2,12,'APLICADA','Almoxarifado Teste'))
for b in bobs[:12]:
    local=conn.execute('SELECT local_fisico FROM dim_bobina_fisica WHERE lote=?',(b['lote'],)).fetchone()[0]
    conn.execute("INSERT INTO snapshot_totvs (importacao_id,lote,codigo_spec,peso_totvs,local_fisico,arquivo_nome,usuario) VALUES(?,?,?,?,?,?,?)",(imp,b['lote'],b['codigo_spec'],b['peso_real'],local,'TOTVS_DEMO_20260822.xlsx','Almoxarifado Teste'))
for table,rid,acao,user in [('fact_movimentacao',1,'CRIAR','João Pedro'),('fact_movimentacao',1,'VALIDAR','PCP Teste'),('fact_movimentacao',32,'CRIAR','João Pedro'),('fact_movimentacao',35,'DEVOLVER','PCP Teste'),('fact_inventario_fisico',1,'CONTAR','Almoxarifado Teste'),('importacoes_totvs',0,'IMPORTAR','Almoxarifado Teste')]:
    conn.execute("INSERT INTO audit_log (tabela,registro_id,acao,usuario,motivo) VALUES(?,?,?,?,?)",(table,rid,acao,user,'Demonstração V3'))
conn.commit(); conn.close(); print('Demo criada')
