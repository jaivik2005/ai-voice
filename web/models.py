"""Pydantic schemas shared across the web agent boundary."""
from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl

class SearchOptions(BaseModel):
    max_results: int = Field(default=10, ge=1, le=20)
    recency: str | None = None
    domain: str | None = None
    file_type: str | None = None
    language: str | None = None
    region: str | None = None
    safe_search: bool = True

class SearchResult(BaseModel):
    title: str
    url: str = ""
    snippet: str = ""
    source: str = ""
    published_date: str | None = None
    relevance_score: float = 0.0

class SearchResponse(BaseModel):
    results: list[SearchResult] = Field(default_factory=list)

class Citation(BaseModel):
    source_id: str
    title: str
    url: str
    domain: str
    date: str | None = None

class QueryPlan(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=4)
    options: SearchOptions = Field(default_factory=SearchOptions)
    research_mode: bool = False

class WebAnswer(BaseModel):
    spoken_summary: str
    detail: str
    citations: list[Citation] = Field(default_factory=list)
    results: list[SearchResult] = Field(default_factory=list)
