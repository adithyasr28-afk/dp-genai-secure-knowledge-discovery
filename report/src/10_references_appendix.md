# References {-}

{{REFERENCES}}

# Appendix A: Reproducibility and Configuration {-}

**Environment.** Python 3.11 on Windows. Install with `pip install -r requirements.txt -c constraints.txt`. `constraints.txt` holds the exact versions of the original environment, so this command reproduces it.

**Commands (from the project root).**

```
venv\Scripts\python -m pytest -m "not slow"        # 43 tests: 42 pass, 1 live test skipped (~25 s)
venv\Scripts\python -m pytest -m slow              # 5 end-to-end generator runs (~3 min)
venv\Scripts\python -m analysis.verify_results     # de-duplication, checks, re-evaluation, figures
venv\Scripts\python -m analysis.knowledge_utility  # payload vs real-data agreement
venv\Scripts\python -m analysis.llm_case_study     # fact-check of the real Gemini responses
venv\Scripts\python figures\diagram_builder.py     # diagrams: PNG (600 DPI), SVG, .drawio
venv\Scripts\python report\build_report.py         # this document
run_dashboard.bat                                  # dashboard at http://localhost:8501
venv\Scripts\python run_sweep.py                   # re-run all 41 configurations (hours)
```

**Preprocessing parameters.**

- rare threshold 1%;
- 10 quantile bins;
- spike threshold 30%;
- split 80/20, stratified on income, seed 42;
- vocabulary sizes after grouping, including the `__RARE__`/`__MISSING__` tokens: workclass 8, education 14, marital_status 7, occupation 14, relationship 7, race 5, sex 3, native_country 4, income 3;
- spike values: education_num = 9, capital_gain = 0, capital_loss = 0, hours_per_week = 40.

**LLM settings.**

- provider `auto` (`KD_PROVIDER`: `auto` | `gemini` | `anthropic`);
- Gemini: model `gemini-flash-latest` (`KD_GEMINI_MODEL`; served by `gemini-3.8-flash` on 11 Oct. 2026), `google-genai` 2.29.0, timeout 180 s, 3 attempts on 429/5xx, key `GEMINI_API_KEY` or `GOOGLE_API_KEY`;
- Claude: model `claude-opus-5-5` (`KD_MODEL`), effort `medium` (`KD_EFFORT`), server-side refusal fallback on (`KD_SERVER_FALLBACK=1`), key `ANTHROPIC_API_KEY`;
- `max_tokens` 16,000 (`KD_MAX_TOKENS`, both providers);
- minimum cell count k = 20;
- statistics rounded to 3 decimals;
- prompt version `kd-prompt-v1`.

# Appendix B: Verification Evidence {-}

Table {tab:verify} compares each logged metric with its value recomputed from the saved synthetic data. Table {tab:dups} shows both records of the two duplicated configurations. Table {tab:tests} lists the test results.

{{INCLUDE:generated/table_verify.md}}

{{INCLUDE:generated/table_dups.md}}

Table: {tab:tests} Test results (executed October 2026 in the verification environment)

| Suite / check | Items | Result | Notes |
|---|---|---|---|
| `test_knowledge_discovery.py` | 17 | 17 passed | Fake client; no network |
| `test_live_http_mock.py` | 6 | 6 passed | Real `anthropic` 1.13 SDK vs local mock server |
| `test_gemini_provider.py` | 16 | 15 passed, 1 skipped | Real `google-genai` 2.29 SDK vs local mock server; provider selection; the opt-in live test is skipped by default |
| `test_pipeline_smoke.py` (fast) | 4 | 4 passed | Shape, 41 configs, train-only fit, inverse binning |
| `test_pipeline_smoke.py` (slow) | 5 | 5 passed | AIM, MST, PrivBayes, CTGAN, TVAE end-to-end. AIM first **failed** with a 5-round cap (NaN, see {eq:aimbudget}) and passed with 20 rounds |
| Dashboard, comparative workflow (manual) | 9 pages | Working | PrivBayes run from the UI (4.5 s); log restored afterwards |
| Dashboard, Model Comparison (manual) | — | **Bug found, fixed** | Counted 43 runs; now 41 unique |
| Dashboard, LLM page (manual) | demo + missing key | Working | Audit flag bug found and fixed |
| Secret scan of tracked files | — | Clean | Only fake test keys in `tests/` |
| Live Gemini API calls | 2 | **2 succeeded** | AIM and PrivBayes ε = 3; `gemini-3.8-flash`; ≈ 30 s each; fact-checked (Table {tab:llmcase}) |
| Live Claude API call | — | **Not tested** | No Anthropic API key available |

