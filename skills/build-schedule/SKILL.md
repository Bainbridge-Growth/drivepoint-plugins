---
name: build-schedule
description: Create or rebuild financial supporting schedules in a SmartModel workbook — revenue builds, COGS schedules, opex schedules, headcount plans, debt schedules, depreciation tables. Use when a user asks to "build a schedule", "create a revenue build", "make a COGS schedule", "build out the debt schedule", "build a headcount plan", or needs a detailed supporting schedule for any P&L area. Also triggers on "revenue build", "expense build", "payroll schedule", or "depreciation table".
---

# Build Schedule

**Purpose**: Construct a new v6.0-compliant SmartModel schedule sheet from scratch — the calculation-layer worksheets that feed into the P&L, balance sheet, or cash flow statement.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded — this skill references the protocol grammar for all spec details rather than restating them.

---

## Phase 1 — Discover Data and Confirm Structure

Start by checking what data is available. Do not ask the user to describe the structure upfront — infer it from the data.

### Step 1.1 — Greet and identify the schedule type

Ask: "What type of schedule are we building?" Accept free-form answers. Common types:
- **Revenue schedule** (by channel: DTC, Amazon, Wholesale, TikTok)
- **COGS / product cost schedule** (unit-level cost build)
- **Operating expense schedule** (marketing, payroll, G&A)
- **Headcount / payroll schedule** (employee-level compensation)
- **Debt schedule** (draw, repay, interest)
- **Depreciation / amortization schedule** (fixed assets)

### Step 1.2 — Check for connected data

Call `list_import_definitions` to see if any data imports are available for this workbook.

- **If imports exist**: Offer to pull sample data. Call `build_custom_data_imports` with the relevant `importId` to load sample rows. Analyze the returned columns, grain, dimensions, and measures to infer structure.
- **If no imports exist**: Ask: "Do you have a CSV or data file to upload, or would you like to describe the structure?" Accept either path.

Do not gate this step on protocol version — it works regardless of model version.

### Step 1.3 — Infer structure from data

From the data shape (or user description), infer:

- **What is being modeled** — business process or metric category
- **Structural pattern** (internal, not user-facing):
  - *Volume × Rate* — quantity × per-unit amount (e.g. orders × AOV = revenue)
  - *Headcount × Compensation* — roster × pay components with hire-date step functions
  - *Run Rate + Adjustments* — base amount with growth rates or one-time overlays
  - *Balance Roll-Forward* — beginning + additions − reductions = ending, chained across periods
  - *Funnel / Conversion* — top-of-funnel volume narrowing through rate-based stages
- **Dimensions** — entities being tracked (SKUs, channels, headcount roles)
- **Measures** — metrics per dimension (units, revenue, spend, headcount)
- **Key Drivers vs. Key Results** — which rows are user inputs vs. formula-driven
- **Sections** — logical groupings (e.g. "Orders & Revenue", "COGS")
- **Time grain and range** — read from `read_smartmodel_date_spine` on an existing sheet; default to monthly
- **Cross-references** — which other sheets this schedule feeds or is fed by

### Step 1.4 — Present confirmation summary

```
Schedule name:    [name]
Tab name:         [proposed tab name]
Structural pattern: [inferred pattern]
Dimensions:       [list, or "none" for single-entity schedules]
Key Drivers:      [list]
Key Results:      [list]
Sections:         [list with brief description]
Time range:       [start] → [end], Actual through [cutoff]
Cross-references: [sheets this links to/from, or "none"]
Data source:      [import used, CSV, or manual]
```

**Hard gate**: Do not proceed to Phase 2 until the user explicitly approves.

**Revision path**: If the user requests changes, update the fields, re-present the full summary, and repeat the gate. Do not carry forward any detail the user rejected in a prior iteration.

---

## Phase 2 — Construct

Build the sheet block by block. Each step references the protocol grammar for exact spec details — do not re-derive colors, fonts, or border styles here.

**Step 1 — Create the sheet**
Call `create_sheet` with the confirmed tab name. Apply yellow tab color via `format_range`. Position after any existing schedule sheets.

**Step 2 — Header Block (Rows 1–8)**
Call `write_range` to populate per the Header Block spec in the protocol:
- Row 1: Title bar (light blue `#64B1FF`, white text, `≡` in Col A, `=D9` formula in Col C)
- Row 2: Date spine (black background, white bold, "End of Period" in Col C, month-end dates starting at Col K). Use `convert_string_to_excel_date` if converting date strings.
- Row 3: Period type (gray `#808080`, white text, "Actual" or "Forecast" starting at Col K). Read the boundary from an existing sheet via `read_smartmodel_date_spine`.
- Row 4: Status bar
- Rows 5–6: Blank
- Row 7: Template title (`=D9` in Col C, thick blue bottom border from Col B to last data column)
- Row 8: Template description (gray italic in Col C)
- Cols D–J: Leave empty on all header rows

