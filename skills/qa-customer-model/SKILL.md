---
name: qa-customer-model
description: Validate a SmartModel workbook for structural correctness, add-in compatibility, and data integrity. Use after building or converting a customer model, or when a workbook isn't working correctly with the Drivepoint add-in. Triggers on "validate this model", "QA the workbook", "check if this SmartModel is correct", "the add-in doesn't recognize this model", "run post-validate".
---

# QA Customer Model

**Purpose**: Verify that a SmartModel workbook is structurally correct, compatible with the Drivepoint Excel add-in, and contains valid business data. Catches the issues that cause models to fail in production — missing WebExtension, empty companyId, broken formulas, misaligned cutover.

**Prerequisite**: The `smartmodel-protocol` skill must be loaded for v6 grammar details.

---

## Phase 1 — Structural Validation (post_validate)

Run the smartmodel-service's comprehensive validation suite.

### Step 1.1 — Run post_validate

```python
import sys
sys.path.insert(0, '<path-to>/drivepoint-smartmodel-service/src')
from smartmodel_service.smartmodel_utils.post_validate import post_validate

report = post_validate("workbook.xlsx")
print(f"Passed: {report['passed']}  Errors: {report['error_count']}  Warnings: {report['warning_count']}")
for check in report['checks']:
    if not check['passed']:
        severity = 'ERROR' if check['severity'] == 'error' else 'WARN'
        print(f"  {severity}: [{check['group']}] {check['name']} — {check['detail']}")
```

This checks 15+ groups:
- **Structure**: Settings tab exists, Index tab exists, minimum sheet count
- **Settings**: Required fields present (`smartmodelSpec`, `modelVersion`, `modelName`, `modelType`, `companyName`), correct tab color, Menlo font header, B-E column layout
- **Index**: Has template entries, white tab color
- **Formulas**: No `#REF!` errors anywhere
- **Calculation**: `calcMode` is auto
- **WebExtension**: Present in xlsx zip
- **Pane Integrity**: No dangling pane selections (openpyxl bug)
- **Header Block**: Row 1 fill, row 2 label
- **Gridlines**: OFF on all sheets
- **Freeze Panes**: Schedule sheets freeze at D5
- **Schedule Layout**: Column A width >= 15, column B grouped
- **Tab Colors**: Settings has dark gray
- **Column B**: No legacy alphanumeric IDs
- **Styles**: Heading chrome, input-cell drift, referenced-metric drift
- **Cutover**: Settings date sanity, date spine monotonicity, cutover labels, formula switch
- **R-Tabs**: Date header alignment with schedule spine

### Step 1.2 — Interpret results

**Errors** (severity="error") must be fixed. The workbook will malfunction.

**Warnings** (severity="warning") should be reviewed. Common acceptable warnings:
- `heading_chrome` — row 2/3 fill colors on custom templates may differ from standard
- `settings_missing` — dates stored as strings instead of Excel dates (fix if possible)
- `Schedule col B grouped` — outline level not set (cosmetic)

---

## Phase 2 — Add-in Compatibility

These checks verify the workbook will work with the Drivepoint Excel add-in. The add-in reads Settings, matches `companyId` to the user's account, and gates features accordingly.

### Step 2.1 — Company ID resolution

```python
import openpyxl

wb = openpyxl.load_workbook("workbook.xlsx")
ws = wb["Settings"]
for row in range(1, ws.max_row + 1):
    sid = ws.cell(row=row, column=2).value
    val = ws.cell(row=row, column=4).value
    if sid == "settings.companyId":
        print(f"companyId: {val!r}")
        assert val and len(str(val).strip()) > 0, "companyId is empty — add-in will not resolve company"
```

The add-in does: `drivepointUser.companies.find(it => it.id === settings?.companyId)`. If this returns `undefined`, the add-in restricts import, chat, plan browsing, and all company-scoped features.

**Finding the correct companyId**: Check the data pipeline configs in `streamToBigQuery` (COMPANY_ID field), BigQuery dataset names (`bbcust-<slug>`), or ask the user.

### Step 2.2 — WebExtension presence

