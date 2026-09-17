"""Resolve XDG names, absolute paths, relative paths, and recent references."""
from __future__ import annotations
import re
from pathlib import Path
from core.context import ConversationContext
from config import WORKING_DIRECTORY

ALIASES = {
    "home": Path.home(), "documents": Path.home() / "Documents", "downloads": Path.home() / "Downloads",
    "desktop": Path.home() / "Desktop", "pictures": Path.home() / "Pictures", "videos": Path.home() / "Videos",
    "music": Path.home() / "Music", "projects": Path.home() / "Projects",
}

class PathResolver:
    def resolve(self, value: str, context: ConversationContext, *, base: Path | None = None) -> Path:
        text = value.strip().strip('"\'').rstrip(".")
        lowered = text.lower()
        if lowered in {"it", "there", "that folder", "this folder", "inside it", "inside that"}:
            if context.last_directory is None:
                raise ValueError("I don't yet know which folder that refers to.")
            return context.last_directory
        # An explicit, existing relative path beats a same-named recent item.
        # This prevents "move report.txt" from accidentally selecting a copy
        # in a different recently-used folder.
        explicit = Path(text).expanduser()
        # An absolute path has no base.  Preserve it exactly (aside from
        # harmless lexical normalization performed later by validation).
        if explicit.is_absolute():
            return explicit
        explicit = (base or WORKING_DIRECTORY) / explicit
        if explicit.exists():
            return explicit
        # Keep the raw path untouched, but make natural references comparable
        # to paths remembered in the current conversation.
        reference = re.sub(r"^(?:my|the|this|that)\s+", "", lowered)
        reference = re.sub(r"\s+(?:folder|directory|file)$", "", reference)
        for remembered in context.recent_paths:
            if remembered.name.lower() == reference:
                return remembered
        if lowered.startswith("inside "):
            return self.resolve(text[7:], context, base=base)
        if lowered in ALIASES:
            return ALIASES[lowered]
        # Replace leading natural XDG directory names while retaining child components.
        for name, directory in ALIASES.items():
            if lowered.startswith(name + "/"):
                return directory / text[len(name) + 1:]
        return explicit

    def extract_location(self, text: str, context: ConversationContext) -> Path | None:
        match = re.search(r"\b(?:in|inside|to|under)\s+(.+?)(?:\s*$|\s+called\s+)", text, re.I)
        return self.resolve(match.group(1), context) if match else None
