"""Validated, structured web tools. No raw HTML is returned by search."""
from __future__ import annotations
from typing import Any
from security.validator import validate_web_url
from web.docs_search import search_docs as _search_docs
from web.github_search import search_github as _search_github
from web.models import SearchOptions
from web.news_search import search_news as _search_news
from web.page_fetcher import fetch_page
from web.search_engine import SearchEngine

def _payload(response) -> dict[str, Any]:
    return response.model_dump() if hasattr(response, "model_dump") else response.dict()
def search_web(query: str, options: dict[str, Any] | None = None) -> dict[str, Any]: return _payload(SearchEngine().search(query, SearchOptions(**(options or {}))))
def search_news(query: str) -> dict[str, Any]: return _payload(_search_news(query))
def search_docs(query: str) -> dict[str, Any]: return _payload(_search_docs(query))
def search_github(query: str) -> dict[str, Any]: return _payload(_search_github(query))
def fetch_page_tool(url: str) -> dict[str, str]:
    validate_web_url(url); return {"content": fetch_page(url)}

def register_web_tools(registry) -> None:
    registry.register("web.search_web", search_web)
    registry.register("web.search_news", search_news)
    registry.register("web.search_docs", search_docs)
    registry.register("web.search_github", search_github)
    registry.register("web.fetch_page", fetch_page_tool)
