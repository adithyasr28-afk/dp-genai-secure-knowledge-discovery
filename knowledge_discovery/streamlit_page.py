"""
knowledge_discovery/streamlit_page.py

The "LLM Knowledge Discovery" dashboard page. Kept in its own module so
app.py only needs a two-line hook and the original pages are untouched.
This page does not need the original dataset to be loaded: it works only
from saved DP synthetic datasets and the experiment log.
"""

from __future__ import annotations

import json

import streamlit as st

from knowledge_discovery.catalog import list_dp_synthetic_datasets, load_synthetic_dataset
from knowledge_discovery.llm_client import generate_insights, live_mode_available, model_for, resolve_provider
from knowledge_discovery.prompts import SYSTEM_PROMPT, build_user_message
from knowledge_discovery.summarizer import build_aggregate_summary


def render():
    st.title("LLM knowledge discovery on DP synthetic data")
    st.caption(
        "Extension module: summarises a saved **differentially private** synthetic dataset into "
        "aggregate statistics and asks an LLM to explain patterns, relationships, possible insights "
        "and limitations. The original dataset and individual records are never sent."
    )

    datasets = list_dp_synthetic_datasets()
    if not datasets:
        st.warning("No DP synthetic datasets found in results/synthetic_data/ with a completed log record. "
                   "Run AIM, MST or PrivBayes first.")
        return

    with st.expander("Privacy notes — read before use", expanded=False):
        st.markdown(
            "- Only DP synthetic datasets (AIM / MST / PrivBayes) are selectable; CTGAN/TVAE output has no "
            "formal guarantee and is excluded.\n"
            "- Analysing DP synthetic data is **post-processing**: it spends no additional privacy budget, "
            "provided the generator's DP guarantee and its assumptions hold (here: the preprocessing domain "
            "— bin edges and category vocabulary — is treated as public; see README).\n"
            "- The summary statistics are **not** a separate DP release, and the LLM adds **no** privacy "
            "guarantee. Cells with fewer than the minimum count are suppressed as defence in depth.\n"
            "- The optional *quality metrics* (fidelity, TSTR F1, MIA AUC) were computed by comparing the "
            "synthetic data with the **real** data. They are not covered by the DP guarantee. Untick "
            "*Include quality metrics* to send a payload computed from the DP synthetic data alone.\n"
            "- In live mode the summary is sent to the chosen provider's API (Anthropic or Google); your API key "
            "is never included in the prompt."
        )

    labels = [d.label for d in datasets]
    default_idx = next((i for i, d in enumerate(datasets) if d.method == "AIM" and d.epsilon == 3.0), 0)
    choice = st.selectbox("Synthetic dataset to analyse", labels, index=default_idx)
    info = datasets[labels.index(choice)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Generator", info.method)
    c2.metric("ε", f"{info.epsilon:g}")
    c3.metric("δ", "0 (pure DP)" if not info.delta else f"{info.delta:g}")
    c4.metric("Best TSTR F1", f"{info.best_tstr_f1:.3f}" if info.best_tstr_f1 is not None else "n/a")
    st.info(info.guarantee_statement or "No formal privacy statement recorded.")
    if info.n_log_records > 1:
        st.caption(f"This run_id has {info.n_log_records} completed log records; the latest one "
                   "(which produced the CSV on disk) is used.")

    col_a, col_b, col_c = st.columns(3)
    min_cell = col_a.number_input("Minimum cell count (smaller groups suppressed)", 5, 200, 20, 5)
    provider_labels = {"Auto (configured key)": None, "Claude (Anthropic)": "anthropic", "Gemini (Google)": "gemini"}
    provider_label = col_b.selectbox("LLM provider", list(provider_labels))
    provider = resolve_provider(provider_labels[provider_label])
    live_ok = live_mode_available(provider)
    modes = ["Live (LLM API)", "Demo (rule-based, no LLM)"]
    mode_label = col_c.radio("Mode", modes, index=0 if live_ok else 1, horizontal=True)
    mode = "live" if mode_label.startswith("Live") else "demo"
    key_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "GEMINI_API_KEY"
    if mode == "live":
        st.caption(f"Provider: **{provider}** · model `{model_for(provider)}` "
                   f"(override with {'KD_MODEL' if provider == 'anthropic' else 'KD_GEMINI_MODEL'})")
    if mode == "live" and not live_ok:
        st.error(f"{key_var} is not configured, so live mode will fail. Copy .env.example to .env and add the "
                 "key, choose the other provider, or switch to Demo mode.")
    if mode == "demo":
        st.warning("Demo mode produces a deterministic template explanation. It is **not** LLM output.")

    question = st.text_area("Optional analyst focus (do not paste personal data)", max_chars=500,
                            placeholder="e.g. Which attributes are most associated with high income, and how reliable is that?")

    df = load_synthetic_dataset(info)
    include_q = st.checkbox(
        "Include quality metrics (computed against the real data; not covered by DP)", value=True,
        help="Seven scalar metrics from the evaluation pipeline that help the LLM qualify its claims. "
             "They were computed by comparing the synthetic data with the real training/test data.")
    summary = build_aggregate_summary(df, info, target_column="income", min_cell_count=int(min_cell),
                                      include_quality_context=include_q)

    with st.expander("Exact payload that will be sent to the LLM", expanded=False):
        st.caption("Identical for both providers: system prompt followed by the user message.")
        st.code(SYSTEM_PROMPT, language="markdown")
        st.code(build_user_message(summary, question), language="json")
        st.download_button("Download summary JSON", json.dumps(summary, indent=2, default=str),
                           file_name=f"{info.run_id}_summary.json", mime="application/json")

    if st.button("Generate explanation", type="primary"):
        with st.spinner("Generating..." if mode == "demo" else f"Calling {provider}..."):
            result = generate_insights(summary, mode=mode, analyst_question=question, provider=provider)
        if not result.ok:
            st.error(result.error)
        else:
            header = (f"**LLM response** — {result.provider}, model `{result.model}`, stop_reason "
                      f"`{result.stop_reason}`, {result.elapsed_seconds}s. Treat every claim as a hypothesis; "
                      "synthetic data can contain artefacts (see report Section XIV)." if result.mode == "live"
                      else "**Demo output (not an LLM response)**")
            st.markdown(header)
            st.markdown(result.text)
        if result.audit_path:
            st.caption(f"Audit record written to `{result.audit_path}` (git-ignored).")
