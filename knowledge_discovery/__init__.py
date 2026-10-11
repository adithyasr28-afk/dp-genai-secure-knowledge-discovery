"""
knowledge_discovery/

LLM-based knowledge-discovery extension (added on top of the original
comparative study). It turns an already-generated DP synthetic dataset
into a compact, aggregate-only summary and asks an LLM (Claude, via the
Anthropic API) to explain the patterns, relationships, possible insights
and limitations visible in that summary.

Privacy design (see README "LLM knowledge-discovery extension"):
  - Only files under results/synthetic_data/ produced by a DP method
    (AIM / MST / PrivBayes) can be loaded; the original dataset path is
    refused explicitly.
  - Only aggregate statistics are sent -- never individual rows -- and
    any cell computed from fewer than `min_cell_count` synthetic rows is
    suppressed before it leaves the machine.
  - Analysing a DP synthetic dataset is post-processing of a DP output
    and spends no additional privacy budget *provided* the original DP
    guarantee and its assumptions hold. The LLM itself adds no DP
    guarantee, and the aggregates here are not separately DP.
"""

from knowledge_discovery.catalog import SyntheticDatasetInfo, list_dp_synthetic_datasets, load_synthetic_dataset
from knowledge_discovery.summarizer import build_aggregate_summary
from knowledge_discovery.llm_client import InsightResult, generate_insights, live_mode_available

__all__ = [
    "SyntheticDatasetInfo",
    "list_dp_synthetic_datasets",
    "load_synthetic_dataset",
    "build_aggregate_summary",
    "InsightResult",
    "generate_insights",
    "live_mode_available",
]
