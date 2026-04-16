---
name: audit-model
description: Perform structural integrity and data quality checks on a SmartModel workbook. Use when a user asks to "audit", "check", "validate", or "QA" their model, when something seems off ("numbers don't look right", "something is broken", "formulas are wrong"), or before sharing a model externally. Also triggers on "sanity check", "validate before I send", "does this model look right?", "can you double-check this?", or "pre-flight check".
---

# Audit Model

**Purpose**: Systematically check a SmartModel for structural errors, data quality issues, formula problems, and protocol compliance violations. Run before sharing a model, after a major import or roll-forward, or whenever numbers look suspicious.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User explicitly asks to audit, validate, or QA the model
- User reports that something seems wrong or numbers don't match
- Before running critical analysis (agent should self-trigger)
- After a model conversion, roll forward, or major data import
- Before sharing the model with investors or for due diligence

---

## Phase 1 — Orient

Settings, index, and date spine are already loaded by the protocol's auto-orient. Use the model context for identity, template list, and time range.
Call `get_sheet_names` → get all actual sheets and compare to Index manifest from the model context.

---

## Phase 2 — Run Audit Checklist

**If `/summarize-model` ran this session**, reuse settings, index, date spine, sheet inventory, and health check results already gathered. Do not re-read data that was already read.

Run checks in order. For each: record Pass, Warning, or Fail with location and detail.

### Check 1 — Protocol Compliance

Use settings data from Phase 1 (already read). Verify:
- [ ] `settings.smartmodelSpec` = "6.0"
- [ ] `settings.modelType` is "model" or "template" (not blank)
- [ ] `settings.modelVersion` is valid semver (e.g., "1.0.0")
- [ ] `settings.companyName` is not blank
- [ ] `settings.modelStartDate` is a valid date
- [ ] `settings.historicalStartDate` is a valid date and precedes `modelStartDate`

### Check 2 — Sheet Structure

Compare `get_sheet_names` output to `read_smartmodel_index` manifest:
- [ ] Index tab exists
- [ ] Settings tab exists with dark gray tab color
- [ ] Every sheet referenced in Index manifest actually exists
- [ ] Tab colors follow convention (yellow = schedule, blue = report, default = R-)
- [ ] No orphan sheets (tabs present but not referenced in any template)

### Check 3 — Date Spine Integrity

Call `read_smartmodel_date_spine` on each schedule sheet:
- [ ] Row 2 has contiguous monthly dates with no gaps
- [ ] All schedule sheets share the same date range
- [ ] Row 3 has "Actual" or "Forecast" in every column that has a date
- [ ] The Actual/Forecast boundary is consistent across all schedule sheets

Call `get_todays_date` to assess:
- [ ] Actuals are not more than 2 months stale

### Check 4 — Data Population

Call `read_smartmodel_sheet_metadata` on each R- sheet:
- [ ] Note which R- sheets are populated and which are empty
- [ ] For populated R- sheets, check they have data for the expected date range

Call `read_smartmodel_data_section` on a sample of schedule sheets:
- [ ] Actual columns contain non-zero values (not all blank or zero)
- [ ] Forecast columns are populated

### Check 5 — Formula Integrity

Call `sheet_error_find` → scan all sheets for formula errors. Check for:
- [ ] No #REF! errors anywhere
- [ ] No #DIV/0! errors in the visible data range
- [ ] No #NAME? errors
- [ ] No #VALUE! errors

Call `read_smartmodel_data_section` on schedule sheets and verify:
- [ ] Key Result rows (marked `  ⚡ Key Result` in column A) contain formulas, not hardcoded values
- [ ] Key Driver rows (marked `•⚡ Key Driver` in column A) contain user-entered values or import formulas

### Check 6 — Cross-Sheet Consistency

Call `read_smartmodel_data_section` on consolidation (M - Monthly):
- [ ] Total revenue on consolidation ≥ sum of material channel revenues (formula tie)
- [ ] Gross profit = Revenue − COGS (verify formula logic)
- [ ] EBITDA or net income line ties to components above it

### Check 7 — Metadata Integrity

Call `read_smartmodel_sheet_metadata` on each schedule sheet:
- [ ] Every schedule sheet has `metadata___template_id` in column B
- [ ] Template IDs match what's declared in the Index tab manifest
- [ ] No two sheets share the same `metadata___template_id`
- [ ] `settings___identifier_structure` is declared on each sheet

Call `read_smartmodel_registries` on sheets with dimension/measure registries:
- [ ] Dimension registries are populated (not empty)
- [ ] Measure registries are populated

---

## Phase 3 — Categorize and Report

### Severity levels

| Level | Meaning | Examples |
|-------|---------|---------|
| FAIL | Model is broken or producing wrong numbers | #REF! errors, missing sheets, broken consolidation tie, hardcoded Key Results |
| WARNING | Model works but something is off or incomplete | Empty R- sheets, stale actuals, missing optional metadata fields |
| INFO | Observation, not an error | Cosmetic inconsistencies, minor formatting deviations |

### Output format

```
# Model Audit Report — [Company Name]
**Model**: [name] v[version]
**Audited**: [today's date]

## Summary
[X] Fails | [Y] Warnings | [Z] Info | Overall: [PASS / NEEDS WORK / FAIL]

## Critical Issues (FAIL)
- [Check name] — [Sheet/location] — [Description] — [How to fix]

## Warnings
- [Check name] — [Sheet/location] — [Description]

## Observations (INFO)
- [Description]

## What's Working
- [List passing areas — give credit where the model is solid]

## Recommended Next Steps
1. [Most critical fix first]
2. [Second fix]
...
Reference `/clean-model` to fix structural and formatting issues.
Reference `/optimize-model` for performance improvements.
```

---

## Guardrails

- This skill reads and assesses only — it never writes to or modifies the workbook
- Do not stop auditing after finding the first error — complete the full checklist
- Trace errors to root cause: "Revenue is $0 because R - GL is empty" is more useful than "Revenue row has no data"

---

## Common Mistakes to Avoid

1. Don't just check the first sheet — errors hide in mid-workbook templates
2. Don't skip the consolidation tie-out — it's the most common source of material errors
3. Don't report cosmetic issues as Fails — prioritize data accuracy issues
4. Don't declare the model clean until the formula error check passes — a single #REF! can corrupt downstream calculations silently
5. Don't ignore stale actuals — a model where actuals are months old will produce misleading variance analysis

---

## Integration with Other Skills

- **`/summarize-model`**: Run first for a lighter orientation; audit for deeper integrity
- **`/clean-model`**: Fix the FAIL and WARNING issues found by this audit
- **`/optimize-model`**: After cleaning, optimize for performance
- **`/investor-readiness-analysis`**: Investor readiness requires a clean audit first
