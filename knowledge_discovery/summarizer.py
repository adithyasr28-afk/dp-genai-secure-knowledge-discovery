"""
knowledge_discovery/summarizer.py

Builds the ONLY payload that is ever sent to the LLM: a JSON-serialisable
dictionary of aggregate statistics computed from one DP synthetic
dataset. No individual-level rows are included.

What the summary contains:
  - dataset metadata and the formal privacy statement from the experiment log,
  - per-column marginals (numerical quantiles; categorical shares),
  - the target's positive rate overall and broken down by each column,
  - the strongest pairwise associations (Cramer's V / Pearson r),
  - optionally, generator-quality context already measured by the
    project's own evaluation (fidelity, TSTR F1, MIA AUC), so the LLM can
    calibrate how much to trust the patterns,
  - a manifest describing what was suppressed or withheld.

Privacy boundary: everything except the quality context is computed from
the DP synthetic dataset alone, so it is post-processing of the DP release.
The quality context is different: those seven scalars were computed by the
evaluation pipeline by COMPARING the synthetic data with the real training
and test data. They are not covered by the generator's DP guarantee and
are not a DP release. They are included by default because they let the
model qualify its claims; pass include_quality_context=False to send a
payload that is pure post-processing. The manifest records which case
applies.

Small-cell suppression: every category, group or bin computed from fewer
than `min_cell_count` synthetic rows is dropped and folded into a
suppressed-count. This is NOT a formal privacy mechanism -- DP already
covers the synthetic data -- it is a defence-in-depth measure that keeps
the LLM from over-interpreting tiny, noise-dominated cells.
"""

from __future__ import annotations

from itertools import combinations
from typing import Optional

import numpy as np
import pandas as pd

from knowledge_discovery.catalog import SyntheticDatasetInfo

DEFAULT_MIN_CELL_COUNT = 20
DEFAULT_TOP_K = 8
DEFAULT_N_ASSOCIATIONS = 10
DECIMALS = 3


def _r(x) -> Optional[float]:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return round(float(x), DECIMALS)


def _infer_types(df: pd.DataFrame) -> tuple:
    numerical, categorical = [], []
    for col in df.columns:
        if col.endswith("__was_missing"):
            continue
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique() > 10:
            numerical.append(col)
        else:
            categorical.append(col)
    return numerical, categorical


def _cramers_v(a: pd.Series, b: pd.Series) -> float:
    table = pd.crosstab(a, b).values
    if table.shape[0] < 2 or table.shape[1] < 2:
        return 0.0
    n = table.sum()
    expected = table.sum(axis=1, keepdims=True) @ table.sum(axis=0, keepdims=True) / n
    chi2 = float(np.sum((table - expected) ** 2 / np.where(expected == 0, 1e-10, expected)))
    r, k = table.shape
    return float(np.sqrt((chi2 / n) / max(min(r - 1, k - 1), 1)))


