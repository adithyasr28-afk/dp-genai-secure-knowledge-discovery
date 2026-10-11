# Differential Privacy-Enhanced Generative AI for Secure Knowledge Discovery {-}

**ABSTRACT** Generative models can turn sensitive tabular records into shareable synthetic data, and large language models (LLMs) can turn data into readable insight, but both can leak information about individuals. This study evaluates a pipeline that combines the two under differential privacy. Three differentially private generators (AIM, MST and PrivBayes) and two non-private baselines (CTGAN and TVAE) were compared on a 3,000-record sample of the UCI Adult census data across five privacy budgets, using one shared leakage-safe preprocessing protocol and six evaluation dimensions: statistical fidelity, machine-learning utility, empirical privacy risk, fairness, rare-pattern preservation and runtime. All 41 unique runs were verified by recomputing 738 logged metric values from the saved synthetic data; 733 matched exactly and the remainder differed by less than three in a million. At a budget of three and above, AIM and PrivBayes retained about 81–82% of the real-data F1 score, close to the non-private TVAE (85%), while MST retained 62–69%. A simple nearest-neighbour membership attack could not distinguish any method from random guessing, which shows the attack's weakness rather than the safety of the non-private models. An LLM knowledge-discovery layer was added that sends only suppressed aggregate statistics from private synthetic data to Claude. An offline check showed that these statistics track the real data well for AIM and PrivBayes at higher budgets but poorly for MST, and exposed spurious associations that an LLM would report as insight.

**INDEX TERMS** Differential privacy, generative AI, knowledge discovery, large language models, membership inference, privacy–utility trade-off, synthetic data, tabular data.





# Draft Status and Review Notes {-}

> **For the student team — delete this section before submission.** This is a first draft generated from the verified repository (`dp-genai-secure-knowledge-discovery`). Every number in Sections XIV–XV and Appendix B is read from `results/verified/`; please do not edit numbers by hand. Instead, rerun `python -m analysis.verify_results` and rebuild with `python report/build_report.py`.
>
> Items that need a human decision or check are marked **[CONFIRM]**, **[VERIFY]** or **[TEAM]**. The main ones:
>
> 1. **Abstract length conflict.** The template asks for a 150–250-word abstract (the ABSTRACT box above, about 240 words). The section plan asks for a 450–750-word "Executive Summary and Abstract". This draft provides both: the short abstract in the template slot and the Executive Summary below. Please confirm with the instructor which one is graded. **[CONFIRM]**
> 2. **Layout.** The template's paper body is two-column. The draft body is single-column so it is easier to edit; switch with *Layout → Columns → Two* after editing. Wide figures and tables will need section breaks. **[TEAM]**
> 3. **Front matter.** Student names, faculty name, e-mails and author order are placeholders. Page numbers in the Index, List of Figures and List of Tables must be filled in after the final layout. **[TEAM]**
> 4. **Contributions.** The Contributions table lists the automatically counted words per section. Assigning sections to registration numbers is the team's decision. **[TEAM]**
> 5. **References.** 62 references are cited.
>    - 19 were checked against online records while drafting.
>    - 5 are flagged **[VERIFY]** because a DOI or page range could not be confirmed.
>    - The rest are long-established works reproduced from standard metadata and should be spot-checked.
>
>    The mix is about 21% journal articles, 56% conference papers and 23% standards, legislation, documentation or preprints. The guideline asks for 80% journal articles from IEEE/ACM/Springer/Elsevier, so the team should swap conference papers for journal versions where they exist, or confirm the requirement with the instructor. **[TEAM]**
> 6. **Similarity.** No similarity checker has been run. The 10% threshold must be confirmed with the authorised tool after the team rewrites the text in its own words. **[TEAM]**
> 7. **Figure and table counts.** 29 figures (25 in the body, 4 in appendices) and 19 tables, which is above the guideline's 10–15 and 8–12. Candidates to move to an appendix or drop are noted in captions: the heatmap, the Logistic Regression plot, and one of the radar or heatmap pair. **[TEAM]**
> 10. **Word counts.** Counted without tables, these sections are still below the section plan's suggested minimum and could be expanded: Threat Model (about 680 of 1,000), Framework (about 880 of 1,200), Data Preparation (about 640 of 1,000), Explainability (about 700 of 1,000), Business Impact (about 400 of 500), Challenges (about 425 of 600) and Future Directions (about 425 of 600). The per-section counts are in the Contributions table. **[TEAM]**
> 8. **Equations.** These are native Word equations (editable in the Equation Editor). Numbers are typed at the right of each equation; Word does not renumber them automatically.
> 9. **Live LLM output.** No API key was available, so **no real LLM response is reported anywhere in this draft**. If the team obtains a key, run the dashboard in live mode and add a real, labelled example to Appendix D. **[TEAM]**

# Executive Summary {-}

**Context.** Organisations hold tabular data — patient records, loan books, census and survey microdata — whose analysis creates value but whose disclosure harms individuals. Generative AI offers two tempting shortcuts. Synthetic data generators can stand in for the real records, and large language models (LLMs) can explain the data in plain language. Neither is private by default. Generators memorise and reproduce training records [1][2]. LLMs leak training data [3][4], and their prompts reach third-party services. Differential privacy (DP) is the only widely accepted framework that bounds what any output can reveal about one individual [5][6].

**What was built.** This case study evaluates a three-layer pipeline. In the first layer, a leakage-safe preparation stage learns every preprocessing parameter from the training split only. In the second, a DP synthesis layer produces synthetic tables with AIM [7], MST [8] or PrivBayes [9]; CTGAN and TVAE [10] serve as non-private baselines. In the third, an evaluation and knowledge-discovery layer measures each synthetic table on six dimensions and passes only aggregate, small-cell-suppressed statistics from DP output to an LLM (Claude) for explanation.

The comparative study and dashboard existed before this iteration. The LLM layer, the verification tooling, the test suite and two dashboard fixes were added. Training a new LLM, DP-SGD and retrieval-augmented generation are discussed but **not** implemented.

**How it was evaluated.** The study uses 41 configurations on a 3,000-record sample of the UCI Adult dataset [11]: five privacy budgets (ε = 0.5–10) with three seeds each for MST and PrivBayes, one seed for AIM, and three seeds each for CTGAN and TVAE. The saved log holds 43 records because two configurations were run twice, and the latest record of each was used. Every logged metric was recomputed from the saved synthetic data: 733 of 738 values matched exactly, and the remaining five differed by less than 3 × 10⁻⁶.

**Key findings.**

