# Introduction

## Motivation

Most of the data that organisations would like to mine for knowledge are about people. Hospitals hold diagnoses and outcomes, banks hold transactions and credit histories, and statistical agencies hold census responses. Analysing these records improves services, but disclosing them — even in apparently anonymised form — can expose the individuals behind them. Removing names does not stop re-identification when quasi-identifiers such as age, occupation and location are retained [@stadler2022]. Modern privacy law therefore treats data as personal unless identification is no longer reasonably likely [@gdpr2016; @dpdp2023].

Generative artificial intelligence (AI) appears to offer a way around this tension, in two ways. First, a generative model trained on the sensitive table can emit *synthetic* records that preserve its statistical structure and can be shared more widely [@hernandez2022; @murtaza2023]. Second, a large language model (LLM) can read a dataset or its statistics and explain patterns in natural language, lowering the skill needed to obtain insight. Both routes, however, create their own leakage channels:

- Generators can memorise training rows, and membership-inference attacks against them are well documented [@hilprecht2019; @vanbreugel2023domias].
- LLMs reproduce fragments of their training data [@carlini2021extract], leak personally identifiable information [@lukas2023], and can be steered by injected instructions [@greshake2023].
- Retrieval-augmented systems add a further store that can be extracted [@zeng2024rag].

Differential privacy (DP) [@dwork2006; @dwork2014] provides the mathematical tool to bound these risks. A DP mechanism guarantees that its output distribution changes by at most a factor $e^{\varepsilon}$ (plus a small $\delta$) when any one person's record is added or removed. The guarantee survives any later processing of the output — including analysis by an LLM — and it composes across releases. DP is used in production by the U.S. Census Bureau [@abowd2018], and NIST now publishes guidance on evaluating DP claims [@near2025].

## Context of This Case Study

This report documents the BCSE318L case study *Differential Privacy-Enhanced Generative AI for Secure Knowledge Discovery*. The technical artefact started as a comparative study of synthetic tabular data generators, delivered as a Streamlit dashboard. The study covers three DP generators — AIM [@mckenna2022aim], MST [@mckenna2021mst] and PrivBayes [@zhang2017privbayes] — and two non-private deep generative baselines, CTGAN and TVAE [@xu2019ctgan]. In this iteration the artefact was extended with an LLM knowledge-discovery layer and with verification tooling. The report is careful to separate four categories:

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

## Objectives

The study pursues six objectives:

- **O1.** Compare DP and non-DP synthetic tabular data generators fairly under one preprocessing and evaluation protocol.
- **O2.** Quantify the privacy–utility–fidelity trade-off across privacy budgets ε ∈ {0.5, 1, 3, 5, 10}.
- **O3.** Assess empirical privacy risk, fairness, rare-pattern preservation and runtime alongside utility.
- **O4.** Design and implement a knowledge-discovery layer in which an LLM explains patterns in DP synthetic data without ever receiving the original records.
- **O5.** Verify every reported number against saved outputs and make the work reproducible.
- **O6.** Analyse the governance, compliance, ethical and business implications of deploying such a pipeline.

## Contributions

The contributions are deliberately modest; this is an empirical comparison, not a new algorithm.

1. A controlled, verified comparison of five generators across 41 runs on six evaluation dimensions. All 738 logged metric values were recomputed from the saved synthetic data (Section XIV).
2. A modular, privacy-scoped LLM extension. It accepts only DP synthetic data, refuses the original dataset, sends suppressed aggregates only, labels demo output as non-LLM, and audits every request (Section X).
3. A *knowledge-utility* check (Eq. {eq:ku}). It measures how faithfully the LLM's input statistics reflect the real data, and it revealed generator-induced spurious associations (Section XIV).
4. An explicit account of where the formal guarantee depends on assumptions: a non-private preprocessing domain, an unseeded generator, and the AIM round cap (Sections IX and XX).

## Scope

The scope is centralised, single-release synthetic data generation for one binary-classification table. Out of scope: federated or on-device training; continual releases; text or image data; training or fine-tuning an LLM; and certifying legal compliance. The bundled dataset is public census data used as a stand-in for sensitive data. Conclusions about its sensitivity are illustrative.

## Organisation of the Report

Sections II–III state the problem and review the literature. Sections IV–VI analyse requirements, the data lifecycle and threats. Sections VII–XI present the framework layer by layer. Sections XII–XV report the experimental setup, metrics, results and comparisons. Sections XVI–XIX cover compliance, ethics, applications and business impact. Sections XX–XXII close with limitations, future work and conclusions.

# Problem Statement

## The Core Problem

Let $D$ be a sensitive table of $n$ records over $d$ attributes. An organisation wants to (i) release a synthetic table $\tilde{D}$ that supports downstream analysis and machine learning, and (ii) obtain natural-language explanations of the knowledge in it. Both must hold while limiting what an adversary can learn about any individual in $D$. Four challenges make this difficult.

**Privacy leakage and memorisation.** Expressive generators fit their training data closely. Without a formal mechanism, nothing stops them from reproducing individual rows or near-copies [@stadler2022]. Membership-inference attacks exploit exactly this [@shokri2017; @hilprecht2019; @vanbreugel2023domias].

**Model inversion and attribute inference.** Even without copying rows, a released model or dataset can let an adversary infer a sensitive attribute of a known individual from the remaining attributes [@fredrikson2015].

**Uncontrolled knowledge extraction.** An LLM sitting on top of the data is a new interface. If it is given raw records, it can repeat them. If it is given rich statistics about small groups, it can describe those groups in identifying detail. And any data in the prompt leave the organisation's control [@yao2024survey; @weidinger2022].

**The privacy–utility tension.** DP bounds leakage by adding calibrated noise, which degrades fidelity and utility. It degrades rare subgroups disproportionately [@bagdasaryan2019; @ganev2022]. Choosing a mechanism and a budget is therefore an empirical question that depends on the data.

**The problem as instantiated here.** In this study, $D$ is the 2,400-row training split of a census sample whose records are easy to single out: 30.6% of the full sample is unique on age, sex, race, native country and occupation (Section V). The organisation wants to share synthetic versions with analysts and let them ask an LLM what the data show. The question is not whether this is possible in principle, but at which budget, with which generator, and with what residual risk and error.

## Research Questions

- **RQ1.** Among AIM, MST, PrivBayes, CTGAN and TVAE, which gives the best balance of privacy, fidelity, utility and cost on privacy-sensitive tabular data? Is the prior hypothesis that AIM is the strongest DP method supported?
- **RQ2.** How do fidelity, utility, fairness and rare-pattern preservation change as ε varies from 0.5 to 10?
- **RQ3.** Can an LLM knowledge-discovery layer be added without exposing the original records, and how trustworthy are the statistics it reasons over?

## Why It Matters

If DP synthetic data can be shown to retain most of their analytical value at a defensible budget, organisations gain a governed way to share data internally and with partners. An LLM layer could then widen access to insight. If the value is not retained — or if the "insights" reflect noise rather than reality — then naive deployments risk both privacy harm and wrong decisions. Fig. {fig:risk} summarises the risk landscape this study responds to.

![{fig:risk} Generative AI privacy risk landscape: leakage channels around a generative system. Redrawn for this report; adapted from the threat categories in [@yao2024survey; @weidinger2022].](figures/diagrams/fig01_genai_privacy_risk_landscape.png){width=6.2in}
