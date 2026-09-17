"""Explicit confirmation state; destructive operations are never auto-run."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class PendingConfirmation:
    operation: dict[str, Any]
    prompt: str

class ConfirmationRequired(Exception):
    def __init__(self, prompt: str, operation: dict[str, Any]):
        self.prompt, self.operation = prompt, operation
        super().__init__(prompt)
