<!--ABSTRACT-->
Generative models can turn sensitive tabular records into shareable synthetic data, and large language models (LLMs) can turn data into readable insight, but both can leak information about individuals. This study evaluates a pipeline that combines the two under differential privacy. Three differentially private generators (AIM, MST and PrivBayes) and two non-private baselines (CTGAN and TVAE) were compared on a 3,000-record sample of the UCI Adult census data across five privacy budgets, using one shared leakage-safe preprocessing protocol and six evaluation dimensions: statistical fidelity, machine-learning utility, empirical privacy risk, fairness, rare-pattern preservation and runtime. All 41 unique runs were verified by recomputing 738 logged metric values from the saved synthetic data; 733 matched exactly and the remainder differed by less than three in a million. At budgets of three to five, AIM and PrivBayes retained 79–85% of the real-data F1 score, close to the non-private TVAE (85%), while MST retained 62–68%. A simple nearest-neighbour membership attack could not distinguish any method from random guessing, which shows the attack's weakness rather than the safety of the non-private models. An LLM knowledge-discovery layer was added that sends only suppressed aggregate statistics from private synthetic data to Gemini or Claude. An offline check showed that these statistics track the real data well for AIM and PrivBayes at higher budgets but poorly for MST. Two real Gemini responses confirmed the risk: the model faithfully reported a gender gap that AIM had reversed.
<!--/ABSTRACT-->

<!--KEYWORDS-->
Differential privacy, generative AI, knowledge discovery, large language models, membership inference, privacy–utility trade-off, synthetic data, tabular data.
<!--/KEYWORDS-->

# Draft Status and Review Notes {-}

> **For the student team — delete this section before submission.** This is a first draft generated from the verified repository (`dp-genai-secure-knowledge-discovery`). Every number in Sections XIV–XV and Appendix B is read from `results/verified/`; please do not edit numbers by hand. Instead, rerun `python -m analysis.verify_results` and rebuild with `python report/build_report.py`.
>
> Items that need a human decision or check are marked **[CONFIRM]**, **[VERIFY]** or **[TEAM]**. The main ones:
>
> 1. **Abstract length conflict.** The template asks for a 150–250-word abstract (the ABSTRACT box above, about 240 words). The section plan asks for a 450–750-word "Executive Summary and Abstract". This draft provides both: the short abstract in the template slot and the Executive Summary below. Please confirm with the instructor which one is graded. **[CONFIRM]**
> 2. **Layout.** The template's paper body is two-column. The draft body is single-column so it is easier to edit; switch with *Layout → Columns → Two* after editing. Wide figures and tables will need section breaks. **[TEAM]**
> 3. **Front matter.** Student names, faculty name, e-mails and author order are placeholders. Page numbers in the Index, List of Figures and List of Tables must be filled in after the final layout. **[TEAM]**
> 4. **Contributions.** The Contributions table lists the automatically counted words per section. Assigning sections to registration numbers is the team's decision. **[TEAM]**
> 5. **References.** 63 references are cited.
>    - 19 were checked against online records while drafting.
>    - 5 are flagged **[VERIFY]** because a DOI or page range could not be confirmed.
>    - The rest are long-established works reproduced from standard metadata and should be spot-checked.
>
>    The mix is about 21% journal articles, 56% conference papers and 24% standards, legislation, documentation or preprints. The guideline asks for 80% journal articles from IEEE/ACM/Springer/Elsevier, so the team should swap conference papers for journal versions where they exist, or confirm the requirement with the instructor. **[TEAM]**
> 6. **Similarity.** No similarity checker has been run. The 10% threshold must be confirmed with the authorised tool after the team rewrites the text in its own words. **[TEAM]**
> 7. **Figure and table counts.** 30 figures (25 in the body, 5 in appendices) and 20 tables, which is above the guideline's 10–15 and 8–12. Candidates to move to an appendix or drop are noted in captions: the heatmap, the Logistic Regression plot, and one of the radar or heatmap pair. **[TEAM]**
> 10. **Word counts.** Counted without tables, these sections are still below the section plan's suggested minimum and could be expanded: Threat Model (about 680 of 1,000), Framework (about 880 of 1,200), Data Preparation (about 640 of 1,000), Explainability (about 700 of 1,000), Business Impact (about 400 of 500), Challenges (about 425 of 600) and Future Directions (about 425 of 600). The per-section counts are in the Contributions table. **[TEAM]**
> 8. **Equations.** These are native Word equations (editable in the Equation Editor). Numbers are typed at the right of each equation; Word does not renumber them automatically.
> 9. **Live LLM output.** Two real responses from Google Gemini (`gemini-3.8-flash`, 11 Oct. 2026) are reported and fact-checked in Section XIV and Appendix D; their full text is in the repository (`evidence/llm_responses/`). No real Claude response was obtained (no Anthropic API key). Every other LLM-style text in this draft is labelled demo output. **[TEAM: rotate the Gemini key before submission.]**

