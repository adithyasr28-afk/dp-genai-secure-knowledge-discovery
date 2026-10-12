# Demonstration guide (academic review, about 10 minutes)

## Before the review

1. `run_dashboard.bat` → <http://localhost:8501>. If live mode will be shown, first put `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY`) in `.env`. A live Gemini call takes about 30 s; if the network is unreliable, show the saved outputs in `evidence/llm_responses/` instead.
2. Optional: `venv\Scripts\python -m pytest -m "not slow"` in a second terminal (≈30 s; 43 passed, 1 skipped) to show the tests passing.
3. Make sure `git status` is clean, so the published results are what is on disk.
4. **The LLM page opens in Live mode whenever a key is configured.** Select *Demo* before pressing *Generate* unless you intend a real (billable) call. During screenshot capture, two calls were made by accident this way.

## Script

| Min | Show | Say |
|---|---|---|
| 0–1 | README top section | "A comparative study of 3 DP and 2 non-DP generators, plus an LLM extension that only sees aggregates of DP data." |
| 1–3 | Sidebar → **Use bundled example dataset** → Dataset → Confirm → Preprocessing → Fit | "One leakage-safe protocol: every parameter is fitted on the 2,400 training rows only." |
| 3–4 | Model Selection → PrivBayes, ε = 3, **seed 7** (not a sweep seed, so no published CSV is overwritten) → Run (≈5 s) → Privacy page | "The formal guarantee is generated from code: pure ε-DP for PrivBayes, (ε, δ) for AIM/MST, none for CTGAN/TVAE." |
| 4–6 | Model Comparison | "41 unique runs from 43 log records — we found and fixed a double-counting bug. No arbitrary overall score." |
| 6–9 | Workspace → **LLM Knowledge Discovery** → AIM ε = 3 → expand *Exact payload* → Generate | "The original data are never read; groups under 20 rows are suppressed; demo mode is clearly not LLM output. The *Include quality metrics* box is the one input computed against the real data, and it can be switched off. Note the education ↔ race association — our knowledge-utility check shows it is a synthetic artefact (0.49 vs 0.12 in real data)." |
| — | Optional: provider **Gemini**, mode **Live** → Generate (≈30 s) | "This is real LLM output. On AIM ε=3 it says women out-earn men — true of the synthetic data, false in reality (10% vs 31%). PrivBayes kept the real gap, and the LLM reported it correctly. The LLM explains the data it is given; it cannot detect a distortion it never sees." |
| 9–10 | `results/verified/verification_report.json` | "733/738 logged metrics re-computed exactly from the saved data." |

**Afterwards (always):** a run triggered from the UI appends a record to the log and writes (or overwrites) that run's CSV. Restore the published results with `git checkout -- results/` and delete any new CSV, for example `del results\synthetic_data\*seed7*`.

## Likely questions

- **Is the LLM differentially private?** No. The LLM adds no guarantee of its own. Its input is post-processing of a DP release — so it leaks no more than the release, provided the guarantee and its assumptions hold — **except** for the seven quality metrics, which were computed against the real data. The manifest discloses them and the checkbox removes them.
- **Why is MIA AUC 0.5 even for CTGAN/TVAE?** The 1-NN attack is weak, and the member and non-member sets share 18 records. It is not evidence that the non-DP models are private. TVAE copied training rows.
- **Why one AIM seed?** Runtime: AIM is the slowest method even with its rounds capped at 60. This is disclosed and listed as future work.
- **Has live mode been tested?** Yes for Gemini: five real calls (2026-10-11/12), all in `evidence/llm_responses/`; the two analysed ones are fact-checked in `results/verified/llm_case_study.csv`. Claude only against a mock server (no Anthropic key).
- **Can the LLM be trusted?** Not on its own. It was faithful to the payload on 9 of 10 checked claims but repeated AIM's reversed gender gap as a finding. Treat its output as hypotheses.
