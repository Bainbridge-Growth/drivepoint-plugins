---
name: build-schedule
description: Guides construction of a new v6.0-compliant SmartModel schedule sheet from scratch. Use when no pre-built template exists and the user wants to build a custom schedule.
user-invocable: true
---

# Build Schedule

**Purpose**: Construct a new v6.0-compliant SmartModel schedule sheet from scratch.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded — this skill references the protocol grammar for all spec details rather than restating them.

---

## Structural Patterns

Five patterns describe how financial math flows in a schedule. Match the user's request to one or more before designing the structure.

**Volume × Rate** — A quantity multiplied by a per-unit amount. Dimensions are the countable things (SKUs, channels, orders); Key Drivers are volume and rate; Key Results are the derived amounts (e.g. revenue = units × price).

**Headcount × Compensation** — A roster of roles multiplied by pay components, with step-function timing (hire dates, ramp periods). Key Drivers are headcount counts and comp rates per role; Key Results are total compensation by role and in aggregate.

**Run Rate + Adjustments** — A base per-period amount with growth rates, step changes, or one-time overlays layered on top. Key Drivers are the base value and adjustment parameters; Key Results are the adjusted run rate per period.

**Balance Roll-Forward** — Beginning balance + additions − reductions = ending balance, chained across periods so each period's ending becomes the next period's beginning. Key Drivers are inflow/outflow amounts; Key Results are the ending balances.

**Funnel / Conversion** — Top-of-funnel volume narrows through rate-based stages. Key Drivers are top-of-funnel inputs and conversion rates at each stage; Key Results are the output volume at each stage and the final converted quantity.

---

## Phase 1 — Infer and Confirm

Read available context (user request, open workbook, existing sheets) and infer:

- **What is being modeled** — business process or metric category
- **Structural pattern(s)** — match to one or more of the five patterns above
- **Dimensions** — the entities being tracked (e.g. SKUs, channels, headcount roles)
- **Measures** — the metrics tracked per dimension (e.g. units, revenue, spend)
- **Input vs. calculated** — which measures are Key Drivers (user inputs) vs. Key Results (formulas)
- **Sections** — logical groupings of data rows (e.g. "Orders & Revenue", "COGS")
- **Time grain and range** — monthly/weekly, how many periods, where Actual ends and Forecast begins
- **Cross-references** — which other sheets this schedule will reference or be referenced by

Present a concise confirmation summary:

```
Schedule name:    [name]
Pattern(s):       [matched patterns]
Dimensions:       [list]
Key Drivers:      [list]
Key Results:      [list]
Sections:         [list with brief description of each]
Time range:       [start] → [end], Actual through [cutoff]
Cross-references: [sheets this schedule links to/from, or "none"]
```

**Hard gate**: Do not proceed to Phase 2 until the user explicitly approves.

**Revision path**: If the user requests changes, update the relevant fields, re-present the full summary, and repeat the gate. Continue iterating until the user explicitly approves. Do not carry forward any detail the user has rejected in a prior iteration.

---

## Phase 2 — Construct

Build the sheet block by block. Each step references the protocol grammar for exact spec details (colors, fonts, border styles, identifier conventions) — do not re-derive them here.

**Step 1 — Create the sheet**
Add a new sheet with a yellow tab color. Position it after any existing schedule sheets in the workbook.

**Step 2 — Header Block (Rows 1–8)**
Per the Header Block spec in the protocol:
- Row 1: Title bar (light blue background, white text, `≡` in Col A, `=D9` formula in Col C)
- Row 2: Date spine (black background, white bold, "End of Period" in Col C, month-end dates starting at Col K)
- Row 3: Period type (gray background, white text, "Actual" or "Forecast" values starting at Col K)
- Row 4: Status bar
- Rows 5–6: Leave blank
- Row 7: Template title (`=D9` in Col C, thick blue bottom border from Col B to last data column)
- Row 8: Template description (gray italic in Col C)
- Cols D–J: Leave empty on all header rows

