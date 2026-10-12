# Requirements Analysis for Secure Knowledge Discovery

## Stakeholders

Five stakeholder groups shape the requirements:

- **Data subjects** — the people in the census records. They need assurance that their participation cannot be inferred from anything released.
- **The data custodian** — the organisation holding the raw table. It is accountable for lawful processing and for every release.
- **Analysts and model developers.** They need synthetic data accurate enough to support exploratory analysis and model prototyping, and explanations they can act on.
- **Governance roles** — a data-protection officer, an ethics board and auditors. They need evidence: the stated guarantee, risk assessments and an audit trail.
- **The research team.** It needs a fair, reproducible comparison.

The groups pull in different directions. Analysts want maximum fidelity and the richest possible LLM payload. Data subjects and governance want the smallest ε and the least detail. The requirements make that tension explicit instead of resolving it silently.

## Derivation and Prioritisation

Requirements were derived from three sources: the research questions, the threat model in Section VI, and the regulatory principles in Section XVI. They were prioritised with MoSCoW labels:

- **Must have:** every privacy and security requirement — PR1–PR5, SR1–SR4.
- **Should have:** the explainability requirements XR1–XR3.
- **Could have:** live LLM generation, FR6 in live mode. The component had to remain usable, in a labelled demo mode, without API access.

Non-functional requirements complement the six families below:

- the full sweep must run on student hardware in hours rather than days — the reason for the AIM round cap;
- the dashboard must remain usable without the extension;
- every result must be traceable to a run identifier.

**Requirement conflicts and resolutions.**

1. *Richer payloads* (better explanations) conflict with *minimisation* (PR3–PR4). The resolution is aggregates only, with small-cell suppression at k = 20.
2. *Reproducibility* (TR1) conflicts with the fact that upstream DP libraries manage their own randomness. The resolution is to make the *evaluation* exactly reproducible from saved data, and to disclose that generation is not.
3. *Runtime* conflicts with *faithfulness to the AIM paper*. The resolution is a disclosed round cap, logged in every AIM record.

## Requirement Families

The requirements are grouped into six families (Fig. {fig:req}, Appendix D). Table {tab:req} (Appendix D) traces each requirement to the component that implements it and to the evidence that it holds. A requirement is marked *met* only when that evidence was produced by executing code in this study.

**Functional requirements.**

- **FR1** — load and profile an arbitrary CSV.
- **FR2** — split and preprocess without leakage.
- **FR3** — generate synthetic data with five methods under a common interface.
- **FR4** — evaluate the six dimensions.
- **FR5** — compare runs across budgets.
- **FR6** — explain a selected DP synthetic dataset in natural language.

**Privacy requirements.**

- **PR1** — DP methods must state their exact guarantee, distinguishing pure from approximate DP.
- **PR2** — non-DP methods must never be presented as private.
- **PR3** — the LLM must never receive the original data or individual-level records.
- **PR4** — small groups must be suppressed in LLM payloads.
- **PR5** — no claim of DP for the LLM layer or the aggregates.

**Security requirements.**

- **SR1** — no credentials in source code or prompts.
- **SR2** — secrets kept in a git-ignored environment file.
- **SR3** — path guards so that only approved files can be analysed.
- **SR4** — robust handling of API failures.

**Explainability requirements.**

- **XR1** — show the exact payload sent to the LLM.
- **XR2** — label demo output as non-LLM.
- **XR3** — provide provenance for every number.

**Compliance requirements.**

- **CR1** — support data minimisation.
- **CR2** — keep audit records.
- **CR3** — document the assumptions behind the guarantee.

**Trustworthiness requirements.**

- **TR1** — results must be reproducible from saved outputs.
- **TR2** — duplicates must not be double-counted.
- **TR3** — limitations must be disclosed.

**Acceptance criteria.** Each requirement was given a check that can fail. PR3, for example, is accepted only if a test that scans the request body for the first 300 original rows finds none, and if a second test confirms that the original CSV is never opened while a summary is built and sent. TR2 is accepted only if the dashboard reports 41 unique runs from the 43 log records. A requirement without such a check would be a design intention, not a verified property.

# Data Lifecycle and Privacy Classification

## Dataset and Its Sensitivity

The study uses a 3,000-record stratified sample of the UCI Adult (Census Income) dataset [@becker1996adult]. Its 14 attributes are:

- **Numerical (5):** age, education_num, capital_gain, capital_loss, hours_per_week.
- **Categorical (9):** workclass, education, marital_status, occupation, relationship, race, sex, native_country, and the binary target *income*. 23.9% of records have income `>50K`.

