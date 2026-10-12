# Compliance, Governance, and Regulatory Analysis

## Approach

This section maps the framework onto the principal regulations and standards. It distinguishes controls that are *implemented in the artefact* from those that an adopting organisation would have to supply. Nothing here is legal advice, and the artefact has not been audited for compliance. Fig. {fig:compliance} and Table {tab:compliance} summarise the mapping.

![{fig:compliance} Compliance and governance mapping: obligations → control objectives → implemented (solid) and organisational (dashed) controls.](figures/diagrams/fig12_compliance_governance_mapping.png){width=6.3in}

## Regulations

**GDPR** [@gdpr2016].

- Recital 26 excludes anonymous information from the Regulation's scope. Whether DP synthetic data qualifies depends on whether identification remains "reasonably likely", which in turn depends on ε, on the assumptions behind the guarantee, and on the context. A low ε strengthens the argument, but no particular ε is recognised as sufficient.
- The real data remain personal data throughout, and the generator's training is processing that needs a lawful basis.
- The framework supports Art. 5 (data minimisation, purpose limitation) and Art. 25 (data protection by design and by default) through DP at generation and the aggregate-only LLM layer.
- A DPIA (Art. 35) would be expected for large-scale processing of special-category data. Race is special-category data under Art. 9.

**India's Digital Personal Data Protection Act, 2023** [@dpdp2023].

- The Act regulates digital personal data processed by Data Fiduciaries on the basis of consent or legitimate uses.
- It requires reasonable security safeguards, breach notification, and erasure when the purpose is served.
- DP synthesis supports minimisation and limits breach impact if synthetic data leak. Training on real data still needs a valid basis.
- The Digital Personal Data Protection Rules, 2025 were notified on 14 November 2025 with staggered commencement; most obligations on Data Fiduciaries — notice and consent, security safeguards, breach reporting and retention — apply from 14 May 2027. A deployment planned for 2026–27 should be designed against them now.

**HIPAA** [@hipaa2012]. De-identification uses either *Safe Harbor* (removing 18 identifier types) or *Expert Determination* (a qualified expert finds the risk of re-identification very small). A DP synthetic release would fall under Expert Determination, with ε and the threat model as part of the expert's evidence.

**CCPA/CPRA** [@ccpa2018]. Deidentified data are excluded from "personal information" when the business takes reasonable measures, publicly commits not to re-identify, and binds recipients contractually. The latter two are organisational controls.

**EU AI Act** [@euaiact2024]. The LLM layer is a limited-risk use of a general-purpose model: an assistant for analysts, not an automated decision about people. If synthetic data were used to train a high-risk system — for example, credit scoring — the Art. 10 data-governance requirements would apply, including examination of possible biases. The fairness results in Section XIV are directly relevant to that examination.

## Frameworks and Standards

- **NIST Privacy Framework 1.0** [@nist2020pf]. Its *Identify-P* (inventory, data mapping), *Govern-P*, *Control-P* (data processing management, minimisation) and *Protect-P* functions map onto the classification, the budget policy and the path guards.
- **NIST AI RMF 1.0** [@nist2023airmf]. *Map* (context, threats), *Measure* (the six evaluation dimensions, the knowledge-utility check) and *Manage* (thresholds, human review).
- **NIST SP 800-226** [@near2025]. Asks evaluators to state the unit of privacy, the ε and δ, and the trust and threat assumptions. Sections VI and IX do so, including the assumption that the domain is public.
- **ISO/IEC 27701** [@iso27701] and **ISO/IEC 42001** [@iso42001]. Management-system wrappers — policies, roles, records and continual improvement — into which an organisation would place this pipeline.

## Governance Processes

Technical controls need processes around them. A minimal governance process for this framework has five steps:

1. **Intake.** A request for a synthetic release states its purpose, recipients and required analyses. The data owner approves the purpose.
2. **Assessment.** The custodian runs a DPIA-style assessment and proposes a mechanism and ε from evidence like Section XIV. The data-protection officer reviews the assessment.
3. **Generation and validation.** The release is generated in the trusted environment and evaluated on the six dimensions. The thresholds of the trust vector {eq:trust} are checked and the transparency report is drafted.
4. **Approval and release.** The owner signs off. The steward records the release in the ledger and the catalogue and attaches the transparency report.
5. **Monitoring.** Releases are reviewed periodically and retired when no longer needed. Incidents — for example, discovered artefacts or new attacks — trigger re-assessment.

