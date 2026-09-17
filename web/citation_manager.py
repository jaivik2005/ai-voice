"""Traceable source identifiers for every surfaced result."""
from __future__ import annotations
from urllib.parse import urlparse
from web.models import Citation, SearchResult
def citations_for(results: list[SearchResult]) -> list[Citation]:
    return [Citation(source_id=f"S{i}", title=result.title, url=result.url, domain=urlparse(result.url).netloc, date=result.published_date) for i, result in enumerate(results, 1)]
