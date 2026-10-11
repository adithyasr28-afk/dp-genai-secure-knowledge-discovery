"""
models/privbayes_model.py

Wrapper around a faithful PrivBayes reimplementation (Zhang et al.,
2017), from `daanknoors/synthetic_data_generation`
(pip: `synthetic_data_generation`, import name `synthesis`). No
actively-maintained, packaged implementation from a DP-specialist org
exists for PrivBayes (unlike AIM/MST, which come from the original
authors via smartnoise-synth) -- this is disclosed here and in the
README rather than presented as equivalent-provenance to AIM/MST.
This is still a faithful port of the original greedy-Bayesian-network-
plus-exponential-mechanism algorithm (Rule 2: not a "fake simplified
algorithm").

DISCLOSED COMPATIBILITY FIX:
    The package's dependency `thomas_core` calls the removed
    `numpy.product` alias (removed in numpy >= 2.0; use `numpy.prod`
    instead). Downgrading numpy project-wide was rejected because other
    models in this project (CTGAN/TVAE) were verified against the
    current numpy release, and pinning numpy backwards risks silently
    breaking those. Instead we restore the alias at import time --
    `numpy.product = numpy.prod` -- which is functionally identical
    (confirmed: both compute the product of array elements) and touches
    nothing except this one missing attribute. This shim is applied
    once, only within this module, and is logged here for visibility.

DISCLOSED PRIVACY-ACCOUNTING DIFFERENCE:
    PrivBayes's original formulation provides pure epsilon-differential
    privacy (no delta term), unlike AIM/MST which are (epsilon, delta)-DP
    via Gaussian-mechanism/zCDP accounting. This wrapper's
    `privacy_params()` reports delta=0 explicitly rather than reusing
    the project's shared delta value, so the results table does not
    imply a false apples-to-apples equivalence -- this exact
    non-comparability point is called out in the project's written
    report (see Section 4.1/4.4 of the research review).
"""

from __future__ import annotations

import warnings

import numpy as np

# See "DISCLOSED COMPATIBILITY FIX" above.
if not hasattr(np, "product"):
    np.product = np.prod

# Cosmetic only: the package's `thomas_core` dependency triggers pandas'
# groupby(observed=...) FutureWarning on every internal marginal
# computation (hundreds of times per fit), which floods logs without
# indicating any actual problem with our results. Suppressed narrowly by
# message text, not blanket-suppressed, so unrelated warnings still surface.
warnings.filterwarnings(
    "ignore", message=".*observed=False is deprecated.*", category=FutureWarning
)

from typing import Optional

import pandas as pd

from models.base import BaseSynthesizer, ColumnSpec


class PrivBayesModel(BaseSynthesizer):
    method_name = "PrivBayes"
    is_differentially_private = True

    def __init__(
        self,
        epsilon: float = 1.0,
        random_seed: int = 42,
        verbose: bool = False,
    ):
        super().__init__(random_seed=random_seed)
        self.epsilon = epsilon
        self.verbose = verbose
        self._synth = None
        self._columns: Optional[list] = None

    def privacy_params(self) -> dict:
        return {
            "epsilon": self.epsilon,
            "delta": 0.0,
            "mechanism": "PrivBayes (Bayesian network + exponential mechanism), Zhang et al. 2017",
            "note": (
                "PrivBayes provides pure epsilon-DP (delta=0), not (epsilon,delta)-DP "
                "like AIM/MST -- not directly budget-equivalent at the 'same' epsilon."
            ),
        }

    def _fit_impl(self, train_df: pd.DataFrame, column_spec: ColumnSpec) -> None:
        from synthesis.synthesizers.privbayes import PrivBayes

        self._columns = list(train_df.columns)
        self._synth = PrivBayes(epsilon=self.epsilon, verbose=self.verbose)
        self._synth.fit(train_df)

    def _generate_impl(self, n: int) -> pd.DataFrame:
        synthetic = self._synth.sample(n_records=n)
        return synthetic[self._columns].reset_index(drop=True)
