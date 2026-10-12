# Baseline audit (Phase 1)

- **Date:** 2026-10-12.
- **Auditor:** Claude (Claude Code session), working on the team's behalf.
- **Scope:** the repository, the report draft and its sources, and the three guideline documents plus the course roster.
- **Changes during this phase:** none to the code, the experiment outputs or the report sources. Only `project_docs/` was added and the report baseline was copied to `report/archive/`.

## 1. Repository state

| Item | Finding |
|---|---|
| Local path | `C:\Users\adith\Desktop\Data Privacy Proj\dp-genai-secure-knowledge-discovery` |
| Remote | https://github.com/adithyasr28-afk/dp-genai-secure-knowledge-discovery (public) |
| Branch at start | `main` = `origin/main` @ `ef727a396f9bdceb3304d17e17e377a2090ef0a0`, clean |
| Working branch | `report-finalisation` (created from `ef727a3`) |
| History | 9 commits. `052d334` imports the original ZIP unchanged (minus `venv/` and `__pycache__/`); later commits add the extension, verification, report and docs |
| Tracked files | 197 (≈ 25 MB), with `.git` at ≈ 20 MB. Largest are 600-DPI PNG diagrams (≤ 0.53 MB) and the synthetic CSVs (≤ 0.36 MB each) |
| Original vs repo | `models/`, `preprocessing/`, `evaluation/`, `experiments/`, `data/`, `results/synthetic_data/` and `results/experiment_results.jsonl` are **byte-identical** to the original ZIP's `project/` folder (checked with `diff -rq` and `cmp`). `app.py` differs only by the documented extension switch and two bug fixes |

## 2. Credential and sensitive-information check

| Check | Result |
|---|---|
| Real-key patterns in **all git history** (`git log --all -p`): Google `AQ.`/`AIza…`, Anthropic `sk-ant-api…`, OpenAI `sk-proj-`, GitHub `ghp_` | **0 matches** |
| Tracked files matching `.env`/secret/key/credential/`.pem`/`venv`/`__pycache__` | Only `.env.example` (placeholders) |
| `.env` | Exists locally and is git-ignored. It holds a real Gemini key, which was **pasted into a chat session on 2026-10-11 → must be rotated** (👤) |
| Fake keys in tests | `sk-ant-test-…` and `AQ.test-local-mock-…`, clearly fake |
| Faculty photo and e-mail | In the official template and the built DOCX. Both are git-ignored (`report/template/`, `report/*.docx`) by an earlier team decision |
| Personal data | The dataset is a public, de-identified UCI Adult sample. No team personal data are in the repo apart from reg. nos. in `report/build_report.py` |
| LLM audit records `results/llm_insights/*.json` | git-ignored. They contain prompts (aggregates only) and responses, **no keys** (checked) |

## 3. Experiments (verified from the actual files)

| Item | Finding |
|---|---|
| Log `results/experiment_results.jsonl` | **43 records**, all `status = completed` |
| Unique `run_id`s | **41**. Two duplicates: `adult_example_AIM_eps3.0_seed42` ×2 and `adult_example_PrivBayes_eps3.0_seed42` ×2 |
| Records per method | AIM 6, MST 15, PrivBayes 16, CTGAN 3, TVAE 3 |
| Unique runs per method | AIM 5 (seed 42 only), MST 15, PrivBayes 15, CTGAN 3, TVAE 3 |
| Synthetic CSVs | 41 present, each with the logged row count; no orphan CSVs |
| Dataset | `data/example_dataset.csv`: UCI Adult sample, 3,000 rows × 14 columns; 80/20 stratified split (2,400 / 600), seed 42 |
| Configurations vs code | 41/41 privacy configurations consistent (`results/verified/config_checks.csv`) |
| Re-evaluation | 733/738 logged metric values recomputed exactly. The other 5 are MIA AUC, all differing by ≤ 2.8 × 10⁻⁶ (`verification_report.json`) |
| Duplicate handling | The original Model Comparison page counted 43 runs. Fixed to "latest completed record per run_id" (41) |

## 4. Mechanisms actually implemented (from the code)

| Method | Library | Guarantee in code | Notes |
|---|---|---|---|
| AIM | smartnoise-synth (`Synthesizer.create("aim")`) | (ε, δ)-DP, δ = 1e-5 (zCDP accounting) | `rounds = min(16·d, 60)`, so it is capped at 60 instead of 224. `preprocessor_eps = 0` |
| MST | smartnoise-synth (`"mst"`) | (ε, δ)-DP, δ = 1e-5 | `preprocessor_eps = 0` |
| PrivBayes | `synthetic_data_generation` (`synthesis.synthesizers.privbayes`), a third-party port | pure ε-DP (δ = 0). The code splits ε as β = 0.3 for structure (exponential mechanism) and 0.7 for the CPTs (truncated Laplace, sensitivity 2/n) | The record count n is treated as public. The `numpy.product` shim is disclosed |
| CTGAN | `ctgan` | **none** (`is_differentially_private = False`) | 300 epochs |
| TVAE | `ctgan.TVAE` | **none** | 300 epochs |

