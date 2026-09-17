"""Filesystem operations implemented only with pathlib/shutil (never shell)."""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from security.validator import validate_destination, validate_path

class FileManager:
    def create_folder(self, path: Path) -> str:
        path = validate_path(path)
        path.mkdir(parents=True, exist_ok=False)
        return f"Created folder: {path}"
    def create_file(self, path: Path, content: str = "") -> str:
        path = validate_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists(): raise FileExistsError(f"'{path}' already exists.")
        path.write_text(content, encoding="utf-8")
        return f"Created file: {path}"
    def delete(self, path: Path) -> str:
        path = validate_path(path, must_exist=True)
        if path.is_dir(): shutil.rmtree(path)
        else: path.unlink()
        return f"Deleted: {path}"
    def rename(self, source: Path, new_name: str, *, overwrite: bool = False) -> str:
        source = validate_path(source, must_exist=True)
        if Path(new_name).name != new_name: raise ValueError("A new name cannot contain a path.")
        target = validate_destination(source, source.with_name(new_name), overwrite=overwrite)
        source.replace(target)
        return f"Renamed to: {target}"
    def move(self, source: Path, destination: Path, *, overwrite: bool = False) -> str:
        source = validate_path(source, must_exist=True)
        target = destination / source.name if destination.is_dir() else destination
        target = validate_destination(source, target, overwrite=overwrite)
        shutil.move(str(source), str(target)); return f"Moved to: {target}"
    def copy(self, source: Path, destination: Path, *, overwrite: bool = False) -> str:
        source = validate_path(source, must_exist=True)
        target = destination / source.name if destination.is_dir() else destination
        target = validate_destination(source, target, overwrite=overwrite)
        if source.is_dir(): shutil.copytree(source, target, dirs_exist_ok=overwrite)
        else: shutil.copy2(source, target)
        return f"Copied to: {target}"
    def list_directory(self, path: Path) -> list[Path]:
        path = validate_path(path, must_exist=True)
        if not path.is_dir(): raise NotADirectoryError(f"'{path}' is not a directory.")
        return sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    def open_path(self, path: Path) -> str:
        path = validate_path(path, must_exist=True)
        subprocess.Popen(["xdg-open", str(path)], start_new_session=True)
        return f"Opened: {path}"
