# Changes made in this iteration

Baseline: commit `052d334` imports the original project unchanged from
`synthetic_tabular_data_project_FINAL (2).zip`, without the machine-specific
`venv/` and `__pycache__/`. Every later change is in separate commits.

## Modified original files

| File | Change | Why |
|---|---|---|
| `app.py` | Added a sidebar **Workspace** switch that renders the LLM extension page before the "load a dataset" gate (≈10 lines). | The extension runs from saved DP results and must not require the original data to be loaded. |
| `app.py` | Model Comparison keeps the **latest completed record per run_id** and reports how many duplicates were excluded. | **Bug:** the original page counted 43 runs instead of 41 (two configurations were logged twice). |
| `app.py` | Caption for "Fidelity vs Utility" changed from "Bottom-right is best" to "Top-left is best". | **Bug:** the x-axis is KS (lower is better) and the y-axis is F1 (higher is better), so the old caption pointed at the worst corner. |
| `requirements.txt` | Added anthropic, python-dotenv, matplotlib, pytest, pypandoc_binary, python-docx. | Extension, figures, tests, report build. |
| `README.md` | Rewritten: Windows setup, LLM configuration, verified results, limitations. | Repository deliverable. |
| `.gitignore` | New: secrets, venv, caches, audit logs, local tool config. | Keep secrets and generated clutter out of git. |

Unchanged: `models/`, `preprocessing/`, `evaluation/`, `experiments/`,
`run_sweep.py`, `data/`, `results/experiment_results.jsonl`, and `results/synthetic_data/`
(verified byte-identical with git after the UI test run).

## Added files

| Path | Purpose |
|---|---|
| `knowledge_discovery/catalog.py` | Lists eligible DP synthetic datasets from the log (latest completed record, DP methods only); guarded loader. |
| `knowledge_discovery/summarizer.py` | Aggregate-only payload with k = 20 small-cell suppression and a privacy manifest. |
| `knowledge_discovery/prompts.py` | Versioned system prompt (`kd-prompt-v1`) and user-message template. |
| `knowledge_discovery/llm_client.py` | Live mode (Claude API via the official SDK, typed error handling, refusal handling) and labelled demo mode; audit records. |
| `knowledge_discovery/streamlit_page.py` | Dashboard page: dataset selection, guarantee panel, payload preview, generation, audit notice. |
| `analysis/verify_results.py` | Log integrity, de-duplication, configuration checks, re-evaluation of all metrics, TRTR and fairness references, aggregated tables, result figures (600 DPI PNG + SVG). |
| `analysis/knowledge_utility.py` | Offline agreement of payload statistics with the real training split (KU, Spearman ρ, top-1). |
| `tests/` (3 files, 32 tests) and `pytest.ini` | Extension privacy and error handling; real SDK against a mock server; pipeline smoke tests. |
| `figures/diagram_builder.py`, `figures/diagrams/` | 15 report diagrams as PNG (600 DPI), SVG and editable `.drawio`. |
| `figures/fig_res_*.png/.svg` | 13 result figures. |
| `results/verified/` | Verification outputs used by the report. |
| `constraints.txt` | Exact package versions recovered from the original venv, plus the new packages. |
| `run_dashboard.bat` | Windows launcher. |
| `.env.example` | Placeholder for `ANTHROPIC_API_KEY`. |
| `docs/screenshots/` | Dashboard evidence captured during testing. |
| `report/` | Report sources (`src/*.md`), build scripts, references, generated tables, `Diagrams/` folder, DOCX draft. |
| `docs/GUIDELINE_CHECKLIST.md`, `docs/DEMO_GUIDE.md`, `docs/HANDOVER.md` | Delivery documentation. |

## Findings surfaced while verifying (documented, not "fixed" in the original code)

1. The DP generator wrappers do not pass `random_seed` to snsynth/PrivBayes, so DP runs are not reproducible bit-for-bit.
2. Preprocessing (bin edges, vocabulary) is fitted on real data with `preprocessor_eps = 0`. The DP guarantee assumes this domain is public.
3. AIM's round cap must exceed about 0.9 × n_columns, or snsynth overspends ρ on the one-way marginals and fails.
4. 18 records occur in both the train and the test split (because the data contain duplicates), and the near-duplicate threshold is 0. Both weaken the empirical privacy metrics.
5. The README's "SIGMOD 2025" benchmark citation is Chen *et al.*, *Proc. ACM Manag. Data* 3(6), 2025 (SIGMOD '26).

These were left in place deliberately. Changing them would invalidate the saved
results, which the brief said to preserve. They are disclosed in the README and the
report, and listed as future work.
