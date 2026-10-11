"""
knowledge_discovery/catalog.py

Finds the DP synthetic datasets that are eligible for LLM analysis and
loads one of them, with hard guards so that the original (real) dataset
or a non-DP synthetic dataset can never be passed to the LLM pipeline by
mistake.

Eligibility rules:
  1. The file must live directly inside results/synthetic_data/.
  2. Its run_id must map to a COMPLETED record in
     results/experiment_results.jsonl whose method is a DP method
     (AIM / MST / PrivBayes) and whose is_differentially_private flag is
     true. The privacy parameters shown to the user and the LLM are taken
     from that record, never inferred from the filename alone.
  3. When a run_id appears more than once in the log (the project log has
     two such re-runs), the LATEST completed record is used, because the
     synthetic CSV on disk was overwritten by that later run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_DIR = PROJECT_ROOT / "results" / "synthetic_data"
RESULTS_LOG = PROJECT_ROOT / "results" / "experiment_results.jsonl"
ORIGINAL_DATA_DIR = PROJECT_ROOT / "data"

DP_METHODS = {"AIM", "MST", "PrivBayes"}


class IneligibleDatasetError(ValueError):
    """Raised when a caller tries to load something that is not a DP synthetic dataset."""


@dataclass
class SyntheticDatasetInfo:
    run_id: str
    method: str
    epsilon: Optional[float]
    delta: Optional[float]
    random_seed: Optional[int]
    csv_path: Path
    mechanism: str = ""
    guarantee_statement: str = ""
    extra_privacy_notes: dict = field(default_factory=dict)
    fidelity: dict = field(default_factory=dict)
    best_tstr_f1: Optional[float] = None
    mia_auc: Optional[float] = None
    n_log_records: int = 1

    @property
    def label(self) -> str:
        delta_part = "pure ε-DP, δ=0" if not self.delta else f"δ={self.delta:g}"
        return f"{self.method} | ε={self.epsilon:g} ({delta_part}) | seed {self.random_seed}"


def _latest_completed_records(results_log: Path) -> dict:
    """run_id -> (latest completed record, number of completed records for that run_id)."""
    latest: dict = {}
    counts: dict = {}
    if not results_log.exists():
        return {}
    with open(results_log, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("status") != "completed":
                continue
            rid = rec.get("run_id")
            counts[rid] = counts.get(rid, 0) + 1
            prev = latest.get(rid)
            if prev is None or str(rec.get("timestamp", "")) >= str(prev.get("timestamp", "")):
                latest[rid] = rec
    return {rid: (rec, counts[rid]) for rid, rec in latest.items()}


def list_dp_synthetic_datasets(
    synthetic_dir: Path = SYNTHETIC_DIR, results_log: Path = RESULTS_LOG
) -> list:
    """Every eligible DP synthetic CSV, sorted by method then epsilon then seed."""
    records = _latest_completed_records(results_log)
    out = []
    for csv_path in sorted(Path(synthetic_dir).glob("*.csv")):
        rid = csv_path.stem
        if rid not in records:
            continue
        rec, n = records[rid]
        if rec.get("method") not in DP_METHODS or not rec.get("is_differentially_private"):
            continue
        pp = rec.get("privacy_params") or {}
        tstr = rec.get("utility_tstr") or []
        f1s = [m.get("f1") for m in tstr if m.get("f1") is not None]
        out.append(SyntheticDatasetInfo(
            run_id=rid,
            method=rec["method"],
            epsilon=pp.get("epsilon", rec.get("epsilon")),
            delta=pp.get("delta", rec.get("delta")),
            random_seed=rec.get("random_seed"),
            csv_path=csv_path,
            mechanism=pp.get("mechanism", ""),
            guarantee_statement=(rec.get("privacy_formal") or {}).get("formal_guarantee", ""),
            extra_privacy_notes={k: v for k, v in pp.items() if k in ("rounds_cap_applied", "note")},
            fidelity=rec.get("fidelity") or {},
            best_tstr_f1=max(f1s) if f1s else None,
            mia_auc=(rec.get("privacy_mia") or {}).get("attack_auc"),
            n_log_records=n,
        ))
    out.sort(key=lambda d: (d.method, d.epsilon or 0, d.random_seed or 0))
    return out


def _assert_eligible_path(csv_path: Path, synthetic_dir: Path) -> Path:
    resolved = Path(csv_path).resolve()
    if resolved.parent != Path(synthetic_dir).resolve():
        raise IneligibleDatasetError(
            f"Refusing to load '{csv_path}': only files directly inside "
            f"{synthetic_dir} can be sent to the LLM pipeline."
        )
    if ORIGINAL_DATA_DIR.resolve() in resolved.parents:
        raise IneligibleDatasetError("Refusing to load the original (real) dataset.")
    return resolved


def load_synthetic_dataset(info: SyntheticDatasetInfo, synthetic_dir: Path = SYNTHETIC_DIR) -> pd.DataFrame:
    """Load the CSV behind a catalog entry after re-checking eligibility."""
    if info.method not in DP_METHODS:
        raise IneligibleDatasetError(f"{info.method} is not a DP method; refusing to analyse it with the LLM.")
    path = _assert_eligible_path(info.csv_path, synthetic_dir)
    return pd.read_csv(path)
