"""
evaluation/fidelity.py

Quantitative fidelity metrics comparing real vs. synthetic data.
Never judge by eyeballing rows -- every metric here is a number that
can be logged, compared across methods, and plotted against epsilon.

All functions take the CONTINUOUS representation (i.e. the output of
Preprocessor.transform_continuous(), or the discretized-then-inverse-
transformed output for DP methods -- see preprocessing/pipeline.py),
so real and synthetic data are always compared on a like-for-like
representation regardless of which internal representation a given
method needed during generation.
"""

from __future__ import annotations

from itertools import combinations
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, wasserstein_distance


def _safe_probs(counts: pd.Series, categories: list) -> np.ndarray:
    """Turn a value_counts() Series into a probability vector aligned to
    a fixed category list, with zero mass for unseen categories."""
    total = counts.sum()
    if total == 0:
        return np.ones(len(categories)) / len(categories)
    probs = np.array([counts.get(c, 0) for c in categories], dtype=float)
    return probs / probs.sum()


def total_variation_distance(real: pd.Series, synthetic: pd.Series) -> float:
    """TVD between two categorical distributions: 0 = identical, 1 = disjoint."""
    categories = sorted(set(real.dropna().unique()) | set(synthetic.dropna().unique()))
    p = _safe_probs(real.value_counts(), categories)
    q = _safe_probs(synthetic.value_counts(), categories)
    return float(0.5 * np.abs(p - q).sum())


def jensen_shannon_divergence(real: pd.Series, synthetic: pd.Series) -> float:
    """JSD between two categorical distributions (base-2, bounded [0,1])."""
    categories = sorted(set(real.dropna().unique()) | set(synthetic.dropna().unique()))
    p = _safe_probs(real.value_counts(), categories)
    q = _safe_probs(synthetic.value_counts(), categories)
    m = 0.5 * (p + q)

    def _kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))

    return float(0.5 * _kl(p, m) + 0.5 * _kl(q, m))


def marginal_fidelity_report(
    real_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    numerical_columns: list,
    categorical_columns: list,
) -> pd.DataFrame:
    """Per-column 1-way marginal fidelity: KS + Wasserstein for numerical
    columns, TVD + JSD for categorical columns. Returns one row per
    column so results can be aggregated (mean) or inspected individually
    to spot which specific columns a method struggles with."""
    rows = []

    for col in numerical_columns:
        real_vals = pd.to_numeric(real_df[col], errors="coerce").dropna()
        synth_vals = pd.to_numeric(synthetic_df[col], errors="coerce").dropna()
        if len(real_vals) == 0 or len(synth_vals) == 0:
            continue
        ks_stat, ks_p = ks_2samp(real_vals, synth_vals)
        # Normalize Wasserstein by the real column's range so it's
        # comparable across columns with very different scales.
        real_range = real_vals.max() - real_vals.min()
        w_dist = wasserstein_distance(real_vals, synth_vals)
        w_dist_norm = w_dist / real_range if real_range > 0 else w_dist

        rows.append({
            "column": col,
            "type": "numerical",
            "ks_statistic": float(ks_stat),
            "ks_pvalue": float(ks_p),
            "wasserstein_distance": float(w_dist),
            "wasserstein_distance_normalized": float(w_dist_norm),
            "tvd": np.nan,
            "jsd": np.nan,
        })

    for col in categorical_columns:
        real_vals = real_df[col].astype("object")
        synth_vals = synthetic_df[col].astype("object")
        rows.append({
            "column": col,
            "type": "categorical",
            "ks_statistic": np.nan,
            "ks_pvalue": np.nan,
            "wasserstein_distance": np.nan,
            "wasserstein_distance_normalized": np.nan,
            "tvd": total_variation_distance(real_vals, synth_vals),
            "jsd": jensen_shannon_divergence(real_vals, synth_vals),
        })

    return pd.DataFrame(rows)


