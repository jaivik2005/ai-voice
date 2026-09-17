"""Path validation.  No filesystem operation should bypass this module."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from config import PROTECTED_PATHS, allowed_roots
from config import SEARCH_TIMEOUT, WEB_ALLOWED_DOMAINS, WEB_DENIED_DOMAINS

class SecurityError(ValueError):
    pass

def validate_path(path: Path, *, must_exist: bool = False) -> Path:
    candidate = path.expanduser().resolve(strict=False)
    if any(candidate == protected or protected in candidate.parents for protected in PROTECTED_PATHS):
        raise SecurityError(f"Access to protected system location '{candidate}' is not allowed.")
    roots = allowed_roots()
    if not any(candidate == root or root in candidate.parents for root in roots):
        raise SecurityError(f"'{candidate}' is outside the assistant's allowed locations.")
    if must_exist and not candidate.exists():
        raise FileNotFoundError(f"I couldn't find '{candidate}'.")
    return candidate

def validate_destination(source: Path, destination: Path, *, overwrite: bool = False) -> Path:
    target = validate_path(destination)
    if target.exists() and not overwrite:
        raise FileExistsError(f"'{target}' already exists; confirmation is required to overwrite it.")
    if source.is_dir() and (target == source or source in target.parents):
        raise SecurityError("A folder cannot be moved or copied into itself.")
    return target

def validate_web_url(url: str, *, timeout: int | None = None) -> str:
    """Validate outbound web targets; only HTTPS public domains are allowed."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise SecurityError("Web requests must use a well-formed HTTPS URL.")
    host = (parsed.hostname or "").lower().rstrip(".")
    if host in {"localhost", "0.0.0.0", "::1"} or host.startswith("127.") or host.startswith("10.") or host.startswith("192.168."):
        raise SecurityError("Requests to local or private network hosts are not allowed.")
    if any(host == domain or host.endswith("." + domain) for domain in WEB_DENIED_DOMAINS):
        raise SecurityError(f"The domain '{host}' is blocked.")
    if WEB_ALLOWED_DOMAINS and not any(host == domain or host.endswith("." + domain) for domain in WEB_ALLOWED_DOMAINS):
        raise SecurityError(f"The domain '{host}' is not on the allowed list.")
    if timeout is not None and (timeout < 1 or timeout > SEARCH_TIMEOUT):
        raise SecurityError("Web request timeout is outside the allowed limit.")
    return url
