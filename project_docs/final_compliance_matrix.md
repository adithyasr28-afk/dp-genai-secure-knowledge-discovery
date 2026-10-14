# Final compliance matrix (2026-10-14)

- **Report checked:** `report/final_report.docx` / `.pdf`, 67 pages, branch `report-finalisation`.
- **Status meanings:**
  - **Verified:** checked in the actual files during this pass.
  - **Needs correction:** a problem is still present.
  - **Pending student action:** the remaining work belongs to the students.
  - **Unable to verify:** no tool or permission was available to check it.
- **Sources:**
  - **T** = `3_Consolidated_Template.docx`
  - **G** = `1_🧾 Manuscript Guidelines.pdf`
  - **P** = `13.pdf` (section plan)

## Report structure and content

| Requirement | Source | Evidence (checked 2026-10-14) | Status |
|---|---|---|---|
| All 22 sections, numbered and titled as in P | P, G §2 | Headings I–XXII in the PDF and resolved Markdown | **Verified** |
| Section word counts within P ranges | P | Counted by `build_report.section_word_counts`. All 22 are in range: XIV at 1,993 of the 2,000 maximum; I at 815 and XXII at 509, close to their minimums | **Verified** |
| Abstract 150–250 words | T | 242 | **Verified** |
| Executive Summary + Abstract 450–750 | P | Executive Summary 735 + separate Abstract 242 (the guidelines conflict) | **Verified**; faculty to confirm the interpretation (pending student action) |
| Keywords 20–40, alphabetical | P, T | 29 words, alphabetical | **Verified** |
| Appendix 500–2,000 words (optional) | P | ≈ 990 (A–E) | **Verified** |

## References and citations

| Requirement | Source | Evidence | Status |
|---|---|---|---|
| 30–50 references | G §3 | 50 | **Verified** |
| ≈ 80% journals / 20% other | G §3 | **16 journal (32%)**, 19 conference (38%), 15 other (30%: regulations, standards, NIST, SDK documentation, dataset, one preprint). Two conference entries were replaced by verified journal sources this pass (Dwork *et al.* → *J. Privacy Confidentiality*; Census DP → *Harvard Data Sci. Rev.*) | **Needs correction (cannot be met honestly)**: P requires ≥ 14 legal/standard sources, and the primary DP-synthesis and attack papers exist only as conference papers. Documented; faculty to confirm |
| 2020–2025 emphasis | G §3 | 34 of 50 from 2020 or later | **Verified** |
| IEEE style, [1] / [1][3][5] | G §3, T | Build renders separate brackets; IEEE list format | **Verified** |
| Every citation resolves; no unused reference | — | `check_report.py`: citations 1–50, none uncited | **Verified** |
| No `[VERIFY]` markers; details checked | brief | 0 markers. 22 entries are marked as checked online (Crossref, NeurIPS or publisher pages); the other 28 are standard metadata of established works and laws, not re-checked online | **Verified** (22 entries); **unable to verify** online for the remaining standard-metadata entries |
| Citations support claims | — | Phase 5 spot checks (e.g. Tao *et al.* paper text; survey abstracts checked before use) | **Verified** for the checked claims; a full claim-by-claim audit of all 50 was not done |

## Template and layout

| Requirement | Source | Evidence | Status |
|---|---|---|---|
| Official template front matter (cover, Index, LoF, LoT, contributions) | T | Merged from the template; SmartArt has 3 member slots | **Verified** |
| Team ID, members, faculty | T | 26FSDPYCPMID1031; Amy Jose 23BCE2179, Swetha 23BCE2180, Adithya Shaji 23BCE2182; Dr M Rajasekhara Babu | **Verified** |
| Student VIT e-mails | T | `[VIT e-mail]` placeholders | **Pending student action** |
| Contribution tables (reg. no. per section, words per student) | T | `[Reg. No.]` / `[words]` placeholders; word counts per section filled | **Pending student action** |
| Index, LoF, LoT page numbers | T | Filled from the PDF; stable over two builds | **Verified** |
| Two-column body | T | 56 sections in the DOCX, continuous; body `cols=2`; wide items in one-column sections | **Verified** |
| A4, 1 in / 0.5 in margins; template fonts | T | Section properties set | **Verified** |
| Heading spacing, minor typography | T | Not redesigned | **Pending student action** (minor formatting) |

## Equations, figures, tables

| Requirement | Source | Evidence | Status |
|---|---|---|---|
| Editable equations (Equation Editor) | G §2 | 30 OMML display equations in `document.xml`; 0 raw TeX in the PDF | **Verified** |
| Numbered (1)–(15), referenced in text | G §2, T | Numbers 1–15 present, each referenced via labels. Numbers are typed text, so Word does not renumber them automatically | **Verified** (manual renumbering needed if equations are added) |
| 10–15 figures | P | 15 body figures (= P's recommended list); 18 supplementary in Appendices D–E | **Verified** |
| 8–12 tables | P | 12 body tables; 8 in appendices | **Verified** |
| Captions "Fig. N." / "TABLE N" (Roman), in order, referenced | T | `check_report.py`: in page order; no unresolved references | **Verified** |

## Diagrams

| Requirement | Source | Evidence | Status |
|---|---|---|---|
| ≥ 600 DPI | G §2 | All 26 exported PNGs carry 600 DPI and were rendered natively at that resolution (not upscaled) | **Verified** |
| Separate folder, "Fig NN <Name>" | G §2 | `diagrams/` (repo), `Deliverables/Diagrams/` | **Verified** |
| Re-drawn in draw.io | G §2 | Generated by code. Editable `.drawio` sources exist for the 16 diagrams; result charts have SVG | **Pending student action** (redraw/restyle; see `student_action_items.md`) |
| Adapted diagrams cite source | G §2 | Fig. 1 "adapted from [23][24]" | **Verified** |

## Deliverables and integrity

| Requirement | Source | Evidence | Status |
|---|---|---|---|
| Data Availability Statement in a prescribed form | G | Form 1, GitHub URL + UCI DOI; datasets are on `main` and on `report-finalisation` | **Verified** |
| Manuscript (.doc) | G §5 | `Deliverables/final report.docx` | **Verified** |
| Source code (GitHub link) | G §5 | Public repo; branch `report-finalisation` pushed | **Verified** (see the final response for the commit) |
| Datasets folder | G §5 | `data/`, `results/synthetic_data/` (41 CSVs) | **Verified** |
| Execution videos | G §5 | `evidence/videos/README.md` placeholder; no video exists | **Pending student action** |
| Similarity ≤ 10% | G §4 | No authorised checker available; no percentage claimed | **Pending student action** |
| Reproducibility instructions | brief | `project_docs/reproduction_guide.md`; clean install executed 2026-10-12; full suite re-run 2026-10-14 | **Verified** |
| Secrets excluded | brief | 0 keys in tracked files and full history; `.env` ignored; `.env.example` placeholders | **Verified**; key rotation **pending student action** |
