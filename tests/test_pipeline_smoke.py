"""Smoke tests for the ORIGINAL pipeline (dataset loading, leakage-safe
preprocessing, and each generator end-to-end through the experiment
runner). Generator runs write to a temporary results directory, never to
results/experiment_results.jsonl.

The generator tests are marked `slow` (MST/AIM take ~1 min each):
    pytest -m "not slow"   # fast checks only
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import experiments.runner as runner
from experiments.config import RunConfig, SweepConfig
from preprocessing.pipeline import Preprocessor, train_test_split_no_leakage
from preprocessing.schema import profile_dataset


@pytest.fixture(scope="module")
def data():
    df = pd.read_csv("data/example_dataset.csv")
    profile = profile_dataset(df)
    num = [c.name for c in profile.columns if c.inferred_type == "numerical"]
    cat = [c.name for c in profile.columns if c.inferred_type == "categorical"]
    if "income" not in cat:
        cat.append("income")
    train, test = train_test_split_no_leakage(df, test_size=0.2, random_seed=42, stratify_column="income")
    pp = Preprocessor(rare_threshold=0.01, n_bins=10, random_seed=42)
    pp.fit(train, numerical_columns=num, categorical_columns=cat, target_column="income", sensitive_column="sex")
    return df, train, test, pp, num, cat


def test_dataset_shape(data):
    df, train, test, *_ = data
    assert df.shape == (3000, 14)
    assert (len(train), len(test)) == (2400, 600)


def test_sweep_has_41_configs():
    configs = SweepConfig(dataset_name="adult_example").build_run_configs()
    assert len(configs) == 41
    assert len({c.run_id() for c in configs}) == 41


def test_preprocessing_fit_uses_train_only(data):
    _, train, test, pp, num, cat = data
    pp2 = Preprocessor(rare_threshold=0.01, n_bins=10, random_seed=42)
    pp2.fit(pd.concat([train, test.assign(age=999)]), num, cat, target_column="income")
    assert pp.fitted_.numerical_bin_edges["age"] != pp2.fitted_.numerical_bin_edges["age"]
    disc = pp.transform_discretized(test)
    assert disc.shape[0] == len(test) and disc.notna().all().all()


def test_inverse_transform_stays_in_bin(data):
    _, train, _, pp, num, _ = data
    disc = pp.transform_discretized(train)
    back = pp.inverse_transform_discretized_numerical(disc, rng=np.random.default_rng(0))
    edges = pp.fitted_.numerical_bin_edges["age"]
    assert back["age"].between(edges[0], edges[-1]).all()


@pytest.fixture
def tmp_results(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(runner, "RESULTS_LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(runner, "SYNTHETIC_DIR", tmp_path / "synthetic_data")
    return tmp_path


@pytest.mark.slow
@pytest.mark.parametrize("method,kwargs", [
    ("PrivBayes", dict(epsilon=1.0, delta=0.0)),
    ("MST", dict(epsilon=1.0, delta=1e-5)),
    # rounds must exceed ~0.9 * n_columns (14 here) or snsynth AIM overspends rho on the
    # initial one-way measurements and fails with NaN probabilities; 20 keeps the test short.
    ("AIM", dict(epsilon=1.0, delta=1e-5, extra_params={"aim_max_rounds": 20})),
    ("CTGAN", dict(epochs=2)),
    ("TVAE", dict(epochs=2)),
])
def test_generator_end_to_end(data, tmp_results, method, kwargs):
    _, train, test, pp, num, cat = data
    cfg = RunConfig(dataset_name="smoke", method=method, random_seed=42, **kwargs)
    rec = runner.run_single_experiment(cfg, train, test, pp, num, cat, "income", "sex", skip_if_completed=False)
    assert rec["status"] == "completed", rec.get("traceback")
    assert rec["n_synthetic_rows"] == len(train)
    assert rec["is_differentially_private"] == (method in runner.DP_METHODS)
    assert 0.0 <= rec["privacy_mia"]["attack_auc"] <= 1.0
    assert (tmp_results / "synthetic_data" / f"{cfg.run_id()}.csv").exists()
