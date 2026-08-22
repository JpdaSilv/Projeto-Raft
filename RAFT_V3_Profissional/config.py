"""Configuração central do RAFT V3."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("RAFT_DB_PATH", str(ROOT / "banco" / "raft_app.db")))
APP_NAME = os.getenv("RAFT_APP_NAME", "RAFT • Controle Industrial")
SESSION_DAYS = int(os.getenv("RAFT_SESSION_DAYS", "3"))

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
