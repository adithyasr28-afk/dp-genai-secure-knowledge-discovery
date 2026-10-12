"""
report/build_report.py

Builds the editable report DOCX from the Markdown sources in report/src/.

  1. Concatenates report/src/*.md in filename order.
  2. Resolves labels so numbering never drifts while the team edits:
       # Heading            -> "I. Heading"     (## -> "A.", ### -> "1)")
       # Heading {-}        -> unnumbered
       ![{fig:key} Caption](path){width=..}  -> "Fig. N. Caption"; {fig:key} in text -> N
       Table: {tab:key} Title                -> "TABLE IV. Title";  {tab:key} in text -> IV
       $$ ... $$ {#eq:key}                   -> equation with "(N)";  {eq:key} in text -> (N)
       [@key] / [@a; @b]                     -> [n] / [n][m]  (IEEE order of first citation)
       {{REFERENCES}}  {{LIST_OF_FIGURES}}  {{LIST_OF_TABLES}}  {{WORDCOUNT:...}}
  3. Converts to DOCX with pandoc (equations become native, editable Word
     equations) using report/reference.docx for template-matching styles.
  4. Prepends the official template's front matter (cover page, index, list
     of figures, list of tables, contribution tables) and fills its tables.

Run from the project root:  python report/build_report.py
Outputs: report/Report_Draft_DP_GenAI_Secure_Knowledge_Discovery.docx and
         report/Report_Draft_full.md (the resolved Markdown).
"""

from __future__ import annotations

import copy
import io
import re
import sys
from pathlib import Path

import docx
import pypandoc
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = HERE / "src"
TEMPLATE = HERE / "template" / "3_Consolidated_Template.docx"
REFDOC = HERE / "reference.docx"
OUT_DOCX = HERE / "final_report.docx"
OUT_MD = HERE / "final_report_resolved.md"

sys.path.insert(0, str(HERE))
from references import REFERENCES  # noqa: E402

IEEE_BLUE = RGBColor(0x00, 0x62, 0x9B)
HEAD_FONT = "Helvetica Neue"  # as in the template; Word substitutes Arial if absent
BODY_FONT = "Times New Roman"

# Team 26FSDPYCPMID1028 has THREE members. The course roster lists two
# registration numbers (23BCE2114, 23BCE2133 = PoC); the third member's number
# and all student names/e-mails must be supplied by the team. Placeholders are
# bracketed so they are easy to find; nothing here is invented.
STUDENT_NAME = "[Student name]"
MEMBERS = [  # (registration number, name)
    ("23BCE2114", STUDENT_NAME),
    ("23BCE2133", STUDENT_NAME),
    ("[Reg. No. of 3rd member]", STUDENT_NAME),
]
FRONT = {
    "team_id": "26FSDPYCPMID1028",
    "title": "Differential Privacy-Enhanced Generative AI for Secure Knowledge Discovery",
    "members": [f"{reg} – {name}" for reg, name in MEMBERS],
    "authors": "Dr. M Rajasekhara Babu¹, [Student name]² (23BCE2114), [Student name]³ (23BCE2133), "
               "[Student name]⁴ ([Reg. No. of 3rd member])",
    "affil": "School of Computer Science and Engineering, Vellore Institute of Technology (VIT), Vellore-632014, T.N., India",
    "emails": "¹mrajasekharababu@vit.ac.in, ²[VIT e-mail], ³[VIT e-mail], ⁴[VIT e-mail]",
    "corresponding": "Corresponding author: M Rajasekhara Babu (e-mail: mrajasekharababu@vit.ac.in).",
}

# Page geometry of the template body (A4; margins in twips) and its two-column layout.
PG_W, PG_H = 11906, 16838
MARGINS = dict(top=720, right=1440, bottom=720, left=1440, header=709, footer=709, gutter=0)
COL_SPACE = 708
COLUMN_WIDTH_IN = 2.85     # (8.27 - 2 - 0.49) / 2 = 2.89 in per column
PAGE_WIDTH_IN = 6.25
WIDE_FIGURE_MIN_IN = 4.8   # figures specified at least this wide span the page
WIDE_TABLE_MIN_COLS = 4    # tables with this many columns span the page


