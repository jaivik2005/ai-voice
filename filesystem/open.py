from filesystem.manager import FileManager
def open_file(path): return FileManager().open_path(path)
def open_directory(path): return FileManager().open_path(path)
