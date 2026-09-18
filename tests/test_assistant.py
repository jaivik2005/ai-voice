import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core.assistant import FileAssistant
from core.context import ConversationContext
from documents.search import search_documents
from filesystem.path_resolver import PathResolver
from config import WORKING_DIRECTORY
from security.validator import SecurityError, validate_path

class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.root = Path(self.temp.name)
        self.assistant = FileAssistant()
        self.assistant.context.last_directory = self.root
    def tearDown(self): self.temp.cleanup()
    def test_contextual_creation_and_delete_confirmation(self):
        self.assertIn("Created folder", self.assistant.handle(f"create a folder {self.root} called Project"))
        self.assertIn("Created folder", self.assistant.handle("create a folder called Reports inside it"))
        self.assertIn("Reports", self.assistant.handle("show me what is inside Project"))
        self.assertIn("Do you want", self.assistant.handle("delete Project"))
        self.assertTrue((self.root / "Project").exists())
        self.assertIn("Deleted", self.assistant.handle("yes"))
    def test_protected_paths_are_rejected(self):
        with self.assertRaises(SecurityError): validate_path(Path("/etc/passwd"))
    def test_file_lifecycle_search_and_cancel(self):
        a = self.assistant
        self.assertIn("Created folder", a.handle(f"create a folder {self.root} called Destination"))
        self.assertIn("Created folder", a.handle(f"create a folder {self.root} called MoveDestination"))
        report = self.root / "report.txt"
        self.assertIn("Created file", a.handle(f"create a file called report.txt in {self.root}"))
        self.assertIn("Found", a.handle(f"find report in {self.root}"))
        self.assertIn("Do you want", a.handle(f"rename {report} to final.txt"))
        self.assertEqual("Cancelled.", a.handle("no"))
        self.assertTrue(report.exists())
        self.assertIn("Do you want", a.handle(f"copy {report} to {self.root / 'Destination'}"))
        self.assertIn("Copied", a.handle("yes"))
        self.assertTrue((self.root / "Destination" / "report.txt").exists())
        self.assertIn("Do you want", a.handle(f"move {report} to {self.root / 'MoveDestination'}"))
        self.assertIn("Moved", a.handle("yes"))
        self.assertFalse((self.root / "report.txt").exists())
        self.assertTrue((self.root / "MoveDestination" / "report.txt").exists())
    def test_document_search_and_natural_folder_reference(self):
        a = self.assistant
        self.assertIn("Created folder", a.handle(f"create a folder {self.root} called Project"))
        self.assertIn("Created folder", a.handle("Inside my Project folder create a folder called Reports"))
        self.assertTrue((self.root / "Project" / "Reports").is_dir())
        doc = self.root / "notes.md"
        doc.write_text("The NLU design resolves intents safely.", encoding="utf-8")
        results = search_documents(self.root, "NLU intents")
        self.assertEqual(doc, results[0][0])
    def test_absolute_parent_is_preserved_exactly(self):
        parent = self.root / "Download"
        parent.mkdir()
        result = self.assistant.handle(f"Create a folder {parent} called VoiceTest")
        self.assertEqual(f"Created folder: {parent / 'VoiceTest'}", result)
        self.assertTrue((parent / "VoiceTest").is_dir())
    def test_relative_paths_use_configured_working_directory(self):
        context = ConversationContext(last_directory=self.root)
        self.assertEqual(WORKING_DIRECTORY / "Download" / "VoiceTest", PathResolver().resolve("Download/VoiceTest", context))
    def test_open_is_fixed_argument_manager_operation(self):
        a = self.assistant
        a.files.open_path = lambda path: f"Opened safely: {path}"
        self.assertIn("Opened safely", a.handle("open ."))

    def test_home_aliases_use_existing_directories(self):
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            (home / "Document").mkdir()
            (home / "Download").mkdir()
            with patch("pathlib.Path.home", return_value=home), patch.dict("os.environ", {"HOME": str(home)}), patch("filesystem.path_resolver.subprocess.run", side_effect=OSError):
                resolver = PathResolver()
                context = ConversationContext()
                self.assertEqual(home / "Document", resolver.resolve("my Documents", context))
                self.assertEqual(home / "Document", resolver.resolve("my Documents folder", context))
                self.assertEqual(home / "Document", resolver.resolve("Documents", context))
                self.assertEqual(home / "Download", resolver.resolve("my Downloads", context))
                self.assertEqual(home, resolver.resolve("home directory", context))
                self.assertEqual(home, resolver.resolve("~", context))

    def test_home_search_finds_semantic_resume_and_pdfs(self):
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            documents = home / "Documents"
            downloads = home / "Downloads"
            documents.mkdir()
            downloads.mkdir()
            (documents / "Resume_2026.pdf").write_text("resume", encoding="utf-8")
            (documents / "AI Project Report.pdf").write_text("report", encoding="utf-8")
            (downloads / "notes.txt").write_text("notes", encoding="utf-8")
            environment = {"ASSISTANT_ALLOWED_ROOTS": f"{documents},{downloads}"}
            with patch("pathlib.Path.home", return_value=home), patch.dict("os.environ", environment, clear=False):
                assistant = FileAssistant()
                resume = assistant.handle("find my resume")
                pdfs = assistant.handle("where is my PDF")
                self.assertIn("Resume_2026.pdf", resume)
                self.assertIn(str(documents / "Resume_2026.pdf"), resume)
                self.assertIn("AI Project Report.pdf", pdfs)
                self.assertNotIn("notes.txt", pdfs)

    def test_open_home_folder_and_invalid_folder_are_safe(self):
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            documents = home / "Documents"
            documents.mkdir()
            environment = {"ASSISTANT_ALLOWED_ROOTS": str(documents)}
            with patch("pathlib.Path.home", return_value=home), patch.dict("os.environ", {**environment, "HOME": str(home)}, clear=False), patch("filesystem.path_resolver.subprocess.run", side_effect=OSError):
                assistant = FileAssistant()
                open_path = assistant.files.open_path
                assistant.files.open_path = lambda path: f"Opening {path}"
                self.assertIn(str(documents), assistant.handle("open my Documents folder"))
                assistant.files.open_path = open_path
                documents.rmdir()
                self.assertIn("I couldn't find", assistant.handle("open my Documents folder"))

    def test_relative_and_absolute_paths_keep_their_meaning(self):
        absolute = self.root / "absolute.txt"
        absolute.touch()
        context = ConversationContext()
        resolver = PathResolver()
        self.assertEqual(absolute, resolver.resolve(str(absolute), context))
        self.assertEqual(Path("~").expanduser(), resolver.resolve("~", context))
        self.assertEqual(WORKING_DIRECTORY / "relative.txt", resolver.resolve("relative.txt", context))

    def test_file_directory_detection_and_allowed_root(self):
        file_path = self.root / "file.txt"
        file_path.touch()
        with self.assertRaises(NotADirectoryError): self.assistant.files.list_directory(file_path)
        with self.assertRaises(SecurityError): validate_path(Path("/tmp"))

    def test_destructive_actions_still_require_confirmation(self):
        target = self.root / "remove.txt"
        target.touch()
        response = self.assistant.handle(f"delete {target}")
        self.assertIn("Do you want", response)
        self.assertTrue(target.exists())
        self.assertEqual("Cancelled.", self.assistant.handle("no"))
        self.assertTrue(target.exists())

    def test_show_home_directory_lists_only_that_directory(self):
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            pictures = home / "Pictures"
            pictures.mkdir()
            (pictures / "photo.jpg").touch()
            (home / "project-secret.txt").touch()
            with patch("pathlib.Path.home", return_value=home), patch.dict("os.environ", {"HOME": str(home)}), patch("filesystem.path_resolver.subprocess.run", side_effect=OSError):
                assistant = FileAssistant()
                result = assistant.handle("show my Pictures")
                self.assertIn("Contents of ~/Pictures", result)
                self.assertIn("photo.jpg", result)
                self.assertNotIn("project-secret.txt", result)

    def test_open_project_folder_uses_project_root(self):
        project = self.root / "assistant-project"
        project.mkdir()
        with patch("filesystem.path_resolver.PROJECT_ROOT", project):
            assistant = FileAssistant()
            assistant.files.open_path = lambda path: f"Opening {path}"
            self.assertEqual(f"Opening {project}", assistant.handle("open my project folder"))

    def test_unknown_folder_search_opens_unique_allowed_match(self):
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            python_folder = home / "Documents" / "python-project"
            python_folder.mkdir(parents=True)
            with patch("pathlib.Path.home", return_value=home), patch.dict("os.environ", {"HOME": str(home)}), patch("filesystem.path_resolver.subprocess.run", side_effect=OSError), patch("filesystem.path_resolver.search_roots", return_value=(home,)):
                assistant = FileAssistant()
                assistant.files.open_path = lambda path: f"Opening {path}"
                self.assertEqual(f"Opening {python_folder}", assistant.handle("open my python folder"))

    def test_unknown_folder_search_reports_ambiguity(self):
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            first = home / "Documents" / "Python"
            second = home / "Downloads" / "python_project"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            with patch("pathlib.Path.home", return_value=home), patch.dict("os.environ", {"HOME": str(home)}), patch("filesystem.path_resolver.subprocess.run", side_effect=OSError), patch("filesystem.path_resolver.search_roots", return_value=(home,)):
                result = FileAssistant().handle("open my python folder")
                self.assertIn("multiple folders", result)
                self.assertIn("Python", result)
                self.assertIn("python_project", result)

    def test_directory_traversal_is_rejected(self):
        with self.assertRaises(SecurityError):
            validate_path(Path.home() / "Documents" / ".." / ".." / "tmp")

if __name__ == "__main__": unittest.main()
