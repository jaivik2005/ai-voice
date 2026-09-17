"""SQLite storage for expiring web-search data."""
from __future__ import annotations
import json
import sqlite3
import time
from typing import Any
from config import APP_DATA_DIR, WEB_CACHE_PATH

def get(key: str) -> Any | None:
    try:
        with sqlite3.connect(WEB_CACHE_PATH) as db:
            db.execute("CREATE TABLE IF NOT EXISTS web_cache (cache_key TEXT PRIMARY KEY, expires_at REAL NOT NULL, value TEXT NOT NULL)")
            row = db.execute("SELECT value FROM web_cache WHERE cache_key=? AND expires_at>?", (key, time.time())).fetchone()
        return json.loads(row[0]) if row else None
    except (OSError, sqlite3.Error, json.JSONDecodeError):
        return None

def put(key: str, value: Any, ttl: int) -> None:
    if ttl <= 0: return
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(WEB_CACHE_PATH) as db:
            db.execute("CREATE TABLE IF NOT EXISTS web_cache (cache_key TEXT PRIMARY KEY, expires_at REAL NOT NULL, value TEXT NOT NULL)")
            db.execute("INSERT OR REPLACE INTO web_cache VALUES (?, ?, ?)", (key, time.time() + ttl, json.dumps(value)))
    except (OSError, sqlite3.Error, TypeError):
        pass
