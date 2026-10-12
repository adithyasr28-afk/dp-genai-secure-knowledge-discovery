# Proposed Differential Privacy-Enhanced Generative AI Framework

## Architecture Overview

The framework has three layers (Fig. {fig:arch}). Each layer only consumes the outputs of the layer before it.

- **L1 — data and preparation.** Profiles the dataset, assigns column roles, performs a stratified 80/20 split (seed 42), and fits all preprocessing parameters on the training split only. It emits two views of the same data: a *discretised* view for the marginal-based DP generators, and a *continuous* view for CTGAN and TVAE. The fitted parameters (bin edges, spike values, vocabularies, medians) are serialisable for provenance.
- **L2 — synthesis.** Wraps five generators behind one `BaseSynthesizer` interface. Each wrapper reports `is_differentially_private` and `privacy_params()`, so the dashboard labels every run correctly by construction. DP output is mapped back to continuous values by sampling uniformly within the training-fitted bins, so all five methods are evaluated on the same representation.
- **L3 — evaluation and knowledge discovery.** Computes the six evaluation dimensions, writes every run to an append-only JSON-lines log with its synthetic CSV, and serves two consumers: the comparison dashboard and the LLM knowledge-discovery layer. The latter only accepts DP runs.

![{fig:arch} Implemented DP-enhanced generative AI framework (three layers). All components shown are implemented and tested.](figures/diagrams/fig05_framework_architecture.png){width=6.3in}

## Design Principles

1. **One protocol for all methods.** Preprocessing choices change benchmark outcomes materially [@chen2025bench]. The same bin edges, rare-category grouping and vocabularies are therefore applied identically to every method.
2. **Guarantees are labelled by code, not by convention.** Non-DP wrappers cannot report an ε. PrivBayes reports δ = 0 explicitly, so pure and approximate DP are never conflated.
3. **Privacy by architecture for the LLM.** The LLM layer has no code path to the raw data. Its catalogue is built from the log, and its loader refuses any file outside `results/synthetic_data/`.
4. **No single "overall score".** Trade-offs are shown, not collapsed into an arbitrary weighted index.

## Components and Interfaces

**Generator interface.** `BaseSynthesizer` defines a two-call contract:

- `fit(train_df, column_spec)` sees only the training data and records the fit time.
- `generate(n)` returns a `GenerationResult` with the synthetic frame, fit and sample times, the DP flag and the privacy parameters.

Each wrapper delegates to an unmodified, original-author implementation:

- AIM and MST via OpenDP's smartnoise-synth on the `mbi` (Private-PGM) backend [@smartnoise];
- PrivBayes via a faithful third-party port;
- CTGAN and TVAE via the open-source `ctgan` package [@xu2019ctgan].

None of the five algorithms is re-implemented. This limits the risk that a comparison measures an implementation bug rather than a method.

**Experiment runner.** `run_single_experiment` turns a `RunConfig` into a result record. The configuration covers method, ε, δ, seed, epochs, size multiplier and extra parameters. The runner:

1. selects the representation the method needs;
2. fits and samples;
3. reconstructs DP output to continuous values;
4. runs the five evaluation modules;
5. appends the record to the log and saves the CSV.

The log is *resumable*: a sweep restarted after a crash skips every run identifier already marked completed, and failed runs are retried. This is what made a multi-hour sweep practical. It is also the source of the duplicate records. An explicit re-run from the dashboard always executes and appends, so the log can hold several records for one identifier. The fix made in this iteration treats the latest record as authoritative everywhere.

**Dashboard.** The Streamlit application has nine pages: dataset, preprocessing, generation, synthetic data, fidelity, utility, privacy, fairness and rare patterns, and model comparison. Each page reads from session state or from the log. The extension is attached by a single sidebar switch and a lazy import, so the original pages are untouched and keep working when the LLM dependencies are absent.

