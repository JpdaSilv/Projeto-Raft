"""Teste de concorrência seguro: usa linhas de teste e remove tudo ao final."""
import argparse, sqlite3, threading, time, uuid
from pathlib import Path

def worker(db, wid, n, result, lock):
    conn=sqlite3.connect(db,timeout=30)
    conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA busy_timeout=15000")
    ok=0; fail=0; times=[]
    for i in range(n):
        t=time.perf_counter()
        try:
            conn.execute("""INSERT INTO fact_movimentacao
              (data,pedido,cliente,produto_codigo,tipo,mt_produzida,status,usuario)
              VALUES(date('now'),'__TESTE__','__TESTE__','__TESTE__','PRODUÇÃO',0,'CANCELADO',?)""",
              (f"__TESTE__{wid}_{i}",))
            conn.commit(); ok+=1
        except Exception: fail+=1
        times.append(time.perf_counter()-t)
    conn.close()
    with lock: result.append((ok,fail,sum(times)/len(times)*1000))

p=argparse.ArgumentParser(); p.add_argument("--db",required=True); p.add_argument("--operadores",type=int,default=15); p.add_argument("--lancamentos",type=int,default=10)
a=p.parse_args()
if not Path(a.db).exists(): raise SystemExit("Banco não encontrado.")
res=[]; lock=threading.Lock(); ts=[]
for w in range(a.operadores):
    t=threading.Thread(target=worker,args=(a.db,w,a.lancamentos,res,lock)); ts.append(t); t.start()
for t in ts:t.join()
conn=sqlite3.connect(a.db); conn.execute("DELETE FROM fact_movimentacao WHERE pedido='__TESTE__'"); conn.commit(); conn.close()
ok=sum(x[0] for x in res); fail=sum(x[1] for x in res)
print(f"Sucesso: {ok} | Falhas: {fail} | Média por thread: {sum(x[2] for x in res)/len(res):.2f} ms")
