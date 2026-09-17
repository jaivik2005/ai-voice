"""Safe file-management helper functions used by the assistant.

All operations are sandboxed to the repository-local `files/` folder and
validate paths to prevent path-traversal attacks. Functions return
informative strings or raise ValueError on invalid input.
"""
from pathlib import Path
from typing import Union

SAFE_DIR = Path.cwd() / "files"
SAFE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_path(name: str) -> Path:
    if not name or any(c in name for c in ("..", "~", ":", "\\")):
        raise ValueError("Invalid filename")
    p = (SAFE_DIR / name).resolve()
    if SAFE_DIR.resolve() not in p.parents and p != SAFE_DIR.resolve():
        raise ValueError("Filename escapes safe directory")
    return p


def create_file(filename: str) -> str:
    """Create an empty file under `files/`.

    Returns a human readable message.
    """
    path = _safe_path(filename)
    if path.exists():
        return f"Error: {filename} already exists."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    return f"{filename} created."


def delete_file(filename: str) -> str:
    """Delete a file under `files/`.

    Returns a human readable message.
    """
    path = _safe_path(filename)
    if not path.exists():
        return f"Error: {filename} does not exist."
    if path.is_dir():
        return f"Error: {filename} is a directory."
    path.unlink()
    return f"{filename} deleted."


def rename_file(old_name: str, new_name: str) -> str:
    """Rename a file under `files/`.

    Returns a human readable message.
    """
    old_path = _safe_path(old_name)
    new_path = _safe_path(new_name)
    if not old_path.exists():
        return f"Error: {old_name} does not exist."
    if new_path.exists():
        return f"Error: {new_name} already exists."
    new_path.parent.mkdir(parents=True, exist_ok=True)
    old_path.replace(new_path)
    return f"{old_name} renamed to {new_name}."


def run_command(command: str) -> str:
    """Legacy API intentionally disabled; the assistant never executes shells."""
    return "Error: arbitrary shell commands are intentionally disabled."
