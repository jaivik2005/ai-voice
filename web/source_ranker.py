"""Rank and deduplicate results, favoring primary and authoritative sources."""
from __future__ import annotations
from urllib.parse import urlparse, urlunparse
from web.models import SearchResult

def _authority(url: str, *, prefer_official: bool = False) -> float:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host.endswith((".gov", ".edu")): score = 4.0
    elif host in {"github.com", "docs.python.org"} or host.startswith("docs."): score = 3.5
    else: score = 1.0
    if prefer_official and ("official" in host or host.startswith("docs.") or "/docs" in parsed.path.lower() or "documentation" in parsed.path.lower()):
        score += 3.0
    return score
def _canonical(url: str) -> str:
    p = urlparse(url); return urlunparse((p.scheme, p.netloc.lower(), p.path.rstrip("/"), "", "", ""))
def rank_and_deduplicate(results: list[SearchResult], *, prefer_official: bool = False) -> list[SearchResult]:
    seen: set[str] = set(); output: list[SearchResult] = []
    for result in results:
        canonical = _canonical(result.url)
        if canonical and canonical in seen: continue
        if canonical: seen.add(canonical)
        result.relevance_score += _authority(result.url, prefer_official=prefer_official); output.append(result)
    return sorted(output, key=lambda item: item.relevance_score, reverse=True)
