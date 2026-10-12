# Challenges and Limitations

**Privacy–performance trade-offs.** Utility, higher-order fidelity and knowledge utility all deteriorated sharply below ε = 1. PrivBayes became unusable at ε = 0.5. The budgets at which DP synthetic data were most useful here (ε = 3–5) are moderate. They are not the "strong" ε ≤ 1 values sometimes quoted as a target.

**Assumptions behind the guarantee.**

- The preprocessing domain — bin edges, spike values and vocabularies — is fitted on the real data without budget. The stated ε holds only if this domain is treated as public.
- The evaluation metrics, which use the real data, are included in the LLM payload as quality context by default. They are not covered by the DP guarantee; a dashboard switch withholds them.
- The unit of privacy is a row. With 52 duplicate rows in the sample, a person who appears twice is protected at 2ε, not ε.
- Neither point invalidates the comparison, but all three qualify the formal claim.

**Reproducibility.**

- The DP generators are not seeded, so the synthetic data cannot be regenerated bit-for-bit. The two duplicated runs differed noticeably.
- The evaluation *is* reproducible from the saved data: 733 of 738 values matched exactly.
- Runtimes depend on unrecorded hardware.

**Statistical power.**

- AIM has one seed per ε, and the other methods have three.
- With 600 test records and 193 women, the fairness and utility estimates have wide uncertainty.
- No significance tests were run, and none would be meaningful for AIM.
- Even a perfectly random membership attack would score an AUC between about 0.47 and 0.53 with 600 + 600 candidates, so the observed AUCs (0.478–0.525) cannot separate any two methods.

**Computational overhead and scalability.**

- AIM needed up to 626 s even with its rounds capped at 60. Uncapped (224 rounds) it took 35–40 minutes per run on 14 columns.
- Marginal-based methods scale exponentially with the domain size of the marginals they model.
- The study used 3,000 rows and 14 columns. Wider tables would need stronger dimensionality control.

**AIM configuration.** The 60-round cap reduces AIM's adaptivity relative to the published default, so AIM may be under-represented. The cap must also exceed 0.9·d, as shown in {eq:aimbudget}.

**Evaluation weaknesses.**

- The 1-NN membership attack cannot distinguish any method from chance, so it provides no ranking.
- 18 records overlap between the member and non-member sets.
- The near-duplicate threshold collapses to 0.
- TPR is reported at FPR 0.1 rather than at a low-FPR operating point.
- Only four rare categories exist.
- Fairness uses one attribute and one classifier.

**LLM layer.**

- Five live responses from one provider (Gemini) exist: two fact-checked claim by claim (9/10 claims faithful), and three used only to check repetition. They give a case study of faithfulness and error propagation, not a hallucination rate. No live Claude response was obtained.
- LLM output varies between calls; the same AIM payload produced the suppression misreading in two of three responses. A single response cannot be treated as *the* explanation of a release.
- The served model behind the alias `gemini-flash-latest` can change without notice, so explanations are not reproducible over time unless the model version is pinned.
- Prompt-injection robustness was argued, not tested adversarially.
- In live mode the payload leaves the organisation. On Google's free tier, prompts and responses may be used to improve Google's products, so a deployment would need a paid tier or an enterprise agreement.

**Generality.** One public dataset with a binary target. The findings may not transfer to healthcare, finance or high-dimensional data.

**Regulatory complexity and deployment barriers.** Legal status as anonymous data is jurisdiction- and context-specific and has not been assessed by a qualified person. Organisational controls — DPIA, consent records, retention, provider terms — are outside the artefact.

# Future Research Directions

Table {tab:future} and Fig. {fig:roadmap} organise the directions by horizon. The near-term items address this study's own limitations directly.

![{fig:roadmap} Future research roadmap.](figures/diagrams/fig15_future_research_roadmap.png){width=6.3in}

**Closing this study's gaps (near term).**

