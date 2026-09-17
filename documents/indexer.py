"""Small metadata index hook; lexical search is usable without pre-indexing."""
from pathlib import Path
from documents.search import search_documents
def index_directory(root: Path): return search_documents(root, "")
