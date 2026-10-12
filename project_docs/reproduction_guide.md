# Reproduction guide

Every command below was executed on 2026-10-12 on Windows 11 Home (build 26200) with Python 3.11.0, unless a step is marked *not re-run*. Measured times are wall-clock on that laptop.

## 1. Requirements

| Item | Version / note |
|---|---|
| OS | Windows 10/11 (tested). macOS/Linux use the same commands with `venv/bin/python` (not tested in this session) |
| Python | **3.11** (3.11.0 tested). The pinned versions in `constraints.txt` were recovered from the original environment |
| Disk | ≈ 2.5 GB for the virtual environment (PyTorch, XGBoost, smartnoise) |
| Network | Needed for `pip install`, and for live LLM mode only |
| API credentials | **Only** for live LLM mode: `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) and/or `ANTHROPIC_API_KEY`. Everything else, including demo mode, runs without any key |

## 2. Installation

```bat
git clone https://github.com/adithyasr28-afk/dp-genai-secure-knowledge-discovery.git
cd dp-genai-secure-knowledge-discovery
py -3.11 -m venv venv
venv\Scripts\python -m pip install -r requirements.txt -c constraints.txt
venv\Scripts\python -m pip check
```

**Clean-install test (2026-10-12):** a fresh `git clone` of `report-finalisation` into a new Python 3.11.0 venv installed in about 16 min (20:29 → 20:45, mostly downloads). `pip check`: *No broken requirements found*. The fast test suite in that clone: **43 passed, 1 skipped**. One harmless `setup.py install` deprecation warning for `antlr4-python3-runtime`.

## 3. Configuration (live LLM mode only)

```bat
copy .env.example .env
notepad .env
```

| Variable | Meaning | Default |
|---|---|---|
| `KD_PROVIDER` | `auto` / `gemini` / `anthropic` | `auto`: Claude if `ANTHROPIC_API_KEY` is set, else Gemini |
| `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) | Google AI Studio key | — |
| `KD_GEMINI_MODEL` | Gemini model id | `gemini-flash-latest` (alias; the served version is logged) |
| `ANTHROPIC_API_KEY` | Anthropic API key (a Claude chat subscription does **not** include API credit) | — |
| `KD_MODEL`, `KD_EFFORT`, `KD_SERVER_FALLBACK` | Claude settings | `claude-opus-5-5`, `medium`, `1` |
| `KD_MAX_TOKENS` | Output token limit (both providers) | 16000 |

`.env` is git-ignored. Never commit it, and never paste a key into a prompt, issue or chat. Placeholder values such as `your-…-here` are treated as unset.

## 4. Launch the dashboard

```bat
run_dashboard.bat            REM http://localhost:8501
run_dashboard.bat 8517       REM another port, if 8501 is taken
```

Expected result: the page "Privacy-Preserving Synthetic Tabular Data — Comparative Study".
- **Comparative workflow:** sidebar → **Use bundled example dataset**.
- **LLM page:** sidebar → **Workspace → LLM Knowledge Discovery**.

A generator run started from the UI **appends to the log and overwrites that run's CSV**. Restore the published results with:

```bat
git checkout -- results/
```

## 5. Tests

```bat
venv\Scripts\python -m pytest -m "not slow"     REM fast suite
venv\Scripts\python -m pytest                   REM everything, incl. 5 end-to-end generator runs
set RUN_LIVE_LLM=1 && venv\Scripts\python -m pytest -m live   REM ONE real, billable Gemini call (needs a key)
```

| Suite | Result on 2026-10-12 | Time |
|---|---|---|
| fast (`-m "not slow"`) | 43 passed, 1 skipped (the live test) | ≈ 25 s |
| full | 47 passed, 1 skipped (run before the Phase-2 test was added) | 337 s |

The tests never read the real `.env`: the fixtures patch `.env` loading and clear all key variables.

## 6. Reproduce the analysis from the saved outputs (no re-training)

```bat
venv\Scripts\python -m analysis.verify_results     REM log integrity, de-duplication, config checks, re-evaluation, tables, figures
venv\Scripts\python -m analysis.knowledge_utility  REM payload statistics vs real training split
venv\Scripts\python -m analysis.llm_case_study     REM fact-check of the 2 real Gemini responses
venv\Scripts\python figures\diagram_builder.py     REM 15 diagrams: PNG 600 DPI, SVG, .drawio
venv\Scripts\python report\build_report.py         REM report DOCX from report/src/*.md
```

| Step | Expected output | Time (2026-10-12) |
|---|---|---|
| `verify_results` | `results/verified/*.csv`, `verification_report.json`; `figures/fig_res_*.png/.svg`. Expect: 43 records, 41 unique, 733/738 exact | 2 min 46 s |
| `knowledge_utility` | `results/verified/knowledge_utility_*.csv`; `figures/fig_res_12_knowledge_utility.*` | 26 s |
| `llm_case_study` | `results/verified/llm_case_study*.csv`; `evidence/llm_responses/*.md` (only if the git-ignored audit records exist) | 8 s |
| `build_report` | `report/final_report.docx` | ≈ 1 min |

## 7. Re-running the experiments (*not re-run in this session*)

```bat
venv\Scripts\python run_sweep.py
```

- **Runtime.** The 41 logged fits took 50 min in total (AIM 24 min, CTGAN 12, MST 10, TVAE 2, PrivBayes 2). Evaluation and generation add more on top. Plan for 1–3 hours. The sweep resumes: run_ids already in the log are skipped. Rename `results/experiment_results.jsonl` to start fresh.
- **Not bit-reproducible.** The DP wrappers do not forward the seed to smartnoise or PrivBayes, so re-runs give different synthetic data. Expect AIM, MST and PrivBayes metrics to move by roughly the seed spread in Tables IX–XII. CTGAN and TVAE are seeded.
- **AIM rounds** are capped at 60 (`models/aim_model.py`). A cap at or below 0.9 × d (= 12.6 here) makes AIM fail.

## 8. Verification log (2026-10-12)

| Check | Result |
|---|---|
| Full test suite | 47 passed, 1 skipped, 337 s |
| Fast suite after the Phase-2 code change | 43 passed, 1 skipped |
| Clean clone + fresh venv + install + fast suite | install OK, `pip check` clean, 43 passed, 1 skipped |
| `verify_results` + `knowledge_utility` + `llm_case_study` re-run on the saved outputs | **All tracked CSV/JSON outputs and PNG figures byte-identical** to the committed versions. The exceptions: the 13 SVGs differ only in their embedded creation timestamp and element ids, and `reevaluation_comparison.csv` differs by ≤ 1.1 × 10⁻¹⁶ (floating-point noise). These differences were reverted |
| Dashboard launch | `run_dashboard.bat 8517` serves the app. All 10 feature areas were exercised by `evidence/screenshots/capture_screenshots.py` with no error element visible (`capture_log*.json`) |
| Experiments (`run_sweep.py`) | **Not re-run.** The 41 reported runs were checked against their saved CSVs, not regenerated |
