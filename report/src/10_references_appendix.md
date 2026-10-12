# Appendix A: Reproducibility and Configuration {-}

**Environment.** Python 3.11 on Windows. Install with `pip install -r requirements.txt -c constraints.txt`. `constraints.txt` holds the exact versions of the original environment, so this command reproduces it.

**Commands (from the project root).**

```
# tests: 44 fast (43 pass, 1 live test skipped, ~30 s); 5 slow (~5 min)
venv\Scripts\python -m pytest -m "not slow"
venv\Scripts\python -m pytest -m slow
# re-evaluation, tables and figures from the saved outputs
venv\Scripts\python -m analysis.verify_results
venv\Scripts\python -m analysis.knowledge_utility
venv\Scripts\python -m analysis.llm_case_study
venv\Scripts\python -m analysis.quasi_identifier_risk
# diagrams (PNG 600 DPI, SVG, .drawio) and this document
venv\Scripts\python figures\diagram_builder.py
venv\Scripts\python report\finalize.py
# dashboard (http://localhost:8501) and the full sweep (hours)
run_dashboard.bat
venv\Scripts\python run_sweep.py
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
| `test_knowledge_discovery.py` | 18 | 18 passed | Fake client; no network; includes the quality-context disclosure test |
| `test_live_http_mock.py` | 6 | 6 passed | Real `anthropic` 1.13 SDK vs local mock server |
| `test_gemini_provider.py` | 16 | 15 passed, 1 skipped | Real `google-genai` 2.29 SDK vs local mock server; provider selection; the opt-in live test is skipped by default |
| `test_pipeline_smoke.py` (fast) | 4 | 4 passed | Shape, 41 configs, train-only fit, inverse binning |
| `test_pipeline_smoke.py` (slow) | 5 | 5 passed | AIM, MST, PrivBayes, CTGAN, TVAE end-to-end. AIM first **failed** with a 5-round cap (NaN, see {eq:aimbudget}) and passed with 20 rounds |
| Dashboard, comparative workflow (manual, 11 Oct.) | 9 pages | Working | PrivBayes run from the UI (4.5 s); log restored afterwards |
| Dashboard, all 10 feature areas (automated capture, 12 Oct.) | 14 screenshots | Working; no error element | PrivBayes ε = 3, seed 7 run from the UI; log and CSV restored afterwards (Appendix E) |
| Dashboard, Model Comparison (manual) | — | **Bug found, fixed** | Counted 43 runs; now 41 unique |
| Dashboard, LLM page (manual) | demo + missing key | Working | Audit flag bug found and fixed |
| Full suite, final run (12 Oct.) | 49 | 48 passed, 1 skipped | 298 s; saved results unchanged afterwards |
| Clean install from a fresh clone (12 Oct.) | — | Passed | `pip check` clean; fast suite 43 passed, 1 skipped |
| Secret scan of tracked files and full git history | — | Clean | Only fake test keys in `tests/` |
| Live Gemini API calls | 5 | **5 succeeded** | 11 Oct.: AIM and PrivBayes ε = 3, fact-checked (Table {tab:llmcase}); 12 Oct.: one for Fig. {fig:ss7} and two unintended (Section X); all `gemini-3.8-flash` |
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

# Appendix D: Supplementary Tables and Figures {-}

This appendix holds the supporting tables and result figures referred to in Sections IV, X, XIV and XV. They were moved here to keep the main text within the guideline's recommended number of figures and tables; their content is unchanged.

**Design tables.** Table {tab:req} traces each requirement to its implementation and evidence, and Table {tab:failures} lists how the LLM layer handles failures.

Table: {tab:req} Requirements traceability matrix

| ID | Requirement | Implemented in | Evidence | Status |
|---|---|---|---|---|
| FR1–FR2 | Profiling; train-only preprocessing | `preprocessing/` | `test_preprocessing_fit_uses_train_only`, `test_dataset_shape` | Met |
| FR3 | Five generators, common interface | `models/`, `experiments/runner.py` | 5 end-to-end smoke tests passed | Met |
| FR4–FR5 | Six evaluation dimensions; comparison | `evaluation/`, dashboard | 733/738 metrics re-computed exactly | Met |
| FR6 | LLM explanation of DP synthetic data | `knowledge_discovery/` | Mock-server tests via the real `google-genai` and `anthropic` SDKs; demo mode in UI; two real Gemini calls | Met (live verified for Gemini only) |
| PR1–PR2 | Exact guarantees; non-DP labelled | `models/*`, `privacy.py` | `config_checks.csv`: 41/41 pass | Met |
| PR3 | No original data to the LLM | `catalog.py` path guard | `test_original_rows_never_in_prompt`, `test_original_file_not_read…` | Met |
| PR4 | Small-cell suppression | `summarizer.py` (k = 20) | `test_small_cells_suppressed` | Met |
| PR5 | No DP claim for aggregates/LLM | UI notes, manifest, README | Manual review | Met |
| SR1–SR2 | No secrets in repository | `.env.example`, `.gitignore` | Secret scan of tracked files | Met |
| SR3 | Path guards | `catalog.py` | `test_refuses_original_dataset_and_non_dp` | Met |
| SR4 | API error handling | `llm_client.py` | HTTP 400/401/403/404/429/500, connection and safety-block tests | Met |
| XR1–XR2 | Payload shown; demo labelled | `streamlit_page.py` | Dashboard inspection; `test_demo_mode_is_labelled…` | Met |
| XR3, CR2 | Provenance, audit | Log, audit JSON | Audit records inspected | Met |
| CR3, TR3 | Assumptions disclosed | README, this report | Sections IX, XX | Met |
| TR1 | Reproducibility from outputs | `analysis/verify_results.py` | Re-evaluation report | Met (generators unseeded — see XX) |
| TR2 | No double counting | Dashboard fix, catalogue | 41 unique runs shown | Met (bug found and fixed) |

Table: {tab:failures} Failure modes of the LLM layer and their handling

| Failure | Handling |
|---|---|
| API key missing | Clear message pointing to `.env.example`; no request is attempted, and the audit records `user_message_sent_to_api = false` |
| Key rejected (400 invalid key, 401) or lacking permission (403) | Typed SDK exceptions mapped to actionable messages |
| Unknown or retired model (404) | Message naming the `KD_MODEL` / `KD_GEMINI_MODEL` setting and quoting the provider's reason (observed for real when `gemini-2.5-flash` was closed to new users) |
| Rate limit (429), server error or overload (5xx), network failure | SDK retries (three attempts in total), then shows a retry-later message (a real 503 "high demand" was observed during testing) |
| Request rejected (400) | Message with the API's own explanation, e.g. if the fallback parameter were unavailable for an account |
| Safety refusal or Gemini safety / prompt block | `stop_reason = refusal` reported as an error, not as an empty explanation |
| Truncation at `max_tokens` | Text kept and marked as truncated |
| Empty response | Reported as an error |

**Supplementary result tables.** Tables {tab:fidelity}, {tab:rarefair} and {tab:ku} give the fidelity, rare-pattern and fairness, and knowledge-utility results summarised in Section XIV.

{{INCLUDE:generated/table_fidelity.md}}

{{INCLUDE:generated/table_rarefair.md}}

{{INCLUDE:generated/table_ku.md}}

**Supplementary figures.** Fig. {fig:req} shows the requirements framework. Figs. {fig:3way}–{fig:radar} show the remaining result plots, and Fig. {fig:lr} repeats Fig. {fig:f1} for the Logistic Regression model.

![{fig:req} Requirements framework: six requirement families verified through tests, re-evaluation and payload inspection.](figures/diagrams/fig02b_requirements_framework.png){width=6.0in}

![{fig:3way} Privacy budget versus mean 3-way marginal TVD (lower is better).](figures/fig_res_03_epsilon_vs_3way_error.png){width=4.6in}

![{fig:mia} Privacy budget versus distance-based MIA AUC. Values near 0.5 for all methods, including non-DP baselines, indicate a weak attack rather than safety.](figures/fig_res_05_epsilon_vs_mia_auc.png){width=4.6in}

![{fig:rare} Privacy budget versus percentage of rare 2-way attribute combinations lost.](figures/fig_res_06_epsilon_vs_rare_loss.png){width=4.6in}

![{fig:fair} Privacy budget versus demographic-parity difference (sex) of a Logistic Regression trained on synthetic data. Real-data reference: 0.169.](figures/fig_res_07_epsilon_vs_dp_difference.png){width=4.6in}

![{fig:runtime} Fit runtime versus privacy budget (log–log). Non-DP baselines shown at 300 epochs.](figures/fig_res_08_runtime.png){width=4.6in}

![{fig:ku} Knowledge utility (left) and Spearman rank agreement of subgroup target rates (right) between LLM payload statistics and the real training split.](figures/fig_res_12_knowledge_utility.png){width=6.2in}

![{fig:pu} Empirical privacy–utility scatter (each point is one run).](figures/fig_res_09_privacy_utility_scatter.png){width=4.6in}

![{fig:heat} Metric heatmap at ε = 3 (DP) and for non-DP baselines; cell text shows raw values, colour is column-normalised. Candidate for the appendix.](figures/fig_res_11_heatmap_eps3.png){width=6.3in}

![{fig:radar} Radar comparison at ε = 3 using bounded "higher is better" transforms of the raw metrics (no min–max rescaling).](figures/fig_res_13_radar_eps3.png){width=3.8in}

![{fig:lr} Privacy budget versus TSTR F1 (Logistic Regression).](figures/fig_res_02_epsilon_vs_f1_logreg.png){width=4.4in}

The full per-run results (41 rows) are in `results/verified/runs_deduplicated.csv`. The aggregated means and standard deviations behind the result tables are in `results/verified/aggregated_by_method_epsilon.csv`.

# Appendix E: Dashboard Evidence {-}

Figs. {fig:ss1}–{fig:ss7} are genuine screenshots of the running dashboard, captured on 12 October 2026 at 2,000 px width (full index and uncropped originals: `evidence/screenshots/`). Figs. {fig:ss2} and {fig:ss3} come from a demonstration run started in the interface (PrivBayes, ε = 3, seed 7) that is **not** one of the 41 reported runs; its log record and data file were removed afterwards. Fig. {fig:ss4} was captured on the published log. Tall pages are shown from the top and cropped at a blank line.

![{fig:ss1} Dataset page: the bundled 3,000-record UCI Adult sample, its column profile (52 duplicate rows, 3 columns with missing values) and the target/sensitive-attribute selection.](report/figures/screens/02a_dataset_overview.png){width=5.6in}

![{fig:ss2} Model selection and generation: PrivBayes at ε = 3 (pure DP, δ = 0) run from the interface, with the measured fit and generation times.](report/figures/screens/03_model_selection_generation.png){width=5.6in}

![{fig:ss3} Privacy page for the same run: the formal guarantee generated from the code, the distance-based membership attack (AUC ≈ 0.51) and the near-duplicate check (threshold 0, see Section XIV).](report/figures/screens/07_privacy_evaluation.png){width=5.6in}

![{fig:ss4} Model Comparison on the published log: 41 unique completed runs from 43 records, with the duplicate notice (top of the page).](report/figures/screens/09_model_comparison.png){width=5.6in}

![{fig:ss5} LLM knowledge-discovery page: DP-only dataset list, guarantee from the log, duplicate-record notice, provider and mode controls, and the switch that withholds the real-data quality metrics.](report/figures/screens/10a_llm_page_dataset_selection.png){width=5.6in}

![{fig:ss6} Demo mode for AIM ε = 3: rule-based template text labelled **not** generated by an LLM. Note the spurious education–race association reported from the synthetic data.](report/figures/screens/10c_llm_demo_output.png){width=5.6in}

![{fig:ss7} Live mode, provider Gemini, PrivBayes ε = 3: a **real LLM response** (`gemini-3.8-flash`, 12 Oct. 2026, 24.6 s), shown with the provider, model and stop reason and a hypothesis warning (top of the response).](report/figures/screens/10d_llm_live_gemini_output.png){width=5.6in}

**Excerpt of a real LLM response.** The lines below are quoted unedited from the Gemini response for AIM ε = 3 (seed 42; payload SHA-256 `4e62da3d…`; 6,277 input and 1,678 output tokens; 30.6 s). This **is** LLM output. The first quotation is the reversed gender gap discussed in Section XIV; the second is the suppression misreading.

> *Key patterns — Sex:* "In this synthetic distribution, females have a slightly higher `>50K` rate (25.4%) than males (23.3%)."
>
> *Limitations — Suppression:* "Aggregates suppressed cells below a count of 8 […]"
>
> *Limitations — Privacy boundary:* "neither this summary nor the language model confers any additional privacy guarantees beyond the generator's original claim."

From the PrivBayes ε = 3 response (6,427 input and 1,815 output tokens; 29.5 s):

> "`12th` grade education has an implausibly high positive rate of **67.4%** (1.9% share), exceeding `Bachelors` (**37.3%**) […] These anomalies likely reflect DP noise in small slices."

Both full responses are in the repository at `evidence/llm_responses/`.

# Data Availability Statement {-}

The datasets generated and analysed during the current study are available in the project's GitHub repository, https://github.com/adithyasr28-afk/dp-genai-secure-knowledge-discovery. These comprise the 41 synthetic datasets, the experiment log, the verified result tables and the analysis code. The source dataset is a 3,000-record sample of the UCI Adult dataset [@becker1996adult], available from the UCI Machine Learning Repository (doi: 10.24432/C5XW20) under a CC BY 4.0 licence; the sample used is included in the repository as `data/example_dataset.csv`.

# Acknowledgment {-}

The authors thank Dr M Rajasekhara Babu, School of Computer Science and Engineering, Vellore Institute of Technology, for guidance in the BCSE318L Data Privacy course. An AI assistant (Claude, Anthropic) was used to help write and test code, verify the logged results and draft this report; every number was checked against the project repository, and the authors take responsibility for the content.

# References {-}

{{REFERENCES}}
