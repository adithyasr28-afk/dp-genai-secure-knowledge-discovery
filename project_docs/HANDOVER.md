# Handover: status, open items and next steps (2026-10-12)

## Finished and verified by execution

- **Environment:** a fresh clone installs from `requirements.txt` + `constraints.txt` on Python 3.11 (`pip check` clean).
- **Tests:** the full suite gives 48 passed, 1 skipped (the opt-in live LLM test), 0 failed. The fast suite gives 43 passed, 1 skipped.
- **Results:**
  - 43 log records → 41 unique runs;
  - all privacy configurations correct;
  - 733/738 logged metrics recomputed exactly; the other 5 differ by ≤ 2.8 × 10⁻⁶;
  - the analysis scripts reproduce all published tables and figures byte for byte.
- **Dashboard:** all ten feature areas exercised, with 14 genuine screenshots in `evidence/screenshots/2026-10-12/`.
- **LLM extension:**
  - Gemini (`google-genai`) and Claude (`anthropic`) providers, both tested on a mock server;
  - five real Gemini calls succeeded (two fact-checked, Table IX of the report);
  - **Claude has not been called live** (no Anthropic key);
  - the payload's real-data quality metrics are now disclosed in the manifest and can be switched off.
- **Report:** `report/final_report.docx` and `.pdf`, 67 pages.
  - Template front matter and a two-column body.
  - Page numbers in the Index, List of Figures and List of Tables.
  - 15 body figures and 12 body tables, with the rest in the appendices.
  - 50 references.
  - Every section within the topic plan's word range.
  - Automated checks pass (`python report/check_report.py`).

## Needs a person (see `final_audit.md` §4 for details)

| Item | Why it is open | How |
|---|---|---|
| Student VIT e-mails | Not supplied yet (names and reg. nos. added 2026-10-13) | Edit `FRONT["emails"]` in `report/build_report.py`, then run `python report/finalize.py` |
| Contribution allocation (reg. no. per section; words per student) | Team decision | Same file, or edit the DOCX tables |
| Similarity check (≤ 10%) | Needs the authorised tool | Rewrite in your own words, then run the checker. No percentage has been measured |
| ~~Execution videos~~ | **Done** 2026-10-16: `evidence/videos/execution_demo_2026-10-16.mp4` | — |
| **Rotate the Gemini API key** | The key was pasted into a chat on 2026-10-11 | Create a new key in Google AI Studio, delete the old one, update `.env`. Never commit it |
| Faculty confirmation | Guideline conflicts | Abstract (≈ 240 words) vs "Executive Summary and Abstract" (450–750): both are provided. 80% journal references: 28% achieved |
| Persistent data link (optional) | A GitHub URL is not a DOI | Archive a release on Zenodo and cite its DOI in the Data Availability Statement |
| Claude live test (optional) | No Anthropic key | Put `ANTHROPIC_API_KEY` in `.env` and select Claude on the LLM page |

## Rebuilding everything

```bat
venv\Scripts\python -m analysis.verify_results
venv\Scripts\python -m analysis.knowledge_utility
venv\Scripts\python -m analysis.llm_case_study
venv\Scripts\python -m analysis.quasi_identifier_risk
venv\Scripts\python figures\diagram_builder.py
venv\Scripts\python report\finalize.py
venv\Scripts\python report\check_report.py
```

The report sources are in `report/src/*.md`. Numbers come from `results/verified/` through `report/make_tables.py`, so edit the text, not the numbers. Labels such as `{fig:f1}`, `{tab:utility}`, `{eq:dp}` and `[@key]` are numbered automatically.

**Warning for anyone scripting edits.** Python and shell string escapes silently corrupt LaTeX: `\v`, `\f`, `\a`, `\r`, `\t` and `\b` become control characters, so `\varepsilon` turns into a vertical tab plus "arepsilon". `check_report.py` now fails on any control character in `report/src`.
