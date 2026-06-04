---
name: migrate-customer-model
description: Migrate a customer's existing financial model into a SmartModel workbook. Use when an FDE or agent needs to convert a non-Drivepoint Excel model (IFM, custom spreadsheet, legacy model) into a v6 SmartModel that works with the Drivepoint add-in and data import system. Triggers on "convert this model", "migrate to SmartModel", "build a model for [customer]", "create a SmartModel from this spreadsheet".
---

# Migrate Customer Model

**Purpose**: Convert a customer's existing financial model into a fully functional SmartModel v6 workbook — one that passes `post_validate`, works with the Drivepoint Excel add-in, and supports automated data import.

**Prerequisite**: The `smartmodel-protocol` skill must be loaded for all v6 grammar details.

**Key principle**: The `drivepoint-smartmodel-service` repo contains battle-tested Python utilities for all structural SmartModel operations. **Never reinvent Settings tabs, Index tabs, header blocks, tab colors, or WebExtension injection.** Use the service's code. Your job is the business content — the customer's data, formulas, and domain logic.

---

## What goes wrong without this skill

Without guidance, agents tend to:
- Create sheets that _look_ like Drivepoint (formatting, tab colors) but have no real structure — identifiers missing, formulas not linked, schedules disconnected
- Reinvent Settings and Index tabs from scratch, missing required fields or using wrong fonts/layouts
- Forget WebExtension injection, so the add-in can't auto-discover the workbook
- Leave `settings.companyId` empty, which blocks add-in functionality
- Split generation into multiple scripts (generate + populate) that duplicate data and drift apart
- Store dates as strings instead of Excel date values, breaking cutover logic

---

## Phase 1 — Analyze Source Material

Understand what you're converting before writing any code. Read the source model thoroughly.

### Step 1.1 — Inventory the source workbook

Open the customer's existing model and catalog:
- Every sheet name, its purpose, and approximate row/column extent
- The date structure: monthly columns? weekly rows? fiscal year boundaries?
- Key financial line items: revenue lines, COGS, opex categories, balance sheet items
- Data sources: which sheets contain imported/raw data vs. calculated/formula content?
- Cross-sheet references: which sheets feed into which?

### Step 1.2 — Identify the customer and company ID

Determine the customer's Drivepoint company ID (the slug used across infrastructure). Check:
- `drivepoint-customers/customers/<slug>/` directory existence
- Data pipeline configs (BigQuery datasets named `bbcust-<slug>`)
- Existing SmartModel workbooks for the customer

The company ID is a lowercase alphanumeric slug (e.g., `nanit`, `everydaydose`, `mudwtr`). If unsure, ask the user.

### Step 1.3 — Map to SmartModel templates

Determine which standard templates apply (from `drivepoint-smartmodel-templates`):
- `dtc-revenue`, `amzn-revenue`, `wholesale-revenue`, `tiktok-revenue`
- `product` (COGS), `opex`, `payroll`
- `consolidation` (M-Monthly), `balance-sheet`, `reports`

For sheets that don't map to standard templates: plan custom schedule sheets with appropriate template IDs. Every schedule sheet needs a `metadata___template_id`.

### Step 1.4 — Write the implementation spec

Before generating any code, write a spec document at `customers/<slug>/notes/implementation-spec.md` covering:
- Source sheet to SmartModel sheet mapping
- Settings tab values (companyId, companyName, dates, currency)
- Template registry (what goes in the Index tab)
- Formula translation plan (how source formulas become SmartModel formulas)
- R-sheet plan (which data imports are needed)
- Known gaps or decisions needed from the user

Get user confirmation on the spec before proceeding.

---

## Phase 2 — Build the Workbook

### Step 2.1 — Write ONE generation script

Write a single Python script at `customers/<slug>/models/build_<slug>_model.py` that:
1. Creates the workbook with openpyxl
2. Builds ALL sheets with structure AND data in a single pass (no separate populate step)
3. Writes all formulas, seed data, and reference data
4. Saves to a temporary path

**Do NOT** create the Settings tab, Index tab, or header blocks yourself. The service handles that in step 2.2.

**Do** create:
- Schedule sheets (yellow) with the customer's data, formulas, dimension/measure registries
- R-sheets with reference data and import-layer structure
- Report sheets with summary formulas

### Step 2.2 — Convert to SmartModel using the service

After generating the raw content workbook, use the smartmodel-service's `convert_to_smartmodel.py`:

