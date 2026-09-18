"""Resolve natural-language locations without confusing home and project paths."""
from __future__ import annotations
import re
import os
import subprocess
from pathlib import Path
from core.context import ConversationContext
from config import PROJECT_ROOT, WORKING_DIRECTORY, search_roots

HOME_DIRECTORY_NAMES = {
    "documents": ("Documents", "Document"),
    "downloads": ("Downloads", "Download"),
    "desktop": ("Desktop",),
    "pictures": ("Pictures",),
    "videos": ("Videos",),
    "music": ("Music",),
}
XDG_DIRECTORY_KEYS = {
    "documents": "DOCUMENTS", "downloads": "DOWNLOAD", "desktop": "DESKTOP",
    "pictures": "PICTURES", "videos": "VIDEOS", "music": "MUSIC",
}


class AmbiguousDirectoryError(ValueError):
    def __init__(self, name: str, matches: list[Path]):
        self.matches = matches
        rendered = "\n".join(f"[{index}] {_display_path(path)}" for index, path in enumerate(matches, 1))
        super().__init__(f"I found multiple folders named {name.title()}:\n{rendered}\nWhich one should I open?")


def _display_path(path: Path) -> str:
    try:
        relative = str(path.relative_to(Path.home()))
        return "~" if relative == "." else "~/" + relative
    except ValueError:
        return str(path)


def resolve_user_directory(name: str) -> Path:
    """Resolve a standard user directory through XDG, then known home names."""
    key = name.lower()
    if key not in XDG_DIRECTORY_KEYS:
        return Path.home()
    xdg_key = XDG_DIRECTORY_KEYS[key]
    try:
        result = subprocess.run(["xdg-user-dir", xdg_key], capture_output=True, text=True,
                                timeout=2, check=False).stdout.strip()
        home_environment = Path(os.environ.get("HOME", str(Path.home()))).expanduser()
        if result and result != xdg_key and home_environment.resolve() == Path.home().resolve():
            configured = Path(result).expanduser()
            if configured.is_dir() and configured.resolve() != Path.home().resolve():
                return configured
    except (OSError, subprocess.SubprocessError):
        pass
    home = Path.home()
    names = HOME_DIRECTORY_NAMES[key]
    return next((home / value for value in names if (home / value).is_dir()), home / names[0])


def _home_aliases() -> dict[str, Path]:
    home = Path.home()
    aliases = {"home": home, "my files": home, "home directory": home, "home folder": home}
    aliases.update({alias: resolve_user_directory(alias) for alias in HOME_DIRECTORY_NAMES})
    return aliases


def _natural_location(text: str) -> str:
    cleaned = text.strip().strip("'\"").rstrip(".").lower()
    cleaned = re.sub(r"^(?:please\s+)?(?:open|go\s+to|show\s+me)\s+", "", cleaned)
    cleaned = re.sub(r"^(?:my|the)\s+", "", cleaned)
    cleaned = re.sub(r"\s+(?:folder|directory)$", "", cleaned)
    return re.sub(r"\s+", " ", cleaned)


def _normalized_name(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())

class PathResolver:
    def search_directories(self, name: str) -> list[Path]:
        needle = _normalized_name(name)
        matches: dict[Path, Path] = {}
        for root in search_roots():
            try:
                if not root.is_dir():
                    continue
                for current, directories, _ in os.walk(root, onerror=lambda _: None):
                    directories[:] = [item for item in directories if not item.startswith(".") and item != "__pycache__"]
                    for directory in directories:
                        candidate = Path(current) / directory
                        normalized = _normalized_name(directory)
                        if normalized == needle or normalized.startswith(needle):
                            matches[candidate.resolve()] = candidate
            except (OSError, PermissionError):
                continue
        return sorted(matches.values(), key=lambda path: (len(path.parts), str(path).lower()))

    def resolve_directory(self, value: str, context: ConversationContext) -> Path:
        natural = _natural_location(value)
        if natural == "project":
            remembered = next((path for path in context.recent_paths if path.is_dir() and path.name.lower() == "project"), None)
            if remembered is not None:
                return remembered
        if natural in {"project", "this project", "my project", "project root", "project directory", "assistant project"}:
            return PROJECT_ROOT
        aliases = _home_aliases()
        if natural in aliases:
            return aliases[natural]
        if natural.startswith("project/"):
            return PROJECT_ROOT / natural.removeprefix("project/")
        candidate = self.resolve(value, context)
        if candidate.exists():
            return candidate
        name = re.sub(r"\s+(?:folder|directory)$", "", natural)
        matches = self.search_directories(name)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise AmbiguousDirectoryError(name, matches)
        raise FileNotFoundError(f"I couldn't find a {name.title()} directory.")

    def resolve(self, value: str, context: ConversationContext, *, base: Path | None = None) -> Path:
        text = value.strip().strip('"\'').rstrip(".")
        lowered = text.lower()
        if lowered in {"it", "there", "that folder", "this folder", "inside it", "inside that"}:
            if context.last_directory is None:
                raise ValueError("I don't yet know which folder that refers to.")
            return context.last_directory
        # Expand home and absolute paths before applying natural-language rules.
        explicit = Path(text).expanduser()
        if explicit.is_absolute():
            return explicit

        aliases = _home_aliases()
        natural = _natural_location(text)
        if natural in aliases:
            return aliases[natural]
        for name, directory in aliases.items():
            if natural.startswith(name + "/"):
                return directory / text[text.lower().find(name) + len(name) + 1:]

        # An explicit, existing relative path beats a same-named recent item.
        # This prevents "move report.txt" from accidentally selecting a copy
        # in a different recently-used folder.
        reference = re.sub(r"^(?:my|the|this|that)\s+", "", lowered)
        reference = re.sub(r"\s+(?:folder|directory|file)$", "", reference)
        if "/" not in text and "\\" not in text:
            for remembered in context.recent_paths:
                if remembered.is_dir() and remembered.name.lower() == reference:
                    return remembered
        explicit = (base or WORKING_DIRECTORY) / explicit
        if explicit.exists():
            return explicit
        # Keep the raw path untouched, but make natural references comparable
        # to paths remembered in the current conversation.
        for remembered in context.recent_paths:
            if remembered.name.lower() == reference:
                return remembered
        if lowered.startswith("inside "):
            return self.resolve(text[7:], context, base=base)
        return explicit

    def extract_location(self, text: str, context: ConversationContext) -> Path | None:
        match = re.search(r"\b(?:in|inside|to|under)\s+(.+?)(?:\s*$|\s+called\s+)", text, re.I)
        return self.resolve(match.group(1), context) if match else None
