---
name: investor-readiness-analysis
description: Assess a SmartModel for fundraising and due diligence readiness — checking time coverage, assumption documentation, KPI completeness, and model consistency. Use when a user is preparing to fundraise, is in due diligence, asks "is this model investor-ready?", "what do investors want to see?", "prepare for due diligence", or "review for fundraise". Also triggers on "investor model", "due diligence", "Series A model", or "data room".
---

# Investor Readiness Analysis

**Purpose**: Audit a SmartModel for the gaps that investors and acquirers flag most often — time coverage, assumption transparency, KPI completeness, and internal consistency. Produces a prioritized checklist of what to fix before sending the model.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User is preparing for a fundraise (Seed, Series A, Series B, growth equity)
- User is in due diligence and needs to share their model
- User asks "is this model investor-ready?"
- User is building a data room and wants to validate the financial model
- User asks what investors or acquirers typically want to see

---

## Phase 1 — Orient

**Step 1.1 — Read model identity and time coverage**
Call `read_smartmodel_settings` → capture `settings.modelName`, `settings.modelStartDate`, `settings.historicalStartDate`, `settings.companyName`.

**Step 1.2 — Read workbook map**
Call `read_smartmodel_index` → get all templates, sheet names, and what data sources are configured.

**Step 1.3 — Read time context**
Call `read_smartmodel_date_spine` on the consolidation sheet → determine:
- How far back actuals go (months of historical data)
- How far forward the forecast runs (months of forward projection)
- Where the Actual/Forecast boundary sits

**Step 1.4 — Check structural integrity**
Call `sheet_validate` → flag any structural errors before the investor readiness analysis.

---

## Phase 2 — Gather and Assess

### 2.1 — Time coverage check

Read date spine data and assess:

| Requirement | Minimum | Preferred |
|-------------|---------|-----------|
| Historical actuals | 12 months | 24+ months |
| Forward forecast | 18 months | 36 months |
| YTD actuals current | Within 1 month of today | Current month |

Call `get_todays_date` to verify how stale the actuals are.

### 2.2 — P&L completeness check

Call `read_smartmodel_data_section` on the consolidation sheet (M - Monthly). Verify the following line items are present and populated:

| Line Item | Required | Notes |
|-----------|---------|-------|
| Revenue (by channel) | Yes | Channel breakdown required for most investors |
| COGS | Yes | At minimum total; by product preferred |
| Gross profit / margin % | Yes | Both $ and % |
| Operating expenses | Yes | At minimum by major category |
| EBITDA | Yes | Or net income |
| Headcount | Preferred | Investors want to see team scaling |
| CAC (if DTC) | Preferred | Critical for consumer brand investors |
| LTV or retention | Preferred | Strong signal for subscription businesses |

### 2.3 — Assumption transparency check

Call `read_smartmodel_data_section` on each schedule sheet → count Key Driver rows vs. Key Result rows.

Flag if:
- Key Driver rows have no values populated (blank assumptions)
- Growth rate assumptions seem unrealistic (>100% YoY without explanation)
- Assumptions are hardcoded without identifiers (no column B id = can't be traced)

### 2.4 — Revenue quality check

Call `read_smartmodel_data_section` on channel sheets. Assess:
- Is revenue broken out by channel? Investors want this.
- Is there a distinction between Actual and Forecast? (Row 3 check)
- Are there cohort or retention assumptions for subscription revenue?
- Is there a path from unit economics (price × volume) to total revenue, or is revenue assumed at the top level?

Bottom-up revenue builds are far more credible to investors than top-down.

### 2.5 — Cash and runway check

Look for a cash flow or cash runway section. If absent, flag as a gap — investors will always ask about runway.

### 2.6 — Cross-sheet consistency check

Call `read_smartmodel_data_section` on the consolidation sheet and compare totals to channel-level sheets. Flag if:
- Consolidation revenue ≠ sum of channel revenues
- COGS in consolidation ≠ COGS in product sheet
- Any #REF! or #VALUE! errors in consolidation rows

---

## Phase 3 — Output

### Investor readiness scorecard

Present findings as a prioritized checklist:

```
# Investor Readiness Report — [Company Name]
Model: [model name] | Reviewed: [today's date]

## Summary
Overall Readiness: [Ready / Needs Work / Not Ready]
Critical gaps: [count] | Recommended improvements: [count] | Nice-to-haves: [count]

## CRITICAL (Fix before sharing)
- [ ] [Issue] — [Why investors flag this] — [How to fix]

## RECOMMENDED (Fix if time allows)
- [ ] [Issue] — [Why it matters] — [How to fix]

## NICE-TO-HAVE (Enhances credibility)
- [ ] [Issue] — [Why it helps]

## What's Working Well
- [List strengths to preserve]
```

### Standard gap table

| Category | Status | Gap | Priority |
|----------|--------|-----|---------|
| Time coverage (historical) | | | |
| Time coverage (forecast) | | | |
| Actuals currency | | | |
| Revenue by channel | | | |
| Bottom-up revenue build | | | |
| COGS detail | | | |
| Gross margin % | | | |
| Opex by category | | | |
| Headcount plan | | | |
| EBITDA / net income | | | |
| Cash / runway | | | |
| CAC (if applicable) | | | |
| LTV / retention (if applicable) | | | |
| Assumption documentation | | | |
| Cross-sheet consistency | | | |

---

## Guardrails

- Never write to Actual columns or overwrite Key Drivers
- This skill assesses the model — it does not fix issues. Reference `/audit_model` and `/clean_model` for repairs.
- Do not fabricate assessments for data that isn't in the model — if a section is missing, flag it as missing

---

## Common Mistakes to Avoid

1. Don't declare a model "investor-ready" based on formatting alone — structure and data quality matter more than cosmetics
2. Don't ignore stale actuals — a model where actuals are 3+ months old will immediately raise questions in due diligence
3. Don't miss the cash / runway gap — this is the first thing any investor asks and the most common omission
4. Don't overlook assumption reasonableness — a technically complete model with implausible assumptions is worse than a simpler honest one
5. Don't conflate "model exists" with "model tells a story" — investors want to understand the business through the model, not just see numbers

---

## Integration with Other Skills

- **`/audit_model`**: Fix structural issues identified here
- **`/variance_analysis`**: Populate the actuals vs. plan commentary investors expect
- **`/cohort_analysis`**: Build the retention and LTV section if missing
- **`/build_report`**: Create the investor update or board deck from the model