```python
import sys
sys.path.insert(0, '<path-to>/drivepoint-smartmodel-service/src')
from smartmodel_service.smartmodel_utils.convert_to_smartmodel import convert

config = {
    "model_name": "Customer Name Financial Model",
    "company_name": "Customer Name",
    "company_id": "<slug>",  # REQUIRED — must match Drivepoint user account
    "currency": "USD",
    "model_start_date": "2026-06-01",
    "historical_start_date": "2025-01-01",
    "templates": [
        {
            "template_id": "custom-revenue",
            "name": "Revenue Forecast",
            "version": "1.0.0",
            "description": "Revenue forecast by channel",
            "grain": "monthly",
            "sheets": ["Revenue"],
            "date_row": 2,
            "date_start_col": 11
        }
    ],
    "r_sheets": ["R-source-data"],
    "report_sheets": ["Dashboard"],
    "skip_sheets": []
}

output_path = convert("raw_workbook.xlsx", config)
```

This adds: Settings tab (with companyId populated), Index tab, header blocks on schedule sheets, tab colors, WebExtension XML, conformance enforcement (gridlines off, freeze panes), and style normalization.

### Step 2.3 — If you can't use the converter

When the service repo isn't available or the source model has formulas that would break if the converter inserts rows, do the conversion manually but use the service's individual utilities:

```python
from smartmodel_service.smartmodel_utils.convert_to_smartmodel import (
    build_settings_tab,
    build_index_tab,
    apply_tab_colors,
    enforce_workbook_conformance,
    inject_webextension,
)
```

If even these aren't importable, follow this checklist exactly:
- Settings tab: column A empty, B=id (Menlo 10pt), C=setting, D=value, E=description. Header row dark fill + white Menlo bold. Tab color `404040`.
- `settings.companyId` **must be set** to the customer's Drivepoint slug
- `settings.modelStartDate` and `settings.historicalStartDate` must be Excel date values, not strings
- Index tab: white tab, template manifest starting at row 12
- Schedule sheets: yellow tab (`FFC000`), gridlines OFF, freeze at `D5` or `K5`
- R-sheets: default tab color, no freeze
- Report sheets: blue tab
- WebExtension injection: add `webextension1.xml` and `taskpanes.xml` to the xlsx zip under `xl/webextensions/`

---

## Phase 3 — Validate

### Step 3.1 — Run post_validate

```python
from smartmodel_service.smartmodel_utils.post_validate import post_validate
report = post_validate("output.xlsx")
```

The workbook must pass with 0 errors. Warnings are acceptable but review each one.

### Step 3.2 — Business-level checks

Beyond structural validation, verify:
- Every schedule sheet has data (not just headers)
- Formulas evaluate to reasonable values (spot-check key totals)
- Cross-sheet references resolve (no #REF! errors)
- Date spine is contiguous and covers the expected range
- Revenue = Units x Price (or equivalent) on schedule sheets
- Totals rows sum their children

### Step 3.3 — Add-in compatibility

Verify the workbook will work with the Drivepoint Excel add-in:
- `settings.companyId` matches a company in the Drivepoint system
- `settings.smartmodelSpec` is `"6.0"`
- WebExtension XML is present in the xlsx zip
- `settings.modelType` is `"model"` (not `"template"`)

---

## Phase 4 — Deliver

### Step 4.1 — Commit to drivepoint-customers

Place output files in `customers/<slug>/models/`:
- The workbook(s): `<slug>_<model_type>.xlsx`
- The generation script: `build_<slug>_model.py`
- The implementation spec: `customers/<slug>/notes/implementation-spec.md`

### Step 4.2 — Upload to SharePoint (if needed)

If the customer's SharePoint site is configured, upload the workbook to their Plans folder. The add-in reads workbooks from SharePoint.

---

## Common Pitfalls

| Pitfall | Consequence | Prevention |
|---------|------------|-----------|
| Empty `settings.companyId` | Add-in can't resolve company, all features gated | Always set it from the data pipeline config or ask the user |
| Dates stored as strings | Cutover audit fails, period-type formulas break | Use `datetime` objects in openpyxl, set number_format to `YYYY-MM-DD` |
| Missing WebExtension | Add-in doesn't auto-discover the workbook | Always run `inject_webextension()` after saving with openpyxl |
| Separate generate/populate scripts | Duplicated data drifts, harder to maintain | One script does everything |
| Reinventing Settings/Index tabs | Missing fields, wrong fonts, wrong layout | Use the service's `build_settings_tab()` and `build_index_tab()` |
| Creating unlinked schedules | Model looks right but formulas don't connect | Always verify cross-sheet references before delivery |
| Gridlines left ON | Fails post_validate, looks unprofessional | Call `enforce_workbook_conformance()` or set manually |
