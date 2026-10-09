import json
from collections.abc import Callable
from typing import Any

from services.health import get_health

StartResponse = Callable[[str, list[tuple[str, str]]], Any]


def application(environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
    """WSGI entry point for on-demand HTTP adapters."""
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "")
    cors_headers = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]

    if path not in ("/api/health", "/health"):
        status = "404 Not Found"
        payload = json.dumps({"detail": "Not found."}).encode("utf-8")
    elif method == "OPTIONS":
        start_response("204 No Content", cors_headers)
        return [b""]
    elif method != "GET":
        status = "405 Method Not Allowed"
        payload = json.dumps({"detail": "Method not allowed."}).encode("utf-8")
    else:
        status = "200 OK"
        payload = json.dumps(get_health()).encode("utf-8")

    headers = cors_headers + [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(payload))),
        ("Cache-Control", "no-store"),
    ]
    start_response(status, headers)
    return [payload]