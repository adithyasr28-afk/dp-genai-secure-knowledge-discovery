# Results and Findings

All numbers in this section are read from `results/verified/`. They are means ± standard deviations over seeds; AIM has one seed per ε, marked †. Standard deviations over three seeds are indicative only.

## Verification of the Saved Results

**Log integrity.**

- The experiment log contains **43 records but 41 unique run identifiers**, all with status `completed`.
- `AIM_eps3.0_seed42` and `PrivBayes_eps3.0_seed42` each appear twice. The second runs started at 20:42 on 18 September 2026 and overwrote the corresponding CSVs.
- The two records of each pair differ (Table {tab:dups}). For AIM ε = 3, the 3-way TVD was 0.220 versus 0.189 and the fit time 181 s versus 436 s. This is direct evidence of run-to-run variability from the unseeded generators and of runtime sensitivity to machine load.

**De-duplication and configuration checks.**

- The analysis uses the later record of each pair. That record is the one consistent with the data on disk.
- All 41 configurations pass the checks: ε matches the run identifier; δ = 10⁻⁵ for AIM and MST and δ = 0 for PrivBayes; AIM's round cap is 60; and CTGAN and TVAE carry "no formal guarantee".
- All 41 CSVs are present and have 2,400 rows each.

**Re-evaluation.** Recomputing the metrics from the CSVs reproduced **733 of 738 logged values exactly** (Appendix B, Table {tab:verify}). The five exceptions are MIA AUC values that differ by at most 2.8 × 10⁻⁶. This is consistent with floating-point and nearest-neighbour tie effects.

**TRTR reference.** The TRTR reference, which was not stored in the log, was recomputed: F1 = 0.583 (LR), 0.620 (RF) and 0.647 (XGBoost); XGBoost AUROC = 0.886.

**What could not be reproduced.** The synthetic data themselves, which would need seeded generators, and the runtimes, which depend on the hardware.

## Utility (RQ1, RQ2)

Table {tab:utility} and Fig. {fig:f1} show the TSTR results.

- **At ε ≥ 3, AIM and PrivBayes are close to the best non-private baseline.** XGBoost F1 retention {eq:retention} was 81% (AIM, ε = 3), 85% (AIM, ε = 5), 82% (PrivBayes, ε = 3) and 79% (PrivBayes, ε = 5), against 85% for TVAE.
- **MST trails.** Its retention was 48–69% at every ε, and it barely improved beyond ε = 1. That puts it close to CTGAN's level (62%) rather than to the other DP methods.
- **PrivBayes collapses at ε = 0.5.** Logistic Regression F1 fell to 0.014 ± 0.023 (2% retention): the model trained on that data almost never predicts the positive class.
- **CTGAN is the least stable** (XGBoost F1 0.404 ± 0.163).
- **AIM is not monotonic in ε** (XGBoost F1 0.549 at ε = 5 but 0.496 at ε = 10). With a single seed, such differences are within the run-to-run variation seen in Table {tab:dups}.
- **TVAE exceeds the real-data ceiling for one model.** Its Logistic Regression F1 (0.598) exceeds the TRTR value (0.583), giving 103% retention. Retention above 100% is possible on a 600-row test set and is reported, not clipped.

{{INCLUDE:generated/table_utility.md}}

![{fig:f1} Privacy budget versus TSTR F1 (XGBoost). Error bars: ±1 std over 3 seeds (AIM: 1 seed). Dashed: non-DP baselines; dotted: real-data TRTR.](figures/fig_res_01_epsilon_vs_f1_xgboost.png){width=4.6in}

## Fidelity

Table {tab:fidelity} gives the fidelity metrics.

**One-way fidelity.**

- Categorical TVD falls steadily with ε for AIM and MST, reaching 0.003–0.009 at ε = 10. PrivBayes plateaus at about 0.034.
- Numerical KS {eq:ks} is about 0.08–0.09 for every DP run except PrivBayes at ε = 0.5 (0.145). This floor comes largely from reconstructing values uniformly within bins.
- The non-private generators have *worse* one-way fidelity: KS 0.326 (CTGAN) and 0.248 (TVAE), TVD 0.095 and 0.117. Mode-specific normalisation struggles with the spike-inflated columns.

