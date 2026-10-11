"""
preprocessing/pipeline.py

The single shared preprocessing protocol used by every synthesizer in
this project. This module is the most important one for the fairness of
the comparison: the SIGMOD 2025 DP-synthesis benchmark (Chen, Li, Gong,
McKenna & Wang) found that preprocessing choices materially change
reported results between papers, so we fix ONE protocol and apply it
identically to every method.

Golden rule (Rule 6 / no leakage):
    Every fitted parameter (imputation values, bin edges, rare-category
    groupings, category vocabularies) is learned from `fit(train_df)`
    ONLY. The test split is only ever passed through `transform_real()`
    for evaluation -- it never touches `fit`.

Design choices, made explicit rather than implicit:
  - Missing values: categorical -> a new explicit "__MISSING__" category
    (never imputed by mode, which would fabricate information and bias
    fidelity metrics that compare "real" to "synthetic" distributions of
    that column). Numerical -> median imputation with a companion
    "<col>__was_missing" indicator column, a standard, auditable choice.
  - Rare categories: categories with a training-set frequency below
    `rare_category_threshold` are grouped into a single "__RARE__" level
    BEFORE any generator is fit, for two reasons: (1) DP marginal-based
    methods (MST/AIM/PrivBayes) treat every distinct category as a
    dimension of the query workload, so ungrouped rare categories burn
    privacy budget on noise-dominated cells; (2) it keeps the comparison
    fair, since the same grouping is applied identically to GAN/VAE
    training data too.
  - High-cardinality categorical columns are flagged and, by default,
    excluded from generation (the user can override this in the UI),
    since none of the five methods handle e.g. free-text or ID-like
    columns well, and including them would silently penalize whichever
    method handles them worst rather than testing generation quality.
  - Numerical binning: DP graphical methods (MST/AIM/PrivBayes) require
    discretized/categorical input. We compute quantile-based bin edges
    on the TRAINING split only, and expose both the binned representation
    (for DP methods) and the raw continuous representation (for
    CTGAN/TVAE, which natively handle continuous columns). Every model
    receives the representation it needs from the *same* underlying
    fitted bin edges, so bin boundaries are never method-specific.
  - Zero-/spike-inflated numerical columns (e.g. "capital_gain" in the
    bundled example, where >90% of rows are exactly 0): plain quantile
    binning collapses such a column into a single degenerate bin,
    silently deleting all of its information before any generator sees
    it. We detect a dominant point mass (>= `spike_threshold` share of
    training rows at one value) and give it its own dedicated bin, then
    quantile-bin only the remaining, non-spike values into the rest of
    the budget. This is a standard technique for skewed/zero-inflated
    features and is applied identically for every method.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

MISSING_CATEGORY_TOKEN = "__MISSING__"
RARE_CATEGORY_TOKEN = "__RARE__"
DEFAULT_RARE_THRESHOLD = 0.01     # categories under 1% of training rows are grouped
DEFAULT_N_BINS = 10               # quantile bins for DP-method discretization
DEFAULT_SPIKE_THRESHOLD = 0.30    # a single value covering >=30% of rows gets its own bin
SPIKE_BIN_LABEL = "bin_spike"


@dataclass
class ColumnConfig:
    """User-confirmed / auto-detected configuration for one column,
    produced by the Streamlit 'Preprocessing' page before fitting."""
    name: str
    role: str            # "feature" | "target" | "sensitive" | "excluded"
    dtype: str            # "numerical" | "categorical"
    include: bool = True


@dataclass
class FittedPreprocessor:
    """Everything learned from the training split. Serializable to JSON
    for reproducibility / experiment logging (Rule: reproducible runs)."""
    numerical_columns: list
    categorical_columns: list
    excluded_columns: list
    target_column: Optional[str]
    sensitive_column: Optional[str]

    numerical_medians: dict = field(default_factory=dict)
    numerical_bin_edges: dict = field(default_factory=dict)  # col -> list[float] (edges for the *non-spike* remainder)
    numerical_spike_value: dict = field(default_factory=dict)  # col -> float | None
    categorical_vocab: dict = field(default_factory=dict)    # col -> list[str] (post rare-grouping)
    rare_threshold: float = DEFAULT_RARE_THRESHOLD
    n_bins: int = DEFAULT_N_BINS
    spike_threshold: float = DEFAULT_SPIKE_THRESHOLD
    random_seed: int = 42

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2, default=str)

    @classmethod
    def from_json(cls, s: str) -> "FittedPreprocessor":
        return cls(**json.loads(s))


class Preprocessor:
    """Fit on the training split; apply consistently to train/test/synthetic
    data. See module docstring for the exact leakage-avoidance contract."""

    def __init__(
        self,
        rare_threshold: float = DEFAULT_RARE_THRESHOLD,
        n_bins: int = DEFAULT_N_BINS,
        spike_threshold: float = DEFAULT_SPIKE_THRESHOLD,
        random_seed: int = 42,
    ):
        self.rare_threshold = rare_threshold
        self.n_bins = n_bins
        self.spike_threshold = spike_threshold
        self.random_seed = random_seed
        self.fitted_: Optional[FittedPreprocessor] = None

    # ------------------------------------------------------------------
    def fit(
        self,
        train_df: pd.DataFrame,
        numerical_columns: list,
        categorical_columns: list,
        excluded_columns: Optional[list] = None,
        target_column: Optional[str] = None,
        sensitive_column: Optional[str] = None,
    ) -> "Preprocessor":
        """Learn all imputation values, bin edges, and category
        vocabularies from `train_df` ONLY. Never call this with test data."""
        excluded_columns = excluded_columns or []

        medians = {}
        bin_edges = {}
        spike_values = {}
        for col in numerical_columns:
            series = pd.to_numeric(train_df[col], errors="coerce")
            medians[col] = float(series.median())
            filled = series.fillna(medians[col])

            # Detect a dominant point mass (e.g. "capital_gain" is 0 for
            # >90% of rows). If one value covers >= spike_threshold of the
            # training rows, quantile-binning the *whole* column would
            # produce a single degenerate bin containing everything,
            # silently deleting the column's information. Instead: give
            # the spike value its own dedicated bin (bin_spike) and
            # quantile-bin only the remaining, non-spike values.
            value_counts = filled.value_counts(normalize=True)
            top_value, top_share = value_counts.index[0], value_counts.iloc[0]

            if top_share >= self.spike_threshold and len(value_counts) > 1:
                spike_values[col] = float(top_value)
                remainder = filled[filled != top_value]
                if remainder.nunique() > 1:
                    try:
                        _, edges = pd.qcut(
                            remainder, q=self.n_bins, retbins=True, duplicates="drop"
                        )
                        bin_edges[col] = [float(e) for e in edges]
                    except ValueError:
                        bin_edges[col] = [float(remainder.min()), float(remainder.max()) + 1e-9]
                else:
                    # Remainder is itself constant (or empty) -- one bin covers it.
                    lo = float(remainder.min()) if len(remainder) else float(top_value)
                    hi = float(remainder.max()) if len(remainder) else float(top_value)
                    bin_edges[col] = [lo, hi + 1e-9]
            else:
                spike_values[col] = None
                # Quantile bin edges for the DP-method discretized view.
                try:
                    _, edges = pd.qcut(filled, q=self.n_bins, retbins=True, duplicates="drop")
                    bin_edges[col] = [float(e) for e in edges]
                except ValueError:
                    # Degenerate column (near-constant): fall back to a single bin.
                    bin_edges[col] = [float(filled.min()), float(filled.max()) + 1e-9]

        vocab = {}
        for col in categorical_columns:
            series = train_df[col].astype("object")
            series = series.where(series.notna(), MISSING_CATEGORY_TOKEN)
            counts = series.value_counts(normalize=True)
            keep = set(counts[counts >= self.rare_threshold].index)
            # Every kept category, plus the two synthetic tokens, forms the
            # closed vocabulary every downstream representation must respect.
            categories = sorted(str(c) for c in keep)
            if MISSING_CATEGORY_TOKEN not in categories and MISSING_CATEGORY_TOKEN in series.values:
                categories.append(MISSING_CATEGORY_TOKEN)
            categories.append(RARE_CATEGORY_TOKEN)
            vocab[col] = categories

        self.fitted_ = FittedPreprocessor(
            numerical_columns=list(numerical_columns),
            categorical_columns=list(categorical_columns),
            excluded_columns=list(excluded_columns),
            target_column=target_column,
            sensitive_column=sensitive_column,
            numerical_medians=medians,
            numerical_bin_edges=bin_edges,
            numerical_spike_value=spike_values,
            categorical_vocab=vocab,
            rare_threshold=self.rare_threshold,
            n_bins=self.n_bins,
            spike_threshold=self.spike_threshold,
            random_seed=self.random_seed,
        )
        return self

    # ------------------------------------------------------------------
    def _require_fitted(self):
        if self.fitted_ is None:
            raise RuntimeError("Preprocessor.fit() must be called before transform.")

    def transform_continuous(self, df: pd.DataFrame) -> pd.DataFrame:
        """Representation for continuous-native models (CTGAN/TVAE):
        numerical columns imputed (median from TRAIN) with a
        was-missing indicator; categorical columns cleaned to the
        fitted vocabulary (rare/unseen -> '__RARE__', missing ->
        '__MISSING__'). Safe to call on train, test, or synthetic data."""
        self._require_fitted()
        f = self.fitted_
        out = pd.DataFrame(index=df.index)

        for col in f.numerical_columns:
            series = pd.to_numeric(df[col], errors="coerce")
            was_missing = series.isna().astype(int)
            filled = series.fillna(f.numerical_medians[col])
            out[col] = filled
            if was_missing.sum() > 0:
                out[f"{col}__was_missing"] = was_missing

        for col in f.categorical_columns:
            series = df[col].astype("object")
            series = series.where(series.notna(), MISSING_CATEGORY_TOKEN)
            allowed = set(f.categorical_vocab[col])
            out[col] = series.apply(lambda v: str(v) if str(v) in allowed else RARE_CATEGORY_TOKEN)

        return out

    def transform_discretized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Representation for DP graphical models (MST/AIM/PrivBayes):
        numerical columns binned using the TRAIN-fitted quantile edges
        (out-of-range values from test/synthetic data are clipped into
        the outermost bin rather than dropped); categorical columns as
        in transform_continuous(). All columns end up categorical-typed,
        as required by the marginal/graphical-model synthesizers."""
        self._require_fitted()
        f = self.fitted_
        out = pd.DataFrame(index=df.index)

        for col in f.numerical_columns:
            series = pd.to_numeric(df[col], errors="coerce")
            filled = series.fillna(f.numerical_medians[col])
            edges = np.array(f.numerical_bin_edges[col])
            spike = f.numerical_spike_value.get(col)

            if spike is not None:
                is_spike = filled.values == spike
                clipped = np.clip(filled.values, edges[0], edges[-1] - 1e-9)
                bin_idx = np.digitize(clipped, edges[1:-1], right=False)
                labels = np.where(is_spike, SPIKE_BIN_LABEL, [f"bin_{i}" for i in bin_idx])
                out[col] = labels
            else:
                # np.digitize with clipping handles values outside the
                # train-fitted range instead of producing NaN bins.
                clipped = np.clip(filled.values, edges[0], edges[-1] - 1e-9)
                bin_idx = np.digitize(clipped, edges[1:-1], right=False)
                out[col] = [f"bin_{i}" for i in bin_idx]

        for col in f.categorical_columns:
            series = df[col].astype("object")
            series = series.where(series.notna(), MISSING_CATEGORY_TOKEN)
            allowed = set(f.categorical_vocab[col])
            out[col] = series.apply(lambda v: str(v) if str(v) in allowed else RARE_CATEGORY_TOKEN)

        return out

    def inverse_transform_discretized_numerical(
        self, binned_df: pd.DataFrame, rng: Optional[np.random.Generator] = None
    ) -> pd.DataFrame:
        """Map a discretized synthetic column back to a continuous value
        by sampling uniformly within the bin's edges (train-fitted).
        Needed after DP methods generate binned synthetic data, so that
        fidelity/utility evaluation can be run on a comparable continuous
        representation across all five methods."""
        self._require_fitted()
        f = self.fitted_
        rng = rng or np.random.default_rng(self.random_seed)
        out = binned_df.copy()

        for col in f.numerical_columns:
            edges = np.array(f.numerical_bin_edges[col])
            n_bins = len(edges) - 1
            spike = f.numerical_spike_value.get(col)

            def sample_from_bin(bin_label, edges=edges, n_bins=n_bins, spike=spike):
                label = str(bin_label)
                if spike is not None and label == SPIKE_BIN_LABEL:
                    return spike
                idx = int(label.replace("bin_", ""))
                idx = min(idx, n_bins - 1)
                lo, hi = edges[idx], edges[idx + 1]
                return rng.uniform(lo, hi)

            out[col] = binned_df[col].apply(sample_from_bin)

        return out


def train_test_split_no_leakage(
    df: pd.DataFrame, test_size: float = 0.2, random_seed: int = 42, stratify_column: Optional[str] = None
):
    """Thin, explicit wrapper around sklearn's split so the "no leakage"
    contract is visible at the call site used throughout the codebase."""
    from sklearn.model_selection import train_test_split

    stratify = df[stratify_column] if stratify_column else None
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_seed, stratify=stratify
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)