The sample contains 52 duplicate rows and missing values in workclass (151), occupation (153) and native_country (52). Although Adult is public and de-identified, it is a realistic stand-in for sensitive data. It combines quasi-identifiers (age, sex, race, native country, occupation) with sensitive attributes (income, capital gains, marital status). In many jurisdictions, race and sex are special or protected categories.

**How identifying the sample is.** Counting equivalence classes in the real sample (`analysis/quasi_identifier_risk.py`) shows how quickly a few ordinary attributes single people out. On age, sex and race alone, 3.5% of the 3,000 records are unique in the sample. Adding native country raises this to 11.6%, adding occupation to 30.6%, and adding marital status to 47.3%. With those six attributes, 81.9% of records sit in groups of fewer than five, the usual k-anonymity threshold. Uniqueness in a sample does not imply uniqueness in the population. It does show that releasing even modestly detailed records, or exact copies of them, would expose many individuals to linkage with auxiliary data. This is why the real records are classified as Restricted below, and why exact copies from a generator (Section XIV) matter.

## Privacy Classification

Table {tab:class} assigns each artefact to one of three handling levels, together with its controls. The classification follows the risk-based logic of the NIST Privacy Framework [@nist2020pf] and the minimisation principle of the GDPR and the DPDP Act [@gdpr2016; @dpdp2023]. The key design decision is that **the LLM layer may only touch L2 artefacts.** The real records (L3) never leave the curator's environment.

Two artefacts are easy to misclassify. The first is the set of evaluation metrics. They are computed by comparing synthetic data with the real training and test splits, so they are *derived from* L3 data and are not covered by any generator's guarantee. Seven of them are included in the LLM payload by default as quality context. The payload's manifest says so explicitly, and the dashboard can withhold them. The second is the preprocessing domain: bin edges, spike values and category vocabularies are learned from the real training split and travel with every synthetic dataset. Both are treated as L2 for convenience in this study, but a stricter custodian could treat the metrics as L3 and replace the domain with public or DP-estimated bounds (Section XXI).

Table: {tab:class} Data privacy classification matrix

| Level | Artefacts in this project | Example attributes | Owner | Permitted processing | Controls |
|---|---|---|---|---|---|
| L3 Restricted | Real dataset (`data/`), train/test splits in memory | age, sex, race, native_country (quasi-identifiers); income, capital_gain (sensitive) | Data custodian | Preprocessing fit, generator fit, evaluation | Not sent to LLM; path guard; never committed in production |
| L2 Internal | DP synthetic CSVs, aggregate summaries, metrics, audit logs | Reconstructed records, group rates | Analytics team | Analysis, LLM explanation (DP runs only), sharing under agreement | Small-cell suppression; provenance; labelled guarantee |
| L2* Internal, no guarantee | CTGAN/TVAE synthetic CSVs | Same schema | Analytics team | Research comparison only | Excluded from LLM layer; labelled "no formal privacy guarantee" |
| L1 Public | Code, configuration, report, documentation | — | Team | Publication | Secret scan; no data values in docs |

## Lifecycle Governance

Fig. {fig:lifecycle} shows the lifecycle stages and where each classification applies.

- **Collection and consent.** These are outside this study, since the data are a published research dataset under CC BY 4.0. In a production deployment, a lawful basis and, where required, consent records would precede collection [@dpdp2023].
- **Classification and preparation.** The training split is the only input to fitted preprocessing (Section VIII).
- **Synthesis.** Consumes the budget.
- **Evaluation.** Re-uses the real test split, which is a further, non-DP use of L3 data. The metrics themselves are therefore not DP releases. They are internal diagnostics, which is acceptable for research but should be considered before publishing metrics about a sensitive dataset.
- **Release and retention.** Synthetic data and logs are retained in `results/` with run identifiers.
- **Disposal.** Disposal of the real data after release is proposed but not implemented.

![{fig:lifecycle} Data lifecycle and privacy classification framework. Dashed box: proposed but not implemented in this project.](figures/diagrams/fig03_data_lifecycle_privacy_classification.png){width=6.2in}

## Data Ownership and Roles

A lifecycle needs owners. In a deployment of this framework, four roles would hold distinct responsibilities:

- **Data owner** — a business or clinical lead. Decides the purpose, approves each release and its ε, and accepts the residual risk.
- **Data custodian** — an IT or data-platform team. Operates the trusted environment that holds L3 data and runs the generators. Here the repository's runner and preprocessing code stand in for it.
- **Data steward.** Maintains the classification, the budget ledger and the release catalogue.
- **Data consumers** — analysts, partners and the LLM service. May access only L2 artefacts under an agreement.

