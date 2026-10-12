# Generative AI Knowledge Discovery Layer

## Purpose and Boundaries

The knowledge-discovery layer answers one question: *what does this DP synthetic dataset suggest, and how far can the suggestion be trusted?* It is an extension added in this iteration (`knowledge_discovery/`). It is reached from a *Workspace* switch in the dashboard sidebar, so it works from saved results without loading the original data.

Its boundaries are explicit:

- it is **not** a trained or fine-tuned LLM;
- it is **not** a retrieval-augmented generation system;
- it gives **no** DP guarantee of its own.

It is a single, auditable LLM call over aggregate statistics.

## Workflow

Fig. {fig:kd} shows the implemented workflow.

1. **Catalogue.** The layer reads `results/experiment_results.jsonl` and keeps, for each run identifier, the latest *completed* record. It lists only records whose method is AIM, MST or PrivBayes and whose `is_differentially_private` flag is true — 35 datasets. The ε, δ, mechanism and AIM round cap are taken from the log, so the guarantee shown is the one the generator actually reported. For the two re-run configurations, the UI states that two records exist and that the latest one, which produced the CSV on disk, is used.
2. **Guarded loading.** The resolved file path must lie directly inside `results/synthetic_data/`. Paths in the original data folder and non-DP methods raise an `IneligibleDatasetError`.
3. **Aggregate summary.** For the selected dataset the summariser computes:
   - one-way marginals: mean, standard deviation, deciles and zero share for numerical columns; top-8 level shares for categorical columns;
   - the positive-target rate overall and per level of every categorical column and per quartile of every numerical column;
   - the ten strongest categorical associations (Cramér's V) and numerical correlations (Pearson);
   - the run's own fidelity, best TSTR F1 and MIA AUC, with a reading guide;
   - a privacy manifest.

   Every group with fewer than $k = 20$ synthetic rows is suppressed. Values are rounded to three decimals. For AIM at ε = 3, 8 cells were suppressed and the user message was about 14,900 characters long, with no row-level content.
4. **Prompting.** A fixed system prompt (`kd-prompt-v1`, Appendix C) instructs the model to:
   - write five sections: overview, key patterns, relationships, hypotheses, and limitations;
   - base every claim on the given numbers;
   - phrase insights as hypotheses for validation on governed real data;
   - treat the tagged summary as data, not instructions;
   - never describe individuals or claim extra privacy.
5. **Generation.**
   - *Live mode* calls the selected provider. **Gemini** is called through Google's official `google-genai` SDK [@geminiapi] (`models.generate_content`, model alias `gemini-flash-latest`, system instruction, 16,000 output tokens, three attempts on 429/5xx). **Claude** is called through the Anthropic Messages API [@anthropicapi] with `claude-opus-5-5`, medium effort, and the server-side refusal fallback. `KD_PROVIDER=auto` uses Claude when its key is present and Gemini otherwise. Keys are read from `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` in the environment or a git-ignored `.env` file, and travel only in the HTTP authentication header.
   - *Demo mode* builds a deterministic template from the same summary. It is labelled in the UI, the output and the audit record as **not** LLM output.
6. **Transparency and audit.** The UI shows the exact system prompt and user message before generation, and offers the summary for download. Each request writes an audit record with the prompt version, a SHA-256 hash of the payload, the mode, the provider, the model version that actually answered, stop reason, token usage, and whether a request was actually sent.

![{fig:kd} Knowledge-discovery workflow (implemented). The original dataset has no path into the pipeline.](figures/diagrams/fig08_llm_knowledge_discovery_workflow.png){width=6.3in}

## Payload Design Rationale

Why aggregates, and why these aggregates? Sending the synthetic rows themselves would be *privacy-neutral* — DP synthetic data are already safe to post-process. It would still be a poor design, for four reasons.

1. **Arithmetic.** LLMs are unreliable at computing statistics over thousands of rows in a prompt, so the explanation would rest on arithmetic the model cannot do well.
2. **Size.** Row-level prompts are roughly a hundred times larger, which costs more and runs into context limits.
3. **Habit.** If the interface ever accepted non-DP or real data — through a configuration error or a later change — a row-level payload would leak individuals directly, whereas an aggregate payload degrades gracefully.
4. **Context.** Aggregates let the payload carry the *quality context* the model needs to qualify its claims: the dataset's own fidelity, utility and MIA metrics, together with a reading guide.

The chosen statistics mirror what an analyst would compute first:

- the distribution of each attribute;
- how the target varies across groups;
- which attributes move together.

The positive-target rate by group is the core of the knowledge-discovery question, "who has high income, and how sure are we?". Group shares of rows are included next to each rate so that the model can see when a rate rests on a small group. Only the ten strongest associations are sent, because they dominate any narrative the model would write.

## Failure Modes and How They Are Handled

Table {tab:failures} lists how the layer behaves when something goes wrong. Every row is exercised by a test (Appendix B).

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

## Verification Status of the LLM Component

The verification status is stated per provider.

**Verified with real API calls (Gemini, 11 October 2026):**

- two live requests succeeded — AIM ε = 3 (scripted) and PrivBayes ε = 3 (from the dashboard UI, Fig. {fig:ss4}). The alias `gemini-flash-latest` was served by `gemini-3.8-flash`;
- each used about 6,300 input, 1,700–1,800 output and 2,600–2,900 internal "thinking" tokens and took about 30 s;
- both returned the five requested sections, framed insights as hypotheses and stated that the LLM adds no privacy guarantee;
- the outputs were fact-checked claim by claim against the payload and the real training split (Section XIV, Table {tab:llmcase}); the unedited texts are in `docs/llm_evidence/` and an excerpt is in Appendix D.

**Verified by execution against a local mock server (both providers):**

- request construction through the real `google-genai` 2.29 and `anthropic` 1.13 SDKs: model, system instruction, token limit, (for Claude) beta flag and fallback parameter, and the key present only in the authentication header;
- the absence of any of the first 300 original rows in the request body;
- that the original file is never opened;
- small-cell suppression;
- clear errors for a missing key and for HTTP 400, 401, 403, 404, 429 and 500, connection failure, refusal, safety blocks, truncation and empty responses;
- the demo-mode path in the running dashboard.

**Not verified:**

- a live Claude request (no Anthropic API key was available; a Claude Pro chat subscription does not include API credits);
- explanation quality beyond the two Gemini responses, and stability across repeated calls — LLM output is not deterministic, so a repeat call may phrase or select claims differently.

Real LLM text appears only in Section XIV and Appendix D, where it is labelled with the provider, model and date. The demo excerpt in Appendix D is template text.

## Knowledge Utility

Post-processing guarantees that the explanation is no *less* private than the DP dataset. It says nothing about whether the explanation is *true*. The layer therefore needs a measure of how faithfully its inputs reflect the population. Following the idea of epistemic parity [@rosenblatt2023], an offline evaluation (`analysis/knowledge_utility.py`) compares the target-rate cells that appear in both summaries — synthetic $s_{\mathrm{syn}}$ and real training split $s_{\mathrm{real}}$ — over the set $C$ of shared (column, level) pairs:

$$\mathrm{KU} \;=\; 1-\frac{1}{|C|}\sum_{(c,v)\in C}\big|\,s_{\mathrm{syn}}(c,v)-s_{\mathrm{real}}(c,v)\,\big| $$ {#eq:ku}

Two further measures complement KU: the Spearman rank correlation ρ between the two sets of group rates, and *top-1 agreement*, the share of columns whose highest-rate level is the same in both. These are evaluation-only quantities: they consult the real data and must never be computed inside the released pipeline. Results are reported in Section XIV.

## Controlled Knowledge Dissemination

Dissemination is controlled at four points:

- what may be summarised — DP datasets only;
- what may leave the machine — suppressed and rounded aggregates;
- how the output is framed — hypotheses with an explicit limitations section;
- what is recorded — audit records.

A production deployment would add role-based access to the page, retention limits for audit records, and a contractual position with the LLM provider on data use and region (Section XVIII).

# Explainability, Transparency, and Trust Assessment

## Explainability Mechanisms

Explainability here means that a reviewer can trace every claim back to its evidence. Five mechanisms provide this (Fig. {fig:trust}):

1. **Formal statements** generated from code: $(\varepsilon,\delta)$, mechanism name, and pure versus approximate DP.
2. **Empirical privacy evidence:** MIA AUC, TPR at FPR 0.1, and distance to closest record.
3. **Quality evidence:** fidelity, utility, rare-pattern and fairness metrics.
4. **Provenance:** run identifier, seed, configuration, disclosed deviations, and the duplicate policy.
5. **LLM transparency:** the shown payload, prompt version and audit hash.

The system shows these indicators side by side, in line with model-card and datasheet practice [@mitchell2019; @gebru2021].

![{fig:trust} Explainability, transparency and trust assessment layer.](figures/diagrams/fig09_explainability_trust_layer.png){width=6.2in}

## What Can and Cannot Be Explained

DP changes what explanation means. Some things *can* be explained precisely: the mechanism, the budget, which statistics were measured (for MST, which tree edges), and how the synthetic data compare with the real data on aggregate metrics. Other things *cannot* be explained, by design:

- which real individuals influenced a given synthetic record — there is no such correspondence;
- why a specific synthetic record has particular values, beyond "it was sampled from the fitted model".

Two consequences follow. Explanations must operate at the level of the population, and statements that sound individual-level ("a 45-year-old female executive earns…") should be read as statements about a model, not about a person. The system prompt asks the LLM never to describe individuals for this reason.

Explaining the LLM's *own* reasoning is out of scope. The layer offers *input transparency* — the exact payload and prompt are shown — and *output framing* — required sections and a hypothesis register. It does not offer insight into the model's internals.

## A Reviewer's Workflow

The intended use of the evidence is a short review before acting on any LLM-generated insight:

1. Check the guarantee panel: ε, δ, pure or approximate DP, and the round cap if any.
2. Check the quality context: is the 3-way TVD low and the utility retention high for this dataset?
3. For each claimed pattern, find the supporting numbers in the shown payload.
4. For patterns involving protected attributes, or patterns that will drive a decision, request the corresponding statistic from the custodian on the governed real data.
5. Record the decision.

The audit record links the explanation to its exact input through the SHA-256 payload hash.

## Transparency Reporting

A release published from this framework should carry a short transparency report. All of its fields are already produced by the code:

- dataset and purpose;
- mechanism and guarantee, including the domain assumption;
- ε, δ and the composed total if several releases exist;
- fidelity, utility, fairness and rare-pattern summaries against the stated thresholds;
- empirical attack results *with their stated weakness*;
- known artefacts, such as the spurious associations found by the knowledge-utility check;
- a contact for questions.

This mirrors the model-card idea [@mitchell2019] applied to a data release, and NIST's call to state the unit of privacy and the assumptions [@near2025].

## Trust Assessment

The section plan calls for a trust-score equation. A single weighted score would hide trade-offs and invite gaming, so the trust assessment is defined as an *evidence vector* with explicit acceptance thresholds $\tau$ chosen by the data owner:

$$\mathbf{T}=\big(\varepsilon,\ \delta,\ \mathrm{AUC}_{\mathrm{MIA}},\ 1-\mathrm{TVD}_3,\ R_{F1},\ \mathrm{KU},\ \Delta_{\mathrm{DP}}\big),\qquad \mathrm{accept}\iff \bigwedge_j\, T_j \trianglelefteq \tau_j $$ {#eq:trust}

Here $\trianglelefteq$ means "no worse than" in each component's direction. For example, with $\varepsilon\le3$, $|\mathrm{AUC}-0.5|\le0.05$, $R_{F1}\ge 75\%$ and $\mathrm{KU}\ge0.9$, the AIM ε = 3 dataset would pass, while the MST ε = 3 datasets would fail on $R_{F1}$ and KU (Section XIV). Adding a fairness threshold such as $\Delta_{\mathrm{DP}}\le0.2$ would reject the AIM dataset as well, since its value is 0.48 against 0.17 for a model trained on real data. This shows why the components must be inspected together. The thresholds above are illustrative and were not elicited from stakeholders.

## Auditability

Auditability rests on the append-only JSON-lines experiment log, the per-request audit records, and version control. The verification script shows the log is auditable in practice:

- it identified the two duplicate run identifiers;
- it confirmed that every configuration matches its declared guarantee;
- it reproduced 733 of 738 metric values exactly from the saved data.

The audit trail also surfaced a defect: the original dashboard counted 43 runs instead of 41. That defect was fixed.
