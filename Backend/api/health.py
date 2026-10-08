import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path.partition("?")[0] not in ("/api/health", "/health"):
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            return

        payload = json.dumps({"status": "ok", "service": "local-foundry-api"}).encode()
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), handler)
    print("Health API listening at http://127.0.0.1:8000/api/health")
    server.serve_forever()