**Higher-order fidelity** (Fig. {fig:3way}).

- AIM has the lowest 3-way TVD at ε = 0.5 (0.224, against 0.318 for MST and 0.304 for PrivBayes).
- AIM and PrivBayes improve with ε to about 0.14–0.15 at ε = 10.
- MST plateaus at about 0.24, because a tree of two-way marginals cannot represent three-way structure. The difference in Cramér's V shows the same pattern.
- CTGAN (0.269) and TVAE (0.288) are worse than every DP method at ε ≥ 3.

{{INCLUDE:generated/table_fidelity.md}}

![{fig:3way} Privacy budget versus mean 3-way marginal TVD (lower is better).](figures/fig_res_03_epsilon_vs_3way_error.png){width=4.6in}

## Empirical Privacy

**The attack cannot separate the methods.** The 1-NN membership attack {eq:mia} gave a mean AUC between 0.492 and 0.510 for every configuration, **including the non-private CTGAN and TVAE** (Fig. {fig:mia}, Table {tab:privacy}). TPR at FPR 0.1 was 0.07–0.11, which is what random guessing gives.

**Why this is not evidence of privacy.** The attack is weak, and the measurement is diluted in two ways:

1. 18 records are shared by the member and non-member sets because the data contain duplicates.
2. The near-duplicate threshold is 0, so only exact copies are counted.

So the attack cannot distinguish these methods; it does *not* establish that the non-DP baselines are safe. Stronger, density-based attacks are known to succeed against non-DP generators [@stadler2022; @vanbreugel2023domias].

**Signals of memorisation.** The distance-based diagnostics do reveal them:

- TVAE's mean distance to the closest real record (0.74) is less than half that of every other method (≥ 1.51).
- TVAE emitted exact copies of training rows in two of its three runs (2, 0 and 1 rows).
- No DP run produced an exact copy.
- For the DP methods, DCR shrinks as ε grows — for example, AIM from 1.86 to 1.51 — as expected from weaker noise.

![{fig:mia} Privacy budget versus distance-based MIA AUC. Values near 0.5 for all methods, including non-DP baselines, indicate a weak attack rather than safety.](figures/fig_res_05_epsilon_vs_mia_auc.png){width=4.6in}

{{INCLUDE:generated/table_privacy.md}}

{{INCLUDE:generated/table_rarefair.md}}

## Rare Patterns

Only four categories are rare (below 1%) in the training data, so the category-level results are coarse (Fig. {fig:rare}, Table {tab:rarefair}).

- **TVAE** erased all four rare categories and 84% of rare 2-way combinations — a strong mode-collapse signature.
- **MST** kept every rare category but lost 41–48% of rare combinations at every ε.
- **PrivBayes** lost rare categories at low ε (42% at ε = 0.5) and improved steadily on combinations, from 26% to 11%.
- **AIM** lost 17–46% of rare combinations, without a monotone trend.
- **CTGAN** preserved rare combinations best (4%).

For applications that depend on small subpopulations, these results argue *against* MST and TVAE.

![{fig:rare} Privacy budget versus percentage of rare 2-way attribute combinations lost.](figures/fig_res_06_epsilon_vs_rare_loss.png){width=4.6in}

## Fairness

A Logistic Regression trained on the real data has a demographic-parity difference (ΔDP, {eq:fair}) of 0.169 between men and women, and an equalised-odds gap of 0.215. Synthetic-data classifiers vary widely (Fig. {fig:fair}).

