"""Extract text from common office and plain-text documents."""
from __future__ import annotations
from pathlib import Path

def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".rst", ".csv"}: return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        except ImportError: raise RuntimeError("Install pypdf to read PDF files.")
    if suffix == ".docx":
        try:
            from docx import Document
            return "\n".join(p.text for p in Document(str(path)).paragraphs)
        except ImportError: raise RuntimeError("Install python-docx to read DOCX files.")
    raise ValueError(f"Unsupported document type: {suffix or 'no extension'}")
