# Differential Privacy-Enhanced Generative AI for Secure Knowledge Discovery

BCSE318L Data Privacy case study (Team 26FSDPYCPMID1028).

This repository contains:

1. **A comparative empirical study of synthetic tabular data generators.** It
   compares three differentially private generators — **AIM**, **MST**, **PrivBayes** —
   with two non-DP baselines, **CTGAN** and **TVAE**. All five share one
   leakage-safe preprocessing pipeline and are evaluated on statistical fidelity,
   ML utility, empirical privacy risk, fairness, rare-pattern preservation and
   runtime. *(Original project.)*
2. **An LLM knowledge-discovery extension.** It summarises a saved **DP synthetic**
   dataset into aggregate statistics and asks Claude (Anthropic API) to explain
   patterns, relationships, possible insights and limitations. *(Added in this
   iteration.)*
3. **Verification tooling.** It de-duplicates the experiment log, re-evaluates
   every logged metric from the saved synthetic CSVs, and produces the tables and
   600-DPI figures used in the report. *(Added.)*

> **What this project is not.** It does not train a new generative model or LLM,
> does not implement DP-SGD, and is not a retrieval-augmented generation (RAG)
> system. The LLM receives only aggregate statistics computed from DP synthetic
> data. The LLM adds **no** privacy guarantee of its own.

---

## Contents

