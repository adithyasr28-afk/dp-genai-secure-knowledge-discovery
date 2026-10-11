"""
preprocessing/schema.py

Dataset profiling and column-type inference.

This module answers: "what does this CSV look like?" It never fits any
transformation and never touches a train/test split -- it is pure,
read-only profiling of whatever DataFrame it is given. Callers are
responsible for only ever passing the *training* split into anything
that later fits a transform (see preprocessing/pipeline.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

# A column with more unique values than this (relative to n_rows) is flagged
# as "high cardinality" -- a signal that it may need special handling
# (grouping rare categories, or excluding it) before DP methods can use it.
HIGH_CARDINALITY_ABS_THRESHOLD = 50
HIGH_CARDINALITY_REL_THRESHOLD = 0.05  # >5% unique values relative to n_rows

# A binary/multi-class column is flagged as "imbalanced" if the minority
# class falls below this fraction of the total.
IMBALANCE_THRESHOLD = 0.2


@dataclass
class ColumnProfile:
    name: str
    inferred_type: str          # "numerical" | "categorical" | "boolean" | "datetime" | "id_like"
    dtype: str                  # original pandas dtype, as string
    n_missing: int
    pct_missing: float
    n_unique: int
    is_high_cardinality: bool
    sample_values: list = field(default_factory=list)
    # numerical-only
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    # categorical-only
    top_categories: Optional[dict] = None      # {category: count}, top 10
    rare_category_count: Optional[int] = None  # categories with < 1% share


@dataclass
class DatasetProfile:
    n_rows: int
    n_columns: int
    columns: list  # list[ColumnProfile]
    duplicate_row_count: int
    suggested_target_columns: list
    suggested_sensitive_columns: list

    def to_summary_dict(self) -> dict:
        """A flat, JSON-serializable summary suitable for the Streamlit UI
        or for logging alongside experiment results."""
        return {
            "n_rows": self.n_rows,
            "n_columns": self.n_columns,
            "duplicate_row_count": self.duplicate_row_count,
            "n_numerical": sum(1 for c in self.columns if c.inferred_type == "numerical"),
            "n_categorical": sum(1 for c in self.columns if c.inferred_type == "categorical"),
            "n_high_cardinality": sum(1 for c in self.columns if c.is_high_cardinality),
            "n_columns_with_missing": sum(1 for c in self.columns if c.n_missing > 0),
            "suggested_target_columns": self.suggested_target_columns,
            "suggested_sensitive_columns": self.suggested_sensitive_columns,
        }


def _infer_column_type(series: pd.Series, n_rows: int) -> str:
    """Heuristic column-type inference. Deliberately simple and
    explainable -- this drives downstream DP-binning and encoding
    decisions, so a surprising misclassification should be easy for a
    user to spot and override in the UI, not buried in a black box."""
    non_null = series.dropna()
    if non_null.empty:
        return "categorical"  # can't tell; default safe choice

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    n_unique = non_null.nunique()

    # ID-like: (almost) every row has a unique value -- not useful for
    # generation, should be excluded by default.
    if n_unique >= 0.95 * n_rows and n_rows > 20:
        return "id_like"

    if pd.api.types.is_numeric_dtype(series):
        # A numeric column with very few distinct values (e.g. 0/1/2 codes)
        # is more usefully treated as categorical.
        if n_unique <= 10:
            return "categorical"
        return "numerical"

    # Everything else (strings, objects) is categorical.
    return "categorical"


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    """Profile a raw DataFrame. Read-only: does not mutate df and fits
    nothing. Safe to call on the full dataset before any train/test split
    purely for display purposes in the UI; must NOT be used to decide
    fitted-transform parameters used later in the pipeline (use the
    training split for that -- see pipeline.py)."""
    n_rows = len(df)
    n_columns = len(df.columns)
    duplicate_row_count = int(df.duplicated().sum())

    columns: list[ColumnProfile] = []
    suggested_targets: list[str] = []
    suggested_sensitive: list[str] = []

    # Common naming patterns used to *suggest* (never force) a target or
    # sensitive attribute -- the user always makes the final choice in the UI.
    target_name_hints = ("target", "label", "class", "outcome", "income", "y")
    sensitive_name_hints = ("sex", "gender", "race", "ethnicity", "age", "disability", "religion")

    for col in df.columns:
        series = df[col]
        n_missing = int(series.isna().sum())
        pct_missing = round(100 * n_missing / n_rows, 2) if n_rows else 0.0
        n_unique = int(series.nunique(dropna=True))
        inferred_type = _infer_column_type(series, n_rows)

        is_high_card = (
            inferred_type == "categorical"
            and n_unique > HIGH_CARDINALITY_ABS_THRESHOLD
            and (n_unique / max(n_rows, 1)) > HIGH_CARDINALITY_REL_THRESHOLD
        )

        profile_kwargs = dict(
            name=col,
            inferred_type=inferred_type,
            dtype=str(series.dtype),
            n_missing=n_missing,
            pct_missing=pct_missing,
            n_unique=n_unique,
            is_high_cardinality=is_high_card,
            sample_values=series.dropna().unique()[:5].tolist(),
        )

        if inferred_type == "numerical":
            non_null = series.dropna()
            profile_kwargs.update(
                min_value=float(non_null.min()) if len(non_null) else None,
                max_value=float(non_null.max()) if len(non_null) else None,
                mean_value=float(non_null.mean()) if len(non_null) else None,
                std_value=float(non_null.std()) if len(non_null) else None,
            )
        elif inferred_type == "categorical":
            counts = series.value_counts(dropna=True)
            top = counts.head(10).to_dict()
            rare = int((counts / n_rows < 0.01).sum()) if n_rows else 0
            profile_kwargs.update(top_categories=top, rare_category_count=rare)

        # Match hints against whole tokens (split on non-alphanumeric)
        # rather than raw substrings, so e.g. "workclass" does not
        # spuriously match the "class" hint.
        col_tokens = set(re.split(r"[^a-z0-9]+", col.lower()))
        if inferred_type == "categorical" and 2 <= n_unique <= 20 and col_tokens & set(target_name_hints):
            suggested_targets.append(col)
        # For sensitive-attribute suggestion: a raw continuous numerical
        # column (e.g. "age" with dozens of distinct values) makes a poor
        # AUTO-SUGGESTED default, since the Fairness module groups by
        # exact value -- grouping by every individual age produces many
        # degenerate, near-single-row "subgroups" and meaningless metrics.
        # Such a column remains manually selectable in the UI; we simply
        # don't want it silently chosen as the default ahead of an
        # actually-categorical demographic column like "sex" or "race"
        # purely because it appears earlier in the dataframe.
        is_suggestible_sensitive = col_tokens & set(sensitive_name_hints) and not (
            inferred_type == "numerical" and n_unique > 15
        )
        if is_suggestible_sensitive:
            suggested_sensitive.append(col)

        columns.append(ColumnProfile(**profile_kwargs))

    # Fallback: if no name-based target hint matched, suggest the lowest-
    # cardinality categorical column (2-10 classes) as a plausible target,
    # since classification is the most common downstream-utility task.
    if not suggested_targets:
        categorical_cols = [c for c in columns if c.inferred_type == "categorical"]
        low_card = [c for c in categorical_cols if 2 <= c.n_unique <= 10]
        if low_card:
            low_card.sort(key=lambda c: c.n_unique)
            suggested_targets.append(low_card[0].name)

    return DatasetProfile(
        n_rows=n_rows,
        n_columns=n_columns,
        columns=columns,
        duplicate_row_count=duplicate_row_count,
        suggested_target_columns=suggested_targets,
        suggested_sensitive_columns=suggested_sensitive,
    )


def class_imbalance_report(df: pd.DataFrame, target_column: str) -> dict:
    """Report the class balance of a chosen target column. Used both in
    the Dataset overview page and later to interpret rare-pattern /
    fairness results (a class already imbalanced in the real data needs
    that baseline reported alongside the synthetic-data comparison)."""
    if target_column not in df.columns:
        raise KeyError(f"Target column '{target_column}' not found in dataframe.")

    counts = df[target_column].value_counts(dropna=False)
    proportions = (counts / len(df)).round(4)
    minority_share = float(proportions.min()) if len(proportions) else None

    return {
        "target_column": target_column,
        "class_counts": counts.to_dict(),
        "class_proportions": proportions.to_dict(),
        "n_classes": int(len(counts)),
        "minority_class_share": minority_share,
        "is_imbalanced": (minority_share is not None and minority_share < IMBALANCE_THRESHOLD),
    }
