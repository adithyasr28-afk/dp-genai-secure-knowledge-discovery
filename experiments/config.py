"""
experiments/config.py

Configuration objects for a single experiment run and for the overall
sweep (the AIM epsilon sweep, plus the DP-baseline and non-DP-reference
runs). Kept as plain, JSON-serializable dataclasses so a full
experiment's exact configuration can be logged alongside its results
(Rule: reproducibility) and so a config can be re-loaded to resume an
interrupted multi-day sweep (see runner.py's resumability contract).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

DEFAULT_DELTA = 1e-5
DEFAULT_EPSILON_SWEEP = [0.5, 1.0, 3.0, 5.0, 10.0]
DEFAULT_N_SEEDS = 3
AIM_N_SEEDS_DEFAULT = 1  # AIM's per-round cost makes 3 full repeats impractical by default -- see aim_model.py


@dataclass
class RunConfig:
    """One fully-specified (method, hyperparameters, seed) run."""
    dataset_name: str
    method: str                      # "AIM" | "MST" | "PrivBayes" | "CTGAN" | "TVAE"
    random_seed: int
    epsilon: Optional[float] = None  # None for non-DP methods
    delta: Optional[float] = None
    synthetic_size_multiplier: float = 1.0  # 1.0 = same size as real training data
    epochs: Optional[int] = None     # CTGAN/TVAE only
    extra_params: dict = field(default_factory=dict)

    def run_id(self) -> str:
        """A stable, filesystem-safe identifier for this exact run,
        used both as the results-log key (for resumability -- see
        runner.py) and as the synthetic-CSV filename."""
        eps_part = f"_eps{self.epsilon}" if self.epsilon is not None else ""
        size_part = f"_x{self.synthetic_size_multiplier}" if self.synthetic_size_multiplier != 1.0 else ""
        return f"{self.dataset_name}_{self.method}{eps_part}{size_part}_seed{self.random_seed}"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SweepConfig:
    """The full experiment plan: which methods, which epsilons, how
    many seeds each. Mirrors the project spec's Section 6/7/8."""
    dataset_name: str
    epsilon_sweep: list = field(default_factory=lambda: list(DEFAULT_EPSILON_SWEEP))
    delta: float = DEFAULT_DELTA
    n_seeds_dp: int = DEFAULT_N_SEEDS
    n_seeds_aim: int = AIM_N_SEEDS_DEFAULT
    n_seeds_non_dp: int = DEFAULT_N_SEEDS
    ctgan_epochs: int = 300
    tvae_epochs: int = 300
    aim_max_rounds: int = 60  # see models/aim_model.py docstring
    include_methods: list = field(default_factory=lambda: ["AIM", "MST", "PrivBayes", "CTGAN", "TVAE"])
    synthetic_size_multipliers: list = field(default_factory=lambda: [1.0])  # add 2.0, 5.0 for augmentation experiment
    base_seed: int = 42

    def build_run_configs(self) -> list:
        """Expand this sweep into the full, explicit list of RunConfig
        objects to execute. Each is independent and resumable."""
        runs = []

        for size_mult in self.synthetic_size_multipliers:
            # DP methods: sweep epsilon x seeds
            for method, n_seeds in [("AIM", self.n_seeds_aim), ("MST", self.n_seeds_dp), ("PrivBayes", self.n_seeds_dp)]:
                if method not in self.include_methods:
                    continue
                for eps in self.epsilon_sweep:
                    for seed_idx in range(n_seeds):
                        runs.append(RunConfig(
                            dataset_name=self.dataset_name,
                            method=method,
                            random_seed=self.base_seed + seed_idx,
                            epsilon=eps,
                            delta=self.delta,
                            synthetic_size_multiplier=size_mult,
                            extra_params={"aim_max_rounds": self.aim_max_rounds} if method == "AIM" else {},
                        ))

            # Non-DP reference methods: no epsilon, just seeds
            for method, epochs in [("CTGAN", self.ctgan_epochs), ("TVAE", self.tvae_epochs)]:
                if method not in self.include_methods:
                    continue
                for seed_idx in range(self.n_seeds_non_dp):
                    runs.append(RunConfig(
                        dataset_name=self.dataset_name,
                        method=method,
                        random_seed=self.base_seed + seed_idx,
                        epsilon=None,
                        delta=None,
                        synthetic_size_multiplier=size_mult,
                        epochs=epochs,
                    ))

        return runs