- **AIM at ε = 3** reached ΔDP = 0.477 and an equalised-odds gap of 1.0. In other words, its classifier treated the two groups completely differently on one error type. This is a single run.
- **Very low ΔDP at low ε** — PrivBayes at ε = 0.5 (0.004) and AIM at ε = 0.5 (0.045) — reflects classifiers that rarely predict the positive class for anyone. It is fairness by uselessness, not genuine parity.
- **The non-private baselines** (ΔDP 0.23–0.24) and most DP runs at ε ≥ 1 show *larger* disparities than the real-data model. This is consistent with the disparate-impact findings for DP and for synthetic data [@bagdasaryan2019; @ganev2022].

With one classifier per run and 193 women in the test set, these fairness estimates are noisy. They should be read as a warning sign, not a ranking.

![{fig:fair} Privacy budget versus demographic-parity difference (sex) of a Logistic Regression trained on synthetic data. Real-data reference: 0.169.](figures/fig_res_07_epsilon_vs_dp_difference.png){width=4.6in}

## Runtime

Fit times (Fig. {fig:runtime}) separate the methods clearly:

- PrivBayes: 0.5–21 s, growing with ε as larger networks become affordable.
- MST: 25–58 s.
- TVAE: 41 s.
- CTGAN: 238 s.
- AIM: 52–626 s, even with the 60-round cap.

The two AIM ε = 3 records (181 s and 436 s) show that runtimes vary by more than a factor of two between repeats of the same configuration, so small runtime differences should not be over-interpreted.

![{fig:runtime} Fit runtime versus privacy budget (log–log). Non-DP baselines shown at 300 epochs.](figures/fig_res_08_runtime.png){width=4.6in}

## Knowledge-Discovery Findings (RQ3)

**The LLM layer works within its privacy design.** All 35 DP datasets load. The original file is never read, the payload contains no row-level data, and demo output is labelled. Live mode is implemented and tested against a mock server, but not against the real API.

**How trustworthy the payload is** (Table {tab:ku}, Fig. {fig:ku}). Knowledge utility rises with ε for AIM (KU 0.88 → 0.95; Spearman ρ 0.32 → 0.88) and PrivBayes (KU 0.86 → 0.92; ρ 0.07 → 0.82). At ε ≥ 5 the payloads rank the subgroup income rates in nearly the same order as the real data. **MST payloads do not**: ρ stays at or below 0.30 at every ε, even though MST's one-way TVD is the best of all methods. A dataset can match its marginals and still give misleading subgroup "insights". This is precisely the case that one-way fidelity metrics miss.

**Spurious associations.** In the AIM and MST ε = 3 datasets, the strongest associations reported to the LLM included education ↔ race with Cramér's V of 0.493 and 0.450, against **0.119 in the real training split**. PrivBayes (0.062) and TVAE (0.068) did not show this artefact. Relationship ↔ sex, a genuine structural association, was preserved by all of them (0.62–0.65 against 0.65 real). An LLM given the AIM ε = 3 payload would — correctly, from its input — describe a strong education–race link that does not exist in the population. This is the over-trust threat A6 made concrete. It is why the payload carries quality metrics and why outputs are framed as hypotheses.

{{INCLUDE:generated/table_ku.md}}

![{fig:ku} Knowledge utility (left) and Spearman rank agreement of subgroup target rates (right) between LLM payload statistics and the real training split.](figures/fig_res_12_knowledge_utility.png){width=6.2in}

## Answering the Research Questions

**RQ1** — AIM provides the best DP fidelity at small ε and competitive utility, so the hypothesis that it is the strongest DP method is **partly supported**. At ε ≥ 3 its single-seed results lie within PrivBayes's seed spread. It is the slowest DP method (up to 626 s per fit, against at most 58 s for MST and 21 s for PrivBayes), and it had the worst fairness outlier. PrivBayes is the most cost-effective at ε ≥ 3 but unusable at ε = 0.5. MST is fast and stable but weakest on utility, higher-order fidelity, rare combinations and knowledge utility. Among the non-DP baselines, TVAE has the best utility but memorisation signals and the worst rare-pattern loss.

**RQ2** — Utility, higher-order fidelity and knowledge utility improve markedly from ε = 0.5 to ε = 3, then flatten. Fairness and rare-pattern behaviour do not improve monotonically.

