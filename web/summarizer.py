"""Conservative result summarization using only provider supplied fields."""
from __future__ import annotations
from web.citation_manager import citations_for
from web.models import SearchResult, WebAnswer

def summarize(query: str, results: list[SearchResult]) -> WebAnswer:
    citations = citations_for(results)
    if not results: return WebAnswer(spoken_summary="I couldn't find any results for that search.", detail="No results were returned.")
    official = "official website" in query.lower() or "official site" in query.lower()
    lines = [f"I found the official result for: {query}" if official else f"Search results for: {query}"]
    for citation, result in zip(citations, results):
        lines.extend([
            f"[{citation.source_id}] {result.title}",
            f"URL: {result.url or 'Unavailable'}",
            f"Description: {result.snippet or 'No description available.'}",
        ])
        if citation.domain:
            lines.append(f"Domain: {citation.domain}")
    summary_prefix = "I found the official result" if official else f"I found {len(results)} sources"
    return WebAnswer(spoken_summary=f"{summary_prefix}. The top result is {results[0].title}.", detail="\n".join(lines), citations=citations, results=results)
