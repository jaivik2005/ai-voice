"""Rank and deduplicate results, favoring primary and authoritative sources."""
from __future__ import annotations
from urllib.parse import urlparse, urlunparse
from web.models import SearchResult

def _authority(url: str) -> float:
    host = urlparse(url).hostname or ""
    if host.endswith((".gov", ".edu")): return 4.0
    if host in {"github.com", "docs.python.org"} or host.startswith("docs."): return 3.5
    if host.startswith("www."): host = host[4:]
    return 1.0
def _canonical(url: str) -> str:
    p = urlparse(url); return urlunparse((p.scheme, p.netloc.lower(), p.path.rstrip("/"), "", "", ""))
def rank_and_deduplicate(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set(); output: list[SearchResult] = []
    for result in results:
        canonical = _canonical(result.url)
        if canonical in seen: continue
        seen.add(canonical); result.relevance_score += _authority(result.url); output.append(result)
    return sorted(output, key=lambda item: item.relevance_score, reverse=True)
