"""Permission checks are delegated to pathlib and reported as user-facing errors."""
from pathlib import Path
import os
def can_read(path: Path) -> bool: return os.access(path, os.R_OK)
def can_write(path: Path) -> bool: return os.access(path.parent if path.parent else path, os.W_OK)
