# Demonstration guide (academic review, about 10 minutes)

## Before the review

1. `run_dashboard.bat` → <http://localhost:8501>. If live mode will be shown, first put `ANTHROPIC_API_KEY` in `.env`.
2. Optional: `venv\Scripts\python -m pytest -m "not slow"` in a second terminal (≈15 s) to show the tests passing.
3. Make sure `git status` is clean, so the published results are what is on disk.

## Script

| Min | Show | Say |
|---|---|---|
| 0–1 | README top section | "A comparative study of 3 DP and 2 non-DP generators, plus an LLM extension that only sees aggregates of DP data." |
| 1–3 | Sidebar → **Use bundled example dataset** → Dataset → Confirm → Preprocessing → Fit | "One leakage-safe protocol: every parameter is fitted on the 2,400 training rows only." |
| 3–4 | Model Selection → PrivBayes, ε = 3 → Run (≈5 s) → Privacy page | "The formal guarantee is generated from code: pure ε-DP for PrivBayes, (ε, δ) for AIM/MST, none for CTGAN/TVAE." |
| 4–6 | Model Comparison | "41 unique runs from 43 log records — we found and fixed a double-counting bug. No arbitrary overall score." |
| 6–9 | Workspace → **LLM Knowledge Discovery** → AIM ε = 3 → expand *Exact payload* → Generate | "The original data are never read; groups under 20 rows are suppressed; demo mode is clearly not LLM output. Note the education ↔ race association — our knowledge-utility check shows it is a synthetic artefact (0.49 vs 0.12 in real data)." |
| 9–10 | `results/verified/verification_report.json` | "733/738 logged metrics re-computed exactly from the saved data." |

**Afterwards:** a run triggered from the UI appends to the log and overwrites that
run's CSV. Restore the published results with `git checkout -- results/`.

## Likely questions

- **Is the LLM differentially private?** No. Its *input* is post-processing of a DP release, so it leaks no more than the release does, provided the DP guarantee and its assumptions hold. The LLM adds no guarantee of its own.
- **Why is MIA AUC 0.5 even for CTGAN/TVAE?** The 1-NN attack is weak, and the member and non-member sets share 18 records. It is not evidence that the non-DP models are private. TVAE copied training rows.
- **Why one AIM seed?** Runtime: AIM is the slowest method even with its rounds capped at 60. This is disclosed and listed as future work.
- **Has live mode been tested?** Through the real SDK against a mock server, yes. Against the real API, no, because no key was available.