- *Utility.* At ε ≥ 3, AIM and PrivBayes retained 81–82% of the real-data XGBoost F1 (0.647), close to non-private TVAE (85%). MST retained 62–69%. PrivBayes collapsed at ε = 0.5 (26%).
- *Fidelity.* AIM had the lowest three-way marginal error at ε = 0.5 (0.224, against 0.30–0.32 for the other DP methods). The non-private generators had the worst one-way numerical fidelity (KS 0.25–0.33, against 0.08–0.15 for the DP methods).
- *Privacy.* A simple nearest-neighbour membership attack scored an AUC of about 0.50 for **every** method. This exposes the attack's weakness; it does not show that CTGAN or TVAE are safe. TVAE produced the closest records and was the only method that emitted exact copies of training rows.
- *Rare patterns and fairness.* TVAE erased every rare category, and MST lost 41–48% of rare attribute combinations. Fairness metrics varied widely across single runs.
- *Knowledge discovery.* Payload statistics agreed with the real data far better for AIM and PrivBayes at ε ≥ 5 (Spearman ρ 0.76–0.88) than for MST (ρ ≤ 0.30). Some DP datasets contained spurious associations: education and race appeared strongly associated (Cramér's V ≈ 0.45–0.49) where the real association was weak (0.12). An LLM would report such artefacts as insight.

**Implications.** The prior hypothesis — that AIM offers the best DP trade-off — is only partly supported. AIM leads at low budgets but is the slowest DP method and was run with one seed. The formal guarantee also rests on treating the preprocessing domain as public. For organisations, the results support DP synthetic data as a *first-pass* analytical resource, with LLM explanations treated as hypotheses. They do not support it as a drop-in replacement for governed access to real data.

**Main limitations.** Single small dataset; AIM capped at 60 rounds and single-seed; DP generator randomness not seeded; weak membership attack; preprocessing not privatised; no live LLM output verified.


# I. Introduction {-}

## A. Motivation {-}

Most of the data that organisations would like to mine for knowledge are about people. Hospitals hold diagnoses and outcomes, banks hold transactions and credit histories, and statistical agencies hold census responses. Analysing these records improves services, but disclosing them — even in apparently anonymised form — can expose the individuals behind them. Removing names does not stop re-identification when quasi-identifiers such as age, occupation and location are retained [1]. Modern privacy law therefore treats data as personal unless identification is no longer reasonably likely [12][13].

Generative artificial intelligence (AI) appears to offer a way around this tension, in two ways. First, a generative model trained on the sensitive table can emit *synthetic* records that preserve its statistical structure and can be shared more widely [14][15]. Second, a large language model (LLM) can read a dataset or its statistics and explain patterns in natural language, lowering the skill needed to obtain insight. Both routes, however, create their own leakage channels:

- Generators can memorise training rows, and membership-inference attacks against them are well documented [2][16].
- LLMs reproduce fragments of their training data [3][17], leak personally identifiable information [4], and can be steered by injected instructions [18].
- Retrieval-augmented systems add a further store that can be extracted [19].

Differential privacy (DP) [20][5] provides the mathematical tool to bound these risks. A DP mechanism guarantees that its output distribution changes by at most a factor $e^{\varepsilon}$ (plus a small $\delta$) when any one person's record is added or removed. The guarantee survives any later processing of the output — including analysis by an LLM — and it composes across releases. DP is used in production by the U.S. Census Bureau [21], and NIST now publishes guidance on evaluating DP claims [6].

## B. Context of This Case Study {-}

This report documents the BCSE318L case study *Differential Privacy-Enhanced Generative AI for Secure Knowledge Discovery*. The technical artefact started as a comparative study of synthetic tabular data generators, delivered as a Streamlit dashboard. The study covers three DP generators — AIM [7], MST [8] and PrivBayes [9] — and two non-private deep generative baselines, CTGAN and TVAE [10]. In this iteration the artefact was extended with an LLM knowledge-discovery layer and with verification tooling. The report is careful to separate four categories:

- **Implemented in the original project:** data profiling, leakage-safe preprocessing, the five generators, the six evaluation modules, the experiment runner and log, and the nine-page dashboard.
- **Added in this iteration:**
  - the LLM knowledge-discovery package and dashboard page;
  - an offline knowledge-utility analysis;
  - result verification and de-duplication;
  - a 32-test suite;
  - two dashboard fixes (duplicate counting and a mislabelled chart caption);
  - reproducibility tooling.
- **Discussed theoretically:** DP-SGD, DP fine-tuning of LLMs, retrieval-augmented generation, federated learning, formal DP release of the aggregate statistics.
- **Proposed or future work:** see Sections XX–XXI.

## C. Objectives {-}

The study pursues six objectives:

- **O1.** Compare DP and non-DP synthetic tabular data generators fairly under one preprocessing and evaluation protocol.
- **O2.** Quantify the privacy–utility–fidelity trade-off across privacy budgets ε ∈ {0.5, 1, 3, 5, 10}.
- **O3.** Assess empirical privacy risk, fairness, rare-pattern preservation and runtime alongside utility.
- **O4.** Design and implement a knowledge-discovery layer in which an LLM explains patterns in DP synthetic data without ever receiving the original records.
- **O5.** Verify every reported number against saved outputs and make the work reproducible.
- **O6.** Analyse the governance, compliance, ethical and business implications of deploying such a pipeline.

## D. Contributions {-}

The contributions are deliberately modest; this is an empirical comparison, not a new algorithm.

1. A controlled, verified comparison of five generators across 41 runs on six evaluation dimensions. All 738 logged metric values were recomputed from the saved synthetic data (Section XIV).
2. A modular, privacy-scoped LLM extension. It accepts only DP synthetic data, refuses the original dataset, sends suppressed aggregates only, labels demo output as non-LLM, and audits every request (Section X).
3. A *knowledge-utility* check (Eq. (9)). It measures how faithfully the LLM's input statistics reflect the real data, and it revealed generator-induced spurious associations (Section XIV).
4. An explicit account of where the formal guarantee depends on assumptions: a non-private preprocessing domain, an unseeded generator, and the AIM round cap (Sections IX and XX).

## E. Scope {-}

The scope is centralised, single-release synthetic data generation for one binary-classification table. Out of scope: federated or on-device training; continual releases; text or image data; training or fine-tuning an LLM; and certifying legal compliance. The bundled dataset is public census data used as a stand-in for sensitive data. Conclusions about its sensitivity are illustrative.

## F. Organisation of the Report {-}

Sections II–III state the problem and review the literature. Sections IV–VI analyse requirements, the data lifecycle and threats. Sections VII–XI present the framework layer by layer. Sections XII–XV report the experimental setup, metrics, results and comparisons. Sections XVI–XIX cover compliance, ethics, applications and business impact. Sections XX–XXII close with limitations, future work and conclusions.

# II. Problem Statement {-}

## A. The Core Problem {-}

Let $D$ be a sensitive table of $n$ records over $d$ attributes. An organisation wants to (i) release a synthetic table $\tilde{D}$ that supports downstream analysis and machine learning, and (ii) obtain natural-language explanations of the knowledge in it. Both must hold while limiting what an adversary can learn about any individual in $D$. Four challenges make this difficult.

**Privacy leakage and memorisation.** Expressive generators fit their training data closely. Without a formal mechanism, nothing stops them from reproducing individual rows or near-copies [1]. Membership-inference attacks exploit exactly this [22][2][16].

**Model inversion and attribute inference.** Even without copying rows, a released model or dataset can let an adversary infer a sensitive attribute of a known individual from the remaining attributes [23].

**Uncontrolled knowledge extraction.** An LLM sitting on top of the data is a new interface. If it is given raw records, it can repeat them. If it is given rich statistics about small groups, it can describe those groups in identifying detail. And any data in the prompt leave the organisation's control [24][25].

**The privacy–utility tension.** DP bounds leakage by adding calibrated noise, which degrades fidelity and utility. It degrades rare subgroups disproportionately [26][27]. Choosing a mechanism and a budget is therefore an empirical question that depends on the data.

## B. Research Questions {-}

- **RQ1.** Among AIM, MST, PrivBayes, CTGAN and TVAE, which gives the best balance of privacy, fidelity, utility and cost on privacy-sensitive tabular data? Is the prior hypothesis that AIM is the strongest DP method supported?
- **RQ2.** How do fidelity, utility, fairness and rare-pattern preservation change as ε varies from 0.5 to 10?
- **RQ3.** Can an LLM knowledge-discovery layer be added without exposing the original records, and how trustworthy are the statistics it reasons over?

## C. Why It Matters {-}

If DP synthetic data can be shown to retain most of their analytical value at a defensible budget, organisations gain a governed way to share data internally and with partners. An LLM layer could then widen access to insight. If the value is not retained — or if the "insights" reflect noise rather than reality — then naive deployments risk both privacy harm and wrong decisions. Fig. 1 summarises the risk landscape this study responds to.

![Fig. 1. Generative AI privacy risk landscape: leakage channels around a generative system. Redrawn for this report; adapted from the threat categories in [24][25].](figures/diagrams/fig01_genai_privacy_risk_landscape.png){width=6.2in}


# III. Background and Literature Review {-}

## A. Differential Privacy {-}

A randomised mechanism $\mathcal{M}$ is $(\varepsilon,\delta)$-differentially private if, for all pairs of datasets $D, D'$ that differ in one record and for all output sets $S$ [20][5]:

$$\Pr[\mathcal{M}(D)\in S]\;\le\; e^{\varepsilon}\,\Pr[\mathcal{M}(D')\in S] + \delta \qquad\qquad (1)$$

Here $\varepsilon$ is the privacy budget: smaller values mean stronger protection. $\delta$ is a small probability of exceeding that bound, usually chosen well below $1/n$. When $\delta = 0$ the guarantee is called *pure* DP. The guarantee is easiest to read through the privacy-loss random variable for an output $o$:

$$\mathcal{L}_{D,D'}(o) \;=\; \ln\frac{\Pr[\mathcal{M}(D)=o]}{\Pr[\mathcal{M}(D')=o]} \qquad\qquad (2)$$

Pure $\varepsilon$-DP bounds the privacy loss in (2) by $|\mathcal{L}|\le\varepsilon$ for every output. $(\varepsilon,\delta)$-DP allows the bound to fail with probability at most $\delta$.

Three properties make DP practical:

- **Post-processing.** If $\mathcal{M}$ is $(\varepsilon,\delta)$-DP, then $g\circ\mathcal{M}$ is too, for any $g$ that does not touch $D$ again.
- **Composition.** Budgets of successive mechanisms add up.
- **Group privacy.** The guarantee degrades gracefully, by a factor $k$, for groups of $k$ records [5].

The post-processing property is what licenses the knowledge-discovery layer in this work. Computing statistics on DP synthetic data, or giving them to an LLM, costs no further budget — *provided* nothing in that pipeline consults the real data.

The basic mechanisms add noise scaled to a query's sensitivity $\Delta f$, the maximum change in $f$ caused by one record. The Laplace mechanism with noise scale $\Delta_1 f/\varepsilon$ gives pure DP. The Gaussian mechanism is analysed most tightly with zero-concentrated DP (zCDP) [28], where adding $\mathcal{N}(0,\sigma^2)$ noise to a query of $\ell_2$ sensitivity $\Delta_2$ costs $\rho = \Delta_2^2/(2\sigma^2)$. zCDP composes additively, and converts to $(\varepsilon,\delta)$-DP as

$$\varepsilon \;=\; \rho + 2\sqrt{\rho\,\ln(1/\delta)} \qquad\qquad (3)$$

The exponential mechanism [29] selects a discrete candidate $r$ with probability proportional to $\exp\!\big(\varepsilon\,q(D,r)/(2\Delta q)\big)$, where $q$ is a quality score. AIM and PrivBayes use it to choose *which* statistics to measure. Rényi DP [30] is another accounting framework, widely used for DP-SGD [31]. Practical guidance on stating guarantees, choosing $\delta$ and reporting the unit of privacy is collected in [32] and in NIST SP 800-226 [6].

## B. The Privacy–Utility Trade-off {-}

Every DP release trades privacy for accuracy. The design problem can be written as choosing, from the family $\mathcal{A}_{\varepsilon,\delta}$ of mechanisms that satisfy (1), the one that maximises an expected utility $U$ of its output:

$$\mathcal{M}^{*} \;=\; \arg\max_{\mathcal{M}\in\mathcal{A}_{\varepsilon,\delta}}\; \mathbb{E}\big[\,U(\mathcal{M}(D))\,\big] \qquad\qquad (4)$$

No single $U$ in (4) captures all uses of synthetic data. A table can match every one-way distribution and still break correlations, or support a classifier well while erasing a rare subgroup. This study therefore reports a vector of utilities (Section XIII) rather than one score. That follows recent benchmarks [33][34], which found that conclusions change with the metric and with preprocessing choices.

## C. Differentially Private Synthetic Data {-}

**Marginal-based (select–measure–generate) methods.**

- *PrivBayes* [9] uses the exponential mechanism to learn a Bayesian network of low-degree conditional distributions, then releases those conditionals with Laplace noise. This gives pure $\varepsilon$-DP.
- *MST* [8] selects a maximum spanning tree of two-way marginals, measures all one-way and selected two-way marginals with Gaussian noise, and fits a graphical model with Private-PGM. A variant of MST won the 2018 NIST synthetic-data challenge.
- *AIM* [7] makes the selection adaptive. Over $T$ rounds it uses the exponential mechanism to pick the workload marginal that the current model approximates worst, measures it, and refits the model, allocating budget with zCDP.

Both independent benchmarks found that marginal-based methods often give the best utility at moderate budgets [34][33]. Chen *et al.* also reported that they are markedly slower than most deep-learning alternatives [33].

**Deep generative models.**

- *CTGAN* and *TVAE* [10] are the reference conditional GAN and variational autoencoder for mixed-type tables, distributed with the Synthetic Data Vault [35]. They give no formal privacy guarantee.
- DP variants train with DP-SGD [31] or with PATE, as in PATE-GAN [36].
- Diffusion models such as TabDDPM [37] and LLM-based generators such as GReaT [38] improve fidelity further but are non-private in their basic form.

**Privacy of "anonymous" synthetic data.** Stadler *et al.* showed that synthetic data produced without DP gives an unpredictable and often poor privacy–utility trade-off. Linkage and membership attacks still succeed against outlier records [1]. Distance-based and density-based membership attacks on generative models are described in [2] and [16]. Shadow-model attacks and the low-false-positive reporting convention come from [22][39]. Empirical audits can lower-bound the true leakage of a DP implementation [40].

**Fairness and rare groups.** DP noise hurts small groups most. DP training has a disparate impact on accuracy [26], and Ganev *et al.* found that DP synthetic data can either flatten ("Robin Hood") or exaggerate ("Matthew") group imbalances, with accuracy loss concentrated on minorities [27]. Rosenblatt *et al.* proposed *epistemic parity* — whether conclusions drawn from synthetic data reproduce those drawn from real data — as an evaluation criterion [41]. That idea motivates the knowledge-utility check in Section X.

## D. Privacy in Large Language Models and Generative AI {-}

LLMs memorise training data, and the amount grows with model size and with how often an example is repeated [3][17]. Lukas *et al.* demonstrated extraction, reconstruction and inference of personally identifiable information from fine-tuned models [4]. Surveys organise these threats alongside misuse risks [24][25].

Mitigations at training time include DP fine-tuning, which is now practical for large models [42][43], although Tramèr *et al.* questioned how much "public" pre-training data really protects [44]. At generation time there are two DP approaches. One produces DP synthetic text by DP fine-tuning [45]. The other uses *Private Evolution*, which needs only API access to a foundation model [46][47].

Retrieval-augmented generation (RAG) [48] adds a document store that can itself leak [19]. Instructions hidden in retrieved content can hijack an LLM-integrated application [18]. Federated learning keeps raw data local but needs DP to bound what the updates reveal [49].

## E. Other Privacy-Enhancing Technologies {-}

DP is one of several privacy-enhancing technologies, and it is worth being clear about why it is the right tool here.

**Syntactic anonymisation** — k-anonymity and its refinements — generalises or suppresses quasi-identifiers until each record hides among k others. It offers no protection against adversaries with auxiliary information, and it degrades badly in high dimensions. Synthetic data produced without DP inherit a similar weakness [1].

**Cryptographic techniques** — secure multi-party computation, homomorphic encryption and trusted execution environments — protect data *during* computation, so that no party sees another's inputs. They say nothing about what the *output* reveals.

**Federated learning** keeps data where they are, but its model updates leak unless combined with DP [49].

DP is the only one of these that bounds what a released output reveals about any individual, which is exactly the problem of publishing a synthetic table or an explanation. In practice these technologies complement each other. A deployment could combine a trusted environment for generation, DP for the release, and encrypted transport for the LLM call.

## F. Secure Knowledge Discovery and Governance {-}

Knowledge discovery is the extraction of useful, understandable patterns from data. Doing it securely means controlling who sees which data, at which granularity, under what guarantee, and with what accountability. Fig. 2 places the actors of this study in such an ecosystem: data subjects, a trusted curator who holds the raw data and the budget, a DP release, analysts and an LLM service, overseen by governance.

Governance instruments that complement the technical layer include:

- documentation artefacts — datasheets for datasets [50] and model cards [51];
- risk frameworks — the NIST Privacy Framework [52] and the AI Risk Management Framework [53];
- management-system standards — ISO/IEC 27701 [54] and ISO/IEC 42001 [55].

![Fig. 2. Secure knowledge-discovery ecosystem assumed in this study. Dashed arrows are governance relationships; the LLM receives only aggregates of the DP release.](figures/diagrams/fig02_secure_knowledge_discovery_ecosystem.png){width=6.2in}

## G. Comparative Summary and Research Gap {-}

Table I compares representative works. Three gaps motivate this study:

1. Benchmarks of DP synthesis rarely report fairness, rare-pattern loss and empirical attacks *together* with utility.
2. LLM-based analysis of DP synthetic data is discussed but seldom measured against what the same statistics look like on the real data.
3. Student-scale reproductions seldom verify their logged results or disclose the assumptions behind the guarantee — for example, the public-domain assumption for preprocessing.

Table: TABLE I. Comparison of representative literature

| Work | Data / setting | Privacy mechanism | Main contribution | Limitation relevant here |
|---|---|---|---|---|
| Zhang *et al.* 2017 [9] | Tabular | Pure ε-DP (exponential + Laplace) | Bayesian-network synthesis (PrivBayes) | Network degree limits higher-order fidelity |
| McKenna *et al.* 2021 [8] | Tabular | (ε, δ) via zCDP | MST + Private-PGM; NIST 2018 winner | Fixed tree; no workload adaptivity |
| McKenna *et al.* 2022 [7] | Tabular | (ε, δ) via zCDP | Adaptive workload-aware AIM | High runtime for many rounds |
| Xu *et al.* 2019 [10] | Tabular | None | CTGAN / TVAE for mixed types | No guarantee; memorisation risk |
| Jordon *et al.* 2019 [36] | Tabular | (ε, δ) via PATE | DP GAN training | Utility at small ε |
| Stadler *et al.* 2022 [1] | Tabular | Evaluates DP and non-DP | Privacy gain of synthetic data is unpredictable without DP | Attack-specific |
| Ganev *et al.* 2022 [27] | Tabular | DP generators | Disparate impact on subgroups | Classification tasks only |
| Chen *et al.* 2025 [33] | Tabular benchmark | Many DP methods | Unified preprocessing/evaluation; utility vs efficiency | No LLM layer |
| Carlini *et al.* 2021 [3] | LLM | None | Training-data extraction from LLMs | Attack, not defence |
| Li *et al.* 2022 [42] | LLM fine-tuning | DP-SGD | Strong DP fine-tuning of LLMs | Requires model training |
| Xie *et al.* 2024 [47] | Text | DP via API-only Private Evolution | DP synthetic text without training | Text, not tables |
| Zeng *et al.* 2024 [19] | RAG | — | Retrieval-store leakage | No DP mechanism |
| **This study** | Tabular + LLM explanations | (ε, δ) and pure ε via generators; post-processing | Verified 5-method comparison + aggregate-only LLM layer + knowledge-utility check | One small dataset; no live LLM evaluation |


# IV. Requirements Analysis for Secure Knowledge Discovery {-}

## A. Stakeholders {-}

Five stakeholder groups shape the requirements:

- **Data subjects** — the people in the census records. They need assurance that their participation cannot be inferred from anything released.
- **The data custodian** — the organisation holding the raw table. It is accountable for lawful processing and for every release.
- **Analysts and model developers.** They need synthetic data accurate enough to support exploratory analysis and model prototyping, and explanations they can act on.
- **Governance roles** — a data-protection officer, an ethics board and auditors. They need evidence: the stated guarantee, risk assessments and an audit trail.
- **The research team.** It needs a fair, reproducible comparison.

The groups pull in different directions. Analysts want maximum fidelity and the richest possible LLM payload. Data subjects and governance want the smallest ε and the least detail. The requirements make that tension explicit instead of resolving it silently.

## B. Derivation and Prioritisation {-}

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

## C. Requirement Families They are grouped into six families (Fig. 3). Table II traces each requirement to the component that implements it and to the evidence that it holds. A requirement is marked *met* only when that evidence was produced by executing code in this study. {-}

![Fig. 3. Requirements framework: six requirement families verified through tests, re-evaluation and payload inspection.](figures/diagrams/fig02b_requirements_framework.png){width=6.0in}

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

Table: TABLE II. Requirements traceability matrix

| ID | Requirement | Implemented in | Evidence | Status |
|---|---|---|---|---|
| FR1–FR2 | Profiling; train-only preprocessing | `preprocessing/` | `test_preprocessing_fit_uses_train_only`, `test_dataset_shape` | Met |
| FR3 | Five generators, common interface | `models/`, `experiments/runner.py` | 5 end-to-end smoke tests passed | Met |
| FR4–FR5 | Six evaluation dimensions; comparison | `evaluation/`, dashboard | 733/738 metrics re-computed exactly | Met |
| FR6 | LLM explanation of DP synthetic data | `knowledge_discovery/` | Mock-server tests via real SDK; demo mode in UI | Met (live output **not** verified) |
| PR1–PR2 | Exact guarantees; non-DP labelled | `models/*`, `privacy.py` | `config_checks.csv`: 41/41 pass | Met |
| PR3 | No original data to the LLM | `catalog.py` path guard | `test_original_rows_never_in_prompt`, `test_original_file_not_read…` | Met |
| PR4 | Small-cell suppression | `summarizer.py` (k = 20) | `test_small_cells_suppressed` | Met |
| PR5 | No DP claim for aggregates/LLM | UI notes, manifest, README | Manual review | Met |
| SR1–SR2 | No secrets in repository | `.env.example`, `.gitignore` | Secret scan of tracked files | Met |
| SR3 | Path guards | `catalog.py` | `test_refuses_original_dataset_and_non_dp` | Met |
| SR4 | API error handling | `llm_client.py` | HTTP 400/401/429/500 and connection tests | Met |
| XR1–XR2 | Payload shown; demo labelled | `streamlit_page.py` | Dashboard inspection; `test_demo_mode_is_labelled…` | Met |
| XR3, CR2 | Provenance, audit | Log, audit JSON | Audit records inspected | Met |
| CR3, TR3 | Assumptions disclosed | README, this report | Sections IX, XX | Met |
| TR1 | Reproducibility from outputs | `analysis/verify_results.py` | Re-evaluation report | Met (generators unseeded — see XX) |
| TR2 | No double counting | Dashboard fix, catalogue | 41 unique runs shown | Met (bug found and fixed) |

# V. Data Lifecycle and Privacy Classification {-}

## A. Dataset and Its Sensitivity {-}

The study uses a 3,000-record stratified sample of the UCI Adult (Census Income) dataset [11]. Its 14 attributes are:

- **Numerical (5):** age, education_num, capital_gain, capital_loss, hours_per_week.
- **Categorical (9):** workclass, education, marital_status, occupation, relationship, race, sex, native_country, and the binary target *income*. 23.9% of records have income `>50K`.

The sample contains 52 duplicate rows and missing values in workclass (151), occupation (153) and native_country (52). Although Adult is public and de-identified, it is a realistic stand-in for sensitive data. It combines quasi-identifiers (age, sex, race, native country, occupation) with sensitive attributes (income, capital gains, marital status). In many jurisdictions, race and sex are special or protected categories.

## B. Privacy Classification {-}

Table III assigns each artefact to one of three handling levels, together with its controls. The classification follows the risk-based logic of the NIST Privacy Framework [52] and the minimisation principle of the GDPR and the DPDP Act [12][13]. The key design decision is that **the LLM layer may only touch L2 artefacts.** The real records (L3) never leave the curator's environment.

Table: TABLE III. Data privacy classification matrix

| Level | Artefacts in this project | Example attributes | Owner | Permitted processing | Controls |
|---|---|---|---|---|---|
| L3 Restricted | Real dataset (`data/`), train/test splits in memory | age, sex, race, native_country (quasi-identifiers); income, capital_gain (sensitive) | Data custodian | Preprocessing fit, generator fit, evaluation | Not sent to LLM; path guard; never committed in production |
| L2 Internal | DP synthetic CSVs, aggregate summaries, metrics, audit logs | Reconstructed records, group rates | Analytics team | Analysis, LLM explanation (DP runs only), sharing under agreement | Small-cell suppression; provenance; labelled guarantee |
| L2* Internal, no guarantee | CTGAN/TVAE synthetic CSVs | Same schema | Analytics team | Research comparison only | Excluded from LLM layer; labelled "no formal privacy guarantee" |
| L1 Public | Code, configuration, report, documentation | — | Team | Publication | Secret scan; no data values in docs |

## C. Lifecycle Governance {-}

Fig. 4 shows the lifecycle stages and where each classification applies.

- **Collection and consent.** These are outside this study, since the data are a published research dataset under CC BY 4.0. In a production deployment, a lawful basis and, where required, consent records would precede collection [13].
- **Classification and preparation.** The training split is the only input to fitted preprocessing (Section VIII).
- **Synthesis.** Consumes the budget.
- **Evaluation.** Re-uses the real test split, which is a further, non-DP use of L3 data. The metrics themselves are therefore not DP releases. They are internal diagnostics, which is acceptable for research but should be considered before publishing metrics about a sensitive dataset.
- **Release and retention.** Synthetic data and logs are retained in `results/` with run identifiers.
- **Disposal.** Disposal of the real data after release is proposed but not implemented.

![Fig. 4. Data lifecycle and privacy classification framework. Dashed box: proposed but not implemented in this project.](figures/diagrams/fig03_data_lifecycle_privacy_classification.png){width=6.2in}

## D. Data Ownership and Roles {-}

A lifecycle needs owners. In a deployment of this framework, four roles would hold distinct responsibilities:

- **Data owner** — a business or clinical lead. Decides the purpose, approves each release and its ε, and accepts the residual risk.
- **Data custodian** — an IT or data-platform team. Operates the trusted environment that holds L3 data and runs the generators. Here the repository's runner and preprocessing code stand in for it.
- **Data steward.** Maintains the classification, the budget ledger and the release catalogue.
- **Data consumers** — analysts, partners and the LLM service. May access only L2 artefacts under an agreement.

In the student project the team plays all four roles, which is acceptable for research. It is precisely the separation of duties that a production deployment would need to add.

## E. Consent and Lawful Basis {-}

The Adult data were collected by the U.S. Census Bureau and released for research. No consent management was needed or performed. For a real deployment on newly collected data, three points matter:

1. Generating synthetic data is itself processing of personal data, so the purpose must be covered by the original lawful basis or by a compatible purpose.
2. Consent withdrawals cannot be honoured *retroactively* in an already-released DP dataset. This is a known tension between DP releases and erasure rights, and it argues for documenting releases and their dates carefully.
3. Special-category attributes (race here) normally need an explicit legal basis even for statistical use [12][13].

## F. Retention, Lineage and Disposal {-}

The project stores every synthetic dataset with a run identifier that encodes dataset, method, ε and seed. The JSON-lines log records the configuration, the guarantee statement and every metric, which gives a full lineage from a released file back to the configuration that produced it. The proposed retention policy per level is:

- **L3:** delete the real training copy once the release is approved and the evaluation archived.
- **L2:** retain synthetic data and metrics for the life of the project.
- **Audit records:** keep for a fixed review period.
- **L1:** retain indefinitely.

None of these schedules is automated in the artefact.

# VI. Threat Model and Privacy Risk Assessment {-}

## A. Assets, Adversaries and Trust Boundaries {-}

**Assets.** The real training records and, in particular, the membership of an individual in the training set and their sensitive attributes.

**Trust assumptions.** The data custodian is trusted. It runs preprocessing, generator fitting and evaluation.

**Adversary.** Assumed to see everything released: the synthetic CSVs, the logged metrics, the code and configuration, and — in live mode — anything sent to the LLM provider. Following the DP threat model, the adversary may know every record except the target's, and has unbounded computation. Fig. 5 shows the attack surface.

![Fig. 5. Threat model and attack surface. Solid arrows: data flow; dashed: attack vectors A1–A5.](figures/diagrams/fig04_threat_model.png){width=6.2in}

## B. Adversary Models {-}

Three adversary profiles are considered:

- **External analyst-adversary.** Has the released synthetic data and public auxiliary information, such as a voter roll or social-media profile that gives a target's age, sex, race and occupation. Wants to learn whether the target is in the data, or the target's income.
- **Honest-but-curious service provider.** Operates the LLM API. Follows the protocol, but can read and retain every prompt.
- **Careless insider.** Not malicious, but may commit raw data or keys to a public repository, or point the analysis at the wrong file.

DP is designed for the first profile and gives a guarantee that holds whatever auxiliary information the adversary has. The second and third are handled by architecture and hygiene, not by DP.

## C. Threats {-}

- **A1 — Membership inference** against the released synthetic data [22][2][16]. The study measures this empirically (Section XIII) with a 1-nearest-neighbour distance attack.
- **A2 — Linkage and attribute inference** from synthetic records that copy or closely resemble real ones [1][23].
- **A3 — Provider-side exposure.** Prompts sent to an LLM API are processed outside the organisation [24].
- **A4 — Insider or misconfiguration risk.** Raw data or API keys are committed to a repository, or the wrong file is analysed.
- **A5 — Prompt injection** through data values. Category labels or free text crafted to look like instructions [18].
- **A6 — Over-trust in generated explanations.** An LLM describes a spurious or noise-driven pattern as real knowledge, leading to wrong or unfair decisions [25].

## D. How Differential Privacy Addresses Each Threat {-}

**A1 — membership inference.** DP gives a quantitative bound. For any test the adversary runs, the true-positive and false-positive rates satisfy $\mathrm{TPR}\le e^{\varepsilon}\,\mathrm{FPR}+\delta$, a direct consequence of (1). At ε = 1, an attacker operating at FPR = 1% can reach at most about 2.7% TPR. At ε = 10 the bound is vacuous, and protection then rests on the mechanism's practical behaviour rather than on the guarantee.

**A2 — attribute inference.** DP limits how much the release changes the adversary's belief about a target's attribute, *relative to a world in which the target did not participate*. It does not prevent inferences that follow from population-level patterns. If high income is common among a target's occupation and age group, the synthetic data will reveal that pattern regardless — and that is intended utility, not a privacy failure.

**A3, A4 and A5.** These threats are outside DP's scope. They are addressed by sending aggregates only, by repository hygiene and path guards, and by prompt design.

**A6 — over-trust.** This is an integrity risk rather than a confidentiality risk. It is addressed by including quality context, by the knowledge-utility check, and by human review.

The privacy-threat categories of linkability, identifiability, disclosure of information, unawareness and non-compliance, as used in privacy threat-modelling practice, map onto A1–A2, A3, A6 and the compliance gaps in Section XVI.

## E. Risk Assessment {-}

Table IV rates each threat by likelihood and impact *for this project's configuration*, lists the controls that are actually implemented, and states the residual risk. Ratings are qualitative judgements by the authors, not measurements. Two findings from the experiments sharpen the assessment:

1. **Exact copies.** TVAE emitted 3 exact copies of training rows across its 3 runs (Section XIV). A2 is therefore concrete for the non-DP baselines, which is why they are excluded from the LLM layer.
2. **Overlap between splits.** 18 distinct records appear in both the train and the test split because the sample contains duplicates. Some "non-members" in the A1 attack are therefore actually members, which biases the measured AUC towards 0.5.

Table: TABLE IV. Threat and risk assessment (L = likelihood, I = impact; H/M/L)

| Threat | L | I | Implemented controls | Residual risk |
|---|---|---|---|---|
| A1 Membership inference | M | H | DP generators (ε ≤ 10); attack measured | Low for DP runs within the stated ε; **unknown** for CTGAN/TVAE because the attack is weak |
| A2 Linkage / attribute inference | M (non-DP), L (DP) | H | DP; near-duplicate check; non-DP excluded from LLM layer | Medium for non-DP data if released |
| A3 Provider-side exposure | M | M | Aggregates only, rounding, k ≥ 20 suppression; no keys in prompts | Low–medium; depends on provider terms |
| A4 Insider / misconfiguration | M | H | `.gitignore`, `.env.example`, secret scan, path guard | Low |
| A5 Prompt injection via data | L | M | Data wrapped in tags; system prompt says data are not instructions; categories come from a fitted vocabulary | Low; not adversarially tested |
| A6 Over-trust in explanations | H | M | Quality metrics in payload; "hypothesis" framing; knowledge-utility check | **Medium–high**: spurious associations observed |
| Assumption risk: non-private preprocessing domain | M | M | Disclosed; bins and vocabulary fitted on training data only | Formal ε holds only if the domain is treated as public |


# VII. Proposed Differential Privacy-Enhanced Generative AI Framework {-}

## A. Architecture Overview {-}

The framework has three layers (Fig. 6). Each layer only consumes the outputs of the layer before it.

- **L1 — data and preparation.** Profiles the dataset, assigns column roles, performs a stratified 80/20 split (seed 42), and fits all preprocessing parameters on the training split only. It emits two views of the same data: a *discretised* view for the marginal-based DP generators, and a *continuous* view for CTGAN and TVAE. The fitted parameters (bin edges, spike values, vocabularies, medians) are serialisable for provenance.
- **L2 — synthesis.** Wraps five generators behind one `BaseSynthesizer` interface. Each wrapper reports `is_differentially_private` and `privacy_params()`, so the dashboard labels every run correctly by construction. DP output is mapped back to continuous values by sampling uniformly within the training-fitted bins, so all five methods are evaluated on the same representation.
- **L3 — evaluation and knowledge discovery.** Computes the six evaluation dimensions, writes every run to an append-only JSON-lines log with its synthetic CSV, and serves two consumers: the comparison dashboard and the LLM knowledge-discovery layer. The latter only accepts DP runs.

![Fig. 6. Implemented DP-enhanced generative AI framework (three layers). All components shown are implemented and tested.](figures/diagrams/fig05_framework_architecture.png){width=6.3in}

## B. Design Principles {-}

1. **One protocol for all methods.** Preprocessing choices change benchmark outcomes materially [33]. The same bin edges, rare-category grouping and vocabularies are therefore applied identically to every method.
2. **Guarantees are labelled by code, not by convention.** Non-DP wrappers cannot report an ε. PrivBayes reports δ = 0 explicitly, so pure and approximate DP are never conflated.
3. **Privacy by architecture for the LLM.** The LLM layer has no code path to the raw data. Its catalogue is built from the log, and its loader refuses any file outside `results/synthetic_data/`.
4. **No single "overall score".** Trade-offs are shown, not collapsed into an arbitrary weighted index.

## C. Components and Interfaces {-}

**Generator interface.** `BaseSynthesizer` defines a two-call contract:

- `fit(train_df, column_spec)` sees only the training data and records the fit time.
- `generate(n)` returns a `GenerationResult` with the synthetic frame, fit and sample times, the DP flag and the privacy parameters.

Each wrapper delegates to an unmodified, original-author implementation:

- AIM and MST via OpenDP's smartnoise-synth on the `mbi` (Private-PGM) backend [56];
- PrivBayes via a faithful third-party port;
- CTGAN and TVAE via the Synthetic Data Vault's `ctgan` package [35].

None of the five algorithms is re-implemented. This limits the risk that a comparison measures an implementation bug rather than a method.

**Experiment runner.** `run_single_experiment` turns a `RunConfig` into a result record. The configuration covers method, ε, δ, seed, epochs, size multiplier and extra parameters. The runner:

1. selects the representation the method needs;
2. fits and samples;
3. reconstructs DP output to continuous values;
4. runs the five evaluation modules;
5. appends the record to the log and saves the CSV.

The log is *resumable*: a sweep restarted after a crash skips every run identifier already marked completed, and failed runs are retried. This is what made a multi-hour sweep practical. It is also the source of the duplicate records. An explicit re-run from the dashboard always executes and appends, so the log can hold several records for one identifier. The fix made in this iteration treats the latest record as authoritative everywhere.

**Dashboard.** The Streamlit application has nine pages: dataset, preprocessing, generation, synthetic data, fidelity, utility, privacy, fairness and rare patterns, and model comparison. Each page reads from session state or from the log. The extension is attached by a single sidebar switch and a lazy import, so the original pages are untouched and keep working when the LLM dependencies are absent.

**Knowledge-discovery package.** Four modules with single responsibilities: `catalog` (eligibility and provenance), `summarizer` (aggregate payload), `prompts` (versioned templates) and `llm_client` (live and demo generation, error handling, audit). They are covered by 23 tests (Appendix B).

## D. End-to-End Sequence of One Run {-}

For a single DP run, for example MST at ε = 1 with seed 43, the sequence is:

1. The runner builds the MST wrapper with ε = 1 and δ = 10⁻⁵.
2. It applies the fitted discretiser to the 2,400 training rows.
3. MST fits in about 25–80 s.
4. MST samples 2,400 discretised rows.
5. The rows are mapped back to continuous values within the training bins, using a random generator seeded with 43.
6. The result is evaluated against the real training split (fidelity, rare patterns) and the real test split (utility, fairness, MIA).
7. The record, including the formal statement "(1.0, 1e-05)-differential privacy via MST …", is appended to the log, and the CSV is written.

The knowledge-discovery layer can then pick this dataset from the catalogue without any further access to the real data.

## E. Privacy Loss Across the Pipeline {-}

The only components that read the real training split *and* produce something released are the generators. Writing $\mathcal{G}_{\varepsilon,\delta}$ for a DP generator and $g$ for any downstream computation — summary statistics, prompt construction, LLM inference — the end-to-end privacy loss of a released explanation $E$ is governed by post-processing:

$$E = g\big(\mathcal{G}_{\varepsilon,\delta}(D_{\mathrm{train}})\big)\;\Rightarrow\; E \text{ is } (\varepsilon,\delta)\text{-DP w.r.t. } D_{\mathrm{train}} \qquad\qquad (5)$$

The implication in (5) holds only if $g$ never consults $D_{\mathrm{train}}$. In this implementation there are two exceptions, discussed in Section IX:

1. The preprocessing domain is fitted on $D_{\mathrm{train}}$ without budget.
2. The evaluation metrics use the real data.

The metrics are internal diagnostics and are not sent to the LLM as released data. They *are* included in the payload as quality context, and that is a small, disclosed exception.

# VIII. Privacy-Aware Data Preparation and Management Layer {-}

## A. Pipeline {-}

Fig. 7 shows the preparation pipeline (`preprocessing/pipeline.py`). Its no-leakage contract is that `fit()` sees only the training split; the test split and synthetic data are only transformed. The steps are:

- **Profiling.** Infers numerical, categorical and ID-like columns, flags high-cardinality columns for exclusion, and suggests a target and a sensitive attribute. The user confirms both.
- **Missing values.** Categorical gaps become an explicit `__MISSING__` level. Imputing the mode would fabricate information and bias fidelity comparisons. Numerical gaps use the training median plus a missing-indicator column.
- **Rare categories.** Levels with less than 1% training frequency are grouped as `__RARE__`. Grouping removes noise-dominated cells that would waste budget in marginal-based methods, and it reduces the uniqueness of rare quasi-identifier values. For example, native_country shrinks from 35 levels to 4.
- **Discretisation.** Each numerical column gets 10 quantile bins. Columns with a dominant point mass — at least 30% of rows on one value, as for capital_gain = 0, capital_loss = 0, hours_per_week = 40 and education_num = 9 — get a dedicated spike bin, so that quantile binning does not collapse them into one bin.

![Fig. 7. Privacy-aware data preparation pipeline as implemented. The red box is a disclosed assumption, not a control.](figures/diagrams/fig06_privacy_aware_preprocessing_pipeline.png){width=6.3in}

## B. Effects of Preparation Choices on the Results {-}

Preparation choices shape several of the results in Section XIV, and they should be read with that in mind.

**Uniform reconstruction within bins.** DP numerical output is mapped back by drawing a value uniformly within its training-fitted bin. A real age distribution is not uniform inside a quantile bin, so the reconstructed values cannot match the real CDF exactly, however accurate the DP model is. This puts a floor of roughly 0.07–0.08 under the KS statistic for every DP method. It also explains why the non-private generators — which model numerical values directly — can beat the DP methods on numeric correlations while losing on categorical structure.

**Spike bins.** Spike bins preserve the exact share of zero capital gains and losses and of the 40-hour week. Without them those columns would collapse into a single degenerate bin, and every DP method would erase them.

**Rare grouping.** Grouping before generation means that "rare-category loss" is measured on the *remaining* rare categories. Only four categories are rare after grouping, which makes that metric coarse.

**One protocol for all methods.** Applying the same preprocessing to every method means that differences between methods are not caused by preprocessing. It does *not* mean the protocol is optimal for any single method. Chen *et al.* found that method-specific tuning of the discretisation can change rankings [33].

## C. Anonymisation, Sanitisation and Storage {-}

The section plan lists anonymisation, sanitisation, token filtering and secure storage. In this implementation:

- *Sanitisation* is the closed vocabulary: any unseen value maps to `__RARE__`, which also prevents arbitrary strings from reaching the LLM.
- *Generalisation* is the rare grouping and binning.
- *Secure storage* is limited to repository hygiene: git-ignored secrets, no keys in code, and a secret scan before publishing.

Classical anonymisation (k-anonymity, suppression of identifiers) is not applied to the real data, because DP replaces it as the protection mechanism for the release [1]. Encryption at rest, access control and retention schedules are organisational controls outside the code and are proposed in Section XVIII.

## D. A Disclosed Weakness: Non-Private Domain {-}

Bin edges, spike values and the category vocabulary are computed from the real training data, and the generators are called with `preprocessor_eps = 0`. Strictly, these choices are a function of the sensitive data that is not covered by the generators' budget. A quantile edge or the existence of a rare category can reveal information about a few records.

The standard remedies are:

- to fix the domain from public knowledge — for example, published census category lists and fixed age bands; or
- to spend a small part of ε on DP quantiles and DP category selection [6][32].

Neither is implemented. The formal statements in this report should therefore be read as "$(\varepsilon,\delta)$-DP *given* the preprocessing domain".

# IX. Differential Privacy Integration Layer {-}

## A. Mechanisms Used {-}

Table V compares the three DP mechanisms as they are used here, together with DP-SGD, which is discussed but not implemented.

Table: TABLE V. Differential privacy mechanisms comparison

| Mechanism | Guarantee & accounting | Noise | Selection step | Strengths | Weaknesses observed / known |
|---|---|---|---|---|---|
| AIM [7] | (ε, δ) via zCDP, δ = 10⁻⁵ | Gaussian on marginals | Adaptive, exponential mechanism over the workload, T ≤ 60 rounds here | Workload-aware; best low-ε fidelity here | Slowest DP method (52–626 s); rounds capped; single seed |
| MST [8] | (ε, δ) via zCDP, δ = 10⁻⁵ | Gaussian on 1- and 2-way marginals | Maximum spanning tree (one shot) | Fast (25–58 s), stable across seeds | Tree structure misses higher-order structure; lowest utility of the DP methods here |
| PrivBayes [9] | Pure ε-DP (δ = 0) | Laplace on conditionals | Exponential mechanism over parent sets | Fastest (0.5–21 s); pure DP | Collapses at ε = 0.5; not budget-equivalent to (ε, δ) methods |
| DP-SGD [31] (not implemented) | (ε, δ) via RDP / PRV accounting | Gaussian on clipped gradients | — | Applies to neural generators and LLM fine-tuning | Needs training; typically lower tabular utility at equal ε |

## B. How Each Mechanism Spends Its Budget {-}

**MST** [8] spends its zCDP budget $\rho$ in three equal parts:

1. It measures all one-way marginals with Gaussian noise ($\sigma=\sqrt{3/(2
ho)}$).
2. It uses the exponential mechanism to select, edge by edge, a maximum spanning tree over the attributes, scored by the estimated mutual information of each pair.
3. It measures the two-way marginals on the tree's edges.

Private-PGM then fits the graphical model that best explains the noisy measurements, and records are sampled from it. Every step after the measurements is post-processing. The single, non-adaptive tree explains MST's stability across seeds and its plateau in three-way fidelity.

**AIM** [7] starts like MST with noisy one-way marginals. Over rounds $t = 1,\dots,T$ it then:

1. uses the exponential mechanism to select the workload marginal whose current model estimate is worst, after subtracting the error expected from noise alone, $\sqrt{2/\pi}\,\sigma$ times the number of cells;
2. measures it with Gaussian noise;
3. refits the model.

Its budget split is 90% for measurements and 10% for selections (see (7)). When a new measurement barely changes the model's estimate, the next measurements are made more precise: σ is halved and the selection ε doubled. When the remaining budget can no longer pay for two rounds, it is spent on one final round. Each round's refit runs mirror descent, which is where most of AIM's runtime goes.

**PrivBayes** [9] splits a pure-DP budget ε between two phases — 30% and 70% in the implementation used:

1. structure learning: an exponential mechanism greedily chooses each attribute's parents, scored by mutual information;
2. measurement of the resulting conditional distributions with Laplace noise.

Sampling then follows the network's topological order. Because Laplace noise on small conditional tables at ε = 0.5 can wipe out the signal entirely, PrivBayes collapses at low budgets in this study.

**Pure versus approximate DP.** PrivBayes's pure ε-DP and the (ε, 10⁻⁵)-DP of AIM and MST are different guarantees. Pure DP is stronger at the same ε: it allows no failure probability, and it composes more simply under group privacy. Comparing the methods "at the same ε" therefore slightly favours AIM and MST. The reports and the dashboard state the guarantee type every time, and readers should not treat the ε axes of Fig. 12 as strictly equivalent across mechanism types.

## C. Privacy Budget Management {-}

Each run has one fixed budget. The study sweeps ε ∈ {0.5, 1, 3, 5, 10} with δ = 10⁻⁵ for AIM and MST; δ = 10⁻⁵ is below $1/n = 4.2\times10^{-4}$. Every run is an *independent* release from the same training data, and the runs are not meant to be published together. If all 35 DP datasets in `results/synthetic_data/` were released, sequential composition would apply:

$$\varepsilon_{\mathrm{total}} = \sum_{i=1}^{k}\varepsilon_i ,\qquad \rho_{\mathrm{total}}=\sum_{i=1}^{k}\rho_i \qquad\qquad (6)$$

By (6), the total would be 3 × (0.5 + 1 + 3 + 5 + 10) = 58.5 for the MST runs alone. This point matters for deployment. A production system needs a budget ledger that records every release from a dataset (Section XVIII), and the LLM layer must present each dataset as a separate release with its own ε, never as one of many views of the same protected data.

**AIM's internal budget split.** In the snsynth implementation, AIM converts $(\varepsilon,\delta)$ to a zCDP budget $\rho$ with OpenDP's numerical zCDP-to-approximate-DP conversion. This is a binary search that is slightly tighter than the closed form (3). It then sets the initial noise scale from the planned number of rounds $T$ as $\sigma_0=\sqrt{T/(2\cdot0.9\,\rho)}$, and first measures all $d$ one-way marginals. Each one-way measurement costs $1/(2\sigma_0^2)$, so the initial step uses

$$\rho_{\mathrm{init}} = \frac{d}{2\sigma_0^{2}} = 0.9\,\rho\,\frac{d}{T}\;<\;\rho \;\iff\; T > 0.9\,d \qquad\qquad (7)$$

With $d = 14$ columns, the cap of $T = 60$ spends 21% of $\rho$ on one-way marginals and leaves the rest for adaptive rounds. During testing, a cap of $T = 5$ made $\rho_{\mathrm{init}} = 2.52\,\rho$. The remaining budget went negative and the run failed with undefined (NaN) selection probabilities.

The cap therefore has a hard lower bound, and it trades adaptivity for runtime. The paper's default of $16d = 224$ rounds was measured at about 35–40 minutes per run on this dataset, which is why the cap was applied. The cap changes how the budget is spent, not the $(\varepsilon,\delta)$ bound.

**A budget ledger for deployment.** The study releases independent datasets for comparison. A deployment would instead keep a ledger per source dataset, with:

- a lifetime cap $\varepsilon_{\max}$;
- an entry for each release (date, mechanism, ε, δ, purpose, approver);
- a rule that a release is refused when the composed total would exceed the cap.

The LLM layer needs no ledger entry of its own because it only post-processes approved releases. A version that queried the real data would.

**Choosing δ.** δ should be well below $1/n$, so that the "small failure probability" cannot amount to revealing one record outright. δ = 10⁻⁵ against $n$ = 2,400 satisfies this by a factor of about 40. For larger datasets the same δ would need revisiting [32].

## D. Workflow {-}

Fig. 8 contrasts the implemented select–measure–generate workflow with DP-SGD. In DP-SGD, each per-example gradient $g_i$ is clipped to norm $C$, Gaussian noise is added to the average of a batch $B$, and an accountant tracks the cumulative loss [31][30]:

$$\theta_{t+1}=\theta_t-\eta\Big(\tfrac{1}{|B|}\textstyle\sum_{i\in B}\bar g_i+\mathcal{N}(0,\sigma^2C^2\mathbf{I})\Big),\quad \bar g_i=g_i/\max\!\big(1,\lVert g_i\rVert_2/C\big) \qquad\qquad (8)$$

The update rule (8) would be needed to make CTGAN or TVAE private, or to fine-tune an LLM on sensitive text [42][43]. It is **not** used in this project. CTGAN and TVAE run without it and are treated strictly as non-private baselines.

![Fig. 8. Differential privacy integration workflow. Top: implemented (AIM/MST select–measure–generate; PrivBayes). Bottom, dashed: DP-SGD, discussed only.](figures/diagrams/fig07_dp_integration_workflow.png){width=6.3in}

## E. Adaptive Privacy Strategies {-}

AIM is itself adaptive *within* a release: it spends budget where the current model is worst. Adaptive strategies *across* releases are not implemented. Examples include choosing ε per dataset from a utility target, or reserving budget for DP domain discovery. They are proposed in Section XXI.


# X. Generative AI Knowledge Discovery Layer {-}

## A. Purpose and Boundaries {-}

The knowledge-discovery layer answers one question: *what does this DP synthetic dataset suggest, and how far can the suggestion be trusted?* It is an extension added in this iteration (`knowledge_discovery/`). It is reached from a *Workspace* switch in the dashboard sidebar, so it works from saved results without loading the original data.

Its boundaries are explicit:

- it is **not** a trained or fine-tuned LLM;
- it is **not** a retrieval-augmented generation system;
- it gives **no** DP guarantee of its own.

It is a single, auditable LLM call over aggregate statistics.

## B. Workflow {-}

Fig. 9 shows the implemented workflow.

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
   - *Live mode* calls the Anthropic Messages API [57] with `claude-opus-5-5`, medium effort, and the server-side refusal fallback. The key is read from the `ANTHROPIC_API_KEY` environment variable or a git-ignored `.env` file.
   - *Demo mode* builds a deterministic template from the same summary. It is labelled in the UI, the output and the audit record as **not** LLM output.
6. **Transparency and audit.** The UI shows the exact system prompt and user message before generation, and offers the summary for download. Each request writes an audit record with the prompt version, a SHA-256 hash of the payload, the mode, model, stop reason, token usage, and whether a request was actually sent.

![Fig. 9. Knowledge-discovery workflow (implemented). The original dataset has no path into the pipeline.](figures/diagrams/fig08_llm_knowledge_discovery_workflow.png){width=6.3in}

## C. Payload Design Rationale {-}

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

## D. Failure Modes and How They Are Handled {-}

Table VI lists how the layer behaves when something goes wrong. Every row is exercised by a test (Appendix B).

Table: TABLE VI. Failure modes of the LLM layer and their handling

| Failure | Handling |
|---|---|
| API key missing | Clear message pointing to `.env.example`; no request is attempted, and the audit records `user_message_sent_to_api = false` |
| Key rejected (401) or lacking permission (403) | Typed SDK exceptions mapped to actionable messages |
| Unknown model (404) | Message naming the `KD_MODEL` setting |
| Rate limit (429), server error (5xx), network failure | SDK retries twice, then shows a retry-later message |
| Request rejected (400) | Message with the API's own explanation, e.g. if the fallback parameter were unavailable for an account |
| Safety refusal | `stop_reason = refusal` reported as an error, not as an empty explanation |
| Truncation at `max_tokens` | Text kept and marked as truncated |
| Empty response | Reported as an error |

## E. Verification Status of the LLM Component {-}

No Anthropic API key was available while this work was carried out. A Claude Pro chat subscription does not include API credits. The verification status is therefore stated precisely in four parts.

**Verified by execution:**

- request construction through the real `anthropic` 1.13 SDK against a local mock HTTP server: model, beta flag, fallback parameter, and the key present only in the authentication header;
- the absence of any of the first 300 original rows in the request body;
- that the original file is never opened;
- small-cell suppression;
- clear errors for a missing key and for HTTP 400, 401, 429 and 500, connection failure, refusal and empty responses;
- the demo-mode path in the running dashboard.

**Not verified:**

- that the live API accepts the request;
- the content and quality of real model explanations.

**No real LLM output appears in this report.** The demo excerpt in Appendix D is template text.

## F. Knowledge Utility {-}

Post-processing guarantees that the explanation is no *less* private than the DP dataset. It says nothing about whether the explanation is *true*. The layer therefore needs a measure of how faithfully its inputs reflect the population. Following the idea of epistemic parity [41], an offline evaluation (`analysis/knowledge_utility.py`) compares the target-rate cells that appear in both summaries — synthetic $s_{\mathrm{syn}}$ and real training split $s_{\mathrm{real}}$ — over the set $C$ of shared (column, level) pairs:

$$\mathrm{KU} \;=\; 1-\frac{1}{|C|}\sum_{(c,v)\in C}\big|\,s_{\mathrm{syn}}(c,v)-s_{\mathrm{real}}(c,v)\,\big| \qquad\qquad (9)$$

Two further measures complement KU: the Spearman rank correlation ρ between the two sets of group rates, and *top-1 agreement*, the share of columns whose highest-rate level is the same in both. These are evaluation-only quantities: they consult the real data and must never be computed inside the released pipeline. Results are reported in Section XIV.

## G. Controlled Knowledge Dissemination {-}

Dissemination is controlled at four points:

- what may be summarised — DP datasets only;
- what may leave the machine — suppressed and rounded aggregates;
- how the output is framed — hypotheses with an explicit limitations section;
- what is recorded — audit records.

A production deployment would add role-based access to the page, retention limits for audit records, and a contractual position with the LLM provider on data use and region (Section XVIII).

# XI. Explainability, Transparency, and Trust Assessment {-}

## A. Explainability Mechanisms {-}

Explainability here means that a reviewer can trace every claim back to its evidence. Five mechanisms provide this (Fig. 10):

1. **Formal statements** generated from code: $(\varepsilon,\delta)$, mechanism name, and pure versus approximate DP.
2. **Empirical privacy evidence:** MIA AUC, TPR at FPR 0.1, and distance to closest record.
3. **Quality evidence:** fidelity, utility, rare-pattern and fairness metrics.
4. **Provenance:** run identifier, seed, configuration, disclosed deviations, and the duplicate policy.
5. **LLM transparency:** the shown payload, prompt version and audit hash.

The system shows these indicators side by side, in line with model-card and datasheet practice [51][50].

![Fig. 10. Explainability, transparency and trust assessment layer.](figures/diagrams/fig09_explainability_trust_layer.png){width=6.2in}

## B. What Can and Cannot Be Explained {-}

DP changes what explanation means. Some things *can* be explained precisely: the mechanism, the budget, which statistics were measured (for MST, which tree edges), and how the synthetic data compare with the real data on aggregate metrics. Other things *cannot* be explained, by design:

- which real individuals influenced a given synthetic record — there is no such correspondence;
- why a specific synthetic record has particular values, beyond "it was sampled from the fitted model".

Two consequences follow. Explanations must operate at the level of the population, and statements that sound individual-level ("a 45-year-old female executive earns…") should be read as statements about a model, not about a person. The system prompt asks the LLM never to describe individuals for this reason.

Explaining the LLM's *own* reasoning is out of scope. The layer offers *input transparency* — the exact payload and prompt are shown — and *output framing* — required sections and a hypothesis register. It does not offer insight into the model's internals.

## C. A Reviewer's Workflow {-}

The intended use of the evidence is a short review before acting on any LLM-generated insight:

1. Check the guarantee panel: ε, δ, pure or approximate DP, and the round cap if any.
2. Check the quality context: is the 3-way TVD low and the utility retention high for this dataset?
3. For each claimed pattern, find the supporting numbers in the shown payload.
4. For patterns involving protected attributes, or patterns that will drive a decision, request the corresponding statistic from the custodian on the governed real data.
5. Record the decision.

The audit record links the explanation to its exact input through the SHA-256 payload hash.

## D. Transparency Reporting {-}

A release published from this framework should carry a short transparency report. All of its fields are already produced by the code:

- dataset and purpose;
- mechanism and guarantee, including the domain assumption;
- ε, δ and the composed total if several releases exist;
- fidelity, utility, fairness and rare-pattern summaries against the stated thresholds;
- empirical attack results *with their stated weakness*;
- known artefacts, such as the spurious associations found by the knowledge-utility check;
- a contact for questions.

This mirrors the model-card idea [51] applied to a data release, and NIST's call to state the unit of privacy and the assumptions [6].

## E. Trust Assessment {-}

The section plan calls for a trust-score equation. A single weighted score would hide trade-offs and invite gaming, so the trust assessment is defined as an *evidence vector* with explicit acceptance thresholds $\tau$ chosen by the data owner:

$$\mathbf{T}=\big(\varepsilon,\ \delta,\ \mathrm{AUC}_{\mathrm{MIA}},\ 1-\mathrm{TVD}_3,\ R_{F1},\ \mathrm{KU},\ \Delta_{\mathrm{DP}}\big),\qquad \mathrm{accept}\iff \bigwedge_j\, T_j \trianglelefteq \tau_j \qquad\qquad (10)$$

Here $\trianglelefteq$ means "no worse than" in each component's direction. For example, with $\varepsilon\le3$, $|\mathrm{AUC}-0.5|\le0.05$, $R_{F1}\ge 75\%$ and $\mathrm{KU}\ge0.9$, the AIM ε = 3 dataset would pass, while the MST ε = 3 datasets would fail on $R_{F1}$ and KU (Section XIV). Adding a fairness threshold such as $\Delta_{\mathrm{DP}}\le0.2$ would reject the AIM dataset as well, since its value is 0.48 against 0.17 for a model trained on real data. This shows why the components must be inspected together. The thresholds above are illustrative and were not elicited from stakeholders.

## F. Auditability {-}

Auditability rests on the append-only JSON-lines experiment log, the per-request audit records, and version control. The verification script shows the log is auditable in practice:

- it identified the two duplicate run identifiers;
- it confirmed that every configuration matches its declared guarantee;
- it reproduced 733 of 738 metric values exactly from the saved data.

The audit trail also surfaced a defect: the original dashboard counted 43 runs instead of 41. That defect was fixed.


# XII. Experimental Setup {-}

## A. Dataset and Splits {-}

The data are the 3,000-record Adult sample described in Section V. A stratified 80/20 split on *income* with seed 42 gives 2,400 training and 600 test records. Every generator is fit on the training split, and every synthetic dataset has 2,400 rows (size multiplier 1.0). The test split is used only for scoring: TSTR/TRTR utility, fairness and non-member candidates for the MIA. The sensitive attribute for fairness is *sex* (33.0% female).

## B. Generators and Configurations {-}

Table VII lists the 41 configurations of the sweep (`experiments/config.py`, run with `run_sweep.py`). Additional settings:

- CTGAN and TVAE use 300 epochs and a batch size of 500. They use a GPU if one is available, and the hardware of the original runs was not recorded.
- AIM's rounds are capped at 60, as explained in Section IX.
- Within each family, the seeds are 42, 43 and 44.

The DP wrappers do not forward the seed to the underlying synthesizers. For DP methods the seed therefore controls only the evaluation randomness (3-way query sampling, rare-combination sampling, MIA candidate sampling and inverse binning). The generators' own randomness is uncontrolled.

Table: TABLE VII. Experimental configuration

| Method | Library (version) | Guarantee | ε values | δ | Seeds | Other settings | Runs |
|---|---|---|---|---|---|---|---|
| AIM | smartnoise-synth 1.0.8, mbi 1.1.0 | (ε, δ)-DP, zCDP | 0.5, 1, 3, 5, 10 | 10⁻⁵ | 1 | rounds ≤ 60 (paper: 16·d = 224) | 5 |
| MST | smartnoise-synth 1.0.8, mbi 1.1.0 | (ε, δ)-DP, zCDP | 0.5, 1, 3, 5, 10 | 10⁻⁵ | 3 | — | 15 |
| PrivBayes | synthetic_data_generation 0.1.14 | pure ε-DP | 0.5, 1, 3, 5, 10 | 0 | 3 | numpy.product shim | 15 |
| CTGAN | ctgan 0.12.1 | none | — | — | 3 | 300 epochs, batch 500 | 3 |
| TVAE | ctgan 0.12.1 | none | — | — | 3 | 300 epochs, batch 500 | 3 |
| **Preprocessing (all)** | in-house | — | — | — | — | 10 quantile bins + spike bin (≥ 30%); rare < 1% → `__RARE__` | **41** |

## C. Implementation Environment {-}

- **Software:** Python 3.11; pandas 2.3.3, NumPy 2.4.6, scikit-learn 1.8.0, XGBoost 3.2.0, PyTorch 2.14.0, Streamlit 1.64.0, OpenDP 0.14.2, anthropic 1.13.0.
- **Pinning:** the exact versions are pinned in `constraints.txt`, recovered from the original environment.
- **Original runs:** the 43 logged runs were executed on 18 September 2026 on the original authors' Windows machine. Its hardware specification was not recorded. **[CONFIRM]**
- **Verification environment:** a fresh environment with the same package versions on Windows 11, using CPU only, for re-evaluation, testing and the dashboard checks.

## D. Benchmark Scenarios {-}

The evaluation covers three scenarios:

- **S1 — ε sweep.** Each DP method at five budgets, for RQ2.
- **S2 — cross-family comparison.** DP methods at ε = 3 against the non-DP baselines, for RQ1.
- **S3 — knowledge discovery.** The aggregate summary of each DP dataset compared with the same summary on real data, plus dashboard operation of the LLM layer, for RQ3.

Fig. 11 shows how runs flow into the evaluation and verification stages.

![Fig. 11. Experimental evaluation framework.](figures/diagrams/fig10_experimental_evaluation_framework.png){width=6.3in}

## E. Threats to Validity {-}

**Internal validity.**

- The DP generators are unseeded, so a single run's numbers include generator randomness. AIM's single seed leaves no way to separate signal from that noise.
- All methods share one preprocessing protocol. That is fair, but it may favour methods whose assumptions it matches.

**Construct validity.**

- The 1-NN membership attack measures only one kind of leakage, and the near-duplicate threshold degenerates to exact matching.
- The fairness metric depends on one classifier.
- Knowledge utility covers only target rates by single attributes.

**External validity.** One small census sample; findings may not hold for wider, larger or differently distributed data.

**Conclusion validity.** No significance testing. Reported differences smaller than about two seed standard deviations should not be read as rankings.

## F. Verification Protocol {-}

Because the report must rest only on saved outputs, `analysis/verify_results.py` performs five steps:

1. It checks log integrity (record count, unique identifiers, statuses).
2. It de-duplicates by keeping the latest completed record per identifier, consistent with the CSV on disk.
3. It checks each configuration's privacy parameters.
4. It recomputes every metric from the saved CSV with the project's own evaluation code and compares it with the logged value, using a tolerance of 10⁻⁶.
5. It computes the TRTR reference and a real-data fairness reference, neither of which was logged originally.

No generator was re-trained for the reported results. Re-training would not reproduce the saved data, because the DP generators are unseeded.

# XIII. Evaluation Metrics {-}

## A. Why These Metrics {-}

The metric set follows recent DP-synthesis benchmarks [34][33], with three additions.

Fidelity is measured at three levels, because each level can fail independently. One-way marginals can be perfect while correlations are wrong, and pairwise correlations can be right while three-way structure is broken.

Utility uses the TSTR protocol with three model families, so that one model's inductive bias does not decide the result. Retention relative to TRTR puts all numbers on the same scale.

The three additions:

1. **Empirical privacy.** It cannot certify privacy, but it can reveal gross failures such as copying, and it shows how weak or strong a particular attack is.
2. **Fairness and rare patterns.** DP's harms concentrate there [26][27].
3. **Knowledge utility.** This is the metric the LLM layer depends on.

No metric is aggregated into an overall score.

## B. Definitions {-}

Table VIII defines the metrics; the main formulas follow. Real training data are denoted $r$ and synthetic data $s$.

**Fidelity.** For each numerical column, the Kolmogorov–Smirnov statistic between the empirical CDFs is

$$\mathrm{KS}=\sup_x\big|F_r(x)-F_s(x)\big| \qquad\qquad (11)$$

and for each categorical column, the total variation distance is

$$\mathrm{TVD}(P_r,P_s)=\tfrac12\textstyle\sum_{v}\big|P_r(v)-P_s(v)\big| \qquad\qquad (12)$$

The *3-way TVD* applies (12) to the joint distribution of 30 randomly chosen triples of categorical columns and averages the results. It tests whether higher-order structure survives. Correlation fidelity is measured by the Frobenius norm of the difference between Pearson matrices, and by the mean absolute difference in bias-corrected Cramér's V.

**Utility.** Train-on-synthetic, test-on-real (TSTR) F1 is computed for Logistic Regression, Random Forest (200 trees) and XGBoost (200 trees) on the real test split, with one-hot encoding fixed to the training vocabulary. *Utility retention* is

$$R_{F1}=100\cdot \mathrm{F1}_{\mathrm{TSTR}}\,/\,\mathrm{F1}_{\mathrm{TRTR}} \qquad\qquad (13)$$

**Empirical privacy.** Members are 600 training records and non-members are 600 test records. Each candidate $x$ is scored by its negative distance to the nearest synthetic record in a standardised, one-hot feature space $\phi$:

$$\mathrm{score}(x)=-\min_{y\in\tilde D}\lVert\phi(x)-\phi(y)\rVert_2 \qquad\qquad (14)$$

The attack AUC and the TPR at FPR = 0.1 are reported. An AUC of 0.5 means the attack does no better than chance. The *distance to closest record* (DCR) and the share of synthetic records at or below the 1st percentile of real-to-real nearest-neighbour distances ("near-duplicates") are also reported.

**Fairness.** A Logistic Regression is trained on synthetic data and scored on the real test set, grouped by sex. The metrics are the demographic-parity difference and the equalised-odds gap [58]:

$$\Delta_{\mathrm{DP}}=\max_g P(\hat y=1\mid A=g)-\min_g P(\hat y=1\mid A=g),\qquad \Delta_{\mathrm{EO}}=\max\big(\Delta_{\mathrm{TPR}},\Delta_{\mathrm{FPR}}\big) \qquad\qquad (15)$$

**Rare patterns.** The rare-pattern metrics are:

- the share of categories with frequency below 1% in the real training data that disappear from the synthetic data;
- the same for 2-way value combinations below 0.5%, across all 36 pairs of the 9 categorical columns;
- the largest absolute change in class share.

**Runtime.** Fit and sample wall-clock time, in seconds.

**Knowledge utility.** KU, Spearman ρ and top-1 agreement, as defined in (9).

Table: TABLE VIII. Evaluation metrics definition

| Dimension | Metric | Range / ideal | Meaning and caveats |
|---|---|---|---|
| Fidelity (1-way) | Mean KS (numerical) | [0, 1], ↓ | DP numerics are reconstructed uniformly within bins, which floors KS |
| Fidelity (1-way) | Mean TVD (categorical) | [0, 1], ↓ | Matches marginals; blind to correlations |
| Fidelity (higher-order) | Mean 3-way TVD | [0, 1], ↓ | 30 sampled triples; seed-dependent sample |
| Correlation | ΔCramér's V; ‖ΔPearson‖ (Frobenius) | ≥ 0, ↓ | Pairwise structure |
| Utility | TSTR F1 (LR, RF, XGB); retention $R_{F1}$ | [0, 1] / %, ↑ | Positive class `>50K`; TRTR F1 = 0.583 / 0.620 / 0.647 |
| Privacy (formal) | ε, δ, mechanism | ↓ ε | Holds only given the public-domain assumption (Section VIII) |
| Privacy (empirical) | MIA AUC; TPR@FPR 0.1 | 0.5 ideal; ↓ TPR | Weak 1-NN attack; train/test overlap of 18 records |
| Privacy (empirical) | Mean DCR; % near-duplicates | ↑ DCR; ↓ % | Threshold = 0 here because of duplicate rows ⇒ counts exact copies only |
| Rare patterns | % rare categories / combinations lost | [0, 100], ↓ | Only 4 rare categories exist |
| Fairness | ΔDP, ΔEO, F1 gap (sex) | [0, 1], ↓ | Single LR per run; noisy; real-data reference ΔDP = 0.169 |
| Cost | Fit + sample time (s) | ↓ | Hardware not recorded; varies between repeats (AIM ε=3: 181 s vs 436 s) |
| Knowledge | KU, Spearman ρ, top-1 agreement | ↑ | Offline only — uses real data |


# XIV. Results and Findings {-}

All numbers in this section are read from `results/verified/`. They are means ± standard deviations over seeds; AIM has one seed per ε, marked †. Standard deviations over three seeds are indicative only.

## A. Verification of the Saved Results {-}

**Log integrity.**

- The experiment log contains **43 records but 41 unique run identifiers**, all with status `completed`.
- `AIM_eps3.0_seed42` and `PrivBayes_eps3.0_seed42` each appear twice. The second runs started at 20:42 on 18 September 2026 and overwrote the corresponding CSVs.
- The two records of each pair differ (Table XVIII). For AIM ε = 3, the 3-way TVD was 0.220 versus 0.189 and the fit time 181 s versus 436 s. This is direct evidence of run-to-run variability from the unseeded generators and of runtime sensitivity to machine load.

**De-duplication and configuration checks.**

- The analysis uses the later record of each pair. That record is the one consistent with the data on disk.
- All 41 configurations pass the checks: ε matches the run identifier; δ = 10⁻⁵ for AIM and MST and δ = 0 for PrivBayes; AIM's round cap is 60; and CTGAN and TVAE carry "no formal guarantee".
- All 41 CSVs are present and have 2,400 rows each.

**Re-evaluation.** Recomputing the metrics from the CSVs reproduced **733 of 738 logged values exactly** (Appendix B, Table XVII). The five exceptions are MIA AUC values that differ by at most 2.8 × 10⁻⁶. This is consistent with floating-point and nearest-neighbour tie effects.

**TRTR reference.** The TRTR reference, which was not stored in the log, was recomputed: F1 = 0.583 (LR), 0.620 (RF) and 0.647 (XGBoost); XGBoost AUROC = 0.886.

**What could not be reproduced.** The synthetic data themselves, which would need seeded generators, and the runtimes, which depend on the hardware.

## B. Utility (RQ1, RQ2) {-}

Table IX and Fig. 12 show the TSTR results.

- **At ε ≥ 3, AIM and PrivBayes are close to the best non-private baseline.** XGBoost F1 retention (13) was 81% (AIM, ε = 3), 85% (AIM, ε = 5), 82% (PrivBayes, ε = 3) and 79% (PrivBayes, ε = 5), against 85% for TVAE.
- **MST trails.** Its retention was 48–69% at every ε, and it barely improved beyond ε = 1. That puts it close to CTGAN's level (62%) rather than to the other DP methods.
- **PrivBayes collapses at ε = 0.5.** Logistic Regression F1 fell to 0.014 ± 0.023 (2% retention): the model trained on that data almost never predicts the positive class.
- **CTGAN is the least stable** (XGBoost F1 0.404 ± 0.163).
- **AIM is not monotonic in ε** (XGBoost F1 0.549 at ε = 5 but 0.496 at ε = 10). With a single seed, such differences are within the run-to-run variation seen in Table XVIII.
- **TVAE exceeds the real-data ceiling for one model.** Its Logistic Regression F1 (0.598) exceeds the TRTR value (0.583), giving 103% retention. Retention above 100% is possible on a 600-row test set and is reported, not clipped.

Table: TABLE IX. TSTR utility across the ε sweep (mean ± std over seeds; † = single seed)

| Configuration | F1 LR | F1 RF | F1 XGB | AUROC XGB | $R_{F1}$ XGB (%) |
|---|---|---|---|---|---|
| AIM ε=0.5 | 0.354† | 0.397† | 0.357† | 0.601† | 55.3 |
| AIM ε=1 | 0.449† | 0.471† | 0.459† | 0.722† | 71.0 |
| AIM ε=3 | 0.485† | 0.546† | 0.525† | 0.758† | 81.2 |
| AIM ε=5 | 0.534† | 0.519† | 0.549† | 0.835† | 84.8 |
| AIM ε=10 | 0.538† | 0.555† | 0.496† | 0.780† | 76.7 |
| MST ε=0.5 | 0.325 ± 0.071 | 0.296 ± 0.150 | 0.313 ± 0.114 | 0.609 ± 0.078 | 48.3 |
| MST ε=1 | 0.396 ± 0.029 | 0.396 ± 0.055 | 0.420 ± 0.061 | 0.725 ± 0.054 | 65.0 |
| MST ε=3 | 0.392 ± 0.036 | 0.348 ± 0.046 | 0.399 ± 0.032 | 0.755 ± 0.032 | 61.6 |
| MST ε=5 | 0.476 ± 0.034 | 0.382 ± 0.026 | 0.439 ± 0.017 | 0.774 ± 0.034 | 67.9 |
| MST ε=10 | 0.465 ± 0.007 | 0.428 ± 0.011 | 0.447 ± 0.015 | 0.776 ± 0.011 | 69.0 |
| PrivBayes ε=0.5 | 0.014 ± 0.023 | 0.030 ± 0.031 | 0.170 ± 0.037 | 0.595 ± 0.028 | 26.2 |
| PrivBayes ε=1 | 0.439 ± 0.046 | 0.381 ± 0.063 | 0.411 ± 0.033 | 0.750 ± 0.012 | 63.6 |
| PrivBayes ε=3 | 0.553 ± 0.015 | 0.562 ± 0.023 | 0.530 ± 0.014 | 0.814 ± 0.005 | 81.9 |
| PrivBayes ε=5 | 0.525 ± 0.021 | 0.506 ± 0.035 | 0.514 ± 0.032 | 0.807 ± 0.015 | 79.4 |
| PrivBayes ε=10 | 0.485 ± 0.101 | 0.483 ± 0.055 | 0.506 ± 0.062 | 0.814 ± 0.011 | 78.3 |
| CTGAN (non-DP) | 0.477 ± 0.118 | 0.436 ± 0.138 | 0.404 ± 0.163 | 0.780 ± 0.030 | 62.4 |
| TVAE (non-DP) | 0.598 ± 0.010 | 0.572 ± 0.029 | 0.547 ± 0.046 | 0.853 ± 0.010 | 84.5 |
| **TRTR (real data)** | 0.583 | 0.620 | 0.647 | 0.886 | 100 |


![Fig. 12. Privacy budget versus TSTR F1 (XGBoost). Error bars: ±1 std over 3 seeds (AIM: 1 seed). Dashed: non-DP baselines; dotted: real-data TRTR.](figures/fig_res_01_epsilon_vs_f1_xgboost.png){width=4.6in}

## C. Fidelity {-}

Table X gives the fidelity metrics.

**One-way fidelity.**

- Categorical TVD falls steadily with ε for AIM and MST, reaching 0.003–0.009 at ε = 10. PrivBayes plateaus at about 0.034.
- Numerical KS (11) is about 0.08–0.09 for every DP run except PrivBayes at ε = 0.5 (0.145). This floor comes largely from reconstructing values uniformly within bins.
- The non-private generators have *worse* one-way fidelity: KS 0.326 (CTGAN) and 0.248 (TVAE), TVD 0.095 and 0.117. Mode-specific normalisation struggles with the spike-inflated columns.

**Higher-order fidelity** (Fig. 13).

- AIM has the lowest 3-way TVD at ε = 0.5 (0.224, against 0.318 for MST and 0.304 for PrivBayes).
- AIM and PrivBayes improve with ε to about 0.14–0.15 at ε = 10.
- MST plateaus at about 0.24, because a tree of two-way marginals cannot represent three-way structure. The difference in Cramér's V shows the same pattern.
- CTGAN (0.269) and TVAE (0.288) are worse than every DP method at ε ≥ 3.

Table: TABLE X. Statistical fidelity across the ε sweep (lower is better) (mean ± std over seeds; † = single seed)

| Configuration | Mean KS | Mean TVD | 3-way TVD | ΔCramér's V |
|---|---|---|---|---|
| AIM ε=0.5 | 0.079† | 0.043† | 0.224† | 0.128† |
| AIM ε=1 | 0.076† | 0.026† | 0.242† | 0.129† |
| AIM ε=3 | 0.076† | 0.011† | 0.189† | 0.079† |
| AIM ε=5 | 0.076† | 0.008† | 0.157† | 0.083† |
| AIM ε=10 | 0.078† | 0.009† | 0.145† | 0.070† |
| MST ε=0.5 | 0.089 ± 0.014 | 0.045 ± 0.005 | 0.318 ± 0.028 | 0.166 ± 0.001 |
| MST ε=1 | 0.079 ± 0.008 | 0.024 ± 0.002 | 0.260 ± 0.016 | 0.131 ± 0.019 |
| MST ε=3 | 0.078 ± 0.001 | 0.009 ± 0.001 | 0.253 ± 0.020 | 0.139 ± 0.007 |
| MST ε=5 | 0.076 ± 0.001 | 0.005 ± 0.001 | 0.237 ± 0.005 | 0.133 ± 0.003 |
| MST ε=10 | 0.077 ± 0.002 | 0.003 ± 0.000 | 0.238 ± 0.008 | 0.140 ± 0.003 |
| PrivBayes ε=0.5 | 0.145 ± 0.024 | 0.089 ± 0.003 | 0.304 ± 0.029 | 0.179 ± 0.003 |
| PrivBayes ε=1 | 0.089 ± 0.008 | 0.061 ± 0.007 | 0.239 ± 0.024 | 0.136 ± 0.002 |
| PrivBayes ε=3 | 0.090 ± 0.010 | 0.037 ± 0.003 | 0.176 ± 0.017 | 0.086 ± 0.016 |
| PrivBayes ε=5 | 0.093 ± 0.018 | 0.034 ± 0.005 | 0.157 ± 0.013 | 0.075 ± 0.018 |
| PrivBayes ε=10 | 0.093 ± 0.005 | 0.034 ± 0.006 | 0.142 ± 0.015 | 0.065 ± 0.010 |
| CTGAN (non-DP) | 0.326 ± 0.024 | 0.095 ± 0.004 | 0.269 ± 0.010 | 0.085 ± 0.004 |
| TVAE (non-DP) | 0.248 ± 0.023 | 0.117 ± 0.010 | 0.288 ± 0.022 | 0.087 ± 0.016 |


![Fig. 13. Privacy budget versus mean 3-way marginal TVD (lower is better).](figures/fig_res_03_epsilon_vs_3way_error.png){width=4.6in}

## D. Empirical Privacy {-}

**The attack cannot separate the methods.** The 1-NN membership attack (14) gave a mean AUC between 0.492 and 0.510 for every configuration, **including the non-private CTGAN and TVAE** (Fig. 14, Table XI). TPR at FPR 0.1 was 0.07–0.11, which is what random guessing gives.

**Why this is not evidence of privacy.** The attack is weak, and the measurement is diluted in two ways:

1. 18 records are shared by the member and non-member sets because the data contain duplicates.
2. The near-duplicate threshold is 0, so only exact copies are counted.

So the attack cannot distinguish these methods; it does *not* establish that the non-DP baselines are safe. Stronger, density-based attacks are known to succeed against non-DP generators [1][16].

**Signals of memorisation.** The distance-based diagnostics do reveal them:

- TVAE's mean distance to the closest real record (0.74) is less than half that of every other method (≥ 1.51).
- TVAE emitted exact copies of training rows in two of its three runs (2, 0 and 1 rows).
- No DP run produced an exact copy.
- For the DP methods, DCR shrinks as ε grows — for example, AIM from 1.86 to 1.51 — as expected from weaker noise.

![Fig. 14. Privacy budget versus distance-based MIA AUC. Values near 0.5 for all methods, including non-DP baselines, indicate a weak attack rather than safety.](figures/fig_res_05_epsilon_vs_mia_auc.png){width=4.6in}

Table: TABLE XI. Empirical privacy and runtime (mean ± std over seeds; † = single seed)

| Configuration | MIA AUC | TPR@FPR 0.1 | Mean DCR ↑ | Exact copies (%) | Fit time (s) |
|---|---|---|---|---|---|
| AIM ε=0.5 | 0.496† | 0.077† | 1.86† | 0.000† | 71.4† |
| AIM ε=1 | 0.499† | 0.102† | 1.67† | 0.000† | 51.9† |
| AIM ε=3 | 0.496† | 0.097† | 1.61† | 0.000† | 436.2† |
| AIM ε=5 | 0.495† | 0.093† | 1.54† | 0.000† | 244.3† |
| AIM ε=10 | 0.510† | 0.110† | 1.51† | 0.000† | 626.0† |
| MST ε=0.5 | 0.497 ± 0.015 | 0.083 ± 0.006 | 1.79 ± 0.06 | 0.000 ± 0.000 | 58.2 ± 9.5 |
| MST ε=1 | 0.501 ± 0.017 | 0.076 ± 0.003 | 1.72 ± 0.03 | 0.000 ± 0.000 | 55.4 ± 26.3 |
| MST ε=3 | 0.495 ± 0.014 | 0.072 ± 0.019 | 1.63 ± 0.02 | 0.000 ± 0.000 | 38.8 ± 9.8 |
| MST ε=5 | 0.496 ± 0.018 | 0.077 ± 0.016 | 1.59 ± 0.00 | 0.000 ± 0.000 | 26.5 ± 5.4 |
| MST ε=10 | 0.492 ± 0.008 | 0.084 ± 0.019 | 1.56 ± 0.00 | 0.000 ± 0.000 | 25.3 ± 3.4 |
| PrivBayes ε=0.5 | 0.500 ± 0.000 | 0.098 ± 0.026 | 2.48 ± 0.13 | 0.000 ± 0.000 | 0.5 ± 0.5 |
| PrivBayes ε=1 | 0.507 ± 0.016 | 0.100 ± 0.003 | 2.17 ± 0.03 | 0.000 ± 0.000 | 1.6 ± 0.4 |
| PrivBayes ε=3 | 0.501 ± 0.014 | 0.088 ± 0.012 | 2.05 ± 0.02 | 0.000 ± 0.000 | 5.0 ± 1.3 |
| PrivBayes ε=5 | 0.497 ± 0.009 | 0.083 ± 0.009 | 2.05 ± 0.05 | 0.000 ± 0.000 | 11.5 ± 1.2 |
| PrivBayes ε=10 | 0.502 ± 0.011 | 0.109 ± 0.014 | 1.78 ± 0.04 | 0.000 ± 0.000 | 21.0 ± 0.3 |
| CTGAN (non-DP) | 0.499 ± 0.016 | 0.096 ± 0.010 | 2.10 ± 0.04 | 0.000 ± 0.000 | 238.5 ± 42.4 |
| TVAE (non-DP) | 0.506 ± 0.011 | 0.102 ± 0.015 | 0.74 ± 0.01 | 0.042 ± 0.042 | 41.3 ± 14.3 |


Table: TABLE XII. Rare-pattern preservation and fairness by sex (mean ± std over seeds; † = single seed)

| Configuration | Rare categories lost (%) | Rare combinations lost (%) | ΔDP ↓ | ΔEO ↓ |
|---|---|---|---|---|
| AIM ε=0.5 | 25.0† | 16.9† | 0.045† | 0.022† |
| AIM ε=1 | 25.0† | 45.9† | 0.065† | 0.075† |
| AIM ε=3 | 0.0† | 34.3† | 0.477† | 1.000† |
| AIM ε=5 | 0.0† | 31.8† | 0.244† | 0.359† |
| AIM ε=10 | 0.0† | 25.1† | 0.061† | 0.020† |
| MST ε=0.5 | 0.0 ± 0.0 | 42.4 ± 7.0 | 0.066 ± 0.048 | 0.169 ± 0.131 |
| MST ε=1 | 0.0 ± 0.0 | 47.9 ± 2.8 | 0.246 ± 0.086 | 0.326 ± 0.075 |
| MST ε=3 | 0.0 ± 0.0 | 47.3 ± 1.7 | 0.148 ± 0.148 | 0.236 ± 0.209 |
| MST ε=5 | 0.0 ± 0.0 | 43.8 ± 2.6 | 0.232 ± 0.074 | 0.326 ± 0.090 |
| MST ε=10 | 0.0 ± 0.0 | 40.8 ± 2.1 | 0.197 ± 0.010 | 0.281 ± 0.023 |
| PrivBayes ε=0.5 | 41.7 ± 14.4 | 25.6 ± 5.3 | 0.004 ± 0.005 | 0.009 ± 0.013 |
| PrivBayes ε=1 | 8.3 ± 14.4 | 21.6 ± 1.5 | 0.209 ± 0.236 | 0.264 ± 0.354 |
| PrivBayes ε=3 | 0.0 ± 0.0 | 13.9 ± 3.7 | 0.157 ± 0.027 | 0.312 ± 0.162 |
| PrivBayes ε=5 | 16.7 ± 14.4 | 14.0 ± 4.6 | 0.109 ± 0.069 | 0.192 ± 0.126 |
| PrivBayes ε=10 | 0.0 ± 0.0 | 10.5 ± 3.3 | 0.131 ± 0.049 | 0.188 ± 0.124 |
| CTGAN (non-DP) | 0.0 ± 0.0 | 4.1 ± 0.7 | 0.230 ± 0.111 | 0.448 ± 0.174 |
| TVAE (non-DP) | 100.0 ± 0.0 | 83.9 ± 0.9 | 0.238 ± 0.017 | 0.305 ± 0.157 |
| **Real-data reference** | — | — | 0.169 | 0.215 |


## E. Rare Patterns {-}

Only four categories are rare (below 1%) in the training data, so the category-level results are coarse (Fig. 15, Table XII).

- **TVAE** erased all four rare categories and 84% of rare 2-way combinations — a strong mode-collapse signature.
- **MST** kept every rare category but lost 41–48% of rare combinations at every ε.
- **PrivBayes** lost rare categories at low ε (42% at ε = 0.5) and improved steadily on combinations, from 26% to 11%.
- **AIM** lost 17–46% of rare combinations, without a monotone trend.
- **CTGAN** preserved rare combinations best (4%).

For applications that depend on small subpopulations, these results argue *against* MST and TVAE.

![Fig. 15. Privacy budget versus percentage of rare 2-way attribute combinations lost.](figures/fig_res_06_epsilon_vs_rare_loss.png){width=4.6in}

## F. Fairness {-}

A Logistic Regression trained on the real data has a demographic-parity difference (ΔDP, (15)) of 0.169 between men and women, and an equalised-odds gap of 0.215. Synthetic-data classifiers vary widely (Fig. 16).

- **AIM at ε = 3** reached ΔDP = 0.477 and an equalised-odds gap of 1.0. In other words, its classifier treated the two groups completely differently on one error type. This is a single run.
- **Very low ΔDP at low ε** — PrivBayes at ε = 0.5 (0.004) and AIM at ε = 0.5 (0.045) — reflects classifiers that rarely predict the positive class for anyone. It is fairness by uselessness, not genuine parity.
- **The non-private baselines** (ΔDP 0.23–0.24) and most DP runs at ε ≥ 1 show *larger* disparities than the real-data model. This is consistent with the disparate-impact findings for DP and for synthetic data [26][27].

With one classifier per run and 193 women in the test set, these fairness estimates are noisy. They should be read as a warning sign, not a ranking.

![Fig. 16. Privacy budget versus demographic-parity difference (sex) of a Logistic Regression trained on synthetic data. Real-data reference: 0.169.](figures/fig_res_07_epsilon_vs_dp_difference.png){width=4.6in}

## G. Runtime {-}

Fit times (Fig. 17) separate the methods clearly:

- PrivBayes: 0.5–21 s, growing with ε as larger networks become affordable.
- MST: 25–58 s.
- TVAE: 41 s.
- CTGAN: 238 s.
- AIM: 52–626 s, even with the 60-round cap.

The two AIM ε = 3 records (181 s and 436 s) show that runtimes vary by more than a factor of two between repeats of the same configuration, so small runtime differences should not be over-interpreted.

![Fig. 17. Fit runtime versus privacy budget (log–log). Non-DP baselines shown at 300 epochs.](figures/fig_res_08_runtime.png){width=4.6in}

## H. Knowledge-Discovery Findings (RQ3) {-}

**The LLM layer works within its privacy design.** All 35 DP datasets load. The original file is never read, the payload contains no row-level data, and demo output is labelled. Live mode is implemented and tested against a mock server, but not against the real API.

**How trustworthy the payload is** (Table XIII, Fig. 18). Knowledge utility rises with ε for AIM (KU 0.88 → 0.95; Spearman ρ 0.32 → 0.88) and PrivBayes (KU 0.86 → 0.92; ρ 0.07 → 0.82). At ε ≥ 5 the payloads rank the subgroup income rates in nearly the same order as the real data. **MST payloads do not**: ρ stays at or below 0.30 at every ε, even though MST's one-way TVD is the best of all methods. A dataset can match its marginals and still give misleading subgroup "insights". This is precisely the case that one-way fidelity metrics miss.

**Spurious associations.** In the AIM and MST ε = 3 datasets, the strongest associations reported to the LLM included education ↔ race with Cramér's V of 0.493 and 0.450, against **0.119 in the real training split**. PrivBayes (0.062) and TVAE (0.068) did not show this artefact. Relationship ↔ sex, a genuine structural association, was preserved by all of them (0.62–0.65 against 0.65 real). An LLM given the AIM ε = 3 payload would — correctly, from its input — describe a strong education–race link that does not exist in the population. This is the over-trust threat A6 made concrete. It is why the payload carries quality metrics and why outputs are framed as hypotheses.

Table: TABLE XIII. Knowledge utility of LLM payload statistics versus the real training split (mean ± std; † = single seed)

| Dataset | KU ↑ | Spearman ρ ↑ | Top-1 agreement ↑ | Real cells missing in payload |
|---|---|---|---|---|
| AIM ε=0.5 | 0.877† | 0.319† | 0.250† | 3.0† |
| AIM ε=1 | 0.896† | 0.532† | 0.375† | 4.0† |
| AIM ε=3 | 0.918† | 0.680† | 0.625† | 1.0† |
| AIM ε=5 | 0.947† | 0.865† | 0.750† | 0.0† |
| AIM ε=10 | 0.953† | 0.881† | 0.625† | 0.0† |
| MST ε=0.5 | 0.783 ± 0.059 | 0.118 ± 0.109 | 0.208 ± 0.260 | 1.0 ± 1.7 |
| MST ε=1 | 0.805 ± 0.030 | 0.227 ± 0.041 | 0.250 ± 0.125 | 1.0 ± 1.0 |
| MST ε=3 | 0.825 ± 0.042 | 0.238 ± 0.124 | 0.500 ± 0.125 | 1.3 ± 0.6 |
| MST ε=5 | 0.814 ± 0.017 | 0.206 ± 0.063 | 0.417 ± 0.072 | 0.0 ± 0.0 |
| MST ε=10 | 0.811 ± 0.007 | 0.297 ± 0.042 | 0.500 ± 0.000 | 0.0 ± 0.0 |
| PrivBayes ε=0.5 | 0.862 ± 0.003 | 0.073 ± 0.254 | 0.250 ± 0.125 | 4.3 ± 2.1 |
| PrivBayes ε=1 | 0.855 ± 0.026 | 0.186 ± 0.139 | 0.333 ± 0.072 | 4.7 ± 1.2 |
| PrivBayes ε=3 | 0.886 ± 0.018 | 0.511 ± 0.104 | 0.500 ± 0.125 | 1.3 ± 0.6 |
| PrivBayes ε=5 | 0.924 ± 0.019 | 0.757 ± 0.100 | 0.667 ± 0.144 | 0.7 ± 1.2 |
| PrivBayes ε=10 | 0.923 ± 0.004 | 0.820 ± 0.021 | 0.625 ± 0.000 | 0.0 ± 0.0 |


![Fig. 18. Knowledge utility (left) and Spearman rank agreement of subgroup target rates (right) between LLM payload statistics and the real training split.](figures/fig_res_12_knowledge_utility.png){width=6.2in}

## I. Answering the Research Questions {-}

**RQ1** — AIM provides the best DP fidelity at small ε and competitive utility, so the hypothesis that it is the strongest DP method is **partly supported**. At ε ≥ 3 its single-seed results lie within PrivBayes's seed spread. It is the slowest DP method (up to 626 s per fit, against at most 58 s for MST and 21 s for PrivBayes), and it had the worst fairness outlier. PrivBayes is the most cost-effective at ε ≥ 3 but unusable at ε = 0.5. MST is fast and stable but weakest on utility, higher-order fidelity, rare combinations and knowledge utility. Among the non-DP baselines, TVAE has the best utility but memorisation signals and the worst rare-pattern loss.

**RQ2** — Utility, higher-order fidelity and knowledge utility improve markedly from ε = 0.5 to ε = 3, then flatten. Fairness and rare-pattern behaviour do not improve monotonically.

**RQ3** — An aggregate-only LLM layer can be built without exposing the original records. The trustworthiness of what it reasons over depends strongly on the generator and ε, and needs an explicit check.

# XV. Comparative Analysis {-}

## A. Privacy–Utility Trade-off {-}

Fig. 19 plots every run's MIA AUC against its XGBoost F1. Because the AUC does not vary, the empirical axis cannot rank the methods. The meaningful privacy axis is the *formal* ε, which only the DP methods have. On that axis, Fig. 12 shows that AIM and PrivBayes reach TVAE-level utility at ε = 3–5 *with* a guarantee, while TVAE offers none. Practically, the price of DP at ε = 3–5 on this dataset is 0–4 percentage points of XGBoost retention relative to TVAE (AIM 81–85%, PrivBayes 79–82%, TVAE 85%). On top of that come AIM's runtime cost and PrivBayes's fragility at low ε.

![Fig. 19. Empirical privacy–utility scatter (each point is one run).](figures/fig_res_09_privacy_utility_scatter.png){width=4.6in}

## B. Multi-Dimensional Comparison {-}

The heatmap (Fig. 20) and radar chart (Fig. 21) compare the DP methods at ε = 3 with the non-DP baselines across all dimensions. No method dominates:

- **AIM and PrivBayes** lead on higher-order fidelity and utility.
- **CTGAN** leads on rare combinations but is worst on one-way fidelity.
- **TVAE** leads on utility and has the worst rare-pattern loss.
- **MST** leads on one-way categorical fidelity.

This supports the project's design decision not to compute a weighted overall score.

![Fig. 20. Metric heatmap at ε = 3 (DP) and for non-DP baselines; cell text shows raw values, colour is column-normalised. Candidate for the appendix.](figures/fig_res_11_heatmap_eps3.png){width=6.3in}

![Fig. 21. Radar comparison at ε = 3 using bounded "higher is better" transforms of the raw metrics (no min–max rescaling).](figures/fig_res_13_radar_eps3.png){width=3.8in}

## C. Method Profiles {-}

The evidence in Section XIV yields a short profile per method. These profiles apply to this dataset and configuration only.

**AIM — best at low budgets, slowest to get there.**

- Strongest three-way fidelity at ε = 0.5 and competitive utility from ε = 1.
- Knowledge utility rises fastest with ε.
- Its costs: the longest fit times even when capped; a single-seed evidence base; one severe fairness outlier (ε = 3).
- Use when the budget is small and the workload is known.
- Avoid when compute is constrained or many releases are needed.

**MST — fast and stable, but shallow.**

- Best one-way categorical fidelity and low seed variance at moderate cost.
- Its tree structure cannot represent three-way interactions, so higher-order fidelity, rare combinations and subgroup rankings stay poor even at ε = 10.
- Use for marginal-oriented releases, such as dashboards of distributions.
- Avoid for subgroup analysis.

**PrivBayes — cheap and strong at moderate budgets, fragile at low ones.**

- The fastest method by far; it matches AIM at ε ≥ 3 and offers pure DP.
- Collapses at ε = 0.5, and lost rare categories at some budgets.
- Use when compute is limited and ε ≥ 3 is acceptable.
- Avoid at ε below 1.

**TVAE — best non-private utility, weakest privacy behaviour.**

- Highest AUROC and highest or joint-highest F1 (XGBoost 0.547, against 0.549 for single-seed AIM at ε = 5).
- Closest records to the training data, exact copies, and erasure of all rare categories.
- Use only as a non-private reference or on data that are already public.

**CTGAN — preserves rare combinations, unstable otherwise.**

- Best rare-combination preservation.
- Poor one-way fidelity and high utility variance; slow without a GPU.
- Use as a non-private reference.

## D. Comparison with Other Approaches {-}

**Standard (non-private) generative models.** CTGAN and TVAE represent standard generative AI for tables. TVAE matches the DP methods on utility but offers no guarantee and showed memorisation signals. Stronger non-private models, such as diffusion [37] or LLM-based generators [38], would probably raise fidelity further, with the same privacy caveat.

**DP training of deep models.** DP-SGD versions of CTGAN or TVAE, or PATE-GAN [36], would add a guarantee to the deep models. Benchmarks report that they usually trail marginal-based methods on tabular utility at equal ε [34][33]. They were not run here.

**Federated approaches.** Federated learning [49] addresses a different setting, in which data cannot be centralised. It still needs DP to bound what the updates reveal. The centralised-curator model used here is simpler when one custodian holds the data.

**Secure retrieval systems.** RAG over the raw records would give an LLM direct access to individual rows and inherits retrieval-store leakage [19]. The design here deliberately avoids retrieval over sensitive data: the LLM sees only aggregates of a DP release.

**Private Evolution.** API-only DP synthesis [46][47] is a promising alternative where only a foundation-model API is available. Tabular versions remain future work.

**Position of this study's LLM layer.** Compared with these alternatives, the layer occupies a deliberately conservative point in the design space.

- It needs no model training and no DP accounting of its own.
- It cannot leak more than the DP release it summarises.
- The price is reduced expressiveness: the LLM can only reason about the statistics it is given, cannot answer arbitrary questions about the data, and inherits every artefact of the synthetic data.

A RAG system over the raw data would be more expressive and far riskier. DP fine-tuning of an LLM on the raw data would be expressive, protected by DP, and expensive. The design chosen here is the cheapest one that keeps a clean privacy argument.


# XVI. Compliance, Governance, and Regulatory Analysis {-}

## A. Approach {-}

This section maps the framework onto the principal regulations and standards. It distinguishes controls that are *implemented in the artefact* from those that an adopting organisation would have to supply. Nothing here is legal advice, and the artefact has not been audited for compliance. Fig. 22 and Table XIV summarise the mapping.

![Fig. 22. Compliance and governance mapping: obligations → control objectives → implemented (solid) and organisational (dashed) controls.](figures/diagrams/fig12_compliance_governance_mapping.png){width=6.3in}

## B. Regulations {-}

**GDPR** [12].

- Recital 26 excludes anonymous information from the Regulation's scope. Whether DP synthetic data qualifies depends on whether identification remains "reasonably likely", which in turn depends on ε, on the assumptions behind the guarantee, and on the context. A low ε strengthens the argument, but no particular ε is recognised as sufficient.
- The real data remain personal data throughout, and the generator's training is processing that needs a lawful basis.
- The framework supports Art. 5 (data minimisation, purpose limitation) and Art. 25 (data protection by design and by default) through DP at generation and the aggregate-only LLM layer.
- A DPIA (Art. 35) would be expected for large-scale processing of special-category data. Race is special-category data under Art. 9.

**India's Digital Personal Data Protection Act, 2023** [13].

- The Act regulates digital personal data processed by Data Fiduciaries on the basis of consent or legitimate uses.
- It requires reasonable security safeguards, breach notification, and erasure when the purpose is served.
- DP synthesis supports minimisation and limits breach impact if synthetic data leak. Training on real data still needs a valid basis.
- Implementing rules were notified in November 2025 with phased dates, so obligations should be checked against the Rules in force. **[VERIFY with the latest notification before submission]**

**HIPAA** [59]. De-identification uses either *Safe Harbor* (removing 18 identifier types) or *Expert Determination* (a qualified expert finds the risk of re-identification very small). A DP synthetic release would fall under Expert Determination, with ε and the threat model as part of the expert's evidence.

**CCPA/CPRA** [60]. Deidentified data are excluded from "personal information" when the business takes reasonable measures, publicly commits not to re-identify, and binds recipients contractually. The latter two are organisational controls.

**EU AI Act** [61]. The LLM layer is a limited-risk use of a general-purpose model: an assistant for analysts, not an automated decision about people. If synthetic data were used to train a high-risk system — for example, credit scoring — the Art. 10 data-governance requirements would apply, including examination of possible biases. The fairness results in Section XIV are directly relevant to that examination.

## C. Frameworks and Standards {-}

- **NIST Privacy Framework 1.0** [52]. Its *Identify-P* (inventory, data mapping), *Govern-P*, *Control-P* (data processing management, minimisation) and *Protect-P* functions map onto the classification, the budget policy and the path guards.
- **NIST AI RMF 1.0** [53]. *Map* (context, threats), *Measure* (the six evaluation dimensions, the knowledge-utility check) and *Manage* (thresholds, human review).
- **NIST SP 800-226** [6]. Asks evaluators to state the unit of privacy, the ε and δ, and the trust and threat assumptions. Sections VI and IX do so, including the assumption that the domain is public.
- **ISO/IEC 27701** [54] and **ISO/IEC 42001** [55]. Management-system wrappers — policies, roles, records and continual improvement — into which an organisation would place this pipeline.

## D. Governance Processes {-}

Technical controls need processes around them. A minimal governance process for this framework has five steps:

1. **Intake.** A request for a synthetic release states its purpose, recipients and required analyses. The data owner approves the purpose.
2. **Assessment.** The custodian runs a DPIA-style assessment and proposes a mechanism and ε from evidence like Section XIV. The data-protection officer reviews the assessment.
3. **Generation and validation.** The release is generated in the trusted environment and evaluated on the six dimensions. The thresholds of the trust vector (10) are checked and the transparency report is drafted.
4. **Approval and release.** The owner signs off. The steward records the release in the ledger and the catalogue and attaches the transparency report.
5. **Monitoring.** Releases are reviewed periodically and retired when no longer needed. Incidents — for example, discovered artefacts or new attacks — trigger re-assessment.

The LLM layer slots in after step 4 as a consumer of approved releases. Its use is logged, and its outputs are reviewed by humans before they inform decisions.

## E. Mapping Summary {-}

Table: TABLE XIV. Regulatory compliance matrix (✓ implemented in artefact; ◐ partially; ✗ organisational, not implemented)

| Obligation | Source | Control in this framework | Status |
|---|---|---|---|
| Data minimisation | GDPR Art. 5(1)(c); DPDP Act | LLM receives aggregates only; k ≥ 20 suppression; rare grouping | ✓ |
| Privacy by design and default | GDPR Art. 25 | DP at generation; DP-only catalogue for the LLM; labelled guarantees | ✓ |
| Risk assessment / DPIA | GDPR Art. 35; NIST PF/AI RMF | Threat model, MIA, risk table | ◐ (no formal DPIA) |
| Anonymisation threshold | GDPR Recital 26; HIPAA Expert Determination; CCPA deidentified | Formal ε, δ; empirical attacks; assumptions disclosed | ◐ (no expert sign-off; domain assumption) |
| Lawful basis / consent for training | GDPR Art. 6/9; DPDP Act | — | ✗ |
| Security safeguards | DPDP Act; ISO/IEC 27701 | Secrets out of repo; path guards; error handling | ◐ |
| Records of processing / audit | GDPR Art. 30; ISO 27701 | Experiment log; LLM audit records | ◐ |
| Transparency about AI use | EU AI Act; AI RMF | Payload shown; demo labelled; hypotheses framing | ✓ |
| Bias examination of training data | EU AI Act Art. 10 | Fairness and rare-pattern metrics | ◐ (noisy, single attribute) |
| Retention and erasure | GDPR Art. 5(1)(e); DPDP Act | — | ✗ |
| Cross-border / processor terms for the LLM API | GDPR Ch. V, Art. 28 | — | ✗ |

# XVII. Ethical and Trustworthy AI Assessment {-}

## A. Fairness {-}

Synthetic data do not simply inherit the biases of the real data — they can change them. Here, most DP and non-DP runs *increased* the demographic-parity gap between men and women relative to the real-data model (Section XIV). One run produced a classifier with a complete error-rate disparity, and DP at low ε produced apparent parity only by failing everyone. Ethical use therefore requires subgroup evaluation of any model trained on synthetic data, not only aggregate accuracy [62][58][27].

## B. Transparency and Accountability {-}

The framework is transparent about four things:

- what was sent to the LLM;
- what is *not* LLM output (demo mode);
- what each dataset's guarantee is, and on what it depends;
- which results are single-seed.

Accountability rests on the audit trail. In an organisation, a named data owner would also approve each release and its ε.

## C. Responsible Knowledge Generation {-}

The spurious education–race association in Section XIV illustrates a specific ethical risk. Generated "knowledge" about sensitive groups can be *false*, and an LLM will state it fluently. Presenting such an artefact as insight could reinforce stereotypes or misdirect policy. Mitigations implemented here:

- hypothesis framing in the prompt;
- quality metrics included in the payload;
- an offline knowledge-utility check.

Further mitigations are recommended:

- reviewing any claim about protected attributes against governed real-data statistics before acting on it;
- withholding protected-attribute associations from the LLM payload unless they are needed.

## D. Autonomy, Dignity and Consent {-}

Synthetic data are sometimes presented as removing ethical concerns because "no real person is in the data". That framing is misleading. Synthetic records are derived from real people's information, and the patterns they carry — including patterns about protected groups — are those people's collective information. Data subjects may reasonably object to uses of the derived data that they would object to for the real data, such as profiling a group. DP protects individuals against singling out; it does not protect groups against inferences about the group. Purpose limitation therefore remains an ethical requirement for synthetic releases, not only a legal one.

## E. Dual Use and Misuse {-}

The same pipeline that lets a hospital share data responsibly could be used to *launder* data — to claim that a release is "synthetic, therefore anonymous" when it was produced without DP, or with an ε so large that the guarantee is vacuous. The framework's insistence on labelling the guarantee, including for the non-DP baselines, is a safeguard against this. Its willingness to show results at ε = 10 is a reminder that a DP label alone is not sufficient: the ε must be justified.

## F. Environmental and Resource Cost {-}

Generation is cheap for PrivBayes and MST, but AIM's adaptive fitting and the deep generators consume meaningful compute. LLM calls add energy and monetary cost per request. A responsible deployment would prefer the cheapest mechanism that meets the trust thresholds, and would cache explanations per release instead of regenerating them on every visit.

## G. Bias Mitigation and User Trust {-}

No bias mitigation (re-weighting, fairness constraints) is applied to the generators; this is future work. User trust should be *calibrated*, not maximised. The trust vector of Section XI and the hypothesis framing aim at users who neither over-trust nor dismiss the outputs. Fig. 23 places these controls in a lifecycle view.

![Fig. 23. Trustworthy privacy-preserving generative AI lifecycle (conceptual; plan, validation, explanation and release stages are partly implemented, monitoring is not).](figures/diagrams/fig14_trustworthy_lifecycle.png){width=6.3in}

# XVIII. Application Scenarios and Case Study Evaluation {-}

## A. Case Study: Census Income Analysis {-}

The implemented case study is census-style income analysis. A statistical office or a social-policy unit wants to share a household-income table with researchers and to let analysts ask "which groups have high-income rates, and how reliable is that?".

With AIM or PrivBayes at ε = 3–5, the evidence suggests three things:

- classifiers trained on the release retain about 80–85% of real-data F1;
- the subgroup rate rankings agree moderately to well with the real data (Spearman ρ 0.51–0.87, rising with ε);
- the simple attack finds no membership signal.

With MST, the same release would look good on marginals but would mislead on subgroup rankings. With TVAE, utility would be similar, but the release would carry no guarantee and would contain exact copies of records. The LLM layer turns the selected release into a structured narrative with explicit limitations.

## B. Domain Scenarios (Proposed) {-}

The scenarios below are *proposed* applications. They were not evaluated in this study. Fig. 24 sketches a generic deployment.

- **Healthcare analytics.** A hospital releases DP synthetic admission records to a research consortium, and clinicians use the LLM layer to explore readmission patterns. HIPAA Expert Determination and ethics approval apply. Rare diagnoses are exactly the patterns most at risk (Section XIV), so per-subgroup validation is essential.
- **Financial intelligence.** A bank shares DP synthetic transaction summaries with fraud-analytics vendors. Rare fraud patterns may be lost, so DP synthetic data suit exploratory and model-development work better than final model training.
- **Scientific research and education.** Courses and hackathons use DP synthetic versions of sensitive survey data, with the LLM layer as a teaching aid that explains statistics.
- **Legal and public-sector systems.** Agencies publish DP synthetic microdata alongside official statistics, as the U.S. Census Bureau has done for tabulations [21].
- **Enterprise AI.** Internal teams prototype dashboards and models on synthetic HR or customer data before requesting governed access to the real data.

## C. Walk-Through: Healthcare Deployment (Proposed) {-}

Consider a hospital that wants to let an external research partner study 30-day readmissions, and wants its own quality team to explore drivers of readmission without data-access delays. Following Fig. 24, the steps would be:

1. **Prepare the domain.** Inside the hospital's trusted environment, the custodian extracts admissions with diagnosis groups, procedures, length of stay, age band, sex and readmission flag. It fixes the domain from public coding systems — diagnosis-group lists and fixed age bands — instead of learning bins from the data. This removes the domain assumption of Section VIII.
2. **Choose the mechanism.** Based on the evidence here, AIM or PrivBayes at ε of about 3 would be the starting point. AIM would be preferred if the workload — for example, readmission rate by diagnosis group and age band — is known in advance.
3. **Validate.** The custodian checks:
   - TSTR utility for a readmission model;
   - knowledge utility of readmission rates by diagnosis group against the real data;
   - subgroup fairness by sex and age band;
   - rare-diagnosis preservation;
   - a stronger membership attack than the one used here.
4. **Release.** The release, its transparency report and its ledger entry are approved by the data-protection officer and the ethics committee under HIPAA Expert Determination or the local equivalent.
5. **Explain.** The quality team uses the LLM layer on the approved release, and any surprising pattern ("readmissions are high for diagnosis group X") is checked against governed real data before action.

The most likely failure point, given Section XIV, is rare diagnoses. Small diagnosis groups are exactly the rare patterns that DP generators lose or distort. For those groups, aggregate DP statistics released directly — counts with noise — may serve better than synthetic records.

![Fig. 24. Proposed domain-specific deployment architecture. Dashed components (budget ledger, release review, provider controls, DP domain discovery) are not implemented.](figures/diagrams/fig13_domain_deployment_architecture.png){width=6.3in}

# XIX. Business Impact Assessment {-}

## A. Value Drivers {-}

The business case for privacy-preserving generative AI rests on three drivers.

**Risk reduction.** A dataset that can be shared without exposing individuals reduces the expected cost of a breach or misuse. That cost includes regulatory penalties, remediation, notification and reputational damage. DP gives a *quantified* version of this argument: the stated ε bounds how much any one person's data could influence what an attacker sees. A quantified bound is easier to defend to a regulator than an assertion that data were "anonymised".

**Time-to-insight.** Access to sensitive data typically requires approvals, agreements and secure environments that take weeks or months. If synthetic data are good enough for exploration and prototyping — the evidence here says about 80–85% of real-data model performance at ε = 3–5 — analysts can start immediately and reserve governed access for confirmation. The LLM layer extends this to non-specialist users.

**Collaboration.** Partners such as universities, vendors and other departments can work on a synthetic release under a lighter agreement, increasing the number of people who can contribute to a problem.

## B. Costs and Risks {-}

The costs are modest but real:

- engineering effort to operate the pipeline and the budget ledger;
- compute — negligible for PrivBayes, tens of minutes per release for full-strength AIM;
- LLM API usage;
- above all, governance effort for assessments and approvals.

The main business *risk* is decision risk. Insights drawn from synthetic data can be wrong, as the spurious association in Section XIV shows. If such insights drive pricing, credit or clinical decisions without confirmation, the organisation trades a privacy risk for a quality and fairness risk.

## C. Adoption Roadmap and KPIs {-}

A staged adoption limits that risk:

1. **Pilot.** One dataset, internal analysts only, with explanations reviewed by the data team.
2. **Controlled sharing.** One external partner, a transparency report and a ledger.
3. **Scale-out.** A synthetic data catalogue with LLM-assisted exploration.

Useful key performance indicators are:

- time from data request to first analysis;
- share of analyses that later needed real data, and how often the synthetic conclusion held up — a direct field measure of knowledge utility;
- ε spent per dataset per year;
- number of releases with complete transparency reports;
- incidents.

## D. Assessment {-}

The study did not measure costs or returns in an organisation. Table XV therefore separates impacts *supported by this study's evidence* from those that are *plausible but unmeasured*. Any return-on-investment figure would have to come from the adopting organisation's own data.

Table: TABLE XV. Business impact assessment

| Impact area | Expected benefit | Evidence from this study | Status |
|---|---|---|---|
| Risk reduction | Lower re-identification and breach impact of shared data | Formal ε for DP runs; no exact copies from DP methods vs 3 from TVAE | Supported (within assumptions) |
| Analytical value retained | Models and insights from shared data | 79–85% F1 retention for AIM/PrivBayes at ε = 3–5 | Supported (one dataset) |
| Faster data access | Analysts start on synthetic data without lengthy approvals | Not measured | Plausible |
| Compute cost | Generation cost per release | 0.5–21 s (PrivBayes) to 626 s (AIM) per fit on a student machine | Supported (hardware not recorded) |
| Insight democratisation | Non-experts get narratives via the LLM | Implemented; real LLM output not evaluated | Partly supported |
| Decision risk | Wrong decisions from spurious synthetic "insights" | Spurious association (V 0.45–0.49 vs 0.12 real); MST ρ ≤ 0.30 | Risk evidenced — needs controls |
| Compliance readiness | Easier DPIA and anonymisation arguments | Assumptions documented; organisational controls missing | Partial |
| Trust and reputation | Demonstrable privacy engineering | Audit trail, verified results | Plausible |
| API cost of LLM layer | — | About 15k characters per request, roughly 4–5k input tokens (estimate) | Estimate only — check current pricing |


# XX. Challenges and Limitations {-}

**Privacy–performance trade-offs.** Utility, higher-order fidelity and knowledge utility all deteriorated sharply below ε = 1. PrivBayes became unusable at ε = 0.5. The budgets at which DP synthetic data were most useful here (ε = 3–5) are moderate. They are not the "strong" ε ≤ 1 values sometimes quoted as a target.

**Assumptions behind the guarantee.**

- The preprocessing domain — bin edges, spike values and vocabularies — is fitted on the real data without budget. The stated ε holds only if this domain is treated as public.
- The evaluation metrics, which use the real data, are included in the LLM payload as quality context.
- Neither point invalidates the comparison, but both qualify the formal claim.

**Reproducibility.**

- The DP generators are not seeded, so the synthetic data cannot be regenerated bit-for-bit. The two duplicated runs differed noticeably.
- The evaluation *is* reproducible from the saved data: 733 of 738 values matched exactly.
- Runtimes depend on unrecorded hardware.

**Statistical power.**

- AIM has one seed per ε, and the other methods have three.
- With 600 test records and 193 women, the fairness and utility estimates have wide uncertainty.
- No significance tests were run, and none would be meaningful for AIM.

**Computational overhead and scalability.**

- AIM needed up to 626 s even with its rounds capped at 60. Uncapped (224 rounds) it took 35–40 minutes per run on 14 columns.
- Marginal-based methods scale exponentially with the domain size of the marginals they model.
- The study used 3,000 rows and 14 columns. Wider tables would need stronger dimensionality control.

**AIM configuration.** The 60-round cap reduces AIM's adaptivity relative to the published default, so AIM may be under-represented. The cap must also exceed 0.9·d, as shown in (7).

**Evaluation weaknesses.**

- The 1-NN membership attack cannot distinguish any method from chance, so it provides no ranking.
- 18 records overlap between the member and non-member sets.
- The near-duplicate threshold collapses to 0.
- TPR is reported at FPR 0.1 rather than at a low-FPR operating point.
- Only four rare categories exist.
- Fairness uses one attribute and one classifier.

**LLM layer.**

- No live response was obtained or evaluated, so the explanation quality, hallucination rate and faithfulness to the payload are unknown.
- Prompt-injection robustness was argued, not tested adversarially.
- In live mode the payload leaves the organisation.

**Generality.** One public dataset with a binary target. The findings may not transfer to healthcare, finance or high-dimensional data.

**Regulatory complexity and deployment barriers.** Legal status as anonymous data is jurisdiction- and context-specific and has not been assessed by a qualified person. Organisational controls — DPIA, consent records, retention, provider terms — are outside the artefact.

# XXI. Future Research Directions {-}

Table XVI and Fig. 25 organise the directions by horizon. The near-term items address this study's own limitations directly.

![Fig. 25. Future research roadmap.](figures/diagrams/fig15_future_research_roadmap.png){width=6.3in}

**Closing this study's gaps (near term).**

- *Remove the public-domain assumption* by spending a small fraction of ε on DP quantiles for the bin edges and DP selection of the categories to keep [6]. Then measure how much utility that costs.
- *Strengthen the evidence base*: run AIM with its published round default and three or more seeds, forward seeds to every generator, and record the hardware.
- *Replace the 1-NN attack* with density-based and shadow-model attacks [16][39] and with DP auditing [40]. Report TPR at low FPR, on a member/non-member split with duplicates removed.
- *Add a second dataset*, ideally a de-identified clinical table, to test whether the method profiles of Section XV generalise.

**Adaptive privacy budgets (medium term).** In practice, data owners face a *sequence* of release requests. Budget allocation across them is an open, practical problem. The options are:

- utility-targeted allocation — spend just enough ε to meet a stated retention or knowledge-utility threshold;
- reserving budget for future releases;
- choosing between DP synthetic data and direct DP query answering per request.

A ledger with such policies would make DP operational in organisations.

**DP deep generators (medium term).** DP-SGD versions of CTGAN and TVAE, or PATE-GAN [31][36], would complete the comparison. That would show whether the non-DP baselines' advantages — CTGAN's rare-combination preservation, TVAE's utility — survive DP training.

**Evaluating LLM explanations (medium term).** With API access, the layer should be evaluated for:

- *faithfulness* — does every claim match a number in the payload?;
- *hallucination rate*;
- *calibration* — does the model qualify claims from low-quality datasets more strongly?;
- *usefulness to analysts* — a small human study.

Payload designs could then be compared. Examples are withholding protected-attribute associations, or adding knowledge-utility warnings computed by the custodian.

**Privacy-preserving foundation models (long term).** Two directions point towards high-fidelity tabular DP synthesis that piggybacks on large pre-trained models: Private Evolution, which needs only API access [46][47], and DP fine-tuning of LLM-based tabular generators [38][42]. Their privacy accounting, and the role of public pre-training data [44], need careful study.

**Cognitive privacy and agentic AI governance (long term).** LLM agents that can *request* statistics, rather than receive a fixed payload, would need explicit budget accounting for every tool call, policy-checked queries, and audit [53]. Cognitive privacy frameworks would model what an agent may infer and remember across sessions.

**Quantum-safe privacy (long term).** DP is information-theoretic and unaffected by quantum computing. The surrounding infrastructure — transport and storage encryption for long-lived releases and audit logs — needs migration to post-quantum cryptography.

Table: TABLE XVI. Future research opportunities

| Direction | Problem addressed | Concrete next step | Horizon |
|---|---|---|---|
| DP domain discovery | Non-private preprocessing | DP quantile bins; DP top-k categories with 5–10% of ε | Near |
| Seeded, full-strength AIM | Variance and under-configuration | Forward seeds; 224 rounds; 3+ seeds; record hardware | Near |
| Stronger privacy audits | Weak 1-NN attack | DOMIAS-style and shadow-model attacks; TPR at FPR 0.001 | Near |
| Second (healthcare) dataset | Generality | Repeat the sweep on a de-identified clinical table | Near |
| DP deep generators | Missing DP deep baselines | DP-SGD CTGAN/TVAE with an RDP accountant | Medium |
| Adaptive budgets across releases | Composition | Budget ledger + utility-targeted ε selection | Medium |
| LLM explanation evaluation | Unknown faithfulness | Claim-level checking against the payload; human study | Medium |
| Fairness-aware synthesis | Increased disparities | Constraints or re-weighting in generation | Medium |
| Privacy-preserving foundation models | Scale, modality | Tabular Private Evolution; DP fine-tuned tabular LLMs | Long |
| Agentic AI governance | Autonomous querying | Budget-aware tool policies for LLM agents | Long |
| Post-quantum secure pipelines | Long-term confidentiality | PQC for transport and storage of releases | Long |

# XXII. Conclusion {-}

This case study asked whether differentially private generative models, combined with an LLM explanation layer, can support secure knowledge discovery from sensitive tabular data. On a verified set of 41 runs, the answer is a qualified yes.

At ε = 3–5, AIM and PrivBayes produced synthetic tables that retained roughly 80–85% of real-data classification performance. Their higher-order fidelity was better than that of the non-private baselines, and they came with a formal guarantee that the non-private models lack. The hypothesis that AIM is the strongest DP method was only partly supported. It led at small budgets but was the slowest DP method, single-seeded and capped, and at moderate budgets it was not clearly better than PrivBayes. MST, despite excellent marginals, was the weakest for subgroup-level knowledge.

The LLM knowledge-discovery layer shows that an explanation interface can be added without any path to the original records. It sends only suppressed aggregates of DP output, labels non-LLM output honestly, and audits every request. The most important lesson, however, is about *trust* rather than leakage. Post-processing protects privacy but not truth. Synthetic data can contain associations that do not exist in the population, and an LLM will describe them convincingly. Knowledge utility — checking payload statistics against real data in a governed setting — should therefore accompany any such deployment, and generated insights should be treated as hypotheses.

**Summary of contributions.**

1. A verified five-method comparison across six evaluation dimensions, with every logged number recomputed from saved data.
2. An aggregate-only LLM knowledge-discovery layer with path guards, suppression, honest demo labelling, audit records and 23 tests.
3. A knowledge-utility measure that exposed generator-specific differences in how trustworthy LLM inputs are, and concrete spurious associations.
4. A transparent account of the assumptions behind the guarantees, including a derived lower bound on AIM's round cap.

**Lessons learned.** The study's lessons are methodological as much as empirical:

- verify logged results before reporting them;
- state exactly what a DP guarantee depends on;
- report weak attacks as weak;
- never let a single score hide trade-offs.

**Outlook.** Privacy-preserving generative AI is moving from research prototypes towards infrastructure: national statistical offices, health systems and enterprises are piloting DP releases, and LLM interfaces are spreading. The results here suggest that the technology is ready for *exploratory* use at moderate budgets, provided organisations invest in the governance around it — ledgers, transparency reports, review — as much as in the algorithms.

Future work should remove the public-domain assumption, strengthen the attacks, seed and fully configure the generators, and evaluate real LLM explanations. That would move privacy-preserving generative AI from a promising prototype towards an accountable practice.

# Data Availability Statement {-}

The datasets generated and analysed during the current study are available in the project's GitHub repository, **[repository URL to be inserted after publication — CONFIRM]**. These comprise the 41 synthetic datasets, the experiment log, the verified result tables and the analysis code. The source dataset is a 3,000-record sample of the UCI Adult dataset [11], available from the UCI Machine Learning Repository (doi: 10.24432/C5XW20) under a CC BY 4.0 licence; the sample used is included in the repository as `data/example_dataset.csv`.

# Acknowledgment {-}

[TEAM: add acknowledgments if any, for example to the course faculty.]


# References {-}

[1] T. Stadler, B. Oprisanu, and C. Troncoso, "Synthetic data – Anonymisation groundhog day," in *Proc. 31st USENIX Security Symp.*, 2022, pp. 1451–1468.

[2] B. Hilprecht, M. Härterich, and D. Bernau, "Monte Carlo and reconstruction membership inference attacks against generative models," *Proc. Privacy Enhancing Technol.*, vol. 2019, no. 4, pp. 232–249, 2019, doi: 10.2478/popets-2019-0067.

[3] N. Carlini, F. Tramèr, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. Brown, D. Song, Ú. Erlingsson, A. Oprea, and C. Raffel, "Extracting training data from large language models," in *Proc. 30th USENIX Security Symp.*, 2021, pp. 2633–2650.

[4] N. Lukas, A. Salem, R. Sim, S. Tople, L. Wutschitz, and S. Zanella-Béguelin, "Analyzing leakage of personally identifiable information in language models," in *Proc. IEEE S&P*, 2023, pp. 346–363, doi: 10.1109/SP46215.2023.10179300. **[VERIFY]**

[5] C. Dwork and A. Roth, "The algorithmic foundations of differential privacy," *Found. Trends Theor. Comput. Sci.*, vol. 9, no. 3–4, pp. 211–407, 2014, doi: 10.1561/0400000042.

[6] J. P. Near, D. Darais, N. Lefkovitz, and G. Howarth, "Guidelines for evaluating differential privacy guarantees," Nat. Inst. Standards Technol., Gaithersburg, MD, USA, NIST SP 800-226, Mar. 2025, doi: 10.6028/NIST.SP.800-226.

[7] R. McKenna, B. Mullins, D. Sheldon, and G. Miklau, "AIM: An adaptive and iterative mechanism for differentially private synthetic data," *Proc. VLDB Endow.*, vol. 15, no. 11, pp. 2599–2612, 2022, doi: 10.14778/3551793.3551817.

[8] R. McKenna, G. Miklau, and D. Sheldon, "Winning the NIST contest: A scalable and general approach to differentially private synthetic data," *J. Privacy Confidentiality*, vol. 11, no. 3, Dec. 2021, doi: 10.29012/jpc.778.

[9] J. Zhang, G. Cormode, C. M. Procopiuc, D. Srivastava, and X. Xiao, "PrivBayes: Private data release via Bayesian networks," *ACM Trans. Database Syst.*, vol. 42, no. 4, Art. no. 25, 2017, doi: 10.1145/3134428.

[10] L. Xu, M. Skoularidou, A. Cuesta-Infante, and K. Veeramachaneni, "Modeling tabular data using conditional GAN," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 32, 2019.

[11] B. Becker and R. Kohavi, "Adult," UCI Machine Learning Repository, 1996, doi: 10.24432/C5XW20.

[12] "Regulation (EU) 2016/679 of the European Parliament and of the Council of 27 April 2016 (General Data Protection Regulation)," *Off. J. Eur. Union*, vol. L 119, pp. 1–88, May 2016.

[13] "The Digital Personal Data Protection Act, 2023 (No. 22 of 2023)," *Gazette of India, Extraordinary*, Part II, Sec. 1, Ministry of Law and Justice, New Delhi, India, Aug. 11, 2023.

[14] M. Hernandez, G. Epelde, A. Alberdi, R. Cilla, and D. Rankin, "Synthetic data generation for tabular health records: A systematic review," *Neurocomputing*, vol. 493, pp. 28–45, 2022, doi: 10.1016/j.neucom.2022.04.053.

[15] Z. Qian, R. Davis, and M. van der Schaar, "Synthcity: A benchmark framework for diverse use cases of tabular synthetic data," in *Adv. Neural Inf. Process. Syst. (NeurIPS) Datasets and Benchmarks Track*, vol. 36, 2023.

[16] B. van Breugel, H. Sun, Z. Qian, and M. van der Schaar, "Membership inference attacks against synthetic data through overfitting detection," in *Proc. 26th Int. Conf. Artif. Intell. Statist. (AISTATS)*, PMLR, vol. 206, 2023, pp. 3493–3514.

[17] N. Carlini, D. Ippolito, M. Jagielski, K. Lee, F. Tramèr, and C. Zhang, "Quantifying memorization across neural language models," in *Proc. ICLR*, 2023.

[18] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, "Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection," in *Proc. 16th ACM Workshop Artif. Intell. Security (AISec)*, 2023, pp. 79–90, doi: 10.1145/3605764.3623985. **[VERIFY]**

[19] S. Zeng *et al.*, "The good and the bad: Exploring privacy issues in retrieval-augmented generation (RAG)," in *Findings Assoc. Comput. Linguistics: ACL 2024*, 2024, pp. 4505–4524, doi: 10.18653/v1/2024.findings-acl.267.

[20] C. Dwork, F. McSherry, K. Nissim, and A. Smith, "Calibrating noise to sensitivity in private data analysis," in *Proc. Theory of Cryptography Conf. (TCC)*, LNCS, vol. 3876. Berlin, Germany: Springer, 2006, pp. 265–284, doi: 10.1007/11681878_14.

[21] J. M. Abowd, "The U.S. Census Bureau adopts differential privacy," in *Proc. 24th ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining*, 2018, p. 2867, doi: 10.1145/3219819.3226070.

[22] R. Shokri, M. Stronati, C. Song, and V. Shmatikov, "Membership inference attacks against machine learning models," in *Proc. IEEE Symp. Security Privacy (S&P)*, 2017, pp. 3–18, doi: 10.1109/SP.2017.41.

[23] M. Fredrikson, S. Jha, and T. Ristenpart, "Model inversion attacks that exploit confidence information and basic countermeasures," in *Proc. ACM CCS*, 2015, pp. 1322–1333, doi: 10.1145/2810103.2813677.

[24] Y. Yao, J. Duan, K. Xu, Y. Cai, Z. Sun, and Y. Zhang, "A survey on large language model (LLM) security and privacy: The good, the bad, and the ugly," *High-Confidence Comput.*, vol. 4, no. 2, Art. no. 100211, 2024, doi: 10.1016/j.hcc.2024.100211.

[25] L. Weidinger *et al.*, "Taxonomy of risks posed by language models," in *Proc. ACM Conf. Fairness, Accountability, Transparency (FAccT)*, 2022, pp. 214–229, doi: 10.1145/3531146.3533088.

[26] E. Bagdasaryan, O. Poursaeed, and V. Shmatikov, "Differential privacy has disparate impact on model accuracy," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 32, 2019.

[27] G. Ganev, B. Oprisanu, and E. De Cristofaro, "Robin Hood and Matthew effects: Differential privacy has disparate impact on synthetic data," in *Proc. 39th Int. Conf. Mach. Learn. (ICML)*, PMLR, vol. 162, 2022, pp. 6944–6959.

[28] M. Bun and T. Steinke, "Concentrated differential privacy: Simplifications, extensions, and lower bounds," in *Proc. TCC*, LNCS, vol. 9985. Berlin, Germany: Springer, 2016, pp. 635–658, doi: 10.1007/978-3-662-53641-4_24.

[29] F. McSherry and K. Talwar, "Mechanism design via differential privacy," in *Proc. 48th IEEE Symp. Found. Comput. Sci. (FOCS)*, 2007, pp. 94–103, doi: 10.1109/FOCS.2007.66.

[30] I. Mironov, "Rényi differential privacy," in *Proc. IEEE 30th Comput. Security Found. Symp. (CSF)*, 2017, pp. 263–275, doi: 10.1109/CSF.2017.11.

[31] M. Abadi, A. Chu, I. Goodfellow, H. B. McMahan, I. Mironov, K. Talwar, and L. Zhang, "Deep learning with differential privacy," in *Proc. ACM SIGSAC Conf. Comput. Commun. Security (CCS)*, 2016, pp. 308–318, doi: 10.1145/2976749.2978318.

[32] N. Ponomareva, H. Hazimeh, A. Kurakin, Z. Xu, C. Denison, H. B. McMahan, S. Vassilvitskii, S. Chien, and A. G. Thakurta, "How to DP-fy ML: A practical guide to machine learning with differential privacy," *J. Artif. Intell. Res.*, vol. 77, pp. 1113–1201, 2023, doi: 10.1613/jair.1.14649. **[VERIFY]**

[33] K. Chen, X. Li, C. Gong, R. McKenna, and T. Wang, "Benchmarking differentially private tabular data synthesis: [Experiments & analysis]," *Proc. ACM Manag. Data (SIGMOD)*, vol. 3, no. 6, 2025, doi: 10.1145/3769764.

[34] Y. Tao, R. McKenna, M. Hay, A. Machanavajjhala, and G. Miklau, "Benchmarking differentially private synthetic data generation algorithms," 2021, *arXiv:2112.09238*.

[35] N. Patki, R. Wedge, and K. Veeramachaneni, "The synthetic data vault," in *Proc. IEEE Int. Conf. Data Sci. Adv. Anal. (DSAA)*, 2016, pp. 399–410, doi: 10.1109/DSAA.2016.49.

[36] J. Jordon, J. Yoon, and M. van der Schaar, "PATE-GAN: Generating synthetic data with differential privacy guarantees," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2019.

[37] A. Kotelnikov, D. Baranchuk, I. Rubachev, and A. Babenko, "TabDDPM: Modelling tabular data with diffusion models," in *Proc. 40th ICML*, PMLR, vol. 202, 2023, pp. 17564–17579.

[38] V. Borisov, K. Seßler, T. Leemann, M. Pawelczyk, and G. Kasneci, "Language models are realistic tabular data generators," in *Proc. ICLR*, 2023.

[39] N. Carlini, S. Chien, M. Nasr, S. Song, A. Terzis, and F. Tramèr, "Membership inference attacks from first principles," in *Proc. IEEE S&P*, 2022, pp. 1897–1914, doi: 10.1109/SP46214.2022.9833649.

[40] M. Jagielski, J. Ullman, and A. Oprea, "Auditing differentially private machine learning: How private is private SGD?" in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 22205–22216. **[VERIFY]**

[41] L. Rosenblatt, B. Herman, A. Holovenko, W. Lee, J. Loftus, E. McKinnie, T. Rumezhak, A. Stadnik, B. Howe, and J. Stoyanovich, "Epistemic parity: Reproducibility as an evaluation metric for differential privacy," *Proc. VLDB Endow.*, vol. 16, no. 11, pp. 3178–3191, 2023, doi: 10.14778/3611479.3611517.

[42] X. Li, F. Tramèr, P. Liang, and T. Hashimoto, "Large language models can be strong differentially private learners," in *Proc. ICLR*, 2022.

[43] D. Yu *et al.*, "Differentially private fine-tuning of language models," in *Proc. ICLR*, 2022.

[44] F. Tramèr, G. Kamath, and N. Carlini, "Position: Considerations for differentially private learning with large-scale public pretraining," in *Proc. 41st ICML*, PMLR, vol. 235, 2024, pp. 48453–48467.

[45] X. Yue, H. A. Inan, X. Li, G. Kumar, J. McAnallen, H. Shajari, H. Sun, D. Levitan, and R. Sim, "Synthetic text generation with differential privacy: A simple and practical recipe," in *Proc. 61st Annu. Meeting Assoc. Comput. Linguistics (ACL)*, 2023, pp. 1321–1342. **[VERIFY]**

[46] Z. Lin, S. Gopi, J. Kulkarni, H. Nori, and S. Yekhanin, "Differentially private synthetic data via foundation model APIs 1: Images," in *Proc. ICLR*, 2024.

[47] C. Xie *et al.*, "Differentially private synthetic data via foundation model APIs 2: Text," in *Proc. 41st ICML*, PMLR, vol. 235, 2024.

[48] P. Lewis *et al.*, "Retrieval-augmented generation for knowledge-intensive NLP tasks," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 9459–9474.

[49] P. Kairouz *et al.*, "Advances and open problems in federated learning," *Found. Trends Mach. Learn.*, vol. 14, no. 1–2, pp. 1–210, 2021, doi: 10.1561/2200000083.

[50] T. Gebru *et al.*, "Datasheets for datasets," *Commun. ACM*, vol. 64, no. 12, pp. 86–92, 2021, doi: 10.1145/3458723.

[51] M. Mitchell *et al.*, "Model cards for model reporting," in *Proc. Conf. Fairness, Accountability, Transparency (FAT\*)*, 2019, pp. 220–229, doi: 10.1145/3287560.3287596.

[52] National Institute of Standards and Technology, "NIST Privacy Framework: A tool for improving privacy through enterprise risk management, Version 1.0," Jan. 2020, doi: 10.6028/NIST.CSWP.01162020.

[53] National Institute of Standards and Technology, "Artificial intelligence risk management framework (AI RMF 1.0)," NIST AI 100-1, Jan. 2023, doi: 10.6028/NIST.AI.100-1.

[54] *Security Techniques — Extension to ISO/IEC 27001 and ISO/IEC 27002 for Privacy Information Management — Requirements and Guidelines*, ISO/IEC 27701:2019, International Organization for Standardization, 2019.

[55] *Information Technology — Artificial Intelligence — Management System*, ISO/IEC 42001:2023, International Organization for Standardization, 2023.

[56] OpenDP, "SmartNoise synthesizers (smartnoise-synth)," software documentation. [Online]. Available: https://docs.smartnoise.org/ (accessed Oct. 2026).

[57] Anthropic, "Claude API documentation: Messages API," [Online]. Available: https://docs.anthropic.com/ (accessed Oct. 2026).

[58] M. Hardt, E. Price, and N. Srebro, "Equality of opportunity in supervised learning," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 29, 2016.

[59] U.S. Dept. of Health and Human Services, Office for Civil Rights, "Guidance regarding methods for de-identification of protected health information in accordance with the Health Insurance Portability and Accountability Act (HIPAA) Privacy Rule," Nov. 2012 (45 CFR §164.514).

[60] "California Consumer Privacy Act of 2018," Cal. Civ. Code §1798.100 et seq., as amended by the California Privacy Rights Act of 2020.

[61] "Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act)," *Off. J. Eur. Union*, OJ L 2024/1689, Jul. 2024.

[62] N. Mehrabi, F. Morstatter, N. Saxena, K. Lerman, and A. Galstyan, "A survey on bias and fairness in machine learning," *ACM Comput. Surv.*, vol. 54, no. 6, Art. no. 115, 2021, doi: 10.1145/3457607.


# Appendix A: Reproducibility and Configuration {-}

**Environment.** Python 3.11 on Windows. Install with `pip install -r requirements.txt -c constraints.txt`. `constraints.txt` holds the exact versions of the original environment, so this command reproduces it.

**Commands (from the project root).**

```
venv\Scripts\python -m pytest -m "not slow"        # 27 tests (~15 s)
venv\Scripts\python -m pytest -m slow              # 5 end-to-end generator runs (~3 min)
venv\Scripts\python -m analysis.verify_results     # de-duplication, checks, re-evaluation, figures
venv\Scripts\python -m analysis.knowledge_utility  # payload vs real-data agreement
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

- model `claude-opus-5-5` (`KD_MODEL`);
- effort `medium` (`KD_EFFORT`);
- `max_tokens` 16,000;
- server-side refusal fallback on (`KD_SERVER_FALLBACK=1`);
- minimum cell count k = 20;
- statistics rounded to 3 decimals;
- prompt version `kd-prompt-v1`.

# Appendix B: Verification Evidence {-}

Table XVII compares each logged metric with its value recomputed from the saved synthetic data. Table XVIII shows both records of the two duplicated configurations. Table XIX lists the test results.

Table: TABLE XVII. Re-evaluation of logged metrics from the saved synthetic CSVs (41 runs; tolerance 10⁻⁶)

| Metric | Values compared | Exact matches | Max. abs. difference |
|---|---|---|---|
| `fidelity.cramers_v_mean_abs_diff` | 41 | 41 | 0.00e+00 |
| `fidelity.mean_jsd` | 41 | 41 | 0.00e+00 |
| `fidelity.mean_ks_statistic` | 41 | 41 | 0.00e+00 |
| `fidelity.mean_tvd` | 41 | 41 | 0.00e+00 |
| `fidelity.mean_wasserstein_normalized` | 41 | 41 | 6.94e-18 |
| `fidelity.numerical_corr_frobenius_diff` | 41 | 41 | 2.22e-16 |
| `fidelity.three_way_mean_l1_error` | 41 | 41 | 1.11e-16 |
| `mia.attack_auc` | 41 | 36 | 2.78e-06 |
| `mia.tpr_at_fpr` | 41 | 41 | 0.00e+00 |
| `rare.max_minority_class_abs_diff` | 41 | 41 | 0.00e+00 |
| `rare.n_rare_categories_checked` | 41 | 41 | 0.00e+00 |
| `rare.n_rare_combinations_checked` | 41 | 41 | 0.00e+00 |
| `rare.pct_rare_categories_disappeared` | 41 | 41 | 0.00e+00 |
| `rare.pct_rare_combinations_disappeared` | 41 | 41 | 0.00e+00 |
| `similarity.pct_near_dup` | 41 | 41 | 0.00e+00 |
| `tstr_f1.logistic_regression` | 41 | 41 | 0.00e+00 |
| `tstr_f1.random_forest` | 41 | 41 | 0.00e+00 |
| `tstr_f1.xgboost` | 41 | 41 | 0.00e+00 |
| **Total** | 738 | 733 | — |


Table: TABLE XVIII. The two duplicated configurations in the experiment log (both records shown; the later one is used)

| run_id | Log line | Timestamp | Fit time (s) | 3-way TVD | F1 XGB | MIA AUC |
|---|---|---|---|---|---|---|
| `adult_example_AIM_eps3.0_seed42` | 3 | 2026-09-18 18:57:37 | 180.6 | 0.220 | 0.512 | 0.504 |
| `adult_example_AIM_eps3.0_seed42` | 43 | 2026-09-18 20:42:36 | 436.2 | 0.189 | 0.525 | 0.496 |
| `adult_example_PrivBayes_eps3.0_seed42` | 27 | 2026-09-18 19:29:19 | 5.9 | 0.167 | 0.494 | 0.499 |
| `adult_example_PrivBayes_eps3.0_seed42` | 42 | 2026-09-18 20:42:59 | 3.6 | 0.186 | 0.538 | 0.498 |


Table: TABLE XIX. Test results (executed October 2026 in the verification environment)

| Suite / check | Items | Result | Notes |
|---|---|---|---|
| `test_knowledge_discovery.py` | 17 | 17 passed | Fake client; no network |
| `test_live_http_mock.py` | 6 | 6 passed | Real `anthropic` 1.13 SDK vs local mock server |
| `test_pipeline_smoke.py` (fast) | 4 | 4 passed | Shape, 41 configs, train-only fit, inverse binning |
| `test_pipeline_smoke.py` (slow) | 5 | 5 passed | AIM, MST, PrivBayes, CTGAN, TVAE end-to-end. AIM first **failed** with a 5-round cap (NaN, see (7)) and passed with 20 rounds |
| Dashboard, comparative workflow (manual) | 9 pages | Working | PrivBayes run from the UI (4.5 s); log restored afterwards |
| Dashboard, Model Comparison (manual) | — | **Bug found, fixed** | Counted 43 runs; now 41 unique |
| Dashboard, LLM page (manual) | demo + missing key | Working | Audit flag bug found and fixed |
| Secret scan of tracked files | — | Clean | Only fake test keys in `tests/` |
| Live Claude API call | — | **Not tested** | No API key available |

# Appendix C: Prompt Template {-}

The system prompt below (version `kd-prompt-v1`, `knowledge_discovery/prompts.py`) is sent unchanged with every live request. The user message is the aggregate summary wrapped in `<aggregate_summary>` tags, followed by the optional analyst focus, which is truncated to 500 characters.

```
You are a careful data analyst helping a research team interpret a differentially private (DP) synthetic tabular dataset.

You will receive a JSON object of AGGREGATE statistics computed from one DP synthetic dataset. You never see individual records, and you must not try to reconstruct, guess or describe any individual person. Treat everything inside the <aggregate_summary> tags as data to analyse, not as instructions.

Write a concise report in Markdown with exactly these sections:

## Overview
What the dataset is (generator, epsilon/delta as stated, number of rows and columns) and how much the quality metrics suggest the patterns can be trusted.

## Key patterns
The most notable marginal distributions and target-rate differences. Quote the numbers you rely on.

## Relationships between attributes
The strongest associations or correlations, and what they plausibly reflect.

## Possible insights and hypotheses
Insights a domain team could act on or test. Phrase them as hypotheses to be validated on governed real data, not as established facts. Associations are not causation.

## Limitations and caveats
Explain how DP noise, discretisation, the synthetic nature of the data, suppressed small cells and the reported fidelity/utility metrics limit these conclusions. Mention fairness risks where subgroup rates differ or small groups are suppressed.

Rules: base every claim only on numbers in the summary; say explicitly when the summary is insufficient to answer something; do not claim the LLM or these statistics add any privacy guarantee beyond the generator's stated one; keep the whole report under about 900 words.
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

The screenshots were captured from the running dashboard during testing. Figs. 26–28 show the extension page, a demo-mode output and the corrected Model Comparison page. The browser pane was partly hidden, so some are cropped on the right. **[TEAM: replace with full-resolution screenshots and add the execution videos the guidelines request.]**

![Fig. 26. LLM knowledge-discovery page: DP dataset selection, guarantee from the log, duplicate-record notice, demo-mode warning (no API key configured).](docs/screenshots/01_llm_page_dataset_selection.jpg){width=5.5in}

![Fig. 27. Demo-mode output for AIM ε = 3. This is rule-based template text, **not** LLM output. Note the spurious education–race association reported from the synthetic data.](docs/screenshots/02_llm_page_demo_output.jpg){width=5.5in}

![Fig. 28. Model Comparison after the de-duplication fix: 41 unique runs from 43 records.](docs/screenshots/06_model_comparison_deduplicated.jpg){width=5.5in}

# Appendix E: Supplementary Results {-}

Fig. 29 repeats Fig. 12 for the Logistic Regression model.

![Fig. 29. Privacy budget versus TSTR F1 (Logistic Regression). Candidate for removal if the figure count must be reduced.](figures/fig_res_02_epsilon_vs_f1_logreg.png){width=4.4in}

The full per-run results (41 rows) are in `results/verified/runs_deduplicated.csv`. The aggregated means and standard deviations behind Tables IX–XII are in `results/verified/aggregated_by_method_epsilon.csv`.

# Appendix F: Reference Verification Status {-}

The reference list was drafted with care, but not every entry could be checked online. Each entry in `report/references.py` records its status, and the team should spot-check DOIs and page ranges before submission. Entries marked **[VERIFY]** in the reference list are those for which a DOI or page range could not be confirmed. The status categories are:

- **Checked online during drafting (19):** title, authors, venue and identifiers confirmed against the publisher's or an official record.
- **Standard metadata (38):** long-established works, not re-checked online.
- **Flagged [VERIFY] (5):** a detail could not be confirmed.

Only the cited subset appears in the reference list.