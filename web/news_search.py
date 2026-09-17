from web.models import SearchOptions, SearchResponse
from web.search_engine import SearchEngine
def search_news(query: str, engine: SearchEngine | None = None) -> SearchResponse:
    return (engine or SearchEngine()).search(query, SearchOptions(recency="pw"))
