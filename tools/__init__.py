"""Allow-listed tool package exposed to planners; no shell execution."""
from pathlib import Path
from filesystem.manager import FileManager

def create_file(filename: str) -> str:
    return FileManager().create_file(Path.cwd() / "files" / filename)

def delete_file(filename: str) -> str:
    return FileManager().delete(Path.cwd() / "files" / filename)

def rename_file(old_name: str, new_name: str) -> str:
    return FileManager().rename(Path.cwd() / "files" / old_name, new_name)

def run_command(command: str) -> str:
    return "Error: arbitrary shell commands are intentionally disabled."