def roman(n: int) -> str:
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
            (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


# ---------------------------------------------------------------------------
def resolve(md: str):
    figs, tabs, eqs, cites = {}, {}, {}, {}
    fig_list, tab_list = [], []

    # Pass 1: assign figure/table/equation numbers in order of definition.
    for m in re.finditer(r"!\[\{fig:([\w-]+)\}\s*(.*?)\]\(", md):
        figs[m.group(1)] = len(figs) + 1
        fig_list.append((len(figs), re.sub(r"\[@[^\]]+\]", "", m.group(2)).strip().rstrip(".")))
    for m in re.finditer(r"^Table:\s*\{tab:([\w-]+)\}\s*(.*)$", md, re.M):
        tabs[m.group(1)] = len(tabs) + 1
        tab_list.append((roman(len(tabs)), m.group(2).strip()))
    for m in re.finditer(r"\{#eq:([\w-]+)\}", md):
        eqs[m.group(1)] = len(eqs) + 1

    # Citations: number by first appearance in the body text.
    for m in re.finditer(r"\[(@[^\]]+)\]", md):
        for key in re.findall(r"@([\w:-]+)", m.group(1)):
            if key not in cites:
                if key not in REFERENCES:
                    raise KeyError(f"Unknown citation key: {key}")
                cites[key] = len(cites) + 1

    md = re.sub(r"!\[\{fig:([\w-]+)\}\s*", lambda m: f"![Fig. {figs[m.group(1)]}. ", md)
    md = re.sub(r"^Table:\s*\{tab:([\w-]+)\}\s*", lambda m: f"Table: TABLE {roman(tabs[m.group(1)])}. ", md, flags=re.M)
    md = re.sub(r"\$\$\s*\{#eq:([\w-]+)\}",
                lambda m: f"\\qquad\\qquad ({eqs[m.group(1)]})$$", md)
    md = re.sub(r"\{fig:([\w-]+)\}", lambda m: str(figs[m.group(1)]), md)
    md = re.sub(r"\{tab:([\w-]+)\}", lambda m: roman(tabs[m.group(1)]), md)
    md = re.sub(r"\{eq:([\w-]+)\}", lambda m: f"({eqs[m.group(1)]})", md)
    md = re.sub(r"\[(@[^\]]+)\]",
                lambda m: "".join(f"[{cites[k]}]" for k in re.findall(r"@([\w:-]+)", m.group(1))), md)

    refs = "\n".join(f"[{n}] {REFERENCES[k]['text']}" + ("" if REFERENCES[k].get("verified", True) else
                     " **[VERIFY]**") + "\n" for k, n in sorted(cites.items(), key=lambda kv: kv[1]))
    md = md.replace("{{REFERENCES}}", refs)
    md = md.replace("{{LIST_OF_FIGURES}}", "\n".join(f"- Fig. {n}. {t}" for n, t in fig_list))
    md = md.replace("{{LIST_OF_TABLES}}", "\n".join(f"- TABLE {n}. {t}" for n, t in tab_list))

    # Section numbering.
    c1 = c2 = c3 = 0
    out_lines, toc = [], []
    in_code = False
    for line in md.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{1,3} ", line):
            level = len(line.split(" ")[0])
            text = line[level + 1:].strip()
            unnumbered = text.endswith("{-}")
            text = text.replace("{-}", "").strip()
            if unnumbered:
                out_lines.append("#" * level + " " + text + " {-}")
                if level == 1:
                    toc.append(("", text))
                continue
            if level == 1:
                c1 += 1; c2 = c3 = 0
                label = f"{roman(c1)}. "
                toc.append((roman(c1), text))
            elif level == 2:
                c2 += 1; c3 = 0
                label = f"{chr(64 + c2)}. "
            else:
                c3 += 1
                label = f"{c3}) "
            out_lines.append("#" * level + " " + label + text + " {-}")
        else:
            out_lines.append(line)
    md = "\n".join(out_lines)
    return md, fig_list, tab_list, toc, cites


def _section_break(cols: int) -> str:
    """Raw OOXML paragraph that ENDS a continuous section with `cols` columns."""
    num = ' w:num="2"' if cols == 2 else ""
    mar = " ".join(f'w:{k}="{v}"' for k, v in MARGINS.items())
    return ("```{=openxml}\n"
            f'<w:p><w:pPr><w:sectPr><w:type w:val="continuous"/><w:pgSz w:w="{PG_W}" w:h="{PG_H}"/>'
            f'<w:pgMar {mar}/><w:cols{num} w:space="{COL_SPACE}"/></w:sectPr></w:pPr></w:p>\n```')


def apply_two_column_layout(md: str) -> str:
    """Lay the body out like the template: a continuous two-column section.

    - Figures specified >= WIDE_FIGURE_MIN_IN wide and tables with
      >= WIDE_TABLE_MIN_COLS columns become page-wide (one-column) sections;
      other figures are set to the column width.
    - The appendices (code listings, wide tables) form one single-column region,
      from 'Appendix A' up to the Data Availability Statement.
    """
    lines = md.split("\n")
    out, i, region = [], 0, "two"

    def width_of(line):
        m = re.search(r"\{width=([\d.]+)in\}", line)
        return float(m.group(1)) if m else PAGE_WIDTH_IN

    def take_block(start):
        """A figure line, or a table caption + blank + pipe rows. Returns (end, is_wide, text)."""
        line = lines[start]
        if line.startswith("!["):
            w = width_of(line)
            wide = w >= WIDE_FIGURE_MIN_IN
            new_w = min(w, PAGE_WIDTH_IN) if wide else COLUMN_WIDTH_IN
            return start + 1, wide, re.sub(r"\{width=[\d.]+in\}", f"{{width={new_w}in}}", line)
        j = start + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        k = j
        while k < len(lines) and lines[k].startswith("|"):
            k += 1
        ncols = lines[j].count("|") - 1 if j < len(lines) else 0
        return k, ncols >= WIDE_TABLE_MIN_COLS, "\n".join(lines[start:k])

    in_code = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^# Appendix A\b", line) and region == "two":
            out.append(_section_break(2))
            region = "one"
        elif not in_code and line.startswith("# Data Availability Statement") and region == "one":
            out.append(_section_break(1))
            region = "two"
        if (not in_code and region == "two"
                and (line.startswith("![") or line.startswith("Table: TABLE"))):
            # gather a run of consecutive wide items into one page-wide section
            end, wide, text = take_block(i)
            if not wide:
                out.append(text)
                i = end
                continue
            group = [text]
            j = end
            while True:
                k = j
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines) and (lines[k].startswith("![") or lines[k].startswith("Table: TABLE")):
                    e2, w2, t2 = take_block(k)
                    if w2:
                        group += ["", t2]
                        j = e2
                        continue
                break
            out += [_section_break(2), ""] + group + ["", _section_break(1)]
            i = j
            continue
        if region == "one" and line.startswith("!["):
            w = width_of(line)
            line = re.sub(r"\{width=[\d.]+in\}", f"{{width={min(w, PAGE_WIDTH_IN)}in}}", line)
        out.append(line)
        i += 1
    return "\n".join(out)


