import os
import tempfile
import unittest
from unittest.mock import patch

from services.operations import queue_evaluation, read_evaluation
from services.storage import connect


def seed_completed_run_and_test_dataset() -> None:
    with connect() as connection:
        connection.execute(
            "INSERT INTO projects "
            "(id, name, workflow, model_id, model_name, status, created_at, updated_at) "
            "VALUES ('project-1', 'Test project', 'instructional_finetuning', 'model-1', "
            "'Model One', 'draft', 'now', 'now')"
        )
        connection.execute(
            "INSERT INTO datasets "
            "(id, project_id, name, workflow, format, size_bytes, row_count, fingerprint, "
            "storage_path, role, status, created_at) "
            "VALUES ('train-data', 'project-1', 'train.jsonl', 'instructional_finetuning', "
            "'JSONL', 10, 1, 'train-hash', '/tmp/train', 'training', 'validated', 'now')"
        )
        connection.execute(
            "INSERT INTO datasets "
            "(id, project_id, name, workflow, format, size_bytes, row_count, fingerprint, "
            "storage_path, role, status, created_at) "
            "VALUES ('eval-data', 'project-1', 'eval.jsonl', 'instructional_finetuning', "
            "'JSONL', 10, 1, 'eval-hash', '/tmp/eval', 'evaluation', 'validated', 'now')"
        )
        connection.execute(
            "INSERT INTO runs "
            "(id, project_id, name, model_id, model_name, method, dataset_id, status, created_at, updated_at) "
            "VALUES ('run-1', 'project-1', 'Run One', 'model-1', 'Model One', 'LoRA', "
            "'train-data', 'passed', 'now', 'now')"
        )


class EvaluationTests(unittest.TestCase):
    def test_records_worker_unavailable_without_fabricating_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            with patch.dict(os.environ, {
                "LOCAL_FOUNDRY_DB_PATH": os.path.join(temp_directory, "workspace.sqlite3")
            }):
                seed_completed_run_and_test_dataset()
                result = queue_evaluation("run-1", "eval-data")
                stored = read_evaluation(result["id"])

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["metrics"], [])
        self.assertIn("worker is not configured", result["message"])
        self.assertEqual(stored["datasetName"], "eval.jsonl")

    def test_rejects_training_data_as_evaluation_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            with patch.dict(os.environ, {
                "LOCAL_FOUNDRY_DB_PATH": os.path.join(temp_directory, "workspace.sqlite3")
            }):
                seed_completed_run_and_test_dataset()
                with self.assertRaisesRegex(ValueError, "held-out"):
                    queue_evaluation("run-1", "train-data")


if __name__ == "__main__":
    unittest.main()