The LLM layer slots in after step 4 as a consumer of approved releases. Its use is logged, and its outputs are reviewed by humans before they inform decisions.

## Evidence the Artefact Produces for Compliance

Compliance claims need evidence. The artefact already produces several pieces that an assessor would ask for:

- **For minimisation (GDPR Art. 5(1)(c); DPDP Act):** the payload manifest of every LLM request — minimum cell count, number of suppressed cells, rounding, whether real-data-derived metrics were included — stored in the audit record with a SHA-256 hash of the payload.
- **For accountability (GDPR Art. 5(2), Art. 30):** the append-only experiment log, which records configuration, guarantee statement and metrics per run, and the verification report that checks it.
- **For privacy by design (Art. 25):** the code-level guarantee labels and the test suite that checks the path guard and the absence of original rows in prompts.
- **For the DPIA (Art. 35):** Sections VI and XIV — threats, controls and measured residual risk.

**International transfers and processors.** In live mode the payload is sent to the chosen provider — in the recorded calls, Google's Gemini API. Even though the payload contains only aggregates of a DP release, an organisation would treat the provider as a processor: a data-processing agreement (GDPR Art. 28), a transfer mechanism if processing happens outside the jurisdiction (GDPR Chapter V), and a check that the destination is not restricted under Section 16 of the DPDP Act. The free tier used for testing does not meet these conditions, because its terms allow prompts to be used for product improvement.

## Mapping Summary

Table: {tab:compliance} Regulatory compliance matrix (✓ implemented in artefact; ◐ partially; ✗ organisational, not implemented)

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

# Ethical and Trustworthy AI Assessment

## Fairness

Synthetic data do not simply inherit the biases of the real data — they can change them. Here, most DP and non-DP runs *increased* the demographic-parity gap between men and women relative to the real-data model (Section XIV). One run produced a classifier with a complete error-rate disparity, and DP at low ε produced apparent parity only by failing everyone. Ethical use therefore requires subgroup evaluation of any model trained on synthetic data, not only aggregate accuracy [@mehrabi2021; @ganev2022].

**Fairness across other attributes.** The study measured fairness by sex only. The UI demonstration run on PrivBayes, ε = 3, scored the same classifier by race (`evidence/screenshots/2026-10-12/08_fairness_rare_patterns.png`). The four non-White groups had 5 to 58 test records each and subgroup F1 between 0 and 0.5, against 0.54 for the White group of 512. Subgroups this small cannot support conclusions, which is itself an ethical point: the groups most exposed to distortion are the ones for which the evidence is thinnest.

## Transparency and Accountability

The framework is transparent about four things:

- what was sent to the LLM;
- what is *not* LLM output (demo mode);
- what each dataset's guarantee is, and on what it depends;
- which results are single-seed.

Accountability rests on the audit trail. In an organisation, a named data owner would also approve each release and its ε.

## Responsible Knowledge Generation

The spurious education–race association and the reversed gender gap in Section XIV illustrate a specific ethical risk. Generated "knowledge" about sensitive groups can be *false*, and an LLM will state it fluently — the real Gemini response on AIM ε = 3 told the reader that women out-earn men. Presenting such an artefact as insight could reinforce stereotypes or misdirect policy. Mitigations implemented here:

- hypothesis framing in the prompt;
- quality metrics included in the payload;
- an offline knowledge-utility check.

Further mitigations are recommended:

- reviewing any claim about protected attributes against governed real-data statistics before acting on it;
- withholding protected-attribute associations from the LLM payload unless they are needed.

## Human Oversight and Disclosure

Three oversight points are built into the design. A person chooses the dataset and reads the guarantee before generating. A person sees the exact payload before it is sent. And every output is framed as hypotheses that the reviewer's workflow (Section XI) checks against the payload and, for decisions, against governed real data. The case study shows why the last point matters: without it, a confidently written but false statement about women's incomes would have passed into the analysis.

Disclosure applies to the authors too. This report states where real LLM output appears, labels demo output, and acknowledges that an AI assistant was used to help build, verify and draft the work.

## Autonomy, Dignity and Consent

Synthetic data are sometimes presented as removing ethical concerns because "no real person is in the data". That framing is misleading. Synthetic records are derived from real people's information, and the patterns they carry — including patterns about protected groups — are those people's collective information. Data subjects may reasonably object to uses of the derived data that they would object to for the real data, such as profiling a group. DP protects individuals against singling out; it does not protect groups against inferences about the group. Purpose limitation therefore remains an ethical requirement for synthetic releases, not only a legal one.

