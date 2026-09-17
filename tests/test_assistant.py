import tempfile
import unittest
from pathlib import Path
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

if __name__ == "__main__": unittest.main()