def build_aggregate_summary(
    synthetic_df: pd.DataFrame,
    info: SyntheticDatasetInfo,
    target_column: Optional[str] = "income",
    min_cell_count: int = DEFAULT_MIN_CELL_COUNT,
    top_k: int = DEFAULT_TOP_K,
    n_associations: int = DEFAULT_N_ASSOCIATIONS,
    include_quality_context: bool = True,
) -> dict:
    """Aggregate-only summary of one DP synthetic dataset (see module docstring)."""
    df = synthetic_df.copy()
    n = len(df)
    numerical, categorical = _infer_types(df)
    if target_column not in df.columns:
        target_column = None
    suppressed_cells = 0

    # --- marginals ---------------------------------------------------------
    numerical_summary = {}
    for col in numerical:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        q = s.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
        numerical_summary[col] = {
            "mean": _r(s.mean()), "std": _r(s.std()),
            "p10": _r(q[0.1]), "p25": _r(q[0.25]), "median": _r(q[0.5]),
            "p75": _r(q[0.75]), "p90": _r(q[0.9]),
            "share_exactly_zero": _r((s == 0).mean()),
        }

    categorical_summary = {}
    for col in categorical:
        counts = df[col].astype(str).value_counts()
        kept = counts[counts >= min_cell_count]
        suppressed_cells += int((counts < min_cell_count).sum())
        top = kept.head(top_k)
        categorical_summary[col] = {
            "n_distinct_levels": int(counts.size),
            "top_levels": {str(k): _r(v / n) for k, v in top.items()},
            "share_in_other_levels": _r(1 - top.sum() / n),
        }

    # --- target breakdowns -------------------------------------------------
    target_summary = None
    if target_column is not None:
        classes = sorted(df[target_column].astype(str).unique())
        positive = classes[-1]  # same convention as evaluation/utility.py
        y = (df[target_column].astype(str) == positive).astype(int)
        by_column = {}
        for col in categorical:
            if col == target_column:
                continue
            g = y.groupby(df[col].astype(str)).agg(["mean", "size"])
            suppressed_cells += int((g["size"] < min_cell_count).sum())
            g = g[g["size"] >= min_cell_count].sort_values("mean", ascending=False)
            by_column[col] = {str(k): {"positive_rate": _r(r["mean"]), "share_of_rows": _r(r["size"] / n)}
                              for k, r in g.head(top_k).iterrows()}
        for col in numerical:
            try:
                bins = pd.qcut(pd.to_numeric(df[col], errors="coerce"), q=4, duplicates="drop")
            except ValueError:
                continue
            g = y.groupby(bins, observed=True).agg(["mean", "size"])
            suppressed_cells += int((g["size"] < min_cell_count).sum())
            g = g[g["size"] >= min_cell_count]
            by_column[col + " (quartile bins)"] = {
                f"{iv.left:.4g} to {iv.right:.4g}": {"positive_rate": _r(r["mean"]), "share_of_rows": _r(r["size"] / n)}
                for iv, r in g.iterrows()
            }
        target_summary = {
            "target_column": target_column,
            "positive_class": positive,
            "overall_positive_rate": _r(y.mean()),
            "positive_rate_by_column": by_column,
        }

    # --- associations ------------------------------------------------------
    cat_assoc = []
    for a, b in combinations(categorical, 2):
        cat_assoc.append({"columns": [a, b], "cramers_v": _r(_cramers_v(df[a].astype(str), df[b].astype(str)))})
    cat_assoc.sort(key=lambda d: d["cramers_v"] or 0, reverse=True)

    num_assoc = []
    if len(numerical) >= 2:
        corr = df[numerical].apply(pd.to_numeric, errors="coerce").corr()
        for a, b in combinations(numerical, 2):
            num_assoc.append({"columns": [a, b], "pearson_r": _r(corr.loc[a, b])})
        num_assoc.sort(key=lambda d: abs(d["pearson_r"] or 0), reverse=True)

    # --- context from the project's own evaluation ---------------------------
    fid = info.fidelity or {}
    quality_context = {
        "fidelity_vs_real_training_data": {
            "mean_ks_statistic_numerical": _r(fid.get("mean_ks_statistic")),
            "mean_total_variation_distance_categorical": _r(fid.get("mean_tvd")),
            "cramers_v_mean_abs_diff": _r(fid.get("cramers_v_mean_abs_diff")),
            "three_way_marginal_mean_l1_error": _r(fid.get("three_way_mean_l1_error")),
        },
        "best_tstr_f1_on_real_test_set": _r(info.best_tstr_f1),
        "membership_inference_attack_auc": _r(info.mia_auc),
        "how_to_read": (
            "Lower KS/TVD/L1 = closer to the real data. TSTR F1 = F1 of a classifier trained on this "
            "synthetic data and scored on held-out real data. MIA AUC near 0.5 = the simple distance "
            "attack could not distinguish training members."
        ),
    }

    return {
        "dataset": {
            "run_id": info.run_id,
            "generator": info.method,
            "mechanism": info.mechanism,
            "epsilon": info.epsilon,
            "delta": info.delta,
            "formal_guarantee": info.guarantee_statement,
            "generator_notes": info.extra_privacy_notes,
            "n_synthetic_rows": n,
            "numerical_columns": numerical,
            "categorical_columns": categorical,
            "representation_note": (
                "DP generators were fit on a discretised view; numerical values in this synthetic "
                "dataset were reconstructed by sampling uniformly within train-fitted bins, so "
                "within-bin detail and exact numeric correlations are approximate."
            ),
        },
        "numerical_marginals": numerical_summary,
        "categorical_marginals": categorical_summary,
        "target_analysis": target_summary,
        "strongest_categorical_associations": cat_assoc[:n_associations],
        "strongest_numerical_correlations": num_assoc[:n_associations],
        **({"generator_quality_context": quality_context} if include_quality_context else {}),
        "privacy_manifest": {
            "data_source": ("Statistics computed from the DP synthetic dataset only (results/synthetic_data/); "
                            "this layer never reads the original dataset."),
            "individual_records_included": False,
            "min_cell_count": min_cell_count,
            "cells_suppressed_below_min_count": suppressed_cells,
            "statistics_rounded_to_decimals": DECIMALS,
            "aggregates_are_separately_dp": False,
            "quality_context_included": include_quality_context,
            "quality_context_uses_real_data": include_quality_context,
            "note": (
                "Marginals, group rates and associations are post-processing of a DP synthetic dataset and "
                "spend no extra privacy budget, assuming the generator's DP guarantee and its assumptions hold. "
                + ("The generator_quality_context metrics were computed by comparing the synthetic data with the "
                   "real training/test data; they are NOT covered by the DP guarantee and are not a DP release. "
                   if include_quality_context else "No metric computed from the real data is included. ")
                + "No statistic here is a separate DP release, and the LLM adds no privacy guarantee."
            ),
        },
    }


def summary_contains_row_level_data(summary: dict, synthetic_df: pd.DataFrame, max_rows_checked: int = 500) -> bool:
    """Heuristic leak check used by tests and the app: True if any complete
    synthetic record (all of its values, in order) appears verbatim in the
    serialised summary. Aggregate summaries should never trigger it."""
    import json

    text = json.dumps(summary, default=str)
    for _, row in synthetic_df.head(max_rows_checked).iterrows():
        if ",".join(str(v) for v in row.values) in text:
            return True
    return False
