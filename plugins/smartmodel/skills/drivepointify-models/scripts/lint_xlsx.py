#!/usr/bin/env python3
"""Check an .xlsx for the records Excel deletes or repairs on open.

Excel's "We found a problem with some content ... Removed Records: Cell information from
/xl/worksheets/sheetN.xml part" means a sheet's XML breaks a rule Excel enforces but
openpyxl / LibreOffice tolerate. Run this on every workbook a script writes, before it
leaves the session:

    python3 lint_xlsx.py <book.xlsx> [--max 8]      # exit 1 on any problem

Cell records: duplicate addresses, rows or cells out of order, a cell outside its row,
bad cell types / values / shared-string or style indexes, child order, shared formulas
without a master or outside the master's range, array formulas not anchored on their
range, formulas over 8,192 characters, nesting over 64, unbalanced parentheses or quotes,
a leading "=", Excel-365 functions written without their _xlfn. prefix, cell text over
32,767 characters, overlapping merges.
Package: every relationship target exists, every part has a content type, no external-workbook
links (Excel's security bar on open; remove unused ones, ask before removing used ones).
"""
from __future__ import annotations

import argparse
import posixpath
import re
import sys
import zipfile
from collections import Counter

from lxml import etree

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
CT = "{http://schemas.openxmlformats.org/package/2006/content-types}"
RX = re.compile(r"^([A-Z]{1,3})([0-9]+)$")
ERRS = {"#NULL!", "#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#NUM!", "#N/A", "#GETTING_DATA",
        "#SPILL!", "#CALC!", "#FIELD!", "#BLOCKED!", "#CONNECT!", "#BUSY!", "#UNKNOWN!", "#PYTHON!"}
# functions Excel stores with a _xlfn. (or _xlfn._xlws.) prefix; written bare they are #NAME?
XLFN = ("XLOOKUP", "XMATCH", "IFS", "MAXIFS", "MINIFS", "SWITCH", "TEXTJOIN", "CONCAT", "FILTER",
        "UNIQUE", "SORT", "SORTBY", "SEQUENCE", "RANDARRAY", "LET", "LAMBDA", "IFNA", "STDEV.S",
        "STDEV.P", "VAR.S", "VAR.P", "DAYS", "ISOWEEKNUM", "AGGREGATE", "FORECAST.LINEAR",
        "TEXTBEFORE", "TEXTAFTER", "TEXTSPLIT", "VSTACK", "HSTACK", "TOCOL", "TOROW", "CHOOSECOLS",
        "CHOOSEROWS", "TAKE", "DROP", "EXPAND", "WRAPROWS", "WRAPCOLS", "ARRAYTOTEXT", "VALUETOTEXT")
BARE = re.compile(r"(?<![\w\.])(" + "|".join(re.escape(f) for f in XLFN) + r")\(")
STRS = re.compile(r'"(?:[^"]|"")*"')
QSHEET = re.compile(r"'(?:[^']|'')*'!")


def col2n(c):
    n = 0
    for ch in c:
        n = n * 26 + ord(ch) - 64
    return n


def parse_ref(r):
    m = RX.match(r or "")
    return (int(m.group(2)), col2n(m.group(1))) if m else None


def rng(ref):
    a, _, b = ref.partition(":")
    pa, pb = parse_ref(a), parse_ref(b or a)
    if pa is None or pb is None:
        return None
    return pa[0], pa[1], pb[0], pb[1]


def formula_problems(txt):
    out = []
    if len(txt) > 8192:
        out.append(("f-length", f"{len(txt)} chars"))
    if txt.startswith("="):
        out.append(("f-leading-eq", txt[:60]))
    if txt.count('"') % 2:
        out.append(("f-quote", txt[:100]))
    bare = QSHEET.sub("S!", STRS.sub('""', txt))
    d = mx = 0
    for ch in bare:
        if ch == "(":
            d += 1
            mx = max(mx, d)
        elif ch == ")":
            d -= 1
            if d < 0:
                break
    if d != 0:
        out.append(("f-parens", txt[:100]))
    if mx > 64:
        out.append(("f-nesting", f"depth {mx}"))
    m = BARE.search(bare)
    if m:
        out.append(("f-missing-xlfn", f"{m.group(1)} in {txt[:80]}"))
    return out


