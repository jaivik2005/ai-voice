"""Conservative result summarization using only provider supplied fields."""
from __future__ import annotations
from web.citation_manager import citations_for
from web.models import SearchResult, WebAnswer
def summarize(query: str, results: list[SearchResult]) -> WebAnswer:
    citations = citations_for(results)
    if not results: return WebAnswer(spoken_summary="I couldn't find any results for that search.", detail="No results were returned.")
    lines = [f"Search results for: {query}"]
    for citation, result in zip(citations, results): lines.append(f"[{citation.source_id}] {result.title} — {result.snippet}".strip())
    return WebAnswer(spoken_summary=f"I found {len(results)} sources. The top result is {results[0].title}.", detail="\n".join(lines), citations=citations, results=results)
