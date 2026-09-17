"""Structured operations permitted by the assistant."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Action(str, Enum):
    CREATE_FOLDER="CREATE_FOLDER"; CREATE_FILE="CREATE_FILE"; LIST_DIRECTORY="LIST_DIRECTORY"
    SEARCH_FILES="SEARCH_FILES"; DELETE="DELETE"; RENAME="RENAME"; MOVE="MOVE"; COPY="COPY"
    OPEN="OPEN"; READ_DOCUMENT="READ_DOCUMENT"; SEARCH_DOCUMENTS="SEARCH_DOCUMENTS"
    WEB_SEARCH="WEB_SEARCH"; NEWS_SEARCH="NEWS_SEARCH"; DOCUMENTATION_SEARCH="DOCUMENTATION_SEARCH"
    GITHUB_SEARCH="GITHUB_SEARCH"; WEBSITE_SEARCH="WEBSITE_SEARCH"; RESEARCH="RESEARCH"
    WEB_OPEN_RESULT="WEB_OPEN_RESULT"

@dataclass
class Operation:
    action: Action
    parameters: dict[str, Any] = field(default_factory=dict)
    destructive: bool = False