## Dual Use and Misuse

The same pipeline that lets a hospital share data responsibly could be used to *launder* data — to claim that a release is "synthetic, therefore anonymous" when it was produced without DP, or with an ε so large that the guarantee is vacuous. The framework's insistence on labelling the guarantee, including for the non-DP baselines, is a safeguard against this. Its willingness to show results at ε = 10 is a reminder that a DP label alone is not sufficient: the ε must be justified.

## Environmental and Resource Cost

Generation is cheap for PrivBayes and MST, but AIM's adaptive fitting and the deep generators consume meaningful compute. LLM calls add energy and monetary cost per request. A responsible deployment would prefer the cheapest mechanism that meets the trust thresholds, and would cache explanations per release instead of regenerating them on every visit.

## Bias Mitigation and User Trust

No bias mitigation (re-weighting, fairness constraints) is applied to the generators; this is future work. User trust should be *calibrated*, not maximised. The trust vector of Section XI and the hypothesis framing aim at users who neither over-trust nor dismiss the outputs. Fig. {fig:lifecycle2} places these controls in a lifecycle view.

![{fig:lifecycle2} Trustworthy privacy-preserving generative AI lifecycle (conceptual; plan, validation, explanation and release stages are partly implemented, monitoring is not).](figures/diagrams/fig14_trustworthy_lifecycle.png){width=6.3in}

# Application Scenarios and Case Study Evaluation

## Case Study: Census Income Analysis

The implemented case study is census-style income analysis. A statistical office or a social-policy unit wants to share a household-income table with researchers and to let analysts ask "which groups have high-income rates, and how reliable is that?".

With AIM or PrivBayes at ε = 3–5, the evidence suggests three things:

- classifiers trained on the release retain about 79–85% of real-data F1;
- the subgroup rate rankings agree moderately to well with the real data (Spearman ρ 0.51–0.87, rising with ε);
- the simple attack finds no membership signal.

With MST, the same release would look good on marginals but would mislead on subgroup rankings. With TVAE, utility would be similar, but the release would carry no guarantee and would contain exact copies of records. The LLM layer turns the selected release into a structured narrative with explicit limitations.

## Case-Study Evaluation

The case study can be evaluated against the requirements of Section IV and the evidence of Section XIV.

- **Privacy requirements (PR1–PR5)** are met for the release and the payload: the guarantee is stated per dataset, non-DP data are excluded, no row reaches the provider, small cells are suppressed, and the manifest discloses that the quality context is not DP.
- **Utility for the stated question.** The question "which groups have high-income rates?" is answered correctly by a PrivBayes ε = 3 release — the real gender gap (10.3% vs 30.7%) appears as 11.5% vs 31.6% — and incorrectly by the AIM ε = 3 and MST ε = 3 releases, which reverse or erase it.
- **Explanation quality.** The live Gemini explanation of the PrivBayes release was faithful and correct on the checked claims and flagged one artefact itself. The explanation of the AIM release repeated the reversed gap.
- **Residual issues.** The chosen PrivBayes release (seed 42) still weakens one structural association: relationship ↔ sex falls from 0.65 to 0.37, and `12th` grade has an implausible 67.4% high-income rate.

A defensible choice for this case would therefore be PrivBayes at ε = 3 — pure DP, five seconds to fit, 82% utility retention — released with a transparency report that lists these two known artefacts. The evaluation also shows that the choice cannot be made from utility alone. AIM and PrivBayes have almost identical retention at ε = 3, yet only one of them preserves the subgroup pattern the analysts care about.

## Domain Scenarios (Proposed)

The scenarios below are *proposed* applications. They were not evaluated in this study. Fig. {fig:deploy} sketches a generic deployment.

- **Healthcare analytics.** A hospital releases DP synthetic admission records to a research consortium, and clinicians use the LLM layer to explore readmission patterns. HIPAA Expert Determination and ethics approval apply. Rare diagnoses are exactly the patterns most at risk (Section XIV), so per-subgroup validation is essential.
- **Financial intelligence.** A bank shares DP synthetic transaction summaries with fraud-analytics vendors. Rare fraud patterns may be lost, so DP synthetic data suit exploratory and model-development work better than final model training.
- **Scientific research and education.** Courses and hackathons use DP synthetic versions of sensitive survey data, with the LLM layer as a teaching aid that explains statistics.
- **Legal and public-sector systems.** Agencies publish DP synthetic microdata alongside official statistics, as the U.S. Census Bureau has done for tabulations [@abowd2018].
- **Enterprise AI.** Internal teams prototype dashboards and models on synthetic HR or customer data before requesting governed access to the real data.