**Knowledge-discovery package.** Four modules with single responsibilities: `catalog` (eligibility and provenance), `summarizer` (aggregate payload), `prompts` (versioned templates) and `llm_client` (provider selection, live and demo generation, error handling, audit). `llm_client` supports two providers behind one interface — Google Gemini through the official `google-genai` SDK and Anthropic Claude through the official `anthropic` SDK — chosen by `KD_PROVIDER` or a drop-down on the page. Both receive the identical system prompt and payload. The package is covered by 40 tests (Appendix B).

## Design Alternatives Considered

Several alternative designs were considered and rejected, and the reasons explain the shape of the framework.

- **Sending synthetic rows to the LLM.** Privacy-neutral, because the rows are already a DP release, but poor in practice: language models compute statistics over thousands of rows unreliably, and a row-level interface would leak individuals directly the day a misconfiguration pointed it at real data (Section X).
- **Retrieval over the raw records (RAG).** This would give the most specific answers, but it gives the LLM access to individual rows and inherits retrieval-store leakage [@zeng2024rag]. It contradicts PR3 and was not built.
- **DP-trained deep generators.** DP-SGD versions of CTGAN or TVAE would put all five methods under a guarantee, but benchmarks show they usually trail marginal-based methods on tabular data [@tao2021bench; @chen2025bench], and their training cost exceeds the project's budget (Section XXI).
- **A single weighted score.** Rejected because it would hide the trade-offs that are the main finding.
- **A single LLM provider.** The client was written provider-neutral (Gemini and Claude behind one interface, identical prompt and payload), so the explanation layer does not depend on one vendor's availability or terms.

## End-to-End Sequence of One Run

For a single DP run, for example MST at ε = 1 with seed 43, the sequence is:

1. The runner builds the MST wrapper with ε = 1 and δ = 10⁻⁵.
2. It applies the fitted discretiser to the 2,400 training rows.
3. MST fits in about 25–80 s.
4. MST samples 2,400 discretised rows.
5. The rows are mapped back to continuous values within the training bins, using a random generator seeded with 43.
6. The result is evaluated against the real training split (fidelity, rare patterns) and the real test split (utility, fairness, MIA).
7. The record, including the formal statement "(1.0, 1e-05)-differential privacy via MST …", is appended to the log, and the CSV is written.

The knowledge-discovery layer can then pick this dataset from the catalogue without any further access to the real data.

## Privacy Loss Across the Pipeline

The only components that read the real training split *and* produce something released are the generators. Writing $\mathcal{G}_{\varepsilon,\delta}$ for a DP generator and $g$ for any downstream computation — summary statistics, prompt construction, LLM inference — the end-to-end privacy loss of a released explanation $E$ is governed by post-processing:

