#!/usr/bin/env python3
"""
audit_drivepointified.py — the audit half of the hand-off gate: does the built workbook actually WORK?

validate_drivepointified.py checks that a tab is drivepointified (spine, markers, meaning). This script checks the
whole workbook the way a reviewer would after opening it — every formula, across every tab:

  PROTOCOL  Settings keys present and typed (spec 6.0, modelType, semver, companyId, real dates in order)
  INDEX     every schedule / report tab listed in the Index manifest; one manifest row per template id
  SPINE     every time-series tab shares one date spine and one Actual/Forecast boundary
  CALC      no error values, no uncached formulas
  REFS      no reference to a missing sheet or an out-of-range cell; single-cell refs to EMPTY cells are listed
            (fine when the formula guards them with ISNUMBER/IF, a finding when it doesn't)
  CYCLES    no circular references (Tarjan over the full cell dependency graph, ranges expanded)
  ORPHANS   no seed row nothing reads; no Key Driver that moves nothing
  HARDCODE  numeric literals inside formulas (a constant belongs on an input row)
  SUMMARY   every Budget Summary SUMIFS cell equals the sum of its spine row over its period
  IDENTITY  optional --identities JSON: row identities per tab and sum-across checks (rollups, allocations)

    python3 audit_drivepointified.py BUILT.xlsx [--identities identities.json]

identities.json (ids match exactly or by suffix "_<suffix>"; "sheets"/"sources" take fnmatch globs; "missing_as_zero"
counts an id a tab does not carry — an unmarked line that is 0 by design, e.g. no broker on one account — as 0):
    [{"type": "row", "name": "net = gross + deductions", "sheets": "Retail - *",
      "lhs": "netRevenue", "rhs": [["+", "grossSales"], ["+", "disc"], ["+", "cred"]], "tol": 0.5},
     {"type": "sum", "name": "rollup gross = Σ retailer tabs", "target": "Retail P&L!retail_gross",
      "sources": "Retail - *!grossSales", "tol": 1},
     {"type": "row", "name": "opex = Σ lines", "sheets": "Retail - *", "lhs": "operatingCosts", "missing_as_zero": true,
      "rhs": [["+", "ful"], ["+", "broker"]]},
     {"type": "sum", "name": "freight fully allocated", "target": "Freight Allocation!freight_fulTotal",
      "sources": "Retail - *!ful", "tol": 1}]

Exit code 1 on any FAIL.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime

import openpyxl
from openpyxl.utils import column_index_from_string as ci, get_column_letter as gl

SPINE_COL = 11
KD_TOKEN, KR_TOKEN = "Key Driver", "Key Result"
ERRORS = ("#REF!", "#DIV/0!", "#NAME?", "#VALUE!", "#N/A", "#NUM!", "#NULL!")
REF = re.compile(r"(?:(?:'((?:[^']|'')+)'|([A-Za-z_][A-Za-z0-9_\.]*))!)?\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?")
OK_LITERALS = {"0", "1", "2", "3", "7", "12", "100", "0.5"}


class Report:
    def __init__(self):
        self.lines: list[tuple[str, str, str]] = []

    def add(self, level, group, msg):
        self.lines.append((level, group, msg))

    def ok(self, cond, group, msg, bad="FAIL"):
        self.add("PASS" if cond else bad, group, msg)

    def counts(self):
        return {k: sum(1 for x in self.lines if x[0] == k) for k in ("PASS", "WARN", "FAIL", "INFO")}

    def render(self):
        order = {"FAIL": 0, "WARN": 1, "INFO": 2, "PASS": 3}
        return "\n".join(f"{l:5} {g:9} {m}" for l, g, m in sorted(self.lines, key=lambda x: order[x[0]]))


def _is_formula(v):
    return isinstance(v, str) and v.startswith("=")


def _spine(ws):
    ds, c = [], SPINE_COL
    while isinstance(ws.cell(2, c).value, (datetime, date)):
        ds.append(ws.cell(2, c).value)
        c += 1
    return ds


def _ids(ws):
    return {ws.cell(r, 2).value: r for r in range(1, ws.max_row + 1) if isinstance(ws.cell(r, 2).value, str)}


def _match_id(ids: dict, key: str):
    if key in ids:
        return ids[key]
    hits = [r for k, r in ids.items() if k.endswith("_" + key)]
    return hits[0] if len(hits) == 1 else None


def audit(path: str, identities: str | None = None) -> Report:
    rep = Report()
    wf = openpyxl.load_workbook(path)
    wv = openpyxl.load_workbook(path, data_only=True)
    names = wf.sheetnames
    rtab = lambda n: bool(re.match(r"^[RDF]\s*-", n))  # noqa: E731

    # ---- PROTOCOL --------------------------------------------------------------------------------
    st = {}
    if "Settings" in names:
        for r in wv["Settings"].iter_rows(values_only=True):
            if len(r) > 3 and isinstance(r[1], str) and r[1].startswith("settings."):
                st[r[1]] = r[3]
    for k in ("smartmodelSpec", "modelType", "modelVersion", "modelName", "companyName", "companyId",
              "historicalStartDate", "modelStartDate", "lastDateActuals"):
        rep.ok(st.get(f"settings.{k}") not in (None, ""), "PROTOCOL", f"settings.{k} = {st.get(f'settings.{k}')!r}")
    rep.ok(str(st.get("settings.smartmodelSpec")) == "6.0", "PROTOCOL", "smartmodelSpec is 6.0")
    rep.ok(st.get("settings.modelType") in ("model", "template"), "PROTOCOL", "modelType is model | template")
    rep.ok(bool(re.match(r"^\d+\.\d+\.\d+$", str(st.get("settings.modelVersion")))), "PROTOCOL", "modelVersion is semver")
    hsd, msd, lda = (st.get(f"settings.{k}") for k in ("historicalStartDate", "modelStartDate", "lastDateActuals"))
    if all(isinstance(x, datetime) for x in (hsd, msd, lda)):
        rep.ok(hsd < msd, "PROTOCOL", f"historicalStartDate {hsd:%Y-%m-%d} < modelStartDate {msd:%Y-%m-%d}")
    else:
        rep.add("FAIL", "PROTOCOL", "historicalStartDate / modelStartDate / lastDateActuals must be real dates")

    # ---- INDEX + metadata ------------------------------------------------------------------------
    listed, manifest_ids = set(), Counter()
    if "Index" in names:
        I = wv["Index"]
        hdr = next((r for r in range(1, I.max_row + 1) if I.cell(r, 2).value == "Template ID"), None)
        if hdr:
            for r in range(hdr + 1, I.max_row + 1):
                tid, sheets = I.cell(r, 2).value, I.cell(r, 4).value
                if tid:
                    manifest_ids[tid] += 1
                    listed |= {x.strip() for x in str(sheets or "").split(",") if x.strip()}
    rep.ok("Index" in names and bool(manifest_ids), "INDEX", f"Index manifest present ({len(manifest_ids)} template ids)")
    content = [n for n in names if n not in ("Index", "Settings", "Plan Settings") and not rtab(n)]
    missing = [n for n in content if n not in listed]
    rep.ok(not missing, "INDEX", f"every schedule / report tab is listed in the manifest (missing: {missing[:6]})")
    dups = {k: v for k, v in manifest_ids.items() if v > 1}
    rep.ok(not dups, "INDEX", f"one manifest row per template id — list a multi-sheet template's sheets comma-separated "
                              f"(duplicates: {dups})", "WARN")
    for n in content:
        ws = wf[n]
        tid = next((ws.cell(r, 4).value for r in range(1, 25) if ws.cell(r, 2).value == "metadata___template_id"), None)
        if not tid:
            rep.add("FAIL", "INDEX", f"{n}: no metadata___template_id")
        elif tid not in manifest_ids:
            rep.add("FAIL", "INDEX", f"{n}: template id {tid!r} not in the Index manifest")
        col = str(ws.sheet_properties.tabColor.rgb if ws.sheet_properties.tabColor is not None else "")[-6:]
        want = "64B0FF" if wv[n]["C2"].value != "End of Period" or not _spine(wv[n]) else "FFC000"
        if col not in (want, "63AEFF" if want == "64B0FF" else want):
            rep.add("WARN", "TABS", f"{n}: tab colour {col or 'none'} (schedule FFC000 / report 64B0FF)")

    # ---- SPINE -----------------------------------------------------------------------------------
    ts = [n for n in content if wv[n]["C2"].value == "End of Period" and _spine(wv[n])]
    ref_sp = ref_fl = None
    for n in ts:
        sp = _spine(wv[n])
        fl = [wv[n].cell(3, SPINE_COL + i).value for i in range(len(sp))]
        if ref_sp is None:
            ref_sp, ref_fl, ref_n = sp, fl, n
        if sp != ref_sp:
            rep.add("FAIL", "SPINE", f"{n}: date spine differs from {ref_n}")
        elif fl != ref_fl:
            rep.add("FAIL", "SPINE", f"{n}: Actual/Forecast boundary differs from {ref_n}")
    if ref_sp:
        rep.add("PASS", "SPINE", f"{len(ts)} time-series tabs checked against one spine "
                                 f"{ref_sp[0]:%b-%y}…{ref_sp[-1]:%b-%y} (Actual ×{ref_fl.count('Actual')})")
    ncols = len(ref_sp or [])

    # ---- walk every formula: CALC, REFS, HARDCODE, graph -------------------------------------------
    graph: dict = {}
    errors, uncached, bad_sheet, oob = [], [], [], []
    empty_refs, literals = Counter(), Counter()
    refd_rows = Counter()
    maxrc = {n: (wf[n].max_row, wf[n].max_column) for n in names}
    for n in names:
        ws, vs = wf[n], wv[n]
        grp = re.sub(r" - .*", " - *", n) if n.count(" - ") and not rtab(n) else n
        for row in ws.iter_rows():
            for c in row:
                v, cv = c.value, vs[c.coordinate].value
                if isinstance(cv, str) and cv.startswith(ERRORS):
                    errors.append(f"{n}!{c.coordinate} {cv}")
                if not _is_formula(v):
                    continue
                if cv is None:
                    uncached.append(f"{n}!{c.coordinate}")
                f = re.sub(r'"[^"]*"', '""', v[1:])
                deps = set()
                for m in REF.finditer(f):
                    if m.group(2) and m.group(2).upper() in ("TRUE", "FALSE"):
                        continue
                    if not m.group(1) and not m.group(2) and m.start() and (f[m.start() - 1].isalnum() or f[m.start() - 1] in "_."):
                        continue
                    s = (m.group(1) or m.group(2) or n).replace("''", "'")
                    if s not in maxrc:
                        bad_sheet.append(f"{n}!{c.coordinate} → {s}")
                        continue
                    c1, r1 = ci(m.group(3)), int(m.group(4))
                    c2, r2 = (ci(m.group(5)), int(m.group(6))) if m.group(5) else (c1, r1)
                    if r2 > 1048576 or c2 > 16384:
                        oob.append(f"{n}!{c.coordinate}")
                        continue
                    if (r2 - r1 + 1) * (c2 - c1 + 1) <= 5000:
                        for rr in range(r1, r2 + 1):
                            refd_rows[(s, rr)] += 1
                            for cc in range(c1, c2 + 1):
                                deps.add((s, rr, cc))
                    if not m.group(5) and wf[s].cell(r1, c1).value is None:
                        empty_refs[(grp, s, "guarded" if re.search(r"ISNUMBER|ISBLANK|IF\(", f) else "unguarded")] += 1
                graph[(n, c.row, c.column)] = deps
                stripped = REF.sub("", f)
                lits = {x for x in re.findall(r"(?<![A-Za-z0-9_\$\.])(\d+\.?\d*)(?![\d:A-Za-z])", stripped)} - OK_LITERALS
                if lits:
                    literals[(grp, tuple(sorted(lits))[:3])] += 1
    rep.ok(not errors, "CALC", f"no error values ({len(errors)}: {errors[:4]})")
    rep.ok(not uncached, "CALC", f"every formula has a cached value ({len(uncached)} without: {uncached[:4]}) — recalc "
                                 "before hand-off")
    rep.ok(not bad_sheet, "REFS", f"no reference to a missing sheet ({len(bad_sheet)}: {bad_sheet[:4]})")
    rep.ok(not oob, "REFS", f"no out-of-range reference ({len(oob)})")
    for (g, s, kind), k in sorted(empty_refs.items()):
        rep.add("INFO" if kind == "guarded" else "WARN", "REFS", f"{k} single-cell refs from {g} to EMPTY cells on {s} "
                f"({kind}{'' if kind == 'guarded' else ' — guard with ISNUMBER/IF or fill the source'})")
    for (g, lits), k in literals.most_common(8):
        rep.add("WARN", "HARDCODE", f"{k} formulas on {g} contain literal(s) {', '.join(lits)} — put constants on an input row")

    # ---- CYCLES (iterative Tarjan) ---------------------------------------------------------------
    index, low, onst, stack, cycles, ctr = {}, {}, set(), [], [], [0]
    for root in graph:
        if root in index:
            continue
        work = [(root, iter(graph[root]))]
        index[root] = low[root] = ctr[0]; ctr[0] += 1; stack.append(root); onst.add(root)  # noqa: E702
        while work:
            node, it = work[-1]
            nxt = next((d for d in it if d in graph), None)
            if nxt is not None:
                if nxt not in index:
                    index[nxt] = low[nxt] = ctr[0]; ctr[0] += 1; stack.append(nxt); onst.add(nxt)  # noqa: E702
                    work.append((nxt, iter(graph[nxt])))
                elif nxt in onst:
                    low[node] = min(low[node], index[nxt])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop(); onst.discard(w); comp.append(w)  # noqa: E702
                    if w == node:
                        break
                if len(comp) > 1 or node in graph[node]:
                    cycles.append(comp)
    rep.ok(not cycles, "CYCLES", f"no circular references ({len(cycles)} groups: "
           + "; ".join(f"{c[0][0]}!{gl(c[0][2])}{c[0][1]} +{len(c) - 1}" for c in cycles[:4]) + ")")

    # ---- ORPHANS ---------------------------------------------------------------------------------
    for n in names:
        ws = wf[n]
        if rtab(n):
            orph = [ws.cell(r, 3).value or ws.cell(r, 2).value for r in range(1, ws.max_row + 1)
                    if str(ws.cell(r, 2).value or "").startswith("seed___") and not refd_rows[(n, r)]]
            if orph:
                rep.add("WARN", "ORPHANS", f"{n}: {len(orph)} seed rows nothing reads ({orph[:3]})")
        else:
            dead = [ws.cell(r, 3).value for r in range(1, ws.max_row + 1)
                    if KD_TOKEN in str(ws.cell(r, 1).value or "") and not refd_rows[(n, r)]]
            if dead:
                rep.add("WARN", "ORPHANS", f"{n}: {len(dead)} Key Drivers no formula reads — they move nothing ({dead[:3]})")
    rep.add("PASS", "ORPHANS", "seed rows and Key Drivers checked for readers")

    # ---- SUMMARY = Σ spine -------------------------------------------------------------------------
    sumre = re.compile(r"^=SUMIFS\('([^']+)'!\$K\$(\d+):\$([A-Z]+)\$\d+,'[^']+'!\$K\$2:\$[A-Z]+\$2,\">=\"&([A-Z]+)\$(\d+),"
                       r"'[^']+'!\$K\$2:\$[A-Z]+\$2,\"<=\"&[A-Z]+\$(\d+)\)$")
    n_sum = bad_sum = 0
    for n in content:
        ws, vs = wf[n], wv[n]
        for row in ws.iter_rows():
            for c in row:
                m = sumre.match(str(c.value or ""))
                if not m:
                    continue
                src, r, _, pc, r0, r1 = m.groups()
                a, b = ws[f"{pc}{r0}"].value, ws[f"{pc}{r1}"].value
                sv, sr = wv[src], int(r)
                tot = sum(float(sv.cell(sr, SPINE_COL + i).value or 0) for i, d in enumerate(_spine(sv))
                          if a and b and a <= d <= b)
                n_sum += 1
                if abs(tot - float(vs[c.coordinate].value or 0)) > 0.5:
                    bad_sum += 1
    if n_sum:
        rep.ok(bad_sum == 0, "SUMMARY", f"{n_sum - bad_sum}/{n_sum} summary cells equal Σ of their spine row over the period")

    # ---- IDENTITIES --------------------------------------------------------------------------------
    if identities:
        spec = json.load(open(identities))
        vals = lambda n, r: [float(wv[n].cell(r, SPINE_COL + i).value or 0) for i in range(ncols)]  # noqa: E731
        for t in spec:
            tol, bad, checked = float(t.get("tol", 0.5)), [], 0
            if t["type"] == "row":
                for n in [x for x in names if fnmatch.fnmatch(x, t["sheets"])]:
                    ids = _ids(wf[n])
                    lr = _match_id(ids, t["lhs"])
                    rr = [(sg, _match_id(ids, k)) for sg, k in t["rhs"]]
                    if t.get("missing_as_zero"):          # an account that doesn't carry a line (unmarked, = 0)
                        rr = [(sg, r) for sg, r in rr if r is not None]
                    if lr is None or any(r is None for _, r in rr):
                        bad.append(f"{n}: ids not found")
                        continue
                    lhs = vals(n, lr)
                    rhs = [sum((1 if sg == "+" else -1) * vals(n, r)[i] for sg, r in rr) for i in range(ncols)]
                    checked += 1
                    d = max(abs(x - y) for x, y in zip(lhs, rhs))
                    if d > tol:
                        bad.append(f"{n} (max Δ {d:,.2f})")
            else:
                tn, tk = t["target"].split("!", 1)
                sg_, sk = t["sources"].split("!", 1)
                tr = _match_id(_ids(wf[tn]), tk)
                tot = [0.0] * ncols
                for n in [x for x in names if fnmatch.fnmatch(x, sg_)]:
                    r = _match_id(_ids(wf[n]), sk)
                    if r is None:
                        if not t.get("missing_as_zero"):
                            bad.append(f"{n}: {sk} not found")
                        continue
                    checked += 1
                    tot = [a + b for a, b in zip(tot, vals(n, r))]
                if tr is None:
                    bad.append(f"target {t['target']} not found")
                else:
                    d = max(abs(x - y) for x, y in zip(tot, vals(tn, tr)))
                    if d > tol:
                        bad.append(f"max Δ {d:,.2f}")
            rep.ok(not bad and checked > 0, "IDENTITY", f"{t['name']} ({checked} checked{'; off: ' + '; '.join(bad[:4]) if bad else ''})")
    return rep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--identities")
    a = ap.parse_args()
    rep = audit(a.xlsx, a.identities)
    print(f"# audit_drivepointified — {a.xlsx.split('/')[-1]}\n")
    print(rep.render())
    c = rep.counts()
    print(f"\n{c['PASS']} pass · {c['WARN']} warn · {c['FAIL']} fail · {c['INFO']} info")
    return 1 if c["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
