import os
import tempfile
import unittest
from unittest.mock import patch

from services.operations import load_workspace, save_project


class ProjectServiceTests(unittest.TestCase):
    def test_save_project_persists_project_in_workspace(self) -> None:
        project = {
            "name": "Support assistant",
            "description": "Product support responses",
            "workflow": "instructional_finetuning",
            "technique": "LoRA",
            "modelId": "org/model",
            "modelName": "Org Model",
            "dataset": {"id": "dataset-123"},
        }
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = os.path.join(temp_directory, "workspace.sqlite3")
            with patch.dict(os.environ, {"LOCAL_FOUNDRY_DB_PATH": database_path}):
                created = save_project(project)
                workspace = load_workspace()

        self.assertEqual(created["name"], "Support assistant")
        self.assertEqual(created["datasetId"], "dataset-123")
        self.assertEqual(workspace["projects"][0]["id"], created["id"])
        self.assertEqual(workspace["projects"][0]["runCount"], 0)

    def test_quantization_project_does_not_require_dataset(self) -> None:
        project = {
            "name": "Quantized model",
            "workflow": "quantization",
            "technique": "8-bit",
            "modelId": "org/model",
            "modelName": "Org Model",
        }
        with tempfile.TemporaryDirectory() as temp_directory:
            with patch.dict(os.environ, {
                "LOCAL_FOUNDRY_DB_PATH": os.path.join(temp_directory, "workspace.sqlite3")
            }):
                created = save_project(project)

        self.assertIsNone(created["datasetId"])

    def test_training_project_requires_dataset(self) -> None:
        project = {
            "name": "Missing data",
            "workflow": "instructional_finetuning",
            "modelId": "org/model",
            "modelName": "Org Model",
        }
        with self.assertRaisesRegex(ValueError, "dataset is required"):
            save_project(project)


if __name__ == "__main__":
    unittest.main()