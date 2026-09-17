"""Explicit allow-listed filesystem tool facade for future LLM tool calling."""
from filesystem.manager import FileManager
from filesystem.search import search_files
__all__ = ["FileManager", "search_files"]