## Walk-Through: Healthcare Deployment (Proposed)

Consider a hospital that wants to let an external research partner study 30-day readmissions, and wants its own quality team to explore drivers of readmission without data-access delays. Following Fig. {fig:deploy}, the steps would be:

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

![{fig:deploy} Proposed domain-specific deployment architecture. Dashed components (budget ledger, release review, provider controls, DP domain discovery) are not implemented.](figures/diagrams/fig13_domain_deployment_architecture.png){width=6.3in}

# Business Impact Assessment

## Value Drivers

The business case for privacy-preserving generative AI rests on three drivers.

**Risk reduction.** A dataset that can be shared without exposing individuals reduces the expected cost of a breach or misuse. That cost includes regulatory penalties, remediation, notification and reputational damage. DP gives a *quantified* version of this argument: the stated ε bounds how much any one person's data could influence what an attacker sees. A quantified bound is easier to defend to a regulator than an assertion that data were "anonymised".

**Time-to-insight.** Access to sensitive data typically requires approvals, agreements and secure environments that take weeks or months. If synthetic data are good enough for exploration and prototyping — the evidence here says about 79–85% of real-data model performance at ε = 3–5 — analysts can start immediately and reserve governed access for confirmation. The LLM layer extends this to non-specialist users.

**Collaboration.** Partners such as universities, vendors and other departments can work on a synthetic release under a lighter agreement, increasing the number of people who can contribute to a problem.

## Costs and Risks

The costs are modest but real:

- engineering effort to operate the pipeline and the budget ledger;
- compute — negligible for PrivBayes, tens of minutes per release for full-strength AIM;
- LLM API usage;
- above all, governance effort for assessments and approvals.

The main business *risk* is decision risk. Insights drawn from synthetic data can be wrong, as the spurious association in Section XIV shows. If such insights drive pricing, credit or clinical decisions without confirmation, the organisation trades a privacy risk for a quality and fairness risk.

## Operational Cost of the Implemented Components

Some costs were measured directly. A synthetic release takes seconds (PrivBayes, mean 0.5–21 s), under a minute (MST) or up to ten minutes (AIM, capped) to fit on this 2,400-row table. One LLM explanation used about 6,300 input and 1,700–1,900 output tokens, plus 1,200–4,000 internal "thinking" tokens, and took 25–50 s in the recorded calls (one call took 215 s under load). Prices are not quoted, because provider pricing changes and was not part of the evaluation. The verification tooling also has a measurable operational benefit: it found a duplicate-counting defect in the original dashboard (43 runs shown instead of 41) that would otherwise have reached the report.

## Adoption Roadmap and KPIs

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

## Assessment

The study did not measure costs or returns in an organisation. Table {tab:business} therefore separates impacts *supported by this study's evidence* from those that are *plausible but unmeasured*. Any return-on-investment figure would have to come from the adopting organisation's own data.

Table: {tab:business} Business impact assessment

| Impact area | Expected benefit | Evidence from this study | Status |
|---|---|---|---|
| Risk reduction | Lower re-identification and breach impact of shared data | Formal ε for DP runs; no exact copies from DP methods vs 3 from TVAE | Supported (within assumptions) |
| Analytical value retained | Models and insights from shared data | 79–85% F1 retention for AIM/PrivBayes at ε = 3–5 | Supported (one dataset) |
| Faster data access | Analysts start on synthetic data without lengthy approvals | Not measured | Plausible |
| Compute cost | Generation cost per release | 0.5–21 s (PrivBayes) to 626 s (AIM) per fit on a student machine | Supported (hardware not recorded) |
| Insight democratisation | Non-experts get narratives via the LLM | Implemented; real LLM output not evaluated | Partly supported |
| Decision risk | Wrong decisions from spurious synthetic "insights" | Spurious association (V 0.45–0.63 vs 0.12 real); MST ρ ≤ 0.30 | Risk evidenced — needs controls |
| Compliance readiness | Easier DPIA and anonymisation arguments | Assumptions documented; organisational controls missing | Partial |
| Trust and reputation | Demonstrable privacy engineering | Audit trail, verified results | Plausible |
| API cost of LLM layer | — | About 15k characters per request, roughly 4–5k input tokens (estimate) | Estimate only — check current pricing |