- [Quick start (Windows)](#quick-start-windows)
- [Quick start (macOS / Linux)](#quick-start-macos--linux)
- [Using the dashboard](#using-the-dashboard)
- [LLM knowledge-discovery extension](#llm-knowledge-discovery-extension)
- [Reproducing the analysis](#reproducing-the-analysis)
- [Running the tests](#running-the-tests)
- [Experiments and verified results](#experiments-and-verified-results)
- [Dataset](#dataset)
- [Repository structure](#repository-structure)
- [Disclosed deviations and known limitations](#disclosed-deviations-and-known-limitations)
- [Change log for this iteration](#change-log-for-this-iteration)

---

## Quick start (Windows)

Requirements: **Python 3.11** (the project was verified on 3.11.0 and 3.11.5),
**Git** (one dependency installs from GitHub), and an internet connection during
installation. The full install is about 2–3 GB because of PyTorch and JAX.

```bat
git clone https://github.com/adithyasr28-afk/dp-genai-secure-knowledge-discovery.git
cd dp-genai-secure-knowledge-discovery
py -3.11 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt
run_dashboard.bat
```

Then open <http://localhost:8501>. `run_dashboard.bat 8510` uses another port.

`constraints.txt` pins every package to the exact version that produced the saved
results (recovered from the original project's virtual environment). Without it,
pip's resolver can spend a very long time backtracking over `pyjanitor` versions.

## Quick start (macOS / Linux)

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -c constraints.txt
streamlit run app.py
```

---

## Using the dashboard

The sidebar has a **Workspace** switch.

**Comparative study** (original nine pages; load the bundled example dataset first):

| Page | What it does |
|---|---|
| Dataset | Profile the CSV; choose target, sensitive and excluded columns |
| Preprocessing | Stratified train/test split; fit bins, rare-category grouping and imputation on the training split only |
| Model Selection & Generate | Pick a method and ε/δ or epochs, run it, compute the TRTR reference |
| Synthetic Data | Preview, summary statistics and download of the generated data |
| Fidelity | Marginal, correlation and 3-way query error; out-of-range check |
| ML Utility | TSTR vs TRTR for Logistic Regression, Random Forest and XGBoost |
| Privacy | Formal (ε, δ) statement, membership-inference AUC, record similarity |
| Fairness / Rare Patterns | Minority class, rare categories and combinations; demographic parity, equalised odds |
| Model Comparison | All logged runs (latest record per run_id), ε sweeps and trade-off scatter plots |

> Running a generator from the dashboard **appends to `results/experiment_results.jsonl`
> and overwrites that run's CSV**. Use `git checkout -- results/` afterwards if you
> want the published results back unchanged.

**LLM Knowledge Discovery (extension)** works from the saved results alone, so no
dataset needs to be loaded first.

---

## LLM knowledge-discovery extension

Code: `knowledge_discovery/` (`catalog.py`, `summarizer.py`, `prompts.py`,
`llm_client.py`, `streamlit_page.py`).

**Pipeline**

1. List the eligible datasets. These are CSVs in `results/synthetic_data/` whose
   latest completed log record is a DP method (AIM, MST or PrivBayes). The privacy
   parameters shown come from the log, not the filename.
2. Load the selected CSV through a path guard. Anything outside
   `results/synthetic_data/` — including the original `data/` folder — is refused.
3. Build an **aggregate-only** summary:
   - per-column marginals;
   - target rate by group;
   - strongest Cramér's V / Pearson associations;
   - the run's own fidelity, utility and MIA metrics;
   - a privacy manifest.

   Groups with fewer than *k* = 20 synthetic rows are suppressed, and values are
   rounded to 3 decimals.
4. Show the exact system prompt and user message in the UI, then:
   - **Live mode:** call Claude (`claude-opus-5-5` by default, server-side refusal
     fallback enabled).
   - **Demo mode:** produce a deterministic rule-based template that is clearly
     labelled *"NOT generated by an LLM"*.
5. Write an audit record to `results/llm_insights/` (git-ignored). It holds the
   prompt, SHA-256 of the payload, mode, model, usage, and whether a request was
   actually sent.

**Configuring live mode**

A Claude Pro/Max *chat* subscription does **not** include API credits. You need an
API key from <https://console.anthropic.com/>.

```bat
copy .env.example .env
notepad .env          &REM set ANTHROPIC_API_KEY=...
run_dashboard.bat
```

The key is read from the environment (or from the git-ignored `.env`). It is never
placed in a prompt, an audit file or the UI. Optional settings: `KD_MODEL`,
`KD_EFFORT` (default `medium`), `KD_MAX_TOKENS`, and `KD_SERVER_FALLBACK=0` to
turn off the server-side refusal fallback.

**Live-mode verification status.** No API key was available while this was built,
so **no real Claude response has been generated or verified**.

What *is* tested:
- the request is serialised correctly through the real `anthropic` 1.13 SDK against
  a local mock server (body, headers, beta flag, no key in the body, no original
  rows);
- HTTP 400/401/429/500 and connection errors are handled;
- refusal and empty-response handling;
- the missing-key path.

What only a real key can confirm: that the API accepts the request, and the
quality of the model's explanations.

**Privacy notes**

- Analysing a DP synthetic dataset is post-processing. It spends no extra privacy
  budget *provided the generator's DP guarantee and its assumptions hold*. Here one
  of those assumptions is that the preprocessing domain (bin edges and category
  vocabulary) is treated as public — see the limitations below.
- The summary statistics are **not** a separate DP release. Small-cell suppression
  is defence in depth, not a formal mechanism.
- In live mode the summary leaves your machine and is processed by Anthropic under
  its API terms.
- Synthetic data can contain **spurious associations**. For example, the AIM and
  MST ε=3 datasets show education ↔ race Cramér's V ≈ 0.45–0.49, versus 0.12 in the
  real training split. An LLM will describe such artifacts faithfully. Treat its
  output as hypotheses (see `analysis/knowledge_utility.py`).

---

## Reproducing the analysis

No generator is re-trained by these scripts. They read the saved log and CSVs.

```bat
venv\Scripts\python -m analysis.verify_results      &REM ~2 min: tables + figures
venv\Scripts\python -m analysis.knowledge_utility   &REM ~1 min: payload vs real-data agreement
venv\Scripts\python figures\diagram_builder.py      &REM report diagrams (PNG 600 DPI, SVG, .drawio)
```

Outputs:
- `results/verified/`: verification report, de-duplicated runs, aggregated
  mean ± std tables, TRTR reference, re-evaluation comparison, knowledge-utility
  tables.
- `figures/`: result plots.
- `figures/diagrams/`: architecture and workflow diagrams. Open the `.drawio` files
  in draw.io to restyle them.

To regenerate all 41 runs from scratch (several hours; AIM dominates):

```bat
venv\Scripts\python run_sweep.py
```

The sweep resumes where it stopped. Completed run_ids in the log are skipped, so
move or rename `results/experiment_results.jsonl` first if you want fresh runs.
DP generator randomness is **not** seeded (see the limitations), so re-runs will
not reproduce the saved synthetic data bit-for-bit.

---

## Running the tests

```bat
venv\Scripts\python -m pytest -m "not slow"   &REM 27 tests, ~15 s
venv\Scripts\python -m pytest -m slow         &REM 5 end-to-end generator runs, ~3 min
```

| Suite | Covers |
|---|---|
| `tests/test_knowledge_discovery.py` | DP-only catalogue (35 datasets), privacy parameters from the log, duplicate handling, refusal of the original/non-DP data, aggregate-only payload, original rows never in the prompt, original file never read, small-cell suppression, demo labelling, missing key, request shape, no key leakage, refusal/empty/API errors |
| `tests/test_live_http_mock.py` | Real `anthropic` SDK against a local mock server: request body/headers, HTTP 400/401/429/500, connection failure |
| `tests/test_pipeline_smoke.py` | Dataset shape, 41-run sweep, train-only preprocessing, inverse binning, and AIM/MST/PrivBayes/CTGAN/TVAE end-to-end in a temporary results folder |

---

## Experiments and verified results

**Configuration** (`experiments/config.py`, run via `run_sweep.py`):

| Method | Guarantee | Configurations | Seeds | Runs |
|---|---|---|---|---|
| AIM | (ε, δ)-DP, δ = 1e-5, zCDP accounting | ε ∈ {0.5, 1, 3, 5, 10}, rounds ≤ 60 | 1 (42) | 5 |
| MST | (ε, δ)-DP, δ = 1e-5 | ε ∈ {0.5, 1, 3, 5, 10} | 3 (42–44) | 15 |
| PrivBayes | pure ε-DP (δ = 0) | ε ∈ {0.5, 1, 3, 5, 10} | 3 | 15 |
| CTGAN | none (non-DP baseline) | 300 epochs | 3 | 3 |
| TVAE | none (non-DP baseline) | 300 epochs | 3 | 3 |
| | | | **Total** | **41** |

**Log integrity** (`results/verified/verification_report.json`):

- 43 records but 41 unique run_ids, all with status `completed`.
  `AIM_eps3.0_seed42` and `PrivBayes_eps3.0_seed42` were each run twice (second
  runs at 20:42 on 2026-09-18). The **latest** record is used because it produced
  the CSV on disk. The two AIM records differ (3-way error 0.220 vs 0.189), which
  illustrates run-to-run variability.
- All 41 configurations pass checks on ε, δ, pure vs approximate DP, the AIM rounds
  cap and non-DP labelling. All 41 CSVs are present with 2,400 rows.
- **733 of 738** logged metric values reproduce exactly (≤ 1e-6) when recomputed
  from the saved CSVs. The other 5 are MIA AUC values that differ by ≤ 2.8 × 10⁻⁶.
- TRTR (real-data) F1: LR 0.583, RF 0.620, XGBoost 0.647. This reference was not
  stored in the original log; it is recomputed deterministically.

**Headline findings** (mean over seeds; the AIM figures come from a single seed):

| | XGBoost TSTR F1 | F1 retention vs TRTR | 3-way TVD ↓ | MIA AUC |
|---|---|---|---|---|
| AIM ε=1 / 3 / 10 | 0.459 / 0.525 / 0.496 | 71% / 81% / 77% | 0.242 / 0.189 / 0.145 | ≈ 0.50 |
| MST ε=1 / 3 / 10 | 0.420 / 0.399 / 0.447 | 65% / 62% / 69% | 0.260 / 0.253 / 0.238 | ≈ 0.50 |
| PrivBayes ε=1 / 3 / 10 | 0.411 / 0.530 / 0.506 | 64% / 82% / 78% | 0.239 / 0.176 / 0.142 | ≈ 0.50 |
| CTGAN (non-DP) | 0.404 | 62% | 0.269 | 0.499 |
| TVAE (non-DP) | 0.547 | 85% | 0.288 | 0.506 |

How to read these results:

- The original hypothesis — that AIM gives the best DP trade-off — is **only
  partly supported**.
  - AIM has the highest point estimates at ε ≤ 1 on utility, and on 3-way
    fidelity at ε = 0.5.
  - At ε ≥ 3 its single-seed values fall within PrivBayes's seed-to-seed spread,
    so no ranking between the two can be claimed.
  - It is also the slowest DP method: 52–626 s per fit, against 0.5–21 s for
    PrivBayes and 25–58 s for MST.
- The 1-nearest-neighbour membership-inference attack gives AUC ≈ 0.5 for **every**
  method, including the non-DP ones. This attack is too weak to separate the
  methods; it is **not** evidence that CTGAN/TVAE are private. TVAE produced the
  closest records (mean distance to closest record 0.74 vs ≥ 1.5 for the others).
  It is the only method that emitted exact copies of training rows: 3 rows across
  its 3 runs (2 / 0 / 1).
- Full tables are in `results/verified/aggregated_by_method_epsilon.csv` and in the
  report.

---

## Dataset

`data/example_dataset.csv` is a 3,000-row stratified sample of the UCI Adult
(Census Income) dataset (Becker & Kohavi, 1996, doi:10.24432/C5XW20, CC BY 4.0):
14 columns, target `income` (24% `>50K`), sensitive attribute `sex` (used by the
sweep; the dashboard suggests `race` by default).

- It is public, de-identified census data, used here as a *stand-in* for sensitive
  data.
- It contains 52 duplicate rows and missing values in three columns.
- The 80/20 split gives 2,400 training and 600 test rows, stratified on `income`
  with seed 42.

---

## Repository structure

```
app.py                      Streamlit dashboard (+ Workspace switch for the extension)
run_dashboard.bat           Windows launcher
run_sweep.py                Full 41-run experiment sweep (resumable)
requirements.txt            Dependencies; use with -c constraints.txt
constraints.txt             Exact versions from the original environment
.env.example                Placeholder for ANTHROPIC_API_KEY (copy to .env)
data/example_dataset.csv    UCI Adult sample (n = 3,000)
models/                     AIM, MST, PrivBayes, CTGAN, TVAE wrappers (unchanged)
preprocessing/              Profiling + leakage-safe preprocessing (unchanged)
evaluation/                 Fidelity, utility, privacy, fairness, rare patterns (unchanged)
experiments/                RunConfig/SweepConfig, runner with JSON-lines log (unchanged)
knowledge_discovery/        LLM extension (new)
analysis/                   verify_results.py, knowledge_utility.py (new)
figures/                    Result figures (PNG 600 DPI + SVG), diagram_builder.py, diagrams/ (new)
results/experiment_results.jsonl   Original 43-record log (unchanged)
results/synthetic_data/     41 synthetic CSVs (unchanged)
results/verified/           Verification outputs (new)
tests/                      pytest suite (new)
docs/screenshots/           Dashboard evidence (new)
report/                     Report draft (DOCX + Markdown source)
```

---

## Disclosed deviations and known limitations

1. **AIM's rounds are capped at 60** (`models/aim_model.py`). The paper's default is
   16 × columns = 224 rounds, measured at about 35–40 min per run. The cap does not
   change the (ε, δ) bound but can reduce utility.
   - The cap must stay above about 0.9 × number of columns: snsynth spends
     0.9·d/T of ρ on the initial one-way measurements, and with T too small the
     remaining budget goes negative and AIM fails.
   - Logged AIM fit times range from 52 s to 626 s.
2. **Preprocessing is not privatised.** Quantile bin edges, spike values and the
   rare-category vocabulary are learned from the real training split, and the
   generators are called with `preprocessor_eps = 0`. The formal DP guarantee
   therefore holds only if this domain information is treated as public (or
   computed with a separate DP budget). This is a known weakness of many
   DP-synthesis pipelines and is stated in the report.
3. **DP generator randomness is not seeded.** `random_seed` is passed to the
   evaluation code and to CTGAN/TVAE, but not to the snsynth AIM/MST or PrivBayes
   synthesizers. "Seeds" for DP methods vary the evaluation, and the generators'
   own randomness is uncontrolled.
4. **AIM uses one seed per ε**, so it has no variance estimates.
5. **The empirical privacy evaluation is weak.**
   - The membership-inference attack is a simple 1-NN distance attack.
   - The near-duplicate threshold is 0, because the data contain exact duplicates,
     so it counts only exact copies.
   - The TPR is reported at FPR = 0.1, not at a low-FPR operating point.
6. **Single dataset, binary target only.** 3,000 rows is small. All conclusions are
   specific to this sample.
7. **PrivBayes** uses a faithful third-party port (`daanknoors/synthetic_data_generation`)
   with a `numpy.product` shim. It provides pure ε-DP, which is not
   budget-equivalent to AIM/MST at the same ε.
8. **Install `mbi` from PyPI, not GitHub.** The GitHub repository was rewritten
   with an incompatible API.
9. The fairness metrics use a single Logistic Regression per run and are noisy
   (e.g. AIM ε=3 has a demographic-parity difference of 0.48, against a real-data
   reference of 0.17).

## Change log for this iteration

See `report/CHANGES.md` for the full list of modified and added files.

## Licence and citation

Academic coursework. The third-party generator packages (smartnoise-synth, mbi,
ctgan, synthetic_data_generation) keep their own licences — check each package
before any non-academic use. Please cite the original method papers listed in
the report.
