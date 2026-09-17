"""Extract bounded readable text; fetched pages remain untrusted data."""
from __future__ import annotations
from bs4 import BeautifulSoup
def extract_content(html: str, *, limit: int = 12_000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]): node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())[:limit]
