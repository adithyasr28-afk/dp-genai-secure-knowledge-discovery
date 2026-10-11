"""
figures/diagram_builder.py

Generates the report's conceptual/architecture diagrams from one simple
specification per figure, exporting each as:
  - <name>.png    600 DPI raster (manuscript guideline: >= 600 DPI)
  - <name>.svg    vector version
  - <name>.drawio editable draw.io file with the same boxes and arrows, so
                  the team can restyle/redraw in draw.io as the guidelines ask.

Run from the project root:  python figures/diagram_builder.py
Coordinates are in a 100 x 60 canvas (x right, y down).
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent / "diagrams"
SCALE = 12  # canvas unit -> draw.io px

PALETTE = {
    "data": "#DCEBF7", "dp": "#D9F2E3", "ai": "#FCE8D5", "eval": "#EDE4F5",
    "gov": "#FFF4CC", "risk": "#F8D7DA", "neutral": "#F2F2F2", "future": "#E8E8E8",
}


@dataclass
class Node:
    id: str
    label: str
    x: float
    y: float
    w: float = 16
    h: float = 6
    kind: str = "neutral"
    dashed: bool = False


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    dashed: bool = False
    src_side: str = ""  # optional override: "left" | "right" | "top" | "bottom"


@dataclass
class Group:
    label: str
    x: float
    y: float
    w: float
    h: float
    kind: str = "neutral"


@dataclass
class Diagram:
    name: str
    title: str
    nodes: list
    edges: list = field(default_factory=list)
    groups: list = field(default_factory=list)
    width: float = 100
    height: float = 60
    legend: list = field(default_factory=list)


def _side_point(n: Node, side: str):
    return {"left": (n.x, n.y + n.h / 2), "right": (n.x + n.w, n.y + n.h / 2),
            "top": (n.x + n.w / 2, n.y), "bottom": (n.x + n.w / 2, n.y + n.h)}[side]


def _anchor(a: Node, b: Node, src_side: str = ""):
    if src_side:
        start = _side_point(a, src_side)
        end = _side_point(b, "left" if b.x >= a.x + a.w else "right" if b.x + b.w <= a.x else "top")
        return start, end
    ax, ay = a.x + a.w / 2, a.y + a.h / 2
    bx, by = b.x + b.w / 2, b.y + b.h / 2
    dx, dy = bx - ax, by - ay
    if abs(dx) * a.h > abs(dy) * a.w:
        start = (a.x + a.w if dx > 0 else a.x, ay)
        end = (b.x if dx > 0 else b.x + b.w, by)
    else:
        start = (ax, a.y + a.h if dy > 0 else a.y)
        end = (bx, b.y if dy > 0 else b.y + b.h)
    return start, end


def render_matplotlib(d: Diagram):
    fig_w = 7.16
    fig, ax = plt.subplots(figsize=(fig_w, fig_w * d.height / d.width))
    ax.set_xlim(0, d.width)
    ax.set_ylim(d.height, 0)
    ax.axis("off")
    plt.rcParams["font.family"] = "Arial"
    for g in d.groups:
        ax.add_patch(FancyBboxPatch((g.x, g.y), g.w, g.h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                    fc=PALETTE[g.kind], ec="#7F7F7F", lw=0.6, alpha=0.45, ls="--"))
        ax.text(g.x + 0.8, g.y + 1.6, g.label, fontsize=6.2, fontweight="bold", color="#404040", va="center")
    nodes = {n.id: n for n in d.nodes}
    for e in d.edges:
        a, b = nodes[e.src], nodes[e.dst]
        s, t = _anchor(a, b, e.src_side)
        ax.add_patch(FancyArrowPatch(s, t, arrowstyle="-|>", mutation_scale=7, lw=0.7, color="#404040",
                                     ls="--" if e.dashed else "-", shrinkA=0, shrinkB=0))
        if e.label:
            ax.text((s[0] + t[0]) / 2, (s[1] + t[1]) / 2 - 0.8, e.label, fontsize=5, ha="center", va="bottom",
                    color="#303030", bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.85))
    for n in d.nodes:
        ax.add_patch(FancyBboxPatch((n.x, n.y), n.w, n.h, boxstyle="round,pad=0.15,rounding_size=0.8",
                                    fc=PALETTE[n.kind], ec="#404040", lw=0.7, ls="--" if n.dashed else "-"))
        ax.text(n.x + n.w / 2, n.y + n.h / 2, n.label, fontsize=5.6, ha="center", va="center", wrap=True,
                linespacing=1.15)
    if d.legend:
        lx = 1
        for kind, text in d.legend:
            ax.add_patch(FancyBboxPatch((lx, d.height - 3.2), 2.2, 2, boxstyle="round,pad=0.1",
                                        fc=PALETTE[kind], ec="#404040", lw=0.5))
            ax.text(lx + 2.8, d.height - 2.2, text, fontsize=5.2, va="center")
            lx += 3.6 + len(text) * 0.95
    fig.tight_layout(pad=0.1)
    fig.savefig(OUT / f"{d.name}.png", dpi=600)
    fig.savefig(OUT / f"{d.name}.svg")
    plt.close(fig)


def render_drawio(d: Diagram):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for i, g in enumerate(d.groups):
        style = (f"rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor={PALETTE[g.kind]};opacity=50;"
                 "strokeColor=#7F7F7F;verticalAlign=top;align=left;spacingLeft=6;fontStyle=1;fontSize=11;")
        cells.append(f'<mxCell id="g{i}" value="{html.escape(g.label)}" style="{style}" vertex="1" parent="1">'
                     f'<mxGeometry x="{g.x*SCALE:.0f}" y="{g.y*SCALE:.0f}" width="{g.w*SCALE:.0f}" '
                     f'height="{g.h*SCALE:.0f}" as="geometry"/></mxCell>')
    for n in d.nodes:
        style = (f"rounded=1;whiteSpace=wrap;html=1;fillColor={PALETTE[n.kind]};strokeColor=#404040;"
                 f"fontSize=11;{'dashed=1;' if n.dashed else ''}")
        label = html.escape(n.label).replace("\n", "&lt;br&gt;")
        cells.append(f'<mxCell id="{n.id}" value="{label}" style="{style}" vertex="1" parent="1">'
                     f'<mxGeometry x="{n.x*SCALE:.0f}" y="{n.y*SCALE:.0f}" width="{n.w*SCALE:.0f}" '
                     f'height="{n.h*SCALE:.0f}" as="geometry"/></mxCell>')
    for i, e in enumerate(d.edges):
        style = f"endArrow=block;html=1;rounded=0;fontSize=9;{'dashed=1;' if e.dashed else ''}"
        cells.append(f'<mxCell id="e{i}" value="{html.escape(e.label)}" style="{style}" edge="1" parent="1" '
                     f'source="{e.src}" target="{e.dst}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml = (f'<mxfile host="diagram_builder.py"><diagram name="{html.escape(d.title)}" id="{d.name}">'
           f'<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" page="1" pageWidth="{d.width*SCALE:.0f}" '
           f'pageHeight="{d.height*SCALE:.0f}"><root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>')
    (OUT / f"{d.name}.drawio").write_text(xml, encoding="utf-8")


# ---------------------------------------------------------------------------
# Figure specifications. "dashed" nodes = proposed / not implemented.
# ---------------------------------------------------------------------------
def diagrams():
    D = []
    impl_legend = [("data", "Data"), ("dp", "DP mechanism"), ("ai", "Generative AI / LLM"),
                   ("eval", "Evaluation"), ("gov", "Governance")]

    D.append(Diagram("fig01_genai_privacy_risk_landscape", "Generative AI privacy risk landscape", nodes=[
        Node("core", "Generative AI system\n(training data, model,\nprompts, outputs)", 40, 24, 20, 10, "ai"),
        Node("mem", "Training-data\nmemorisation & extraction", 4, 6, 20, 7, "risk"),
        Node("mia", "Membership\ninference", 40, 4, 20, 7, "risk"),
        Node("inv", "Model inversion /\nattribute inference", 76, 6, 20, 7, "risk"),
        Node("pi", "Prompt injection &\ncontext leakage", 4, 30, 20, 7, "risk"),
        Node("rag", "Retrieval-store\nleakage (RAG)", 76, 30, 20, 7, "risk"),
        Node("over", "Uncontrolled knowledge\nextraction / over-sharing", 22, 46, 22, 7, "risk"),
        Node("bias", "Bias amplification &\nrare-group erasure", 56, 46, 22, 7, "risk"),
    ], edges=[Edge("core", t) for t in ["mem", "mia", "inv", "pi", "rag", "over", "bias"]]))

    D.append(Diagram("fig02_secure_knowledge_discovery_ecosystem", "Secure knowledge discovery ecosystem", nodes=[
        Node("own", "Data owners /\ndata subjects", 2, 8, 15, 7, "data"),
        Node("cust", "Data custodian\n(trusted curator)", 22, 8, 16, 7, "gov"),
        Node("dp", "DP synthetic data\ngeneration", 44, 8, 16, 7, "dp"),
        Node("rel", "Released DP\nsynthetic dataset", 66, 8, 16, 7, "dp"),
        Node("kd", "LLM knowledge-\ndiscovery layer", 66, 26, 16, 7, "ai"),
        Node("an", "Analysts /\ndecision makers", 66, 44, 16, 7, "neutral"),
        Node("ml", "Downstream ML\n(TSTR)", 86, 8, 12, 7, "eval"),
        Node("gov", "Governance: budget ledger,\naudit log, policy, DPIA", 22, 28, 22, 8, "gov"),
        Node("reg", "Regulators /\nethics board", 22, 46, 16, 7, "gov"),
    ], edges=[Edge("own", "cust", "raw data"), Edge("cust", "dp", "ε, δ"), Edge("dp", "rel"),
              Edge("rel", "ml"), Edge("rel", "kd", "aggregates only"), Edge("kd", "an", "explanations"),
              Edge("gov", "cust", dashed=True), Edge("gov", "kd", dashed=True), Edge("reg", "gov", dashed=True)]))

    D.append(Diagram("fig02b_requirements_framework", "Requirements framework", nodes=[
        Node("goal", "Goal: useful knowledge from sensitive tabular data\nwithout exposing individuals", 25, 2, 50, 8, "neutral"),
        Node("fr", "Functional\nFR1–FR6", 2, 18, 15, 7, "data"),
        Node("pr", "Privacy\nPR1–PR5", 19, 18, 15, 7, "dp"),
        Node("sr", "Security\nSR1–SR4", 36, 18, 15, 7, "risk"),
        Node("xr", "Explainability\nXR1–XR3", 53, 18, 15, 7, "ai"),
        Node("cr", "Compliance\nCR1–CR3", 70, 18, 13, 7, "gov"),
        Node("tr", "Trust\nTR1–TR3", 85, 18, 13, 7, "eval"),
        Node("ver", "Verification: tests (pytest), re-evaluation of saved results,\nconfiguration checks, payload inspection", 15, 34, 70, 8, "eval"),
        Node("ev", "Evidence in report: traceability matrix, results tables, audit records", 15, 47, 70, 7, "gov"),
    ], edges=[Edge("goal", n) for n in ["fr", "pr", "sr", "xr", "cr", "tr"]] +
              [Edge(n, "ver") for n in ["fr", "pr", "sr", "xr", "cr", "tr"]] + [Edge("ver", "ev")]))

    D.append(Diagram("fig03_data_lifecycle_privacy_classification", "Data lifecycle and privacy classification", nodes=[
        Node("c", "Collect\n(UCI Adult sample)", 2, 6, 14, 7, "data"),
        Node("cl", "Classify\n(levels L1–L3)", 19, 6, 14, 7, "gov"),
        Node("p", "Prepare\n(split, bin, group)", 36, 6, 14, 7, "data"),
        Node("s", "Synthesise\n(DP / non-DP)", 53, 6, 14, 7, "dp"),
        Node("e", "Evaluate\n(6 dimensions)", 70, 6, 14, 7, "eval"),
        Node("r", "Release / analyse\n(LLM layer)", 84, 20, 14, 7, "ai"),
        Node("a", "Archive / retain\n(results/)", 62, 34, 16, 7, "gov"),
        Node("d", "Dispose\n(raw data off repo\nin production)", 40, 34, 16, 7, "gov", dashed=True),
        Node("l1", "L3 Restricted: raw records with\nquasi-identifiers + sensitive attributes", 2, 46, 30, 7, "risk"),
        Node("l2", "L2 Internal: DP synthetic data,\naggregates, metrics", 35, 46, 30, 7, "dp"),
        Node("l3", "L1 Public: code, configs,\nreport, documentation", 68, 46, 30, 7, "neutral"),
    ], edges=[Edge("c", "cl"), Edge("cl", "p"), Edge("p", "s"), Edge("s", "e"), Edge("e", "r"),
              Edge("r", "a"), Edge("a", "d")]))

    D.append(Diagram("fig04_threat_model", "Threat model and attack surface", nodes=[
        Node("raw", "Real training split\n(n = 2,400)", 2, 24, 16, 7, "data"),
        Node("gen", "Generator\n(AIM / MST / PrivBayes;\nCTGAN / TVAE)", 26, 22, 18, 11, "dp"),
        Node("syn", "Released synthetic\ndataset", 52, 24, 16, 7, "dp"),
        Node("llm", "LLM API\n(third party)", 78, 24, 16, 7, "ai"),
        Node("a1", "A1 Membership inference\n(1-NN distance attack)", 46, 4, 26, 7, "risk"),
        Node("a2", "A2 Linkage / attribute\ninference on synthetic rows", 46, 42, 26, 7, "risk"),
        Node("a3", "A3 Provider-side exposure\nof prompts", 74, 42, 24, 7, "risk"),
        Node("a4", "A4 Insider / misconfiguration\n(raw data or keys in repo)", 2, 42, 26, 7, "risk"),
        Node("a5", "A5 Prompt injection via\ndata values", 74, 4, 24, 7, "risk"),
    ], edges=[Edge("raw", "gen", "fit"), Edge("gen", "syn", "sample"), Edge("syn", "llm", "summary"),
              Edge("a1", "syn", dashed=True), Edge("a2", "syn", dashed=True), Edge("a3", "llm", dashed=True),
              Edge("a4", "raw", dashed=True), Edge("a5", "llm", dashed=True)]))

    D.append(Diagram("fig05_framework_architecture", "Implemented DP-enhanced generative AI framework", groups=[
        Group("L1 Data & preparation layer", 1, 3, 30, 50, "data"),
        Group("L2 DP synthesis layer", 34, 3, 30, 50, "dp"),
        Group("L3 Evaluation & knowledge-discovery layer", 67, 3, 32, 50, "eval"),
    ], nodes=[
        Node("ds", "Dataset loader &\nprofiler (schema.py)", 4, 8, 24, 6, "data"),
        Node("sp", "Stratified train/test\nsplit (80/20, seed 42)", 4, 17, 24, 6, "data"),
        Node("pp", "Leakage-safe preprocessing\n(bins, rare groups, imputation)\nfit on train split only", 4, 26, 24, 9, "data"),
        Node("par", "Fitted parameters (JSON):\nbin edges, spike values,\nvocabularies, medians", 4, 40, 24, 9, "gov"),
        Node("aim", "AIM (ε, δ)\nrounds ≤ 60", 37, 8, 11, 6, "dp"),
        Node("mst", "MST (ε, δ)", 37, 26, 11, 6, "dp"),
        Node("pb", "PrivBayes\npure ε", 37, 17, 11, 6, "dp"),
        Node("ct", "CTGAN / TVAE\n(non-DP)", 37, 41, 11, 7, "neutral"),
        Node("inv", "Inverse binning\n(uniform in bin)", 51, 17, 12, 7, "dp"),
        Node("store", "results/:\nJSONL log +\nsynthetic CSVs", 51, 39, 12, 10, "gov"),
        Node("ev", "Fidelity · Utility · Privacy\nFairness · Rare patterns · Runtime", 70, 8, 26, 8, "eval"),
        Node("dash", "Streamlit dashboard\n(9 pages + extension)", 70, 20, 26, 6, "eval"),
        Node("kd", "LLM knowledge discovery\n(aggregate summary → Claude)", 70, 31, 26, 7, "ai"),
        Node("aud", "Audit log + demo/live\nlabelling", 70, 43, 26, 6, "gov"),
    ], edges=[Edge("ds", "sp"), Edge("sp", "pp"), Edge("pp", "par"),
              Edge("pp", "aim", "discretised", src_side="right"), Edge("pp", "pb", src_side="right"),
              Edge("pp", "mst", src_side="right"), Edge("pp", "ct", "continuous", src_side="right"), Edge("aim", "inv"), Edge("pb", "inv"),
              Edge("mst", "inv"), Edge("inv", "store"), Edge("ct", "store"), Edge("store", "ev"),
              Edge("ev", "dash"), Edge("store", "kd", "DP runs only"), Edge("kd", "aud")],
        legend=impl_legend))

    D.append(Diagram("fig06_privacy_aware_preprocessing_pipeline", "Privacy-aware data preparation pipeline", nodes=[
        Node("in", "Raw CSV\n(3,000 × 14)", 2, 10, 13, 7, "data"),
        Node("prof", "Profile: types,\ncardinality, missing", 18, 10, 14, 7, "data"),
        Node("roles", "Assign roles:\ntarget, sensitive,\nexcluded", 35, 10, 14, 7, "gov"),
        Node("split", "Split first\n(train only fits)", 52, 10, 14, 7, "gov"),
        Node("imp", "Median impute +\nmissing flags", 69, 4, 14, 6, "data"),
        Node("rare", "Rare categories\n(< 1%) → __RARE__", 69, 13, 14, 6, "data"),
        Node("bin", "Quantile bins (10)\n+ spike bin", 69, 22, 14, 6, "data"),
        Node("dview", "Discretised →\nDP methods", 86, 22, 13, 6, "dp"),
        Node("cview", "Continuous →\nCTGAN / TVAE", 86, 4, 13, 6, "neutral"),
        Node("note", "Caveat: bin edges and vocabularies are learned from the real\ntraining split without DP budget (preprocessor_eps = 0); the formal\nguarantee therefore treats this domain as public.",
             18, 36, 64, 10, "risk"),
    ], edges=[Edge("in", "prof"), Edge("prof", "roles"), Edge("roles", "split"), Edge("split", "imp"),
              Edge("split", "rare"), Edge("split", "bin"), Edge("bin", "dview"), Edge("imp", "cview"),
              Edge("bin", "note", dashed=True)]))

    D.append(Diagram("fig07_dp_integration_workflow", "DP integration workflow", groups=[
        Group("Implemented: select–measure–generate (AIM / MST) and Bayesian-network synthesis (PrivBayes)", 1, 2, 98, 30, "dp"),
        Group("Discussed only (not implemented): DP-SGD for neural generators / LLM fine-tuning", 1, 36, 98, 20, "future"),
    ], nodes=[
        Node("bud", "Budget (ε, δ)\nfixed per run", 3, 10, 14, 7, "gov"),
        Node("sel", "Select marginals\n(MST: spanning tree;\nAIM: adaptive, exp. mech.)", 21, 9, 20, 9, "dp"),
        Node("meas", "Measure with\nGaussian noise\n(zCDP accounting)", 45, 9, 17, 9, "dp"),
        Node("pgm", "Private-PGM\nestimation", 66, 10, 14, 7, "dp"),
        Node("samp", "Sample synthetic\nrecords", 83, 10, 14, 7, "dp"),
        Node("pbn", "PrivBayes: exp. mechanism on network,\nLaplace on conditionals (pure ε-DP)", 30, 22, 40, 7, "dp"),
        Node("clip", "Per-example\ngradient clipping (C)", 6, 44, 18, 7, "future", dashed=True),
        Node("noise", "Add N(0, σ²C²I)", 30, 44, 16, 7, "future", dashed=True),
        Node("acc", "RDP / PRV\naccountant", 52, 44, 16, 7, "future", dashed=True),
        Node("upd", "Model update", 74, 44, 16, 7, "future", dashed=True),
    ], edges=[Edge("bud", "sel"), Edge("sel", "meas"), Edge("meas", "pgm"), Edge("pgm", "samp"),
              Edge("meas", "sel", "AIM: repeat ≤ 60 rounds", dashed=True),
              Edge("clip", "noise", dashed=True), Edge("noise", "acc", dashed=True), Edge("acc", "upd", dashed=True)]))

    D.append(Diagram("fig08_llm_knowledge_discovery_workflow", "LLM knowledge-discovery workflow (implemented)", nodes=[
        Node("cat", "Catalogue DP runs\n(log: completed, DP,\nlatest record)", 2, 6, 17, 9, "gov"),
        Node("load", "Load synthetic CSV\n(path guard: only\nresults/synthetic_data)", 22, 6, 18, 9, "dp"),
        Node("agg", "Aggregate summary:\nmarginals, target rates,\nassociations, quality", 43, 6, 18, 9, "eval"),
        Node("sup", "Small-cell suppression\n(k ≥ 20) + rounding", 43, 22, 18, 7, "gov"),
        Node("prm", "Prompt template\n(kd-prompt-v1)", 64, 6, 15, 9, "ai"),
        Node("mode", "Mode?", 83, 6, 14, 9, "neutral"),
        Node("live", "Live: Claude API\n(claude-opus-5-5)", 83, 24, 14, 9, "ai"),
        Node("demo", "Demo: rule-based\ntemplate (labelled\nNOT LLM output)", 64, 24, 15, 9, "neutral"),
        Node("ui", "Dashboard: payload\n+ response shown", 55, 40, 22, 8, "eval"),
        Node("aud", "Audit JSON:\nprompt, hash, mode,\nmodel, usage", 22, 40, 18, 8, "gov"),
        Node("orig", "Original dataset\n(never read)", 2, 24, 15, 7, "risk", dashed=True),
    ], edges=[Edge("cat", "load"), Edge("load", "agg"), Edge("agg", "sup"), Edge("sup", "prm"),
              Edge("prm", "mode"), Edge("mode", "live", "key set"), Edge("mode", "demo", "no key", dashed=True),
              Edge("live", "ui"), Edge("demo", "ui"), Edge("ui", "aud"),
              Edge("orig", "load", "blocked", dashed=True)], height=52))

    D.append(Diagram("fig09_explainability_trust_layer", "Explainability, transparency and trust layer", nodes=[
        Node("t1", "Formal statement\n(ε, δ, mechanism,\npure vs approx.)", 2, 6, 18, 9, "dp"),
        Node("t2", "Empirical evidence\n(MIA AUC, DCR,\nnear-duplicates)", 22, 6, 18, 9, "eval"),
        Node("t3", "Quality evidence\n(fidelity, TSTR,\nrare patterns, fairness)", 42, 6, 18, 9, "eval"),
        Node("t4", "Provenance\n(run_id, seed, config,\ndisclosed deviations)", 62, 6, 18, 9, "gov"),
        Node("t5", "LLM transparency\n(payload shown, prompt\nversion, audit hash)", 82, 6, 16, 9, "ai"),
        Node("trust", "Evidence-based trust assessment — indicators reported side by side,\nno single opaque score", 10, 26, 80, 8, "gov"),
        Node("user", "Analyst / reviewer decision: use, re-tune ε, or reject", 25, 42, 50, 7, "neutral"),
    ], edges=[Edge(n, "trust") for n in ["t1", "t2", "t3", "t4", "t5"]] + [Edge("trust", "user")]))

    D.append(Diagram("fig10_experimental_evaluation_framework", "Experimental evaluation framework", nodes=[
        Node("cfg", "SweepConfig\n41 runs", 2, 22, 13, 7, "gov"),
        Node("dp", "DP: AIM (5 ε × 1 seed)\nMST, PrivBayes (5 ε × 3 seeds)", 18, 12, 24, 8, "dp"),
        Node("ndp", "Non-DP: CTGAN, TVAE\n(300 epochs × 3 seeds)", 18, 30, 24, 8, "neutral"),
        Node("syn", "Synthetic data\n(2,400 rows each)", 46, 22, 15, 7, "dp"),
        Node("f", "Fidelity: KS, W1, TVD,\nJSD, ΔCorr, ΔCramér V, 3-way", 65, 2, 33, 7, "eval"),
        Node("u", "Utility: TSTR vs TRTR\n(LR, RF, XGBoost)", 65, 11, 33, 6, "eval"),
        Node("p", "Privacy: formal (ε, δ) + MIA AUC,\nTPR@FPR 0.1, DCR", 65, 19, 33, 7, "eval"),
        Node("r", "Rare patterns: categories,\n2-way combinations, minority class", 65, 28, 33, 7, "eval"),
        Node("fa", "Fairness (sex): DP difference,\nequalised odds, F1 gap", 65, 37, 33, 7, "eval"),
        Node("rt", "Runtime: fit / generate", 65, 46, 33, 5, "eval"),
        Node("ver", "verify_results.py:\nde-dup, re-evaluate,\naggregate", 40, 44, 20, 9, "gov"),
    ], edges=[Edge("cfg", "dp"), Edge("cfg", "ndp"), Edge("dp", "syn"), Edge("ndp", "syn")] +
              [Edge("syn", t) for t in ["f", "u", "p", "r", "fa", "rt"]] + [Edge("syn", "ver", dashed=True)]))

    D.append(Diagram("fig12_compliance_governance_mapping", "Compliance and governance mapping", nodes=[
        Node("g1", "GDPR (EU 2016/679)\nArt. 5, 25, 35; Recital 26", 2, 4, 22, 7, "gov"),
        Node("g2", "India DPDP Act 2023", 2, 13, 22, 6, "gov"),
        Node("g3", "HIPAA de-identification\n(45 CFR 164.514)", 2, 21, 22, 7, "gov"),
        Node("g4", "CCPA / CPRA", 2, 30, 22, 6, "gov"),
        Node("g5", "EU AI Act (2024/1689)", 2, 38, 22, 6, "gov"),
        Node("g6", "NIST PF 1.0 · AI RMF 1.0\nSP 800-226 · ISO/IEC 27701, 42001", 2, 46, 22, 8, "gov"),
        Node("c1", "Data minimisation &\npurpose limitation", 38, 4, 22, 7, "neutral"),
        Node("c2", "Privacy by design\n(DP at generation)", 38, 14, 22, 7, "dp"),
        Node("c3", "Risk assessment / DPIA\n(threat model, MIA)", 38, 24, 22, 7, "eval"),
        Node("c4", "Transparency & records\n(logs, audit JSON)", 38, 34, 22, 7, "gov"),
        Node("c5", "Human oversight of\nLLM explanations", 38, 44, 22, 7, "ai"),
        Node("i1", "Implemented controls:\nDP generators, path guards,\nsmall-cell suppression,\n.env secrets, audit log", 74, 10, 24, 14, "dp"),
        Node("i2", "Organisational controls\n(not implemented):\nDPO sign-off, consent records,\nretention schedule", 74, 32, 24, 14, "future", dashed=True),
    ], edges=[Edge("g1", "c1"), Edge("g1", "c2"), Edge("g1", "c3"), Edge("g2", "c1"), Edge("g3", "c3"),
              Edge("g4", "c4"), Edge("g5", "c4"), Edge("g5", "c5"), Edge("g6", "c3"), Edge("g6", "c5"),
              Edge("c1", "i1"), Edge("c2", "i1"), Edge("c3", "i1"), Edge("c4", "i2"), Edge("c5", "i2")]))

    D.append(Diagram("fig13_domain_deployment_architecture", "Proposed domain-specific deployment architecture", groups=[
        Group("Trusted zone (data custodian, e.g. hospital or bank)", 1, 3, 46, 50, "data"),
        Group("Shared / analyst zone", 52, 3, 47, 50, "neutral"),
    ], nodes=[
        Node("src", "Source systems\n(EHR / core banking)", 4, 9, 18, 7, "data"),
        Node("prep", "Preparation with DP\ndomain discovery", 26, 9, 18, 7, "dp", dashed=True),
        Node("gen", "DP generator\n(AIM / MST)", 26, 22, 18, 7, "dp"),
        Node("led", "Privacy budget ledger\n(per dataset, per release)", 4, 22, 18, 7, "gov", dashed=True),
        Node("rev", "Release review\n(DPO / ethics)", 15, 37, 18, 7, "gov", dashed=True),
        Node("cat", "Synthetic data\ncatalogue", 56, 22, 18, 7, "dp"),
        Node("kd", "LLM knowledge-\ndiscovery service", 78, 22, 18, 7, "ai"),
        Node("bi", "BI / ML teams", 56, 37, 18, 7, "eval"),
        Node("llm", "LLM provider\n(contract, no-train,\nregion controls)", 78, 37, 18, 9, "ai", dashed=True),
    ], edges=[Edge("src", "prep"), Edge("prep", "gen"), Edge("led", "gen", dashed=True), Edge("gen", "rev"),
              Edge("rev", "cat", "approved"), Edge("cat", "kd"), Edge("cat", "bi"), Edge("kd", "llm", "aggregates")]))

    D.append(Diagram("fig14_trustworthy_lifecycle", "Trustworthy privacy-preserving generative AI lifecycle", nodes=[
        Node(f"s{i}", t, 2 + i * 14, 20, 12, 10, k) for i, (t, k) in enumerate([
            ("Plan\n(purpose, DPIA,\nbudget)", "gov"), ("Prepare\n(classify,\nminimise)", "data"),
            ("Generate\n(DP\nmechanism)", "dp"), ("Validate\n(6 eval\ndimensions)", "eval"),
            ("Explain\n(LLM + human\nreview)", "ai"), ("Release\n(catalogue,\nlicence)", "gov"),
            ("Monitor\n(re-audit,\nretire)", "gov")])
    ], edges=[Edge(f"s{i}", f"s{i+1}") for i in range(6)] + [Edge("s6", "s0", "feedback", dashed=True)]))

    D.append(Diagram("fig15_future_research_roadmap", "Future research roadmap", groups=[
        Group("Near term (next iteration of this project)", 1, 3, 32, 52, "dp"),
        Group("Medium term", 34, 3, 32, 52, "eval"),
        Group("Long term", 67, 3, 32, 52, "future"),
    ], nodes=[
        Node("n1", "DP domain discovery\n(spend budget on bins)", 4, 10, 26, 7, "dp"),
        Node("n2", "Full AIM rounds + 3 seeds;\nsecond (healthcare) dataset", 4, 21, 26, 8, "dp"),
        Node("n3", "Stronger MIAs (shadow /\nDOMIAS-style) and auditing", 4, 33, 26, 8, "eval"),
        Node("m1", "DP-SGD baselines\n(DP-CTGAN, DP-TVAE)", 37, 10, 26, 7, "dp"),
        Node("m2", "Adaptive budget allocation\nacross releases", 37, 21, 26, 8, "gov"),
        Node("m3", "LLM evaluation: factuality vs\nsummary, hallucination rate", 37, 33, 26, 8, "ai"),
        Node("l1", "Privacy-preserving foundation\nmodels for tabular data", 70, 10, 26, 7, "ai"),
        Node("l2", "Agentic AI governance\n(tool-use budgets)", 70, 21, 26, 8, "gov"),
        Node("l3", "Post-quantum secure\ndata-sharing pipelines", 70, 33, 26, 8, "future"),
    ], edges=[Edge("n1", "m2"), Edge("n2", "m1"), Edge("n3", "m3"), Edge("m1", "l1"), Edge("m2", "l2"),
              Edge("m3", "l2")]))
    return D


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for d in diagrams():
        render_matplotlib(d)
        render_drawio(d)
        print("wrote", d.name)


if __name__ == "__main__":
    main()
