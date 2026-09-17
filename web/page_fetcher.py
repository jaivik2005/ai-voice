"""Bounded, validated page retrieval for selected search results only."""
from __future__ import annotations
import httpx
from config import SEARCH_TIMEOUT
from security.validator import validate_web_url

class PageFetchError(RuntimeError): pass
def fetch_page(url: str, *, client: httpx.Client | None = None) -> str:
    validate_web_url(url, timeout=SEARCH_TIMEOUT)
    try:
        if client:
            response = client.get(url, timeout=SEARCH_TIMEOUT, follow_redirects=False)
        else:
            with httpx.Client(timeout=SEARCH_TIMEOUT, follow_redirects=False) as session: response = session.get(url)
        if 300 <= response.status_code < 400:
            location = response.headers.get("location")
            if not location: raise PageFetchError("The page redirected without a destination.")
            validate_web_url(location, timeout=SEARCH_TIMEOUT)
            return fetch_page(location, client=client)
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", "").lower(): raise PageFetchError("That URL is not an HTML page.")
        return response.text[:1_000_000]
    except (httpx.HTTPError, ValueError) as exc:
        raise PageFetchError("I couldn't access that page.") from exc
