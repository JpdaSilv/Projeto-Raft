"""Configuração central do RAFT V4."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("RAFT_DB_PATH", str(ROOT / "banco" / "raft_app.db")))
APP_NAME = os.getenv("RAFT_APP_NAME", "RAFT • Controle Industrial")
APP_VERSION = os.getenv("RAFT_APP_VERSION", "4.0.0")
SESSION_DAYS = max(1, int(os.getenv("RAFT_SESSION_DAYS", "3")))
DB_TIMEOUT = max(5, int(os.getenv("RAFT_DB_TIMEOUT", "30")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
