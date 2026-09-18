"""Configuration for the local-first file assistant."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    PROJECT_ROOT = Path(__file__).resolve().parent
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parent

APP_DATA_DIR = Path(os.getenv("ASSISTANT_DATA_DIR", "~/.local/share/ai-voice-assistant")).expanduser()
DATABASE_PATH = APP_DATA_DIR / "assistant.db"
WEB_CACHE_PATH = APP_DATA_DIR / "web_cache.db"
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
WEB_SEARCH_PROVIDER = os.getenv("WEB_SEARCH_PROVIDER", "").strip().lower()
MAX_SEARCH_RESULTS = max(1, min(int(os.getenv("MAX_SEARCH_RESULTS", "10")), 20))
SEARCH_TIMEOUT = max(1, min(int(os.getenv("SEARCH_TIMEOUT", "10")), 60))
CACHE_TTL = max(0, int(os.getenv("CACHE_TTL", "3600")))
WEB_ALLOWED_DOMAINS = tuple(d.strip().lower() for d in os.getenv("WEB_ALLOWED_DOMAINS", "").split(",") if d.strip())
WEB_DENIED_DOMAINS = tuple(d.strip().lower() for d in os.getenv("WEB_DENIED_DOMAINS", "").split(",") if d.strip())
WORKING_DIRECTORY = Path(os.getenv("ASSISTANT_WORKING_DIRECTORY", Path.cwd())).expanduser().resolve()
PROTECTED_PATHS = tuple(Path(p) for p in ("/etc", "/boot", "/usr", "/bin", "/sbin", "/root", "/sys", "/proc", "/dev", "/lib", "/lib64"))
DEFAULT_ALLOWED_ROOTS = ("~/Documents", "~/Downloads", "~/Desktop", "~/Pictures", "~/Videos", "~/Music")

def allowed_roots() -> tuple[Path, ...]:
    raw = os.getenv("ASSISTANT_ALLOWED_ROOTS")
    values = raw.split(",") if raw else DEFAULT_ALLOWED_ROOTS
    # Home itself is needed for safe navigation. Protected paths remain blocked.
    return tuple({Path.home().resolve(), *(Path(v.strip()).expanduser().resolve() for v in values if v.strip())})


def search_roots() -> tuple[Path, ...]:
    """Return bounded, useful search locations without traversing all of HOME."""
    home = Path.home()
    standard = [home / name for names in (("Documents", "Document"), ("Downloads", "Download"),
                                          ("Desktop",), ("Pictures",), ("Videos",), ("Music",))
                for name in names if (home / name).is_dir()]
    configured = [Path(value.strip()).expanduser() for value in os.getenv("ASSISTANT_ALLOWED_ROOTS", "").split(",") if value.strip()]
    return tuple(dict.fromkeys(standard + configured + [PROJECT_ROOT]))
