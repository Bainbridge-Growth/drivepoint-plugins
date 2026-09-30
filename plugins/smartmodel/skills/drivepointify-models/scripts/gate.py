#!/usr/bin/env python3
"""
gate.py — the whole hand-off gate in one call. Model.save() runs it automatically; run it by hand on any file:

    python3 gate.py BUILT.xlsx [--ties ties.json] [--identities identities.json] [--no-flex] [--company-id ID]
                    [--no-style] [--allow-bands "Tab!COL,..."]

Steps (all on the exact file you deliver):
  1. validate_drivepointified.py   — is every tab drivepointified (spine, markers, meaning, ties)?
  2. audit_drivepointified.py      — does the workbook work (broken refs, circular refs, orphans, hard-codes,
                                     summary = Σ spine, identities / allocation conservation)?
  3. flex test                     — nudge every Key Driver's budget inputs ×1.1 on a copy, recalculate, and prove:
                                     0 error cells, Actual months unchanged, and the Key Results move
  4. Gate 0 — Excel opens it clean: lint_xlsx.py (no repair prompt / "Removed Records"), find_circular.py
                                     (every loop Excel would flag, untaken IF branches included), style_gaps.py
                                     (no white gaps in colour bands; --allow "Tab!COL" for deliberate fills)
  5. style (optional)              — drivepoint-customers tools/smartmodel-style check_cell_roles.py +
                                     check_format.py, when that repo is on disk (sibling or $SMARTMODEL_STYLE_TOOLS)
  6. post_validate (optional)      — drivepoint-smartmodel-service's protocol check, when that repo is on disk
                                     (sibling checkout or $DRIVEPOINT_SMARTMODEL_SERVICE)

Exit code 1 when any step fails. Paste the summary lines into the hand-off.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPINE_COL = 11


def _validator(path, ties):
    args = [sys.executable, str(HERE / "validate_drivepointified.py"), str(path)] + (["--ties", str(ties)] if ties else [])
    p = subprocess.run(args, capture_output=True, text=True)
    out = p.stdout + p.stderr
    fails = [l for l in out.splitlines() if l.startswith("FAIL")]
    tail = next((l for l in reversed(out.splitlines()) if "pass ·" in l), out.strip()[-200:])
    return p.returncode == 0, f"validator  {tail}" + "".join(f"\n  {l}" for l in fails[:10])


def _audit(path, identities):
    from audit_drivepointified import audit
    rep = audit(str(path), str(identities) if identities else None)
    c = rep.counts()
    bad = [f"{l:5} {g:9} {m}" for l, g, m in rep.lines if l in ("FAIL", "WARN")]
    return c["FAIL"] == 0, (f"audit      {c['PASS']} pass · {c['WARN']} warn · {c['FAIL']} fail"
                            + "".join(f"\n  {l}" for l in bad[:12]))


def _flex(path):
    """Perturb every Key Driver budget input ×1.1 (0 → +0.01 for %s is skipped: a zero driver stays zero), recalc a copy."""
    import openpyxl
    import drivepointify_engine as eng
    wf = openpyxl.load_workbook(path)
    base = openpyxl.load_workbook(path, data_only=True)
    moved_tabs, n_inputs, marked = set(), 0, {}
    for ws in wf.worksheets:
        if ws["C2"].value != "End of Period":
            continue
        flags = [base[ws.title].cell(3, SPINE_COL + i).value for i in range(200)]
        n = next((i for i, f in enumerate(flags) if f not in ("Actual", "Forecast")), len(flags))
        act = [SPINE_COL + i for i in range(n) if flags[i] == "Actual"]
        fc = [SPINE_COL + i for i in range(n) if flags[i] == "Forecast"]
        rows = [r for r in range(17, ws.max_row + 1) if "Key" in str(ws.cell(r, 1).value or "")]
        marked[ws.title] = (rows, act, fc)
        for r in rows:
            if "Driver" not in str(ws.cell(r, 1).value):
                continue
            for c in fc:
                v = ws.cell(r, c).value
                if isinstance(v, (int, float)) and not isinstance(v, bool) and v != 0:
                    ws.cell(r, c).value = v * 1.1
                    n_inputs += 1
                    moved_tabs.add(ws.title)
    if not n_inputs:
        return True, "flex       skipped — no non-zero Key Driver inputs"
    with tempfile.TemporaryDirectory() as td:
        raw, out = Path(td) / "flex_raw.xlsx", Path(td) / "flex.xlsx"
        wf.save(raw)
        if not eng.recalc_workbook(raw, out):
            return True, "flex       skipped — `formulas` package not installed (pip install formulas)"
        fx = openpyxl.load_workbook(out, data_only=True)
        errs, hist_moved, still = [], [], []
        for t, (rows, act, fc) in marked.items():
            for rr in fx[t].iter_rows():
                for c in rr:
                    if isinstance(c.value, str) and c.value.startswith("#"):
                        errs.append(f"{t}!{c.coordinate}")
            changed = False
            for r in rows:
                for c in act:
                    a, b = base[t].cell(r, c).value, fx[t].cell(r, c).value
                    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) > 1e-6 * max(1, abs(a)):
                        hist_moved.append(f"{t}!{fx[t].cell(r, c).coordinate}")
                if "Result" in str(wf[t].cell(r, 1).value):
                    for c in fc:
                        a, b = base[t].cell(r, c).value, fx[t].cell(r, c).value
                        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) > 1e-9:
                            changed = True
                            break
            has_results = any("Result" in str(wf[t].cell(r, 1).value) for r in rows)
            if t in moved_tabs and has_results and not changed:
                still.append(t)
    ok = not errs and not hist_moved
    msg = (f"flex       {n_inputs} Key Driver inputs ×1.1 on {len(moved_tabs)} tabs → {len(errs)} error cells, "
           f"{len(hist_moved)} Actual-month cells moved; Key Results moved on every driven tab except {len(still)}")
    if errs:
        msg += f"\n  FAIL errors after flex: {errs[:5]}"
    if hist_moved:
        msg += f"\n  FAIL history moved (drivers leak into Actual months): {hist_moved[:5]}"
    if still:
        msg += f"\n  WARN drivers changed but no Key Result on the same tab moved (zero volumes?): {still[:5]}"
    return ok, msg


def _script(label, args):
    p = subprocess.run([sys.executable] + [str(a) for a in args], capture_output=True, text=True)
    out = [l for l in (p.stdout + p.stderr).splitlines() if l.strip()]
    tail = out[-1] if out else ""
    detail = "" if p.returncode == 0 else "".join(f"\n  {l[:160]}" for l in out[:10])
    return p.returncode == 0, f"{label:10} {'clean' if p.returncode == 0 else 'FAIL'} — {tail[:150]}" + detail


def _gate0(path, allow=""):
    """Gate 0: what Excel itself does on open — repair, circular-reference warning, broken colour bands."""
    steps = [_script("excel-lint", [HERE / "lint_xlsx.py", path]),
             _script("circular", [HERE / "find_circular.py", path]),
             _script("bands", [HERE / "style_gaps.py", path] + (["--allow", allow] if allow else []))]
    return steps


def _style(path):
    roots = [os.environ.get("SMARTMODEL_STYLE_TOOLS", "")] + [str(p / "drivepoint-customers" / "tools" / "smartmodel-style")
                                                              for p in list(HERE.parents)[:8]]
    d = next((Path(r) for r in roots if r and (Path(r) / "check_cell_roles.py").is_file()), None)
    if not d:
        return [(True, "style      skipped — tools/smartmodel-style not found (set $SMARTMODEL_STYLE_TOOLS)")]
    return [_script("roles", [d / "check_cell_roles.py", path]), _script("format", [d / "check_format.py", path])]


def _post_validate(path, company_id):
    roots = [os.environ.get("DRIVEPOINT_SMARTMODEL_SERVICE", "")] + [str(p / "drivepoint-smartmodel-service")
                                                                        for p in list(HERE.parents)[:8]]
    src = next((Path(r) / "src" for r in roots if r and (Path(r) / "src" / "smartmodel_service").is_dir()), None)
    if not src:
        return True, "post_valid skipped — drivepoint-smartmodel-service not found (set $DRIVEPOINT_SMARTMODEL_SERVICE)"
    sys.path.insert(0, str(src))
    try:
        from smartmodel_service.smartmodel_utils.post_validate import post_validate
    except Exception as e:  # noqa: BLE001
        return True, f"post_valid skipped — import failed ({e})"
    r = post_validate(str(path), expected_company_id=company_id) if company_id else post_validate(str(path))
    warns = [f"{c['name']}: {str(c['detail'])[:90]}" for c in r["checks"] if not c["passed"]]
    return r["error_count"] == 0, (f"post_valid {r['error_count']} errors · {r['warning_count']} warnings"
                                   + "".join(f"\n  {w}" for w in warns[:8]))


def run_gate(path, *, ties=None, identities=None, flex=True, company_id=None, post=True, style=True,
             allow_bands="") -> tuple[bool, str]:
    steps = [_validator(path, ties), _audit(path, identities)] + _gate0(path, allow_bands)
    if style:
        steps += _style(path)
    if flex:
        steps.append(_flex(path))
    if post:
        steps.append(_post_validate(path, company_id))
    ok = all(s[0] for s in steps)
    head = f"# hand-off gate — {Path(path).name}: {'PASS' if ok else 'FAIL'}"
    return ok, "\n".join([head] + [("✓ " if s[0] else "✗ ") + s[1] for s in steps])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--ties")
    ap.add_argument("--identities")
    ap.add_argument("--company-id")
    ap.add_argument("--no-flex", action="store_true")
    ap.add_argument("--no-post-validate", action="store_true")
    ap.add_argument("--no-style", action="store_true")
    ap.add_argument("--allow-bands", default="", help='deliberate one-column fills for style_gaps, e.g. "P&L!G"')
    a = ap.parse_args()
    ok, text = run_gate(a.xlsx, ties=a.ties, identities=a.identities, flex=not a.no_flex, company_id=a.company_id,
                        post=not a.no_post_validate, style=not a.no_style, allow_bands=a.allow_bands)
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
