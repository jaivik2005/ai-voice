"""Content search for supported documents (a lexical baseline for embeddings)."""
from __future__ import annotations
from pathlib import Path
import os
from documents.extractor import extract_text
from security.validator import validate_path

SUPPORTED = {".txt", ".md", ".pdf", ".docx"}

def search_documents(root: Path, query: str) -> list[tuple[Path, str]]:
    root = validate_path(root, must_exist=True)
    terms = [part.lower() for part in query.split() if part]
    found: list[tuple[int, Path, str]] = []
    for current, dirs, names in os.walk(root, onerror=lambda _: None):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for name in names:
            path = Path(current) / name
            if path.suffix.lower() not in SUPPORTED: continue
            try:
                text = extract_text(path); lowered = text.lower(); score = sum(lowered.count(term) for term in terms)
                if score:
                    point = min((lowered.find(term) for term in terms if lowered.find(term) >= 0), default=0)
                    snippet = text[max(0, point - 100): point + 300].replace("\n", " ").strip()
                    found.append((score, path, snippet))
            except (OSError, ValueError, RuntimeError): continue
    return [(path, snippet) for _, path, snippet in sorted(found, reverse=True, key=lambda item: item[0])]