# Executive Summary {-}

**Context.** Organisations hold tabular data — patient records, loan books, census and survey microdata — whose analysis creates value but whose disclosure harms individuals. Generative AI offers two tempting shortcuts. Synthetic data generators can stand in for the real records, and large language models (LLMs) can explain the data in plain language. Neither is private by default. Generators memorise and reproduce training records [@stadler2022; @hilprecht2019]. LLMs leak training data [@carlini2021extract; @lukas2023], and their prompts reach third-party services. Differential privacy (DP) is the only widely accepted framework that bounds what any output can reveal about one individual [@dwork2014; @near2025].

**What was built.** This case study evaluates a three-layer pipeline. In the first layer, a leakage-safe preparation stage learns every preprocessing parameter from the training split only. In the second, a DP synthesis layer produces synthetic tables with AIM [@mckenna2022aim], MST [@mckenna2021mst] or PrivBayes [@zhang2017privbayes]; CTGAN and TVAE [@xu2019ctgan] serve as non-private baselines. In the third, an evaluation and knowledge-discovery layer measures each synthetic table on six dimensions and passes only aggregate, small-cell-suppressed statistics from DP output to an LLM — Google Gemini or Anthropic Claude, selectable — for explanation.

The comparative study and dashboard existed before this iteration. The LLM layer, the verification tooling, the test suite and two dashboard fixes were added. Training a new LLM, DP-SGD and retrieval-augmented generation are discussed but **not** implemented.

**How it was evaluated.** The study uses 41 configurations on a 3,000-record sample of the UCI Adult dataset [@becker1996adult]: five privacy budgets (ε = 0.5–10) with three seeds each for MST and PrivBayes, one seed for AIM, and three seeds each for CTGAN and TVAE. The saved log holds 43 records because two configurations were run twice, and the latest record of each was used. Every logged metric was recomputed from the saved synthetic data: 733 of 738 values matched exactly, and the remaining five differed by less than 3 × 10⁻⁶.

**Key findings.**

- *Utility.* At ε = 3–5, AIM and PrivBayes retained 79–85% of the real-data XGBoost F1 (0.647), close to non-private TVAE (85%); at ε = 10 the single-seed AIM run fell to 77%. MST retained 62–69% at ε ≥ 3. PrivBayes collapsed at ε = 0.5 (26%).
- *Fidelity.* AIM had the lowest three-way marginal error at ε = 0.5 (0.224, against 0.30–0.32 for the other DP methods). The non-private generators had the worst one-way numerical fidelity (KS 0.25–0.33, against 0.08–0.15 for the DP methods).
- *Privacy.* A simple nearest-neighbour membership attack scored an AUC of about 0.50 for **every** method. This exposes the attack's weakness; it does not show that CTGAN or TVAE are safe. TVAE produced the closest records and was the only method that emitted exact copies of training rows.
- *Rare patterns and fairness.* TVAE erased every rare category, and MST lost 41–48% of rare attribute combinations. Fairness metrics varied widely across single runs.
- *Knowledge discovery.* Payload statistics agreed with the real data far better for AIM and PrivBayes at ε ≥ 5 (Spearman ρ 0.76–0.88) than for MST (ρ ≤ 0.30). Some DP datasets contained spurious associations: education and race appeared strongly associated (Cramér's V 0.45–0.63 in the AIM run and the three MST runs at ε = 3) where the real association was weak (0.12). Two real Gemini responses showed that an LLM does report such artefacts as insight: on AIM ε = 3 it stated, faithfully to its input, that women out-earn men (25.4% vs 23.3%), whereas the real split shows 10.3% vs 30.7%. On PrivBayes ε = 3 it reported the real gap correctly and flagged an implausible subgroup rate as a DP artefact.

**Implications.** The prior hypothesis — that AIM offers the best DP trade-off — is only partly supported. AIM leads at low budgets but is the slowest DP method and was run with one seed. The formal guarantee also rests on treating the preprocessing domain as public. For organisations, the results support DP synthetic data as a *first-pass* analytical resource, with LLM explanations treated as hypotheses. They do not support it as a drop-in replacement for governed access to real data.

**Main limitations.** Single small dataset; AIM capped at 60 rounds and single-seed; DP generator randomness not seeded; weak membership attack; preprocessing not privatised; only two live LLM responses, from one provider, evaluated.