In the student project the team plays all four roles, which is acceptable for research. It is precisely the separation of duties that a production deployment would need to add.

## Consent and Lawful Basis

The Adult data were collected by the U.S. Census Bureau and released for research. No consent management was needed or performed. For a real deployment on newly collected data, three points matter:

1. Generating synthetic data is itself processing of personal data, so the purpose must be covered by the original lawful basis or by a compatible purpose.
2. Consent withdrawals cannot be honoured *retroactively* in an already-released DP dataset. This is a known tension between DP releases and erasure rights, and it argues for documenting releases and their dates carefully.
3. Special-category attributes (race here) normally need an explicit legal basis even for statistical use [@gdpr2016; @dpdp2023].

## Retention, Lineage and Disposal

The project stores every synthetic dataset with a run identifier that encodes dataset, method, ε and seed. The JSON-lines log records the configuration, the guarantee statement and every metric, which gives a full lineage from a released file back to the configuration that produced it. The proposed retention policy per level is:

- **L3:** delete the real training copy once the release is approved and the evaluation archived.
- **L2:** retain synthetic data and metrics for the life of the project.
- **Audit records:** keep for a fixed review period.
- **L1:** retain indefinitely.

None of these schedules is automated in the artefact.

# Threat Model and Privacy Risk Assessment

## Assets, Adversaries and Trust Boundaries

**Assets.** The real training records and, in particular, the membership of an individual in the training set and their sensitive attributes.

**Trust assumptions.** The data custodian is trusted. It runs preprocessing, generator fitting and evaluation.

**Adversary.** Assumed to see everything released: the synthetic CSVs, the logged metrics, the code and configuration, and — in live mode — anything sent to the LLM provider. Following the DP threat model, the adversary may know every record except the target's, and has unbounded computation. Fig. {fig:threat} shows the attack surface.

![{fig:threat} Threat model and attack surface. Solid arrows: data flow; dashed: attack vectors A1–A5.](figures/diagrams/fig04_threat_model.png){width=6.2in}

## Adversary Models

Three adversary profiles are considered:

- **External analyst-adversary.** Has the released synthetic data and public auxiliary information, such as a voter roll or social-media profile that gives a target's age, sex, race and occupation. Wants to learn whether the target is in the data, or the target's income.
- **Honest-but-curious service provider.** Operates the LLM API. Follows the protocol, but can read and retain every prompt.
- **Careless insider.** Not malicious, but may commit raw data or keys to a public repository, or point the analysis at the wrong file.

DP is designed for the first profile and gives a guarantee that holds whatever auxiliary information the adversary has. The second and third are handled by architecture and hygiene, not by DP.

## Threats

- **A1 — Membership inference** against the released synthetic data [@shokri2017; @hilprecht2019; @vanbreugel2023domias]. The study measures this empirically (Section XIII) with a 1-nearest-neighbour distance attack.
- **A2 — Linkage and attribute inference** from synthetic records that copy or closely resemble real ones [@stadler2022; @fredrikson2015].
- **A3 — Provider-side exposure.** Prompts sent to an LLM API are processed outside the organisation [@yao2024survey].
- **A4 — Insider or misconfiguration risk.** Raw data or API keys are committed to a repository, or the wrong file is analysed.
- **A5 — Prompt injection** through data values. Category labels or free text crafted to look like instructions [@greshake2023].
- **A6 — Over-trust in generated explanations.** An LLM describes a spurious or noise-driven pattern as real knowledge, leading to wrong or unfair decisions [@weidinger2022].

## How Differential Privacy Addresses Each Threat

**A1 — membership inference.** DP gives a quantitative bound. For any test the adversary runs, the true-positive and false-positive rates satisfy $\mathrm{TPR}\le e^{\varepsilon}\,\mathrm{FPR}+\delta$, a direct consequence of {eq:dp}. At ε = 1, an attacker operating at FPR = 1% can reach at most about 2.7% TPR. Across the budgets studied, the multiplier $e^{\varepsilon}$ is 1.65, 2.72, 20.1, 148 and about 22,000 for ε = 0.5, 1, 3, 5 and 10. At FPR = 1% the bound on TPR is therefore 1.7%, 2.7% and 20% for the first three budgets and vacuous (above 100%) for ε = 5 and 10. The budgets at which the generators were most useful here (ε = 3–5) thus give a meaningful worst-case bound only at ε = 3. At ε = 5 and 10, protection rests on the mechanism's practical behaviour rather than on the guarantee — a point that the empirical attack in Section XIV cannot settle, because it is weak.

