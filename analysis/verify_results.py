"""
analysis/verify_results.py

Verifies the saved experiment results and produces the de-duplicated,
aggregated tables and figures used in the report. It does NOT re-train
any generator: every number is either read from
results/experiment_results.jsonl or recomputed from the saved synthetic
CSVs in results/synthetic_data/ with the project's own evaluation code.

Steps
  1. Log integrity: record count, unique run_ids, duplicates, statuses.
  2. De-duplication: keep the LATEST completed record per run_id (the
     synthetic CSV on disk was overwritten by that later run).
  3. Configuration checks: epsilon/delta per method, pure vs approximate
     DP, AIM rounds cap, non-DP labelling of CTGAN/TVAE, row counts.
  4. Re-evaluation: recompute fidelity, utility (TSTR), MIA, record
     similarity, rare-pattern and fairness metrics from each saved CSV and
     compare them with the logged values.
  5. TRTR reference (not stored in the log) computed once.
  6. Aggregation (mean ± std over seeds) and figures (600 DPI PNG + SVG).

Run from the project root:
    python -m analysis.verify_results
Outputs go to results/verified/ and figures/.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from preprocessing.schema import profile_dataset  # noqa: E402
from preprocessing.pipeline import Preprocessor, train_test_split_no_leakage  # noqa: E402
from experiments.runner import compute_trtr_once  # noqa: E402
from evaluation import fidelity as fid_eval  # noqa: E402
from evaluation import utility as util_eval  # noqa: E402
from evaluation import privacy as priv_eval  # noqa: E402
from evaluation import rare_patterns as rare_eval  # noqa: E402

LOG = ROOT / "results" / "experiment_results.jsonl"
SYNTH = ROOT / "results" / "synthetic_data"
OUT = ROOT / "results" / "verified"
FIG = ROOT / "figures"
TOL = 1e-6
METHOD_ORDER = ["AIM", "MST", "PrivBayes", "CTGAN", "TVAE"]


def load_log():
    recs = []
    with open(LOG, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.strip():
                r = json.loads(line)
                r["_line"] = i + 1
                recs.append(r)
    return recs


def setup_data():
    """Recreate exactly the split / preprocessing used by run_sweep.py."""
    df = pd.read_csv(ROOT / "data" / "example_dataset.csv")
    profile = profile_dataset(df)
    num = [c.name for c in profile.columns if c.inferred_type == "numerical"]
    cat = [c.name for c in profile.columns if c.inferred_type == "categorical"]
    if "income" not in cat:
        cat.append("income")
    train, test = train_test_split_no_leakage(df, test_size=0.2, random_seed=42, stratify_column="income")
    pp = Preprocessor(rare_threshold=0.01, n_bins=10, random_seed=42)
    pp.fit(train, numerical_columns=num, categorical_columns=cat, target_column="income", sensitive_column="sex")
    return df, train, test, pp, num, cat


def recompute(rec, synth, train, test, pp, num, cat):
    seed = rec["random_seed"]
    rtr = pp.transform_continuous(train)
    rte = pp.transform_continuous(test)
    vocab = pp.fitted_.categorical_vocab
    m = fid_eval.marginal_fidelity_report(rtr, synth, num, cat)
    c = fid_eval.correlation_fidelity_report(rtr, synth, num, cat)
    t = fid_eval.three_way_marginal_query_error(rtr, synth, cat, n_queries=30, random_seed=seed)
    fid = fid_eval.summarize_fidelity(m, c, t)
    tstr = util_eval.evaluate_utility(synth, rte, "income", num, cat, vocab, "synthetic", random_seed=seed)
    mia = priv_eval.membership_inference_attack(rtr, rte, synth, num, cat, vocab, random_seed=seed)
    sim = priv_eval.record_similarity_report(rtr, synth, num, cat, vocab)
    rare = rare_eval.summarize_rare_pattern_loss(
        rare_eval.minority_class_report(rtr, synth, "income"),
        rare_eval.rare_category_report(rtr, synth, cat),
        rare_eval.rare_combination_report(rtr, synth, cat, combo_size=2, random_seed=seed),
    )
    return {
        "fidelity": fid,
        "f1": {r.model_name: r.f1 for r in tstr},
        "attack_auc": mia["attack_auc"],
        "tpr_at_fpr": mia["tpr_at_fixed_fpr"],
        "pct_near_dup": sim["pct_synthetic_near_duplicate"],
        "rare": rare,
    }


def compare(rec, rc):
    """List of (metric, logged, recomputed, abs_diff) for every comparable value."""
    rows = []
    for k, v in rc["fidelity"].items():
        rows.append((f"fidelity.{k}", rec["fidelity"].get(k), v))
    logged_f1 = {u["model_name"]: u["f1"] for u in rec["utility_tstr"]}
    for k, v in rc["f1"].items():
        rows.append((f"tstr_f1.{k}", logged_f1.get(k), v))
    rows.append(("mia.attack_auc", rec["privacy_mia"]["attack_auc"], rc["attack_auc"]))
    rows.append(("mia.tpr_at_fpr", rec["privacy_mia"]["tpr_at_fixed_fpr"], rc["tpr_at_fpr"]))
    rows.append(("similarity.pct_near_dup", rec["privacy_record_similarity"]["pct_synthetic_near_duplicate"], rc["pct_near_dup"]))
    for k, v in rc["rare"].items():
        rows.append((f"rare.{k}", rec["rare_patterns"].get(k), v))
    out = []
    for name, a, b in rows:
        if a is None or b is None:
            diff = None if a is None and b is None else float("inf")
        else:
            diff = abs(float(a) - float(b))
        out.append({"metric": name, "logged": a, "recomputed": b, "abs_diff": diff})
    return out


def flatten(rec):
    tstr = {u["model_name"]: u for u in rec["utility_tstr"]}
    fid = rec["fidelity"]
    fair = rec.get("fairness") or {}
    return {
        "run_id": rec["run_id"], "method": rec["method"], "epsilon": rec["epsilon"],
        "delta": (rec.get("privacy_params") or {}).get("delta", rec.get("delta")),
        "seed": rec["random_seed"], "is_dp": rec["is_differentially_private"],
        "fit_runtime_s": rec["fit_runtime_seconds"], "generate_runtime_s": rec["generate_runtime_seconds"],
        **{k: fid[k] for k in ["mean_ks_statistic", "mean_wasserstein_normalized", "mean_tvd", "mean_jsd",
                               "numerical_corr_frobenius_diff", "cramers_v_mean_abs_diff", "three_way_mean_l1_error"]},
        **{f"f1_{k}": v["f1"] for k, v in tstr.items()},
        **{f"auroc_{k}": v["auroc"] for k, v in tstr.items()},
        **{f"acc_{k}": v["accuracy"] for k, v in tstr.items()},
        "attack_auc": rec["privacy_mia"]["attack_auc"],
        "tpr_at_fpr0.1": rec["privacy_mia"]["tpr_at_fixed_fpr"],
        "mean_dcr": rec["privacy_record_similarity"]["mean_distance_to_nearest_real"],
        "pct_near_duplicate": rec["privacy_record_similarity"]["pct_synthetic_near_duplicate"],
        "max_minority_class_abs_diff": rec["rare_patterns"]["max_minority_class_abs_diff"],
        "pct_rare_categories_disappeared": rec["rare_patterns"]["pct_rare_categories_disappeared"],
        "pct_rare_combinations_disappeared": rec["rare_patterns"]["pct_rare_combinations_disappeared"],
        "dp_difference_sex": fair.get("demographic_parity_difference"),
        "eo_max_gap_sex": (fair.get("equalized_odds") or {}).get("max_gap"),
        "f1_gap_sex": fair.get("f1_performance_gap"),
    }


def make_figures(runs: pd.DataFrame, agg: pd.DataFrame, trtr: pd.DataFrame):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIG.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 9, "axes.grid": True, "grid.alpha": 0.3})
    colors = {"AIM": "#1f77b4", "MST": "#ff7f0e", "PrivBayes": "#2ca02c", "CTGAN": "#d62728", "TVAE": "#9467bd"}
    dp = agg[agg["is_dp"]]
    nondp = agg[~agg["is_dp"]]

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(FIG / f"{name}.png", dpi=600)
        fig.savefig(FIG / f"{name}.svg")
        plt.close(fig)

    def eps_plot(metric, ylabel, name, ref=None, ref_label=None, include_nondp=True):
        fig, ax = plt.subplots(figsize=(3.5, 2.6))
        for m in ["AIM", "MST", "PrivBayes"]:
            d = dp[dp["method"] == m].sort_values("epsilon")
            ax.errorbar(d["epsilon"], d[f"{metric}_mean"], yerr=d[f"{metric}_std"].fillna(0), marker="o",
                        ms=3, capsize=2, lw=1, label=m + (" (1 seed)" if m == "AIM" else ""), color=colors[m])
        if include_nondp:
            for m in ["CTGAN", "TVAE"]:
                d = nondp[nondp["method"] == m]
                if len(d):
                    ax.axhline(d[f"{metric}_mean"].iloc[0], ls="--", lw=0.9, color=colors[m], label=f"{m} (non-DP)")
        if ref is not None:
            ax.axhline(ref, ls=":", lw=1, color="k", label=ref_label)
        ax.set_xscale("log")
        ax.set_xticks([0.5, 1, 3, 5, 10])
        ax.set_xticklabels(["0.5", "1", "3", "5", "10"])
        ax.set_xlabel("Privacy budget ε (log scale)")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=6, loc="best")
        save(fig, name)

    trtr_f1 = trtr.set_index("model_name")["f1"]
    eps_plot("f1_xgboost", "TSTR F1 (XGBoost)", "fig_res_01_epsilon_vs_f1_xgboost", trtr_f1.get("xgboost"), "TRTR (real data)")
    eps_plot("f1_logistic_regression", "TSTR F1 (Logistic Regression)", "fig_res_02_epsilon_vs_f1_logreg",
             trtr_f1.get("logistic_regression"), "TRTR (real data)")
    eps_plot("three_way_mean_l1_error", "Mean 3-way marginal TVD (lower = better)", "fig_res_03_epsilon_vs_3way_error")
    eps_plot("mean_tvd", "Mean 1-way TVD, categorical (lower = better)", "fig_res_04_epsilon_vs_tvd")
    eps_plot("attack_auc", "Distance-based MIA AUC", "fig_res_05_epsilon_vs_mia_auc", 0.5, "Random guess (0.5)")
    eps_plot("pct_rare_combinations_disappeared", "Rare 2-way combinations lost (%)", "fig_res_06_epsilon_vs_rare_loss")
    eps_plot("dp_difference_sex", "Demographic parity difference (sex)", "fig_res_07_epsilon_vs_dp_difference")

    # Runtime
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for m in ["AIM", "MST", "PrivBayes"]:
        d = dp[dp["method"] == m].sort_values("epsilon")
        ax.errorbar(d["epsilon"], d["fit_runtime_s_mean"], yerr=d["fit_runtime_s_std"].fillna(0), marker="o", ms=3,
                    capsize=2, lw=1, label=m, color=colors[m])
    for m in ["CTGAN", "TVAE"]:
        d = nondp[nondp["method"] == m]
        ax.axhline(d["fit_runtime_s_mean"].iloc[0], ls="--", lw=0.9, color=colors[m], label=f"{m} (300 epochs)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xticks([0.5, 1, 3, 5, 10]); ax.set_xticklabels(["0.5", "1", "3", "5", "10"])
    ax.set_xlabel("Privacy budget ε (log scale)"); ax.set_ylabel("Fit runtime (s, log scale)")
    ax.legend(fontsize=6)
    save(fig, "fig_res_08_runtime")

    # Privacy-utility scatter (per run)
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    for m in METHOD_ORDER:
        d = runs[runs["method"] == m]
        ax.scatter(d["attack_auc"], d["f1_xgboost"], s=12, color=colors[m], label=m, alpha=0.8)
    ax.axvline(0.5, ls=":", color="k", lw=0.8)
    ax.set_xlabel("MIA AUC (empirical privacy risk →)"); ax.set_ylabel("TSTR F1 (XGBoost)")
    ax.legend(fontsize=6)
    save(fig, "fig_res_09_privacy_utility_scatter")

    # Fidelity-utility scatter
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    for m in METHOD_ORDER:
        d = runs[runs["method"] == m]
        ax.scatter(d["three_way_mean_l1_error"], d["f1_xgboost"], s=12, color=colors[m], label=m, alpha=0.8)
    ax.set_xlabel("Mean 3-way marginal TVD (lower = better)"); ax.set_ylabel("TSTR F1 (XGBoost)")
    ax.legend(fontsize=6)
    save(fig, "fig_res_10_fidelity_utility_scatter")

    # Heatmap at epsilon = 3 (DP) and non-DP
    metrics = ["mean_ks_statistic", "mean_tvd", "three_way_mean_l1_error", "cramers_v_mean_abs_diff",
               "f1_xgboost", "attack_auc", "pct_rare_combinations_disappeared", "dp_difference_sex"]
    labels = ["KS", "TVD", "3-way TVD", "ΔCramér V", "F1 XGB", "MIA AUC", "Rare combos lost %", "DP diff"]
    sel = pd.concat([dp[dp["epsilon"] == 3.0], nondp])
    sel = sel.set_index(sel.apply(lambda r: f"{r['method']} ε=3" if r["is_dp"] else f"{r['method']} (non-DP)", axis=1))
    mat = sel[[f"{m}_mean" for m in metrics]].astype(float)
    norm = (mat - mat.min()) / (mat.max() - mat.min()).replace(0, 1)
    fig, ax = plt.subplots(figsize=(7.16, 2.6))
    im = ax.imshow(norm.values, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_yticks(range(len(mat))); ax.set_yticklabels(mat.index)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat.values[i, j]:.3f}", ha="center", va="center", fontsize=6,
                    color="white" if norm.values[i, j] < 0.5 else "black")
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="Column-normalised value")
    save(fig, "fig_res_11_heatmap_eps3")

    # Radar chart at epsilon = 3 (DP) vs non-DP. Every axis is a bounded
    # "higher is better" transform of a raw metric (no min-max rescaling, which
    # would exaggerate small differences):
    axes_def = [
        ("1 − KS", lambda r: 1 - r["mean_ks_statistic_mean"]),
        ("1 − TVD", lambda r: 1 - r["mean_tvd_mean"]),
        ("1 − 3-way TVD", lambda r: 1 - r["three_way_mean_l1_error_mean"]),
        ("F1 / TRTR F1\n(XGBoost)", lambda r: min(r["f1_xgboost_mean"] / trtr_f1["xgboost"], 1.0)),
        ("1 − 2·|AUC − 0.5|\n(MIA)", lambda r: 1 - 2 * abs(r["attack_auc_mean"] - 0.5)),
        ("1 − rare combos\nlost", lambda r: 1 - r["pct_rare_combinations_disappeared_mean"] / 100),
        ("1 − DP diff", lambda r: 1 - r["dp_difference_sex_mean"]),
    ]
    angles = np.linspace(0, 2 * np.pi, len(axes_def), endpoint=False).tolist()
    fig = plt.figure(figsize=(3.5, 4.1))
    ax = fig.add_subplot(111, polar=True)
    ax.set_rlabel_position(100)
    for _, r in sel.iterrows():
        vals = [f(r) for _, f in axes_def]
        ax.plot(angles + angles[:1], vals + vals[:1], lw=1, color=colors[r["method"]],
                ls="-" if r["is_dp"] else "--", label=r.name)
        ax.fill(angles + angles[:1], vals + vals[:1], alpha=0.05, color=colors[r["method"]])
    ax.set_xticks(angles); ax.set_xticklabels([a for a, _ in axes_def], fontsize=6)
    ax.set_ylim(0, 1); ax.tick_params(axis="y", labelsize=6)
    ax.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    save(fig, "fig_res_13_radar_eps3")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    recs = load_log()
    ids = Counter(r["run_id"] for r in recs)
    report["n_records"] = len(recs)
    report["n_unique_run_ids"] = len(ids)
    report["duplicate_run_ids"] = {k: v for k, v in ids.items() if v > 1}
    report["status_counts"] = dict(Counter(r["status"] for r in recs))
    report["records_per_method"] = dict(Counter(r["method"] for r in recs))

    latest = {}
    for r in recs:
        if r["status"] != "completed":
            continue
        if r["run_id"] not in latest or r["timestamp"] >= latest[r["run_id"]]["timestamp"]:
            latest[r["run_id"]] = r
    unique = list(latest.values())
    report["unique_runs_per_method"] = dict(Counter(r["method"] for r in unique))

    # --- configuration checks ------------------------------------------------
    checks = []
    for r in unique:
        pp = r.get("privacy_params") or {}
        m = r["method"]
        if m in ("AIM", "MST"):
            ok = r["is_differentially_private"] and pp.get("delta") == 1e-5 and pp.get("epsilon") == r["epsilon"]
            if m == "AIM":
                ok = ok and pp.get("rounds_cap_applied") == 60
            kind = "(ε, δ)-DP"
        elif m == "PrivBayes":
            ok = r["is_differentially_private"] and pp.get("delta") == 0.0 and "pure DP" in r["privacy_formal"]["formal_guarantee"]
            kind = "pure ε-DP"
        else:
            ok = (not r["is_differentially_private"]) and r["privacy_formal"]["formal_guarantee"] == "None" and r["epsilon"] is None
            kind = "non-DP"
        csv = SYNTH / f"{r['run_id']}.csv"
        rows = len(pd.read_csv(csv)) if csv.exists() else None
        checks.append({"run_id": r["run_id"], "method": m, "guarantee_type": kind, "config_ok": bool(ok),
                       "csv_exists": csv.exists(), "csv_rows": rows, "logged_rows": r["n_synthetic_rows"]})
    checks_df = pd.DataFrame(checks)
    checks_df.to_csv(OUT / "config_checks.csv", index=False)
    report["all_configs_ok"] = bool(checks_df["config_ok"].all())
    report["all_csvs_present_with_matching_rows"] = bool((checks_df["csv_exists"] & (checks_df["csv_rows"] == checks_df["logged_rows"])).all())
    report["extra_csvs_without_log_record"] = sorted({p.stem for p in SYNTH.glob("*.csv")} - set(latest))

    # --- duplicates: compare both records ------------------------------------
    dup_rows = []
    for rid in report["duplicate_run_ids"]:
        for r in [x for x in recs if x["run_id"] == rid]:
            f = flatten(r)
            dup_rows.append({"line": r["_line"], "timestamp": r["timestamp"], **{k: f[k] for k in
                            ["run_id", "fit_runtime_s", "three_way_mean_l1_error", "f1_xgboost", "attack_auc"]}})
    pd.DataFrame(dup_rows).to_csv(OUT / "duplicate_records_comparison.csv", index=False)

    # --- re-evaluation from saved CSVs ---------------------------------------
    _, train, test, pp, num, cat = setup_data()
    comp_rows = []
    for r in sorted(unique, key=lambda x: x["run_id"]):
        synth = pd.read_csv(SYNTH / f"{r['run_id']}.csv")
        rc = recompute(r, synth, train, test, pp, num, cat)
        for row in compare(r, rc):
            comp_rows.append({"run_id": r["run_id"], "method": r["method"], **row})
        print(f"re-evaluated {r['run_id']}", flush=True)
    comp = pd.DataFrame(comp_rows)
    comp["match"] = comp["abs_diff"].apply(lambda d: d is None or (d is not None and d <= TOL))
    comp.to_csv(OUT / "reevaluation_comparison.csv", index=False)
    report["reevaluation_values_compared"] = int(len(comp))
    report["reevaluation_values_matching"] = int(comp["match"].sum())
    report["reevaluation_mismatches_by_metric"] = comp[~comp["match"]].groupby("metric").size().to_dict()
    report["reevaluation_max_abs_diff_by_metric"] = comp.groupby("metric")["abs_diff"].max().to_dict()

    # --- TRTR ----------------------------------------------------------------
    trtr = pd.DataFrame(compute_trtr_once(train, test, pp, num, cat, "income"))
    trtr.to_csv(OUT / "trtr_reference.csv", index=False)
    report["trtr_f1"] = trtr.set_index("model_name")["f1"].to_dict()

    # Real-data fairness reference: same classifier and encoding as the
    # per-run fairness block in experiments/runner.py, trained on REAL data.
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from evaluation import fairness as fair_eval
    rtr, rte = pp.transform_continuous(train), pp.transform_continuous(test)
    feat_cat = [c for c in cat if c != "income"]
    scaler = StandardScaler()
    Xtr = util_eval._encode_features(rtr, num, feat_cat, pp.fitted_.categorical_vocab, scaler=scaler, fit_scaler=True)
    Xte = util_eval._encode_features(rte, num, feat_cat, pp.fitted_.categorical_vocab, scaler=scaler, fit_scaler=False)
    pos = sorted(rte["income"].astype(str).unique())[-1]
    clf = LogisticRegression(max_iter=1000, random_state=42).fit(Xtr, (rtr["income"].astype(str) == pos).astype(int))
    fr = fair_eval.evaluate_fairness(clf, Xte, (rte["income"].astype(str) == pos).astype(int).values, test["sex"])
    report["trtr_fairness_logreg_sex"] = {
        "demographic_parity_difference": fr["demographic_parity_difference"],
        "equalized_odds_max_gap": fr["equalized_odds"]["max_gap"],
        "f1_performance_gap": fr["f1_performance_gap"],
        "subgroups": fr["subgroup_performance"].to_dict(orient="records"),
    }

    # --- aggregation ---------------------------------------------------------
    runs = pd.DataFrame([flatten(r) for r in unique])
    runs["method"] = pd.Categorical(runs["method"], METHOD_ORDER, ordered=True)
    runs = runs.sort_values(["method", "epsilon", "seed"])
    runs.to_csv(OUT / "runs_deduplicated.csv", index=False)
    metric_cols = [c for c in runs.columns if c not in ("run_id", "method", "epsilon", "delta", "seed", "is_dp")]
    g = runs.assign(epsilon=runs["epsilon"].fillna(-1)).groupby(["method", "epsilon"], observed=True)
    agg = g[metric_cols].agg(["mean", "std"])
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    agg = agg.reset_index()
    agg["n_seeds"] = g.size().values
    agg["is_dp"] = agg["method"].isin(["AIM", "MST", "PrivBayes"])
    agg["epsilon"] = agg["epsilon"].replace(-1, np.nan)
    for m in ["logistic_regression", "random_forest", "xgboost"]:
        agg[f"f1_retention_pct_{m}"] = 100 * agg[f"f1_{m}_mean"] / report["trtr_f1"][m]
    agg.to_csv(OUT / "aggregated_by_method_epsilon.csv", index=False)

    (OUT / "verification_report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    make_figures(runs, agg, trtr)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
