from web.models import SearchOptions, SearchResponse
from web.search_engine import SearchEngine
def search_docs(query: str, engine: SearchEngine | None = None) -> SearchResponse:
    return (engine or SearchEngine()).search(query + " documentation", SearchOptions())
