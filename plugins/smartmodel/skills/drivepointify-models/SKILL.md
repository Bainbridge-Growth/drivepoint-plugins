---
name: drivepointify-models
description: Turn a customer's own Excel budget / forecast / department template into a Drivepoint SmartModel ("drivepointify" it) — one continuous date spine with actuals and forecast in the same rows, the customer's logic rebuilt as real Key Drivers and Key Results, a summary tab in place of Total / LY / variance columns, and every number tied back to the source. Use when a user says "drivepointify", "make this Drivepoint compatible", "convert this budget template", "turn this spreadsheet into a SmartModel", "add key drivers and results to this file", "make this work with the add-in", or uploads a non-SmartModel planning workbook. Ships a source profiler and a hand-off validator that must pass before delivery.
---

# Drivepointify Models

**Purpose**: Convert a planning workbook the customer built themselves (a department budget, a channel
P&L, an inventory plan) into a SmartModel tab that the Drivepoint add-in, plan sync and scenario tools
can use — **without** losing the customer's logic and **without** the reviewer having to point out
structural problems.

**Prerequisite**: load `smartmodel-protocol` (grammar, chrome, marker strings, colours).
For a whole-company model migration (many templates, imports, R-GL wiring), this skill covers the
per-tab conversion; the wider programme is a model migration.

**Scripts** (in `scripts/`, Python 3 + openpyxl):

| Script | When | What it does |
|---|---|---|
| `profile_source.py <src.xlsx> [--sheet S]` | **Before** writing the spec | Finds stacked LY / actuals blocks, pasted "% × base" values, "LY × factor" growth builds, rows that are copies of other rows, `=row + constant` adjustments, shifted date blocks, bridges that skip rows, opening balances that don't roll, labels in the wrong column, duplicate names, copied `Plan Settings` tabs. |
| `validate_drivepointified.py <built.xlsx> [--ties ties.json]` | **After** build + recalc, before hand-off | The gate. Fails on: broken / partial date spine, history not in the spine, stacked blocks under the budget, columns right of the spine, anything but markers in A:B, Key Drivers that are formulas, Key Results that are typed, $ drivers that are a pasted % of another row, errors, uncached formulas, protocol chrome. `--ties` compares every mapped row to the source. |

---

## What "drivepointified" means — the non-negotiables

A drivepointified tab passes all of these. Do not hand off one that doesn't, and do not wait for the
user to ask.

1. **One date spine, in the series.** Row 2 from **K2**: contiguous month-end dates covering history
   **and** the plan (e.g. K = Jan of last year … AH = Dec of the budget year). Actuals and the
   customer's current-year forecast sit in the **same rows** as the budget, to the left of it, fed from a
   seed R-tab (`R - <Customer> <Tab> Seed`) until the add-in import takes over. **Never** leave a "2026
   Forecast (LY)" / "Actuals" block stacked under the budget — that is the #1 thing reviewers reject.
   - If the user asks for "the budget to start in column K" **and** the source carries history, say in
     the spec — before building — that K is the spine start and the budget therefore starts later
     (e.g. W), because history must be in the series. Build a budget-only spine at K only if the user
     confirms they want history off the time series.
   - Every schedule tab in the workbook uses the **same** spine (same K2 start, same months).
2. **Row 3** is `Actual` for months ≤ `settings.lastDateActuals`, then `Forecast`, formula-driven.
   Nothing in rows 2–3 right of the last spine date (plan sync rejects a row-3 value without a date).
3. **No Total / LY / variance / 1H-2H columns on the schedule.** Those become a **Budget Summary**
   report tab (blue) that SUMIFS the spine by period: FY history vs FY budget, variance $ / %,
   quarters, halves. Flows are summed; balances take the period-end value; openings take the first month.
4. **Rebuild the logic — do not move cells.** Interrogate every hard-keyed budget number:

   | Source pattern (profiler finding) | Build it as |
   |---|---|
   | `$ = base × constant %` pasted as values | **% Key Driver** (default = the implied %) × base → **Key Result** |
   | `$ = base × a different round % each month` | monthly **% Key Driver** × base → Key Result |
   | `$ = row × another row's monthly %` | that % row is the **Key Driver**; the $ row is a Key Result |
   | `$ = same month LY × factor` (or a pasted growth-block value) | **growth-factor Key Driver** × LY → Key Result |
   | row identical to another row | link it (optionally × a share driver, default 100%) |
   | `= LY row + constant in one month` | LY link + **adjustment Key Driver** ($) → Key Result |
   | opening balance hard-keyed, rest `=prior ending` | Beginning = prior Ending (`{p}`) + an explicit **opening adjustment** row for any gap vs the history's ending; report the gap |
   | flat or irregular $ typed by the planner | **$ Key Driver** |
   | totals, net, margins, %s of totals, KPIs | **Key Results** (formulas) |

   Every rebuilt 2027 value must still equal the customer's number — the rebuild changes *how* it is
   derived, not *what* it is.
5. **Key Driver vs Key Result by meaning.** A Key Driver is an assumption a planner changes (growth
   factor, %, price, a typed $ line). A Key Result is a line computed from drivers. "It's a constant" or
   "it's a formula" is not the test. A driver row may show its implied history (`result ÷ base`) in the
   actual months; its budget months are inputs.
6. **Columns A:B are markers and ids only.** A = `•⚡ Key Driver` / `  ⚡ Key Result` (or empty),
   B = the row id, C = the friendly name. Move labels the customer typed in B into C. Friendly names of
   marked rows are unique (rename "Total" → "Total Selling Expenses", second "Ending Inventory" →
   "FG Ending Inventory"). Calc/memo rows get no marker and no id.
