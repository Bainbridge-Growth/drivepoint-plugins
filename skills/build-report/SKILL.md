---
name: build-report
description: Build a structured financial report tab from SmartModel data — board reports, monthly close reviews, investor updates, department summaries. Use when a user asks to "build a report", "create a summary", "make a board report", "generate a monthly review", "put together an investor update", or wants model data packaged into a structured, shareable document. Also triggers on "executive summary", "board deck", "monthly close report", or "investor update".
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

Settings, index, and date spine are already loaded by the protocol's auto-orient. From the model context, note: `companyName`, `currency`, `modelName`, the consolidation sheet, channel sheets, most recently closed Actual period, and which columns to pull.

---

## Phase 3 — Pull Data from Model

**If a prior analysis skill ran this session** (e.g., `/variance_analysis`, `/margin_analysis`), reuse the data and findings already gathered. Do not re-read sheets that were already read — skip directly to the data points you still need.

**Step 3.1 — Read the relevant sheet(s) — one call per sheet**
Determine which sheet(s) to read based on the report scope from Phase 1:

- **Full P&L report** (Monthly Close, Board Report, Investor Update): Call `read_smartmodel_data_section` on the consolidation sheet (M - Monthly).
- **Channel-specific report** (e.g., DTC performance, Amazon review): Call `read_smartmodel_data_section` on that channel's schedule sheet directly.
- **Department report** (e.g., marketing spend, headcount): Call `read_smartmodel_data_section` on the relevant schedule sheet (Opex, Payroll, etc.).
- **Channel breakdown needed**: Only after reading the primary sheet, read additional channel sheets if the report requires a breakdown across channels.

Read the minimum number of sheets needed. One `read_smartmodel_data_section` call per sheet — never call `read_range` cell-by-cell to assemble data that a single data section read would return.

**Step 3.3 — Note the cell references**
As you read each sheet, record the **sheet name, row number, and column letters** for the Actual period, Plan/Forecast period, and Prior Month period. You will need these to construct formulas in Phase 4. Build a reference map before writing anything:

```
{ line_item: "Total Revenue", sheet: "M - Monthly", row: 42, actual_col: "K", plan_col: "K", prior_col: "J" }
```

Do not proceed to Phase 4 without this map.

---

## Phase 4 — Build the Report Tab

**Step 4.1 — Create the sheet**
Call `create_sheet` with a descriptive name (e.g., "Report - March 2025" or "Board Report Q1"). Apply blue tab color via `format_range`.

**Step 4.2 — Write report headers**
Call `write_range` to populate:
- Row 1: Company name + report title + period (bold, large)
- Row 2: "Prepared: [today's date]" + "Confidential" (gray italic)

**Step 4.3 — Write P&L summary table**
Using the reference map from Step 3.3, build the entire table in as few tool calls as possible:

1. Call `write_range` once to write all row labels and column headers:
   ```
   | | Actual | Plan | Var ($) | Var (%) | Prior Month |
   | Revenue | | | | | |
   | COGS | | | | | |
   | Gross Profit | | | | | |
   | Gross Margin % | | | | | |
   | Opex | | | | | |
   | EBITDA | | | | | |
   ```

2. Call `insert_formula` for each row's Actual and Plan cells, referencing the consolidation sheet using the reference map (e.g., `='M - Monthly'!K42` for Revenue Actual). Then add Var ($) as `=B4-C4`, Var (%) as `=IF(C4<>0,(B4-C4)/ABS(C4),"N/A")`, and Prior Month referencing the prior column.

   Batch formula writes by row — write all 5 formulas for a line item before moving to the next row.

**Step 4.4 — Write channel revenue breakdown (if needed)**
Only if the report type requires it. Call `write_range` once for the full channel table labels, then `insert_formula` for each channel's revenue reference.

**Step 4.5 — Apply formatting (one pass)**
Call `format_range` once per format type — not per cell:
- Currency format: select the entire data range for $ rows
- Percentage format: select all margin/variance % rows
- Bold: header row and total rows
- Call `resize_columns` to fit column widths

**Step 4.6 — Add chart (optional)**
If the user wants a visual: call `create_chart` with type ColumnClustered (revenue by channel) or Line (trend over trailing 6 months). Position below the tables.

**Step 4.7 — Open the new report tab**
Call `activate_sheet` with the new report tab's name to bring it into focus for the user.

---

## Phase 5 — Write the Narrative

After building the tables, draft narrative sections:

### Writing rules

Follow the **Output Formatting Standards** in the protocol, plus these report-specific rules:
- Be honest about misses — pair bad news with context and remediation
- End sections with a forward look — what does this mean for next period?

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
4. **Tab registration**: Do not manually update the Index manifest — the add-in maintains the manifest automatically. If a dedicated registration API/tool becomes available, use that instead

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
