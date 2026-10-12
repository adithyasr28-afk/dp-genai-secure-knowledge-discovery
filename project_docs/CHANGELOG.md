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