def lint_sheet(data, nsst, nxf):
    probs = []
    P = lambda k, m: probs.append((k, m))
    root = etree.fromstring(data, etree.XMLParser(huge_tree=True))
    sd = root.find(NS + "sheetData")
    prev_r, seen = 0, set()
    masters, kids, arrays = {}, [], []
    for row in sd.findall(NS + "row"):
        r = int(row.get("r")) if row.get("r") else prev_r + 1
        if r <= prev_r:
            P("row-order", f"row {r} after {prev_r}")
        prev_r, prev_c = r, 0
        for c in row.findall(NS + "c"):
            ref = c.get("r")
            p = parse_ref(ref) if ref else (r, prev_c + 1)
            if p is None:
                P("bad-ref", ref)
                continue
            if p[0] != r:
                P("cell-outside-row", f"{ref} in row {r}")
            if p in seen:
                P("duplicate-cell", ref)
            elif p[1] <= prev_c:
                P("cell-order", f"{ref} after column {prev_c}")
            seen.add(p)
            prev_c = max(prev_c, p[1])
            if p[1] > 16384 or p[0] > 1048576:
                P("out-of-grid", ref)
            t, s = c.get("t", "n"), c.get("s")
            if s is not None and (not s.isdigit() or int(s) >= nxf):
                P("style-index", f"{ref} s={s} (cellXfs has {nxf})")
            kinds = [k.tag.replace(NS, "") for k in c]
            order = [k for k in kinds if k in ("f", "v", "is", "extLst")]
            if order != sorted(order, key=["f", "v", "is", "extLst"].index):
                P("child-order", f"{ref} {kinds}")
            if t not in ("n", "s", "b", "e", "str", "inlineStr", "d"):
                P("cell-type", f"{ref} t={t}")
            v, f, is_ = c.find(NS + "v"), c.find(NS + "f"), c.find(NS + "is")
            vt = v.text if v is not None else None
            if vt is not None:
                if t == "n":
                    try:
                        float(vt)
                    except ValueError:
                        P("number-value", f"{ref} v={vt[:30]!r}")
                elif t == "s" and (not vt.isdigit() or int(vt) >= nsst):
                    P("shared-string-index", f"{ref} v={vt}")
                elif t == "b" and vt not in ("0", "1"):
                    P("bool-value", f"{ref} v={vt}")
                elif t == "e" and vt not in ERRS:
                    P("error-value", f"{ref} v={vt}")
                elif t == "str" and len(vt) > 32767:
                    P("text-length", ref)
            elif v is not None and t not in ("str",) and f is None:
                P("empty-v", f"{ref} t={t}")  # an empty cached value after a formula is fine
            if t == "inlineStr" and is_ is None:
                P("inline-string", ref)
            if is_ is not None and len("".join(is_.itertext())) > 32767:
                P("text-length", ref)
            if f is None:
                continue
            ft, txt = f.get("t", "normal"), f.text or ""
            for k, m in formula_problems(txt):
                P(k, f"{ref}: {m}")
            if ft == "shared":
                si = f.get("si")
                if f.get("ref"):
                    if si in masters:
                        P("shared-duplicate-master", f"{ref} si={si}")
                    masters[si] = (p, rng(f.get("ref")))
                    if not txt:
                        P("shared-master-empty", ref)
                else:
                    kids.append((si, p, ref))
            elif ft == "array":
                b = rng(f.get("ref") or "")
                if b is None or (b[0], b[1]) != p:
                    P("array-anchor", f"{ref} ref={f.get('ref')}")
            elif ft not in ("normal", "dataTable"):
                P("formula-type", f"{ref} t={ft}")
            elif not txt.strip():
                P("formula-empty", ref)
    for si, p, ref in kids:
        if si not in masters:
            P("shared-orphan", f"{ref} si={si}")
            continue
        mp, b = masters[si]
        if b is None or not (b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]) or p < mp:
            P("shared-outside-master", f"{ref} si={si}")
    mc = root.find(NS + "mergeCells")
    if mc is not None:
        taken = {}
        for m in mc.findall(NS + "mergeCell"):
            b = rng(m.get("ref"))
            if b is None:
                P("merge-ref", m.get("ref"))
                continue
            for rr in range(b[0], b[2] + 1):
                hit = next((cc for cc in range(b[1], b[3] + 1) if (rr, cc) in taken), None)
                if hit:
                    P("merge-overlap", m.get("ref"))
                    break
                for cc in range(b[1], b[3] + 1):
                    taken[(rr, cc)] = 1
    return probs