def section_word_counts(md: str) -> list:
    """(heading, words) for each level-1 section of the resolved Markdown."""
    parts = re.split(r"^# (.+?) \{-\}\s*$", md, flags=re.M)
    counts = []
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        body = re.sub(r"\$\$.*?\$\$", " ", body, flags=re.S)
        body = re.sub(r"!\[.*?\]\(.*?\)(\{.*?\})?", " ", body)
        body = re.sub(r"^\|.*\|$", " ", body, flags=re.M)        # tables are not counted
        body = re.sub(r"^Table:.*$", " ", body, flags=re.M)
        body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
        counts.append((parts[i].replace(" ", " "), len(re.findall(r"[A-Za-z0-9][\w'’-]*", body))))
    return counts


# ---------------------------------------------------------------------------
def make_reference_docx():
    """Pandoc's default reference.docx restyled to the template's formatting."""
    import subprocess

    tmp = HERE / "_pandoc_default_reference.docx"
    pandoc = pypandoc.get_pandoc_path()  # pypandoc_binary ships its own pandoc
    raw = subprocess.run([pandoc, "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout
    tmp.write_bytes(raw)
    d = docx.Document(str(tmp))
    sec = d.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.left_margin = sec.right_margin = Inches(1.0)
    sec.top_margin, sec.bottom_margin = Inches(0.5), Inches(0.7)

    def style(name, font=BODY_FONT, size=10, bold=False, color=None, caps=False, small_caps=False,
              align=None, before=0, after=4, italic=False, first_indent=None):
        try:
            s = d.styles[name]
        except KeyError:
            return
        f = s.font
        f.name, f.size, f.bold, f.italic = font, Pt(size), bold, italic
        f.all_caps, f.small_caps = caps, small_caps
        f.color.rgb = color if color is not None else RGBColor(0, 0, 0)
        rpr = s.element.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = rpr.makeelement(qn("w:rFonts"), {})
            rpr.append(fonts)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            fonts.set(qn(a), font)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            if fonts.get(qn(a)) is not None:
                del fonts.attrib[qn(a)]
        pf = s.paragraph_format
        pf.space_before, pf.space_after = Pt(before), Pt(after)
        if align is not None:
            pf.alignment = align
        if first_indent is not None:
            pf.first_line_indent = Inches(first_indent)

    J, C = WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.CENTER
    style("Normal", size=10, align=J)
    style("Body Text", size=10, align=J, first_indent=0.15)
    style("First Paragraph", size=10, align=J)
    style("Compact", size=10, align=J, after=2)
    style("Heading 1", font=HEAD_FONT, size=9, bold=True, color=IEEE_BLUE, caps=True, before=12, after=4)
    style("Heading 2", font=HEAD_FONT, size=9, color=IEEE_BLUE, caps=True, before=8, after=3)
    style("Heading 3", font=HEAD_FONT, size=9, color=RGBColor(0x58, 0x59, 0x5B), small_caps=True, before=6, after=2)
    style("Title", font=HEAD_FONT, size=22, bold=True, color=IEEE_BLUE, align=C, before=24, after=15)
    style("Image Caption", font=HEAD_FONT, size=8, align=J, before=4, after=10)
    style("Table Caption", size=8, small_caps=True, align=C, before=10, after=4)
    style("Caption", font=HEAD_FONT, size=8, align=J, before=4, after=8)
    style("Captioned Figure", size=10, align=C)
    style("Figure", size=10, align=C)
    style("Block Text", size=9, align=J, before=4, after=4)
    style("Source Code", font="Consolas", size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
    style("Bibliography", size=8, align=J, after=2)

    # Table style: thin borders, small text, header row bold.
    try:
        ts = d.styles["Table"]
        tbl_pr = ts.element.find(qn("w:tblPr"))
        if tbl_pr is None:
            tbl_pr = ts.element.makeelement(qn("w:tblPr"), {})
            ts.element.append(tbl_pr)
        borders = tbl_pr.makeelement(qn("w:tblBorders"), {})
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            b = borders.makeelement(qn(f"w:{edge}"), {qn("w:val"): "single", qn("w:sz"): "4",
                                                      qn("w:space"): "0", qn("w:color"): "808080"})
            borders.append(b)
        old = tbl_pr.find(qn("w:tblBorders"))
        if old is not None:
            tbl_pr.remove(old)
        tbl_pr.append(borders)
        ts.font.size = Pt(8)
        ts.font.name = BODY_FONT
    except KeyError:
        pass
    d.save(str(REFDOC))
    tmp.unlink()


# ---------------------------------------------------------------------------
def _set_text(par_el, text, keep_first_run=True):
    """Replace all text in a template paragraph element, keeping the first run's formatting."""
    runs = par_el.findall(qn("w:r"))
    if not runs:
        return
    first = runs[0]
    for r in runs[1:]:
        par_el.remove(r)
    for t in first.findall(qn("w:t")):
        first.remove(t)
    for br in first.findall(qn("w:br")):
        first.remove(br)
    t = first.makeelement(qn("w:t"), {})
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    first.append(t)


def _fill_table(tbl, rows, header_rows=1, keep_last_rows=0):
    """Fill a python-docx table: keep header rows, clone the first data row for each entry."""
    data_rows = tbl.rows[header_rows:len(tbl.rows) - keep_last_rows] if keep_last_rows else tbl.rows[header_rows:]
    proto = copy.deepcopy(data_rows[0]._tr)
    for r in list(data_rows):
        tbl._tbl.remove(r._tr)
    anchor = tbl.rows[header_rows - 1]._tr
    for values in rows:
        tr = copy.deepcopy(proto)
        anchor.addnext(tr)
        anchor = tr
        cells = tr.findall(qn("w:tc"))
        for tc, v in zip(cells, values):
            ps = tc.findall(qn("w:p"))
            for p in ps[1:]:
                tc.remove(p)
            p = ps[0]
            for r in p.findall(qn("w:r")):
                p.remove(r)
            for np_ in list(p.iter(qn("w:numPr"))):   # explicit numbers replace the template's auto-numbering
                np_.getparent().remove(np_)
            r = p.makeelement(qn("w:r"), {})
            rpr = r.makeelement(qn("w:rPr"), {})
            sz = rpr.makeelement(qn("w:sz"), {qn("w:val"): "20"})
            rpr.append(sz)
            r.append(rpr)
            t = r.makeelement(qn("w:t"), {})
            t.text = str(v)
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            r.append(t)
            p.append(r)


_DROPPED_SMARTART_IDS: set = set()


def _drop_unused_member_slots(xml: str, keep: int) -> str:
    """The template's 'by' SmartArt has four student slots; the team has three.
    Remove the unused node(s) from the SmartArt data model (the node, its
    transitions, its presentation points and their connections) and remember the
    presentation ids so the cached drawing can drop the matching shapes."""
    doc = re.search(r'<dgm:pt modelId="([^"]+)" type="doc"', xml).group(1)
    parents = []  # (srcOrd, node id, parTrans id, sibTrans id)
    for m in re.finditer(r"<dgm:cxn\b[^>]*>", xml):
        c = m.group(0)
        if "type=" in c or f'srcId="{doc}"' not in c:
            continue
        g = lambda a: re.search(a + r'="([^"]+)"', c).group(1)
        parents.append((int(g("srcOrd")), g("destId"), g("parTransId"), g("sibTransId")))
    parents.sort()
    drop = set()
    for _, node, par, sib in parents[keep:]:
        drop |= {node, par, sib}
        # presentation points: presOf target (text shape) and its composite/image siblings
        for m in re.finditer(r'type="presOf" srcId="%s" destId="([^"]+)"' % re.escape(node), xml):
            txt = m.group(1)
            comp = re.search(r'type="presParOf" srcId="([^"]+)" destId="%s"' % re.escape(txt), xml).group(1)
            drop |= {txt, comp}
            drop |= set(re.findall(r'type="presParOf" srcId="%s" destId="([^"]+)"' % re.escape(comp), xml))
    # the spacing point that preceded the last dropped composite
    pres_root = re.search(r'type="presOf" srcId="%s" destId="([^"]+)"' % re.escape(doc), xml).group(1)
    kids = sorted((int(o), d) for d, o in re.findall(
        r'type="presParOf" srcId="%s" destId="([^"]+)" srcOrd="(\d+)"' % re.escape(pres_root), xml))
    kept_ids = [d for _, d in kids if d not in drop]
    while kept_ids and 'presName="spacing"' in (re.search(
            r'<dgm:pt modelId="%s"[^>]*>(.*?)</dgm:pt>' % re.escape(kept_ids[-1]), xml, re.S) or ("",))[0]:
        drop.add(kept_ids.pop())
    for pid in drop:
        xml = re.sub(r'<dgm:pt modelId="%s"[^>]*?(?:/>|>.*?</dgm:pt>)' % re.escape(pid), "", xml, flags=re.S)
        xml = re.sub(r'<dgm:cxn\b[^>]*"%s"[^>]*/>' % re.escape(pid), "", xml)
    _DROPPED_SMARTART_IDS.update(drop)
    return xml


def _fill_smartart_text(blob: bytes) -> bytes:
    """Fill the cover-page SmartArt: student 'Reg No'/'Name' slots, in order,
    and remove the slots the team does not need."""
    xml = blob.decode("utf-8")
    if "<a:t>Reg No </a:t>" not in xml:
        return blob
    members = FRONT["members"]
    if "<dgm:dataModel" in xml:
        xml = _drop_unused_member_slots(xml, len(members))
    else:  # cached drawing: drop the shapes of the removed presentation points
        for pid in _DROPPED_SMARTART_IDS:
            xml = re.sub(r'<dsp:sp modelId="%s".*?</dsp:sp>' % re.escape(pid), "", xml, flags=re.S)
    for m in members:
        reg, _, name = m.partition(" – ")
        xml = xml.replace("<a:t>Reg No </a:t>", f"<a:t>{reg} </a:t>", 1)
        xml = xml.replace("<a:t>Name</a:t>", f"<a:t>{name or '[Name]'}</a:t>", 1)
    return xml.encode("utf-8")


def copy_smartart(tpl, out, front):
    """Copy SmartArt (diagram data/layout/style/colours + cached drawing) used by
    the front matter into the output package, re-pointing the relationship ids."""
    from docx.opc.packuri import PackURI
    from docx.opc.part import Part

    counter = [500]
    copied = {}

    def clone(src_part):
        if src_part.partname in copied:
            return copied[src_part.partname]
        counter[0] += 1
        ext = str(src_part.partname).rsplit(".", 1)[-1]
        base = str(src_part.partname).rsplit("/", 1)[-1].rsplit(".", 1)[0].rstrip("0123456789")
        uri = PackURI(f"/word/diagrams/{base}{counter[0]}.{ext}")
        blob = src_part.blob
        if base in ("data", "drawing"):
            blob = _fill_smartart_text(blob)
        new = Part(uri, src_part.content_type, blob, out.part.package)
        copied[src_part.partname] = new
        for rel in src_part.rels.values():          # e.g. data -> drawing
            if not rel.is_external:
                new.rels.add_relationship(rel.reltype, clone(rel.target_part), rel.rId)
        return new

    for el in front:
        for rel_ids in el.iter("{http://schemas.openxmlformats.org/drawingml/2006/diagram}relIds"):
            for attr in list(rel_ids.attrib):
                old = rel_ids.get(attr)
                if old not in tpl.part.rels:
                    continue
                rel = tpl.part.rels[old]
                rel_ids.set(attr, out.part.relate_to(clone(rel.target_part), rel.reltype))


def merge_front_matter(body_path: Path, toc, fig_list, tab_list, word_counts, abstract, keywords):
    tpl = docx.Document(str(TEMPLATE))
    kids = list(tpl.element.body.iterchildren())
    title_idx = next(i for i, el in enumerate(kids)
                     if "TITLE OF THE PAPER" in "".join(x.text or "" for x in el.iter(qn("w:t"))))
    sect_idx = next(i for i, el in enumerate(kids) if i > title_idx and el.find(".//" + qn("w:sectPr")) is not None)

    def txt(el):
        return "".join(x.text or "" for x in el.iter(qn("w:t")))

    # --- fill cover page ---------------------------------------------------
    for el in kids[:title_idx]:
        t = txt(el)
        if t.startswith("Team ID"):
            # "Team ID:" sits inside the scroll-shaped text box (present twice:
            # DrawingML choice + VML fallback); the paragraph itself says "Case-Study Report".
            for tb in el.iter(qn("w:txbxContent")):
                ts = list(tb.iter(qn("w:t")))
                for j, tnode in enumerate(ts):
                    tnode.text = f"Team ID: {FRONT['team_id']}" if j == 0 else ""
                for tag in ("w:sz", "w:szCs"):        # 10 pt -> 7 pt so the ID fits the scroll shape
                    for sz in tb.iter(qn(tag)):
                        sz.set(qn("w:val"), "14")
        elif "<Title>" in t or "Title" in t and t.startswith("On"):
            runs = el.findall(qn("w:r"))              # runs: "On" (14 pt), then the 32 pt title runs
            title_run = runs[1]
            ts = title_run.findall(qn("w:t"))
            ts[0].text = f"“{FRONT['title']}”"
            for extra in ts[1:]:
                title_run.remove(extra)
            for r in runs[2:]:
                el.remove(r)
            for tag in ("w:sz", "w:szCs"):            # long title: 32 pt -> 20 pt so the cover stays on one page
                for sz in title_run.iter(qn(tag)):
                    sz.set(qn("w:val"), "40")
    # Students ("by") and faculty ("To") live in the template's SmartArt boxes;
    # they are filled in copy_smartart() below rather than as extra text.

    # The two-line title is taller than the template's placeholder: drop two empty
    # spacer paragraphs around "To" (never ones that anchor a drawing) so the
    # cover stays on one page.
    to_idx = next(i for i, el in enumerate(kids) if txt(el).strip() == "To")
    removed = 0
    for el in [kids[to_idx - 1], kids[to_idx + 1]]:
        if el.tag == qn("w:p") and not txt(el).strip() and el.find(".//" + qn("w:drawing")) is None \
                and el.find(".//" + qn("w:sectPr")) is None:
            el.getparent().remove(el)
            removed += 1
    # The page break after the cover sits in its own empty paragraph; on a full
    # cover that paragraph spills onto a blank page. Move the break onto the date line.
    kids = list(tpl.element.body.iterchildren())
    date_idx = next(i for i, el in enumerate(kids) if txt(el).strip().startswith("October"))
    nxt = kids[date_idx + 1]
    if not txt(nxt).strip() and any(b.get(qn("w:type")) == "page" for b in nxt.iter(qn("w:br"))):
        nxt.getparent().remove(nxt)
        docx.text.paragraph.Paragraph(kids[date_idx], tpl._body).add_run().add_break(docx.enum.text.WD_BREAK.PAGE)
    kids = list(tpl.element.body.iterchildren())
    title_idx = next(i for i, el in enumerate(kids)
                     if "TITLE OF THE PAPER" in "".join(x.text or "" for x in el.iter(qn("w:t"))))
    sect_idx = next(i for i, el in enumerate(kids) if i > title_idx and el.find(".//" + qn("w:sectPr")) is not None)

    # --- fill index / LoF / LoT / contributions tables -------------------------
    t_index, t_lof, t_lot, t_contrib, t_cons = tpl.tables[0], tpl.tables[1], tpl.tables[2], tpl.tables[3], tpl.tables[4]
    toc = [(n, t) for n, t in toc if not t.startswith("Draft Status")]
    word_counts = [(h, w) for h, w in word_counts if not h.startswith("Draft Status")]
    index_rows = [("", "Abstract", "")] + [(n or "", t, "") for n, t in toc if t.lower() != "abstract"]
    _fill_table(t_index, index_rows)
    _fill_table(t_lof, [(str(n), t, "") for n, t in fig_list])
    _fill_table(t_lot, [(n, t, "") for n, t in tab_list])
    contrib = [(str(i + 1), h, "[Reg. No.]", str(w)) for i, (h, w) in enumerate(word_counts)]
    _fill_table(t_contrib, contrib)
    total = sum(w for _, w in word_counts)
    cons_rows = t_cons.rows
    student_rows = cons_rows[2:6]                 # the template has four student rows
    for r, (reg, _) in zip(student_rows, MEMBERS):
        r.cells[1].text = reg
        r.cells[2].text = "[words]"
    for r in student_rows[len(MEMBERS):]:         # three-member team: remove the unused row(s)
        r._tr.getparent().remove(r._tr)
    t_cons.rows[-1].cells[-1].text = str(total)

    # --- paper title block -------------------------------------------------------
    block = kids[title_idx:sect_idx + 1]
    for el in block:
        t = txt(el)
        if "TITLE OF THE PAPER" in t:
            _set_text(el, FRONT["title"])
        elif t.startswith("Dr. M Rajasekhara Babu1"):
            _set_text(el, FRONT["authors"])
        elif t.startswith("School of Computer Science"):
            _set_text(el, FRONT["affil"])
        elif t.startswith("1mrajasekharababu"):
            _set_text(el, FRONT["emails"])
        elif t.startswith("Corresponding author"):
            _set_text(el, FRONT["corresponding"])
        elif t.startswith("ABSTRACT"):
            runs = el.findall(qn("w:r"))
            label = runs[0]
            for r in runs[1:]:
                el.remove(r)
            for tt in label.findall(qn("w:t")):
                tt.text = "ABSTRACT "
            p = docx.text.paragraph.Paragraph(el, tpl._body)
            r = p.add_run(abstract)
            r.font.size = Pt(10)
        elif t.startswith("INDEX TERMS"):
            runs = el.findall(qn("w:r"))
            label = runs[0]
            for r in runs[1:]:
                el.remove(r)
            for tt in label.findall(qn("w:t")):
                tt.text = "INDEX TERMS "
            p = docx.text.paragraph.Paragraph(el, tpl._body)
            r = p.add_run(keywords)
            r.font.size = Pt(10)

    front = kids[:sect_idx + 1]
    # The template's two-column body section starts after sect_idx; the body is
    # laid out the same way (see apply_two_column_layout and the end of this function).

    # --- move into the pandoc body document ----------------------------------
    out = docx.Document(str(body_path))
    body = out.element.body
    first = body[0]

    # images referenced by the front matter (e.g. the VIT logo)
    for el in front:
        for blip in el.iter(qn("a:blip")):
            rid = blip.get(qn("r:embed"))
            if not rid:
                continue
            part = tpl.part.related_parts[rid]
            new_rid, _ = out.part.get_or_add_image(io.BytesIO(part.blob))
            blip.set(qn("r:embed"), new_rid)
        # header/footer references point at template-only parts: drop them
        for ref in list(el.iter(qn("w:headerReference"))) + list(el.iter(qn("w:footerReference"))):
            ref.getparent().remove(ref)
        # hyperlinks point at template relationships: keep the text, drop the link
        for h in list(el.iter(qn("w:hyperlink"))):
            parent = h.getparent()
            idx = parent.index(h)
            for child in list(h):
                parent.insert(idx, child)
                idx += 1
            parent.remove(h)

    copy_smartart(tpl, out, front)

    # list numbering used by the front matter: copy definitions with new ids
    tpl_num = tpl.part.numbering_part.element
    out_num = out.part.numbering_part.element
    used = {np_.find(qn("w:numId")).get(qn("w:val")) for el in front for np_ in el.iter(qn("w:numPr"))
            if np_.find(qn("w:numId")) is not None}
    existing_abs = [int(a.get(qn("w:abstractNumId"))) for a in out_num.findall(qn("w:abstractNum"))]
    existing_num = [int(n.get(qn("w:numId"))) for n in out_num.findall(qn("w:num"))]
    next_abs, next_num = max(existing_abs + [0]) + 100, max(existing_num + [0]) + 100
    num_map = {}
    first_num = out_num.find(qn("w:num"))
    for old in sorted(used - {"0"}, key=int):
        src_num = next((n for n in tpl_num.findall(qn("w:num")) if n.get(qn("w:numId")) == old), None)
        if src_num is None:
            continue
        abs_id = src_num.find(qn("w:abstractNumId")).get(qn("w:val"))
        src_abs = next(a for a in tpl_num.findall(qn("w:abstractNum")) if a.get(qn("w:abstractNumId")) == abs_id)
        new_abs = copy.deepcopy(src_abs)
        new_abs.set(qn("w:abstractNumId"), str(next_abs))
        for link in new_abs.findall(qn("w:numStyleLink")) + new_abs.findall(qn("w:styleLink")):
            new_abs.remove(link)
        if first_num is not None:
            first_num.addprevious(new_abs)   # abstractNum elements must precede num elements
        else:
            out_num.append(new_abs)
        new_num = copy.deepcopy(src_num)
        new_num.set(qn("w:numId"), str(next_num))
        new_num.find(qn("w:abstractNumId")).set(qn("w:val"), str(next_abs))
        out_num.append(new_num)
        num_map[old] = str(next_num)
        next_abs += 1
        next_num += 1
    for el in front:
        for np_ in el.iter(qn("w:numPr")):
            nid = np_.find(qn("w:numId"))
            if nid is not None and nid.get(qn("w:val")) in num_map:
                nid.set(qn("w:val"), num_map[nid.get(qn("w:val"))])

    # table style used by the template tables
    tstyles = {s.get(qn("w:styleId")): s for s in tpl.styles.element.findall(qn("w:style"))}
    have = {s.get(qn("w:styleId")) for s in out.styles.element.findall(qn("w:style"))}
    for el in front:
        for ts in el.iter(qn("w:tblStyle")):
            sid = ts.get(qn("w:val"))
            if sid not in have and sid in tstyles:
                out.styles.element.append(copy.deepcopy(tstyles[sid]))
                have.add(sid)

    # Body tables (from pandoc): left-aligned cell text and content-based column
    # widths instead of equal columns with justified text.
    for tbl in body.iter(qn("w:tbl")):
        tbl_pr = tbl.find(qn("w:tblPr"))
        if tbl_pr is not None:
            for old in tbl_pr.findall(qn("w:tblLayout")) + tbl_pr.findall(qn("w:tblW")):
                tbl_pr.remove(old)
            tbl_pr.append(tbl_pr.makeelement(qn("w:tblW"), {qn("w:w"): "5000", qn("w:type"): "pct"}))
            tbl_pr.append(tbl_pr.makeelement(qn("w:tblLayout"), {qn("w:type"): "autofit"}))
        for tcw in list(tbl.iter(qn("w:tcW"))):
            tcw.getparent().remove(tcw)
        for p in tbl.iter(qn("w:p")):
            ppr = p.find(qn("w:pPr"))
            if ppr is None:
                ppr = p.makeelement(qn("w:pPr"), {})
                p.insert(0, ppr)
            for jc in ppr.findall(qn("w:jc")):
                ppr.remove(jc)
            ppr.append(ppr.makeelement(qn("w:jc"), {qn("w:val"): "left"}))

    # Fixed column widths (twips, text width 9029) where Word's autofit splits numbers.
    fixed_widths = {"Claim in the Gemini response": [3800, 1150, 950, 1250, 1879]}
    for tbl in body.iter(qn("w:tbl")):
        first_cell = "".join(t.text or "" for t in next(tbl.iter(qn("w:tc"))).iter(qn("w:t"))).strip()
        widths = fixed_widths.get(first_cell)
        grid = tbl.find(qn("w:tblGrid"))
        if not widths or grid is None or len(grid) != len(widths):
            continue
        tbl_pr = tbl.find(qn("w:tblPr"))
        for el in tbl_pr.findall(qn("w:tblLayout")):
            el.set(qn("w:type"), "fixed")
        for col, w in zip(grid, widths):
            col.set(qn("w:w"), str(w))

    # Code blocks (prompt listing, commands): left-aligned, never justified.
    for p in out.paragraphs:
        if p.style is not None and p.style.name in ("Source Code", "SourceCode"):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    for el in front:
        first.addprevious(copy.deepcopy(el))

    # page size / margins for every section, matching the template (A4, 1 in / 0.5 in)
    for s in out.sections:
        s.page_width, s.page_height = Inches(8.27), Inches(11.69)
        s.left_margin = s.right_margin = Inches(1.0)
        s.top_margin, s.bottom_margin = Inches(0.5), Inches(0.5)
    # the final body section (references) is the template's continuous two-column section
    final = body.find(qn("w:sectPr"))
    for el in final.findall(qn("w:cols")) + final.findall(qn("w:type")):
        final.remove(el)
    final.insert(0, final.makeelement(qn("w:type"), {qn("w:val"): "continuous"}))
    pg_mar = final.find(qn("w:pgMar"))
    cols = final.makeelement(qn("w:cols"), {qn("w:num"): "2", qn("w:space"): str(COL_SPACE)})
    (pg_mar.addnext if pg_mar is not None else final.append)(cols)
    out.core_properties.title = FRONT["title"]
    out.core_properties.author = "Team 26FSDPYCPMID1028"
    out.save(str(OUT_DOCX))


def export_figure_folder(md: str):
    """Manuscript guideline: every figure saved in a separate folder named
    'Fig NN <Figure Name>' (PNG at the generated resolution, plus the editable
    SVG/.drawio source when one exists)."""
    import shutil

    out = ROOT / "diagrams"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    pattern = r"!\[\{fig:[\w-]+\}\s*(.*?)\]\((.*?)\)"
    index = ["# Report figures (final numbering)", "",
             "Generated by `report/build_report.py`. Each figure is saved as `Fig NN <Name>` in the format it was "
             "produced in: PNG at 600 DPI as generated by `figures/diagram_builder.py` or `analysis/verify_results.py`, "
             "plus the editable SVG and draw.io source where one exists. Images were not upscaled. "
             "Dashboard screenshots are figures too but live in `evidence/screenshots/`.", "",
             "| No. | File stem | Source | Editable source |", "|---|---|---|---|"]
    for n, m in enumerate(re.finditer(pattern, md), start=1):
        caption = re.sub(r"\[@[^\]]+\]|\*", "", m.group(1)).strip()
        title = re.split(r"[.:;(]", caption)[0].strip()
        title = re.sub(r'[\\/*?"<>|]', "", title)[:70].strip()
        src = ROOT / m.group(2)
        if "screens" in src.parts or "evidence" in src.parts:
            index.append(f"| {n} | — (screenshot) | `{m.group(2)}` | — |")
            continue
        stem = f"Fig {n:02d} {title}"
        shutil.copy(src, out / f"{stem}{src.suffix}")
        editable = []
        for ext in (".svg", ".drawio"):
            alt = src.with_suffix(ext)
            if alt.exists():
                shutil.copy(alt, out / f"{stem}{ext}")
                editable.append(ext)
        index.append(f"| {n} | {stem} | `{m.group(2)}` | {', '.join(editable) or '—'} |")
    (out / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
def main():
    import make_tables  # regenerate numeric tables from results/verified/ first

    make_tables.main()
    md = "\n\n".join(p.read_text(encoding="utf-8") for p in sorted(SRC.glob("*.md")))
    md = re.sub(r"\{\{INCLUDE:([^}]+)\}\}", lambda m: (HERE / m.group(1)).read_text(encoding="utf-8"), md)
    sys.path.insert(0, str(ROOT))
    from knowledge_discovery.prompts import SYSTEM_PROMPT

    md = md.replace("{{SYSTEM_PROMPT}}", SYSTEM_PROMPT)
    abstract = re.search(r"<!--ABSTRACT-->(.*?)<!--/ABSTRACT-->", md, re.S).group(1).strip()
    keywords = re.search(r"<!--KEYWORDS-->(.*?)<!--/KEYWORDS-->", md, re.S).group(1).strip()
    md = re.sub(r"<!--ABSTRACT-->.*?<!--/ABSTRACT-->", "", md, flags=re.S)
    md = re.sub(r"<!--KEYWORDS-->.*?<!--/KEYWORDS-->", "", md, flags=re.S)
    export_figure_folder(md)
    resolved, fig_list, tab_list, toc, cites = resolve(md)
    for key in ("cite", "fig", "tab", "eq"):
        left = re.findall(r"\{(?:fig|tab|eq):[\w-]+\}", resolved)
        if left:
            raise ValueError(f"Unresolved labels: {left[:5]}")
    OUT_MD.write_text("# " + FRONT["title"] + " {-}\n\n**ABSTRACT** " + abstract + "\n\n**INDEX TERMS** " +
                      keywords + "\n\n" + resolved, encoding="utf-8")
    counts = [("Abstract", len(abstract.split()))] + section_word_counts(resolved)

    make_reference_docx()
    body_path = HERE / "_body.docx"
    pypandoc.convert_text(apply_two_column_layout(resolved), "docx", format="markdown+tex_math_dollars+pipe_tables+implicit_figures",
                          outputfile=str(body_path), extra_args=[f"--reference-doc={REFDOC}",
                                                                 f"--resource-path={ROOT}"])
    merge_front_matter(body_path, toc, fig_list, tab_list, counts, abstract, keywords)
    body_path.unlink()
    print(f"figures={len(fig_list)} tables={len(tab_list)} references={len(cites)}")
    print("words by section:")
    for h, w in counts:
        print(f"  {w:5d}  {h}")
    print("total words:", sum(w for _, w in counts))
    print("wrote", OUT_DOCX)


if __name__ == "__main__":
    main()
