---
name: build-report
description: Build a structured financial report tab from SmartModel data — board reports, monthly close reviews, investor updates, department summaries. Use when a user asks to "build a report", "create a summary", "make a board report", "generate a monthly review", "put together an investor update", or wants model data packaged into a structured, shareable document. Also triggers on "executive summary", "board deck", "monthly close report", or "investor update".
user-invocable: true
---

# Build Report

**Purpose**: Create a structured blue report tab in the workbook that packages SmartModel data into a presentation-ready format tailored to a specific audience — board, investors, CEO, or department.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks for any formatted report or summary document
- User wants to prepare for a board meeting, investor call, or internal review
- User asks to "package" or "pull together" financial data into a shareable format
- User references a specific report type (monthly close, board report, investor update)

---

## Phase 1 — Determine Report Type and Audience

Ask (or infer from context):
1. **What type of report?** — Monthly close, board report, investor update, or department report
2. **What period?** — Most recent closed month, quarter, or YTD
3. **Who is the audience?** — Determines level of detail, tone, and format

If not specified, default to **Monthly Close Report** for the most recently closed Actual period.

### Report types

| Type | Audience | Cadence | Key Contents |
|------|---------|---------|-------------|
| Monthly Close | Finance, CEO, COO | Monthly, after actuals | P&L summary, variances, channel breakdown, outlook |
| Board Report | Board of directors | Quarterly | Executive summary, quarterly P&L, strategic metrics, cash runway |
| Investor Update | Current/prospective investors | Monthly or quarterly | Headline metrics, highlights, financial summary |
| Department Report | Functional leaders | Weekly or monthly | Function-specific metrics only |

---

## Phase 2 — Orient to Data Sources

**Step 2.1 — Read model identity**
Call `read_smartmodel_settings` → capture `settings.companyName`, `settings.currency`, `settings.modelName`.

**Step 2.2 — Map available data**
Call `read_smartmodel_index` → identify the consolidation sheet, channel sheets, and any other templates needed for the report.

**Step 2.3 — Read time context**
Call `read_smartmodel_date_spine` on the consolidation sheet → confirm the most recently closed Actual period and which column(s) to pull.

---

## Phase 3 — Pull Data from Model

Call `read_smartmodel_data_section` on relevant sheets:

| Data Point | Sheet | What to look for |
|-----------|-------|-----------------|
| Revenue by channel | DTC, AMZN, Wholesale | Revenue identifiers |
| Total revenue | M - Monthly consolidation | Revenue rollup row |
| COGS | Product sheet or consolidation | COGS identifiers |
| Gross profit / margin % | Consolidation or derived | Gross profit row |
| Opex by category | Opex sheet | Section headers |
| EBITDA / net income | Consolidation | Bottom of P&L |
| Plan / forecast comparison | Same rows, Forecast columns | For the same period |

Always pull: **Actual for the period**, **Plan/Forecast for the same period**, and **Prior period Actual** for trend context.

---

## Phase 4 — Build the Report Tab

**Step 4.1 — Create the sheet**
Call `create_sheet` with a descriptive name (e.g., "Report - March 2025" or "Board Report Q1"). Apply blue tab color via `format_range`.

**Step 4.2 — Write report headers**
Call `write_range` to populate:
- Row 1: Company name + report title + period (bold, large)
- Row 2: "Prepared: [today's date]" + "Confidential" (gray italic)

**Step 4.3 — Write P&L summary table**
Call `write_range` to populate the core table with headers and labels. Call `insert_formula` to reference the source data cells from schedule sheets — do not hardcode values. Table structure:

```
| | Actual | Plan | Var ($) | Var (%) | Prior Month |
| Revenue | =formula | =formula | =formula | =formula | =formula |
| COGS | | | | | |
| Gross Profit | | | | | |
| Gross Margin % | | | | | |
| Opex | | | | | |
| EBITDA | | | | | |
```

**Step 4.4 — Write channel revenue breakdown**
Call `write_range` for a channel breakdown table. Call `insert_formula` to reference each channel sheet's revenue row.

**Step 4.5 — Key metrics table (if data available)**

```
| Metric | Actual | Plan | Trend |
| Total Orders | | | |
| AOV | | | |
| New Customers | | | |
| Gross Margin % | | | |
```

**Step 4.6 — Apply formatting**
Call `format_range` to apply:
- Currency format to $ rows
- Percentage format to margin/variance % rows
- Bold to header rows and total rows
- Light gray background to alternating data rows for readability

Call `resize_columns` to fit column widths to content.

**Step 4.7 — Add chart (optional)**
If the user wants a visual: call `create_chart` with type ColumnClustered (revenue by channel) or Line (trend over trailing 6 months). Position below the tables.

---

## Phase 5 — Write the Narrative

After building the tables, draft narrative sections:

### Writing rules

1. Lead with the headline — "March revenue was $1.2M, 8% above plan, driven by DTC outperformance"
2. Quantify everything — never say "revenue increased significantly" — say "revenue increased $95K (8%)"
3. Explain the "so what" — every number needs an implication
4. Be honest about misses — pair bad news with context and remediation
5. End sections with a forward look — what does this mean for next period?

### Tone by audience

| Audience | Tone | Detail level | Target length |
|----------|------|-------------|--------------|
| Board | Confident, strategic, concise | High-level with appendix | 2–3 pages |
| CEO/COO | Direct, action-oriented | Moderate detail | 1–2 pages |
| Investors | Optimistic but honest | Key metrics only | 1 page |
| Department | Tactical, specific | Deep on function | 1–2 pages |

Call `write_range` to add narrative text cells below or alongside the tables. Use merged cells for narrative paragraphs where needed.

---

## Phase 6 — Self-Audit

1. **Formulas**: Confirm all data cells contain formulas referencing source sheets, not hardcoded values
2. **Period accuracy**: Confirm all data is from the intended period (check against date spine)
3. **Actual vs. Forecast labeling**: Confirm there's no mixing of Actual and Forecast periods without explicit labeling
4. **Tab registration**: Optionally add the report tab to the Index manifest via `read_smartmodel_index` + `write_range`

---

## Guardrails

- Never write hardcoded values into report cells — always use formulas that reference source schedule sheets
- Never write to Actual columns on schedule sheets
- Confirm with user before creating new tabs

---

## Common Mistakes to Avoid

1. Don't dump raw tables without narrative — a report tells a story, a spreadsheet shows data
2. Don't hardcode values in the report tab — if source data changes, hardcoded report cells become stale
3. Don't mix Actual and Forecast periods without clear labeling
4. Don't make the report longer than it needs to be — board members read the first page first
5. Don't include metrics you can't explain — if a number looks wrong, flag it rather than including it

---

## Integration with Other Skills

- **`/summarize_model`**: Orient to the model before pulling data
- **`/variance_analysis`**: Feeds the variance commentary sections
- **`/margin_analysis`**: Feeds the margin analysis sections
- **`/interrogate_model`**: If user asks follow-up questions about the report