**Seeding:** the DP wrappers do not forward `random_seed` to the libraries, so DP runs are not bit-reproducible. CTGAN/TVAE call `set_random_state`.

## 5. Features: what runs

| Feature | Status at baseline | Evidence |
|---|---|---|
| Streamlit dashboard, 9 original pages | Runs (`run_dashboard.bat 8517`, launched 2026-10-12) | Previous session; browser preview |
| LLM Knowledge Discovery page | Runs. Demo mode, missing-key path and **live Gemini** all exercised | `docs/screenshots/`, `results/llm_insights/` |
| Gemini live calls | 2 successful (2026-10-11 22:49:48 AIM ε=3; 22:52:31 PrivBayes ε=3). The model requested was `gemini-flash-latest`; the response carried the served version `gemini-3.8-flash` | audit JSONs (`is_llm_output: true`, `ok: true`, request ids) |
| Earlier live attempts | 2 failures "ANTHROPIC_API_KEY is not set" (no request sent) and 1 Gemini 404 (`gemini-2.5-flash` retired) | audit JSONs (`is_llm_output: false`) |
| Claude live calls | **None** succeeded; there is no Anthropic key | — |
| Tests | Fast suite: 42 passed, 1 skipped (opt-in live test). Full suite re-run in this phase: see §8 | `pytest` |
| Report build | `report/build_report.py` works. During this audit the default output DOCX was **locked by another process (probably open in Word)**, so the build failed at the save step | Phase 1 run |

## 6. Report baseline (`report/archive/v1_2026-10-12/`)

| Item | Finding |
|---|---|
| Format | Official template front matter merged with a pandoc body; 65 pages in the PDF preview |
| Body layout | **Single column**. The template requires two columns (`w:cols num=2` in template sections 2–3) |
| Front matter | Cover: Team ID, title and reg. nos. 23BCE2114 / 23BCE2133. **Names, e-mails and faculty are placeholders**; the author line is a placeholder |
| Drafting notes | A 555-word "Draft Status and Review Notes" section plus 8 `[TEAM]` and 3 `[CONFIRM]` markers are inside the manuscript |
| Words | ≈ 20,900 in total. Abstract 240, Executive Summary 689. **17 of 22 sections are below the topic plan's minimum** (see compliance matrix C1–C22) |
| Figures / tables | 30 / 20 (recommended 10–15 / 8–12) |
| Equations | 15, native OMML |
| References | 63 cited, all defined; ≈ 21% journal articles; **5 `[VERIFY]`** |
| LLM claims | Gemini verified live (2 calls, fact-checked in Table XIV); Claude correctly described as not tested live |

## 7. Existing evidence

- `docs/screenshots/`:
  - `01_llm_page_dataset_selection.jpg`;
  - `02_llm_page_demo_output.jpg`;
  - `03_llm_page_live_gemini_privbayes.jpg`;
  - `06_model_comparison_deduplicated.jpg`;
  - `07_model_comparison_table.jpg`.

  Several are cropped because the browser pane was partly hidden. The main pages 1–9 (dataset … rare patterns) have **no** screenshots.
- `docs/llm_evidence/`: the two unedited Gemini responses.
- `results/verified/`: verification, aggregation, knowledge-utility and LLM fact-check CSVs.
- `figures/` (13 result plots) and `figures/diagrams/` (15 diagrams: PNG 600 DPI, SVG, `.drawio`).
- Videos: none.

## 8. Test run in this phase

`venv\Scripts\python -m pytest -q` (full suite including the slow tests): **see §8 result appended at the end of Phase 1.**

## 9. Gaps carried into later phases

1. Two-column layout; author block with 3 students and the faculty; remove template slots 4 and 5; remove drafting notes (Phase 5).
2. Word counts for 17 sections (Phase 5).
3. Reduce figures/tables in the body; move the rest to appendices (Phase 5).
4. References: from 63 to ≤ 50, resolve 5 `[VERIFY]`, raise the journal share where verifiable (Phase 5).
5. Full-resolution screenshots for all 10 feature areas (Phase 4).
6. `project_docs/` reproduction guide, claim verification, changelog, final audit (Phases 2–6).
7. The repository structure requested in the brief (`evidence/`, `diagrams/`, `project_docs/`) without breaking imports (Phase 3).
8. Missing human inputs: the **third team member** (the roster lists only 23BCE2114 and 23BCE2133), all student names and e-mails, the contribution allocation, the similarity check, the videos, and rotating the Gemini key.
