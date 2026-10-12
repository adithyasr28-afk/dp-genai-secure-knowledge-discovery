# Experimental Setup

## Dataset and Splits

The data are the 3,000-record Adult sample described in Section V. A stratified 80/20 split on *income* with seed 42 gives 2,400 training and 600 test records. Every generator is fit on the training split, and every synthetic dataset has 2,400 rows (size multiplier 1.0). The test split is used only for scoring: TSTR/TRTR utility, fairness and non-member candidates for the MIA. The sensitive attribute for fairness is *sex* (33.0% female).

## Generators and Configurations

Table {tab:config} lists the 41 configurations of the sweep (`experiments/config.py`, run with `run_sweep.py`). Additional settings:

- CTGAN and TVAE use 300 epochs and a batch size of 500. They use a GPU if one is available, and the hardware of the original runs was not recorded.
- AIM's rounds are capped at 60, as explained in Section IX.
- Within each family, the seeds are 42, 43 and 44.

The DP wrappers do not forward the seed to the underlying synthesizers. For DP methods the seed therefore controls only the evaluation randomness (3-way query sampling, rare-combination sampling, MIA candidate sampling and inverse binning). The generators' own randomness is uncontrolled.

Table: {tab:config} Experimental configuration

| Method | Library (version) | Guarantee | ε values | δ | Seeds | Other settings | Runs |
|---|---|---|---|---|---|---|---|
| AIM | smartnoise-synth 1.0.8, mbi 1.1.0 | (ε, δ)-DP, zCDP | 0.5, 1, 3, 5, 10 | 10⁻⁵ | 1 | rounds ≤ 60 (paper: 16·d = 224) | 5 |
| MST | smartnoise-synth 1.0.8, mbi 1.1.0 | (ε, δ)-DP, zCDP | 0.5, 1, 3, 5, 10 | 10⁻⁵ | 3 | — | 15 |
| PrivBayes | synthetic_data_generation 0.1.14 | pure ε-DP | 0.5, 1, 3, 5, 10 | 0 | 3 | numpy.product shim | 15 |
| CTGAN | ctgan 0.12.1 | none | — | — | 3 | 300 epochs, batch 500 | 3 |
| TVAE | ctgan 0.12.1 | none | — | — | 3 | 300 epochs, batch 500 | 3 |
| **Preprocessing (all)** | in-house | — | — | — | — | 10 quantile bins + spike bin (≥ 30%); rare < 1% → `__RARE__` | **41** |

## Implementation Environment

- **Software:** Python 3.11; pandas 2.3.3, NumPy 2.4.6, scikit-learn 1.8.0, XGBoost 3.2.0, PyTorch 2.14.0, Streamlit 1.64.0, OpenDP 0.14.2, anthropic 1.13.0, google-genai 2.29.0. Live LLM model: `gemini-flash-latest` (served by `gemini-3.8-flash`).
- **Pinning:** the exact versions are pinned in `constraints.txt`, recovered from the original environment.
- **Original runs:** the 43 logged runs were executed on 18 September 2026 on the original authors' Windows machine. Its hardware specification was not recorded, so the runtimes in Section XIV are indicative only.
- **Verification environment:** a fresh environment with the same package versions on Windows 11, using CPU only, for re-evaluation, testing and the dashboard checks.

**Checks executed for this report (12 October 2026).** In the verification environment:

- the full test suite (48 tests, including five end-to-end generator runs) passed with one opt-in live test skipped, in 337 s;
- a fresh clone installed into a new Python 3.11 environment from `requirements.txt` and `constraints.txt`, and its fast tests passed;
- re-running the three analysis scripts on the saved outputs reproduced every table and figure byte for byte, apart from embedded SVG timestamps;
- the dashboard was driven through all ten feature areas, including one demonstration generator run (PrivBayes, ε = 3, seed 7; 4.1 s fit time), which was removed from the log afterwards.

No reported number depends on these checks; they establish that the numbers can be regenerated.

## Benchmark Scenarios

The evaluation covers three scenarios:

- **S1 — ε sweep.** Each DP method at five budgets, for RQ2.
- **S2 — cross-family comparison.** DP methods at ε = 3 against the non-DP baselines, for RQ1.
- **S3 — knowledge discovery.** The aggregate summary of each DP dataset compared with the same summary on real data, plus dashboard operation of the LLM layer, for RQ3.

Fig. {fig:evalfw} shows how runs flow into the evaluation and verification stages.

![{fig:evalfw} Experimental evaluation framework.](figures/diagrams/fig10_experimental_evaluation_framework.png){width=6.3in}

## Threats to Validity

**Internal validity.**

- The DP generators are unseeded, so a single run's numbers include generator randomness. AIM's single seed leaves no way to separate signal from that noise.
- All methods share one preprocessing protocol. That is fair, but it may favour methods whose assumptions it matches.

**Construct validity.**

- The 1-NN membership attack measures only one kind of leakage, and the near-duplicate threshold degenerates to exact matching.
- The fairness metric depends on one classifier.
- Knowledge utility covers only target rates by single attributes.

**External validity.** One small census sample; findings may not hold for wider, larger or differently distributed data.

**Conclusion validity.** No significance testing. Reported differences smaller than about two seed standard deviations should not be read as rankings.

