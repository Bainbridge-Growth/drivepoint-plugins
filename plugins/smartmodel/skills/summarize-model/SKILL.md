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
| `settings.smartmodelSpec` | Protocol version — confirms this is a SmartModel |
| `settings.modelName` | Human-readable name |
| `settings.modelVersion` | Model version (semver) |
| `settings.modelType` | "model" (full workbook) or "template" (single-purpose) |
| `settings.companyName` | Company name |
| `settings.currency` | Currency for all numbers |
| `settings.modelStartDate` | Forecast start date |
| `settings.historicalStartDate` | How far back actuals go |

If `settings.smartmodelSpec` is not "6.0", note the protocol version and proceed cautiously — some structural assumptions in this skill are v6-specific.

The model context also includes the full template manifest from the index (template IDs, owned sheets, skill references, import references) and the date spine (time range, Actual/Forecast boundary).

---

## Phase 2 — Assess Sheet Inventory

Call `get_sheet_names` → get the full list of tabs. Categorize each:

| Category | How to identify | What to report |
|----------|----------------|---------------|
| Schedule sheets | Yellow tabs | List each with template name from D9 |
| Report sheets | Blue tabs | List each |
| R- sheets | "R-" prefix, default color | List each; note populated vs. empty |
| Consolidation | Black tab or "M - Monthly" | Note if present |
| Settings | Dark gray tab | Already read |
| Index | White tab, first position | Already read |

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

For schedule sheets where the Index indicates dimensions exist, call `read_smartmodel_registries` → extract `dim_` entries. Only read registries on sheets that the Index references as having dimensions — do not read every schedule sheet. Report what entities are being modeled (e.g., "DTC sheet models 3 channels: Shopify, Subscription, Retail").

---

## Phase 5 — Quick Health Check

Call `sheet_validate` → capture any structural validation errors.
Also call `sheet_error_find` → check for formula errors (#REF!, #DIV/0!, etc.) across all sheets.

Flag:
- Settings fields that are blank or use default values
- R- sheets that are empty (data not imported — limits analysis)
- Actual/Forecast boundary that is stale (>2 months behind today)
- Sheets referenced in the Index that don't exist
- Template version mismatches
- Any formula errors found

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
- If the workbook is not a SmartModel (no Settings tab or `settings.smartmodelSpec` missing), note this and offer to run `/convert-to-smartmodel` or provide a limited analysis based on available structure

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