**A2 — attribute inference.** DP limits how much the release changes the adversary's belief about a target's attribute, *relative to a world in which the target did not participate*. It does not prevent inferences that follow from population-level patterns. If high income is common among a target's occupation and age group, the synthetic data will reveal that pattern regardless — and that is intended utility, not a privacy failure.

**A3, A4 and A5.** These threats are outside DP's scope. They are addressed by sending aggregates only, by repository hygiene and path guards, and by prompt design.

**A6 — over-trust.** This is an integrity risk rather than a confidentiality risk. It is addressed by including quality context, by the knowledge-utility check, and by human review.

The privacy-threat categories of linkability, identifiability, disclosure of information, unawareness and non-compliance, as used in privacy threat-modelling practice, map onto A1–A2, A3, A6 and the compliance gaps in Section XVI.

## Attack Surface by Pipeline Stage

Walking through the pipeline stage by stage shows where each threat enters and what this implementation does about it.

1. **Preprocessing.** Bin edges and vocabularies are fitted on the real training split without budget. An adversary who sees an unusual bin edge — for example a top `capital_gain` bin ending at 99,999 — learns something about the real maximum. The risk is small for coarse bins on a public dataset, but it is real, and it is why the guarantee is stated as conditional on a public domain.
2. **Generator fitting.** This is the only stage that touches the real records *and* produces a release. For the DP methods the guarantee covers it. For CTGAN and TVAE nothing does, and TVAE's exact copies show the consequence.
3. **Release.** The synthetic CSVs, the log and the metrics are what an external adversary sees. The log also records every evaluation metric of every run, all computed against the real data, so publishing the log is not covered by ε either.
4. **LLM call.** In live mode the aggregate payload — about 6,300 input tokens in the recorded Gemini calls — leaves the organisation. It contains no rows and no keys, but it does contain the quality context and every group rate above the suppression threshold.

**Provider-side exposure in practice.** The two recorded Gemini calls sent only the payload shown in the dashboard, with the key in an HTTP header. That is the strongest guarantee the artefact can offer on the client side. What happens next depends on the provider's terms: on Google's free tier, prompts and responses may be used to improve Google's products, so a deployment would need a paid tier or an enterprise agreement and a data-processing agreement (Section XVI).

## Risk Assessment

Table {tab:threat} rates each threat by likelihood and impact *for this project's configuration*, lists the controls that are actually implemented, and states the residual risk. Ratings are qualitative judgements by the authors, not measurements. Two findings from the experiments sharpen the assessment:

1. **Exact copies.** TVAE emitted 3 exact copies of training rows across its 3 runs (Section XIV). A2 is therefore concrete for the non-DP baselines, which is why they are excluded from the LLM layer.
2. **Overlap between splits.** 18 distinct records appear in both the train and the test split because the sample contains duplicates. Some "non-members" in the A1 attack are therefore actually members, which biases the measured AUC towards 0.5.

Table: {tab:threat} Threat and risk assessment (L = likelihood, I = impact; H/M/L)

| Threat | L | I | Implemented controls | Residual risk |
|---|---|---|---|---|
| A1 Membership inference | M | H | DP generators (ε ≤ 10); attack measured | Low for DP runs within the stated ε; **unknown** for CTGAN/TVAE because the attack is weak |
| A2 Linkage / attribute inference | M (non-DP), L (DP) | H | DP; near-duplicate check; non-DP excluded from LLM layer | Medium for non-DP data if released |
| A3 Provider-side exposure | M | M | Aggregates only, rounding, k ≥ 20 suppression; no keys in prompts | Low–medium; depends on provider terms |
| A4 Insider / misconfiguration | M | H | `.gitignore`, `.env.example`, secret scan, path guard | Low |
| A5 Prompt injection via data | L | M | Data wrapped in tags; system prompt says data are not instructions; categories come from a fitted vocabulary | Low; not adversarially tested |
| A6 Over-trust in explanations | H | M | Quality metrics in payload; "hypothesis" framing; knowledge-utility check | **Medium–high**: spurious associations observed, and repeated by a real LLM (Section XIV) |
| Assumption risk: non-private preprocessing domain | M | M | Disclosed; bins and vocabulary fitted on training data only | Formal ε holds only if the domain is treated as public |
