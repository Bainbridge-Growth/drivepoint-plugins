---
name: summarize-model
description: Generate a structured summary of a SmartModel workbook — what's in it, what state it's in, what time range it covers, what data is populated. Use when a user opens a model and asks "what is this?", "summarize this model", "what's in here?", "give me an overview", "stand up the model", or when the agent needs to orient itself to a new workbook before any other task. This is the foundational orientation skill — run it first on any unfamiliar model.
---

# Summarize Model

**Purpose**: Generate a complete, structured overview of a SmartModel workbook — what templates are present, what data is populated, what time range it covers, and what state it's in. This is the **first skill to run** when encountering a new model.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User opens or uploads a SmartModel and asks for an overview
- User says "what's in this model?" or "summarize this"
- Agent needs to orient itself before performing another skill
- User asks about model completeness, data availability, or configuration
- Any other skill's Phase 1 (Orient) step triggers this as a prerequisite

---

## Phase 1 — Use Model Context

Settings, index, and date spine are already loaded by the protocol's auto-orient. Extract from the model context:

| Field | What it tells you |
|-------|------------------|
| `settings.smartmodelSpec` | `6.0` turns on v6 add-in behaviour. Missing does not mean the file is not a plan |
| `settings.modelName` | Human-readable name |
| `settings.modelVersion` | Model version (semver) |
| `settings.modelType` | "model" (full workbook) or "template" (single-purpose) |
| `settings.companyName` | Company name |
| `settings.currency` | Currency for all numbers |
| `settings.modelStartDate` | Forecast start date |
| `settings.historicalStartDate` | How far back actuals go |

If `settings.smartmodelSpec` is not "6.0", say that v6 template skills and imports are off and keep going. The plan still connects. Do not treat a missing spec as "not a SmartModel".

The model context also includes the full template manifest from the index (template IDs, owned sheets, skill references, import references) and the date spine (time range, Actual/Forecast boundary).

---

## Phase 2 — Assess Sheet Inventory

Call `get_sheet_names` → get the full list of tabs. Categorize each:

| Category | How to identify | What to report |
|----------|----------------|---------------|
| Schedule sheets | Header labels `End of Period` and `Period Type`. Yellow is only a hint | List each. Read column A/B markers. Do not skip a tab because it is not yellow |
| Report sheets | Blue tabs, or a tab with no date spine that only references schedules | List each |
| R- sheets | Name contains `R - ` | List each; note populated vs. empty. These are not timeseries |
| Consolidation | `M - Monthly`, when present | Note if present. Not required |
| Settings | Tab named `Settings` | Already read. A customer copy may sit at `Settings (original)` |
| Key Drivers + Results | That exact name | Prep adds it. It is synced. It is not the ignored tab `Key Drivers and Results` |
| Index | Tab named `Index`, when present | Optional. Missing is not a defect |

**Data population check**: For each R- sheet, call `read_smartmodel_sheet_metadata` to check if it has data beyond headers. Report as "Populated" or "Empty" — this tells the user which data imports have run and which analyses are possible.

---

## Phase 3 — Assess Time Horizon

Time range and Actual/Forecast boundary are already in the model context from auto-orient. Note:
- First date in Row 2 = model start
- Last date in Row 2 = model end
- Last "Actual" column in Row 3 = actuals-through date

Call `get_todays_date` to assess how current the actuals are. Flag if actuals are more than 2 months stale.

---

## Phase 4 — Read Key Dimensions

When an Index lists sheets with dimensions, call `read_smartmodel_registries` on those sheets only. When there is no Index, call it on schedule tabs whose metadata or first rows show a `dim_` registry — do not assume every schedule has one. Report what entities are being modeled (e.g., "DTC sheet models 3 channels: Shopify, Subscription, Retail"). TikTok has no v6 tab; do not invent one.

---

## Phase 5 — Quick Health Check

Call `sheet_validate` → capture any structural validation errors.
Also call `sheet_error_find` → check for formula errors (#REF!, #DIV/0!, etc.) across all sheets.

Separate Drivepoint errors from warnings. Errors: unreadable Settings header, duplicate ids, text dates, another tenant's `companyId`, `Actual`/`Forecast` with no date, formulas with no cached values, broken panes. Warnings, including these:
- Blank Settings fields, or `companyId` / `companyName` / `stores` still `flavorfusion` (prep fills those three from the tenant)
- Missing Settings, missing Index, missing `smartmodelSpec`
- R- sheets that are empty (data not imported — limits analysis)
- Actual/Forecast boundary that is stale (>2 months behind today)
- History shorter than 12 months (allowed)
- Sheets referenced in an Index that don't exist
- `#REF!` and other formula errors
- Hidden channel tabs: unpicked v6 channels, zeroed in Settings, not deleted. TikTok has no v6 tab

---

## Phase 6 — Headline Numbers (if consolidation is populated)

Call `read_smartmodel_data_section` on the consolidation sheet → extract the most recent Actual month's headline metrics:
- Total Revenue
- Gross Margin %
- Total Opex
- EBITDA or Net Income (if row exists)

This gives the user an instant "state of the business" snapshot.

---

## Output

Present in this format:

```
## [Company Name] — Model Summary

**Model**: [model name] (v[version])
**Protocol**: SmartModel v[spec]
**Type**: [model / template]
**Currency**: [currency]

**Time Range**: [start date] → [end date]
**Actuals Through**: [last actual month]
**Forecast From**: [first forecast month]
**Actuals Currency**: [current / stale — N months behind]

---

**Templates**: [count]
  [template id] → [sheets] (v[version])
  ...

**Data Sources**: [populated count] / [total] R- sheets populated
  ✓ R - [name]: Populated
  ✗ R - [name]: Empty
  ...

**Dimensions**:
  [Sheet]: [list of dim_ entries]
  ...

---

**Headline (most recent actuals — [month year])**:
  Revenue: [value]
  Gross Margin: [value] ([%])
  Opex: [value]
  EBITDA: [value]

---

**Health**:
  [List of any issues, or "No issues detected"]
  [Formula errors: list locations, or "None"]
```

---

## Guardrails

- This skill reads only — it never writes to the workbook
- Any `.xlsx` connects. If Settings or `settings.smartmodelSpec` is missing, summarize what is there. Offer `/make-drivepoint-ready` when the user wants the minimum structure, and `/drivepointify-models` only when they want the logic rebuilt. Do not offer a convert step just because the spec is blank

---

## Common Mistakes to Avoid

1. Don't skip the Settings tab — it's the fastest orientation and confirms protocol compliance
2. Don't list every row in every sheet — summarize at the template/section level
3. Don't ignore empty R- sheets — these determine what analyses are possible
4. Don't skip the health check — structural errors caught here prevent wrong numbers in downstream analyses

---

## Integration with Other Skills

- This skill is a **prerequisite** for almost every other skill — run it first
- **`/audit-model`**: Deeper structural integrity check
- **`/variance-analysis`**, **`/margin-analysis`**: Need the orientation from this summary to know which sheets to read
- **`/interrogate-model`**: Answers specific follow-up questions using the map built here
