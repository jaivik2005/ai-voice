"""Minimal structured operation audit history."""
from __future__ import annotations
import json, sqlite3
from config import APP_DATA_DIR, DATABASE_PATH

def record(command: str, action: str, result: str) -> bool:
    """Persist an audit event without allowing logging failures to break work."""
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute("CREATE TABLE IF NOT EXISTS history (created_at TEXT DEFAULT CURRENT_TIMESTAMP, command TEXT, action TEXT, result TEXT)")
            db.execute("INSERT INTO history(command, action, result) VALUES (?, ?, ?)", (command, action, result))
        return True
    except (OSError, sqlite3.Error):
        return False
