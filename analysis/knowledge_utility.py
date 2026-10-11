"""
analysis/knowledge_utility.py

OFFLINE evaluation of the knowledge-discovery payload (run by the
research team, never by the LLM page): how faithfully do the aggregate
statistics computed from each DP synthetic dataset reproduce the same
statistics computed on the REAL training split?

For every categorical column c and level v that is reported (>= k rows)
in BOTH summaries, let s_syn and s_real be the positive-target rate. Then

    KU   = 1 - mean_{c,v} | s_syn(c,v) - s_real(c,v) |       (knowledge utility)
    rho  = Spearman rank correlation of the s values         (ranking agreement)
    top1 = share of columns whose highest-rate level agrees  (headline agreement)

The real data is used here only to score the synthetic summaries; nothing
in this script calls an LLM or writes real-data statistics anywhere other
than the local results/verified/ folder.

Run from the project root:  python -m analysis.knowledge_utility
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis.verify_results import setup_data  # noqa: E402
from knowledge_discovery.catalog import SyntheticDatasetInfo, list_dp_synthetic_datasets, load_synthetic_dataset  # noqa: E402
from knowledge_discovery.summarizer import build_aggregate_summary  # noqa: E402

OUT = ROOT / "results" / "verified"
FIG = ROOT / "figures"


def _cells(summary: dict) -> dict:
    out = {}
    for col, groups in summary["target_analysis"]["positive_rate_by_column"].items():
        if "(quartile bins)" in col:
            continue
        for level, g in groups.items():
            out[(col, level)] = g["positive_rate"]
    return out


def _top_levels(summary: dict) -> dict:
    tops = {}
    for col, groups in summary["target_analysis"]["positive_rate_by_column"].items():
        if "(quartile bins)" not in col and groups:
            tops[col] = next(iter(groups))  # summariser orders levels by rate, descending
    return tops


def main():
    _, train, _, pp, _, _ = setup_data()
    real = pp.transform_continuous(train)
    dummy = SyntheticDatasetInfo(run_id="real_train", method="REAL", epsilon=None, delta=None,
                                 random_seed=None, csv_path=Path("."))
    real_summary = build_aggregate_summary(real, dummy, top_k=100)
    real_cells, real_tops = _cells(real_summary), _top_levels(real_summary)

    rows = []
    for info in list_dp_synthetic_datasets():
        s = build_aggregate_summary(load_synthetic_dataset(info), info, top_k=100)
        cells, tops = _cells(s), _top_levels(s)
        common = sorted(set(cells) & set(real_cells))
        a = np.array([cells[k] for k in common])
        b = np.array([real_cells[k] for k in common])
        shared_cols = set(tops) & set(real_tops)
        rows.append({
            "run_id": info.run_id, "method": info.method, "epsilon": info.epsilon, "seed": info.random_seed,
            "n_cells_compared": len(common),
            "cells_missing_vs_real": len(set(real_cells) - set(cells)),
            "knowledge_utility_KU": 1 - float(np.mean(np.abs(a - b))),
            "spearman_rho": float(spearmanr(a, b).statistic),
            "top1_agreement": float(np.mean([tops[c] == real_tops[c] for c in shared_cols])),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "knowledge_utility_runs.csv", index=False)
    agg = df.groupby(["method", "epsilon"])[["knowledge_utility_KU", "spearman_rho", "top1_agreement",
                                              "cells_missing_vs_real"]].agg(["mean", "std"])
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    agg = agg.reset_index()
    agg.to_csv(OUT / "knowledge_utility_aggregated.csv", index=False)
    print(agg.round(3).to_string())

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
    colors = {"AIM": "#1f77b4", "MST": "#ff7f0e", "PrivBayes": "#2ca02c"}
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.6))
    for m in ["AIM", "MST", "PrivBayes"]:
        d = agg[agg["method"] == m].sort_values("epsilon")
        for ax, metric, label in [(axes[0], "knowledge_utility_KU", "Knowledge utility KU"),
                                  (axes[1], "spearman_rho", "Spearman ρ of group rates")]:
            ax.errorbar(d["epsilon"], d[f"{metric}_mean"], yerr=d[f"{metric}_std"].fillna(0), marker="o", ms=3,
                        capsize=2, lw=1, color=colors[m], label=m)
            ax.set_xscale("log"); ax.set_xticks([0.5, 1, 3, 5, 10]); ax.set_xticklabels(["0.5", "1", "3", "5", "10"])
            ax.set_xlabel("Privacy budget ε (log scale)"); ax.set_ylabel(label)
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "fig_res_12_knowledge_utility.png", dpi=600)
    fig.savefig(FIG / "fig_res_12_knowledge_utility.svg")


if __name__ == "__main__":
    main()