- *Remove the public-domain assumption* by spending a small fraction of ε on DP quantiles for the bin edges and DP selection of the categories to keep [@near2025]. Then measure how much utility that costs.
- *Strengthen the evidence base*: run AIM with its published round default and three or more seeds, forward seeds to every generator, and record the hardware.
- *Replace the 1-NN attack* with density-based and shadow-model attacks [@vanbreugel2023domias; @carlini2022lira] and with DP auditing [@jagielski2020]. Report TPR at low FPR, on a member/non-member split with duplicates removed.
- *Add a second dataset*, ideally a de-identified clinical table, to test whether the method profiles of Section XV generalise.
- *De-duplicate before splitting*, so that the member and non-member sets are disjoint and the unit of privacy matches a person rather than a row.

**Making the LLM layer DP-clean (near term).** The payload's quality context is the one real-data-derived input to the LLM. Three options would remove that exception: send no quality context by default; release the seven metrics through a DP mechanism with a small, accounted budget; or replace them with a custodian-side warning label ("this dataset's subgroup rankings disagree with the real data") that is itself treated as a release. Each option should be compared on explanation quality using the fact-checking method of Section XIV.

**Payload ablation and automatic warnings (near term).** The case study suggests concrete experiments: remove protected-attribute associations from the payload and test whether explanations become less harmful without becoming useless; add the dataset's knowledge-utility score and test whether the model then qualifies its claims; and flag, inside the payload, statistics such as the 43.3% rate for `12th` grade that are implausible relative to their neighbours.

**Adaptive privacy budgets (medium term).** In practice, data owners face a *sequence* of release requests. Budget allocation across them is an open, practical problem. The options are:

- utility-targeted allocation — spend just enough ε to meet a stated retention or knowledge-utility threshold;
- reserving budget for future releases;
- choosing between DP synthetic data and direct DP query answering per request.

A ledger with such policies would make DP operational in organisations.

**DP deep generators (medium term).** DP-SGD or PATE versions of CTGAN and TVAE [@abadi2016; @chen2025bench] would complete the comparison. That would show whether the non-DP baselines' advantages — CTGAN's rare-combination preservation, TVAE's utility — survive DP training.

**Evaluating LLM explanations (medium term).** The two-response case study in Section XIV is a starting point. The layer should be evaluated systematically — all 35 DP datasets, repeated calls, both providers — for:

- *faithfulness* — does every claim match a number in the payload?;
- *hallucination rate*;
- *calibration* — does the model qualify claims from low-quality datasets more strongly?;
- *usefulness to analysts* — a small human study.

Payload designs could then be compared. Examples are withholding protected-attribute associations, or adding knowledge-utility warnings computed by the custodian.

**Privacy-preserving foundation models (long term).** Two directions point towards high-fidelity tabular DP synthesis that piggybacks on large pre-trained models: Private Evolution, which needs only API access [@lin2024pe], and DP fine-tuning of LLM-based tabular generators [@li2022llmdp]. Their privacy accounting, and the role of public pre-training data, need careful study.

**Cognitive privacy and agentic AI governance (long term).** LLM agents that can *request* statistics, rather than receive a fixed payload, would need explicit budget accounting for every tool call, policy-checked queries, and audit [@nist2023airmf]. Cognitive privacy frameworks would model what an agent may infer and remember across sessions.

**Quantum-safe privacy (long term).** DP is information-theoretic and unaffected by quantum computing. The surrounding infrastructure — transport and storage encryption for long-lived releases and audit logs — needs migration to post-quantum cryptography.

Table: {tab:future} Future research opportunities

