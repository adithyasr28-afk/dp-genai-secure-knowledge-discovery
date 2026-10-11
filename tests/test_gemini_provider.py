"""Gemini provider tests.

Provider selection is tested directly. The Gemini call path is exercised
through the REAL google-genai SDK pointed at a local mock HTTP server
(127.0.0.1), so request serialisation, headers, response parsing, safety
blocks and HTTP errors are covered without spending API quota.

A real call is made only by `test_live_gemini_call`, which is skipped unless
RUN_LIVE_LLM=1 and GEMINI_API_KEY are set:
    set RUN_LIVE_LLM=1 && venv\\Scripts\\python -m pytest -m live
"""

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pandas as pd
import pytest

import knowledge_discovery.llm_client as llm
from knowledge_discovery.catalog import ORIGINAL_DATA_DIR, list_dp_synthetic_datasets, load_synthetic_dataset
from knowledge_discovery.prompts import SYSTEM_PROMPT
from knowledge_discovery.summarizer import build_aggregate_summary

genai = pytest.importorskip("google.genai")
from google.genai import types  # noqa: E402

FAKE_KEY = "AQ.test-local-mock-gemini-key-000"
KEY_VARS = ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "KD_PROVIDER", "KD_MODEL",
            "KD_GEMINI_MODEL", "KD_SERVER_FALLBACK")


class Handler(BaseHTTPRequestHandler):
    status = 200
    payload = None
    captured = []

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
        Handler.captured.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()},
                                 "body": body})
        if Handler.status == 200:
            out = Handler.payload or ok_payload()
        else:
            msg = "API key not valid. Please pass a valid API key." if Handler.status == 400 else f"mock {Handler.status}"
            out = {"error": {"code": Handler.status, "message": msg, "status": "MOCK"}}
        data = json.dumps(out).encode("utf-8")
        self.send_response(Handler.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def ok_payload(finish="STOP", text="## Overview\nmock gemini response"):
    return {
        "candidates": [{
            "content": {"role": "model", "parts": [
                {"text": "internal reasoning that must not be shown", "thought": True},
                {"text": text},
            ]},
            "finishReason": finish,
        }],
        "usageMetadata": {"promptTokenCount": 4321, "candidatesTokenCount": 210, "thoughtsTokenCount": 99},
        "modelVersion": "gemini-2.5-flash",
        "responseId": "resp_mock_1",
    }


@pytest.fixture(scope="module")
def server():
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.fixture(scope="module")
def summary():
    info = next(d for d in list_dp_synthetic_datasets() if d.run_id == "adult_example_PrivBayes_eps3.0_seed43")
    return build_aggregate_summary(load_synthetic_dataset(info), info)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch, request):
    monkeypatch.setattr(llm, "AUDIT_DIR", tmp_path)
    if "live" not in request.keywords:
        monkeypatch.setattr(llm, "_load_dotenv_if_present", lambda: None)
        for var in KEY_VARS:
            monkeypatch.delenv(var, raising=False)
    Handler.captured.clear()
    Handler.status, Handler.payload = 200, None


def _client(url):
    return genai.Client(api_key=FAKE_KEY, http_options=types.HttpOptions(base_url=url, timeout=20_000))


# --- provider selection ------------------------------------------------------
def test_provider_auto_detection(monkeypatch):
    assert llm.resolve_provider() == "anthropic"            # nothing configured -> default
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert llm.resolve_provider() == "gemini"               # only Gemini key
    assert llm.live_mode_available() is True
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert llm.resolve_provider() == "anthropic"            # both -> Claude first
    monkeypatch.setenv("KD_PROVIDER", "gemini")
    assert llm.resolve_provider() == "gemini"               # explicit setting wins
    assert llm.resolve_provider("anthropic") == "anthropic"  # argument wins over setting
    with pytest.raises(ValueError):
        llm.resolve_provider("openai")


