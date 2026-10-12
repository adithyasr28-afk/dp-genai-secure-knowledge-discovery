"""
report/finalize.py

Builds the final report and fills the page numbers of the template's Index,
List of Figures and List of Tables from the rendered PDF:

  1. build report/final_report.docx (build_report.main);
  2. export it to PDF with Microsoft Word (PowerShell + COM; Windows only);
  3. locate every section heading, figure caption and table caption in the PDF;
  4. write report/page_map.json and rebuild, so the numbers appear in the tables;
  5. repeat until the page map no longer changes (normally 2 passes).

Page numbers are physical PDF pages, counted from the cover page = 1.

Run from the project root:  python report/finalize.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_report  # noqa: E402

DOCX = build_report.OUT_DOCX
PDF = DOCX.with_suffix(".pdf")
PAGE_MAP = HERE / "page_map.json"


def export_pdf() -> int:
    ps = f"""
$w = New-Object -ComObject Word.Application; $w.Visible = $false
try {{ $d = $w.Documents.Open('{DOCX}', $false, $true); $d.Fields.Update() | Out-Null
      $n = $d.ComputeStatistics(2); $d.ExportAsFixedFormat('{PDF}', 17); $d.Close($false); Write-Output $n }}
finally {{ $w.Quit() }}"""
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, check=True)
    return int(out.stdout.strip().splitlines()[-1])


def _norm(s: str) -> str:
    s = re.sub(r"\s+", " ", s.replace("\u00ad", "")).strip().upper()
    return s.replace("- ", "-")  # words hyphenated across a line break


def locate(toc, fig_list, tab_list) -> dict:
    doc = pymupdf.open(str(PDF))
    pages = [_norm(p.get_text()) for p in doc]
    # the body starts on the page with the paper's ABSTRACT / INDEX TERMS block
    start = next(i for i, t in enumerate(pages) if "INDEX TERMS" in t and "ABSTRACT" in t)
    found, missing = {}, []

    def search(key, needle, from_page):
        for i in range(from_page, len(pages)):
            if needle in pages[i]:
                found[key] = i + 1
                return i
        missing.append(key)
        return from_page

    found["toc:Abstract"] = start + 1
    cur = start
    for num, title in toc:
        label = f"{num}. {title}" if num else title
        cur = search(f"toc:{title}", _norm(label)[:40], cur)
    cur = start
    for n, title in fig_list:
        cap = re.sub(r"[*`]", "", title)
        cur = search(f"fig:{n}", _norm(f"Fig. {n}. {cap}")[:32], cur)
    cur = start
    for n, title in tab_list:
        cap = re.sub(r"[*`]", "", title)
        cur = search(f"tab:{n}", _norm(f"TABLE {n}. {cap}")[:28], cur)
    found["_pages"] = len(pages)
    found["_missing"] = missing
    return found


def main():
    previous = None
    for attempt in range(1, 5):
        md = build_report.main()
        resolved, fig_list, tab_list, toc = md
        n_pages = export_pdf()
        pm = locate(toc, fig_list, tab_list)
        print(f"pass {attempt}: {n_pages} pages, {len(pm) - 2} items located, missing: {pm['_missing']}")
        if previous is not None and {k: v for k, v in pm.items() if not k.startswith('_')} == \
                {k: v for k, v in previous.items() if not k.startswith('_')}:
            print("page map stable; final PDF:", PDF)
            return
        PAGE_MAP.write_text(json.dumps(pm, indent=1), encoding="utf-8")
        previous = pm
    print("WARNING: page map did not stabilise after 4 passes")


if __name__ == "__main__":
    main()
