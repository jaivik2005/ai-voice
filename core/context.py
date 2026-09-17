"""Short-lived conversation references."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from security.confirmation import PendingConfirmation
from typing import Any

@dataclass
class ConversationContext:
    last_directory: Path | None = None
    last_path: Path | None = None
    pending: PendingConfirmation | None = None
    recent_paths: list[Path] = field(default_factory=list)
    last_search_results: list[dict[str, Any]] = field(default_factory=list)
    last_search_query: str | None = None
    def remember_search(self, query: str, results: list[dict[str, Any]]) -> None:
        """Keep normalized web results for safe, explicit follow-up resolution."""
        self.last_search_query, self.last_search_results = query, results[:20]
    def remember(self, path: Path) -> None:
        self.last_path = path
        self.last_directory = path if path.is_dir() else path.parent
        self.recent_paths = ([path] + [p for p in self.recent_paths if p != path])[:10]
