# Execution videos

| File | Recorded | Length | Resolution | Size |
|---|---|---|---|---|
| `execution_demo_2026-10-16.mp4` | 16 Oct 2026, by the team | 3 min 37 s (30 fps) | 1918 × 1078 | 16.9 MB |

**What it shows.** A screen recording of the running dashboard (`run_dashboard.bat`, `http://127.0.0.1:8501`), with on-screen captions. It walks through, in order:

1. Dataset overview: the bundled UCI Adult sample (3,000 rows, 14 columns).
2. Preprocessing: automatic column detection, then fitting the train/test split, rare-category threshold and binning.
3. Model selection and generation: PrivBayes with a chosen privacy budget (ε), then training.
4. Synthetic-data preview and CSV download.
5. Fidelity evaluation.
6. ML utility: TSTR vs TRTR.
7. Fairness and rare-pattern preservation.
8. Model comparison: ε vs utility, fidelity and privacy, plus the utility–privacy (Pareto) view.
9. LLM knowledge discovery: choosing a DP synthetic dataset, and the output (key patterns, attribute relationships, limitations).

**Checks before publishing (16 Oct 2026).** Sixteen frames sampled evenly across the video were inspected. No API key, `.env` content or terminal is visible. The browser's bookmarks bar is visible.

The video was recorded by the team; it is not generated.
