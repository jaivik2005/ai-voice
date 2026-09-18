"""Deterministic intent extractor for common file-management phrases."""
from __future__ import annotations
import re
from core.intent import Action, Operation

COMMON_TYPOS = {
    "webste": "website",
    "doucmentation": "documentation",
    "serach": "search",
    "offical": "official",
    "latestt": "latest",
}

def _quoted_or_tail(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.I)
    return m.group(1).strip(" '\".") if m else None

def _normalize_common_typos(text: str) -> str:
    return re.sub(r"\b[\w]+\b", lambda match: COMMON_TYPOS.get(match.group(0).lower(), match.group(0)), text)

def _has_local_intent(text: str) -> bool:
    return bool(re.search(r"\b(?:my\s+(?:file|files|document|documents|resume|project\s+report)|where\s+is|open\s+my|folder|pdf)\b", text, re.I))

def _has_web_intent(text: str) -> bool:
    return bool(re.search(r"\b(?:search|look\s+up|website|official|documentation|docs|latest|news|headlines|online|google|github|url|web)\b", text, re.I))

def has_web_intent(text: str) -> bool:
    """Return whether a command has strong web intent after typo normalization."""
    normalized = _normalize_common_typos(text.strip())
    return _has_web_intent(normalized) and not _has_local_intent(normalized)

