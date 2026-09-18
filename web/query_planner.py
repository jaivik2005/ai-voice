"""Strict, deterministic query planning; no raw LLM tool output is executed."""
from __future__ import annotations
from web.models import QueryPlan, SearchOptions

def plan_query(question: str, *, mode: str = "web") -> QueryPlan:
    """Return validated search queries and provider filters from user text."""
    query = question.strip()
    options = SearchOptions()
    if mode == "news": options.recency = "pw"
    if mode == "docs":
        options.domain = None
        query = f"{query} official documentation"
    if mode == "github": options.domain = "github.com"
    research = mode == "research"
    queries = [query]
    if research:
        queries += [f"{query} official source", f"{query} independent analysis"]
    return QueryPlan(queries=queries, options=options, research_mode=research)
