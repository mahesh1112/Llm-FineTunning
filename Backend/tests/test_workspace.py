import os
import tempfile
import unittest
from unittest.mock import patch

from services.operations import load_workspace


class WorkspaceTests(unittest.TestCase):
    def test_empty_workspace_returns_expected_collections_and_machine(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = os.path.join(temp_directory, "workspace.sqlite3")
            with patch.dict(os.environ, {"LOCAL_FOUNDRY_DB_PATH": database_path}):
                workspace = load_workspace()

        self.assertEqual(workspace["projects"], [])
        self.assertEqual(workspace["runs"], [])
        self.assertEqual(workspace["datasets"], [])
        self.assertEqual(workspace["models"], [])
        self.assertIn("gpuStatus", workspace["machine"])


if __name__ == "__main__":
    unittest.main()