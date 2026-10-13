import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.storage import connect


class StorageTests(unittest.TestCase):
    def test_connect_creates_workspace_tables_at_configured_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "workspace.sqlite3"
            with patch.dict(os.environ, {"LOCAL_FOUNDRY_DB_PATH": str(database_path)}):
                with connect() as connection:
                    table_names = {
                        row["name"]
                        for row in connection.execute(
                            "SELECT name FROM sqlite_master WHERE type = 'table'"
                        )
                    }

                self.assertTrue(database_path.is_file())
                self.assertTrue({"projects", "datasets", "runs", "evaluations"}.issubset(table_names))

    def test_connection_rolls_back_failed_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "workspace.sqlite3"
            with patch.dict(os.environ, {"LOCAL_FOUNDRY_DB_PATH": str(database_path)}):
                with self.assertRaises(sqlite3.IntegrityError):
                    with connect() as connection:
                        connection.execute(
                            "INSERT INTO projects (id, name, workflow, model_id, model_name, created_at, updated_at) "
                            "VALUES ('same', 'First', 'sft', 'model', 'model', 'now', 'now')"
                        )
                        connection.execute(
                            "INSERT INTO projects (id, name, workflow, model_id, model_name, created_at, updated_at) "
                            "VALUES ('same', 'Duplicate', 'sft', 'model', 'model', 'now', 'now')"
                        )

                with connect() as connection:
                    count = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
                self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()