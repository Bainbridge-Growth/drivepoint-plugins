#!/usr/bin/env python3
"""Find every circular reference Excel would flag in an .xlsx, from the raw XML.

Excel builds its dependency tree from every reference in a formula, whichever IF branch is
live, so a loop through an untaken branch still raises the "circular reference" warning.
This does the same: each formula cell depends on every cell its formula text references
(cells, ranges, whole rows/columns, defined names), and the strongly connected components
of that graph are the loops.

    python3 find_circular.py <book.xlsx> [--json out.json] [--max 40]

Limits (it errs on the side of reporting): OFFSET / INDIRECT are taken at their literal
arguments, not the range they resolve to; INDEX(range, ...) depends on the whole range
(as in Excel). External-workbook references are ignored.
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
import zipfile
from collections import defaultdict

from lxml import etree

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
C, F, ROW = f"{{{NS}}}c", f"{{{NS}}}f", f"{{{NS}}}row"
MAXR, MAXC = 1048576, 16384


def col2n(s: str) -> int:
    n = 0
    for ch in s:
        n = n * 26 + ord(ch) - 64
    return n


def n2col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


SHEET = r"(?:'((?:[^']|'')+)'|([A-Za-z_][\w\.]*))!"
CELL = r"(\$?)([A-Z]{1,3})(\$?)(\d{1,7})"
REF = re.compile(
    rf"(?<![\w\.\]])(?:\[\d+\])?(?:{SHEET})?"
    rf"(?:{CELL}(?::{CELL})?(?![\w\(])"           # A1 or A1:B2
    rf"|(\$?)([A-Z]{{1,3}}):(\$?)([A-Z]{{1,3}})(?![\w\(])"  # A:B
    rf"|(\$?)(\d{{1,7}}):(\$?)(\d{{1,7}})(?![\w\(]))"      # 1:2
)
NAME = re.compile(r"(?<![\w\.\]!'])([A-Za-z_\\][\w\.]*)(?![\w\(!])")
STR = re.compile(r'"(?:[^"]|"")*"')


def strip_strings(f: str) -> str:
    return STR.sub('""', f)


def parse_refs(f: str):
    """[(sheet|None, ext, kind, parts)] with relative flags kept, for later shifting."""
    out = []
    for m in REF.finditer(f):
        g = m.groups()
        ext = m.group(0).startswith("[")
        sheet = g[0].replace("''", "'") if g[0] else g[1]
        if g[3] is not None:      # cell / cell range
            a = (g[2] == "", col2n(g[3]), g[4] == "", int(g[5]))
            b = (g[6] == "", col2n(g[7]), g[8] == "", int(g[9])) if g[7] else a
            out.append((sheet, ext, "c", a, b))
        elif g[11] is not None:   # columns
            out.append((sheet, ext, "col", (g[10] == "", col2n(g[11])), (g[12] == "", col2n(g[13]))))
        elif g[15] is not None:   # rows
            out.append((sheet, ext, "row", (g[14] == "", int(g[15])), (g[16] == "", int(g[17]))))
    return out


def shift(ref, dr, dc):
    sheet, ext, kind, a, b = ref
    if kind == "c":
        def s(p):
            rc, c, rr, r = p
            return (rc, c + dc if rc else c, rr, r + dr if rr else r)
        return (sheet, ext, kind, s(a), s(b))
    if kind == "col":
        return (sheet, ext, kind, (a[0], a[1] + dc if a[0] else a[1]), (b[0], b[1] + dc if b[0] else b[1]))
    return (sheet, ext, kind, (a[0], a[1] + dr if a[0] else a[1]), (b[0], b[1] + dr if b[0] else b[1]))


def box(ref):
    _, _, kind, a, b = ref
    if kind == "c":
        r1, r2 = sorted((a[3], b[3])); c1, c2 = sorted((a[1], b[1]))
    elif kind == "col":
        r1, r2 = 1, MAXR; c1, c2 = sorted((a[1], b[1]))
    else:
        c1, c2 = 1, MAXC; r1, r2 = sorted((a[1], b[1]))
    return r1, c1, r2, c2


def load(path):
    z = zipfile.ZipFile(path)
    wb = etree.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in etree.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    sheets = []
    for s in wb.find(f"{{{NS}}}sheets"):
        t = rels[s.get(RID)].lstrip("/")
        sheets.append((s.get("name"), t if t.startswith("xl/") else "xl/" + t))
    names = {}  # (scope sheet name | None, NAME) -> text
    dn = wb.find(f"{{{NS}}}definedNames")
    if dn is not None:
        for d in dn:
            scope = sheets[int(d.get("localSheetId"))][0] if d.get("localSheetId") else None
            names[(scope, d.get("name").upper())] = d.text or ""
    formulas = {}  # sheet -> {(r,c): [refs]}
    texts = {}
    for name, p in sheets:
        cells = {}
        masters = {}
        for _, c in etree.iterparse(z.open(p), tag=C, huge_tree=True):
            f = c.find(F)
            if f is not None:
                m = re.fullmatch(r"([A-Z]+)(\d+)", c.get("r"))
                rc = (int(m.group(2)), col2n(m.group(1)))
                txt = f.text or ""
                if f.get("t") == "shared":
                    si = f.get("si")
                    if txt:
                        masters[si] = (rc, parse_refs(strip_strings(txt)), txt)
                        cells[rc] = masters[si][1]
                        texts[(name, rc)] = txt
                    elif si in masters:
                        (mr, mc), refs, mt = masters[si]
                        cells[rc] = [shift(x, rc[0] - mr, rc[1] - mc) for x in refs]
                        texts[(name, rc)] = f"<shared {n2col(mc)}{mr}> {mt}"
                else:
                    s = strip_strings(txt)
                    refs = parse_refs(s)
                    for nm in set(NAME.findall(REF.sub(" ", s))):
                        key = (name, nm.upper()) if (name, nm.upper()) in names else (None, nm.upper())
                        if key in names:
                            refs += [x for x in parse_refs(strip_strings(names[key])) if x[0]]
                    cells[rc] = refs
                    texts[(name, rc)] = txt
            c.clear()
        formulas[name] = cells
    return sheets, formulas, texts


def build(formulas):
    ids, keys = {}, []
    for sh, cells in formulas.items():
        for rc in cells:
            ids[(sh, rc)] = len(keys); keys.append((sh, rc))
    bycol = defaultdict(lambda: defaultdict(list))
    for sh, cells in formulas.items():
        for (r, c) in cells:
            bycol[sh][c].append(r)
    for sh in bycol:
        for c in bycol[sh]:
            bycol[sh][c].sort()
    lower = {s.lower(): s for s in formulas}
    rng_ids = {}
    adj = [None] * len(keys)
    rng_adj = []
    for sh, cells in formulas.items():
        for rc, refs in cells.items():
            out = []
            for ref in refs:
                if ref[1]:
                    continue
                tsh = lower.get((ref[0] or sh).lower())
                if tsh is None:
                    continue
                r1, c1, r2, c2 = box(ref)
                if r1 == r2 and c1 == c2:
                    t = ids.get((tsh, (r1, c1)))
                    if t is not None:
                        out.append(t)
                    continue
                k = (tsh, r1, c1, r2, c2)
                rid = rng_ids.get(k)
                if rid is None:
                    members = []
                    for col, rows in bycol[tsh].items():
                        if c1 <= col <= c2:
                            i = bisect.bisect_left(rows, r1)
                            j = bisect.bisect_right(rows, r2)
                            members.extend(ids[(tsh, (rr, col))] for rr in rows[i:j])
                    rid = len(keys) + len(rng_adj)
                    rng_ids[k] = rid
                    rng_adj.append(members)
                out.append(rid)
            adj[ids[(sh, rc)]] = out
    return keys, adj + rng_adj


def scc(adj):
    """Iterative Tarjan. Returns components with >1 node or a self-loop."""
    n = len(adj)
    index = [-1] * n; low = [0] * n; onst = [False] * n
    st, comps, idx = [], [], 0
    for v0 in range(n):
        if index[v0] != -1:
            continue
        work = [(v0, 0)]
        index[v0] = low[v0] = idx; idx += 1; st.append(v0); onst[v0] = True
        while work:
            v, i = work[-1]
            nb = adj[v]
            if i < len(nb):
                work[-1] = (v, i + 1)
                w = nb[i]
                if index[w] == -1:
                    index[w] = low[w] = idx; idx += 1; st.append(w); onst[w] = True
                    work.append((w, 0))
                elif onst[w]:
                    low[v] = min(low[v], index[w])
            else:
                work.pop()
                if work:
                    u = work[-1][0]
                    low[u] = min(low[u], low[v])
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = st.pop(); onst[w] = False; comp.append(w)
                        if w == v:
                            break
                    if len(comp) > 1 or v in adj[v]:
                        comps.append(comp)
    return comps


def summarize(comps, keys, texts):
    out = []
    for comp in comps:
        cells = [keys[i] for i in comp if i < len(keys)]
        by = defaultdict(set)
        for sh, (r, c) in cells:
            by[sh].add(r)
        rows = {sh: sorted(rs) for sh, rs in by.items()}
        sample = [f"{sh}!{n2col(c)}{r}: ={texts.get((sh,(r,c)),'')[:160]}" for sh, (r, c) in sorted(cells)[:6]]
        out.append({"cells": len(cells), "rows": rows, "sample": sample,
                    "all": [f"{sh}!{n2col(c)}{r}" for sh, (r, c) in sorted(cells)]})
    return sorted(out, key=lambda d: -d["cells"])


def find(path):
    sheets, formulas, texts = load(path)
    keys, adj = build(formulas)
    return summarize(scc(adj), keys, texts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx"); ap.add_argument("--json"); ap.add_argument("--max", type=int, default=40)
    a = ap.parse_args()
    sys.setrecursionlimit(10000)
    loops = find(a.xlsx)
    print(f"{len(loops)} circular reference loop(s), {sum(l['cells'] for l in loops)} cells")
    for l in loops[: a.max]:
        print(f"- {l['cells']} cells: " + "; ".join(f"{sh} rows {rs[:12]}{'…' if len(rs) > 12 else ''}" for sh, rs in l["rows"].items()))
        for s in l["sample"][:3]:
            print("     ", s)
    if a.json:
        json.dump(loops, open(a.json, "w"), indent=1)
    return 1 if loops else 0


if __name__ == "__main__":
    sys.exit(main())