def correlation_fidelity_report(
    real_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    numerical_columns: list,
    categorical_columns: list,
    correlation_method: str = "pearson",
) -> dict:
    """Compare real vs synthetic pairwise structure:
      - Pearson/Spearman correlation matrix for numerical columns
        (Frobenius-norm difference, and per-pair max absolute difference).
      - Cramer's V for categorical-categorical pairs (mean absolute
        difference across all pairs).
    `correlation_method`: 'pearson' or 'spearman'.
    """
    result = {"correlation_method": correlation_method}

    if len(numerical_columns) >= 2:
        real_num = real_df[numerical_columns].apply(pd.to_numeric, errors="coerce")
        synth_num = synthetic_df[numerical_columns].apply(pd.to_numeric, errors="coerce")
        real_corr = real_num.corr(method=correlation_method).fillna(0)
        synth_corr = synth_num.corr(method=correlation_method).fillna(0)
        diff = (real_corr - synth_corr).values
        result["numerical_corr_frobenius_diff"] = float(np.linalg.norm(diff))
        result["numerical_corr_max_abs_diff"] = float(np.max(np.abs(diff)))
        result["numerical_corr_mean_abs_diff"] = float(np.mean(np.abs(diff)))
    else:
        result["numerical_corr_frobenius_diff"] = None
        result["numerical_corr_max_abs_diff"] = None
        result["numerical_corr_mean_abs_diff"] = None

    if len(categorical_columns) >= 2:
        cramers_diffs = []
        for col_a, col_b in combinations(categorical_columns, 2):
            v_real = _cramers_v(real_df[col_a], real_df[col_b])
            v_synth = _cramers_v(synthetic_df[col_a], synthetic_df[col_b])
            cramers_diffs.append(abs(v_real - v_synth))
        result["cramers_v_mean_abs_diff"] = float(np.mean(cramers_diffs)) if cramers_diffs else None
        result["cramers_v_max_abs_diff"] = float(np.max(cramers_diffs)) if cramers_diffs else None
    else:
        result["cramers_v_mean_abs_diff"] = None
        result["cramers_v_max_abs_diff"] = None

    return result


def _cramers_v(series_a: pd.Series, series_b: pd.Series) -> float:
    """Cramer's V association measure between two categorical columns,
    with the standard bias correction (Bergsma 2013). Returns a value
    in [0, 1]; 0 = no association, 1 = perfect association."""
    confusion = pd.crosstab(series_a, series_b)
    if confusion.size == 0 or confusion.shape[0] < 2 or confusion.shape[1] < 2:
        return 0.0
    chi2 = _chi2_stat(confusion.values)
    n = confusion.values.sum()
    if n == 0:
        return 0.0
    phi2 = chi2 / n
    r, k = confusion.shape
    # Bias correction
    phi2_corr = max(0.0, phi2 - ((k - 1) * (r - 1)) / max(n - 1, 1))
    r_corr = r - ((r - 1) ** 2) / max(n - 1, 1)
    k_corr = k - ((k - 1) ** 2) / max(n - 1, 1)
    denom = min(k_corr - 1, r_corr - 1)
    if denom <= 0:
        return 0.0
    return float(np.sqrt(phi2_corr / denom))


def _chi2_stat(observed: np.ndarray) -> float:
    """Pearson chi-squared statistic, computed directly to avoid an
    extra scipy.stats.chi2_contingency dependency edge case with
    zero-count rows/columns (which we handle via a small epsilon)."""
    row_sums = observed.sum(axis=1, keepdims=True)
    col_sums = observed.sum(axis=0, keepdims=True)
    total = observed.sum()
    if total == 0:
        return 0.0
    expected = row_sums @ col_sums / total
    expected = np.where(expected == 0, 1e-10, expected)
    return float(np.sum((observed - expected) ** 2 / expected))


