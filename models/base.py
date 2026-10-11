"""
models/base.py

Common interface every synthesizer wraps itself in, so that
experiments/runner.py can treat AIM, MST, PrivBayes, CTGAN, and TVAE
polymorphically without special-casing each one.

Design notes:
  - `is_differentially_private` and `privacy_params()` exist specifically
    so the Streamlit UI and results table can label every method
    correctly and automatically (Rule 7: never claim non-DP data is
    private). This is enforced structurally, not just by convention:
    non-DP subclasses hardcode `is_differentially_private = False` and
    `privacy_params()` returns an explanatory dict rather than a
    fabricated epsilon.
  - `fit()` takes only a training DataFrame plus column-role metadata --
    it must never see the test split (Rule 6).
  - `generate(n)` is deterministic given the synthesizer's internal
    random seed, so repeated experiment runs with the same seed are
    reproducible (Rule: reproducibility).
  - Every concrete subclass records its own `runtime_seconds` for
    fit+generate, since computational cost is one of the axes we are
    explicitly comparing.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class ColumnSpec:
    """What a synthesizer needs to know about the columns it will see.
    Built once from preprocessing.schema/pipeline output and passed
    identically to every model so no synthesizer gets a preprocessing
    advantage over another (see preprocessing/pipeline.py docstring)."""
    numerical_columns: list
    categorical_columns: list
    target_column: Optional[str] = None


@dataclass
class GenerationResult:
    """What every synthesizer hands back to the experiment runner."""
    synthetic_df: pd.DataFrame
    fit_runtime_seconds: float
    generate_runtime_seconds: float
    method_name: str
    is_differentially_private: bool
    privacy_params: dict = field(default_factory=dict)
    extra_metadata: dict = field(default_factory=dict)


class BaseSynthesizer(ABC):
    """Abstract base class every model wrapper (AIM/MST/PrivBayes/CTGAN/
    TVAE) must implement. See module docstring for the contract."""

    method_name: str = "base"
    is_differentially_private: bool = False

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self._fit_runtime_seconds: Optional[float] = None
        self._is_fitted = False

    # ------------------------------------------------------------------
    @abstractmethod
    def _fit_impl(self, train_df: pd.DataFrame, column_spec: ColumnSpec) -> None:
        """Subclasses implement the actual model-fitting call here.
        Must only look at train_df -- never the held-out test split."""
        raise NotImplementedError

    @abstractmethod
    def _generate_impl(self, n: int) -> pd.DataFrame:
        """Subclasses implement the actual sampling call here. Must
        return a DataFrame with exactly the columns in `column_spec`."""
        raise NotImplementedError

    def privacy_params(self) -> dict:
        """Overridden by DP subclasses to report {epsilon, delta}.
        Non-DP subclasses must NOT override this to fabricate a
        guarantee (Rule 7) -- the base implementation makes that
        explicit rather than silently returning {}."""
        return {"note": "This method provides no formal differential privacy guarantee."}

    # ------------------------------------------------------------------
    def fit(self, train_df: pd.DataFrame, column_spec: ColumnSpec) -> "BaseSynthesizer":
        start = time.perf_counter()
        self._fit_impl(train_df, column_spec)
        self._fit_runtime_seconds = time.perf_counter() - start
        self._is_fitted = True
        self._column_spec = column_spec
        return self

    def generate(self, n: int) -> GenerationResult:
        if not self._is_fitted:
            raise RuntimeError(f"{self.method_name}: call fit() before generate().")
        start = time.perf_counter()
        synthetic_df = self._generate_impl(n)
        generate_runtime = time.perf_counter() - start

        return GenerationResult(
            synthetic_df=synthetic_df,
            fit_runtime_seconds=self._fit_runtime_seconds,
            generate_runtime_seconds=generate_runtime,
            method_name=self.method_name,
            is_differentially_private=self.is_differentially_private,
            privacy_params=self.privacy_params(),
        )
