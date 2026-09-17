"""Metadata-aware filesystem search with bounded traversal."""
from __future__ import annotations
from datetime import datetime, timedelta
import os
from pathlib import Path
from security.validator import validate_path

def search_files(root: Path, query: str = "", extension: str | None = None, min_size: int | None = None, modified_today: bool = False) -> list[Path]:
    root = validate_path(root, must_exist=True)
    needle = query.lower().replace(" ", "")
    cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    matches: list[Path] = []
    for current, dirs, names in os.walk(root, onerror=lambda _: None):
        # Avoid traversing virtual environments, repositories, caches, and
        # hidden application state unless the user explicitly searches there.
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for name in names:
            path = Path(current) / name
            try:
                stat = path.stat()
                if needle and needle not in path.name.lower().replace(" ", ""): continue
                if extension and path.suffix.lower() != "." + extension.lower().lstrip("."): continue
                if min_size is not None and stat.st_size < min_size: continue
                if modified_today and stat.st_mtime < cutoff: continue
                matches.append(path)
            except (OSError, PermissionError): continue
    return sorted(matches, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