def three_way_marginal_query_error(
    real_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    categorical_columns: list,
    n_queries: int = 50,
    random_seed: int = 42,
) -> dict:
    """Higher-order-relationship check: sample random 3-way column
    combinations, compute the joint marginal distribution on real vs.
    synthetic data, and report the mean L1 (total variation) error.
    This is the exact style of metric used in the SIGMOD 2025 DP-
    synthesis benchmark specifically because a model can nail every
    1-way marginal while still failing to capture how three columns
    interact jointly."""
    rng = np.random.default_rng(random_seed)
    if len(categorical_columns) < 3:
        return {"n_queries_run": 0, "mean_l1_error": None, "note": "Fewer than 3 categorical columns available."}

    all_triples = list(combinations(categorical_columns, 3))
    n_queries = min(n_queries, len(all_triples))
    chosen_idx = rng.choice(len(all_triples), size=n_queries, replace=False)
    triples = [all_triples[i] for i in chosen_idx]

    errors = []
    for triple in triples:
        real_joint = real_df[list(triple)].astype(str).value_counts(normalize=True)
        synth_joint = synthetic_df[list(triple)].astype(str).value_counts(normalize=True)
        all_keys = set(real_joint.index) | set(synth_joint.index)
        l1 = sum(abs(real_joint.get(k, 0.0) - synth_joint.get(k, 0.0)) for k in all_keys)
        errors.append(0.5 * l1)  # 0.5 factor -> total variation distance convention

    return {
        "n_queries_run": n_queries,
        "mean_l1_error": float(np.mean(errors)),
        "max_l1_error": float(np.max(errors)),
        "std_l1_error": float(np.std(errors)),
    }


def out_of_range_report(
    real_df: pd.DataFrame, synthetic_df: pd.DataFrame, numerical_columns: list
) -> pd.DataFrame:
    """Synthetic-data validation check (pipeline stage 'Synthetic Data
    Validation'): flags numerical columns where the generator produced
    values outside the real training data's observed range (e.g. GAN/
    VAE mode-normalization occasionally emitting small negative values
    for an inherently non-negative column like capital_gain -- an
    expected, reportable model limitation, not silently clipped away)."""
    rows = []
    for col in numerical_columns:
        real_vals = pd.to_numeric(real_df[col], errors="coerce").dropna()
        synth_vals = pd.to_numeric(synthetic_df[col], errors="coerce").dropna()
        if len(real_vals) == 0 or len(synth_vals) == 0:
            continue
        real_min, real_max = real_vals.min(), real_vals.max()
        below = (synth_vals < real_min).sum()
        above = (synth_vals > real_max).sum()
        rows.append({
            "column": col,
            "real_min": float(real_min),
            "real_max": float(real_max),
            "n_below_range": int(below),
            "n_above_range": int(above),
            "pct_out_of_range": round(100 * (below + above) / len(synth_vals), 2),
        })
    return pd.DataFrame(rows)


def summarize_fidelity(marginal_report: pd.DataFrame, correlation_report: dict, three_way_report: dict) -> dict:
    """Collapse the detailed reports into a small set of headline
    numbers for the cross-method comparison table (Section 15 of the
    project spec)."""
    numerical_rows = marginal_report[marginal_report["type"] == "numerical"]
    categorical_rows = marginal_report[marginal_report["type"] == "categorical"]

    return {
        "mean_ks_statistic": float(numerical_rows["ks_statistic"].mean()) if len(numerical_rows) else None,
        "mean_wasserstein_normalized": float(numerical_rows["wasserstein_distance_normalized"].mean()) if len(numerical_rows) else None,
        "mean_tvd": float(categorical_rows["tvd"].mean()) if len(categorical_rows) else None,
        "mean_jsd": float(categorical_rows["jsd"].mean()) if len(categorical_rows) else None,
        "numerical_corr_frobenius_diff": correlation_report.get("numerical_corr_frobenius_diff"),
        "cramers_v_mean_abs_diff": correlation_report.get("cramers_v_mean_abs_diff"),
        "three_way_mean_l1_error": three_way_report.get("mean_l1_error"),
    }
