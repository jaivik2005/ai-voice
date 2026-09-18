"""Read-only search provider adapter. It never fabricates results."""
from __future__ import annotations
import logging
import os
from typing import Any
import httpx
from config import MAX_SEARCH_RESULTS, SEARCH_API_KEY, SEARCH_TIMEOUT, WEB_SEARCH_PROVIDER
from web.cache import get as cache_get, put as cache_put
from web.models import SearchOptions, SearchResponse
from web.result_parser import parse_results

log = logging.getLogger(__name__)
class SearchUnavailable(RuntimeError): pass
SUPPORTED_PROVIDERS = frozenset({"brave", "tavily"})

class SearchEngine:
    def __init__(self, api_key: str | None = None, provider: str | None = None, client: httpx.Client | None = None):
        self.api_key = os.getenv("SEARCH_API_KEY", SEARCH_API_KEY) if api_key is None else api_key
        configured_provider = os.getenv("WEB_SEARCH_PROVIDER", WEB_SEARCH_PROVIDER) if provider is None else provider
        self.provider = configured_provider.strip().lower()
        self.client = client

    def _validate_configuration(self) -> None:
        if not self.provider:
            raise SearchUnavailable("Web search provider is missing. Set WEB_SEARCH_PROVIDER to tavily or brave.")
        if self.provider not in SUPPORTED_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
            raise SearchUnavailable(f"Unsupported web search provider '{self.provider}'. Use {supported}.")
        if not self.api_key:
            raise SearchUnavailable("Web search API key is missing. Set SEARCH_API_KEY in the project .env file.")

    def search(self, query: str, options: SearchOptions | None = None) -> SearchResponse:
        options = options or SearchOptions(max_results=MAX_SEARCH_RESULTS)
        options.max_results = min(options.max_results, MAX_SEARCH_RESULTS)
        cache_value = cache_get("search", f"{self.provider}|{query}|{options.model_dump_json() if hasattr(options, 'model_dump_json') else options.json()}")
        if cache_value is not None: return SearchResponse(**cache_value)
        self._validate_configuration()
        try:
            if self.provider == "tavily":
                payload: dict[str, Any] = {"api_key": self.api_key, "query": query, "max_results": options.max_results, "search_depth": "advanced"}
                if options.domain: payload["include_domains"] = [options.domain]
                if self.client:
                    response = self.client.post("https://api.tavily.com/search", json=payload, timeout=SEARCH_TIMEOUT)
                else:
                    with httpx.Client(follow_redirects=False, timeout=SEARCH_TIMEOUT) as client:
                        response = client.post("https://api.tavily.com/search", json=payload)
            else:
                params: dict[str, Any] = {"q": query, "count": options.max_results, "safesearch": "strict" if options.safe_search else "off"}
                if options.domain: params["site"] = options.domain
                if options.language: params["search_lang"] = options.language
                if options.region: params["country"] = options.region
                if options.recency: params["freshness"] = options.recency
                headers = {"Accept": "application/json", "X-Subscription-Token": self.api_key}
                if self.client:
                    response = self.client.get("https://api.search.brave.com/res/v1/web/search", params=params, headers=headers, timeout=SEARCH_TIMEOUT)
                else:
                    with httpx.Client(follow_redirects=False, timeout=SEARCH_TIMEOUT) as client:
                        response = client.get("https://api.search.brave.com/res/v1/web/search", params=params, headers=headers)
            response.raise_for_status(); data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("web search failed: %s", type(exc).__name__)
            raise SearchUnavailable("I couldn't reach the search service right now.") from exc
        answer = SearchResponse(results=parse_results(data, self.provider)[:options.max_results])
        cache_put("search", f"{self.provider}|{query}|{options.model_dump_json() if hasattr(options, 'model_dump_json') else options.json()}", answer.model_dump() if hasattr(answer, 'model_dump') else answer.dict())
        return answer
