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

### Check 1 — What breaks Drivepoint (FAIL)

These are the only structural FAILs. Anything else in this checklist is a warning.
- [ ] Settings header can be read: literals `id` and `Value` (capital V). A lowercase `value` is a FAIL
- [ ] Settings ids are unique. A duplicate is a FAIL
- [ ] Date settings are Excel dates or serials, not text. Text is a FAIL
- [ ] `settings.companyId` is this tenant or a company-group id. Another tenant is a FAIL. Blank, or the placeholder `flavorfusion`, is a WARNING (publish skipped; prep fills blank and `flavorfusion`)
- [ ] No row-3 `Actual` / `Forecast` without a row-2 date. That is a FAIL
- [ ] Formulas have cached values. A missing cache is a FAIL
- [ ] No dangling pane selections. A broken pane is a FAIL

`settings.smartmodelSpec = "6.0"` turns on v6 add-in behaviour. It is not required for the plan to connect. Missing spec, `modelType`, `modelVersion`, or `companyName` is a WARNING.

### Check 2 — Sheet structure (WARNING unless Check 1 already failed)

Find schedule tabs by the header labels `End of Period` and `Period Type`, not by yellow. Compare `get_sheet_names` to the Index manifest when an Index exists. Index is optional — sync does not read it, and upload prep does not add one.
- [ ] A missing Index is a WARNING, not a FAIL
- [ ] A missing Settings tab is a WARNING (publish skipped). Dark gray tab color is convention
- [ ] Every sheet named in an Index manifest exists. A missing sheet is a WARNING
- [ ] Tab color is convention. A schedule that is not yellow is not a defect
- [ ] Tabs that are not in the Index are not orphans to delete. Hidden channel tabs are unpicked v6 channels: zeroed in Settings (`qsPct*` and the per-channel rates), never deleted. TikTok has no v6 tab
- [ ] `Key Drivers + Results` is a synced tab. `Key Drivers and Results` (the word "and") is on the roll-forward ignore list and is a different name

### Check 3 — Date Spine Integrity

Find each schedule by `End of Period` / `Period Type`, then call `read_smartmodel_date_spine`:
- [ ] Row 2 dates are contiguous. A gap is a WARNING. There is no 12-month minimum
- [ ] Schedule sheets that share a plan usually share a date range. A mismatch is a WARNING
- [ ] Row 3 has "Actual" or "Forecast" under every date. A label with no date is a FAIL (Check 1)
- [ ] Row 3 may use `lastDateActuals` or `modelStartDate`. Both pass. Flag only a gap of more than one month between those two dates
- [ ] The Actual/Forecast boundary differs across sheets — WARNING, unless one of them is the no-date FAIL

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

Call `sheet_error_find` → scan all sheets for formula errors. `#REF!`, `#DIV/0!`, `#NAME?`, and `#VALUE!` are WARNINGS. They do not block connect or sync. Still list every one — a displayed number can be wrong.
- [ ] No #REF! errors (WARNING)
- [ ] No #DIV/0! errors in the visible data range (WARNING)
- [ ] No #NAME? errors (WARNING)
- [ ] No #VALUE! errors (WARNING)

Call `read_smartmodel_data_section` on schedule sheets and verify:
- [ ] Key Result rows (column A contains `Key Result`) contain formulas, not hardcoded values. A hardcoded result is a WARNING — sync still stores the cached value
- [ ] Key Driver rows (column A contains `Key Driver`) contain user-entered values or import formulas. Sync reads these column A/B markers
- [ ] Don't flag a Key Driver for a missing `•` dot in column A: the dot is no longer used

### Check 6 — Cross-Sheet Consistency

Call `read_smartmodel_data_section` on consolidation (M - Monthly):
- [ ] Total revenue on consolidation ≥ sum of material channel revenues (formula tie)
- [ ] Gross profit = Revenue − COGS (verify formula logic)
- [ ] EBITDA or net income line ties to components above it

### Check 7 — Metadata Integrity

Call `read_smartmodel_sheet_metadata` on each schedule sheet. All of these are WARNINGS. Sync reads column A/B markers, not the metadata block.
- [ ] A schedule sheet may have `metadata___template_id` in column B. Missing is fine on a customer file
- [ ] When an Index exists, template ids in it match the sheets. A mismatch is a WARNING
- [ ] Two sheets sharing one `metadata___template_id` is a WARNING, not a broken plan
- [ ] `settings___identifier_structure` is convention

Call `read_smartmodel_registries` on sheets with dimension/measure registries:
- [ ] Dimension registries are populated (not empty)
- [ ] Measure registries are populated

---

## Phase 3 — Categorize and Report

### Severity levels

| Level | Meaning | Examples |
|-------|---------|---------|
| FAIL | Drivepoint cannot publish or sync, or a consolidation total does not tie | Unreadable Settings header, duplicate ids, text dates, another tenant's companyId, Actual/Forecast with no date, no cached values, broken panes, consolidation that does not tie |
| WARNING | The plan still connects. Something is incomplete or ugly | Missing Settings or Index, missing protocol ids, gridlines, #REF! and other formula errors, calc mode, freeze position, short history, empty R- sheets, stale actuals, a schedule that is not yellow |
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
4. Don't call the model a Drivepoint failure because of `#REF!`, a missing Index, gridlines, calc mode, or the freeze cell. Those are warnings. Do report `#REF!` — it can still show a wrong number
5. Don't ignore stale actuals — a model where actuals are months old will produce misleading variance analysis

---

## Integration with Other Skills

- **`/summarize-model`**: Run first for a lighter orientation; audit for deeper integrity
- **`/clean-model`**: Fix the FAIL and WARNING issues found by this audit
- **`/optimize-model`**: After cleaning, optimize for performance
- **`/investor-readiness-analysis`**: Investor readiness requires a clean audit first
