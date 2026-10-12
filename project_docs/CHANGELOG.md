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
