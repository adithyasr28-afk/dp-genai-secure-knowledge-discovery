"""
models/aim_model.py

Wrapper around the ORIGINAL AIM implementation (McKenna, Mullins,
Sheldon & Miklau, 2022), as shipped in `smartnoise-synth` /
`mbi` (Ryan McKenna's own package). This is not a reimplementation
(Rule 2) -- `snsynth.aim.aim.AIMSynthesizer` imports directly from
`mbi` (Dataset, estimation, marginal_oracles, etc.), which is the
authors' own reference codebase.

IMPORTANT, DISCLOSED METHODOLOGICAL DEVIATION:
    AIM's reference implementation defaults to `rounds = 16 * n_columns`
    adaptive rounds, each running a mirror-descent fit with 1000
    iterations. On this project's example dataset (14 columns), that
    default was empirically measured to take ~35-40 minutes for a
    SINGLE (epsilon, seed) run -- consistent with the SIGMOD 2025
    benchmark's finding that AIM is markedly slower than deep-learning
    DP alternatives. Running the full epsilon sweep x 3 seeds at the
    paper's default round count is not tractable on student hardware
    within a reasonable iteration cycle.

    To keep the project realistically runnable (Rule 9) while being
    transparent about the tradeoff (never silently substitute a
    different algorithm -- Rule 5), this wrapper caps `rounds` at
    `MAX_ROUNDS` by default. This is a disclosed hyperparameter choice,
    not an algorithmic substitution: every round still runs AIM's exact
    select-measure-generate step with the exact same privacy accounting.
    Capping rounds simply means AIM spends its (already fixed) privacy
    budget over fewer adaptive iterations, which can reduce utility
    (fewer chances to correct the model) but does NOT change the (epsilon,
    delta) guarantee. This cap and its value are logged into every
    experiment record so results are fully reproducible and the
    deviation is never hidden in a table.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from models.base import BaseSynthesizer, ColumnSpec

MAX_ROUNDS_DEFAULT = 60  # see module docstring for justification


class AIMModel(BaseSynthesizer):
    method_name = "AIM"
    is_differentially_private = True

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        max_rounds: int = MAX_ROUNDS_DEFAULT,
        random_seed: int = 42,
        verbose: bool = False,
    ):
        super().__init__(random_seed=random_seed)
        self.epsilon = epsilon
        self.delta = delta
        self.max_rounds = max_rounds
        self.verbose = verbose
        self._synth = None
        self._columns: Optional[list] = None

    def privacy_params(self) -> dict:
        return {
            "epsilon": self.epsilon,
            "delta": self.delta,
            "mechanism": "AIM (Adaptive and Iterative Mechanism), McKenna et al. 2022",
            "rounds_cap_applied": self.max_rounds,
            "note": (
                "Rounds capped below the paper's default 16*n_columns heuristic "
                "for tractability on student hardware; the (epsilon, delta) "
                "guarantee itself is unaffected -- see models/aim_model.py docstring."
            ),
        }

    def _fit_impl(self, train_df: pd.DataFrame, column_spec: ColumnSpec) -> None:
        # AIM (as wrapped by smartnoise-synth) requires ALL columns to be
        # discretized/categorical -- this class assumes `train_df` is
        # already the output of Preprocessor.transform_discretized(),
        # which is the experiment runner's responsibility to supply.
        from snsynth import Synthesizer

        self._columns = list(train_df.columns)
        n_columns = len(self._columns)
        rounds = min(16 * n_columns, self.max_rounds)

        self._synth = Synthesizer.create(
            "aim",
            epsilon=self.epsilon,
            delta=self.delta,
            verbose=self.verbose,
            rounds=rounds,
        )
        self._synth.fit(
            train_df,
            categorical_columns=self._columns,
            preprocessor_eps=0.0,  # we already fit our own preprocessing; no budget spent here
        )

    def _generate_impl(self, n: int) -> pd.DataFrame:
        synthetic = self._synth.sample(n)
        # snsynth returns columns in its own internal order; re-align to
        # the original fitted column order for downstream consistency.
        return synthetic[self._columns].reset_index(drop=True)
