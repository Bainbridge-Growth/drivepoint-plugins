#!/usr/bin/env python3
"""Find holes in fill bands: header rows and section rows whose colour breaks off for a few
columns and starts again (the cells there have no style, or a different fill).

A column move that leaves columns empty (labels F:J -> C:G leaves H:J with no cells) shows up
in Excel as white gaps in the blue header band and in every banded section row. openpyxl,
LibreOffice and post_validate do not look at styles this way, so check it explicitly:

    python3 style_gaps.py <book.xlsx> [--tabs "P&L,Revenue"] [--cols 40] [--max 12]

Per visible tab and row, over the first --cols visible columns: a run of 1-6 visible columns
whose fill differs from BOTH neighbours, where the two neighbours share one fill (not white /
none), is a hole. White and no fill count as the same; a coloured run of
cells that all hold content (input highlights) is not a hole. --allow lists deliberate one-column fills (a divider
column, a grey input column) as Tab!COL. Hidden columns are skipped (they are never seen). Exit 1 on any hole.
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from collections import defaultdict

from lxml import etree

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def col2n(c):
    n = 0
    for ch in c:
        n = n * 26 + ord(ch) - 64
    return n


def n2col(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def fill_key(st):
    fills = st.find(NS + "fills").findall(NS + "fill")
    xfs = st.find(NS + "cellXfs").findall(NS + "xf")

    def key(s):
        if s is None:
            return None
        f = fills[int(xfs[int(s)].get("fillId", 0))]
        pf = f.find(NS + "patternFill")
        if pf is None or pf.get("patternType") in (None, "none"):
            return None
        fg = pf.find(NS + "fgColor")
        if fg is None:
            return "solid"
        return fg.get("rgb") or f"theme{fg.get('theme')}{fg.get('tint', '')}" or "indexed" + str(fg.get("indexed"))
    return key


def norm(fill):
    """White and no fill look the same on screen."""
    return None if fill in ("FFFFFFFF", "theme0") else fill


def audit(path, tabs=None, ncols=40, out=sys.stdout, max_show=12, want_holes=False, allow=()):
    z = zipfile.ZipFile(path)
    wb = etree.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in etree.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    key = fill_key(etree.fromstring(z.read("xl/styles.xml")))
    total, found = 0, {}
    for s in wb.find(NS + "sheets"):
        name = s.get("name")
        if s.get("state") in ("hidden", "veryHidden") or (tabs and name not in tabs):
            continue
        t = rels[s.get(RID)].lstrip("/")
        root = etree.fromstring(z.read(t if t.startswith("xl/") else "xl/" + t), etree.XMLParser(huge_tree=True))
        hidden, colstyle = set(), {}
        cols = root.find(NS + "cols")
        if cols is not None:
            for c in cols:
                for k in range(int(c.get("min")), min(int(c.get("max")), ncols * 4) + 1):
                    if c.get("hidden") == "1":
                        hidden.add(k)
                    if c.get("style"):
                        colstyle[k] = c.get("style")
        visible = [k for k in range(1, ncols * 4) if k not in hidden][:ncols]
        holes = []
        for row in root.find(NS + "sheetData"):
            if row.get("hidden") == "1":
                continue
            r = int(row.get("r"))
            have = {col2n(re.match(r"[A-Z]+", c.get("r")).group()): c for c in row}
            rowstyle = row.get("s") if row.get("customFormat") == "1" else None
            def style(k):
                c = have.get(k)
                return c.get("s") if c is not None and c.get("s") is not None else (rowstyle or colstyle.get(k))
            fills = [norm(key(style(k))) for k in visible]
            i = 1
            while i < len(fills):
                left = fills[i - 1]
                if fills[i] == left or left is None:
                    i += 1
                    continue
                j = i
                while j < len(fills) and j - i <= 6 and fills[j] != left:
                    j += 1
                content = all((have.get(k) is not None and len(have[k])) or f"{name}!{n2col(k)}" in allow
                              for k in visible[i:j])
                if j < len(fills) and fills[j] == left and 1 <= j - i <= 6 and not (content and fills[i] is not None):
                    lo, hi = visible[i], visible[j - 1]
                    holes.append({"row": r, "lo": lo, "hi": hi, "band": left, "got": fills[i],
                                  "source": visible[j], "source_style": style(visible[j])})
                    i = j
                else:
                    i += 1
        holes = [h for h in holes if not (h["lo"] == h["hi"] and f"{name}!{n2col(h['lo'])}" in allow)]
        found[name] = holes
        if holes:
            total += len(holes)
            byspan = defaultdict(list)
            for h in holes:
                span = n2col(h["lo"]) + (":" + n2col(h["hi"]) if h["hi"] > h["lo"] else "")
                byspan[span].append(h["row"])
            print(f"{name}: {len(holes)} hole(s) — " + "; ".join(
                f"{span} rows {rs[:10]}{'…' if len(rs) > 10 else ''} ({len(rs)})" for span, rs in byspan.items()), file=out)
            for h in holes[:max_show]:
                print(f"    row {h['row']} {n2col(h['lo'])}:{n2col(h['hi'])}: band {h['band']}, hole {h['got']}", file=out)
    print(f"{path}: {'no fill holes' if not total else f'{total} fill hole(s)'}", file=out)
    return found if want_holes else total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx"); ap.add_argument("--tabs"); ap.add_argument("--cols", type=int, default=40)
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--allow", default="", help='deliberate one-column fills, e.g. "P&L!G,Revenue!D"')
    a = ap.parse_args()
    allow = {x.strip() for x in a.allow.split(",") if x.strip()}
    sys.exit(1 if audit(a.xlsx, set(a.tabs.split(",")) if a.tabs else None, a.cols, max_show=a.max, allow=allow) else 0)
