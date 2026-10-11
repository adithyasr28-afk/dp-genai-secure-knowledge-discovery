"""Tests for the LLM knowledge-discovery extension. No network calls are
made: live mode is exercised with a fake client that records exactly what
would have been sent to the Anthropic API."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import knowledge_discovery.llm_client as llm
from knowledge_discovery.catalog import (
    IneligibleDatasetError, ORIGINAL_DATA_DIR, list_dp_synthetic_datasets, load_synthetic_dataset,
)
from knowledge_discovery.summarizer import build_aggregate_summary, summary_contains_row_level_data

ORIGINAL_CSV = ORIGINAL_DATA_DIR / "example_dataset.csv"


class FakeMessages:
    def __init__(self, parent):
        self.parent = parent

    def create(self, **kwargs):
        self.parent.calls.append(kwargs)
        if self.parent.raise_exc is not None:
            raise self.parent.raise_exc
        return SimpleNamespace(
            content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=self.parent.text)],
            stop_reason=self.parent.stop_reason, model="claude-opus-5-5",
            usage=SimpleNamespace(input_tokens=100, output_tokens=50), _request_id="req_test",
        )


class FakeClient:
    def __init__(self, text="## Overview\nfake LLM text", stop_reason="end_turn", raise_exc=None):
        self.calls, self.text, self.stop_reason, self.raise_exc = [], text, stop_reason, raise_exc
        self.messages = FakeMessages(self)
        self.beta = SimpleNamespace(messages=FakeMessages(self))


@pytest.fixture(scope="module")
def catalog():
    return list_dp_synthetic_datasets()


@pytest.fixture(scope="module")
def aim3(catalog):
    return next(d for d in catalog if d.run_id == "adult_example_AIM_eps3.0_seed42")


@pytest.fixture(scope="module")
def summary(aim3):
    return build_aggregate_summary(load_synthetic_dataset(aim3), aim3)


@pytest.fixture(autouse=True)
def isolated_audit(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setattr(llm, "_load_dotenv_if_present", lambda: None)


# --- catalog -----------------------------------------------------------------
def test_catalog_lists_only_dp_methods(catalog):
    assert len(catalog) == 35  # AIM 5 + MST 15 + PrivBayes 15
    assert {d.method for d in catalog} == {"AIM", "MST", "PrivBayes"}


def test_catalog_privacy_parameters_come_from_log(catalog):
    for d in catalog:
        if d.method == "PrivBayes":
            assert d.delta == 0.0 and "pure DP" in d.guarantee_statement
        else:
            assert d.delta == 1e-5
        if d.method == "AIM":
            assert d.extra_privacy_notes.get("rounds_cap_applied") == 60


def test_duplicate_run_uses_latest_record(aim3):
    assert aim3.n_log_records == 2
    latest = [json.loads(l) for l in open(Path("results/experiment_results.jsonl")) if aim3.run_id in l][-1]
    assert aim3.mia_auc == latest["privacy_mia"]["attack_auc"]


def test_refuses_original_dataset_and_non_dp(aim3):
    with pytest.raises(IneligibleDatasetError):
        load_synthetic_dataset(SimpleNamespace(**{**aim3.__dict__, "csv_path": ORIGINAL_CSV}))
    with pytest.raises(IneligibleDatasetError):
        load_synthetic_dataset(SimpleNamespace(**{**aim3.__dict__, "method": "CTGAN"}))


# --- summary -----------------------------------------------------------------
def test_summary_is_aggregate_only(summary, aim3):
    synth = load_synthetic_dataset(aim3)
    assert summary["privacy_manifest"]["individual_records_included"] is False
    assert not summary_contains_row_level_data(summary, synth)
    text = json.dumps(summary)
    assert len(text) < 30_000  # bounded, summary-sized payload


def test_original_rows_never_in_prompt(summary, monkeypatch):
    original = pd.read_csv(ORIGINAL_CSV)
    fake = FakeClient()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-a-real-key")
    llm.generate_insights(summary, mode="live", client=fake)
    sent = json.dumps(fake.calls[0])
    for _, row in original.head(300).iterrows():
        assert ",".join(str(v) for v in row.values) not in sent
        assert json.dumps(list(map(str, row.values))) not in sent


def test_original_file_not_read_during_summary_and_generation(aim3, monkeypatch):
    real_read_csv = pd.read_csv

    def guarded(path, *a, **k):
        assert "example_dataset" not in str(path), "original dataset must not be read"
        return real_read_csv(path, *a, **k)

    monkeypatch.setattr(pd, "read_csv", guarded)
    s = build_aggregate_summary(load_synthetic_dataset(aim3), aim3)
    llm.generate_insights(s, mode="demo")


def test_small_cells_suppressed(aim3):
    df = load_synthetic_dataset(aim3)
    s = build_aggregate_summary(df, aim3, min_cell_count=100)
    for col, info in s["categorical_marginals"].items():
        counts = df[col].astype(str).value_counts()
        for level, share in info["top_levels"].items():
            assert counts[level] >= 100


# --- LLM client --------------------------------------------------------------
def test_demo_mode_is_labelled_and_offline(summary):
    r = llm.generate_insights(summary, mode="demo")
    assert r.ok and r.mode == "demo" and "NOT generated by an LLM" in r.text
    audit = json.loads(Path(r.audit_path).read_text(encoding="utf-8"))
    assert audit["is_llm_output"] is False and audit["user_message_sent_to_api"] is False


def test_missing_api_key_gives_clear_error(summary, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = llm.generate_insights(summary, mode="live")
    assert not r.ok and "ANTHROPIC_API_KEY" in r.error
    assert llm.generate_insights(summary, mode="auto").mode == "demo"


def test_live_mode_request_shape_and_no_secret_leak(summary, monkeypatch):
    secret = "sk-ant-test-SECRET-123456"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    fake = FakeClient()
    r = llm.generate_insights(summary, mode="live", client=fake)
    assert r.ok and r.mode == "live" and r.text.startswith("## Overview")
    call = fake.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default" and call["betas"] == [llm.FALLBACK_BETA]
    assert "<aggregate_summary>" in call["messages"][0]["content"]
    assert secret not in json.dumps(call) and secret not in Path(r.audit_path).read_text(encoding="utf-8")


def test_fallback_can_be_disabled(summary, monkeypatch):
    monkeypatch.setenv("KD_SERVER_FALLBACK", "0")
    fake = FakeClient()
    llm.generate_insights(summary, mode="live", client=fake)
    assert "fallbacks" not in fake.calls[0] and "betas" not in fake.calls[0]


def test_refusal_and_empty_responses_are_errors(summary):
    assert not llm.generate_insights(summary, mode="live", client=FakeClient(stop_reason="refusal")).ok
    assert not llm.generate_insights(summary, mode="live", client=FakeClient(text="  ")).ok


def _api_errors():
    import anthropic
    import importlib

    httpx = importlib.import_module("httpx2") if importlib.util.find_spec("httpx2") else importlib.import_module("httpx")
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = lambda code: httpx.Response(code, request=req)
    return [
        (anthropic.AuthenticationError("bad key", response=resp(401), body=None), "Authentication"),
        (anthropic.RateLimitError("slow down", response=resp(429), body=None), "Rate limited"),
        (anthropic.InternalServerError("boom", response=resp(500), body=None), "HTTP 500"),
        (anthropic.APIConnectionError(request=req), "Could not reach"),
    ]


@pytest.mark.parametrize("idx", range(4))
def test_api_errors_are_handled(summary, idx):
    exc, expected = _api_errors()[idx]
    r = llm.generate_insights(summary, mode="live", client=FakeClient(raise_exc=exc))
    assert not r.ok and expected in r.error
