import json
import unittest
from unittest.mock import patch

from services.operations import search_model_catalog


class FakeResponse:
    def __init__(self, payload: list[dict], link: str | None = None) -> None:
        self.payload = json.dumps(payload).encode("utf-8")
        self.headers = {"Link": link} if link else {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self.payload


class ModelCatalogTests(unittest.TestCase):
    @patch("services.operations.urllib.request.urlopen")
    def test_search_formats_model_and_encodes_next_link(self, urlopen) -> None:
        urlopen.return_value = FakeResponse(
            [{
                "id": "org/example-model",
                "pipeline_tag": "text-generation",
                "safetensors": {"parameters": {"BF16": 1_500_000_000}},
                "cardData": {"license": "apache-2.0"},
                "downloads": 12,
            }],
            '<https://huggingface.co/api/models?cursor=page-two>; rel="next"',
        )

        result = search_model_catalog("example", None)

        self.assertEqual(result["source"], "huggingface")
        self.assertEqual(result["items"][0]["id"], "org/example-model")
        self.assertEqual(result["items"][0]["parameters"], "1.5B")
        self.assertEqual(result["items"][0]["license"], "apache-2.0")
        self.assertIsNotNone(result["nextCursor"])
        request = urlopen.call_args.args[0]
        self.assertIn("limit=20", request.full_url)

    def test_search_rejects_out_of_range_page_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            search_model_catalog("", None, 101)

    def test_rejects_cursor_for_untrusted_host(self) -> None:
        malicious_target = b"https://example.com/api/models"
        cursor = __import__("base64").urlsafe_b64encode(malicious_target).decode().rstrip("=")

        with self.assertRaisesRegex(ValueError, "Invalid model catalog cursor"):
            search_model_catalog("", cursor)


if __name__ == "__main__":
    unittest.main()