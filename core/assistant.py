"""The safe coordinator joining NLU, validation, context, and filesystem tools."""
from __future__ import annotations
import re
from pathlib import Path
from core.context import ConversationContext
from core.intent import Action, Operation
from core.planner import Planner
from database.history import record
from documents.extractor import extract_text
from documents.search import search_documents
from filesystem.manager import FileManager
from filesystem.path_resolver import PathResolver
from filesystem.search import search_files
from security.confirmation import PendingConfirmation

class FileAssistant:
    def __init__(self) -> None:
        self.context, self.planner, self.resolver, self.files = ConversationContext(), Planner(), PathResolver(), FileManager()
        self.web = None  # Imported lazily so file-only deployments need no web extras.
    def handle(self, command: str) -> str:
        normalized = command.strip().lower()
        if normalized in {"yes", "confirm", "do it", "proceed"}:
            if not self.context.pending: return "There is no pending operation to confirm."
            pending = self.context.pending; self.context.pending = None
            return self._execute(Operation(Action(pending.operation["action"]), pending.operation["parameters"], True), confirmed=True, command=command)
        if normalized in {"no", "cancel", "never mind"}: self.context.pending = None; return "Cancelled."
        operations = self.planner.plan(command)
        if not operations: return "I couldn't map that to a safe operation. Try ‘create a folder called Project in Documents’ or ‘search Python documentation’."
        return "\n".join(self._execute(operation, command=command) for operation in operations)
    def _path(self, value: str, *, base: Path | None = None) -> Path: return self.resolver.resolve(value, self.context, base=base)
    def _existing(self, value: str) -> Path:
        candidate = self._path(value)
        if candidate.exists(): return candidate
        name = value.strip(" '\"").lower()
        name = re.sub(r"^(?:my|the|this|that)\s+|\s+(?:folder|directory|file)$", "", name)
        for path in self.context.recent_paths:
            if path.name.lower() == name: return path
        raise FileNotFoundError(f"I couldn't find '{value}'. Use a full path or search for it first.")
    def _known_or_resolved(self, value: str) -> Path:
        """Resolve a location, including a named item mentioned earlier."""
        candidate = self._path(value)
        if candidate.exists():
            return candidate
        for path in self.context.recent_paths:
            if path.name.lower() == value.strip(" '\"").lower():
                return path
        return candidate
    def _execute(self, op: Operation, *, confirmed: bool = False, command: str = "") -> str:
        try:
            if op.destructive and not confirmed:
                prompt = f"This will {op.action.value.lower().replace('_', ' ')}. Do you want me to proceed?"
                self.context.pending = PendingConfirmation({"action":op.action.value,"parameters":op.parameters}, prompt); return prompt
            p = op.parameters
            if op.action is Action.WEB_OPEN_RESULT:
                index = p["index"] - 1
                if index < 0 or index >= len(self.context.last_search_results):
                    raise ValueError("I don't have that search result yet. Search the web first.")
                selected = self.context.last_search_results[index]
                try:
                    from web.page_fetcher import fetch_page, PageFetchError
                    from web.content_extractor import extract_content
                    result = extract_content(fetch_page(selected["url"])) or "That page had no readable text."
                except PageFetchError:
                    result = "I couldn't access that page, but the search result is still available: " + selected["title"]
            elif op.action in {Action.WEB_SEARCH, Action.NEWS_SEARCH, Action.DOCUMENTATION_SEARCH, Action.GITHUB_SEARCH, Action.WEBSITE_SEARCH, Action.RESEARCH}:
                mode = {Action.NEWS_SEARCH: "news", Action.DOCUMENTATION_SEARCH: "docs", Action.GITHUB_SEARCH: "github", Action.RESEARCH: "research"}.get(op.action, "web")
                query = p["query"]
                if self.web is None:
                    from web.search_agent import WebSearchAgent
                    self.web = WebSearchAgent()
                answer = self.web.search(query, mode=mode)
                self.context.remember_search(query, [item.model_dump() if hasattr(item, "model_dump") else item.dict() for item in answer.results])
                result = answer.detail
            elif op.action is Action.CREATE_FOLDER:
                target = self._path(p["location"]) / p["name"]; result = self.files.create_folder(target); self.context.remember(target)
            elif op.action is Action.CREATE_FILE:
                target = self._path(p["location"]) / p["name"]; result = self.files.create_file(target); self.context.remember(target)
            elif op.action is Action.LIST_DIRECTORY:
                target = self._known_or_resolved(p["path"]); entries = self.files.list_directory(target); self.context.remember(target); result = f"{target} is empty." if not entries else "\n".join(str(x) for x in entries[:50])
            elif op.action is Action.SEARCH_FILES:
                root = self._path(p["path"]); matches = search_files(root, p["query"], p["extension"], p["min_size"], p["modified_today"]); self.context.recent_paths = matches[:10]; result = "No matching files found." if not matches else "Found:\n" + "\n".join(str(x) for x in matches[:20])
            elif op.action is Action.DELETE:
                target = self._existing(p["path"]); result = self.files.delete(target); self.context.remember(target.parent)
            elif op.action is Action.RENAME:
                source = self._existing(p["source"]); result = self.files.rename(source, p["name"]); self.context.remember(source.with_name(p["name"]))
            elif op.action in {Action.MOVE, Action.COPY}:
                source, destination = self._existing(p["source"]), self._path(p["destination"]); result = self.files.move(source, destination) if op.action is Action.MOVE else self.files.copy(source, destination); self.context.remember(destination / source.name if destination.is_dir() else destination)
            elif op.action is Action.OPEN:
                target = self._path(p["path"]); result = self.files.open_path(target); self.context.remember(target)
            elif op.action is Action.READ_DOCUMENT:
                target = self._existing(p["path"]); result = extract_text(target)[:4000] or "The document contains no extractable text."; self.context.remember(target)
            elif op.action is Action.SEARCH_DOCUMENTS:
                matches = search_documents(self._path(p["path"]), p["query"])
                self.context.recent_paths = [path for path, _ in matches[:10]]
                result = "No documents mention that text." if not matches else "Found:\n" + "\n".join(f"{path}: {snippet}" for path, snippet in matches[:10])
            else: result = "That action is not implemented yet."
            record(command, op.action.value, result); return result
        except (OSError, ValueError, RuntimeError) as exc:
            result = str(exc); record(command, op.action.value, "ERROR: " + result); return result
