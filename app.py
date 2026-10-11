"""
app.py

Streamlit research dashboard for the privacy-preserving synthetic
tabular data comparison project. See README.md for the full project
description and Section 16 of the original spec for the page layout
this implements.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
import streamlit as st

from preprocessing.schema import profile_dataset, class_imbalance_report
from preprocessing.pipeline import Preprocessor, train_test_split_no_leakage
from experiments.config import RunConfig, SweepConfig, DEFAULT_EPSILON_SWEEP, DEFAULT_DELTA
from experiments.runner import run_single_experiment, compute_trtr_once, load_all_results, DP_METHODS
from evaluation import fidelity as fid_eval
from evaluation import rare_patterns as rare_eval
from evaluation import fairness as fair_eval

st.set_page_config(page_title="Synthetic Tabular Data — Privacy/Utility Comparison", layout="wide")

# ----------------------------------------------------------------------
# Session state initialization
# ----------------------------------------------------------------------
DEFAULTS = {
    "raw_df": None,
    "dataset_name": None,
    "profile": None,
    "target_column": None,
    "sensitive_column": None,
    "excluded_columns": [],
    "numerical_columns": [],
    "categorical_columns": [],
    "train_df": None,
    "test_df": None,
    "preprocessor": None,
    "trtr_results": None,
    "last_generation": {},  # method -> result dict, for the "Generate" page's immediate feedback
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_downstream_state():
    """Called whenever the dataset changes -- everything derived from
    the old dataset (preprocessing, splits, results) must not silently
    carry over."""
    for key in ["profile", "target_column", "sensitive_column", "excluded_columns",
                "numerical_columns", "categorical_columns", "train_df", "test_df",
                "preprocessor", "trtr_results", "last_generation"]:
        st.session_state[key] = DEFAULTS[key]


# ----------------------------------------------------------------------
# Sidebar: dataset loading (always visible) + page navigation
# ----------------------------------------------------------------------
st.sidebar.title("Dataset")

uploaded_file = st.sidebar.file_uploader("Upload a CSV", type=["csv"])
use_example = st.sidebar.button("Use bundled example dataset (Adult Income, n=3000)")

if uploaded_file is not None:
    new_df = pd.read_csv(uploaded_file)
    new_name = uploaded_file.name.rsplit(".", 1)[0]
    if st.session_state["dataset_name"] != new_name:
        reset_downstream_state()
    st.session_state["raw_df"] = new_df
    st.session_state["dataset_name"] = new_name

if use_example:
    example_df = pd.read_csv("data/example_dataset.csv")
    if st.session_state["dataset_name"] != "adult_example":
        reset_downstream_state()
    st.session_state["raw_df"] = example_df
    st.session_state["dataset_name"] = "adult_example"

if st.session_state["raw_df"] is None:
    st.title("Privacy-Preserving Synthetic Tabular Data — Comparative Study")
    st.info(
        "Upload a CSV, or click **'Use bundled example dataset'** in the sidebar to try the "
        "full pipeline immediately with a pre-cleaned Adult Income sample (3,000 rows)."
    )
    st.stop()

PAGES = [
    "Dataset",
    "Preprocessing",
    "Model Selection & Generate",
    "Synthetic Data",
    "Fidelity",
    "ML Utility",
    "Privacy",
    "Fairness / Rare Patterns",
    "Model Comparison",
]
page = st.sidebar.radio("Navigate", PAGES)

df = st.session_state["raw_df"]

# ============================================================================
# PAGE: Dataset
# ============================================================================
if page == "Dataset":
    st.title("Dataset overview")
    st.caption(f"Loaded: **{st.session_state['dataset_name']}**")

    if st.session_state["profile"] is None:
        st.session_state["profile"] = profile_dataset(df)
    profile = st.session_state["profile"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", profile.n_rows)
    c2.metric("Columns", profile.n_columns)
    c3.metric("Duplicate rows", profile.duplicate_row_count)
    c4.metric("Columns with missing values", sum(1 for c in profile.columns if c.n_missing > 0))

    st.subheader("Column analysis")
    col_rows = []
    for c in profile.columns:
        col_rows.append({
            "column": c.name,
            "inferred_type": c.inferred_type,
            "dtype": c.dtype,
            "n_missing": c.n_missing,
            "pct_missing": c.pct_missing,
            "n_unique": c.n_unique,
            "high_cardinality": c.is_high_cardinality,
        })
    st.dataframe(pd.DataFrame(col_rows), use_container_width=True)

    st.subheader("Preview")
    st.dataframe(df.head(20), use_container_width=True)

    st.subheader("Target & sensitive attribute selection")
    candidate_cols = [c.name for c in profile.columns if c.inferred_type != "id_like"]

    default_target = (
        profile.suggested_target_columns[0]
        if profile.suggested_target_columns and profile.suggested_target_columns[0] in candidate_cols
        else candidate_cols[0]
    )
    target_col = st.selectbox(
        "Target column (used for TSTR/TRTR classification)",
        candidate_cols,
        index=candidate_cols.index(default_target),
    )

    sensitive_options = ["(none)"] + [c for c in candidate_cols if c != target_col]
    default_sensitive = (
        profile.suggested_sensitive_columns[0]
        if profile.suggested_sensitive_columns and profile.suggested_sensitive_columns[0] in sensitive_options
        else "(none)"
    )
    sensitive_col = st.selectbox(
        "Sensitive attribute (optional — enables the Fairness module)",
        sensitive_options,
        index=sensitive_options.index(default_sensitive),
    )

    excluded = st.multiselect(
        "Columns to exclude from generation (id-like / high-cardinality columns are pre-selected)",
        [c.name for c in profile.columns if c.name != target_col],
        default=[c.name for c in profile.columns if c.inferred_type == "id_like" or c.is_high_cardinality],
    )

    if st.button("Confirm selections", type="primary"):
        st.session_state["target_column"] = target_col
        st.session_state["sensitive_column"] = None if sensitive_col == "(none)" else sensitive_col
        st.session_state["excluded_columns"] = excluded
        remaining = [c.name for c in profile.columns if c.name not in excluded]
        st.session_state["numerical_columns"] = [
            c.name for c in profile.columns if c.name in remaining and c.inferred_type == "numerical" and c.name != target_col
        ]
        st.session_state["categorical_columns"] = [
            c.name for c in profile.columns if c.name in remaining and c.inferred_type == "categorical" and c.name != target_col
        ]
        # Target itself must also appear in categorical_columns for the
        # DP methods' joint discretized fit and for utility/fairness
        # target handling elsewhere in the pipeline.
        if target_col not in st.session_state["categorical_columns"]:
            st.session_state["categorical_columns"].append(target_col)
        st.success(
            f"Confirmed. Target='{target_col}', sensitive="
            f"'{st.session_state['sensitive_column']}', "
            f"{len(st.session_state['numerical_columns'])} numerical + "
            f"{len(st.session_state['categorical_columns'])} categorical columns."
        )

    if st.session_state["target_column"]:
        st.subheader(f"Class balance of target: {st.session_state['target_column']}")
        report = class_imbalance_report(df, st.session_state["target_column"])
        st.json(report)

# ============================================================================
# PAGE: Preprocessing
# ============================================================================
elif page == "Preprocessing":
    st.title("Preprocessing")

    if not st.session_state["target_column"]:
        st.warning("Confirm your column selections on the **Dataset** page first.")
        st.stop()

    st.write("**Numerical columns:**", st.session_state["numerical_columns"])
    st.write("**Categorical columns (including target):**", st.session_state["categorical_columns"])
    st.write("**Excluded columns:**", st.session_state["excluded_columns"])

    col1, col2, col3 = st.columns(3)
    test_size = col1.slider("Test set fraction", 0.1, 0.4, 0.2, 0.05)
    rare_threshold = col2.slider("Rare-category threshold", 0.001, 0.05, 0.01, 0.001, format="%.3f")
    n_bins = col3.slider("Numerical bins (for DP methods)", 3, 20, 10)

    if st.button("Fit preprocessing (train/test split, no leakage)", type="primary"):
        strat_col = st.session_state["target_column"]
        train_df, test_df = train_test_split_no_leakage(
            df, test_size=test_size, random_seed=42, stratify_column=strat_col
        )
        pp = Preprocessor(rare_threshold=rare_threshold, n_bins=n_bins, random_seed=42)
        pp.fit(
            train_df,
            numerical_columns=st.session_state["numerical_columns"],
            categorical_columns=st.session_state["categorical_columns"],
            target_column=st.session_state["target_column"],
            sensitive_column=st.session_state["sensitive_column"],
        )
        st.session_state["train_df"] = train_df
        st.session_state["test_df"] = test_df
        st.session_state["preprocessor"] = pp
        st.session_state["trtr_results"] = None  # invalidate cached TRTR
        st.success(f"Fitted on {len(train_df)} training rows; held out {len(test_df)} test rows.")

    if st.session_state["preprocessor"] is not None:
        st.subheader("Fitted preprocessing summary")
        fitted = st.session_state["preprocessor"].fitted_
        st.write("Numerical bin edges (per column):")
        st.json(fitted.numerical_bin_edges)
        st.write("Spike values detected (dominant point mass given its own bin):")
        st.json({k: v for k, v in fitted.numerical_spike_value.items() if v is not None})
        st.write("Categorical vocabulary sizes (post rare-grouping):")
        st.json({k: len(v) for k, v in fitted.categorical_vocab.items()})

# ============================================================================
# PAGE: Model Selection & Generate
# ============================================================================
elif page == "Model Selection & Generate":
    st.title("Model selection, privacy configuration, and generation")

    if st.session_state["preprocessor"] is None:
        st.warning("Fit preprocessing on the **Preprocessing** page first.")
        st.stop()

    method = st.selectbox("Method", ["AIM", "MST", "PrivBayes", "CTGAN", "TVAE"])
    is_dp = method in DP_METHODS
    st.write("**Differentially Private**" if is_dp else "**Non-DP (no formal privacy guarantee)**")

    col1, col2 = st.columns(2)
    with col1:
        if is_dp:
            epsilon = st.select_slider("Epsilon", options=DEFAULT_EPSILON_SWEEP, value=3.0)
            delta = st.number_input("Delta", value=DEFAULT_DELTA, format="%.1e") if method != "PrivBayes" else 0.0
            if method == "PrivBayes":
                st.caption("PrivBayes provides pure epsilon-DP (delta=0), not (epsilon,delta)-DP like AIM/MST.")
        else:
            epochs = st.slider("Training epochs", 10, 300, 300, 10)
    with col2:
        size_mult = st.select_slider("Synthetic size (x training rows)", options=[1.0, 2.0, 5.0], value=1.0)
        seed = st.number_input("Random seed", value=42, step=1)

    if st.button("Run generator", type="primary"):
        config = RunConfig(
            dataset_name=st.session_state["dataset_name"],
            method=method,
            random_seed=int(seed),
            epsilon=epsilon if is_dp else None,
            delta=(delta if method != "PrivBayes" else 0.0) if is_dp else None,
            synthetic_size_multiplier=size_mult,
            epochs=epochs if not is_dp else None,
        )

        with st.spinner(f"Running {method}... this can take a while, especially for AIM (see README)."):
            start = time.perf_counter()
            result = run_single_experiment(
                config,
                st.session_state["train_df"], st.session_state["test_df"],
                st.session_state["preprocessor"],
                st.session_state["numerical_columns"], st.session_state["categorical_columns"],
                st.session_state["target_column"], st.session_state["sensitive_column"],
                skip_if_completed=False,  # explicit UI-triggered run always executes
            )
            elapsed = time.perf_counter() - start

        if result["status"] == "completed":
            st.success(f"Done in {elapsed:.1f}s (fit: {result['fit_runtime_seconds']:.1f}s, "
                       f"generate: {result['generate_runtime_seconds']:.1f}s). "
                       f"{result['n_synthetic_rows']} synthetic rows generated.")
            st.session_state["last_generation"][method] = result
        else:
            st.error(f"Run failed: {result.get('error')}")
            with st.expander("Traceback"):
                st.code(result.get("traceback", ""))

    if st.session_state["trtr_results"] is None and st.button("Compute TRTR reference (real-data ceiling)"):
        with st.spinner("Training on real data..."):
            trtr = compute_trtr_once(
                st.session_state["train_df"], st.session_state["test_df"], st.session_state["preprocessor"],
                st.session_state["numerical_columns"], st.session_state["categorical_columns"],
                st.session_state["target_column"],
            )
            st.session_state["trtr_results"] = trtr
        st.success("TRTR computed.")

    if st.session_state["last_generation"]:
        st.subheader("Most recent runs (this session)")
        for m, r in st.session_state["last_generation"].items():
            st.write(f"**{m}** — run_id: `{r['run_id']}` — status: {r['status']}")

# ============================================================================
# PAGE: Synthetic Data
# ============================================================================
elif page == "Synthetic Data":
    st.title("Synthetic data preview")

    if not st.session_state["last_generation"]:
        st.warning("Run at least one generator on the **Model Selection & Generate** page first.")
        st.stop()

    method = st.selectbox("Method to preview", list(st.session_state["last_generation"].keys()))
    result = st.session_state["last_generation"][method]

    if result["status"] != "completed":
        st.error("This run did not complete successfully.")
        st.stop()

    synth_df = pd.read_csv(result["synthetic_csv_path"])
    st.write(f"**{len(synth_df)} synthetic rows, {len(synth_df.columns)} columns**")
    st.dataframe(synth_df.head(50), use_container_width=True)

    st.subheader("Summary statistics")
    st.dataframe(synth_df.describe(include="all").transpose(), use_container_width=True)

    csv_bytes = synth_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download synthetic CSV", csv_bytes, file_name=f"{result['run_id']}.csv", mime="text/csv")

# ============================================================================
# PAGE: Fidelity
# ============================================================================
elif page == "Fidelity":
    st.title("Fidelity evaluation")

    if not st.session_state["last_generation"]:
        st.warning("Run at least one generator first.")
        st.stop()

    method = st.selectbox("Method", list(st.session_state["last_generation"].keys()), key="fid_method")
    result = st.session_state["last_generation"][method]
    if result["status"] != "completed":
        st.error("This run did not complete successfully.")
        st.stop()

    st.subheader("Summary metrics")
    st.json(result["fidelity"])

    st.subheader("Per-column marginal fidelity (recomputed for detail view)")
    synth_df = pd.read_csv(result["synthetic_csv_path"])
    real_cont = st.session_state["preprocessor"].transform_continuous(st.session_state["train_df"])
    marginal_report = fid_eval.marginal_fidelity_report(
        real_cont, synth_df, st.session_state["numerical_columns"], st.session_state["categorical_columns"]
    )
    st.dataframe(marginal_report, use_container_width=True)

    st.subheader("Out-of-range values (synthetic data validation)")
    oor = fid_eval.out_of_range_report(real_cont, synth_df, st.session_state["numerical_columns"])
    st.dataframe(oor, use_container_width=True)
    if len(oor) and (oor["pct_out_of_range"] > 5).any():
        st.caption(
            "Columns above ~5% out-of-range indicate the generator produced values outside "
            "the real training range (e.g. GAN/VAE mode-normalization on skewed columns) — "
            "an expected limitation to report, not silently clipped away."
        )

# ============================================================================
# PAGE: ML Utility
# ============================================================================
elif page == "ML Utility":
    st.title("Downstream ML utility: TSTR vs TRTR")

    if not st.session_state["last_generation"]:
        st.warning("Run at least one generator first.")
        st.stop()
    if st.session_state["trtr_results"] is None:
        st.warning("Compute the TRTR reference on the **Model Selection & Generate** page first.")
        st.stop()

    method = st.selectbox("Method", list(st.session_state["last_generation"].keys()), key="util_method")
    result = st.session_state["last_generation"][method]
    if result["status"] != "completed":
        st.error("This run did not complete successfully.")
        st.stop()

    trtr_df = pd.DataFrame(st.session_state["trtr_results"])
    tstr_df = pd.DataFrame(result["utility_tstr"])

    st.subheader("TRTR (real-data ceiling)")
    st.dataframe(trtr_df, use_container_width=True)
    st.subheader(f"TSTR ({method})")
    st.dataframe(tstr_df, use_container_width=True)

    merged = tstr_df.merge(trtr_df, on="model_name", suffixes=("_tstr", "_trtr"))
    merged["f1_utility_retention_pct"] = np.where(
        merged["f1_trtr"] > 0, 100 * merged["f1_tstr"] / merged["f1_trtr"], np.nan
    )
    st.subheader("Utility retention (F1)")
    st.dataframe(merged[["model_name", "f1_trtr", "f1_tstr", "f1_utility_retention_pct"]], use_container_width=True)

# ============================================================================
# PAGE: Privacy
# ============================================================================
elif page == "Privacy":
    st.title("Privacy evaluation")

    if not st.session_state["last_generation"]:
        st.warning("Run at least one generator first.")
        st.stop()

    method = st.selectbox("Method", list(st.session_state["last_generation"].keys()), key="priv_method")
    result = st.session_state["last_generation"][method]
    if result["status"] != "completed":
        st.error("This run did not complete successfully.")
        st.stop()

    st.subheader("Formal privacy guarantee")
    st.info(result["privacy_formal"]["formal_guarantee"])

    st.subheader("Empirical: membership inference attack")
    st.json(result["privacy_mia"])
    st.caption(
        "AUC near 0.5 = attack no better than random guessing (best case for privacy). "
        "This is a simple distance-based attack, chosen for transparency and auditability "
        "(see evaluation/privacy.py) — a stronger shadow-model attack could reveal more leakage."
    )

    st.subheader("Empirical: record similarity / near-duplicate check")
    st.json(result["privacy_record_similarity"])

# ============================================================================
# PAGE: Fairness / Rare Patterns
# ============================================================================
elif page == "Fairness / Rare Patterns":
    st.title("Fairness and rare-pattern preservation")

    if not st.session_state["last_generation"]:
        st.warning("Run at least one generator first.")
        st.stop()

    method = st.selectbox("Method", list(st.session_state["last_generation"].keys()), key="fair_method")
    result = st.session_state["last_generation"][method]
    if result["status"] != "completed":
        st.error("This run did not complete successfully.")
        st.stop()

    st.subheader("Rare pattern preservation")
    st.json(result["rare_patterns"])

    st.subheader("Fairness")
    if result["fairness"] is None:
        st.info(
            "No sensitive attribute with sufficient group sizes was configured for this "
            "dataset — the fairness module is disabled rather than forcing an irrelevant "
            "analysis (per project spec Section 13)."
        )
    elif "note" in result["fairness"]:
        st.warning(result["fairness"]["note"])
    else:
        f = result["fairness"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Demographic parity difference", f"{f['demographic_parity_difference']:.3f}")
        c2.metric("Equalized odds (max gap)", f"{f['equalized_odds']['max_gap']:.3f}")
        c3.metric("F1 performance gap", f"{f['f1_performance_gap']:.3f}" if f['f1_performance_gap'] is not None else "n/a")
        st.subheader("Subgroup performance")
        st.dataframe(pd.DataFrame(f["subgroup_performance"]), use_container_width=True)

# ============================================================================
# PAGE: Model Comparison
# ============================================================================
elif page == "Model Comparison":
    st.title("Model comparison — all logged experiments")

    all_results = load_all_results()
    if len(all_results) == 0:
        st.warning("No experiments logged yet. Run generators on the **Model Selection & Generate** page, "
                    "or run a full sweep via experiments/config.py + experiments/runner.py from the command line.")
        st.stop()

    completed = all_results[all_results["status"] == "completed"].copy()
    st.write(f"**{len(completed)} completed runs** out of {len(all_results)} logged.")

    if len(completed) == 0:
        st.warning(
            "No runs have completed successfully yet (logged runs so far all failed or are "
            "still in progress). Fix the failing run first, or wait for one to finish, then "
            "revisit this page."
        )
        with st.expander("Raw logged results (JSON)"):
            st.dataframe(all_results, use_container_width=True)
        st.stop()

    # Flatten key nested metrics for the summary table.
    def _extract(row):
        fid = row.get("fidelity") or {}
        tstr = row.get("utility_tstr") or []
        mia = row.get("privacy_mia") or {}
        best_f1 = max([m.get("f1", 0) for m in tstr], default=None)
        return pd.Series({
            "method": row["method"],
            "epsilon": row.get("epsilon"),
            "is_dp": row.get("is_differentially_private"),
            "mean_ks_statistic": fid.get("mean_ks_statistic"),
            "mean_tvd": fid.get("mean_tvd"),
            "three_way_mean_l1_error": fid.get("three_way_mean_l1_error"),
            "best_tstr_f1": best_f1,
            "attack_auc": mia.get("attack_auc"),
            "fit_runtime_seconds": row.get("fit_runtime_seconds"),
        })

    summary = completed.apply(_extract, axis=1)
    st.subheader("Summary table")
    st.dataframe(summary, use_container_width=True)

    st.caption(
        "No arbitrary weighted 'overall' score is computed here (per project spec Section 15) — "
        "trade-offs are shown directly so the reader draws their own conclusion for their priorities."
    )

    # --- AIM epsilon sweep charts, if present ---
    aim_runs = summary[summary["method"] == "AIM"].dropna(subset=["epsilon"]).sort_values("epsilon")
    if len(aim_runs) >= 2:
        st.subheader("Graph 1 & 2: Epsilon vs ML Utility / Fidelity (AIM)")
        col1, col2 = st.columns(2)
        with col1:
            st.line_chart(aim_runs.set_index("epsilon")[["best_tstr_f1"]])
            st.caption("Epsilon vs ML Utility (best TSTR F1)")
        with col2:
            st.line_chart(aim_runs.set_index("epsilon")[["mean_ks_statistic", "mean_tvd"]])
            st.caption("Epsilon vs Fidelity (lower = better)")

        st.subheader("Graph 3: Epsilon vs Privacy Risk (AIM)")
        st.line_chart(aim_runs.set_index("epsilon")[["attack_auc"]])
        st.caption("Attack AUC near 0.5 = low empirical risk; near 1.0 = high risk.")
    else:
        st.info("Run AIM at 2+ epsilon values to see the epsilon-sweep charts.")

    # --- DP method comparison at a shared epsilon ---
    dp_summary = summary[summary["is_dp"] == True]
    if len(dp_summary) >= 2:
        st.subheader("Graph 4: AIM vs MST vs PrivBayes")
        pivot = dp_summary.pivot_table(index="epsilon", columns="method", values="best_tstr_f1")
        st.line_chart(pivot)
        st.caption("TSTR F1 by epsilon, one line per DP method.")

    # --- All methods: fidelity vs utility scatter ---
    if len(summary) >= 2:
        st.subheader("Graph 5: All Methods — Fidelity vs Utility")
        st.scatter_chart(summary, x="mean_ks_statistic", y="best_tstr_f1", color="method")
        st.caption("Bottom-right is best: low fidelity error (KS statistic) and high TSTR F1.")

        st.subheader("Graph 6: Utility–Privacy Trade-off (Pareto view)")
        st.scatter_chart(summary, x="attack_auc", y="best_tstr_f1", color="method")
        st.caption("Bottom-left = safest but least useful; top-right = most useful but riskiest. "
                    "The Pareto frontier (non-dominated points) indicates the best available trade-offs.")

    with st.expander("Raw logged results (JSON)"):
        st.dataframe(all_results, use_container_width=True)