# Appendix C: Prompt Template {-}

The system prompt below (version `kd-prompt-v1`, `knowledge_discovery/prompts.py`) is sent unchanged with every live request. The user message is the aggregate summary wrapped in `<aggregate_summary>` tags, followed by the optional analyst focus, which is truncated to 500 characters.

```
{{SYSTEM_PROMPT}}
```

**Payload schema** (top-level keys):

- `dataset` — run identifier, generator, mechanism, ε, δ, formal statement, notes, rows, columns, representation note;
- `numerical_marginals`;
- `categorical_marginals`;
- `target_analysis` — overall rate; rate by level or quartile with row shares;
- `strongest_categorical_associations`;
- `strongest_numerical_correlations`;
- `generator_quality_context`;
- `privacy_manifest`.

# Appendix D: Dashboard Evidence {-}

The screenshots were captured from the running dashboard during testing. Figs. {fig:ss1}–{fig:ss4} show the extension page, a demo-mode output, the corrected Model Comparison page and a real Gemini response. The browser pane was partly hidden, so some are cropped on the right. **[TEAM: replace with full-resolution screenshots and add the execution videos the guidelines request.]**

![{fig:ss1} LLM knowledge-discovery page: DP dataset selection, guarantee from the log, duplicate-record notice, demo-mode warning (no API key configured).](evidence/screenshots/2026-10-11_initial/01_llm_page_dataset_selection.jpg){width=5.5in}

![{fig:ss2} Demo-mode output for AIM ε = 3. This is rule-based template text, **not** LLM output. Note the spurious education–race association reported from the synthetic data.](evidence/screenshots/2026-10-11_initial/02_llm_page_demo_output.jpg){width=5.5in}

![{fig:ss3} Model Comparison after the de-duplication fix: 41 unique runs from 43 records.](evidence/screenshots/2026-10-11_initial/06_model_comparison_deduplicated.jpg){width=5.5in}

![{fig:ss4} Live mode with provider Gemini on PrivBayes ε = 3: a **real LLM response** (`gemini-3.8-flash`, 11 Oct. 2026), shown with the provider, model and a hypothesis warning.](evidence/screenshots/2026-10-11_initial/03_llm_page_live_gemini_privbayes.jpg){width=5.5in}

**Excerpt of a real LLM response.** The lines below are quoted unedited from the Gemini response for AIM ε = 3 (seed 42; payload SHA-256 `4e62da3d…`; 6,277 input and 1,678 output tokens; 30.6 s). This **is** LLM output. The first quotation is the reversed gender gap discussed in Section XIV; the second is the suppression misreading.

> *Key patterns — Sex:* "In this synthetic distribution, females have a slightly higher `>50K` rate (25.4%) than males (23.3%)."
>
> *Limitations — Suppression:* "Aggregates suppressed cells below a count of 8 […]"
>
> *Limitations — Privacy boundary:* "neither this summary nor the language model confers any additional privacy guarantees beyond the generator's original claim."

From the PrivBayes ε = 3 response (6,427 input and 1,815 output tokens; 29.5 s):

> "`12th` grade education has an implausibly high positive rate of **67.4%** (1.9% share), exceeding `Bachelors` (**37.3%**) […] These anomalies likely reflect DP noise in small slices."

Both full responses are in the repository at `evidence/llm_responses/`.

# Appendix E: Supplementary Results {-}

Fig. {fig:lr} repeats Fig. {fig:f1} for the Logistic Regression model.

![{fig:lr} Privacy budget versus TSTR F1 (Logistic Regression). Candidate for removal if the figure count must be reduced.](figures/fig_res_02_epsilon_vs_f1_logreg.png){width=4.4in}

The full per-run results (41 rows) are in `results/verified/runs_deduplicated.csv`. The aggregated means and standard deviations behind Tables {tab:utility}–{tab:rarefair} are in `results/verified/aggregated_by_method_epsilon.csv`.

# Appendix F: Reference Verification Status {-}

The reference list was drafted with care, but not every entry could be checked online. Each entry in `report/references.py` records its status, and the team should spot-check DOIs and page ranges before submission. Entries marked **[VERIFY]** in the reference list are those for which a DOI or page range could not be confirmed. The status categories are:

- **Checked online during drafting (19):** title, authors, venue and identifiers confirmed against the publisher's or an official record.
- **Standard metadata (39):** long-established works, not re-checked online.
- **Flagged [VERIFY] (5):** a detail could not be confirmed.

Only the cited subset appears in the reference list.
