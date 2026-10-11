# Privacy-Preserving Synthetic Tabular Data: A Comparative Study

A controlled, fair comparison of five representative synthetic tabular
data generation methods — **AIM**, **MST**, **PrivBayes** (differentially
private) and **CTGAN**, **TVAE** (non-DP reference methods) — measuring
the privacy–utility–fidelity trade-off on a shared preprocessing and
evaluation pipeline.

**This is not a new generative model.** It is a research prototype for
running and comparing experiments, built as a Streamlit dashboard, so
that a specific hypothesis — *"AIM provides the strongest privacy–
utility trade-off among DP methods"* — can be tested empirically and
honestly, not assumed.

## Main research question

> Among different synthetic tabular data generation techniques, which
> approach provides the best balance between privacy, data fidelity,
> downstream ML utility, and computational cost for privacy-sensitive
> tabular data?

## What's genuine, and what's disclosed as a compromise

Every method wraps an **unmodified, original-author implementation** —
none of the five algorithms are reimplemented from scratch:

| Method | Package | Provenance |
|---|---|---|
| AIM | `smartnoise-synth` + `mbi` | Original authors (McKenna et al.), via OpenDP |
| MST | `smartnoise-synth` + `mbi` | Original authors (McKenna et al.), via OpenDP |
| PrivBayes | `synthetic_data_generation` (`daanknoors`) | Faithful third-party port; **no actively-maintained packaged version exists from a DP-specialist org** — disclosed here and in `models/privbayes_model.py` |
| CTGAN | `ctgan` (sdv-dev) | Original authors (Xu et al.) |
| TVAE | `ctgan` (sdv-dev) | Original authors (Xu et al.), same package as CTGAN |

Two disclosed, documented compromises were necessary for the project to
be runnable on student hardware — both are logged into every affected
experiment record, never hidden:

1. **AIM's `rounds` parameter is capped** (`models/aim_model.py`,
   `MAX_ROUNDS_DEFAULT = 60`). The paper's default heuristic
   (`rounds = 16 * n_columns`) was empirically measured at ~35–40
   minutes for a *single* run on this project's 14-column example
   dataset — consistent with the SIGMOD 2025 DP-synthesis benchmark's
   finding that AIM is markedly slower than deep-learning DP
   alternatives. Capping rounds does **not** change the (ε, δ)
   guarantee itself — it only limits how many adaptive iterations AIM
   gets to spend that (already fixed) budget over, which can reduce
   utility but never weakens the formal privacy bound.
2. **A numpy≥2.0 compatibility shim** for PrivBayes's `thomas_core`
   dependency, which calls the removed `numpy.product` alias. Restored
   via `numpy.product = numpy.prod` (functionally identical) at import
   time, scoped to `models/privbayes_model.py` only — numpy was not
   downgraded project-wide, since CTGAN/TVAE were verified against the
   current numpy release.