def test_env_example_placeholders_count_as_unset(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")
    monkeypatch.setenv("GEMINI_API_KEY", "real-looking-gemini-key")
    assert llm.resolve_provider() == "gemini"
    assert llm.live_mode_available("anthropic") is False


def test_google_api_key_alias(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "g")
    assert llm.resolve_provider() == "gemini" and llm.live_mode_available("gemini")


def test_missing_gemini_key_no_request(summary):
    r = llm.generate_insights(summary, mode="live", provider="gemini")
    assert not r.ok and "GEMINI_API_KEY" in r.error and not r.api_request_attempted
    assert r.provider == "gemini"


# --- real SDK against the mock server ----------------------------------------
def test_gemini_request_through_real_sdk(server, summary):
    r = llm.generate_insights(summary, mode="live", provider="gemini", client=_client(server))
    assert r.ok and r.provider == "gemini" and r.model == "gemini-2.5-flash"  # served version from response
    assert r.text.startswith("## Overview") and "internal reasoning" not in r.text
    assert r.usage == {"input_tokens": 4321, "output_tokens": 210, "thinking_tokens": 99}
    assert r.stop_reason == "end_turn" and r.api_request_attempted
    req = Handler.captured[0]
    assert f"models/{llm.DEFAULT_GEMINI_MODEL}:generateContent" in req["path"]
    body = json.loads(req["body"])
    assert body["systemInstruction"]["parts"][0]["text"] == SYSTEM_PROMPT
    assert "<aggregate_summary>" in body["contents"][0]["parts"][0]["text"]
    assert body["generationConfig"]["maxOutputTokens"] == 16000
    # credential only in the header, never in the body
    assert req["headers"].get("x-goog-api-key") == FAKE_KEY and FAKE_KEY not in req["body"]
    original = pd.read_csv(ORIGINAL_DATA_DIR / "example_dataset.csv")
    for _, row in original.head(300).iterrows():
        assert ",".join(map(str, row.values)) not in req["body"]
    audit = json.loads(open(r.audit_path, encoding="utf-8").read())
    assert audit["provider"] == "gemini" and audit["is_llm_output"] is True and FAKE_KEY not in json.dumps(audit)


def test_gemini_model_override(server, summary, monkeypatch):
    monkeypatch.setenv("KD_GEMINI_MODEL", "gemini-3.5-flash")
    llm.generate_insights(summary, mode="live", provider="gemini", client=_client(server))
    assert "models/gemini-3.5-flash:generateContent" in Handler.captured[0]["path"]


def test_gemini_safety_block_is_refusal(server, summary):
    Handler.payload = ok_payload(finish="SAFETY", text="")
    r = llm.generate_insights(summary, mode="live", provider="gemini", client=_client(server))
    assert not r.ok and r.stop_reason == "refusal"


def test_gemini_prompt_block_is_refusal(server, summary):
    Handler.payload = {"promptFeedback": {"blockReason": "SAFETY"}, "candidates": []}
    r = llm.generate_insights(summary, mode="live", provider="gemini", client=_client(server))
    assert not r.ok and r.stop_reason == "refusal"


def test_gemini_truncation_marked(server, summary):
    Handler.payload = ok_payload(finish="MAX_TOKENS")
    r = llm.generate_insights(summary, mode="live", provider="gemini", client=_client(server))
    assert r.ok and r.stop_reason == "max_tokens" and "truncated" in r.text


@pytest.mark.parametrize("status,expected", [(400, "Authentication"), (403, "Authentication"),
                                             (404, "Model not found"), (429, "Rate limited"),
                                             (500, "Gemini API error")])
def test_gemini_http_errors(server, summary, status, expected):
    Handler.status = status
    r = llm.generate_insights(summary, mode="live", provider="gemini", client=_client(server))
    assert not r.ok and expected in r.error and FAKE_KEY not in r.error


def test_gemini_connection_error(summary):
    r = llm.generate_insights(summary, mode="live", provider="gemini", client=_client("http://127.0.0.1:9"))
    assert not r.ok and "Could not reach the Gemini API" in r.error


# --- optional real call ------------------------------------------------------
@pytest.mark.live
@pytest.mark.skipif(os.environ.get("RUN_LIVE_LLM") != "1", reason="set RUN_LIVE_LLM=1 to make a real Gemini call")
def test_live_gemini_call(summary):
    llm._load_dotenv_if_present()
    if not llm._gemini_key():
        pytest.skip("GEMINI_API_KEY not configured")
    r = llm.generate_insights(summary, mode="live", provider="gemini")
    assert r.ok, r.error
    assert r.provider == "gemini" and len(r.text) > 200