**Step 3 — Metadata Block (Rows 9–15)**
Per the Metadata Block spec in the protocol. `D9` must be a plain string value — never a formula. Include at minimum: `metadata___name`, `metadata___template_id`, `metadata___template_version`, `metadata___description`, `metadata___grain`.

Leave Row 16 blank as a separator before the next block.

**Step 4 — Settings Block (Rows ~17–21)**
Per the Settings Block spec in the protocol. All `settings___` identifiers must use the plural prefix. Include `settings___identifier_structure` as the last settings row — its value documents the identifier pattern used by all data rows in this sheet (e.g. `pattern: "{dimension-slug}_{measure-code}"`).

Leave a blank row after the settings block before the dimension registry.

**Step 5 — Dimension Registry**
Section header row, subheader row, blank row, then one `dim_` row per dimension confirmed in Phase 1. Col B monospace throughout. If the schedule has no meaningful dimensions (e.g. a single-entity run rate), omit this block and note the omission in the Phase 3 audit.

**Step 6 — Measure Registry**
Section header row, subheader row, blank row, then one `measure_` row per measure confirmed in Phase 1. Col B monospace throughout.

**Step 7 — Data Sections**
For each section confirmed in Phase 1:
1. Section header row (bold 14pt, thick blue bottom border Col B → last column)
2. Subheader row (gray italic description in Col C)
3. Blank spacing row
4. Data rows, one per dimension × measure combination:
   - Col A: correct marker — `•`, `•⚡ Key Driver`, or `  ⚡ Key Result`
   - Col B: identifier formula whose output matches `settings___identifier_structure` — monospace font
   - Col C: human-readable label
   - Cols D–J: leave empty
   - Cols K onward: input values (Key Drivers) or Excel formulas (Key Results) across all time periods
5. Close additive sections with a blank separator row (thin border) and a Key Result total row using SUM formulas

**Step 8 — Formatting pass**
- Apply monospace font (Menlo, size 10, black) to every cell in Col B across the entire sheet
- Apply input cell styling (light gray background, blue-ish text) to all forecast-period cells in Key Driver rows
- Confirm tab color is yellow
- Confirm section header borders match the protocol spec

**Step 9 — Register in Index tab**
Add a row to the Index tab manifest for this sheet: Template ID, version, sheet name, skill file reference, imports file reference (if applicable). Per the Index Tab spec in the protocol.

---

## Phase 3 — Self-Audit

Walk through each check in order. Narrate the result of each check to the user. If a check fails, fix the issue and re-verify before moving on.

1. **Header block** — Rows 1–8 match the protocol spec. `C1` and `C7` contain `=D9`. Date spine starts at Col K. Cols D–J are empty.
2. **Metadata block** — `D9` is a plain string value (not a formula). `metadata___template_id` is unique — no other sheet in the workbook declares the same ID.
3. **Settings block** — All `settings___` identifiers use the plural prefix. `settings___identifier_structure` is present and its declared pattern matches the actual identifier format used in data rows.
4. **Dimension registry** — Every dimension confirmed in Phase 1 is registered. No `dim_` entries are missing.
5. **Measure registry** — Every measure confirmed in Phase 1 is registered. No `measure_` entries are missing.
6. **Data row identifiers** — Every data row's Col B contains a formula (not a hardcoded string). No two rows share the same identifier. All identifiers conform to the `settings___identifier_structure` pattern.
7. **Data row markers** — Key Driver rows carry editable input values in forecast columns. Key Result rows contain Excel formulas — no hardcoded values anywhere.
8. **Formulas** — No Key Result cell contains a hardcoded number. All total rows use SUM formulas, not manually enumerated references.
9. **Formatting** — Every Col B cell uses monospace font. All Key Driver forecast cells have input cell styling. Section header borders and tab color match the protocol spec.
10. **Index registration** — This sheet's template ID appears in the Index tab manifest with correct version, sheet name, and file references.

After all checks pass, report a brief summary: schedule name, sections built, Key Driver count, Key Result count, and any deviations from the Phase 1 plan made during construction.
