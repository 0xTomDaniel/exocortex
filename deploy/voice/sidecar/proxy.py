#!/usr/bin/env python3
"""Narrow, unauthenticated loopback proxy for the Hermes Runs API.

The proxy and Codex sidecar share the Hermes container's network namespace.
Only this proxy receives the Hermes API key. It permits run lifecycle operations
needed by the voice spike and nothing else.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import os
from pathlib import Path
import re

UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 8642
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8765
MAX_BODY = 1024 * 1024
KEY = Path(os.environ["HERMES_API_KEY_FILE"]).read_text().strip()
if not KEY:
    raise SystemExit("Hermes API key file is empty")

RUN = r"run_[A-Za-z0-9_]+"
ALLOWED = [
    ("POST", re.compile(r"^/v1/runs$")),
    ("GET", re.compile(rf"^/v1/runs/{RUN}$")),
    ("GET", re.compile(rf"^/v1/runs/{RUN}/events$")),
    ("POST", re.compile(rf"^/v1/runs/{RUN}/(?:steer|stop|approval)$")),
    ("GET", re.compile(r"^/health$")),
]
PASS_REQUEST_HEADERS = {
    "accept", "content-type", "idempotency-key", "x-hermes-session-key"
}


def permitted(method: str, path: str) -> bool:
    return any(method == candidate and pattern.fullmatch(path) for candidate, pattern in ALLOWED)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "exo-run-proxy/0.1"

    def do_GET(self):
        self._forward()

    def do_POST(self):
        self._forward()

    def do_PUT(self):
        self.send_error(405)

    def do_DELETE(self):
        self.send_error(405)

    def do_PATCH(self):
        self.send_error(405)

    def _forward(self):
        path = self.path.split("?", 1)[0]
        if not permitted(self.command, path):
            self.send_error(403, "endpoint not allowed by voice bridge")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "invalid content length")
            return
        if length < 0 or length > MAX_BODY:
            self.send_error(413, "request body too large")
            return
        body = self.rfile.read(length) if length else None
        headers = {"Authorization": f"Bearer {KEY}", "Connection": "close"}
        for name, value in self.headers.items():
            if name.lower() in PASS_REQUEST_HEADERS:
                headers[name] = value
        upstream = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=1800)
        try:
            upstream.request(self.command, path, body=body, headers=headers)
            response = upstream.getresponse()
            content_type = response.getheader("Content-Type", "application/octet-stream")
            is_stream = "text/event-stream" in content_type.lower()
            self.send_response(response.status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if is_stream:
                self.send_header("Connection", "close")
                self.end_headers()
                while True:
                    line = response.readline()
                    if not line:
                        break
                    self.wfile.write(line)
                    self.wfile.flush()
                self.close_connection = True
            else:
                payload = response.read(MAX_BODY + 1)
                if len(payload) > MAX_BODY:
                    raise RuntimeError("upstream response exceeded limit")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:
            if not self.wfile.closed:
                try:
                    self.send_error(502, str(exc)[:200])
                except Exception:
                    pass
        finally:
            upstream.close()

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {self.command} {self.path} " + (fmt % args), flush=True)


ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler).serve_forever()
