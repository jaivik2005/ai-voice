"""Convert provider payloads to the stable, small result schema."""
from __future__ import annotations
from urllib.parse import urlparse
from web.models import SearchResult

def parse_results(payload: dict, provider: str) -> list[SearchResult]:
    if provider == "brave":
        raw_results = payload.get("web", {}).get("results", [])
    else:
        raw_results = payload.get("results", [])
    normalized: list[SearchResult] = []
    for item in raw_results:
        url, title = str(item.get("url", "")).strip(), str(item.get("title", "")).strip()
        if not title: continue
        if url and not url.startswith("https://"): continue
        normalized.append(SearchResult(title=title, url=url, snippet=str(item.get("description", item.get("snippet", item.get("content", "")))), source=urlparse(url).netloc, published_date=item.get("age") or item.get("published_date"), relevance_score=float(item.get("score", 0))))
    return normalized