**Step 3 — Metadata Block (Rows 9–15)**
Write via `write_range` per the Metadata Block spec. `D9` must be a plain string value — never a formula. Include at minimum: `metadata___name`, `metadata___template_id`, `metadata___template_version`, `metadata___description`, `metadata___grain`. Leave Row 16 blank as a separator.

**Step 4 — Settings Block (Rows ~17–21)**
All `settings___` identifiers must use the plural prefix. Include `settings___identifier_structure` as the last settings row — its value documents the identifier pattern for all data rows (e.g. `pattern: "{dimension-slug}_{measure-code}"`). Leave a blank row after the settings block.

**Step 5 — Dimension Registry**
Section header row, subheader row, blank row, then one `dim_` row per confirmed dimension. Col B monospace throughout. If no meaningful dimensions, omit and note the omission in Phase 3.

**Step 6 — Measure Registry**
Section header row, subheader row, blank row, then one `measure_` row per confirmed measure. Col B monospace throughout.

**Step 7 — Data Sections**
For each section confirmed in Phase 1:
1. Section header row (bold 14pt, thick blue bottom border Col B → last column)
2. Subheader row (gray italic description in Col C)
3. Blank spacing row
4. Data rows via `write_range`, one per dimension × measure combination:
   - Col A: correct marker — `•`, `•⚡ Key Driver`, or `  ⚡ Key Result`
   - Col B: identifier formula matching `settings___identifier_structure` — monospace font
   - Col C: human-readable label
   - Cols D–J: leave empty
   - Cols K onward: input values (Key Drivers) or Excel formulas (Key Results) via `insert_formula`
5. Close additive sections with a blank separator row (thin border) and a Key Result total row using SUM formulas

**Step 8 — Wire imported data (if applicable)**
If data was imported in Phase 1, link the R- sheet data into the schedule's Key Driver rows via `insert_formula`. Reference the R- sheet by column position aligned to the date spine.

**Step 9 — Formatting pass**
- Call `format_range` to apply monospace font (Menlo, size 10, black) to every cell in Col B
- Call `format_range` to apply input cell styling (light gray background, blue-ish text) to all forecast-period cells in Key Driver rows
- Confirm tab color is yellow
- Call `resize_columns` to set Col A = 4, Col B = 40

**Step 10 — Open the new sheet**
Call `activate_sheet` with the new sheet's name to bring it into focus for the user.

---

## Phase 3 — Self-Audit

Walk through each check. Narrate the result of each check to the user. If a check fails, fix and re-verify before moving on.

1. **Header block** — Rows 1–8 match the protocol spec. `C1` and `C7` contain `=D9`. Date spine starts at Col K. Cols D–J are empty on all header rows.
2. **Metadata block** — `D9` is a plain string value (not a formula). `metadata___template_id` is unique — no other sheet declares the same ID.
3. **Settings block** — All `settings___` identifiers use the plural prefix. `settings___identifier_structure` is present and matches the actual identifier format used in data rows.
4. **Dimension registry** — Every dimension confirmed in Phase 1 is registered. No `dim_` entries missing.
5. **Measure registry** — Every measure confirmed in Phase 1 is registered. No `measure_` entries missing.
6. **Data row identifiers** — Every data row's Col B contains a formula (not a hardcoded string). No two rows share the same identifier. All identifiers conform to `settings___identifier_structure`.
7. **Data row markers** — Key Driver rows carry editable input values in forecast columns. Key Result rows contain Excel formulas — no hardcoded values.
8. **Formulas** — No Key Result cell contains a hardcoded number. All total rows use SUM formulas.
9. **Formatting** — Every Col B cell uses monospace font. All Key Driver forecast cells have input cell styling. Section header borders and tab color match protocol spec.
10. **Index registration** — Do not manually write to the Index manifest; the add-in maintains it automatically. Verify the sheet's `metadata___template_id` is set correctly so the add-in can register it on next sync.

After all checks pass, report: schedule name, sections built, Key Driver count, Key Result count, and any deviations from the Phase 1 plan made during construction.

---

## Guardrails

- Never write hardcoded values into Key Result cells — always use formulas
- Never overwrite existing schedule sheets — only create new ones (unless the user explicitly asks to replace)
- Confirm with the user before any step that creates or deletes sheets
- If data import fails or returns no rows, fall back to manual structure and notify the user

---

## Integration with Other Skills

- **`/summarize-model`**: Orient to the workbook before adding schedules
- **`/build-report`**: Schedules feed reports — build the schedule first
- **`/create-scenario`**: Scenarios may need new schedule assumptions
- **`/audit-model`**: Validate the new schedule after construction