def lint_package(z):
    probs = []
    names = set(z.namelist())
    ct = etree.fromstring(z.read("[Content_Types].xml"))
    defaults = {d.get("Extension").lower() for d in ct.findall(CT + "Default")}
    overrides = {o.get("PartName").lstrip("/") for o in ct.findall(CT + "Override")}
    for o in sorted(overrides - names):
        probs.append(("content-type-for-missing-part", o))
    for n in sorted(names):
        if n.endswith("/") or n == "[Content_Types].xml":
            continue
        if n not in overrides and n.rsplit(".", 1)[-1].lower() not in defaults:
            probs.append(("part-without-content-type", n))
    for n in sorted(x for x in names if x.endswith(".rels")):
        base = posixpath.dirname(posixpath.dirname(n))
        for r in etree.fromstring(z.read(n)):
            if r.get("TargetMode") == "External":
                continue
            t = r.get("Target")
            path = t.lstrip("/") if t.startswith("/") else posixpath.normpath(posixpath.join(base, t))
            if path not in names:
                probs.append(("relationship-to-missing-part", f"{n}: {t}"))
    ext = sorted(x for x in names if re.fullmatch(r"xl/externalLinks/externalLink\d+\.xml", x))
    if ext:
        texts = [z.read("xl/workbook.xml").decode("utf-8", "replace")]
        texts += [z.read(x).decode("utf-8", "replace") for x in names if x.startswith("xl/worksheets/sheet")]
        for i, x in enumerate(ext, 1):
            used = any(f"[{i}]" in t for t in texts)
            probs.append(("external-link", f"{x} ({'used' if used else 'unused'}): Excel asks to enable / update links on open"))
    return probs


def lint(path, max_show=8, out=sys.stdout):
    z = zipfile.ZipFile(path)
    sst = z.read("xl/sharedStrings.xml") if "xl/sharedStrings.xml" in z.namelist() else None
    nsst = len(etree.fromstring(sst, etree.XMLParser(huge_tree=True)).findall(NS + "si")) if sst else 0
    nxf = len(etree.fromstring(z.read("xl/styles.xml")).find(NS + "cellXfs").findall(NS + "xf"))
    wb = etree.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in etree.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    total = 0
    pk = lint_package(z)
    if pk:
        total += len(pk)
        print(f"package: {dict(Counter(k for k, _ in pk))}", file=out)
        for k, m in pk[:max_show]:
            print(f"    {k}: {m}", file=out)
    for s in wb.find(NS + "sheets"):
        t = rels[s.get(RID)].lstrip("/")
        part = t if t.startswith("xl/") else "xl/" + t
        probs = lint_sheet(z.read(part), nsst, nxf)
        if probs:
            total += len(probs)
            print(f"{part} ({s.get('name')}): {dict(Counter(k for k, _ in probs))}", file=out)
            for k, m in probs[:max_show]:
                print(f"    {k}: {m}", file=out)
    print(f"{path}: {'clean' if not total else f'{total} problem(s)'}", file=out)
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", nargs="+")
    ap.add_argument("--max", type=int, default=8)
    a = ap.parse_args()
    sys.exit(1 if sum(lint(p, a.max) for p in a.xlsx) else 0)
