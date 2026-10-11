"""
evaluation/utility.py

Downstream ML utility evaluation: Train-on-Synthetic-Test-on-Real (TSTR)
vs. Train-on-Real-Test-on-Real (TRTR), across Logistic Regression,
Random Forest, and XGBoost, per the project spec.

Contract:
  - The REAL TEST SET is only ever used for scoring (`model.predict` /
    `model.predict_proba`), never for fitting anything -- fit_predict()
    below makes this the only entry point that touches labels for
    training, and it always trains on whatever `train_df` it's given
    (real or synthetic), scoring against a separate `test_df` that the
    caller must ensure is the real held-out split (see Rule 6, and
    experiments/runner.py which owns this invariant).
  - Categorical columns are one-hot encoded using a FIXED vocabulary
    (the training data's own value_counts here -- typically the real
    training data's fitted Preprocessor vocabulary, passed in by the
    caller) so real and synthetic feature spaces line up exactly, and a
    synthetic-only category never creates a column the real test set
    can't produce and vice versa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False


MODEL_REGISTRY = {
    "logistic_regression": lambda seed: LogisticRegression(max_iter=1000, random_state=seed),
    "random_forest": lambda seed: RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=-1),
}
if _HAS_XGBOOST:
    MODEL_REGISTRY["xgboost"] = lambda seed: XGBClassifier(
        n_estimators=200, random_state=seed, eval_metric="logloss"
    )


def _encode_features(
    df: pd.DataFrame,
    numerical_columns: list,
    categorical_columns: list,
    categorical_vocab: dict,
    scaler: Optional[StandardScaler] = None,
    fit_scaler: bool = False,
):
    """One-hot encode categorical columns against a FIXED vocabulary
    (not `pd.get_dummies` on this dataframe alone, which would silently
    produce different columns for real vs synthetic data with different
    observed categories). Numerical columns are standardized with a
    scaler fit ONLY on the real training data, then reused everywhere,
    so synthetic-trained and real-trained models see features on the
    same scale."""
    num_part = df[numerical_columns].apply(pd.to_numeric, errors="coerce").fillna(0.0).values
    if scaler is not None:
        num_part = scaler.transform(num_part) if not fit_scaler else scaler.fit_transform(num_part)

    cat_parts = []
    for col in categorical_columns:
        vocab = categorical_vocab[col]
        series = df[col].astype(str)
        one_hot = pd.get_dummies(pd.Categorical(series, categories=vocab))
        cat_parts.append(one_hot.values.astype(float))

    if cat_parts:
        cat_matrix = np.concatenate(cat_parts, axis=1)
        features = np.concatenate([num_part, cat_matrix], axis=1)
    else:
        features = num_part

    return features


@dataclass
class UtilityResult:
    model_name: str
    training_source: str  # "real" (TRTR) or "synthetic" (TSTR)
    accuracy: float
    precision: float
    recall: float
    f1: float
    auroc: Optional[float]
    auprc: Optional[float]


def evaluate_utility(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_column: str,
    numerical_columns: list,
    categorical_columns: list,
    categorical_vocab: dict,
    training_source: str,
    models: Optional[list] = None,
    random_seed: int = 42,
) -> list:
    """Train each requested model on `train_df` (real -> TRTR, synthetic
    -> TSTR) and score on `test_df` (must always be the real held-out
    test split -- see module docstring). `categorical_vocab` must come
    from the fitted Preprocessor so real/synthetic feature encodings
    are guaranteed identical. Returns a list[UtilityResult]."""
    models = models or list(MODEL_REGISTRY.keys())
    feature_categorical = [c for c in categorical_columns if c != target_column]

    scaler = StandardScaler()
    X_train = _encode_features(
        train_df, numerical_columns, feature_categorical, categorical_vocab,
        scaler=scaler, fit_scaler=True,
    )
    X_test = _encode_features(
        test_df, numerical_columns, feature_categorical, categorical_vocab,
        scaler=scaler, fit_scaler=False,
    )

    # Target encoding: binarize using the REAL test set's label ordering
    # so "positive class" means the same thing whichever data trained
    # the model.
    target_classes = sorted(test_df[target_column].astype(str).unique())
    if len(target_classes) != 2:
        raise ValueError(
            f"evaluate_utility currently supports binary targets only; "
            f"found {len(target_classes)} classes in '{target_column}': {target_classes}"
        )
    positive_class = target_classes[-1]  # deterministic: alphabetically-last class is "positive"

    y_train = (train_df[target_column].astype(str) == positive_class).astype(int).values
    y_test = (test_df[target_column].astype(str) == positive_class).astype(int).values

    results = []
    for model_name in models:
        if model_name not in MODEL_REGISTRY:
            continue
        clf = MODEL_REGISTRY[model_name](random_seed)

        if len(np.unique(y_train)) < 2:
            # Degenerate synthetic training set (e.g. a very small/very
            # private run collapsed to a single class) -- report this
            # explicitly as a failure mode rather than crashing silently.
            results.append(UtilityResult(
                model_name=model_name, training_source=training_source,
                accuracy=np.nan, precision=np.nan, recall=np.nan, f1=np.nan,
                auroc=np.nan, auprc=np.nan,
            ))
            continue

        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        auroc = auprc = None
        if hasattr(clf, "predict_proba"):
            y_proba = clf.predict_proba(X_test)[:, 1]
            try:
                auroc = float(roc_auc_score(y_test, y_proba))
                auprc = float(average_precision_score(y_test, y_proba))
            except ValueError:
                pass  # e.g. only one class present in y_test (shouldn't happen with a fixed real test set)

        results.append(UtilityResult(
            model_name=model_name,
            training_source=training_source,
            accuracy=float(accuracy_score(y_test, y_pred)),
            precision=float(precision_score(y_test, y_pred, zero_division=0)),
            recall=float(recall_score(y_test, y_pred, zero_division=0)),
            f1=float(f1_score(y_test, y_pred, zero_division=0)),
            auroc=auroc,
            auprc=auprc,
        ))

    return results


def utility_results_to_dataframe(results: list) -> pd.DataFrame:
    return pd.DataFrame([r.__dict__ for r in results])


def compute_utility_retention(tstr_df: pd.DataFrame, trtr_df: pd.DataFrame, metric: str = "f1") -> pd.DataFrame:
    """For each model, report % of the TRTR (real-data ceiling) metric
    value retained by TSTR (synthetic-trained). >100% is possible and
    should be reported honestly (can happen with class-imbalance
    interactions or small test sets), not clipped."""
    merged = tstr_df.merge(trtr_df, on="model_name", suffixes=("_tstr", "_trtr"))
    merged["utility_retention_pct"] = np.where(
        merged[f"{metric}_trtr"] > 0,
        100 * merged[f"{metric}_tstr"] / merged[f"{metric}_trtr"],
        np.nan,
    )
    return merged[["model_name", f"{metric}_trtr", f"{metric}_tstr", "utility_retention_pct"]]
