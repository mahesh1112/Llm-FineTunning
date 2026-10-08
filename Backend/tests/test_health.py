import json
import unittest
from typing import Any
from wsgiref.util import setup_testing_defaults

from api.health import application


def call_application(path: str, method: str = "GET") -> tuple[str, dict[str, str], bytes]:
    environ: dict[str, Any] = {}
    setup_testing_defaults(environ)
    environ["PATH_INFO"] = path
    environ["REQUEST_METHOD"] = method
    result: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        result["status"] = status
        result["headers"] = dict(headers)

    body = b"".join(application(environ, start_response))
    return result["status"], result["headers"], body


class HealthFunctionTests(unittest.TestCase):
    def test_health_returns_service_payload_and_cors(self) -> None:
        status, headers, body = call_application("/api/health")

        self.assertEqual(status, "200 OK")
        self.assertEqual(json.loads(body), {"status": "ok", "service": "local-foundry-api"})
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_options_supports_browser_preflight(self) -> None:
        status, headers, body = call_application("/api/health", "OPTIONS")

        self.assertEqual(status, "204 No Content")
        self.assertEqual(headers["Access-Control-Allow-Methods"], "GET, OPTIONS")
        self.assertEqual(body, b"")

    def test_unimplemented_routes_return_not_found(self) -> None:
        status, _, body = call_application("/api/workspace")

        self.assertEqual(status, "404 Not Found")
        self.assertEqual(json.loads(body)["detail"], "Not found.")

    def test_health_rejects_unsupported_methods(self) -> None:
        status, _, body = call_application("/api/health", "POST")

        self.assertEqual(status, "405 Method Not Allowed")
        self.assertEqual(json.loads(body)["detail"], "Method not allowed.")


if __name__ == "__main__":
    unittest.main()