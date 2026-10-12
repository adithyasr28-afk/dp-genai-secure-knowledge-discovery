# Compliance matrix

Baseline audit: 2026-10-12, branch `report-finalisation` from `main` @ `ef727a3`.
Report baseline: `report/archive/v1_2026-10-12/` (DOCX, PDF, resolved Markdown).

**Source documents** (all in `C:\Users\adith\Desktop\Data Privacy Proj\`):

| Code | Document |
|---|---|
| **T** | `3_Consolidated_Template.docx`: course cover page, Index, List of Figures, List of Tables, Contribution tables, then the IEEE Access body template (sections 2–3 of the DOCX set to 2 columns) |
| **G** | `1_🧾 Manuscript Guidelines.pdf`: §1 Report Template, §2 Report Contents, §3 References, §4 Plagiarism, §5 Deliverables, Data availability |
| **P** | `13.pdf`: topic section plan with content focus, visuals and word counts; Recommended Figures; Recommended Tables |
| **R** | `Team ID_Title_SectionsLink_Consolidated.pdf`: course roster. Team 26FSDPYCPMID1028 lists **23BCE2114** and **23BCE2133 (PoC)**; slots 3 and 4 are empty |

**Status key:** ✅ met · ◐ partly met · ❌ not met · ⚠ conflict between guidelines · 👤 needs a human.

The **Final** column is filled in at Phase 6.

Word counts exclude tables, captions and equations. They were counted by `report/build_report.py:section_word_counts` on the baseline. Targets are from **P**.

## A. Front matter and author details

| # | Requirement | Source | Current status | Evidence | Required change | Priority | Final |
|---|---|---|---|---|---|---|---|
| A1 | Cover page: "Case-Study Report On <Title>", BCSE318L Data Privacy, "by" (members), "To" (faculty), School, month/year | T (cover) | ◐ Title, course and Team ID filled. Member names are placeholders. Faculty shows "[Faculty name — to confirm]" | `build_report.py` `FRONT` | Faculty = **Dr M Rajasekhara Babu** (given in the brief and the template). Use reg. nos. 23BCE2114, 23BCE2133 and a clearly marked third-member placeholder | High | |
| A2 | Author line: faculty first, then students with superscripts; affiliation; e-mails; corresponding author | T (title block) | ◐ Placeholders "[Author 1]…" | built DOCX | Faculty plus 3 student slots. **Delete the 4th and 5th template slots.** Names and e-mails stay marked placeholders | High | |
| A3 | Index table with page numbers | T | ◐ Rows filled; page numbers blank | built DOCX | Fill page numbers from the final PDF pagination | Med | |
| A4 | List of Figures and List of Tables with page numbers | T | ◐ Titles filled; page numbers blank | built DOCX | As A3 | Med | |
| A5 | Contribution table (section → reg. no. → words) and consolidated table for 4 students | T | ◐ Words filled; reg. nos. blank; 4 rows | built DOCX | 3 rows. Reg. no. per section is a 👤 team decision; leave blank and flag it | Med | |
| A6 | No drafting notes in the submission copy | brief §5.7 | ❌ "Draft Status and Review Notes" (555 words) plus 8 [TEAM] and 3 [CONFIRM] markers | `00_front.md` | Move them to `project_docs/`; strip them from the submission build | High | |

## B. Abstract, keywords, executive summary

| # | Requirement | Source | Current status | Evidence | Required change | Priority | Final |
|---|---|---|---|---|---|---|---|
| B1 | Abstract (IEEE style, ≈150–250 words) | T (ABSTRACT para) | ✅ 240 words | `00_front.md` | Keep within range and in line with the final findings | High | |
| B2 | "Executive Summary and Abstract" 450–750 words | P row 1 | ⚠ Conflicts with B1; resolved as a 689-word Executive Summary plus a separate 240-word Abstract | `00_front.md` | Keep the resolution and document it; 👤 confirm with the faculty | Med | |
| B3 | Keywords 20–40 words, alphabetical (T: "INDEX TERMS… alphabetical order") | P, T | ◐ 15 words, alphabetical | `00_front.md` | Extend to ≥ 20 words, still alphabetical | Low | |

## C. Sections and word counts (P)

| # | Section | Target | Baseline words | Status | Required change | Priority | Final |
|---|---|---|---|---|---|---|---|
| C1 | I. Introduction | 800–1200 | 816 | ✅ | — | Low | |
| C2 | II. Problem Statement | 400–700 | 376 | ❌ short | +≥ 30, project-specific | Med | |
| C3 | III. Background and Literature Review | 1500–2500 | 1339 | ❌ short | +≥ 170 (taxonomy and comparison discussion) | Med | |
| C4 | IV. Requirements Analysis | 600–1000 | 581 | ❌ short | +≥ 20 | Med | |
| C5 | V. Data Lifecycle and Privacy Classification | 800–1200 | 665 | ❌ short | +≥ 140 | Med | |
| C6 | VI. Threat Model and Privacy Risk Assessment | 1000–1500 | 678 | ❌ short | +≥ 330 | Med | |
| C7 | VII. Proposed DP-Enhanced GenAI Framework | 1200–1800 | 925 | ❌ short | +≥ 280 | Med | |
| C8 | VIII. Privacy-Aware Data Preparation | 1000–1500 | 639 | ❌ short | +≥ 370 | Med | |
| C9 | IX. DP Integration Layer | 1200–1800 | 981 | ❌ short | +≥ 220 | Med | |
| C10 | X. GenAI Knowledge Discovery Layer | 1200–1800 | 1314 | ✅ | — | Low | |
| C11 | XI. Explainability, Transparency and Trust | 1000–1500 | 699 | ❌ short | +≥ 310 | Med | |
| C12 | XII. Experimental Setup | 700–1200 | 617 | ❌ short | +≥ 90 | Med | |
| C13 | XIII. Evaluation Metrics | 500–800 | 454 | ❌ short | +≥ 50 | Med | |
| C14 | XIV. Results and Findings | 1200–2000 | 1986 | ✅ at the cap | Do not grow it | Low | |
| C15 | XV. Comparative Analysis | 800–1200 | 763 | ❌ short | +≥ 40 | Med | |
| C16 | XVI. Compliance, Governance, Regulatory | 800–1200 | 689 | ❌ short | +≥ 120 | Med | |
| C17 | XVII. Ethical and Trustworthy AI | 700–1000 | 553 | ❌ short | +≥ 150 | Med | |
| C18 | XVIII. Application Scenarios and Case Study | 800–1500 | 597 | ❌ short | +≥ 210 | Med | |
| C19 | XIX. Business Impact | 500–1000 | 399 | ❌ short | +≥ 110 | Med | |
| C20 | XX. Challenges and Limitations | 600–1000 | 467 | ❌ short | +≥ 140 | Med | |
| C21 | XXI. Future Research Directions | 600–1200 | 443 | ❌ short | +≥ 160 | Med | |
| C22 | XXII. Conclusion | 500–800 | 442 | ❌ short | +≥ 60 | Med | |
| C23 | Appendix (optional) | 500–2000 | ≈ 968 (A–F) | ✅ | Remove stale notes | Low | |
| C24 | Section numbering and titles consistent with P | G §2 | ✅ I–XXII in P's order | `report/src/` | Keep | High | |
| C25 | Content focus per P row, e.g. §IX "DP-SGD", §X "retrieval augmentation" | P | ◐ Covered as discussion or proposed work, honestly labelled as not implemented | §IX, §X | Keep the honest labelling; never present these as implemented | High | |

## D. Figures, tables, equations (G §2, T, P)

| # | Requirement | Source | Current status | Evidence | Required change | Priority | Final |
|---|---|---|---|---|---|---|---|
| D1 | 10–15 recommended figures (list of 15 in P) | P | ⚠ 30 figures (25 body, 5 appendix); all 15 recommended topics present (DP-SGD drawn as "not implemented") | `Report_Draft_full.md` | Reduce body figures to about 15; move result plots and screenshots to appendices | Med | |
| D2 | 8–12 recommended tables (list of 10 in P) | P | ⚠ 20 tables | same | Move verification, duplicate, test and failure-mode tables to appendices; body ≤ 12 | Med | |
| D3 | Diagrams ≥ 600 DPI, redrawn in draw.io | G §2 | ◐ Generated at 600 DPI (PNG + SVG) with editable `.drawio`; drawn by `diagram_builder.py` (matplotlib), not by hand in draw.io | `figures/diagrams/` | Document honestly; 👤 the team may restyle in draw.io | Med | |
| D4 | Separate diagram folder named "Fig NN <Name>" | G §2 | ◐ `report/Diagrams/` (git-ignored) and `Deliverables/Diagrams/` exist; numbering will change when figures move | `Deliverables/Diagrams` | Re-export to `diagrams/` with the final numbering | Med | |
| D5 | Reused diagrams cite the source ("Adapted from [n]") | G §2 | ✅ Fig. 1 says "Redrawn… adapted from" | caption | Check every caption | Low | |
| D6 | Equations editable (Equation Editor), numbered (1) at the right, referenced as "(1)" | G §2, T §III-A | ◐ Native OMML; numbers typed to the right; references rendered "(N)" | build | Check the rendering in the final PDF | Med | |
| D7 | Fig. captions "Fig. N." below; tables in Roman numerals ("TABLE I"); "Fig." abbreviation in text | T §VI-K | ✅ | build | Keep | Low | |
| D8 | Equations named in P: privacy–utility trade-off, privacy loss function, privacy budget, knowledge utility, trust score | P | ✅ All present ({eq:dp}, {eq:loss}, composition, {eq:ku}, trust) | `report/src` | Verify in Phase 6 | Low | |

## E. References (G §3, T)

| # | Requirement | Source | Current status | Evidence | Required change | Priority | Final |
|---|---|---|---|---|---|---|---|
| E1 | 30–50 references | G §3 | ❌ 63 cited | `references.py` | Trim to ≤ 50 by removing weakly used citations; justify any kept | High | |
| E2 | 80% journals (IEEE/ACM/Springer/Elsevier), 20% other | G §3 | ❌ ≈ 13 journal (≈ 21%) | `references.py` | Swap in verified journal versions where they exist; document the remaining deviation (the DP-synthesis literature is conference-heavy) | High | |
| E3 | Sources from 2020–2025 prioritised | G §2, §3 | ◐ Most 2020–2025, plus foundational works | `references.py` | Keep the foundational works that are essential | Low | |
| E4 | IEEE citation format, single [1], multiple [1][3][5] | G §3, T | ✅ The build renders separate brackets | `build_report.py` | — | Low | |
| E5 | Reference list in IEEE format | T | ✅ | `references.py` | — | Low | |
| E6 | No unverified details; every [VERIFY] resolved | brief | ❌ 5 [VERIFY] (greshake2023, jagielski2020, lukas2023, ponomareva2023, yue2023) | `references.py` | Verify online or replace/remove | High | |
| E7 | Summarise in your own words | G §3 | 👤 Text is the drafter's own wording; the team must rewrite and check it | — | 👤 | High | |

## F. Layout (T)

| # | Requirement | Source | Current status | Evidence | Required change | Priority | Final |
|---|---|---|---|---|---|---|---|
| F1 | Two-column body (template DOCX sections 2–3 `w:cols num=2`) | T | ❌ Single-column body | built DOCX | Two-column body section; figures and tables one column wide (3.5 in) or page wide where needed | High | |
| F2 | A4, margins as in the template (1.0 in left/right, 0.5 in top/bottom) | T | ◐ Bottom margin 0.7 in | `build_report.py` | Match the template (bottom 0.5 in) | Low | |
| F3 | Fonts and headings as in the template (IEEE Access styles) | G §1, T | ✅ Styles copied from the template | `reference.docx` | Check visually | Low | |

## G. Data availability, deliverables, similarity

| # | Requirement | Source | Current status | Evidence | Required change | Priority | Final |
|---|---|---|---|---|---|---|---|
| G1 | Data Availability Statement in one of the prescribed forms, with persistent link | G (Data availability) | ✅ Present, with the GitHub URL and UCI source | `09_…md` | Check the wording matches a prescribed form | Med | |
| G2 | Complete manuscript (.doc format) | G §5 | ✅ DOCX | Deliverables | `report/final_report.docx` | High | |
| G3 | Diagram folder | G §5 | ✅ | `Deliverables/Diagrams` | `diagrams/` refreshed | Med | |
| G4 | Source code (preferably on GitHub, with link) | G §5 | ✅ Public repo | GitHub | Push the `report-finalisation` branch | High | |
| G5 | Datasets folder | G §5 | ✅ `data/`, `results/synthetic_data/` | repo | — | Low | |
| G6 | Execution videos folder | G §5 | ❌ none | — | Create `evidence/videos/README.md` placeholder; 👤 record later (per the brief) | Med | |
| G7 | Similarity ≤ 10% | G §4 | ❌ Not checked (no authorised tool available) | — | 👤 Run the authorised checker after the team rewrite; never claim a percentage | High | |
| G8 | Same Data Availability Statement for the submission system | G | 👤 | — | Team pastes it into the submission system | Low | |

## H. Appendices and reproducibility evidence

| # | Requirement | Source | Current status | Evidence | Required change | Priority | Final |
|---|---|---|---|---|---|---|---|
| H1 | Appendix: privacy configurations, algorithms, benchmark settings, derivations, prompt templates, supplementary results | P (Appendix row) | ✅ A (config), B (verification), C (prompt), D (screenshots), E (supplementary), F (reference status) | `10_…md` | Drop F from the submission copy (move to project_docs); add the AIM budget derivation reference | Med | |
| H2 | Genuine screenshots of the running application | brief Phase 4 | ◐ 5 screenshots, some cropped (pane hidden) | `docs/screenshots/` | Recapture all 10 feature screens at full resolution into `evidence/screenshots/` | High | |
| H3 | Reproduction guide | brief Phase 3 | ◐ README and report App. A | README | `project_docs/reproduction_guide.md` | High | |
