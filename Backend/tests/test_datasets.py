import io
import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.operations import validate_and_store_dataset


class DatasetImportTests(unittest.TestCase):
    def test_instruction_dataset_is_validated_hashed_and_persisted(self) -> None:
        content = json.dumps({"instruction": "Say hello", "input": "", "output": "Hello"}).encode()
        upload = SimpleNamespace(filename="../../training.jsonl", file=io.BytesIO(content))
        with tempfile.TemporaryDirectory() as temp_directory:
            with patch.dict(os.environ, {
                "LOCAL_FOUNDRY_DB_PATH": os.path.join(temp_directory, "workspace.sqlite3"),
                "LOCAL_FOUNDRY_DATASET_DIR": os.path.join(temp_directory, "datasets"),
            }):
                result = validate_and_store_dataset(upload, "instructional_finetuning")

        self.assertEqual(result["name"], "training.jsonl")
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["status"], "Validated")
        self.assertEqual(len(result["fingerprint"]), 64)

    def test_invalid_jsonl_is_rejected_and_not_stored(self) -> None:
        upload = SimpleNamespace(filename="training.jsonl", file=io.BytesIO(b"not-json\n"))
        with tempfile.TemporaryDirectory() as temp_directory:
            dataset_directory = os.path.join(temp_directory, "datasets")
            with patch.dict(os.environ, {
                "LOCAL_FOUNDRY_DB_PATH": os.path.join(temp_directory, "workspace.sqlite3"),
                "LOCAL_FOUNDRY_DATASET_DIR": dataset_directory,
            }):
                with self.assertRaisesRegex(ValueError, "Invalid JSON on line 1"):
                    validate_and_store_dataset(upload, "instructional_finetuning")
            self.assertEqual(os.listdir(dataset_directory), [])

    def test_workflow_extension_mismatch_is_rejected(self) -> None:
        upload = SimpleNamespace(filename="training.csv", file=io.BytesIO(b"a,b\n1,2\n"))
        with self.assertRaisesRegex(ValueError, "accepts"):
            validate_and_store_dataset(upload, "instructional_finetuning")

    def test_upload_size_limit_is_enforced(self) -> None:
        upload = SimpleNamespace(filename="training.txt", file=io.BytesIO(b"12345"))
        with tempfile.TemporaryDirectory() as temp_directory:
            with patch.dict(os.environ, {
                "LOCAL_FOUNDRY_DB_PATH": os.path.join(temp_directory, "workspace.sqlite3"),
                "LOCAL_FOUNDRY_DATASET_DIR": os.path.join(temp_directory, "datasets"),
            }), patch("services.operations.MAX_DATASET_BYTES", 4):
                with self.assertRaisesRegex(ValueError, "upload limit"):
                    validate_and_store_dataset(upload, "continued_pretraining")

    def test_invalid_text_encoding_is_rejected(self) -> None:
        upload = SimpleNamespace(filename="training.txt", file=io.BytesIO(b"\xff"))
        with tempfile.TemporaryDirectory() as temp_directory:
            with patch.dict(os.environ, {
                "LOCAL_FOUNDRY_DB_PATH": os.path.join(temp_directory, "workspace.sqlite3"),
                "LOCAL_FOUNDRY_DATASET_DIR": os.path.join(temp_directory, "datasets"),
            }):
                with self.assertRaisesRegex(ValueError, "UTF-8"):
                    validate_and_store_dataset(upload, "continued_pretraining")


if __name__ == "__main__":
    unittest.main()