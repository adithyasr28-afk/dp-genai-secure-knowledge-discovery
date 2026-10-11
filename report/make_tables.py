"""
report/make_tables.py

Generates the numeric results tables of the report as Markdown, directly
from results/verified/ (written by analysis/verify_results.py and
analysis/knowledge_utility.py), so no number is transcribed by hand.
build_report.py includes them through {{INCLUDE:generated/<name>.md}}.

Run from the project root:  python report/make_tables.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "results" / "verified"
OUT = Path(__file__).resolve().parent / "generated"
ORDER = ["AIM", "MST", "PrivBayes", "CTGAN", "TVAE"]


def ms(row, col, d=3, pct=False):
    m, s = row[f"{col}_mean"], row.get(f"{col}_std")
    if pd.isna(m):
        return "—"
    f = f"{{:.{d}f}}"
    if pd.isna(s) or row["n_seeds"] == 1:
        return f.format(m) + ("†" if row["n_seeds"] == 1 else "")
    return f"{f.format(m)} ± {f.format(s)}"


def label(row):
    return f"{row['method']} ε={row['epsilon']:g}" if row["is_dp"] else f"{row['method']} (non-DP)"


def main():
    OUT.mkdir(exist_ok=True)
    agg = pd.read_csv(V / "aggregated_by_method_epsilon.csv")
    agg["method"] = pd.Categorical(agg["method"], ORDER, ordered=True)
    agg = agg.sort_values(["method", "epsilon"])
    rep = json.loads((V / "verification_report.json").read_text(encoding="utf-8"))
    trtr = pd.read_csv(V / "trtr_reference.csv").set_index("model_name")

    def write_table(name, label, caption, header, rows_fn, extra=None):
        lines = [f"Table: {{{label}}} {caption}", "", "| " + " | ".join(header) + " |",
                 "|" + "|".join(["---"] * len(header)) + "|"]
        for _, r in agg.iterrows():
            lines.append("| " + " | ".join([label_of(r)] + rows_fn(r)) + " |")
        if extra:
            lines.append(extra)
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")

    label_of = label
    note = "(mean ± std over seeds; † = single seed)"
    write_table("table_utility.md", "tab:utility", f"TSTR utility across the ε sweep {note}",
                ["Configuration", "F1 LR", "F1 RF", "F1 XGB", "AUROC XGB", "$R_{F1}$ XGB (%)"],
                lambda r: [ms(r, "f1_logistic_regression"), ms(r, "f1_random_forest"), ms(r, "f1_xgboost"),
                           ms(r, "auroc_xgboost"), f"{r['f1_retention_pct_xgboost']:.1f}"],
                f"| **TRTR (real data)** | {trtr.loc['logistic_regression','f1']:.3f} | {trtr.loc['random_forest','f1']:.3f} | "
                f"{trtr.loc['xgboost','f1']:.3f} | {trtr.loc['xgboost','auroc']:.3f} | 100 |")
    write_table("table_fidelity.md", "tab:fidelity", f"Statistical fidelity across the ε sweep (lower is better) {note}",
                ["Configuration", "Mean KS", "Mean TVD", "3-way TVD", "ΔCramér's V"],
                lambda r: [ms(r, "mean_ks_statistic"), ms(r, "mean_tvd"), ms(r, "three_way_mean_l1_error"),
                           ms(r, "cramers_v_mean_abs_diff")])
    write_table("table_privacy.md", "tab:privacy", f"Empirical privacy and runtime {note}",
                ["Configuration", "MIA AUC", "TPR@FPR 0.1", "Mean DCR ↑", "Exact copies (%)", "Fit time (s)"],
                lambda r: [ms(r, "attack_auc"), ms(r, "tpr_at_fpr0.1"), ms(r, "mean_dcr", 2),
                           ms(r, "pct_near_duplicate", 3), ms(r, "fit_runtime_s", 1)])
    fr = rep["trtr_fairness_logreg_sex"]
    write_table("table_rarefair.md", "tab:rarefair", f"Rare-pattern preservation and fairness by sex {note}",
                ["Configuration", "Rare categories lost (%)", "Rare combinations lost (%)", "ΔDP ↓", "ΔEO ↓"],
                lambda r: [ms(r, "pct_rare_categories_disappeared", 1), ms(r, "pct_rare_combinations_disappeared", 1),
                           ms(r, "dp_difference_sex"), ms(r, "eo_max_gap_sex")],
                f"| **Real-data reference** | — | — | {fr['demographic_parity_difference']:.3f} | {fr['equalized_odds_max_gap']:.3f} |")
    for stale in ("table_results.md", "table_privfair.md"):
        if (OUT / stale).exists():
            (OUT / stale).unlink()

    # Knowledge utility
    ku = pd.read_csv(V / "knowledge_utility_aggregated.csv")
    ku["method"] = pd.Categorical(ku["method"], ORDER, ordered=True)
    ku = ku.sort_values(["method", "epsilon"])
    n = pd.read_csv(V / "knowledge_utility_runs.csv").groupby(["method", "epsilon"]).size()
    lines = ["Table: {tab:ku} Knowledge utility of LLM payload statistics versus the real training split (mean ± std; † = single seed)", "",
             "| Dataset | KU ↑ | Spearman ρ ↑ | Top-1 agreement ↑ | Real cells missing in payload |",
             "|---|---|---|---|---|"]
    for _, r in ku.iterrows():
        r = r.copy()
        r["n_seeds"] = int(n[(r["method"], r["epsilon"])])
        lines.append(f"| {r['method']} ε={r['epsilon']:g} | {ms(r, 'knowledge_utility_KU')} | {ms(r, 'spearman_rho')} | "
                     f"{ms(r, 'top1_agreement')} | {ms(r, 'cells_missing_vs_real', 1)} |")
    (OUT / "table_ku.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Verification evidence (appendix)
    cmp = pd.read_csv(V / "reevaluation_comparison.csv")
    g = cmp.groupby("metric").agg(n=("match", "size"), matched=("match", "sum"), max_diff=("abs_diff", "max")).reset_index()
    lines = ["Table: {tab:verify} Re-evaluation of logged metrics from the saved synthetic CSVs (41 runs; tolerance 10⁻⁶)", "",
             "| Metric | Values compared | Exact matches | Max. abs. difference |", "|---|---|---|---|"]
    for _, r in g.iterrows():
        lines.append(f"| `{r['metric']}` | {r['n']} | {int(r['matched'])} | {r['max_diff']:.2e} |")
    lines.append(f"| **Total** | {int(g['n'].sum())} | {int(g['matched'].sum())} | — |")
    (OUT / "table_verify.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Duplicate records
    d = pd.read_csv(V / "duplicate_records_comparison.csv")
    lines = ["Table: {tab:dups} The two duplicated configurations in the experiment log (both records shown; the later one is used)", "",
             "| run_id | Log line | Timestamp | Fit time (s) | 3-way TVD | F1 XGB | MIA AUC |", "|---|---|---|---|---|---|---|"]
    for _, r in d.iterrows():
        lines.append(f"| `{r['run_id']}` | {r['line']} | {r['timestamp']} | {r['fit_runtime_s']:.1f} | "
                     f"{r['three_way_mean_l1_error']:.3f} | {r['f1_xgboost']:.3f} | {r['attack_auc']:.3f} |")
    (OUT / "table_dups.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", sorted(p.name for p in OUT.glob("*.md")))


if __name__ == "__main__":
    main()
