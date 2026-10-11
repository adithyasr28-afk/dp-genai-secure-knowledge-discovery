"""
models/mst_model.py

Wrapper around the ORIGINAL MST implementation (McKenna, Miklau &
Sheldon, 2021 -- winner of the 2018 NIST DP Synthetic Data Challenge),
as shipped in `smartnoise-synth`. Like AIM, this is not a
reimplementation (Rule 2): `snsynth.mst.mst.MSTSynthesizer` builds on
the same `mbi` backend from the original authors.

Unlike AIM, MST is non-adaptive (a single maximum-spanning-tree marginal
selection, then one graphical-model fit), so it does not carry AIM's
per-round mirror-descent cost. Empirically, on this project's example
dataset (14 columns, 2400 training rows), MST fits in ~50 seconds --
no rounds cap or other tractability deviation was necessary here.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from models.base import BaseSynthesizer, ColumnSpec


class MSTModel(BaseSynthesizer):
    method_name = "MST"
    is_differentially_private = True

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        random_seed: int = 42,
        verbose: bool = False,
    ):
        super().__init__(random_seed=random_seed)
        self.epsilon = epsilon
        self.delta = delta
        self.verbose = verbose
        self._synth = None
        self._columns: Optional[list] = None

    def privacy_params(self) -> dict:
        return {
            "epsilon": self.epsilon,
            "delta": self.delta,
            "mechanism": "MST (Maximum Spanning Tree), McKenna, Miklau & Sheldon 2021",
        }

    def _fit_impl(self, train_df: pd.DataFrame, column_spec: ColumnSpec) -> None:
        # Like AIM, MST (as wrapped by smartnoise-synth) requires all
        # columns discretized/categorical -- callers must pass the
        # output of Preprocessor.transform_discretized().
        from snsynth import Synthesizer

        self._columns = list(train_df.columns)
        self._synth = Synthesizer.create(
            "mst",
            epsilon=self.epsilon,
            delta=self.delta,
            verbose=self.verbose,
        )
        self._synth.fit(
            train_df,
            categorical_columns=self._columns,
            preprocessor_eps=0.0,
        )

    def _generate_impl(self, n: int) -> pd.DataFrame:
        synthetic = self._synth.sample(n)
        return synthetic[self._columns].reset_index(drop=True)