```python
import zipfile

with zipfile.ZipFile("workbook.xlsx", "r") as zf:
    names = zf.namelist()
    assert "xl/webextensions/webextension1.xml" in names, "Missing WebExtension — add-in can't auto-discover"
    assert "xl/webextensions/taskpanes.xml" in names, "Missing taskpanes.xml"
```

If missing, inject using the service:

```python
from smartmodel_service.smartmodel_utils.convert_to_smartmodel import inject_webextension
inject_webextension("workbook.xlsx", "workbook_fixed.xlsx")
```

### Step 2.3 — Settings completeness

Verify all required settings are populated (not empty):

| Setting ID | Required | Notes |
|---|---|---|
| `settings.smartmodelSpec` | Yes | Must be `"6.0"` |
| `settings.modelVersion` | Yes | Semver (e.g., `"1.0.0"`) |
| `settings.modelName` | Yes | Human-readable name |
| `settings.modelType` | Yes | `"model"` for customer workbooks, `"template"` for templates |
| `settings.companyId` | Yes | Must match Drivepoint user account |
| `settings.companyName` | Yes | Display name |
| `settings.modelStartDate` | Recommended | Excel date, not string |
| `settings.historicalStartDate` | Recommended | Excel date, not string |
| `settings.currency` | Recommended | ISO 4217 (e.g., `"USD"`) |

---

## Phase 3 — Data Integrity

### Step 3.1 — Cell count audit

Every sheet should have data, not just headers:

```python
for ws in wb.worksheets:
    count = sum(1 for row in ws.iter_rows() for cell in row if cell.value is not None)
    print(f"  {ws.title}: {count} non-empty cells")
    if count < 10 and ws.title not in ("Index", "Settings"):
        print(f"    WARNING: sheet appears empty")
```

### Step 3.2 — Formula spot-checks

For schedule sheets, verify key formula patterns:
- Revenue rows: should reference units and price (or equivalent drivers)
- Total rows: should SUM their children
- Cross-sheet references: should point to existing sheets/cells
- No hardcoded values where formulas are expected

### Step 3.3 — Date spine integrity

On schedule sheets, verify row 2 contains a valid date spine:
- Dates should be contiguous (monthly or weekly)
- Should start from the historical start date or model start date
- No gaps or duplicates
- Monotonically increasing

---

## Phase 4 — Cutover Alignment

The cutover (where actuals end and forecast begins) is where most silent bugs hide.

### Step 4.1 — Run cutover audit

```python
from smartmodel_service.smartmodel_utils.cutover_audit import run_cutover_audit
from pathlib import Path

report = run_cutover_audit(Path("workbook.xlsx"))
if report.ok:
    print("Cutover alignment: clean")
else:
    for finding in report.findings:
        print(f"  [{finding.kind}] {finding.sheet}: {finding.message}")
```

This checks:
- `historicalStartDate` is at least 12 months before `modelStartDate`
- Row 2 date spine is monotonic
- Row 3 cutover labels reference a Settings cell
- Data rows switch formula patterns at the cutover boundary (actuals pull from R-GL, forecasts should not)

---

## Phase 5 — Visual QA (when Excel isn't available)

In sandbox environments where LibreOffice isn't available, render sheets as images for human review.

### Step 5.1 — Pillow-based rendering

Use openpyxl to read cell values and Pillow to render a grid:
- Color-code cells: blue for formulas, green for numbers, yellow for strings, red for errors
- Show the first 20 columns and 50 rows per sheet
- Include cell values (truncated to fit)
- Highlight empty cells in data regions

This is a fallback for visual inspection — it doesn't replace Excel but catches obviously empty or malformed sheets.

---

## Quick Reference: Fix Common Issues

| Issue | Fix |
|---|---|
| `companyId` empty | Set `settings.companyId` to the customer's Drivepoint slug |
| WebExtension missing | Run `inject_webextension(src, dst)` from the service |
| Gridlines ON | `ws.views.sheetView[0].showGridLines = False` on all sheets |
| Dates as strings | Replace with `datetime` objects, set `number_format = 'YYYY-MM-DD'` |
| Settings header font | Use `Font(name='Menlo', size=10, color='FFFFFF', bold=True)` |
| Dangling pane selections | Re-save through the service's `inject_webextension` which cleans these |
| #REF! errors | Check for deleted sheet references or misaligned cross-sheet formulas |
