"""
evaluation/rare_patterns.py

Investigates whether synthetic generation loses rare patterns --
minority classes, rare categories, and rare attribute COMBINATIONS.
This matters most at low epsilon (DP methods) and is exactly the kind
of failure a marginal-fidelity-only evaluation can miss: a method can
nail every 1-way distribution while still systematically erasing rare
multi-attribute subgroups (e.g. a small demographic intersection),
which is precisely the risk this module is built to surface.
"""

from __future__ import annotations

import itertools
from typing import Optional

import numpy as np
import pandas as pd

RARE_CATEGORY_SHARE = 0.01     # categories under 1% of real rows are "rare"
RARE_COMBINATION_SHARE = 0.005  # attribute combinations under 0.5% of real rows are "rare"


def minority_class_report(real_df: pd.DataFrame, synthetic_df: pd.DataFrame, target_column: str) -> pd.DataFrame:
    """Compare class proportions of `target_column` between real and
    synthetic data. A DP method with too small an epsilon can distort
    minority-class share substantially (noise dominates a small true
    count), which directly threatens downstream classifier utility for
    that class -- this is the single most important rare-pattern check
    for any classification-oriented project."""
    real_props = real_df[target_column].astype(str).value_counts(normalize=True)
    synth_props = synthetic_df[target_column].astype(str).value_counts(normalize=True)

    classes = sorted(set(real_props.index) | set(synth_props.index))
    rows = []
    for c in classes:
        r = real_props.get(c, 0.0)
        s = synth_props.get(c, 0.0)
        rows.append({
            "class": c,
            "real_proportion": r,
            "synthetic_proportion": s,
            "absolute_difference": abs(r - s),
            "relative_change_pct": (100 * (s - r) / r) if r > 0 else np.nan,
        })
    return pd.DataFrame(rows).sort_values("real_proportion")


def rare_category_report(
    real_df: pd.DataFrame, synthetic_df: pd.DataFrame, categorical_columns: list,
    rare_share: float = RARE_CATEGORY_SHARE,
) -> pd.DataFrame:
    """For each categorical column, find categories that were RARE in
    the real training data (below `rare_share`) and report how well
    each one's frequency is preserved in the synthetic data -- including
    categories that disappear entirely (synthetic_proportion = 0), which
    is the sharpest, most interpretable form of rare-pattern loss."""
    rows = []
    for col in categorical_columns:
        real_props = real_df[col].astype(str).value_counts(normalize=True)
        synth_props = synthetic_df[col].astype(str).value_counts(normalize=True)
        rare_categories = real_props[real_props < rare_share].index

        for cat in rare_categories:
            r = real_props.get(cat, 0.0)
            s = synth_props.get(cat, 0.0)
            rows.append({
                "column": col,
                "category": cat,
                "real_proportion": r,
                "synthetic_proportion": s,
                "disappeared_in_synthetic": bool(s == 0.0),
                "relative_change_pct": (100 * (s - r) / r) if r > 0 else np.nan,
            })
    return pd.DataFrame(rows).sort_values("real_proportion") if rows else pd.DataFrame(
        columns=["column", "category", "real_proportion", "synthetic_proportion",
                 "disappeared_in_synthetic", "relative_change_pct"]
    )


def rare_combination_report(
    real_df: pd.DataFrame,
    synthetic_df: pd.DataFrame,
    columns: list,
    combo_size: int = 2,
    rare_share: float = RARE_COMBINATION_SHARE,
    max_combinations_checked: int = 200,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Rare COMBINATIONS of attributes (e.g. a specific
    occupation x sex x income intersection that's uncommon in the real
    data) are a stronger test of rare-pattern preservation than single-
    column rarity, since a method can preserve every individual
    category's marginal frequency while still failing to reproduce which
    specific combinations of attributes co-occur. We check all
    `combo_size`-way column combinations up to `max_combinations_checked`
    (randomly sampled if there are more), find each combination's rare
    real-data value-tuples, and report their synthetic-data preservation."""
    rng = np.random.default_rng(random_seed)
    all_combos = list(itertools.combinations(columns, combo_size))
    if len(all_combos) > max_combinations_checked:
        idx = rng.choice(len(all_combos), size=max_combinations_checked, replace=False)
        all_combos = [all_combos[i] for i in idx]

    rows = []
    for combo in all_combos:
        combo_cols = list(combo)
        real_joint = real_df[combo_cols].astype(str).value_counts(normalize=True)
        synth_joint = synthetic_df[combo_cols].astype(str).value_counts(normalize=True)

        rare_tuples = real_joint[real_joint < rare_share]
        for tup, r in rare_tuples.items():
            s = synth_joint.get(tup, 0.0)
            rows.append({
                "columns": " + ".join(combo_cols),
                "value_combination": " | ".join(tup) if isinstance(tup, tuple) else str(tup),
                "real_proportion": r,
                "synthetic_proportion": s,
                "disappeared_in_synthetic": bool(s == 0.0),
            })

    if not rows:
        return pd.DataFrame(columns=["columns", "value_combination", "real_proportion",
                                      "synthetic_proportion", "disappeared_in_synthetic"])
    return pd.DataFrame(rows).sort_values("real_proportion")


def summarize_rare_pattern_loss(
    minority_report: pd.DataFrame,
    rare_cat_report: pd.DataFrame,
    rare_combo_report: pd.DataFrame,
) -> dict:
    """Headline numbers for the cross-method comparison: what fraction
    of rare categories/combinations disappeared entirely, and the
    largest single minority-class distortion observed."""
    return {
        "max_minority_class_abs_diff": (
            float(minority_report["absolute_difference"].max()) if len(minority_report) else None
        ),
        "pct_rare_categories_disappeared": (
            float(100 * rare_cat_report["disappeared_in_synthetic"].mean()) if len(rare_cat_report) else None
        ),
        "n_rare_categories_checked": int(len(rare_cat_report)),
        "pct_rare_combinations_disappeared": (
            float(100 * rare_combo_report["disappeared_in_synthetic"].mean()) if len(rare_combo_report) else None
        ),
        "n_rare_combinations_checked": int(len(rare_combo_report)),
    }
