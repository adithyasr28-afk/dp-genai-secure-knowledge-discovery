# Background and Literature Review

## Differential Privacy

A randomised mechanism $\mathcal{M}$ is $(\varepsilon,\delta)$-differentially private if, for all pairs of datasets $D, D'$ that differ in one record and for all output sets $S$ [@dwork2006; @dwork2014]:

$$\Pr[\mathcal{M}(D)\in S]\;\le\; e^{\varepsilon}\,\Pr[\mathcal{M}(D')\in S] + \delta $$ {#eq:dp}

Here $\varepsilon$ is the privacy budget: smaller values mean stronger protection. $\delta$ is a small probability of exceeding that bound, usually chosen well below $1/n$. When $\delta = 0$ the guarantee is called *pure* DP. The guarantee is easiest to read through the privacy-loss random variable for an output $o$:

$$\mathcal{L}_{D,D'}(o) \;=\; \ln\frac{\Pr[\mathcal{M}(D)=o]}{\Pr[\mathcal{M}(D')=o]} $$ {#eq:privloss}

Pure $\varepsilon$-DP bounds the privacy loss in {eq:privloss} by $|\mathcal{L}|\le\varepsilon$ for every output. $(\varepsilon,\delta)$-DP allows the bound to fail with probability at most $\delta$.

Three properties make DP practical:

- **Post-processing.** If $\mathcal{M}$ is $(\varepsilon,\delta)$-DP, then $g\circ\mathcal{M}$ is too, for any $g$ that does not touch $D$ again.
- **Composition.** Budgets of successive mechanisms add up.
- **Group privacy.** The guarantee degrades gracefully, by a factor $k$, for groups of $k$ records [@dwork2014].

The post-processing property is what licenses the knowledge-discovery layer in this work. Computing statistics on DP synthetic data, or giving them to an LLM, costs no further budget — *provided* nothing in that pipeline consults the real data. Section VII-E lists the two places where this implementation does consult it.

The basic mechanisms add noise scaled to a query's sensitivity $\Delta f$, the maximum change in $f$ caused by one record. The Laplace mechanism with noise scale $\Delta_1 f/\varepsilon$ gives pure DP. The Gaussian mechanism is analysed most tightly with zero-concentrated DP (zCDP) [@bun2016], where adding $\mathcal{N}(0,\sigma^2)$ noise to a query of $\ell_2$ sensitivity $\Delta_2$ costs $\rho = \Delta_2^2/(2\sigma^2)$. zCDP composes additively, and converts to $(\varepsilon,\delta)$-DP as

$$\varepsilon \;=\; \rho + 2\sqrt{\rho\,\ln(1/\delta)} $$ {#eq:zcdp}

The exponential mechanism [@mcsherry2007] selects a discrete candidate $r$ with probability proportional to $\exp\!\big(\varepsilon\,q(D,r)/(2\Delta q)\big)$, where $q$ is a quality score. AIM and PrivBayes use it to choose *which* statistics to measure. Rényi-DP and related numerical accountants are now the standard way to track the cumulative loss of DP-SGD [@abadi2016; @ponomareva2023]. Practical guidance on stating guarantees, choosing $\delta$ and reporting the unit of privacy is collected in [@ponomareva2023] and in NIST SP 800-226 [@near2025].

## The Privacy–Utility Trade-off

Every DP release trades privacy for accuracy. The design problem can be written as choosing, from the family $\mathcal{A}_{\varepsilon,\delta}$ of mechanisms that satisfy {eq:dp}, the one that maximises an expected utility $U$ of its output:

$$\mathcal{M}^{*} \;=\; \arg\max_{\mathcal{M}\in\mathcal{A}_{\varepsilon,\delta}}\; \mathbb{E}\big[\,U(\mathcal{M}(D))\,\big] $$ {#eq:tradeoff}

No single $U$ in {eq:tradeoff} captures all uses of synthetic data. A table can match every one-way distribution and still break correlations, or support a classifier well while erasing a rare subgroup. This study therefore reports a vector of utilities (Section XIII) rather than one score. That follows recent benchmarks [@chen2025bench; @tao2021bench], which found that conclusions change with the metric and with preprocessing choices.

## Differentially Private Synthetic Data

**Marginal-based (select–measure–generate) methods.**

- *PrivBayes* [@zhang2017privbayes] uses the exponential mechanism to learn a Bayesian network of low-degree conditional distributions, then releases those conditionals with Laplace noise. This gives pure $\varepsilon$-DP.
- *MST* [@mckenna2021mst] selects a maximum spanning tree of two-way marginals, measures all one-way and selected two-way marginals with Gaussian noise, and fits a graphical model with Private-PGM. A variant of MST won the 2018 NIST synthetic-data challenge.
- *AIM* [@mckenna2022aim] makes the selection adaptive. Over $T$ rounds it uses the exponential mechanism to pick the workload marginal that the current model approximates worst, measures it, and refits the model, allocating budget with zCDP.

Both independent benchmarks found that marginal-based methods often give the best utility at moderate budgets [@tao2021bench; @chen2025bench]. Chen *et al.* also reported that they are markedly slower than most deep-learning alternatives [@chen2025bench].

**Deep generative models.**

- *CTGAN* and *TVAE* [@xu2019ctgan] are the reference conditional GAN and variational autoencoder for mixed-type tables, distributed in the open-source `ctgan` package. They give no formal privacy guarantee.
- DP variants train with DP-SGD [@abadi2016] or with the PATE framework; the benchmarks cited above include such DP GANs and find that they usually trail marginal-based methods on tabular data [@tao2021bench; @chen2025bench].
- Many further generator families have been proposed and surveyed, for example for health records [@hernandez2022; @murtaza2023]. Without an explicit DP training procedure, none of them carries a formal privacy guarantee.

**Privacy of "anonymous" synthetic data.** Stadler *et al.* showed that synthetic data produced without DP gives an unpredictable and often poor privacy–utility trade-off. Linkage and membership attacks still succeed against outlier records [@stadler2022]. Distance-based and density-based membership attacks on generative models are described in [@hilprecht2019] and [@vanbreugel2023domias]. Shadow-model attacks and the low-false-positive reporting convention come from [@shokri2017; @carlini2022lira]. Empirical audits can lower-bound the true leakage of a DP implementation [@jagielski2020].

**Fairness and rare groups.** DP noise hurts small groups most. DP training has a disparate impact on accuracy [@bagdasaryan2019], and Ganev *et al.* found that DP synthetic data can either flatten ("Robin Hood") or exaggerate ("Matthew") group imbalances, with accuracy loss concentrated on minorities [@ganev2022]. Rosenblatt *et al.* proposed *epistemic parity* — whether conclusions drawn from synthetic data reproduce those drawn from real data — as an evaluation criterion [@rosenblatt2023]. That idea motivates the knowledge-utility check in Section X.

## Privacy in Large Language Models and Generative AI

LLMs memorise training data and can be made to emit verbatim training sequences [@carlini2021extract]. Lukas *et al.* demonstrated extraction, reconstruction and inference of personally identifiable information from fine-tuned models [@lukas2023]. Surveys organise these threats alongside misuse risks [@yao2024survey; @weidinger2022].

Mitigations at training time include DP fine-tuning, which is now practical for large models [@li2022llmdp]. At generation time, *Private Evolution* produces DP synthetic data with only API access to a foundation model [@lin2024pe].

Retrieval-augmented generation (RAG), which grounds an LLM in documents retrieved at query time, adds a document store that can itself leak [@zeng2024rag]. Instructions hidden in retrieved content can hijack an LLM-integrated application [@greshake2023]. Federated learning keeps raw data local but needs DP to bound what the updates reveal [@kairouz2021fl].

## Other Privacy-Enhancing Technologies

DP is one of several privacy-enhancing technologies, and it is worth being clear about why it is the right tool here.

**Syntactic anonymisation** — k-anonymity and its refinements — generalises or suppresses quasi-identifiers until each record hides among k others. It offers no protection against adversaries with auxiliary information, and it degrades badly in high dimensions. Synthetic data produced without DP inherit a similar weakness [@stadler2022].

**Cryptographic techniques** — secure multi-party computation, homomorphic encryption and trusted execution environments — protect data *during* computation, so that no party sees another's inputs. They say nothing about what the *output* reveals.

**Federated learning** keeps data where they are, but its model updates leak unless combined with DP [@kairouz2021fl].

DP is the only one of these that bounds what a released output reveals about any individual, which is exactly the problem of publishing a synthetic table or an explanation. In practice these technologies complement each other. A deployment could combine a trusted environment for generation, DP for the release, and encrypted transport for the LLM call.

## Secure Knowledge Discovery and Governance

Knowledge discovery is the extraction of useful, understandable patterns from data. Doing it securely means controlling who sees which data, at which granularity, under what guarantee, and with what accountability. Fig. {fig:eco} places the actors of this study in such an ecosystem: data subjects, a trusted curator who holds the raw data and the budget, a DP release, analysts and an LLM service, overseen by governance.

Governance instruments that complement the technical layer include:

- documentation artefacts — datasheets for datasets [@gebru2021] and the related practice of model documentation;
- risk frameworks — the NIST Privacy Framework [@nist2020pf] and the AI Risk Management Framework [@nist2023airmf];
- management-system standards — ISO/IEC 27701 [@iso27701] and ISO/IEC 42001 [@iso42001].

![{fig:eco} Secure knowledge-discovery ecosystem assumed in this study. Dashed arrows are governance relationships; the LLM receives only aggregates of the DP release.](figures/diagrams/fig02_secure_knowledge_discovery_ecosystem.png){width=6.2in}

## A Taxonomy of the Literature

The work reviewed above falls into six strands, distinguished by *what* is protected, *where* in the pipeline protection is applied, and *which* threat is addressed:

1. **DP foundations and accounting** — definitions, mechanisms and composition [@dwork2006; @dwork2014; @mcsherry2007; @bun2016], with practical guidance on stating guarantees [@ponomareva2023; @near2025].
2. **DP synthesis of tabular data** — marginal-based methods that measure noisy marginals and fit a model [@zhang2017privbayes; @mckenna2021mst; @mckenna2022aim], deep generators trained with DP-SGD [@abadi2016], and the benchmarks that compare them [@tao2021bench; @chen2025bench].
3. **Attacks and audits** — membership inference [@shokri2017; @hilprecht2019; @vanbreugel2023domias; @carlini2022lira], model inversion [@fredrikson2015], the privacy gain of synthetic data [@stadler2022] and empirical auditing of DP claims [@jagielski2020].
4. **LLM privacy** — memorisation and extraction [@carlini2021extract; @lukas2023], DP fine-tuning and API-only DP synthesis [@li2022llmdp; @lin2024pe], and the risks of retrieval and prompt injection [@zeng2024rag; @greshake2023], surveyed in [@yao2024survey; @weidinger2022].
5. **Fairness under privacy** — disparate impact of DP on accuracy and on synthetic data [@bagdasaryan2019; @ganev2022], within the wider fairness literature [@mehrabi2021].
6. **Governance** — regulation, risk frameworks and documentation [@gdpr2016; @nist2020pf; @nist2023airmf; @gebru2021].

Most studies sit inside one strand. The benchmarks in strand 2 do not consider explanation, and the LLM work in strand 4 is about text, not about tables released under DP. This study connects strands 2, 3 and 4. It asks what an LLM says about DP synthetic data and checks the answer against the real data, using strand 5 to test whether subgroup patterns survive and strand 6 to frame the controls.

## Comparative Summary and Research Gap

Table {tab:lit} compares representative works. Three gaps motivate this study:

1. Benchmarks of DP synthesis rarely report fairness, rare-pattern loss and empirical attacks *together* with utility.
2. LLM-based analysis of DP synthetic data is discussed but seldom measured against what the same statistics look like on the real data.
3. Student-scale reproductions seldom verify their logged results or disclose the assumptions behind the guarantee — for example, the public-domain assumption for preprocessing.

Table: {tab:lit} Comparison of representative literature

| Work | Data / setting | Privacy mechanism | Main contribution | Limitation relevant here |
|---|---|---|---|---|
| Zhang *et al.* 2017 [@zhang2017privbayes] | Tabular | Pure ε-DP (exponential + Laplace) | Bayesian-network synthesis (PrivBayes) | Network degree limits higher-order fidelity |
| McKenna *et al.* 2021 [@mckenna2021mst] | Tabular | (ε, δ) via zCDP | MST + Private-PGM; NIST 2018 winner | Fixed tree; no workload adaptivity |
| McKenna *et al.* 2022 [@mckenna2022aim] | Tabular | (ε, δ) via zCDP | Adaptive workload-aware AIM | High runtime for many rounds |
| Xu *et al.* 2019 [@xu2019ctgan] | Tabular | None | CTGAN / TVAE for mixed types | No guarantee; memorisation risk |
| Tao *et al.* 2021 [@tao2021bench] | Tabular benchmark | Marginal-based and DP-GAN methods | Marginal-based methods lead on utility | Older method set; no LLM layer |
| Stadler *et al.* 2022 [@stadler2022] | Tabular | Evaluates DP and non-DP | Privacy gain of synthetic data is unpredictable without DP | Attack-specific |
| Ganev *et al.* 2022 [@ganev2022] | Tabular | DP generators | Disparate impact on subgroups | Classification tasks only |
| Chen *et al.* 2025 [@chen2025bench] | Tabular benchmark | Many DP methods | Unified preprocessing/evaluation; utility vs efficiency | No LLM layer |
| Carlini *et al.* 2021 [@carlini2021extract] | LLM | None | Training-data extraction from LLMs | Attack, not defence |
| Li *et al.* 2022 [@li2022llmdp] | LLM fine-tuning | DP-SGD | Strong DP fine-tuning of LLMs | Requires model training |
| Lin *et al.* 2024 [@lin2024pe] | Images | DP via API-only Private Evolution | DP synthetic data without training | Images, not tables |
| Zeng *et al.* 2024 [@zeng2024rag] | RAG | — | Retrieval-store leakage | No DP mechanism |
| **This study** | Tabular + LLM explanations | (ε, δ) and pure ε via generators; post-processing | Verified 5-method comparison + aggregate-only LLM layer + knowledge-utility check | One small dataset; two live LLM responses evaluated |
