"""
analysis/quasi_identifier_risk.py

How identifying is the REAL sample on its quasi-identifiers? For growing
sets of quasi-identifiers, count the equivalence classes, the records that
are unique in the sample (class size 1) and the records in classes smaller
than 5 (the usual k-anonymity threshold). Used in report Sections V-VI to
justify treating the real data as Restricted (L3).

This reads the real data and writes only the local results/verified/ folder;
nothing is sent anywhere.

Run from the project root:  python -m analysis.quasi_identifier_risk
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
QI_SETS = [
    ["age", "sex", "race"],
    ["age", "sex", "race", "native_country"],
    ["age", "sex", "race", "native_country", "occupation"],
    ["age", "sex", "race", "native_country", "occupation", "marital_status"],
]


def main():
    df = pd.read_csv(ROOT / "data" / "example_dataset.csv")
    n = len(df)
    rows = []
    for qi in QI_SETS:
        sizes = df.groupby(qi, dropna=False).size()
        rows.append({
            "quasi_identifiers": " + ".join(qi),
            "n_records": n,
            "equivalence_classes": len(sizes),
            "unique_records": int((sizes == 1).sum()),
            "pct_unique": round(100 * (sizes == 1).sum() / n, 1),
            "records_in_classes_below_5": int(sizes[sizes < 5].sum()),
            "pct_in_classes_below_5": round(100 * sizes[sizes < 5].sum() / n, 1),
        })
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results" / "verified" / "quasi_identifier_uniqueness.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