## Verification Protocol

Because the report must rest only on saved outputs, `analysis/verify_results.py` performs five steps:

1. It checks log integrity (record count, unique identifiers, statuses).
2. It de-duplicates by keeping the latest completed record per identifier, consistent with the CSV on disk.
3. It checks each configuration's privacy parameters.
4. It recomputes every metric from the saved CSV with the project's own evaluation code and compares it with the logged value, using a tolerance of 10⁻⁶.
5. It computes the TRTR reference and a real-data fairness reference, neither of which was logged originally.

No generator was re-trained for the reported results. Re-training would not reproduce the saved data, because the DP generators are unseeded.

# Evaluation Metrics

## Why These Metrics

The metric set follows recent DP-synthesis benchmarks [@tao2021bench; @chen2025bench], with three additions.

Fidelity is measured at three levels, because each level can fail independently. One-way marginals can be perfect while correlations are wrong, and pairwise correlations can be right while three-way structure is broken.

Utility uses the TSTR protocol with three model families, so that one model's inductive bias does not decide the result. Retention relative to TRTR puts all numbers on the same scale.

The three additions:

1. **Empirical privacy.** It cannot certify privacy, but it can reveal gross failures such as copying, and it shows how weak or strong a particular attack is.
2. **Fairness and rare patterns.** DP's harms concentrate there [@bagdasaryan2019; @ganev2022].
3. **Knowledge utility.** This is the metric the LLM layer depends on.

No metric is aggregated into an overall score.

## Definitions

Table {tab:metrics} defines the metrics; the main formulas follow. Real training data are denoted $r$ and synthetic data $s$.

**Fidelity.** For each numerical column, the Kolmogorov–Smirnov statistic between the empirical CDFs is

$$\mathrm{KS}=\sup_x\big|F_r(x)-F_s(x)\big| $$ {#eq:ks}

and for each categorical column, the total variation distance is

$$\mathrm{TVD}(P_r,P_s)=\tfrac12\textstyle\sum_{v}\big|P_r(v)-P_s(v)\big| $$ {#eq:tvd}

The *3-way TVD* applies {eq:tvd} to the joint distribution of 30 randomly chosen triples of categorical columns and averages the results. It tests whether higher-order structure survives. Correlation fidelity is measured by the Frobenius norm of the difference between Pearson matrices, and by the mean absolute difference in bias-corrected Cramér's V.

**Utility.** Train-on-synthetic, test-on-real (TSTR) F1 is computed for Logistic Regression, Random Forest (200 trees) and XGBoost (200 trees) on the real test split, with one-hot encoding fixed to the training vocabulary. *Utility retention* is

$$R_{F1}=100\cdot \mathrm{F1}_{\mathrm{TSTR}}\,/\,\mathrm{F1}_{\mathrm{TRTR}} $$ {#eq:retention}

**Empirical privacy.** Members are 600 training records and non-members are 600 test records. Each candidate $x$ is scored by its negative distance to the nearest synthetic record in a standardised, one-hot feature space $\phi$:

$$\mathrm{score}(x)=-\min_{y\in\tilde D}\lVert\phi(x)-\phi(y)\rVert_2 $$ {#eq:mia}

The attack AUC and the TPR at FPR = 0.1 are reported. An AUC of 0.5 means the attack does no better than chance. The *distance to closest record* (DCR) and the share of synthetic records at or below the 1st percentile of real-to-real nearest-neighbour distances ("near-duplicates") are also reported.

**Fairness.** A Logistic Regression is trained on synthetic data and scored on the real test set, grouped by sex. The metrics are the demographic-parity difference and the equalised-odds gap [@mehrabi2021]:

$$\Delta_{\mathrm{DP}}=\max_g P(\hat y=1\mid A=g)-\min_g P(\hat y=1\mid A=g),\qquad \Delta_{\mathrm{EO}}=\max\big(\Delta_{\mathrm{TPR}},\Delta_{\mathrm{FPR}}\big) $$ {#eq:fair}

**Rare patterns.** The rare-pattern metrics are:

- the share of categories with frequency below 1% in the real training data that disappear from the synthetic data;
- the same for 2-way value combinations below 0.5%, across all 36 pairs of the 9 categorical columns;
- the largest absolute change in class share.

**Runtime.** Fit and sample wall-clock time, in seconds.

## Statistical Resolution

Some metrics are noisy at this sample size, and their resolution limits what the results can show. With 600 members and 600 non-members, the AUC of an attack that guesses at random has a standard deviation of $\sqrt{(n_1+n_2+1)/(12\,n_1 n_2)}\approx 0.017$ (the null distribution of the Mann–Whitney statistic). A random attack would therefore score between about 0.47 and 0.53 in 95% of runs. Every one of the 41 observed AUCs (0.478–0.525) falls in that interval, which is a second reason, besides the attack's weakness, not to read differences between them. Similarly, the fairness metrics rest on 193 women in the test split, and F1 on 144 positive test cases, so differences of a few points between single runs are within sampling noise.

**Knowledge utility.** KU, Spearman ρ and top-1 agreement, as defined in {eq:ku}.

Table: {tab:metrics} Evaluation metrics definition

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
