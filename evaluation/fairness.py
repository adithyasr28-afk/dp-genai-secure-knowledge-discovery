"""
evaluation/fairness.py

Fairness analysis: how does DP noise (or GAN/VAE approximation) affect
subgroup prediction quality relative to training on real data? Only
runs when the dataset has a designated sensitive attribute (per Section
13 of the project spec) -- callers must check for this and skip calling
this module entirely rather than forcing an irrelevant analysis on a
dataset without one (see experiments/runner.py).

Metrics:
  - Demographic parity difference: |P(pred=1 | group A) - P(pred=1 | group B)|
  - Equalized odds difference: max over {TPR, FPR} of the group gap
  - Subgroup F1 / AUROC: per-group downstream performance
  - Performance gap: max(group metric) - min(group metric)

All metrics are computed on REAL test-set predictions from a classifier
trained on either real (TRTR) or synthetic (TSTR) data, so this module
answers "does training on this method's synthetic data change fairness
outcomes relative to training on real data" -- not "is the real data
itself fair", which is a different (also legitimate, but out of scope
here) question.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score


def _binarize_target(series: pd.Series, positive_class: str) -> np.ndarray:
    return (series.astype(str) == positive_class).astype(int).values


def subgroup_performance_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray],
    sensitive_values: pd.Series,
) -> pd.DataFrame:
    """Per-subgroup F1 and AUROC (if probabilities are available), plus
    the group's sample size (small subgroups produce noisy metrics --
    reporting n lets the reader judge how much to trust each row)."""
    rows = []
    for group in sorted(sensitive_values.astype(str).unique()):
        mask = (sensitive_values.astype(str) == group).values
        n = int(mask.sum())
        if n == 0:
            continue
        yt, yp = y_true[mask], y_pred[mask]
        f1 = f1_score(yt, yp, zero_division=0) if len(np.unique(yt)) > 0 else np.nan
        auroc = np.nan
        if y_proba is not None and len(np.unique(yt)) == 2:
            try:
                auroc = roc_auc_score(yt, y_proba[mask])
            except ValueError:
                pass
        rows.append({
            "group": group,
            "n": n,
            "positive_rate_true": float(yt.mean()) if n > 0 else np.nan,
            "positive_rate_predicted": float(yp.mean()) if n > 0 else np.nan,
            "f1": float(f1) if pd.notna(f1) else np.nan,
            "auroc": float(auroc) if pd.notna(auroc) else np.nan,
        })
    return pd.DataFrame(rows)


def demographic_parity_difference(y_pred: np.ndarray, sensitive_values: pd.Series) -> float:
    """max_g P(pred=1 | group=g) - min_g P(pred=1 | group=g). 0 = perfect
    parity; larger values indicate the model predicts the positive
    outcome at very different rates across groups."""
    rates = []
    for group in sensitive_values.astype(str).unique():
        mask = (sensitive_values.astype(str) == group).values
        if mask.sum() == 0:
            continue
        rates.append(y_pred[mask].mean())
    return float(max(rates) - min(rates)) if len(rates) >= 2 else float("nan")


def equalized_odds_difference(y_true: np.ndarray, y_pred: np.ndarray, sensitive_values: pd.Series) -> dict:
    """max group-gap in TPR and in FPR. Equalized odds requires BOTH
    gaps to be small; reporting them separately (rather than a single
    blended number) lets the reader see which failure mode, if any, is
    present."""
    tprs, fprs = [], []
    for group in sensitive_values.astype(str).unique():
        mask = (sensitive_values.astype(str) == group).values
        yt, yp = y_true[mask], y_pred[mask]
        pos = yt == 1
        neg = yt == 0
        tpr = yp[pos].mean() if pos.sum() > 0 else np.nan
        fpr = yp[neg].mean() if neg.sum() > 0 else np.nan
        if pd.notna(tpr):
            tprs.append(tpr)
        if pd.notna(fpr):
            fprs.append(fpr)

    tpr_gap = float(max(tprs) - min(tprs)) if len(tprs) >= 2 else float("nan")
    fpr_gap = float(max(fprs) - min(fprs)) if len(fprs) >= 2 else float("nan")
    return {"tpr_gap": tpr_gap, "fpr_gap": fpr_gap, "max_gap": float(np.nanmax([tpr_gap, fpr_gap]))}


def evaluate_fairness(
    classifier,
    X_test: np.ndarray,
    y_test: np.ndarray,
    sensitive_values: pd.Series,
) -> dict:
    """Run the full fairness battery for one already-fitted classifier,
    scored on the real test set. `classifier` must already be fit (by
    evaluation/utility.py's training loop, either TRTR or TSTR) --
    this module does not fit anything itself, it only measures fairness
    properties of predictions already produced elsewhere."""
    y_pred = classifier.predict(X_test)
    y_proba = None
    if hasattr(classifier, "predict_proba"):
        y_proba = classifier.predict_proba(X_test)[:, 1]

    subgroup_df = subgroup_performance_report(y_test, y_pred, y_proba, sensitive_values)
    dp_diff = demographic_parity_difference(y_pred, sensitive_values)
    eo = equalized_odds_difference(y_test, y_pred, sensitive_values)

    f1_col = subgroup_df["f1"].dropna()
    auroc_col = subgroup_df["auroc"].dropna()

    return {
        "subgroup_performance": subgroup_df,
        "demographic_parity_difference": dp_diff,
        "equalized_odds": eo,
        "f1_performance_gap": float(f1_col.max() - f1_col.min()) if len(f1_col) >= 2 else None,
        "auroc_performance_gap": float(auroc_col.max() - auroc_col.min()) if len(auroc_col) >= 2 else None,
    }


def is_fairness_applicable(df: pd.DataFrame, sensitive_column: Optional[str], min_group_size: int = 20) -> bool:
    """Gate function: fairness analysis should be SKIPPED (not forced)
    when there is no sensitive column, or when it exists but doesn't
    have at least 2 groups with a reasonable sample size to support a
    non-degenerate comparison (Section 13 of the project spec)."""
    if not sensitive_column or sensitive_column not in df.columns:
        return False
    counts = df[sensitive_column].astype(str).value_counts()
    return int((counts >= min_group_size).sum()) >= 2