7. **Ties are proof, not rounding.** Every mapped row ties to the source in **every month of every
   year** (budget and history), and the summary ties to the customer's own totals. A difference is a
   finding — either your bug or theirs.
8. **Source bugs are reported, not silently inherited.** If the rebuilt summary disagrees with a bridge
   in the source (e.g. a 1H/2H block that skips a line), keep the correct number and tell the user
   exactly what their bridge left out. Same for basis mismatches and shifted date blocks.
9. **Protocol chrome**: Settings header literally `id | Setting | Value | Description`;
   `settings.companyId` = the Drivepoint tenant id; real Excel dates; Index manifest; metadata block
   B9:B16; recalculated (cached values present); add-in WebExtension part; **do not copy the source's
   hidden `Plan Settings` tab** (it pins the other file's SharePoint id).

---

## Workflow

### Phase 0 — Profile the source (always)

```bash
python3 scripts/profile_source.py <source.xlsx> --sheet <TAB> --out profile.md
```

Read the whole tab too. The profiler is a net, not an oracle: confirm every finding against the
formulas, and look for what it can't see (logic in other files, e.g. COGS that comes from the channel
budgets).

### Phase 1 — Spec (short, concrete)

Write a mapping table — one line per source row:

| Source row | Label | → Model row | Kind (KD / KR / calc) | Budget formula / driver | History source |
|---|---|---|---|---|---|

Plus:
- **Spine**: first/last month, where the budget starts, which months are Actual / seeded forecast / budget.
- **Findings & decisions**: every profiler line, each resolved (built as X / reported to owner / not applicable).
- **Summary tab**: which source totals it replaces and which it ties to.

If the user already asked you to build, present the spec in one message and proceed; pause only for
genuine ambiguity (e.g. two inventory bases, the history-vs-column-K conflict above).

### Phase 2 — Build (one script)

One build script reads the source's **cached values** (never re-type numbers) and writes the
workbook in a single pass: Index, Settings, the schedule tab(s), Budget Summary, seed R-tab.
Useful formula-template tokens for a row engine: `{c}` current column, `{ly}` same month last year
(12 columns back), `{p}` previous column (roll-forwards), `{m11}` 11 back (trailing-12 windows),
`{@row_key}` row lookup. Section order follows the customer's tab.

### Phase 3 — Recalc + chrome

Recalculate so every formula has a cached value (Excel `Ctrl+Alt+F9` + save, or a formula engine),
then inject the add-in WebExtension (openpyxl and LibreOffice strip it).

### Phase 4 — Validate (the gate)

```bash
python3 scripts/validate_drivepointified.py <built.xlsx> --ties ties.json
```

- `ties.json` covers **every** mapped row: budget columns vs the source budget range, history columns
  vs the source LY range, plus summary cells vs the source totals.
- **0 FAIL required.** Explain every WARN in the hand-off (e.g. "growth factors have no history — expected").
- Also re-open the file and eyeball the first screen of each tab: labels in C, dates in row 2, blue
  input cells only on Key Driver budget months.

### Phase 5 — Hand-off message

Lead with what changed and why it's safe:
1. Layout (spine range, where the budget starts, the seed tab, the summary tab).
2. Key Drivers / Key Results per tab — name the drivers.
3. What was a pasted value and is now a driver.
4. Validation: "N monthly values and M totals tie to your file; validator 0 fail."
5. Findings in their file (bridge gaps, basis mismatches, shifted blocks) — with the numbers.
6. How to load it: upload as a plan in the Drivepoint app (Plans → Upload Plan); the add-in shows it
   as a SmartModel only after that registration.

---

## Before you hand off — answer these yourself

The user should never have to ask these. If any answer is "no", fix it first.

- Is there **one** date spine, starting K2, identical on every schedule tab, with history in it?
- Is **anything** below the budget that is really another year's copy of the same lines?
- Are there **Total / FC / variance** columns next to the months? (→ Budget Summary)
- Is every Key Driver something a planner would actually change? Is any "Key Result" really an assumption
  (e.g. an adjustment or share)? Is any typed $ driver actually a % of something?
- Do growth factors / % drivers carry the customer's exact values, so the budget is unchanged?
- Does every opening balance roll from the prior month? If not, is the gap an explicit, labelled row?
- Are any sub-blocks dated differently from the header (e.g. Dec … Nov)? Mapped by date, not column?
- Are friendly names unique and in column C? Are A:B clean on every non-marked row?
- Does every number tie, both years, and do the summary totals match the customer's totals?
- What is wrong **in the source**, and have I said so?

## Failure modes seen in real conversions

| What went wrong | Why it's wrong | Guard |
|---|---|---|
| Cells shifted so the budget lands in K:V, LY block left underneath | Not a time series; plan sync / scenarios see no history; reviewer rejects | Non-negotiable 1; validator `HISTORY` |
| Key Driver = "hard-keyed", Key Result = "formula" | Pasted % rows become $ "drivers", LY-plus-adjustment rows become "results" | Non-negotiables 4–5; validator `MEANING` |
| Totals / 2026 FC / variance columns kept beside the months | Row 2/3 must stop at the spine; values there break sync | Summary tab; validator `HISTORY` |
| Growth factors left as a side block with revenue pasted | Changing the factor doesn't move the P&L | Rebuild revenue as LY × factor |
| Hidden `Plan Settings` copied from the source | Points at the customer's original SharePoint item | Drop it; validator `PROTOCOL` |
| Settings header `value` (lower-case) | Add-in reads every setting as blank → "not a SmartModel" | Header literals; validator `PROTOCOL` |
| Uncalculated workbook | Add-in reads NaN; Plan Save fails | Recalc; validator `CALC` |
| Source bridge silently inherited | Customer's 1H/2H total was short a line | Non-negotiable 8; profiler "bridges" |
