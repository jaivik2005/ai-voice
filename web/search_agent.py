"""Orchestrates read-only, citation-backed web research."""
from __future__ import annotations
from web.models import WebAnswer
from web.query_planner import plan_query
from web.search_engine import SearchEngine
from web.source_ranker import rank_and_deduplicate
from web.summarizer import summarize

class WebSearchAgent:
    def __init__(self, engine: SearchEngine | None = None): self.engine = engine or SearchEngine()
    def search(self, query: str, *, mode: str = "web") -> WebAnswer:
        plan = plan_query(query, mode=mode)
        all_results = []
        for planned_query in plan.queries: all_results.extend(self.engine.search(planned_query, plan.options).results)
        prefer_official = mode in {"docs", "website"} or "official" in query.lower()
        ranked = rank_and_deduplicate(all_results, prefer_official=prefer_official)
        return summarize(query, ranked[:plan.options.max_results])
