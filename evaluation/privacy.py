"""
evaluation/privacy.py

Privacy evaluation, split cleanly into two categories that must never
be conflated (per the project spec and Rule 7):

  1. FORMAL privacy guarantees -- just reporting (epsilon, delta) and
     the mechanism name for DP methods (see `format_formal_privacy`).
     For non-DP methods this explicitly states there is no guarantee.

  2. EMPIRICAL privacy-risk measurements -- a membership inference
     attack (MIA) and a nearest-neighbor record-similarity check. These
     are indirect, imperfect proxies for real-world risk, not proof of
     anything formal; they let us compare relative leakage across
     methods on the same dataset under the same attack, which is the
     most defensible thing an empirical measurement can offer here.

Membership inference attack design (deliberately simple, not a
reimplementation of a complex research algorithm -- Rule 1 favors
mature libraries for complex algorithms like AIM/MST, but a shadow-
model-free distance-based MIA is a standard, well-documented technique
simple enough to implement directly and audit line-by-line):

  For each candidate real record we know the ground truth of "was this
  record used to fit the generator" (member = the training split) or
  not (non-member = the held-out test split, which the generator never
  saw). We compute each candidate's minimum distance to the released
  synthetic dataset. The attack's decision rule is "closer to synthetic
  data => more likely a member" (Hilprecht et al., 2019-style Monte
  Carlo / distance attack). We report the resulting AUC and TPR at a
  fixed low FPR, which is the standard modern privacy-attack reporting
  convention (low-FPR TPR matters more than AUC alone, since it reflects
  how many members an attacker can identify with high confidence).
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


def format_formal_privacy(is_dp: bool, privacy_params: dict) -> dict:
    """Turn a synthesizer's raw privacy_params() into a display-ready,
    unambiguous statement. Never say "the data is private" -- state the
    exact guarantee or the exact absence of one."""
    if not is_dp:
        return {
            "formal_guarantee": "None",
            "statement": (
                "This method provides NO formal differential privacy guarantee. "
                "Any apparent anonymization is incidental and has been shown in "
                "the literature to not prevent membership-inference or "
                "re-identification attacks."
            ),
        }
    eps = privacy_params.get("epsilon")
    delta = privacy_params.get("delta")
    mechanism = privacy_params.get("mechanism", "unknown DP mechanism")
    if delta and delta > 0:
        statement = f"({eps}, {delta})-differential privacy via {mechanism}."
    else:
        statement = f"{eps}-differential privacy (pure DP, delta=0) via {mechanism}."
    return {"formal_guarantee": statement, "epsilon": eps, "delta": delta, "mechanism": mechanism}


def _encode_for_distance(
    df: pd.DataFrame, numerical_columns: list, categorical_columns: list,
    categorical_vocab: dict, scaler: StandardScaler, fit_scaler: bool = False,
) -> np.ndarray:
    """Shared numeric encoding for distance-based computations (MIA and
    record similarity): standardized numerical features + one-hot
    categorical features against a fixed vocabulary, exactly as in
    evaluation/utility.py, so this module doesn't silently diverge from
    how "distance" is defined for the ML utility evaluation."""
    num_part = df[numerical_columns].apply(pd.to_numeric, errors="coerce").fillna(0.0).values
    num_part = scaler.fit_transform(num_part) if fit_scaler else scaler.transform(num_part)

    cat_parts = []
    for col in categorical_columns:
        vocab = categorical_vocab[col]
        series = df[col].astype(str)
        one_hot = pd.get_dummies(pd.Categorical(series, categories=vocab))
        cat_parts.append(one_hot.values.astype(float))

    if cat_parts:
        return np.concatenate([num_part] + cat_parts, axis=1)
    return num_part


def membership_inference_attack(
    train_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    numerical_columns: list,
    categorical_columns: list,
    categorical_vocab: dict,
    n_neighbors: int = 1,
    fixed_fpr: float = 0.1,
    random_seed: int = 42,
) -> dict:
    """Distance-based MIA (see module docstring). `train_df` = members
    (used to fit the generator), `holdout_df` = non-members (the real
    test split, never seen by the generator). Returns attack AUC and
    TPR at `fixed_fpr`. Balances the two candidate sets by subsampling
    the larger one, so the attack's baseline is a fair 50/50 prior
    rather than reflecting an arbitrary train/test size ratio."""
    rng = np.random.default_rng(random_seed)

    n = min(len(train_df), len(holdout_df))
    if n < 5:
        return {"attack_auc": None, "tpr_at_fixed_fpr": None, "note": "Insufficient data for a reliable MIA."}

    members = train_df.sample(n=n, random_state=random_seed).reset_index(drop=True)
    non_members = holdout_df.sample(n=n, random_state=random_seed).reset_index(drop=True)
    candidates = pd.concat([members, non_members], ignore_index=True)
    labels = np.array([1] * n + [0] * n)  # 1 = member (in training data)

    scaler = StandardScaler()
    synth_encoded = _encode_for_distance(
        synthetic_df, numerical_columns, categorical_columns, categorical_vocab, scaler, fit_scaler=True
    )
    cand_encoded = _encode_for_distance(
        candidates, numerical_columns, categorical_columns, categorical_vocab, scaler, fit_scaler=False
    )

    nn = NearestNeighbors(n_neighbors=n_neighbors)
    nn.fit(synth_encoded)
    distances, _ = nn.kneighbors(cand_encoded)
    min_distances = distances.mean(axis=1)  # mean over the k nearest synthetic points

    # Attack score: closer to synthetic data => higher membership score.
    # Negate distance so higher score = more likely member, as
    # roc_auc_score expects.
    attack_scores = -min_distances

    try:
        auc = float(roc_auc_score(labels, attack_scores))
    except ValueError:
        return {"attack_auc": None, "tpr_at_fixed_fpr": None, "note": "Degenerate attack scores."}

    tpr = _tpr_at_fpr(labels, attack_scores, fixed_fpr)

    return {
        "attack_auc": auc,
        "tpr_at_fixed_fpr": tpr,
        "fixed_fpr": fixed_fpr,
        "n_members_tested": n,
        "n_non_members_tested": n,
        "interpretation": (
            "AUC=0.5 means the attack is no better than random guessing (best case for privacy); "
            "AUC=1.0 means perfect membership discrimination (worst case for privacy)."
        ),
    }


def _tpr_at_fpr(labels: np.ndarray, scores: np.ndarray, target_fpr: float) -> float:
    """True positive rate at a fixed, low false-positive-rate operating
    point -- the standard modern way to report attack strength, since it
    reflects how many members an attacker can confidently identify
    without too many false accusations, which AUC alone can obscure."""
    order = np.argsort(-scores)
    sorted_labels = labels[order]
    n_pos = labels.sum()
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")

    tp = fp = 0
    for lab in sorted_labels:
        if lab == 1:
            tp += 1
        else:
            fp += 1
        if fp / n_neg >= target_fpr:
            break
    return float(tp / n_pos)


def record_similarity_report(
    real_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    numerical_columns: list,
    categorical_columns: list,
    categorical_vocab: dict,
    near_duplicate_percentile: float = 1.0,
) -> dict:
    """Nearest-neighbor distance from each synthetic record to its
    closest REAL TRAINING record. A cluster of near-zero distances
    signals possible memorization / near-duplication (the model copying
    training rows rather than generalizing) -- reported as the fraction
    of synthetic records falling in the bottom `near_duplicate_percentile`
    of the observed real-to-real nearest-neighbor distance distribution,
    which gives a data-driven, non-arbitrary threshold for "suspiciously
    close" rather than a hand-picked constant."""
    scaler = StandardScaler()
    real_encoded = _encode_for_distance(
        real_df, numerical_columns, categorical_columns, categorical_vocab, scaler, fit_scaler=True
    )
    synth_encoded = _encode_for_distance(
        synthetic_df, numerical_columns, categorical_columns, categorical_vocab, scaler, fit_scaler=False
    )

    # Baseline: real-to-real nearest-neighbor distance distribution
    # (excluding self-matches), used to calibrate what "close" means for
    # this dataset's own natural record density.
    nn_real = NearestNeighbors(n_neighbors=2)
    nn_real.fit(real_encoded)
    real_distances, _ = nn_real.kneighbors(real_encoded)
    real_nn_distances = real_distances[:, 1]  # skip the 0-distance self-match
    threshold = np.percentile(real_nn_distances, near_duplicate_percentile)

    nn_synth = NearestNeighbors(n_neighbors=1)
    nn_synth.fit(real_encoded)
    synth_to_real_distances, _ = nn_synth.kneighbors(synth_encoded)
    synth_to_real_distances = synth_to_real_distances[:, 0]

    pct_near_duplicate = float(100 * np.mean(synth_to_real_distances <= threshold))

    return {
        "mean_distance_to_nearest_real": float(np.mean(synth_to_real_distances)),
        "median_distance_to_nearest_real": float(np.median(synth_to_real_distances)),
        "near_duplicate_threshold": float(threshold),
        "pct_synthetic_near_duplicate": pct_near_duplicate,
        "note": (
            f"Threshold = {near_duplicate_percentile}th percentile of the real "
            "data's own nearest-neighbor distances (a data-driven notion of "
            "'unusually close', not an arbitrary constant)."
        ),
    }
