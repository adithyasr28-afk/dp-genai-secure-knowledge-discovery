# Handover: status, open items and next steps

## What is finished and verified by execution

- Fresh environment rebuilt from `requirements.txt` + `constraints.txt` (original package versions).
- **32/32 tests pass** — 27 fast + 5 slow end-to-end generator runs — on Windows 11, Python 3.11.
- **Results verified:**
  - 43 log records → 41 unique runs;
  - all privacy configurations correct;
  - **733/738** logged metrics recomputed exactly; the other 5 differ by ≤ 2.8 × 10⁻⁶.
- **Dashboard tested manually:** all original pages plus the LLM page (demo mode and missing-key path). Two bugs were found and fixed.
- **LLM extension:** live mode tested through the real `anthropic` SDK against a local mock server (request shape, headers, HTTP errors).
- Report draft built (DOCX opens in Word; PDF export checked visually), with the diagram folder, change log and checklist.

## What is NOT done or NOT verified

| Item | Why | Who / how |
|---|---|---|
| Live Claude API call | No API key (a Claude Pro subscription has no API credits) | Create a key at console.anthropic.com, put it in `.env`, run the LLM page in Live mode, and add one real, labelled response to report Appendix D. |
| Similarity check (≤ 10%) | Needs the authorised tool | After the team rewrites the text. |
| Student names, author list, e-mails, contribution allocation, page numbers | Team decisions | Edit the DOCX front matter; Word *References → Update Table* is not used here, so fill page numbers manually. |
| Two-column body layout | Kept single-column for editing | Layout → Columns → Two after the final edits; add section breaks for wide figures and tables. |
| Execution videos | Must be recorded by the team | Follow `docs/DEMO_GUIDE.md`. |
| Full-resolution screenshots | The in-app browser pane was hidden, so captures are cropped | Retake from a normal browser at `http://localhost:8501`. |
| 5 references flagged [VERIFY]; journal share ≈ 21% (guideline 80%) | DOI/pages not confirmable; most key works are conference papers | Check in IEEE Xplore / ACM DL; substitute journal versions where they exist. |
| Re-running the experiments | Not required; DP generators are unseeded, so a re-run would change the data | Only if the instructor asks. Then also forward seeds and remove the AIM cap (see report §XXI). |

## Questions to confirm with the instructor

1. **Abstract length:** template 150–250 words vs section plan 450–750 ("Executive Summary and Abstract"). The draft provides both.
2. **Reference count and mix:** 62 cited (guideline 30–50; 80% journals). Trim, or accept?
3. **Figure and table counts:** 29 / 19 against suggested 10–15 / 8–12. Move results figures to the appendix?
4. **Two-column layout:** required for the submitted draft, or only for the final version?
5. Is a 3,000-row public census sample acceptable as the "sensitive" dataset, or is a second (e.g. healthcare) dataset expected?

## Publishing to GitHub (done 2026-10-11)

Published as a **public** repository: https://github.com/adithyasr28-afk/dp-genai-secure-knowledge-discovery . The steps below are kept for reference, e.g. for re-publishing elsewhere.

The repository is fully committed locally at
`C:\Users\adith\Desktop\Data Privacy Proj\dp-genai-secure-knowledge-discovery`.
To publish to <https://github.com/adithyasr28-afk>:

1. Create an **empty** repository named `dp-genai-secure-knowledge-discovery` on GitHub (no README, licence or .gitignore). Choose public or private; for private, invite the instructor as a collaborator.
2. Then run:

```bat
cd "C:\Users\adith\Desktop\Data Privacy Proj\dp-genai-secure-knowledge-discovery"
git remote add origin https://github.com/adithyasr28-afk/dp-genai-secure-knowledge-discovery.git
git push -u origin main
```

Git Credential Manager will open a browser window for sign-in on the first push.

3. Insert the repository URL in report §"Data Availability Statement" (`report/src/09_limitations_future_conclusion.md`) and rebuild with `venv\Scripts\python report\build_report.py`.

## Rebuilding everything

```bat
venv\Scripts\python -m analysis.verify_results
venv\Scripts\python -m analysis.knowledge_utility
venv\Scripts\python figures\diagram_builder.py
venv\Scripts\python report\build_report.py
```

The report sources are in `report/src/*.md`. Numbers come from `results/verified/` through `report/make_tables.py`, so edit the text, not the numbers. Labels such as `{fig:f1}`, `{tab:utility}`, `{eq:dp}` and `[@key]` are numbered automatically on every build.
