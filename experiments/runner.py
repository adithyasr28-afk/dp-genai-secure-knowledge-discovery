"""
experiments/runner.py

Orchestrates one full experiment run end-to-end:
  preprocess (once per dataset, shared) -> fit model -> generate ->
  fidelity -> utility -> privacy -> rare-patterns -> fairness (if
  applicable) -> log JSON-lines result -> save synthetic CSV.

Resumability contract: every completed run's `run_id()` is written to
`results/experiment_results.jsonl`. Before starting a run, the runner
checks whether that exact run_id is already present and skips it if so
-- this is what makes a multi-day, stop-and-restart sweep (Section
17/18 of the spec) safe: re-running the sweep script only executes runs
that haven't finished yet.

This module deliberately does the "boring but critical" plumbing work
(routing each method to the representation it needs, reconstructing
binned DP output back to continuous for fair fidelity/utility/privacy
comparison) so that models/ and evaluation/ stay simple and only know
about their own concern.
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from experiments.config import RunConfig
from preprocessing.pipeline import Preprocessor
from models.base import ColumnSpec
from models.aim_model import AIMModel
from models.mst_model import MSTModel
from models.privbayes_model import PrivBayesModel
from models.ctgan_model import CTGANModel
from models.tvae_model import TVAEModel
from evaluation import fidelity as fid_eval
from evaluation import utility as util_eval
from evaluation import privacy as priv_eval
from evaluation import rare_patterns as rare_eval
from evaluation import fairness as fair_eval
from sklearn.preprocessing import StandardScaler

RESULTS_DIR = Path("results")
RESULTS_LOG = RESULTS_DIR / "experiment_results.jsonl"
SYNTHETIC_DIR = RESULTS_DIR / "synthetic_data"

DP_METHODS = {"AIM", "MST", "PrivBayes"}
NON_DP_METHODS = {"CTGAN", "TVAE"}


def _ensure_dirs():
    RESULTS_DIR.mkdir(exist_ok=True)
    SYNTHETIC_DIR.mkdir(exist_ok=True)


def load_completed_run_ids() -> set:
    """Read every run_id that completed SUCCESSFULLY, for resumability.
    A failed run must NOT count as done -- otherwise a transient failure
    (e.g. a missing dependency, or the disk-full/OOM errors possible in
    a long multi-day sweep) would permanently block that run from ever
    being retried, since its run_id would already appear in the log."""
    _ensure_dirs()
    if not RESULTS_LOG.exists():
        return set()
    ids = set()
    with open(RESULTS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get("status") == "completed":
                    ids.add(record["run_id"])
            except (json.JSONDecodeError, KeyError):
                continue  # tolerate a corrupted trailing line from an interrupted write
    return ids


def _append_result(record: dict):
    _ensure_dirs()
    with open(RESULTS_LOG, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _build_model(config: RunConfig):
    seed = config.random_seed
    if config.method == "AIM":
        return AIMModel(
            epsilon=config.epsilon, delta=config.delta,
            max_rounds=config.extra_params.get("aim_max_rounds", 60),
            random_seed=seed,
        )
    if config.method == "MST":
        return MSTModel(epsilon=config.epsilon, delta=config.delta, random_seed=seed)
    if config.method == "PrivBayes":
        return PrivBayesModel(epsilon=config.epsilon, random_seed=seed)
    if config.method == "CTGAN":
        return CTGANModel(epochs=config.epochs or 300, random_seed=seed)
    if config.method == "TVAE":
        return TVAEModel(epochs=config.epochs or 300, random_seed=seed)
    raise ValueError(f"Unknown method: {config.method}")


def run_single_experiment(
    config: RunConfig,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    preprocessor: Preprocessor,
    numerical_columns: list,
    categorical_columns: list,
    target_column: str,
    sensitive_column: Optional[str] = None,
    skip_if_completed: bool = True,
) -> dict:
    """Run one (method, epsilon, seed) experiment and return its full
    result record (also appended to the JSON-lines log as a side
    effect). `train_df`/`test_df` must be the RAW (untransformed) real
    splits; this function owns routing each method to the
    representation it needs via `preprocessor`."""
    run_id = config.run_id()
    _ensure_dirs()  # must run unconditionally -- do not rely on load_completed_run_ids()
    # as the only path that creates results/synthetic_data/, since
    # skip_if_completed=False (e.g. an explicit UI-triggered run) skips
    # that call entirely and would otherwise fail trying to save the
    # synthetic CSV into a directory that doesn't exist yet.
    if skip_if_completed and run_id in load_completed_run_ids():
        return {"run_id": run_id, "status": "skipped_already_completed"}

    record = {
        "run_id": run_id,
        "dataset_name": config.dataset_name,
        "method": config.method,
        "random_seed": config.random_seed,
        "epsilon": config.epsilon,
        "delta": config.delta,
        "synthetic_size_multiplier": config.synthetic_size_multiplier,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "started",
    }

    try:
        is_dp = config.method in DP_METHODS
        n_synthetic = int(len(train_df) * config.synthetic_size_multiplier)

        # --- 1. Fit & generate, using the representation this method needs ---
        model = _build_model(config)
        if is_dp:
            fit_input = preprocessor.transform_discretized(train_df)
            spec = ColumnSpec(numerical_columns=[], categorical_columns=list(fit_input.columns), target_column=target_column)
        else:
            fit_input = preprocessor.transform_continuous(train_df)
            spec = ColumnSpec(numerical_columns=numerical_columns, categorical_columns=categorical_columns, target_column=target_column)

        model.fit(fit_input, spec)
        gen_result = model.generate(n_synthetic)
        synthetic_raw = gen_result.synthetic_df

        # --- 2. Reconstruct to a common CONTINUOUS representation for evaluation ---
        # DP methods emit binned ("bin_k") numerical columns; map them
        # back to continuous values so fidelity/utility/privacy compare
        # every method on the same footing (see pipeline.py).
        if is_dp:
            synthetic_cont = preprocessor.inverse_transform_discretized_numerical(
                synthetic_raw, rng=np.random.default_rng(config.random_seed)
            )
        else:
            synthetic_cont = synthetic_raw

        real_train_cont = preprocessor.transform_continuous(train_df)
        real_test_cont = preprocessor.transform_continuous(test_df)
        vocab = preprocessor.fitted_.categorical_vocab

        # Save the synthetic CSV for download / later re-analysis.
        synth_path = SYNTHETIC_DIR / f"{run_id}.csv"
        synthetic_cont.to_csv(synth_path, index=False)

        record["is_differentially_private"] = is_dp
        record["privacy_params"] = gen_result.privacy_params
        record["fit_runtime_seconds"] = gen_result.fit_runtime_seconds
        record["generate_runtime_seconds"] = gen_result.generate_runtime_seconds
        record["n_synthetic_rows"] = len(synthetic_cont)
        record["synthetic_csv_path"] = str(synth_path)

        # --- 3. Fidelity ---
        marginal_report = fid_eval.marginal_fidelity_report(
            real_train_cont, synthetic_cont, numerical_columns, categorical_columns
        )
        correlation_report = fid_eval.correlation_fidelity_report(
            real_train_cont, synthetic_cont, numerical_columns, categorical_columns
        )
        three_way_report = fid_eval.three_way_marginal_query_error(
            real_train_cont, synthetic_cont, categorical_columns, n_queries=30, random_seed=config.random_seed
        )
        out_of_range = fid_eval.out_of_range_report(real_train_cont, synthetic_cont, numerical_columns)
        record["fidelity"] = fid_eval.summarize_fidelity(marginal_report, correlation_report, three_way_report)
        record["fidelity"]["out_of_range_columns_flagged"] = (
            int((out_of_range["pct_out_of_range"] > 5.0).sum()) if len(out_of_range) else 0
        )

        # --- 4. Utility (TSTR here; TRTR is computed once per dataset by the caller, not per-run) ---
        tstr_results = util_eval.evaluate_utility(
            train_df=synthetic_cont, test_df=real_test_cont, target_column=target_column,
            numerical_columns=numerical_columns, categorical_columns=categorical_columns,
            categorical_vocab=vocab, training_source="synthetic", random_seed=config.random_seed,
        )
        record["utility_tstr"] = [r.__dict__ for r in tstr_results]

        # --- 5. Privacy ---
        record["privacy_formal"] = priv_eval.format_formal_privacy(is_dp, gen_result.privacy_params)
        mia = priv_eval.membership_inference_attack(
            real_train_cont, real_test_cont, synthetic_cont,
            numerical_columns, categorical_columns, vocab, random_seed=config.random_seed,
        )
        record["privacy_mia"] = mia
        record["privacy_record_similarity"] = priv_eval.record_similarity_report(
            real_train_cont, synthetic_cont, numerical_columns, categorical_columns, vocab
        )

        # --- 6. Rare patterns ---
        minority = rare_eval.minority_class_report(real_train_cont, synthetic_cont, target_column)
        rare_cat = rare_eval.rare_category_report(real_train_cont, synthetic_cont, categorical_columns)
        rare_combo = rare_eval.rare_combination_report(
            real_train_cont, synthetic_cont, categorical_columns, combo_size=2, random_seed=config.random_seed
        )
        record["rare_patterns"] = rare_eval.summarize_rare_pattern_loss(minority, rare_cat, rare_combo)

        # --- 7. Fairness (only if applicable) ---
        if fair_eval.is_fairness_applicable(real_train_cont, sensitive_column):
            feature_categorical = [c for c in categorical_columns if c != target_column]
            scaler = StandardScaler()
            X_train_synth = util_eval._encode_features(
                synthetic_cont, numerical_columns, feature_categorical, vocab, scaler=scaler, fit_scaler=True
            )
            X_test = util_eval._encode_features(
                real_test_cont, numerical_columns, feature_categorical, vocab, scaler=scaler, fit_scaler=False
            )
            target_classes = sorted(real_test_cont[target_column].astype(str).unique())
            positive_class = target_classes[-1]
            y_train_synth = (synthetic_cont[target_column].astype(str) == positive_class).astype(int).values
            y_test = (real_test_cont[target_column].astype(str) == positive_class).astype(int).values

            if len(np.unique(y_train_synth)) == 2:
                from sklearn.linear_model import LogisticRegression
                clf = LogisticRegression(max_iter=1000, random_state=config.random_seed)
                clf.fit(X_train_synth, y_train_synth)
                fairness_result = fair_eval.evaluate_fairness(clf, X_test, y_test, test_df[sensitive_column])
                record["fairness"] = {
                    "demographic_parity_difference": fairness_result["demographic_parity_difference"],
                    "equalized_odds": fairness_result["equalized_odds"],
                    "f1_performance_gap": fairness_result["f1_performance_gap"],
                    "auroc_performance_gap": fairness_result["auroc_performance_gap"],
                    "subgroup_performance": fairness_result["subgroup_performance"].to_dict(orient="records"),
                }
            else:
                record["fairness"] = {"note": "Synthetic training data collapsed to a single class; fairness metrics undefined."}
        else:
            record["fairness"] = None

        record["status"] = "completed"

    except Exception as e:
        record["status"] = "failed"
        record["error"] = str(e)
        record["traceback"] = traceback.format_exc()

    _append_result(record)
    return record


def compute_trtr_once(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    preprocessor: Preprocessor,
    numerical_columns: list,
    categorical_columns: list,
    target_column: str,
) -> list:
    """TRTR (train-on-real reference) doesn't depend on any synthesizer,
    so it's computed once per dataset rather than once per run -- avoids
    redundant work and guarantees every method is compared against
    exactly the same real-data ceiling."""
    real_train_cont = preprocessor.transform_continuous(train_df)
    real_test_cont = preprocessor.transform_continuous(test_df)
    vocab = preprocessor.fitted_.categorical_vocab

    trtr_results = util_eval.evaluate_utility(
        train_df=real_train_cont, test_df=real_test_cont, target_column=target_column,
        numerical_columns=numerical_columns, categorical_columns=categorical_columns,
        categorical_vocab=vocab, training_source="real", random_seed=42,
    )
    return [r.__dict__ for r in trtr_results]


def load_all_results() -> pd.DataFrame:
    """Load every logged result (across possibly many resumed sessions)
    as a flat DataFrame for the Streamlit comparison views."""
    _ensure_dirs()
    if not RESULTS_LOG.exists():
        return pd.DataFrame()
    records = []
    with open(RESULTS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return pd.DataFrame(records)
