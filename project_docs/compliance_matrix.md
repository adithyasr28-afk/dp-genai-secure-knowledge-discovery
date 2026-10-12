# Compliance matrix

- **Baseline audit:** 2026-10-12, branch `report-finalisation` from `main` @ `ef727a3`.
- **Final verification:** 2026-10-12, on `report/final_report.docx` / `.pdf` (67 pages), checked with `report/check_report.py` and by viewing every page.
- **Baseline report:** `report/archive/v1_2026-10-12/`.

**Source documents** (all in `C:\Users\adith\Desktop\Data Privacy Proj\`):

| Code | Document |
|---|---|
| **T** | `3_Consolidated_Template.docx`: course cover page, Index, List of Figures, List of Tables, Contribution tables, then the IEEE Access body template (body sections set to 2 columns, continuous) |
| **G** | `1_🧾 Manuscript Guidelines.pdf`: §1 Report Template, §2 Report Contents, §3 References, §4 Plagiarism, §5 Deliverables, Data availability |
| **P** | `13.pdf`: topic section plan (content focus, visuals, word counts), Recommended Figures, Recommended Tables |
| **R** | `Team ID_Title_SectionsLink_Consolidated.pdf`: course roster. Team 26FSDPYCPMID1028 lists **23BCE2114** and **23BCE2133 (PoC)**; slots 3 and 4 are empty |

**Status key:** ✅ met · ◐ partly met · ❌ not met · ⚠ conflict between guidelines · 👤 needs a human.

Word counts exclude tables, captions and equations. They are counted by `report/build_report.py:section_word_counts`.

## A. Front matter and author details

| # | Requirement | Source | Baseline | Change made | Final |
|---|---|---|---|---|---|
| A1 | Cover: "Case-Study Report On <Title>", course, "by" members, "To" faculty, School, month | T | ◐ placeholders | Title, course, Team ID and October 2026 filled. Faculty **Dr M Rajasekhara Babu** (already in the template SmartArt). Members 23BCE2114, 23BCE2133, and a placeholder for the 3rd reg. no.; names are placeholders | ◐ 👤 names and 3rd reg. no. |
| A2 | Author line (faculty first), affiliation, e-mails, corresponding author | T | ◐ placeholders | "Dr. M Rajasekhara Babu¹, [Student name]² (23BCE2114), [Student name]³ (23BCE2133), [Student name]⁴ ([Reg. No. of 3rd member])"; faculty e-mail and corresponding author from the template | ◐ 👤 names, e-mails |
| A2b | Only as many author slots as team members | brief | ❌ 4 student slots | **4th student slot removed** from the cover SmartArt (data model and cached drawing) and the consolidated contribution table. The author line has faculty + 3 | ✅ |
| A3 | Index with page numbers | T | ◐ blank | Filled automatically from the PDF (`report/finalize.py`; physical pages, cover = 1) | ✅ |
| A4 | List of Figures / Tables with page numbers | T | ◐ blank | Same | ✅ |
| A5 | Contribution tables | T | ◐ | Sections and word counts filled; 3 student rows | ◐ 👤 reg. no. per section, words per student |
| A6 | No drafting notes in the submission copy | brief | ❌ | Notes moved to `project_docs/review_notes_baseline_draft.md`; 0 markers left (checked) | ✅ |

## B. Abstract, keywords, executive summary

| # | Requirement | Source | Baseline | Final |
|---|---|---|---|---|
| B1 | Abstract ≈ 150–250 words | T | ✅ 240 | ✅ 242 words, consistent with the corrected findings |
| B2 | "Executive Summary and Abstract" 450–750 words | P | ⚠ | ⚠ resolved as a 735-word Executive Summary plus the 242-word template Abstract. 👤 faculty to confirm |
| B3 | Keywords 20–40, alphabetical | P, T | ◐ 15 words | ✅ 29 words, alphabetical |

## C. Sections and word counts (P)

| # | Section | Target | Baseline | Final | Status |
|---|---|---|---|---|---|
| C1 | I. Introduction | 800–1200 | 816 | 815 | ✅ |
| C2 | II. Problem Statement | 400–700 | 376 | 463 | ✅ |
| C3 | III. Background and Literature Review | 1500–2500 | 1339 | 1607 | ✅ |
| C4 | IV. Requirements Analysis | 600–1000 | 581 | 670 | ✅ |
| C5 | V. Data Lifecycle and Privacy Classification | 800–1200 | 665 | 928 | ✅ |
| C6 | VI. Threat Model and Risk Assessment | 1000–1500 | 678 | 1059 | ✅ |
| C7 | VII. Proposed Framework | 1200–1800 | 925 | 1230 | ✅ |
| C8 | VIII. Data Preparation | 1000–1500 | 639 | 1099 | ✅ |
| C9 | IX. DP Integration Layer | 1200–1800 | 981 | 1311 | ✅ |
| C10 | X. GenAI Knowledge Discovery | 1200–1800 | 1314 | 1393 | ✅ |
| C11 | XI. Explainability and Trust | 1000–1500 | 699 | 1078 | ✅ |
| C12 | XII. Experimental Setup | 700–1200 | 617 | 747 | ✅ |
| C13 | XIII. Evaluation Metrics | 500–800 | 454 | 590 | ✅ |
| C14 | XIV. Results and Findings | 1200–2000 | 1986 | 1997 | ✅ |
| C15 | XV. Comparative Analysis | 800–1200 | 763 | 901 | ✅ |
| C16 | XVI. Compliance and Regulation | 800–1200 | 689 | 941 | ✅ |
| C17 | XVII. Ethical and Trustworthy AI | 700–1000 | 553 | 753 | ✅ |
| C18 | XVIII. Application Scenarios | 800–1500 | 597 | 843 | ✅ |
| C19 | XIX. Business Impact | 500–1000 | 399 | 525 | ✅ |
| C20 | XX. Challenges and Limitations | 600–1000 | 467 | 603 | ✅ |
| C21 | XXI. Future Research | 600–1200 | 443 | 612 | ✅ |
| C22 | XXII. Conclusion | 500–800 | 442 | 509 | ✅ |
| C23 | Appendix (optional) | 500–2000 | ≈ 968 | ≈ 990 (A–E) | ✅ |
| C24 | Numbering and titles as in P | G §2 | ✅ | I–XXII in P's order | ✅ |
| C25 | P's content focus (e.g. DP-SGD, retrieval augmentation) | P | ◐ | Covered as discussion, explicitly "not implemented" | ✅ honest coverage |

**How the gaps were closed.** All additions are project-specific and verified (`claim_verification.md` §6):
- quasi-identifier uniqueness in the real sample;
- e^ε bounds for the swept budgets;
- the attack-AUC null range;
- the attack surface by pipeline stage;
- the scope of the guarantee (unit of privacy, neighbouring relation);
- the application of the trust assessment to the real Gemini outputs and the repetition check;
- per-criterion rankings;
- the case-study evaluation;
- measured LLM cost;
- compliance evidence and transfers;
- new limitations and future work.

## D. Figures, tables, equations

| # | Requirement | Source | Baseline | Final |
|---|---|---|---|---|
| D1 | 10–15 figures (list of 15 in P) | P | ⚠ 30 (25 body) | ✅ **15 body figures = P's recommended list**. 18 supplementary figures (result plots, requirements diagram, 7 screenshots) are in Appendices D–E |
| D2 | 8–12 tables (list of 10 in P) | P | ⚠ 20 | ✅ **12 body tables** (P's 10 + privacy results + LLM fact-check). 8 in Appendices B and D |
| D3 | Diagrams ≥ 600 DPI, redrawn in draw.io | G §2 | ◐ | ◐ PNG at 600 DPI with SVG and editable `.drawio`, generated by `figures/diagram_builder.py` (not hand-drawn). Images were not upscaled. 👤 may restyle in draw.io |
| D4 | Separate diagram folder "Fig NN <Name>" | G §2 | ◐ | ✅ `diagrams/` (repo) and `Deliverables/Diagrams/`, final numbering, with `README.md` index |
| D5 | Reused diagrams cite the source | G §2 | ✅ | ✅ Fig. 1 "adapted from [23][24]" |
| D6 | Editable, numbered equations referenced as "(n)" | G §2, T | ◐ | ✅ native OMML; 15 numbered equations; no raw TeX left (checked); two corrupted formulas fixed (`\rho`, `\varepsilon`/`\approx`) |
| D7 | "Fig. N." captions; Roman-numeral tables; "Fig." in text | T | ✅ | ✅ |
| D8 | Equations named in P (privacy–utility, privacy loss, budget, knowledge utility, trust score) | P | ✅ | ✅ |

## E. References

| # | Requirement | Source | Baseline | Final |
|---|---|---|---|---|
| E1 | 30–50 references | G §3 | ❌ 63 | ✅ **50** |
| E2 | 80% journals | G §3 | ❌ ≈ 21% | ❌ **28%** (14 journal, 21 conference, 15 standards/legislation/docs/dataset/preprint). The topic plan itself requires GDPR, HIPAA, CCPA, the DPDP Act, NIST, ISO and AI regulation sources, plus dataset and SDK documentation, so ≥ 15 non-journal sources are unavoidable; the key DP-synthesis papers are conference papers. 👤 faculty to confirm |
| E3 | 2020–2025 prioritised | G | ◐ | ✅ 34 of 50 from 2020 or later; foundational DP works kept |
| E4 | IEEE citations [1], [1][3][5] | G §3 | ✅ | ✅ |
| E5 | IEEE reference format | T | ✅ | ✅ |
| E6 | No unverified details; all [VERIFY] resolved | brief | ❌ 5 | ✅ 0 markers; 17 DOIs checked on Crossref, 1 page range on NeurIPS; the rest are standard metadata (see `claim_verification.md` §7) |
| E7 | Own words | G §3 | 👤 | 👤 the team must rewrite and run the similarity check |

## F. Layout

| # | Requirement | Source | Baseline | Final |
|---|---|---|---|---|
| F1 | Two-column body | T | ❌ | ✅ continuous two-column body as in the template. Wide figures and tables (≥ 4.8 in / ≥ 4 columns) in page-wide sections. Appendices single-column (code listings) |
| F2 | A4, margins 1.0 in L/R, 0.5 in T/B | T | ◐ bottom 0.7 | ✅ |
| F3 | Template fonts and heading styles | T | ✅ | ✅ |

## G. Data availability, deliverables, similarity

| # | Requirement | Source | Baseline | Final |
|---|---|---|---|---|
| G1 | Data Availability Statement in a prescribed form | G | ✅ | ✅ form 1 ("…available in the [NAME] repository, [LINK]"). 👤 optional Zenodo DOI for persistence |
| G2 | Manuscript (.doc format) | G §5 | ✅ | ✅ `report/final_report.docx` (+ PDF review copy) |
| G3 | Diagram folder | G §5 | ✅ | ✅ `diagrams/` |
| G4 | Source code on GitHub | G §5 | ✅ | ✅ branch `report-finalisation` (see `final_audit.md` for the push status) |
| G5 | Datasets folder | G §5 | ✅ | ✅ `data/`, `results/synthetic_data/` |
| G6 | Execution videos | G §5 | ❌ | ❌ 👤 to be recorded later (placeholder `evidence/videos/README.md`) |
| G7 | Similarity ≤ 10% | G §4 | ❌ | ❌ 👤 not checked; no percentage is claimed |
| G8 | DAS also in the submission system | G | 👤 | 👤 |

## H. Appendices and reproducibility evidence

| # | Requirement | Source | Baseline | Final |
|---|---|---|---|---|
| H1 | Appendix content per P | P | ✅ | ✅ A config/commands; B verification + tests; C prompt; D supplementary tables/figures; E dashboard evidence. The reference-status appendix moved to `project_docs/` |
| H2 | Genuine screenshots | brief | ◐ 5 cropped | ✅ 14 full-resolution PNG (2,000 px) of all 10 feature areas, plus an index; 7 in Appendix E |
| H3 | Reproduction guide | brief | ◐ | ✅ `project_docs/reproduction_guide.md` (clean install tested) |
