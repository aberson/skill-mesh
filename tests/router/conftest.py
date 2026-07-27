"""
Shared fixtures for tests/router/.

mock_transport_server spins up a local, ephemeral-port HTTP server so GPT
transport tests (Copilot / direct-OpenAI) can exercise real Invoke-RestMethod
call sites in runtime/skill-router.ps1 -- auth failure, rate limiting, timeout,
transport precedence -- WITHOUT any live credentials or real network calls. The
router is pointed at it via the test-only SKILL_MESH_COPILOT_BASE_URL /
SKILL_MESH_OPENAI_BASE_URL / SKILL_MESH_TRANSPORT_TIMEOUT_SEC env overrides
(runtime/skill-router.ps1 Get-CopilotBaseUrl / Get-OpenAIBaseUrl /
Get-TransportTimeoutSec).
"""
import http.server
import json
import threading
import time

import pytest


class _RecordingHandler(http.server.BaseHTTPRequestHandler):
    # Overridden per-instance by MockTransportServer via functools.partial-style
    # class attributes set at construction time (see MockTransportServer.__init__).
    status = 200
    body = None
    delay = 0.0
    received = None

    def _respond(self):
        if self.received is not None:
            self.received.append({"path": self.path, "headers": dict(self.headers)})
        if self.delay:
            time.sleep(self.delay)
        payload = json.dumps(self.body if self.body is not None else {}).encode("utf-8")
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._respond()

    def do_POST(self):
        self._respond()

    def log_message(self, *_args, **_kwargs):
        pass  # silence default request logging


class MockTransportServer:
    """A single-use local HTTP stub. One instance == one base URL."""

    def __init__(self, status=200, body=None, delay=0.0):
        self.received = []
        handler_cls = type(
            "_BoundHandler",
            (_RecordingHandler,),
            {"status": status, "body": body, "delay": delay, "received": self.received},
        )
        self._httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
        self.base_url = f"http://127.0.0.1:{self._httpd.server_address[1]}"
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def shutdown(self):
        self._httpd.shutdown()
        self._httpd.server_close()


@pytest.fixture
def mock_transport_server():
    """
    Factory fixture: mock_transport_server(status=200, body={...}, delay=0) ->
    MockTransportServer with .base_url and .received (list of {path, headers}).
    All instances created via the factory are shut down at test teardown.
    """
    instances = []

    def _make(status=200, body=None, delay=0.0):
        srv = MockTransportServer(status=status, body=body, delay=delay)
        instances.append(srv)
        return srv

    yield _make

    for srv in instances:
        srv.shutdown()


# A response body shaped like the Copilot/OpenAI "responses" API that
# ConvertFrom-ResponsesApiOutput in runtime/skill-router.ps1 parses.
#
# reasoning_leading=True prepends a {"type": "reasoning"} item with NO "content"
# key -- the shape both Copilot peers (gpt-5.6-sol, gpt-5.5; both reasoning-tier
# models) commonly emit before their final message item. This is the real-world
# shape that ConvertFrom-ResponsesApiOutput's PSObject.Properties[...] guards
# (added after deep review) must parse without throwing under Set-StrictMode.
def responses_api_body(text, reasoning_leading=False):
    output = []
    if reasoning_leading:
        output.append({"type": "reasoning", "id": "rs_test_leading"})
    output.append({"type": "message", "content": [{"type": "output_text", "text": text}]})
    return {"output": output}
