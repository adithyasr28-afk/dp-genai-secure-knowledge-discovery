"""Exercises LIVE mode through the real Anthropic SDK against a local mock
HTTP server (127.0.0.1), so request serialisation, headers, response
parsing and HTTP error handling are tested without an API key or network.
This does NOT prove the real API accepts the request -- only a call with a
real key can do that (see README, "Live-mode verification status")."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import anthropic
import pandas as pd
import pytest

import knowledge_discovery.llm_client as llm
from knowledge_discovery.catalog import ORIGINAL_DATA_DIR, list_dp_synthetic_datasets, load_synthetic_dataset
from knowledge_discovery.summarizer import build_aggregate_summary

FAKE_KEY = "sk-ant-test-local-mock-key-000"


class Handler(BaseHTTPRequestHandler):
    status = 200
    captured = []

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8")
        Handler.captured.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "body": body})
        if Handler.status == 200:
            payload = {"id": "msg_test", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
                       "content": [{"type": "text", "text": "## Overview\nmock response"}],
                       "stop_reason": "end_turn", "stop_sequence": None,
                       "usage": {"input_tokens": 1234, "output_tokens": 56}}
        else:
            payload = {"type": "error", "error": {"type": "error", "message": f"mock {Handler.status}"}}
        data = json.dumps(payload).encode("utf-8")
        self.send_response(Handler.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("request-id", "req_mock_1")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def server():
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.fixture(scope="module")
def summary():
    info = next(d for d in list_dp_synthetic_datasets() if d.run_id == "adult_example_MST_eps1.0_seed42")
    return build_aggregate_summary(load_synthetic_dataset(info), info)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "AUDIT_DIR", tmp_path)
    Handler.captured.clear()
    Handler.status = 200


def _client(url):
    return anthropic.Anthropic(api_key=FAKE_KEY, base_url=url, max_retries=0)


def test_live_request_through_real_sdk(server, summary):
    r = llm.generate_insights(summary, mode="live", client=_client(server))
    assert r.ok and r.text.startswith("## Overview") and r.usage["input_tokens"] == 1234
    req = Handler.captured[0]
    body = json.loads(req["body"])
    assert req["path"].startswith("/v1/messages")
    assert body["model"] == "claude-opus-5-5" and body["fallbacks"] == "default"
    assert body["output_config"] == {"effort": "medium"}
    assert llm.FALLBACK_BETA in req["headers"].get("anthropic-beta", "")
    # credential only in the auth header, never in the body
    assert req["headers"].get("x-api-key") == FAKE_KEY and FAKE_KEY not in req["body"]
    # no original record in the body
    original = pd.read_csv(ORIGINAL_DATA_DIR / "example_dataset.csv")
    for _, row in original.head(300).iterrows():
        assert ",".join(map(str, row.values)) not in req["body"]


@pytest.mark.parametrize("status,expected", [(401, "Authentication"), (429, "Rate limited"),
                                             (500, "HTTP 500"), (400, "rejected")])
def test_http_errors_through_real_sdk(server, summary, status, expected):
    Handler.status = status
    r = llm.generate_insights(summary, mode="live", client=_client(server))
    assert not r.ok and expected in r.error


def test_connection_error_through_real_sdk(summary):
    r = llm.generate_insights(summary, mode="live", client=_client("http://127.0.0.1:9"))
    assert not r.ok and "Could not reach" in r.error
