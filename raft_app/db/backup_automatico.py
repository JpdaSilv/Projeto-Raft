"""
backup_automatico.py — copia o banco com timestamp e apaga backups antigos.

Uso (rodar local, via Agendador de Tarefas do Windows ou cron no Linux/Mac):
    python db/backup_automatico.py --db "banco/raft_app.db" --destino "backups/" --manter 30
"""
import argparse
import shutil
from pathlib import Path
from datetime import datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--destino", required=True)
    parser.add_argument("--manter", type=int, default=30, help="Quantos backups recentes manter")
    args = parser.parse_args()

    db_path = Path(args.db)
    destino = Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        print(f"ERRO: banco não encontrado em {db_path}")
        return

    nome = f"raft_app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    destino_arquivo = destino / nome
    shutil.copy2(db_path, destino_arquivo)
    print(f"Backup criado: {destino_arquivo}")

    backups = sorted(destino.glob("raft_app_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for antigo in backups[args.manter:]:
        antigo.unlink()
        print(f"Backup antigo removido: {antigo.name}")

    print(f"Total de backups mantidos: {min(len(backups), args.manter)}")


if __name__ == "__main__":
    main()