| Direction | Problem addressed | Concrete next step | Horizon |
|---|---|---|---|
| DP domain discovery | Non-private preprocessing | DP quantile bins; DP top-k categories with 5–10% of ε | Near |
| Seeded, full-strength AIM | Variance and under-configuration | Forward seeds; 224 rounds; 3+ seeds; record hardware | Near |
| Stronger privacy audits | Weak 1-NN attack | DOMIAS-style and shadow-model attacks; TPR at FPR 0.001 | Near |
| Second (healthcare) dataset | Generality | Repeat the sweep on a de-identified clinical table | Near |
| DP deep generators | Missing DP deep baselines | DP-SGD CTGAN/TVAE with an RDP accountant | Medium |
| Adaptive budgets across releases | Composition | Budget ledger + utility-targeted ε selection | Medium |
| LLM explanation evaluation | Faithfulness checked on two responses only | Claim-level checking against the payload; human study | Medium |
| Fairness-aware synthesis | Increased disparities | Constraints or re-weighting in generation | Medium |
| Privacy-preserving foundation models | Scale, modality | Tabular Private Evolution; DP fine-tuned tabular LLMs | Long |
| Agentic AI governance | Autonomous querying | Budget-aware tool policies for LLM agents | Long |
| Post-quantum secure pipelines | Long-term confidentiality | PQC for transport and storage of releases | Long |

# Conclusion

This case study asked whether differentially private generative models, combined with an LLM explanation layer, can support secure knowledge discovery from sensitive tabular data. On a verified set of 41 runs, the answer is a qualified yes.

At ε = 3–5, AIM and PrivBayes produced synthetic tables that retained roughly 79–85% of real-data classification performance. Their higher-order fidelity was better than that of the non-private baselines, and they came with a formal guarantee that the non-private models lack. The hypothesis that AIM is the strongest DP method was only partly supported. It led at small budgets but was the slowest DP method, single-seeded and capped, and at moderate budgets it was not clearly better than PrivBayes. MST, despite excellent marginals, was the weakest for subgroup-level knowledge.

The LLM knowledge-discovery layer shows that an explanation interface can be added without any path to the original records. It sends only suppressed aggregates of DP output — plus seven disclosed, switchable real-data quality metrics — labels non-LLM output honestly, and audits every request. With a real model, the same layer produced a correct explanation of a PrivBayes release and a confidently wrong one of an AIM release, which reversed the real gender gap in income; the difference lay entirely in the synthetic data. The most important lesson, however, is about *trust* rather than leakage. Post-processing protects privacy but not truth. Synthetic data can contain associations that do not exist in the population, and an LLM will describe them convincingly. Knowledge utility — checking payload statistics against real data in a governed setting — should therefore accompany any such deployment, and generated insights should be treated as hypotheses.

**Summary of contributions.**

1. A verified five-method comparison across six evaluation dimensions, with every logged number recomputed from saved data.
2. An aggregate-only LLM knowledge-discovery layer with path guards, suppression, honest demo labelling, two interchangeable providers (Gemini and Claude), audit records, 40 tests and a fact-checked live case study.
3. A knowledge-utility measure that exposed generator-specific differences in how trustworthy LLM inputs are, and concrete spurious associations.
4. A transparent account of the assumptions behind the guarantees, including a derived lower bound on AIM's round cap.

**Lessons learned.** The study's lessons are methodological as much as empirical. Its two most consequential findings — the duplicate-counting defect and the reversed gender gap — were found by checking, not by modelling:

- verify logged results before reporting them;
- state exactly what a DP guarantee depends on;
- report weak attacks as weak;
- never let a single score hide trade-offs.

**Outlook.** Privacy-preserving generative AI is moving from research prototypes towards infrastructure: national statistical offices, health systems and enterprises are piloting DP releases, and LLM interfaces are spreading. The results here suggest that the technology is ready for *exploratory* use at moderate budgets, provided organisations invest in the governance around it — ledgers, transparency reports, review — as much as in the algorithms.

Future work should remove the public-domain assumption, strengthen the attacks, seed and fully configure the generators, and evaluate real LLM explanations systematically. That would move privacy-preserving generative AI from a promising prototype towards an accountable practice.