$$E = g\big(\mathcal{G}_{\varepsilon,\delta}(D_{\mathrm{train}})\big)\;\Rightarrow\; E \text{ is } (\varepsilon,\delta)\text{-DP w.r.t. } D_{\mathrm{train}} $$ {#eq:postproc}

The implication in {eq:postproc} holds only if $g$ never consults $D_{\mathrm{train}}$. In this implementation there are two exceptions, discussed in Sections VIII and X:

1. The preprocessing domain is fitted on $D_{\mathrm{train}}$ without budget.
2. The evaluation metrics use the real data.

The second exception reaches the LLM. By default the payload carries a *quality context* of seven scalars — four fidelity distances, the best TSTR F1 and the MIA AUC — that the evaluation pipeline computed by comparing the synthetic data with the real training and test splits. These numbers are not covered by the generator's guarantee and are not a DP release, so a payload that includes them is not pure post-processing. Their disclosure risk is small (seven rounded summary statistics about the whole split), but it is not zero and it is not bounded by ε. The payload's privacy manifest states this explicitly (`quality_context_uses_real_data`), and the dashboard offers a switch that withholds the quality context, leaving a payload computed from the DP synthetic data alone. Any further access to the original data — for example, an LLM tool that queried real statistics — would need its own privacy analysis and budget.

# Privacy-Aware Data Preparation and Management Layer

## Pipeline

Fig. {fig:prep} shows the preparation pipeline (`preprocessing/pipeline.py`). Its no-leakage contract is that `fit()` sees only the training split; the test split and synthetic data are only transformed. The steps are:

- **Profiling.** Infers numerical, categorical and ID-like columns, flags high-cardinality columns for exclusion, and suggests a target and a sensitive attribute. The user confirms both.
- **Missing values.** Categorical gaps become an explicit `__MISSING__` level. Imputing the mode would fabricate information and bias fidelity comparisons. Numerical gaps use the training median plus a missing-indicator column.
- **Rare categories.** Levels with less than 1% training frequency are grouped as `__RARE__`. Grouping removes noise-dominated cells that would waste budget in marginal-based methods, and it reduces the uniqueness of rare quasi-identifier values. For example, native_country shrinks from 35 levels to 4.
- **Discretisation.** Each numerical column gets 10 quantile bins. Columns with a dominant point mass — at least 30% of rows on one value, as for capital_gain = 0, capital_loss = 0, hours_per_week = 40 and education_num = 9 — get a dedicated spike bin, so that quantile binning does not collapse them into one bin.

![{fig:prep} Privacy-aware data preparation pipeline as implemented. The red box is a disclosed assumption, not a control.](figures/diagrams/fig06_privacy_aware_preprocessing_pipeline.png){width=6.3in}

## Leakage-Safe Splitting and Its Verification

The split is stratified on the target with seed 42 and gives 2,400 training and 600 test rows, with positive rates of 23.9% and 24.0%. Every learned parameter — medians, quantile edges, spike values, rare-category lists and vocabularies — is fitted on the 2,400 training rows only. The contract is checked by the test `test_preprocessing_fit_uses_train_only`: a second preprocessor fitted on the training rows *plus* deliberately altered test rows produces different age bin edges from the project's preprocessor, which shows that the test split did not influence the fitted parameters; the test split is then only transformed.

The split does not remove duplicate rows first. The sample contains 52 duplicates, and 18 distinct records therefore occur in both splits. This does not leak test labels into preprocessing, but it weakens the membership attack, whose "non-members" include some members (Section XIV). De-duplicating before the split would be cleaner. It was not done here because it would invalidate the saved results; it is listed as future work.

## Payload Sanitisation for the LLM

The same preparation layer also limits what can reach the language model:

- every categorical value comes from the closed, training-fitted vocabulary, so free text cannot be injected through a data value;
- statistics are rounded to three decimals, and groups with fewer than 20 synthetic rows are suppressed;
- the optional analyst question is the only free text; it is truncated to 500 characters and placed outside the data tags;
- prompts and responses are written to local, git-ignored audit records, never to the repository.

These are hygiene and minimisation controls. They are not a privacy mechanism, and they are not counted towards any ε.

## Effects of Preparation Choices on the Results

Preparation choices shape several of the results in Section XIV, and they should be read with that in mind.

**Uniform reconstruction within bins.** DP numerical output is mapped back by drawing a value uniformly within its training-fitted bin. A real age distribution is not uniform inside a quantile bin, so the reconstructed values cannot match the real CDF exactly, however accurate the DP model is. This puts a floor of roughly 0.07–0.08 under the KS statistic for every DP method. It also explains why the non-private generators — which model numerical values directly — can beat the DP methods on numeric correlations while losing on categorical structure.

**Spike bins.** Spike bins preserve the exact share of zero capital gains and losses and of the 40-hour week. Without them those columns would collapse into a single degenerate bin, and every DP method would erase them.

**Rare grouping.** Grouping before generation means that "rare-category loss" is measured on the *remaining* rare categories. Only four categories are rare after grouping, which makes that metric coarse.

**One protocol for all methods.** Applying the same preprocessing to every method means that differences between methods are not caused by preprocessing. It does *not* mean the protocol is optimal for any single method. Chen *et al.* found that method-specific tuning of the discretisation can change rankings [@chen2025bench].

## Anonymisation, Sanitisation and Storage

The section plan lists anonymisation, sanitisation, token filtering and secure storage. In this implementation:

- *Sanitisation* is the closed vocabulary: any unseen value maps to `__RARE__`, which also prevents arbitrary strings from reaching the LLM.
- *Generalisation* is the rare grouping and binning.
- *Secure storage* is limited to repository hygiene: git-ignored secrets, no keys in code, and a secret scan before publishing.

Classical anonymisation (k-anonymity, suppression of identifiers) is not applied to the real data, because DP replaces it as the protection mechanism for the release [@stadler2022]. Encryption at rest, access control and retention schedules are organisational controls outside the code and are proposed in Section XVIII.

## Storage and Release of Artefacts in This Repository

The public repository applies the classification of Section V as follows:

- **Real data (L3).** The 3,000-row sample is in `data/`. It is published only because the UCI Adult data are already public under CC BY 4.0; for a genuinely sensitive table this folder would stay inside the trusted environment.
- **Synthetic data (L2 and L2\*).** All 41 synthetic CSVs are published for reproducibility, including the six from CTGAN and TVAE. Those six carry no guarantee, and TVAE's contain three exact copies of training rows. Publishing them is acceptable here only because the source is public; under the framework's own rules they would not leave the custodian.
- **Credentials and LLM records.** `.env` (API keys) and `results/llm_insights/` (prompts and responses) are git-ignored, and the git history was scanned for keys before publication. The genuine LLM responses used as evidence were exported deliberately, without keys, to `evidence/llm_responses/`.
- **Template material.** The course template and the built report contain the faculty member's photograph and e-mail address and are kept out of the public repository.

## A Disclosed Weakness: Non-Private Domain

Bin edges, spike values and the category vocabulary are computed from the real training data, and the generators are called with `preprocessor_eps = 0`. Strictly, these choices are a function of the sensitive data that is not covered by the generators' budget. A quantile edge or the existence of a rare category can reveal information about a few records.

The standard remedies are:

- to fix the domain from public knowledge — for example, published census category lists and fixed age bands; or
- to spend a small part of ε on DP quantiles and DP category selection [@near2025; @ponomareva2023].

Neither is implemented. The formal statements in this report should therefore be read as "$(\varepsilon,\delta)$-DP *given* the preprocessing domain".

# Differential Privacy Integration Layer

## Mechanisms Used

Table {tab:dpmech} compares the three DP mechanisms as they are used here, together with DP-SGD, which is discussed but not implemented.

Table: {tab:dpmech} Differential privacy mechanisms comparison

| Mechanism | Guarantee & accounting | Noise | Selection step | Strengths | Weaknesses observed / known |
|---|---|---|---|---|---|
| AIM [@mckenna2022aim] | (ε, δ) via zCDP, δ = 10⁻⁵ | Gaussian on marginals | Adaptive, exponential mechanism over the workload, T ≤ 60 rounds here | Workload-aware; best low-ε fidelity here | Slowest DP method (52–626 s per fit); rounds capped; single seed |
| MST [@mckenna2021mst] | (ε, δ) via zCDP, δ = 10⁻⁵ | Gaussian on 1- and 2-way marginals | Maximum spanning tree (one shot) | Fast (mean 25–58 s per configuration), stable across seeds | Tree structure misses higher-order structure; lowest utility of the DP methods here |
| PrivBayes [@zhang2017privbayes] | Pure ε-DP (δ = 0), record count treated as public | Laplace on attribute–parent distributions | Exponential mechanism over parent sets (R score) | Fastest (mean 0.5–21 s); pure DP | Collapses at ε = 0.5; not budget-equivalent to (ε, δ) methods |
| DP-SGD [@abadi2016] (not implemented) | (ε, δ) via RDP / PRV accounting | Gaussian on clipped gradients | — | Applies to neural generators and LLM fine-tuning | Needs training; typically lower tabular utility at equal ε |

## How Each Mechanism Spends Its Budget

**MST** [@mckenna2021mst] spends its zCDP budget $\rho$ in three equal parts:

1. It measures all one-way marginals with Gaussian noise ($\sigma=\sqrt{3/(2\rho)}$).
2. It uses the exponential mechanism to select, edge by edge, a maximum spanning tree over the attributes, scored by the estimated mutual information of each pair.
3. It measures the two-way marginals on the tree's edges.

Private-PGM then fits the graphical model that best explains the noisy measurements, and records are sampled from it. Every step after the measurements is post-processing. The single, non-adaptive tree explains MST's stability across seeds and its plateau in three-way fidelity.

**AIM** [@mckenna2022aim] starts like MST with noisy one-way marginals. Over rounds $t = 1,\dots,T$ it then:

1. uses the exponential mechanism to select the workload marginal whose current model estimate is worst, after subtracting the error expected from noise alone, $\sqrt{2/\pi}\,\sigma$ times the number of cells;
2. measures it with Gaussian noise;
3. refits the model.

Its budget split is 90% for measurements and 10% for selections (see {eq:aimbudget}). When a new measurement barely changes the model's estimate, the next measurements are made more precise: σ is halved and the selection ε doubled. When the remaining budget can no longer pay for two rounds, it is spent on one final round. Each round's refit runs mirror descent, which is where most of AIM's runtime goes.

**PrivBayes** [@zhang2017privbayes] splits a pure-DP budget ε between two phases — 30% and 70% in the implementation used:

1. structure learning: an exponential mechanism greedily chooses each attribute's parents. The implementation uses its default *R* score, the low-sensitivity surrogate for mutual information proposed by Zhang *et al.*, with sensitivity $3/n + 2/n^2$, and caps parent-set domain sizes by θ-usefulness (θ = 4);
2. measurement of the joint distribution of each attribute with its parents with truncated Laplace noise (sensitivity $2/n$ for a normalised distribution), followed by normalisation into conditionals.

Both sensitivities assume that neighbouring datasets have the same size $n$ (one record replaced), so the record count is treated as public. AIM and MST are analysed in the add/remove-one-record model.

Sampling then follows the network's topological order. Because Laplace noise on small conditional tables at ε = 0.5 can wipe out the signal entirely, PrivBayes collapses at low budgets in this study.

**Pure versus approximate DP.** PrivBayes's pure ε-DP and the (ε, 10⁻⁵)-DP of AIM and MST are different guarantees. Pure DP is stronger at the same ε: it allows no failure probability, and it composes more simply under group privacy. Comparing the methods "at the same ε" therefore slightly favours AIM and MST. The reports and the dashboard state the guarantee type every time, and readers should not treat the ε axes of Fig. {fig:f1} as strictly equivalent across mechanism types.

## Scope of the Guarantee

A DP statement is only as useful as its unit and its scope [@near2025]. For the generators here:

- **Unit of privacy.** The unit is one *row* of the 2,400-row training split. If one person contributes several rows, they are protected only as a group: for $k$ rows the bound degrades to $karepsilon$ (and $k e^{(k-1)arepsilon}\delta$ for approximate DP). The sample contains 52 duplicate rows. Some of these may be distinct people with identical attributes, but if any is a repeated person, that person is protected at 2ε, not ε.
- **Neighbouring relation.** PrivBayes's sensitivities assume replacement of one row with *n* fixed, while the AIM and MST implementations use addition or removal of one row. A replacement is a removal followed by an addition, so ε-DP under addition/removal implies 2ε-DP under replacement; the converse does not hold, because PrivBayes treats *n* as public. The ε values of the two families are therefore comparable only up to this factor and assumption.
- **Covered.** The synthetic dataset and anything computed from it alone, including the aggregate payload *without* the quality context.
- **Not covered.** The preprocessing domain, the evaluation metrics and the log, the choice of which run to release (selection among the 35 DP runs uses real-data metrics), and the LLM provider's handling of prompts.

Read this way, the statement "(3, 10⁻⁵)-DP" in the dashboard is accurate for the CSV it labels, and conditional for everything around it.

## Privacy Budget Management

Each run has one fixed budget. The study sweeps ε ∈ {0.5, 1, 3, 5, 10} with δ = 10⁻⁵ for AIM and MST; δ = 10⁻⁵ is below $1/n = 4.2\times10^{-4}$. Every run is an *independent* release from the same training data, and the runs are not meant to be published together. If all 35 DP datasets in `results/synthetic_data/` were released, sequential composition would apply:

$$\varepsilon_{\mathrm{total}} = \sum_{i=1}^{k}\varepsilon_i ,\qquad \rho_{\mathrm{total}}=\sum_{i=1}^{k}\rho_i $$ {#eq:composition}

By {eq:composition}, the total would be 3 × (0.5 + 1 + 3 + 5 + 10) = 58.5 for the MST runs alone. This point matters for deployment. A production system needs a budget ledger that records every release from a dataset (Section XVIII), and the LLM layer must present each dataset as a separate release with its own ε, never as one of many views of the same protected data.

**AIM's internal budget split.** In the snsynth implementation, AIM converts $(\varepsilon,\delta)$ to a zCDP budget $\rho$ with OpenDP's numerical zCDP-to-approximate-DP conversion. This is a binary search that is slightly tighter than the closed form {eq:zcdp}. It then sets the initial noise scale from the planned number of rounds $T$ as $\sigma_0=\sqrt{T/(2\cdot0.9\,\rho)}$, and first measures all $d$ one-way marginals. Each one-way measurement costs $1/(2\sigma_0^2)$, so the initial step uses

$$\rho_{\mathrm{init}} = \frac{d}{2\sigma_0^{2}} = 0.9\,\rho\,\frac{d}{T}\;<\;\rho \;\iff\; T > 0.9\,d $$ {#eq:aimbudget}

With $d = 14$ columns, the cap of $T = 60$ spends 21% of $\rho$ on one-way marginals and leaves the rest for adaptive rounds. During testing, a cap of $T = 5$ made $\rho_{\mathrm{init}} = 2.52\,\rho$. The remaining budget went negative and the run failed with undefined (NaN) selection probabilities.

The cap therefore has a hard lower bound, and it trades adaptivity for runtime. The paper's default of $16d = 224$ rounds was measured at about 35–40 minutes per run on this dataset, which is why the cap was applied. The cap changes how the budget is spent, not the $(\varepsilon,\delta)$ bound.

**A budget ledger for deployment.** The study releases independent datasets for comparison. A deployment would instead keep a ledger per source dataset, with:

- a lifetime cap $\varepsilon_{\max}$;
- an entry for each release (date, mechanism, ε, δ, purpose, approver);
- a rule that a release is refused when the composed total would exceed the cap.

The LLM layer needs no ledger entry of its own because it only post-processes approved releases. A version that queried the real data would.

**Choosing δ.** δ should be well below $1/n$, so that the "small failure probability" cannot amount to revealing one record outright. δ = 10⁻⁵ against $n$ = 2,400 satisfies this by a factor of about 40. For larger datasets the same δ would need revisiting [@ponomareva2023].

## Workflow

Fig. {fig:dpflow} contrasts the implemented select–measure–generate workflow with DP-SGD. In DP-SGD, each per-example gradient $g_i$ is clipped to norm $C$, Gaussian noise is added to the sum of the clipped gradients of a batch $B$, the result is averaged, and an accountant tracks the cumulative loss [@abadi2016; @ponomareva2023]:

$$\theta_{t+1}=\theta_t-\frac{\eta}{|B|}\Big(\textstyle\sum_{i\in B}\bar g_i+\mathcal{N}(0,\sigma^2C^2\mathbf{I})\Big),\quad \bar g_i=g_i/\max\!\big(1,\lVert g_i\rVert_2/C\big) $$ {#eq:dpsgd}

The update rule {eq:dpsgd} would be needed to make CTGAN or TVAE private, or to fine-tune an LLM on sensitive text [@li2022llmdp]. It is **not** used in this project. CTGAN and TVAE run without it and are treated strictly as non-private baselines.

![{fig:dpflow} Differential privacy integration workflow. Top: implemented (AIM/MST select–measure–generate; PrivBayes). Bottom, dashed: DP-SGD, discussed only.](figures/diagrams/fig07_dp_integration_workflow.png){width=6.3in}

## Adaptive Privacy Strategies

AIM is itself adaptive *within* a release: it spends budget where the current model is worst. Adaptive strategies *across* releases are not implemented. Examples include choosing ε per dataset from a utility target, or reserving budget for DP domain discovery. They are proposed in Section XXI.