**RQ3** — An aggregate-only LLM layer can be built without exposing the original records. The trustworthiness of what it reasons over depends strongly on the generator and ε, and needs an explicit check.

# Comparative Analysis

## Privacy–Utility Trade-off

Fig. {fig:pu} plots every run's MIA AUC against its XGBoost F1. Because the AUC does not vary, the empirical axis cannot rank the methods. The meaningful privacy axis is the *formal* ε, which only the DP methods have. On that axis, Fig. {fig:f1} shows that AIM and PrivBayes reach TVAE-level utility at ε = 3–5 *with* a guarantee, while TVAE offers none. Practically, the price of DP at ε = 3–5 on this dataset is 0–4 percentage points of XGBoost retention relative to TVAE (AIM 81–85%, PrivBayes 79–82%, TVAE 85%). On top of that come AIM's runtime cost and PrivBayes's fragility at low ε.

![{fig:pu} Empirical privacy–utility scatter (each point is one run).](figures/fig_res_09_privacy_utility_scatter.png){width=4.6in}

## Multi-Dimensional Comparison

The heatmap (Fig. {fig:heat}) and radar chart (Fig. {fig:radar}) compare the DP methods at ε = 3 with the non-DP baselines across all dimensions. No method dominates:

- **AIM and PrivBayes** lead on higher-order fidelity and utility.
- **CTGAN** leads on rare combinations but is worst on one-way fidelity.
- **TVAE** leads on utility and has the worst rare-pattern loss.
- **MST** leads on one-way categorical fidelity.

This supports the project's design decision not to compute a weighted overall score.

![{fig:heat} Metric heatmap at ε = 3 (DP) and for non-DP baselines; cell text shows raw values, colour is column-normalised. Candidate for the appendix.](figures/fig_res_11_heatmap_eps3.png){width=6.3in}

![{fig:radar} Radar comparison at ε = 3 using bounded "higher is better" transforms of the raw metrics (no min–max rescaling).](figures/fig_res_13_radar_eps3.png){width=3.8in}

## Method Profiles

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

## Comparison with Other Approaches

**Standard (non-private) generative models.** CTGAN and TVAE represent standard generative AI for tables. TVAE matches the DP methods on utility but offers no guarantee and showed memorisation signals. Stronger non-private models, such as diffusion [@kotelnikov2023] or LLM-based generators [@borisov2023], would probably raise fidelity further, with the same privacy caveat.

**DP training of deep models.** DP-SGD versions of CTGAN or TVAE, or PATE-GAN [@jordon2019pategan], would add a guarantee to the deep models. Benchmarks report that they usually trail marginal-based methods on tabular utility at equal ε [@tao2021bench; @chen2025bench]. They were not run here.

**Federated approaches.** Federated learning [@kairouz2021fl] addresses a different setting, in which data cannot be centralised. It still needs DP to bound what the updates reveal. The centralised-curator model used here is simpler when one custodian holds the data.

**Secure retrieval systems.** RAG over the raw records would give an LLM direct access to individual rows and inherits retrieval-store leakage [@zeng2024rag]. The design here deliberately avoids retrieval over sensitive data: the LLM sees only aggregates of a DP release.

**Private Evolution.** API-only DP synthesis [@lin2024pe; @xie2024pe] is a promising alternative where only a foundation-model API is available. Tabular versions remain future work.

**Position of this study's LLM layer.** Compared with these alternatives, the layer occupies a deliberately conservative point in the design space.

- It needs no model training and no DP accounting of its own.
- It cannot leak more than the DP release it summarises.
- The price is reduced expressiveness: the LLM can only reason about the statistics it is given, cannot answer arbitrary questions about the data, and inherits every artefact of the synthetic data.

A RAG system over the raw data would be more expressive and far riskier. DP fine-tuning of an LLM on the raw data would be expressive, protected by DP, and expensive. The design chosen here is the cheapest one that keeps a clean privacy argument.
