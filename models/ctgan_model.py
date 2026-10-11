"""
models/ctgan_model.py

Wrapper around the canonical CTGAN implementation (Xu et al., 2019,
NeurIPS), from the `ctgan` package (sdv-dev, the original authors' org).
This is a NON-DP reference method (Rule 7): it is included purely to
show the "no formal privacy guarantee" ceiling that AIM/MST/PrivBayes
sacrifice fidelity/utility to move away from -- never presented in the
UI or results as privacy-preserving.

CTGAN operates on the CONTINUOUS representation (Preprocessor.
transform_continuous()), not the discretized one used by the DP
graphical methods -- it natively handles continuous numerical columns
via its own internal mode-specific normalization, so binning them first
would only discard information for no benefit.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from models.base import BaseSynthesizer, ColumnSpec


class CTGANModel(BaseSynthesizer):
    method_name = "CTGAN"
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
        from ctgan import CTGAN

        self._columns = list(train_df.columns)
        # Every column not in numerical_columns (categorical, plus any
        # "<col>__was_missing" indicator columns added by
        # transform_continuous) is treated as discrete by CTGAN.
        discrete_columns = [c for c in self._columns if c not in column_spec.numerical_columns]

        self._synth = CTGAN(
            epochs=self.epochs,
            verbose=self.verbose,
            batch_size=self.batch_size,
            enable_gpu=True,  # falls back to CPU automatically if no GPU is available
        )
        self._synth.set_random_state(self.random_seed)
        self._synth.fit(train_df, discrete_columns=discrete_columns)

    def _generate_impl(self, n: int) -> pd.DataFrame:
        synthetic = self._synth.sample(n)
        return synthetic[self._columns].reset_index(drop=True)
