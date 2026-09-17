"""Central allow-list for cross-agent tools."""
from __future__ import annotations
from collections.abc import Callable
from typing import Any
from core.intent import Action
from security.validator import validate_web_url

class ToolRegistry:
    """Only web read tools are exposed to web operations; no file mutations."""
    def __init__(self) -> None: self._tools: dict[str, Callable[..., Any]] = {}
    def register(self, name: str, tool: Callable[..., Any]) -> None: self._tools[name] = tool
    def enabled_for(self, action: Action) -> dict[str, Callable[..., Any]]:
        if action in {Action.WEB_SEARCH, Action.NEWS_SEARCH, Action.DOCUMENTATION_SEARCH, Action.GITHUB_SEARCH, Action.WEBSITE_SEARCH, Action.RESEARCH}:
            return {name: tool for name, tool in self._tools.items() if name.startswith("web.")}
        return {}
    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in self._tools or not name.startswith("web."): raise PermissionError("Tool is not enabled for this agent.")
        if name == "web.fetch_page": validate_web_url(str(kwargs.get("url", "")))
        return self._tools[name](**kwargs)
