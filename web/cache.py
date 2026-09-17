"""Caching policy: fresh-information requests never use cached values."""
from __future__ import annotations
import hashlib
from database import web_cache
from config import CACHE_TTL

FRESH_TERMS = ("latest", "today", "current", "now", "recently", "this week", "this month", "newest", "updated")
def should_bypass(query: str) -> bool: return any(term in query.lower() for term in FRESH_TERMS)
def key(prefix: str, value: str) -> str: return prefix + ":" + hashlib.sha256(value.encode()).hexdigest()
def get(prefix: str, value: str): return None if should_bypass(value) else web_cache.get(key(prefix, value))
def put(prefix: str, value: str, data) -> None:
    if not should_bypass(value): web_cache.put(key(prefix, value), data, CACHE_TTL)