3. **`mbi` must come from PyPI, not GitHub.** The upstream
   `ryan112358/private-pgm` repository (AIM/MST's backend) has since
   been renamed and rewritten to `ryan112358/mbi`, with a different
   internal API than the `mbi` package published on PyPI. `snsynth`'s
   AIM/MST code is written against the **PyPI** API. Installing `mbi`
   via `pip install git+https://github.com/ryan112358/private-pgm.git`
   (an instruction that still circulates in some smartnoise-synth docs
   and error messages) installs the wrong, incompatible rewrite and
   breaks both AIM and MST with an `ImportError` (`FactoredInference`
   or `LinearMeasurement` not found, depending on which version lands).
   `requirements.txt` pins `mbi>=1.1.0,<2` from PyPI directly — do not
   "fix" an import error here by installing `mbi` from GitHub.

PrivBayes also uses **pure ε-DP (δ=0)**, not (ε, δ)-DP like AIM/MST —
this is reported explicitly by `privacy_params()` and the app never
implies a naive apples-to-apples ε comparison across mechanism types
(see the accompanying literature review, Section 4.1, for why AIM/MST/
GEM are not directly comparable to CTGAN/TVAE on fidelity alone either).

## Installation

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

One dependency (PrivBayes) installs from GitHub — this
requires git and a working internet connection during install. AIM/MST's
`mbi` backend installs from plain PyPI (see `requirements.txt` for why
installing it from GitHub instead can silently break both methods).

## Running the app

```bash
streamlit run app.py
```

Click **"Use bundled example dataset"** in the sidebar to try the full
pipeline immediately with a pre-cleaned, stratified 3,000-row sample of
the UCI Adult Income dataset (`data/example_dataset.csv`), or upload
your own CSV. The architecture supports arbitrary tabular CSVs,
including a healthcare or other privacy-sensitive dataset later — the
Dataset page's target/sensitive-attribute selection and the
Preprocessing page's configuration are dataset-agnostic.

### App pages

1. **Dataset** — upload, profile, select target/sensitive/excluded columns.
2. **Preprocessing** — configure and fit the shared, leakage-safe
   preprocessing pipeline (train/test split, imputation, rare-category
   grouping, numerical binning).
3. **Model Selection & Generate** — pick a method, configure ε/δ or
   epochs, run it, and (once) compute the TRTR reference.
4. **Synthetic Data** — preview, summary statistics, CSV download.
5. **Fidelity** — marginal, correlation, and 3-way query-error metrics;
   an out-of-range validation check.
6. **ML Utility** — TSTR vs TRTR across Logistic Regression, Random
   Forest, and XGBoost, with utility retention %.
7. **Privacy** — the formal (ε, δ) statement plus empirical membership
   inference attack (AUC, TPR@FPR) and record-similarity results.
8. **Fairness / Rare Patterns** — minority-class, rare-category, and
   rare-combination preservation; demographic parity / equalized odds
   / subgroup performance when a sensitive attribute is configured.
9. **Model Comparison** — every logged experiment, the epsilon-sweep
   charts, and the fidelity-vs-utility / utility-vs-privacy Pareto
   views. **No arbitrary weighted "overall" score is computed** — the
   spec explicitly asks for trade-offs to be shown, not a fabricated
   single ranking.

## Running a full experiment sweep from the command line

The Streamlit app is best for interactive, one-run-at-a-time
exploration. For the central experiment — the **AIM epsilon sweep**
(ε ∈ {0.5, 1, 3, 5, 10}) plus the MST/PrivBayes/CTGAN/TVAE comparison
runs — use `experiments/config.py`'s `SweepConfig` directly in a script:

```python
import pandas as pd
from preprocessing.schema import profile_dataset
from preprocessing.pipeline import Preprocessor, train_test_split_no_leakage
from experiments.config import SweepConfig
from experiments.runner import run_single_experiment, compute_trtr_once

df = pd.read_csv("data/example_dataset.csv")
profile = profile_dataset(df)
numerical_cols = [c.name for c in profile.columns if c.inferred_type == "numerical"]
categorical_cols = [c.name for c in profile.columns if c.inferred_type == "categorical"] + ["income"]

train_df, test_df = train_test_split_no_leakage(df, test_size=0.2, random_seed=42, stratify_column="income")
pp = Preprocessor(rare_threshold=0.01, n_bins=10, random_seed=42)
pp.fit(train_df, numerical_columns=numerical_cols, categorical_columns=categorical_cols,
       target_column="income", sensitive_column="sex")

compute_trtr_once(train_df, test_df, pp, numerical_cols, categorical_cols, "income")

sweep = SweepConfig(dataset_name="adult_example")  # 41 runs at default settings
for config in sweep.build_run_configs():
    run_single_experiment(
        config, train_df, test_df, pp, numerical_cols, categorical_cols,
        target_column="income", sensitive_column="sex",
    )
```

This is **resumable**: every completed run's ID is logged to
`results/experiment_results.jsonl`, and re-running the same loop
(e.g. after stopping and restarting across multiple days, per the
project's multi-day experiment-collection requirement) automatically
skips anything already finished. Expect the AIM portion of a full sweep
to take multiple hours at default settings (5 epsilons × 1 seed) —
this is the expected, disclosed AIM runtime cost described above, not a
bug.

## Reproducibility

- Every run uses a fixed random seed, logged in its result record.
- DP methods default to 3 seeds per (method, ε) combination (except AIM,
  which defaults to 1 seed per ε given its runtime cost — configurable
  via `SweepConfig.n_seeds_aim`); non-DP methods default to 3 seeds.
- Report **mean ± standard deviation** across seeds when comparing
  methods — do not compare one random run of one method against an
  averaged result from another (`results/experiment_results.jsonl` has
  every individual run; group by `method` + `epsilon` and aggregate
  yourself, or extend `experiments/runner.py`'s `load_all_results()`).
- All preprocessing parameters (bin edges, rare-category groupings,
  imputation values) are fit **once** on the training split and reused
  identically for every method and every synthetic-data evaluation —
  see `preprocessing/pipeline.py` for the full no-leakage contract.

## Project structure

```
project/
├── app.py                        # Streamlit dashboard (entry point)
├── requirements.txt
├── README.md
├── data/
│   └── example_dataset.csv       # bundled UCI Adult Income sample, n=3000
├── models/
│   ├── base.py                   # common BaseSynthesizer interface
│   ├── aim_model.py
│   ├── mst_model.py
│   ├── privbayes_model.py
│   ├── ctgan_model.py
│   └── tvae_model.py
├── preprocessing/
│   ├── schema.py                 # dataset profiling / column-type inference
│   └── pipeline.py                # shared, leakage-safe preprocessing
├── evaluation/
│   ├── fidelity.py
│   ├── utility.py
│   ├── privacy.py
│   ├── fairness.py
│   └── rare_patterns.py
├── experiments/
│   ├── config.py                 # RunConfig / SweepConfig
│   └── runner.py                 # orchestration + resumable JSON-lines logging
├── results/                       # experiment_results.jsonl + synthetic_data/
└── utils/
    └── logging.py
```

## Known limitations (disclosed, not hidden)

- **Binary classification targets only** for TSTR/TRTR utility and
  fairness evaluation (`evaluation/utility.py` raises a clear error on
  multi-class targets — extending to multi-class is a reasonable future
  addition, not implemented here to keep the metric set unambiguous).
- **Zero-inflated numerical columns** (e.g. `capital_gain`) use uniform-
  in-bin sampling when reconstructing DP methods' discretized output
  back to continuous values; this preserves the point-mass share exactly
  but can shift the *mean of the non-spike remainder* under heavy
  skew with few bins — a real, reportable property of the discretization
  choice, not an evaluation bug.
- **The membership-inference attack is a simple, auditable 1-NN
  distance attack**, not a shadow-model attack — chosen deliberately
  per Rule 1 (prefer transparent, directly-implementable techniques
  over reimplementing complex research algorithms). It may under-detect
  leakage relative to stronger attacks; this is noted directly in the
  app's Privacy page.
