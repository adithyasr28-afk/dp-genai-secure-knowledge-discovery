# Changelog — report-finalisation

The baseline is `main` @ `ef727a3` (2026-10-12). Earlier history is in `report/CHANGES.md` and `git log`.

## Phase 1 — Audit (2026-10-12)
- Created branch `report-finalisation`.
- Archived the baseline report to `report/archive/v1_2026-10-12/` (DOCX, PDF, resolved Markdown).
- Added `project_docs/compliance_matrix.md`, `project_docs/baseline_audit.md`, this changelog and `PROGRESS.md`.
- No changes to code, experiment outputs or report sources.

## Phase 2 — Technical verification (2026-10-12)
- **Code:** `knowledge_discovery/summarizer.py` adds `include_quality_context` (default True), new manifest fields `quality_context_included` and `quality_context_uses_real_data`, and an accurate privacy note. `llm_client.py` demo mode works without the quality context. `streamlit_page.py` adds an "Include quality metrics" checkbox and a privacy note.
- **Tests:** new `test_quality_context_is_disclosed_and_optional`.
- **Report sources, corrections:**
  - utility retention range (N4, N18);
  - education–race and relationship–sex values (N15–N17);
  - runtime labels (N12);
  - PrivBayes score and noise description, and the public record count (D3–D5);
  - corrupted MST σ formula (D6);
  - DP-SGD noise scaling (D7);
  - LLM privacy boundary (D11).
- **README:** education–race range corrected.
- **Added:** `project_docs/claim_verification.md`.

## Phase 3 — Repository and reproducibility (2026-10-12)
- **Moved (git mv):**
  - `docs/screenshots/` → `evidence/screenshots/2026-10-11_initial/`
  - `docs/llm_evidence/` → `evidence/llm_responses/`
  - `docs/{DEMO_GUIDE,HANDOVER,GUIDELINE_CHECKLIST}.md` → `project_docs/`
  - All references updated (README, report sources, `analysis/llm_case_study.py`, docs).
- **Added:** `evidence/videos/README.md` (placeholder; videos not recorded) and `project_docs/reproduction_guide.md`.
- **README:** new repository-structure block. Application code was **not** moved into `src/`: moving it would break the imports and the original layout. The README maps the requested structure to the actual folders.
- **Verified:**
  - clean install from scratch;
  - full and fast test suites;
  - byte-identical re-run of the analysis scripts;
  - git-history secret scan (clean).
- **References:** 5 `[VERIFY]` entries resolved against Crossref and the NeurIPS proceedings; DOI added for yue2023.

## Phase 4 — Screenshots (2026-10-12)
- **Added:** `evidence/screenshots/capture_screenshots.py` (CDP-driven capture with a mode guard against accidental live calls), 14 new PNG screenshots in `evidence/screenshots/2026-10-12/`, and `evidence/screenshots/README.md`.
- **Live LLM calls:**
  - **One deliberate live Gemini call** for screenshot 10d (PrivBayes ε=3 s42, 2026-10-12 20:47:34).
  - **Two unintended live calls** (AIM ε=3 s42, 20:39:01 and 20:42:25), caused by the capture script clicking Generate in the default Live mode. They are disclosed, their texts are kept in `evidence/llm_responses/`, and the script was fixed.
- **UI demo run** (PrivBayes ε=3 seed 7): the log record and CSV it created were removed; the log is back to 43 records.

## Phase 5 — Report revision (2026-10-12)
- **Build (`report/build_report.py`):**
  - official front matter for 3 members (4th SmartArt slot and 4th contribution row removed), faculty and corresponding author from the template;
  - continuous two-column body with page-wide sections for wide figures and tables;
  - A4 with 0.5 in top/bottom margins;
  - output `report/final_report.docx`;
  - diagram export to `diagrams/` with an index.
- **Sources:**
  - drafting notes removed (moved to `project_docs/review_notes_baseline_draft.md`);
  - figures 25 → 15 and tables 20 → 12 in the body; the rest in the new Appendix D, and screenshots replaced (Appendix E);
  - appendices moved before the DAS, Acknowledgment and References (template order);
  - every section expanded or trimmed into the topic plan's word range with verified, project-specific content;
  - keywords extended to 29 words.
- **References:** 63 → 50 (14 removed, 1 verified journal survey added); all `[VERIFY]` resolved; DPDP Rules sentence verified.
- **New analysis:** `analysis/quasi_identifier_risk.py`.

## Phase 6 — Validation (2026-10-12)
- **Added:**
  - `report/finalize.py`, which builds, exports a PDF with Word and fills the Index/LoF/LoT page numbers from it (2-pass, stable);
  - `report/check_report.py`, the automated consistency checks;
  - `project_docs/final_audit.md`; the final compliance matrix; claim-verification §§6–7.
- **Fixed during the audit:**
  - corrupted `\varepsilon`, `\approx` and a code path (escape characters);
  - Markdown asterisks in list titles;
  - table column widths and cell indents;
  - Appendix A command layout;
  - stale test counts.
- **Rewritten:** `project_docs/HANDOVER.md` and `DEMO_GUIDE.md`; `GUIDELINE_CHECKLIST.md` now points to the compliance matrix. README updated.

## Phase 7 — GitHub and delivery (2026-10-12/13)
- **Tests on the final commit:** full suite 48 passed, 1 skipped; fast suite 43 passed, 1 skipped.
- **Pushed** `report-finalisation` to `origin` (a new branch; `main` untouched at `ef727a3`). The branch head was verified with the GitHub API.
- **`Deliverables/` refreshed:**
  - `final_report.docx` and `.pdf`;
  - `Diagrams/`, `project_docs/`, `screenshots/`;
  - the updated `Project_Work_Summary.docx`;
  - `26FSDPYCPMID1028_submission.zip`: `git archive` of the branch plus the final report; no `.env`, venv, caches, audit records or template, scanned for secrets.
  - The previous draft is kept in `_previous_draft_2026-10-11/`.
