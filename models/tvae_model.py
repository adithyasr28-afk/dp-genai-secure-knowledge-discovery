"""
models/tvae_model.py

Wrapper around the canonical TVAE implementation (Xu et al., 2019,
NeurIPS -- same paper as CTGAN), from the `ctgan` package, which ships
both models. NON-DP reference method (Rule 7), same role as CTGAN: a
fidelity ceiling to contrast against the DP methods, never presented as
privacy-preserving. Operates on the continuous representation, same as
CTGANModel -- see models/ctgan_model.py docstring for the rationale.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from models.base import BaseSynthesizer, ColumnSpec


class TVAEModel(BaseSynthesizer):
    method_name = "TVAE"
    is_differentially_private = False

    def __init__(
        self,
        epochs: int = 300,
        random_seed: int = 42,
        verbose: bool = False,
        batch_size: int = 500,
    ):
        super().__init__(random_seed=random_seed)
        self.epochs = epochs
        self.verbose = verbose
        self.batch_size = batch_size
        self._synth = None
        self._columns: Optional[list] = None

    def _fit_impl(self, train_df: pd.DataFrame, column_spec: ColumnSpec) -> None:
        from ctgan import TVAE

        self._columns = list(train_df.columns)
        discrete_columns = [c for c in self._columns if c not in column_spec.numerical_columns]

        self._synth = TVAE(
            epochs=self.epochs,
            batch_size=self.batch_size,
            enable_gpu=True,
        )
        self._synth.set_random_state(self.random_seed)
        self._synth.fit(train_df, discrete_columns=discrete_columns)

    def _generate_impl(self, n: int) -> pd.DataFrame:
        synthetic = self._synth.sample(n)
        return synthetic[self._columns].reset_index(drop=True)
