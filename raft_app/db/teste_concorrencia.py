"""
teste_concorrencia.py — simula vários operadores lançando apontamentos ao
mesmo tempo, pra provar (ou derrubar) se o SQLite com WAL aguenta uso real
na fábrica. Sem esse teste, "vai funcionar com todo mundo usando ao mesmo
tempo" é uma suposição, não um fato.

Uso:
    python db/teste_concorrencia.py --db "banco/raft_app.db" --operadores 10 --lancamentos 5
"""
import argparse
import sqlite3
import threading
import time
from pathlib import Path
from datetime import date


def inserir_apontamento(db_path: str, worker_id: int, n_lancamentos: int, resultados: list, lock: threading.Lock):
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 8000;")

    sucesso, falha = 0, 0
    tempos = []
    for i in range(n_lancamentos):
        inicio = time.perf_counter()
        try:
            conn.execute(
                """INSERT INTO fact_movimentacao
                   (op, data, pedido, cliente, produto_codigo, tipo, mt_produzida, status, usuario)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (f"TESTE-{worker_id}-{i}", date.today().isoformat(), "TESTE", "Cliente Teste",
                 "TESTE001", "PRODUÇÃO", 100.0, "PENDENTE", f"worker_{worker_id}"),
            )
            conn.commit()
            sucesso += 1
        except sqlite3.Error as e:
            falha += 1
            print(f"[worker {worker_id}] FALHA: {e}")
        tempos.append(time.perf_counter() - inicio)

    conn.close()
    with lock:
        resultados.append({"worker": worker_id, "sucesso": sucesso, "falha": falha,
                            "tempo_medio_ms": sum(tempos) / len(tempos) * 1000 if tempos else 0})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--operadores", type=int, default=10, help="Quantos operadores simultâneos simular")
    parser.add_argument("--lancamentos", type=int, default=5, help="Quantos lançamentos cada operador faz")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"ERRO: banco não encontrado em {args.db}")
        return

    print(f"Simulando {args.operadores} operadores lançando {args.lancamentos} apontamentos cada, ao mesmo tempo...")
    resultados = []
    lock = threading.Lock()
    threads = []

    inicio_total = time.perf_counter()
    for w in range(args.operadores):
        t = threading.Thread(target=inserir_apontamento, args=(args.db, w, args.lancamentos, resultados, lock))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    tempo_total = time.perf_counter() - inicio_total

    total_sucesso = sum(r["sucesso"] for r in resultados)
    total_falha = sum(r["falha"] for r in resultados)
    tempo_medio = sum(r["tempo_medio_ms"] for r in resultados) / len(resultados)

    print()
    print("=" * 60)
    print(f"RESULTADO: {total_sucesso} inserções OK, {total_falha} falharam")
    print(f"Tempo total: {tempo_total:.2f}s | Tempo médio por insert: {tempo_medio:.1f}ms")
    if total_falha == 0:
        print("✅ SQLite com WAL aguentou a carga simulada sem erro de lock.")
    else:
        print("⚠️ Houve falhas por concorrência — considere migrar pra Postgres se isso "
              "acontecer com o número real de operadores da fábrica.")
    print("=" * 60)

    # limpa os dados de teste
    conn = sqlite3.connect(args.db)
    conn.execute("DELETE FROM fact_movimentacao WHERE op LIKE 'TESTE-%'")
    conn.commit()
    conn.close()
    print("Dados de teste removidos do banco.")


if __name__ == "__main__":
    main()