class RuleBasedNLU:
    def parse(self, text: str) -> list[Operation]:
        t = _normalize_common_typos(text.strip()); low = t.lower()
        if re.fullmatch(r"(?:yes|confirm|do it|proceed)", low): return []
        if re.fullmatch(r"(?:no|cancel|never mind)", low): return []
        result_ref = re.fullmatch(r"(?:open|read)\s+(?:the\s+)?(first|second|third|\d+)(?:\s+(?:search\s+)?result)?", low)
        if result_ref:
            raw = result_ref.group(1); index = {"first": 1, "second": 2, "third": 3}.get(raw, int(raw) if raw.isdigit() else 1)
            return [Operation(Action.WEB_OPEN_RESULT, {"index": index})]
        local_intent = _has_local_intent(t)
        web_intent = _has_web_intent(t) and not local_intent
        # Web patterns come before file "find/search" patterns. A domain or
        # web-specific qualifier makes the intended agent unambiguous.
        if web_intent and re.match(r"(?:find|search)\s+(?:the\s+)?official\s+(?:website|site)\s+(?:of|for)\s+", low):
            query = re.sub(r"^(?:find|search)\s+(?:the\s+)?official\s+(?:website|site)\s+(?:of|for)\s+", "", t, flags=re.I).strip(" .")
            return [Operation(Action.WEBSITE_SEARCH, {"query": query})]
        if web_intent and "github" in low and re.search(r"\b(?:find|search|look up|show)\b", low):
            query = re.sub(r"\b(?:on\s+)?github\b", "", t, flags=re.I)
            query = re.sub(r"^(?:find|search|look up|show)\s+", "", query, flags=re.I).strip(" .")
            return [Operation(Action.GITHUB_SEARCH, {"query": query})]
        if web_intent and re.search(r"\b(?:news|headlines|latest|today|current|recently|this week|this month|newest|updated|now)\b", low) and re.search(r"\b(?:find|search|what|who|when|where|news|latest|current|recent|updated)\b", low):
            query = re.sub(r"^(?:find|search|what(?:'s| is)?|show me|tell me)\s+", "", t, flags=re.I).strip(" .")
            return [Operation(Action.NEWS_SEARCH, {"query": query, "fresh": True})]
        if web_intent and re.search(r"\b(?:documentation|docs|api reference)\b", low):
            query = re.sub(r"\b(?:documentation|docs|api reference)\b", "", t, flags=re.I)
            query = re.sub(r"^(?:find|search|look up)\s+", "", query, flags=re.I).strip(" .")
            return [Operation(Action.DOCUMENTATION_SEARCH, {"query": query})]
        if web_intent and re.match(r"(?:research|compare|investigate)\b", low):
            return [Operation(Action.RESEARCH, {"query": re.sub(r"^(?:research|compare|investigate)\s+", "", t, flags=re.I).strip(" .")})]
        if web_intent and re.match(r"(?:web\s+)?(?:search|look up)\s+", low):
            query = re.sub(r"^(?:web\s+)?(?:search|look up)\s+", "", t, flags=re.I)
            query = re.sub(r"^(?:the\s+)?web\s+(?:for\s+)?", "", query, flags=re.I)
            return [Operation(Action.WEB_SEARCH, {"query": query.strip(" .")})]
        if low.startswith(("show", "list", "what is inside")):
            location = _quoted_or_tail(t, r"(?:inside|in)\s+(.+)$")
            if not location:
                location = re.sub(r"^(?:show|list)(?:\s+me)?\s+", "", t, flags=re.I).strip(" .") or "."
            return [Operation(Action.LIST_DIRECTORY, {"path": location})]
        if low.startswith(("where is", "where are")):
            location = re.sub(r"^(?:where is|where are)\s+(?:my\s+)?", "", t, flags=re.I).strip(" .")
            ext = ".pdf" if re.search(r"\bpdfs?\b", low) else None
            return [Operation(Action.SEARCH_FILES, {"path": ".", "query": "" if ext else location, "extension": ext, "min_size": None, "modified_today": False})]
        if low.startswith(("find", "search")):
            if "document where" in low or "document containing" in low:
                query = re.split(r"(?:where|containing)", t, flags=re.I, maxsplit=1)[-1].strip(" .")
                return [Operation(Action.SEARCH_DOCUMENTS, {"path": _quoted_or_tail(t, r"\bin\s+(.+)$") or ".", "query": query})]
            location = _quoted_or_tail(t, r"\bin\s+(.+)$") or "."
            ext = ".pdf" if re.search(r"\bpdfs?\b", low) else None
            size = re.search(r"larger than\s+(\d+)\s*(kb|mb|gb)", low)
            query = re.sub(r"^(find|search)(?:\s+all)?\s*", "", t, flags=re.I)
            query = re.sub(r"\s+in\s+.+$", "", query, flags=re.I)
            query = re.sub(r"^(?:my\s+)?", "", query, flags=re.I)
            if ext or size or "modified today" in low: query = ""
            min_size = int(size.group(1)) * {"kb":1024,"mb":1024**2,"gb":1024**3}[size.group(2).lower()] if size else None
            return [Operation(Action.SEARCH_FILES, {"path": location, "query": query, "extension": ext, "min_size": min_size, "modified_today": "modified today" in low})]
        # Also accept: "Inside Project create a folder called Reports."
        inside_first = re.match(r"inside\s+(.+?)\s+create\s+(?:a\s+)?(?:folder|directory)(?:\s+(?:called|named)\s+(.+))?$", t, re.I)
        if inside_first:
            location, name = inside_first.group(1), (inside_first.group(2) or "").strip(" '\".")
            return [Operation(Action.CREATE_FOLDER, {"name": name, "location": location})] if name else []
        if low.startswith("create") and "folder" in low:
            # "Create a folder /absolute/parent called Name" has an explicit
            # parent even though it is not introduced by "in" or "inside".
            absolute_parent = re.search(
                r"\bfolder\s+(?P<location>/\S+)\s+(?:called|named)\s+(?P<name>.+)$",
                t,
                re.I,
            )
            if absolute_parent:
                return [Operation(Action.CREATE_FOLDER, {
                    "name": absolute_parent.group("name").strip(" '\"."),
                    "location": absolute_parent.group("location"),
                })]
            name = _quoted_or_tail(t, r"(?:called|named)\s+(.+?)(?:\s+(?:in|inside)\s+.+)?$")
            if not name:
                m = re.search(r"create\s+(?:a\s+)?(.+?)\s+(?:folder|directory)", t, re.I); name = m.group(1).strip() if m else None
            location = _quoted_or_tail(t, r"(?:in|inside)\s+(.+)$") or "."
            return [Operation(Action.CREATE_FOLDER, {"name": name, "location": location})] if name else []
        if low.startswith("create") and "file" in low:
            name = _quoted_or_tail(t, r"(?:called|named)\s+(.+?)(?:\s+in\s+.+)?$")
            return [Operation(Action.CREATE_FILE, {"name": name, "location": _quoted_or_tail(t, r"\bin\s+(.+)$") or "."})] if name else []
        if low.startswith(("delete", "remove")):
            return [Operation(Action.DELETE, {"path": re.sub(r"^(delete|remove)\s+(?:the\s+)?", "", t, flags=re.I)}, True)]
        if low.startswith("rename"):
            m = re.search(r"rename\s+(.+?)\s+to\s+(.+)$", t, re.I)
            return [Operation(Action.RENAME, {"source": m.group(1).strip(), "name": m.group(2).strip()}, True)] if m else []
        if low.startswith(("move", "copy")):
            m = re.search(r"(move|copy)\s+(.+?)\s+to\s+(.+)$", t, re.I)
            if m: return [Operation(Action.MOVE if m.group(1).lower()=="move" else Action.COPY, {"source":m.group(2).strip(), "destination":m.group(3).strip()}, True)]
        if low.startswith(("open", "go to")):
            return [Operation(Action.OPEN, {"path": re.sub(r"^(open|go to)\s+", "", t, flags=re.I)})]
        if low.startswith("read"):
            return [Operation(Action.READ_DOCUMENT, {"path": re.sub(r"^read\s+(?:my\s+)?", "", t, flags=re.I)})]
        return []
