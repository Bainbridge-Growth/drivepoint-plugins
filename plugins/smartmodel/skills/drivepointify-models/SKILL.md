---
name: drivepointify-models
description: Turn a customer's own Excel budget / forecast / department template into a Drivepoint SmartModel ("drivepointify" it) — one continuous date spine with actuals and forecast in the same rows, the customer's logic rebuilt as real Key Drivers and Key Results, a summary tab in place of Total / LY / variance columns, and every number tied back to the source. Use when a user says "drivepointify", "make this Drivepoint compatible", "convert this budget template", "turn this spreadsheet into a SmartModel", "add key drivers and results to this file", "make this work with the add-in", or uploads a non-SmartModel planning workbook. Ships a source profiler, a hand-off validator and an automatic hand-off gate — structure validator, workbook audit (broken refs, circular references, orphans, hard-codes, identities), Excel-integrity checks (no repair prompt, no circular references, no broken colour bands) and a driver flex test — that must pass before delivery.
---

# Drivepointify Models

**Purpose**: Convert a planning workbook the customer built themselves (a department budget, a channel
P&L, an inventory plan) into a SmartModel tab that the Drivepoint add-in, plan sync and scenario tools
can use — **without** losing the customer's logic and **without** the reviewer having to point out
structural problems.

**Prerequisite**: load `smartmodel-protocol` (grammar, chrome, marker strings, colours).
For a whole-company model migration (many templates, imports, R-GL wiring), this skill covers the
per-tab conversion; the wider programme is a model migration.

**Scripts** (in `scripts/`, Python 3 + openpyxl; the Gate 0 checkers also need lxml):

| Script | When | What it does |
|---|---|---|
| `profile_source.py <src.xlsx> [--sheet S]` | **Before** writing the spec | Finds stacked LY / actuals blocks, pasted "% × base" values, "LY × factor" growth builds, rows that are copies of other rows, `=row + constant` adjustments, shifted date blocks, bridges that skip rows, opening balances that don't roll, labels in the wrong column, duplicate names, copied `Plan Settings` tabs. |
| `drivepointify_engine.py` (import it) | Build | `Model` → `seed()` D-tab, `schedule()` tabs with `row()` templates, `summary()`, `save()` = Index + Settings + chrome + recalc (if the `formulas` package is present) + add-in WebExtension. Colours every cell by role (input / actual / linked / calculated) and closes every schedule with End of Schedule + a hyperlinked Return to Top. Refuses a Key Driver without budget inputs or a Key Result without a formula. New seeds are named `D - `; an existing build's `R - ` seed still works (with a warning). `import_tab()` writes an add-in import R-tab (e.g. `R - GL`) in its own layout, and `ImportTab.sumifs()` reads it. `python3 drivepointify_engine.py --inject-addin file.xlsx` injects the add-in part into any workbook. |
| `gate.py <built.xlsx> [--ties ties.json] [--identities identities.json] [--company-id ID] [--no-flex]` | **Automatic**: `Model.save()` runs it; run it by hand on any file you edited after the build | The whole hand-off gate in one call. Runs the validator, the audit, Gate 0 (`lint_xlsx.py`, `find_circular.py`, `style_gaps.py`), a flex test (every Key Driver budget input ×1.1 on a copy, then recalc: 0 error cells, Actual months unchanged, Key Results move) and, when `drivepoint-smartmodel-service` is on disk (sibling checkout or `$DRIVEPOINT_SMARTMODEL_SERVICE`), `post_validate`. Exits 1 on any failure. Paste its summary lines into the hand-off. |
| `audit_drivepointified.py <built.xlsx> [--identities identities.json]` | Inside the gate; run it alone while fixing | Checks that the workbook **works**, across every formula on every tab. It fails on: a reference to a missing sheet or an out-of-range cell; **circular references** (Tarjan over the full cell graph, with ranges expanded); error values; uncached formulas; Index gaps or duplicate template rows; a split spine or Actual/Forecast boundary; a seed row nothing reads; a Key Driver that moves nothing; numeric literals inside formulas; a Budget Summary cell ≠ Σ spine; and any broken identity from the JSON. It lists single-cell refs to empty cells, which is fine when guarded with `IF(ISNUMBER(…))`. |
| `validate_drivepointified.py <built.xlsx> [--ties ties.json] [--allow-uncalculated]` | Inside the gate | Structure, per tab. Fails on: broken / partial date spine, history not in the spine, stacked blocks under the budget, columns right of the spine, anything but markers in A:B, Key Drivers that are formulas, Key Results that are typed, $ drivers that are a pasted % of another row, errors, uncached formulas, protocol chrome. `--ties` compares every mapped row to the source. |
| `lint_xlsx.py <built.xlsx>` | Inside the gate (last); run alone while fixing | Gate 0a: what Excel **repairs** on open ("We found a problem with some content… Removed Records: Cell information from /xl/worksheets/sheetN.xml"). That covers duplicate or out-of-order cells, bad shared formulas, formulas over Excel's limits, functions missing `_xlfn.`, relationships to missing parts (a deleted `calcChain.xml`), and external-workbook links (Excel's security bar). Names the tab behind each `sheetN.xml`. |
| `find_circular.py <built.xlsx>` | Same | Gate 0b: every **circular reference** Excel would flag. Excel checks every reference, including the IF branch that is never taken. Lists each loop with sample formulas. |
| `style_gaps.py <built.xlsx> [--allow "Tab!COL"]` | Same | Gate 0c: white **gaps in colour bands**, i.e. the header band or a section band breaking off for a few columns because cells there were never styled (typical after moving labels or the spine). |

---

## What "drivepointified" means — the non-negotiables

A drivepointified tab passes all of these. Do not hand off one that doesn't, and do not wait for the
user to ask.

1. **One date spine, in the series.** Row 2 from **K2**: contiguous month-end dates covering history
   **and** the plan (e.g. K = Jan of last year … AH = Dec of the budget year). Actuals and the
   customer's current-year forecast sit in the **same rows** as the budget, to the left of it, fed from a
   seed **D-tab** (`D - <Customer> <Tab> Seed`: Data, the customer's own values) until the add-in import
   takes over. Never name it `R - `: that prefix means an add-in import. **Never** leave a "2026
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
10. **Formatting says what each cell is.** Colour every cell by role: input = blue on grey, actual =
    the workbook's actual colour, linked from another tab = green, calculated = black. Building into
    an existing SmartModel means **its** conventions (read its Home legend; v5 actuals are gold), and
    its Home tab is copied, never rebuilt. Only a real sum is a bold total with a rule above it; %
    rows are italic `0.0%`; column B is grouped. Every schedule ends in **End of Schedule** with a
    hyperlinked **Return to Top**. Format every row down to the last one.
11. **The simplest formula that works.** One formula pattern per row across the forecast months; roll
    up once (one total row per channel, or one SUMIFS on a category), never a hand-listed SUM of a
    dozen cells on other tabs; no `=+`, empty arguments or numeric literals; split anything past ~150
    characters into a labelled helper row. Reuse the template's formula for the same line.
12. **Inputs live on the spine, on the tab that uses them.** A typed number that drives the model is a
    Key Driver row by month, blue on grey. No "assumption constants" blocks read as single cells, and
    no parking sections for the source's hard-keyed plugs: each plug becomes a labelled driver next to
    the line it adjusts, or a finding.
13. **No working notes in the workbook.** Labels say what the line is. No "her"/"his", "src row 79",
    "source row N", `_r79` ids, "manual value", or filenames: provenance goes in the spec. One row per
    GL account.

---

## Excel opens it clean — Gate 0

openpyxl, LibreOffice, the validator above and `post_validate` all accept files that Excel then repairs on open,
warns are circular, or shows with white gaps in the header band. A real conversion shipped all three
(a full-company model: 20,344 duplicate cell records, 728 circular references, then a broken header band after
the fix). The user should never be the one who finds these.

- **One `<c>` record per address, cells in column order within each row.** Any step that moves cells (spine
  remaps, label moves, stacked blocks) merges a cell that lands on an occupied address: the one with
  content wins; with none, the moved cell wins; two with content is a bug, so stop. Excel deletes duplicate
  records and reports only the part name (`sheet3.xml`), and `lint_xlsx.py` maps it to the tab.
- **Deleting `calcChain.xml` also deletes its relationship and content-type override.** A relationship to a
  missing part triggers the same repair.
- **No circular references, including through an untaken IF branch.** `find_circular.py` must report 0.
  Iterative calculation is not a fix. The patterns that keep coming back:

  | Pattern | Fix |
  |---|---|
  | Summary column summing its own row: `SUMIFS(30:30,$2:$2,…)` in F30 | Sum the months only: `SUMIFS($K30:$DZ30,$K$2:$DZ$2,…)` |
  | Checker reading a whole column it sits in: `SUMPRODUCT(($C:$C=…)*CM:CM)` in CM303 | Bound it to the rows above (`$C$16:$C$302`) |
  | Toggle whose other branch feeds back: `IF(mode="Formula", top_down, SUM(children))`, each child a share of this cell | Drop the dead branch; it can never compute |
  | Actual/forecast switch where the actual branch reads a row that reads this one (CAC ↔ new orders) | Read the actual source directly |
  | `INDEX(block,…)` whose block contains the formula | End the block above the formula |

- **Columns a move leaves empty have no style.** Run `style_gaps.py`, and style each empty gap cell like
  the cell that closes the band on its right (the first month column). Pass deliberate one-column fills
  (a divider, a grey input column) with `--allow "Tab!COL"` and name them in the hand-off.
- **No external-workbook links.** Remove unused ones. Ask before removing one that formulas use.
- **Prove the fix moved no numbers.** Recalculate before and after, compare every formula cell, and name
  the cells that changed on purpose.
- **Run Gate 0 last,** after recalculation and after any later pass, on the exact file you hand off. When
  you can, open it once in desktop Excel; if you cannot, say so.

## Workflow

### Phase 0 — Scope with the user, then profile (always)

Ask before building, in one message, and **wait for the answer**, even when you have a
recommendation. Record the answers in the spec:

1. **Tab set.** For each area of their file: keep **their tab** (their layout on our spine, formulas
   and formatting), use **our standard tab** (their numbers mapped in), or a **blend** (ours plus
   their extra sections). Show it as a table: their tab → our tab → recommendation.
2. **Depth.** Where our standard tab has a build their file lacks, ask whether they want it:
   - Wholesale: the bottoms-up retail build (Doors × SKUs per Door × Units per SKU per Week, i.e.
     velocity by SKU, then unit sales by product).
   - DTC / TikTok / Amazon: cohort retention and Sales by SKU.
   - Product: SKU-level landed cost.
   - Payroll: headcount schedule vs their department payroll.
   - Opex: one row per GL account vs vendor lines.
3. **Leftovers.** Anything with no home in our tabs (an assumptions tab, notes): where it goes.

A tab carrying a standard name (DTC, AMZN, Wholesale - <Retailer>, Product, Payroll, Opex, …) must
contain that tab's standard sections from the SmartModel templates, ending in End of Schedule,
unless the user agreed to leave one out.

Cohort blocks follow the template: cohorts start at the spine start, month 0 = initial orders (100%),
later months by months since first order, no pre-spine cohorts, no retention-method comparison on the
tab.

Then profile:

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

Once the Phase 0 scope is confirmed, present the spec in one message and proceed; pause only for
genuine ambiguity (e.g. two inventory bases, the history-vs-column-K conflict above).

### Phase 2 — Build (one script, on the engine)

One build script reads the source's **cached values** with openpyxl (`data_only=True` — never re-type
numbers) and writes the workbook in a single pass with `drivepointify_engine.py`:

```python
import sys; sys.path.insert(0, "<skill>/scripts")
from drivepointify_engine import Model, FMT_PCT, FMT_X, FMT_USD
m = Model(company_id="<tenant id>", company_name="…", model_name="… 2027 Budget",
          spine_start=(2026, 1), months=24, budget_start=(2027, 1), last_actuals=(2026, 8))
seed = m.seed("D - <Co> <TAB> Seed", source_note="<file>, <date>", flags=<Act/For per history month>)
seed.add("dr", "D&R", <FY2026 values>)
t = m.schedule("<TAB>", name="… Schedule", template_id="<co>-<tab>-budget", description="…")
t.section("Discounts & returns", "D&R as % of gross (default = FY2026 ratio).")
t.row("drPct", "driver", "D&R % of gross", ident="<tab>_drPct",
      hist="IFERROR({c}{@dr}/{c}{@gross},0)", values=<the customer's exact %>, fmt=FMT_PCT)
t.row("dr", "result", "D&R", ident="<tab>_dr", hist=seed.cell("dr"), bud="{c}{@gross}*{c}{@drPct}")
m.summary("<TAB>", [("Net Sales", "total", "net", FMT_USD), ("D&R %", "ratio", ("dr", "gross"), FMT_PCT)])
path, recalculated = m.save("<TAB>_2027_Template_drivepointified.xlsx", ties="ties.json")  # runs the gate
```

Tokens: `{c}` this column · `{ly}` same month last year · `{p}` previous column (roll-forwards) ·
`{m1}`…`{m24}` N columns back (trailing averages, e.g. `AVERAGE({m1}{@x},{m2}{@x},{m3}{@x})`) ·
`{@key}` / `{@Tab.key}` row lookup. `{@Tab.key}` returns the **row number only**, so write the sheet
yourself: `'Pool'!{c}{@Pool.total}`. `hist` fills the history months and `bud`/`values` the budget months.
Section order follows the customer's tab.

- A back-reference that falls before the spine start (`{ly}` in year 1, `{m3}` in February) raises.
  Pass `row(..., zero_before_spine=True)` to turn those references into `0`. Do this only when a
  trailing average or LY link over the first months is really meant to count as zero.
- **System data comes from import R-tabs, never a seed tab.** `m.import_tab("R - GL", header, rows)` writes the tab
  exactly as the add-in does: row 1 = the import's headers, data from row 2, wide month columns from K =
  `historicalStartDate`. Fill it with that import's own output: its rendered SQL run in the warehouse, or the
  R-tab of a plan the add-in already refreshed. The first add-in refresh then overwrites it in place.
  Formulas read it through `tab.sumifs("{c}", Financial__Report__Name="5405 Retail Fulfillment")`
  (`__` = space; `"{c}"` = the month column in the same letter). If no import carries the data, write one first
  (custom import: Firestore `table_definitions`) and wire to its `destination_tab`. A `D - ` seed
  (`m.seed()`) is only for values that live in the customer's own file and no system holds, such as their
  typed budget. Never use one for GL, Confido, Shopify or any other data an import can bring.
- **Import criteria live in cells.** `t.param("cust", "Confido customer", "Target")` writes the label in C and the
  value in D. Formulas read `$D${@cust}`, so every account tab has one formula shape.
- **Actual vs forecast months inside the history window:** `row(..., hist=<import SUMIFS>, fcst=<driver formula>,
  fcst_start=(y, m))`. `fcst` fills from `fcst_start` (default: the month after `lastDateActuals`) up to the
  budget. `{b0}` = the first budget month's column (absolute), e.g. a rate that reads its Jan input:
  `fcst="{b0}{@rate}"`. `values=` with one value per spine month types an input across the whole spine.
- **Seed refs:** `seed.cell("key")` gives a direct address (`'R - X Seed'!{c}6`). Use it by default:
  it recalculates 10–100× faster than `seed.ref()`, a whole-column SUMIFS per cell. On a 40-tab model,
  `ref()` makes the `formulas` recalc take hours. Keep `ref()` for the case where the add-in's import
  will re-order the R-tab rows.
- Guard seed refs for **open months**, where the GL isn't closed yet:
  `IF(ISNUMBER(<seed cell>),<seed cell>,<forecast>)`. This avoids a checker that reads an empty cell as 0.
- **No literals in formulas.** A rate, a share, a year-to-date ratio or a fallback % goes on an input row,
  and the formula references it. The audit fails on stray constants. It allows 0, 1, 2, 3, 7, 12, 100 and 0.5.

### Many entities, one template (retailer / channel / entity P&Ls)

When the brief is "the same P&L for each of N accounts", build **one** template id with many tabs:
call `m.schedule(title, template_id="<co>-retail-account", …)` in a loop. `save()` writes a single
Index row for the template, with the sheets comma-separated; the protocol wants one row per template id.
Then add:
- a **rollup** tab that sums every account tab (plus subtotals by group, e.g. Direct / KeHE / UNFI);
- **pool** tabs for costs the GL can't split by account. Each pool tab publishes one **rate** (cost per
  unit, or % of gross), and each account line is `rate × its own base`: `='Freight Allocation'!W26*W21`.
  Don't put `IFERROR(pool*units/Σunits,0)` on every tab. With a rate, conservation holds by construction.
  A pool's history is one seed link. Compute any seeded forecast months (e.g. a trailing average) in the
  build, labelled; don't nest `IF(ISNUMBER(seed),…,AVERAGE(…))` in every cell. Say in the spec which base
  allocates each pool. An account that doesn't carry a line gets an **unmarked** `=0` row with the reason
  in its label, never a Key Result constant;
- a **hierarchical rollup**: All = group subtotals (3 terms), each group = its tabs' same row. Not 3D sums:
  the `formulas` recalc can't parse `'A:B'!W22`, and tab reorders break them;
- a **checker** tab: model vs source system vs GL by month. A gap is a finding, not a plug;
- an `identities.json` for the gate. It covers the row identities per tab (net = gross + deductions,
  GP = net − COGS, CM = GP − opex), rollup = Σ tabs, and every pool fully allocated (pool total = Σ the
  account allocation rows). Pass it to `save(..., identities=...)`:

```json
[{"type": "row", "name": "cm = gp − opex", "sheets": "Retail - *", "lhs": "contributionMargin",
  "rhs": [["+", "grossProfit"], ["-", "operatingCosts"]]},
 {"type": "sum", "name": "freight fully allocated", "target": "Freight Allocation!freight_fulTotal",
  "sources": "Retail - *!ful", "tol": 1}]
```

Ids match exactly or by the suffix `_<id>`; `sheets` and `sources` take globs. `"missing_as_zero": true`
counts an id a tab doesn't carry (the unmarked `=0` line) as 0.

**Keep every formula one idea long.** Passing the gate doesn't make a model simple. Before hand-off,
count the nested IFs, the `IFERROR`s and the longest formula per tab. A checker's difference row
subtracts the two rows above it, with the source total seeded, not re-added from 35 cells. A reviewer
sent back a retailer model that passed every gate as "extremely complex". The rewrite cut its longest
checker formula from 962 characters to 68 and changed no revenue number.

If the customer's own "model" is a spec workbook (reference tables plus orange tabs with no formulas
linking them), build the brief's design. Read the reference tables (prices, unit costs, customer lists)
as data. Don't convert the tabs cell by cell.

### Phase 3 — Recalc + chrome + gate (one call)

`Model.save(path, ties=..., identities=...)` recalculates when the `formulas` package is installed,
injects the add-in WebExtension, and **runs the hand-off gate on the saved file**. The report prints
and is kept on `m.gate_ok` / `m.gate_report`. Pass `strict=True` to raise instead. Pass `gate=False`
only when a later step edits the file; then run `python3 scripts/gate.py` on the final file yourself.
The flex step needs the recalculated file, so it is skipped when recalc didn't run. Without `formulas` (e.g. a chat sandbox without package installs) the file is saved
with `fullCalcOnLoad`: the user must open it in Excel, press `Ctrl+Alt+F9`, and save **before** uploading,
because the add-in reads uncached formulas as NaN.

### Phase 4 — Read the gate, fix, rebuild

The gate already ran in `save()`. Re-run it by hand after any edit:

```bash
python3 scripts/gate.py <built.xlsx> --ties ties.json --identities identities.json --company-id <tenant>
```

- **Write `ties.json` from the build script, computed independently of the model.** Aggregate the
  source CSVs or cells yourself (pandas, a dict). Never read the model's own output back as the
  expected value. A relative `source` resolves against the ties file's folder.
- Tolerance is for **documented source rounding** only. Example: a source system whose Net column
  carries cents of rounding against its own revenue − trade. Write the reason into the spec.
- `ties.json` covers **every** mapped row: budget columns vs the source budget range, history columns
  vs the source LY range, plus summary cells vs the source totals.
- **0 FAIL required.** Explain every WARN in the hand-off (e.g. "growth factors have no history — expected").
- No formula engine available: run with `--allow-uncalculated` (the spine is evaluated from its formulas so
  structure is still checked). Value checks and ties then need the recalculated file — say so in the hand-off.
- Also re-open the file and eyeball the first screen of each tab: labels in C, dates in row 2, blue
  input cells only on Key Driver budget months.
- **Gate 0, last, on the exact file you deliver:**
  ```bash
  python3 scripts/lint_xlsx.py <built.xlsx> && python3 scripts/find_circular.py <built.xlsx> \
    && python3 scripts/style_gaps.py <built.xlsx>
  ```
  All three exit 0 (see "Excel opens it clean").
- **Re-run the whole gate after every later pass** on the model, not only after the first build.

### Phase 5 — Hand-off message

Lead with what changed and why it's safe:
1. Scope: the Phase 0 answers, and anything left out on purpose.
2. Layout (spine range, where the budget starts, the seed tab, the summary tab).
3. Key Drivers / Key Results per tab — name the drivers.
4. What was a pasted value and is now a driver.
5. Validation: paste the gate's summary. For example: "N values tie to your file. Gate PASS: validator
   0 fail, audit 0 fail, Excel opens without repair, 0 circular references, no colour-band gaps (allowed: …),
   flex test 0 errors, post_validate 0 errors."
6. Findings in their file (bridge gaps, basis mismatches, shifted blocks) — with the numbers.
7. How to load it: upload as a plan in the Drivepoint app (Plans → Upload Plan); the add-in shows it
   as a SmartModel only after that registration.
8. After upload, if the Drivepoint MCP connector is available, confirm Drivepoint itself reads it:
   `list_company_plans` → `get_valid_plan_tabs` (every schedule tab must be listed) →
   `list_plan_key_drivers_and_results` (every marked row must come back with its id and label).

## In Claude chat (claude.ai / Desktop)

Works when the conversation has **file upload + code execution** and this skill (the SmartModel plugin)
is loaded: upload the customer's .xlsx, run the profiler, build with the engine, validate, and return
the file. Chat users who only have the Drivepoint MCP connector get the procedure as the
`drivepointify-models` skill via `get_skill`; without code execution Claude can plan the conversion
and check a registered plan with the connector tools, but cannot write the workbook.

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
- Did the user confirm the tab set and depth (Phase 0)? Does every standard-named tab have its sections?
- Is every cell coloured for what it does, in the workbook's own convention? Any run of bold "totals"?
  Any row left unformatted? End of Schedule + Return to Top on every tab?
- Could a customer read every formula? One pattern per row, no `=+`, no 12-tab SUMs?
- Any "her", "src row", filename or parking section left in a label?
- Does Gate 0 pass on the file I am handing over: no Excel repair, 0 circular references, no colour-band
  gaps, no external links? Did I re-run it after the last edit and the recalc?
- Did the gate print **PASS** on the exact file I'm delivering (not an earlier build)?
- Does changing a driver move the budget and leave the Actual months alone (the flex line)?
- For multi-entity models: rollup = Σ tabs, and is every pool fully allocated (identities)?

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
| Their layout kept under our tab names | DTC / AMZN / Product lost their SKU, cohort and cost builds; reviewer can't find the Drivepoint tab | Phase 0 scope; standard sections |
| Every cell that touched a seed painted one green | Actuals, links and calcs look the same; file "opens wrong" | Non-negotiable 10; engine role colours |
| Rebuilt Home / v6 colours in an existing v5 model | Orange where the model uses gold; Home doesn't look like Drivepoint | Copy the host Home; its legend |
| Assumption constants and "manual values" parked at the bottom of each tab | Inputs not on the spine; plugs invisible; nothing styled as input | Non-negotiable 12 |
| "her" / "src row 79" / duplicate GL rows in labels | Working notes shipped to the customer | Non-negotiable 13 |
| Cohort month 0 dropped (`IF($C<K$2,…)`) | Repurchase rates never start at 100% | Cohort rule in Phase 0 |
| Seed named `R - …` | Reads as an add-in import | `D - ` prefix; engine refuses `R - ` |
| Cell moves wrote a second record onto occupied addresses | Excel: "Removed Records: Cell information from /xl/worksheets/sheet3.xml" on open | Merge on move; `lint_xlsx.py` |
| `calcChain.xml` deleted, its relationship kept | Excel repair prompt | Remove both; `lint_xlsx.py` |
| Budget Summary `SUMIFS(30:30,…)` / IF toggles feeding back | Circular-reference warning on open, even through untaken branches | Bound the ranges; drop dead branches; `find_circular.py` |
| Labels moved F:J → C:G, H:J left without cells | White gap in the blue header band and every section band | Style each gap cell like the band; `style_gaps.py` |
| Unused external link inherited from the customer file | Excel's "links to external sources" bar on every open | Remove it; `lint_xlsx.py` |
| `recalculated=False` with `formulas` installed | openpyxl ≥3.1 writes `<v></v>`; the cache writer only matched `<v/>` and shipped uncached files | Fixed in the engine; a test asserts recalc |
| One Index row per tab for a shared template | The protocol wants one row per template id | `save()` merges; audit `INDEX` |
| Hard-coded rate in a formula (`*0.0262`) | A reviewer can't find or change it; it silently goes stale | Put it on an input row; audit `HARDCODE` |
| Forecast % carried from the last actual month | A one-month spike becomes the run-rate (broker % Aug → Sep–Dec) | Use a Jan–YTD ratio, or read the row's first budget input |
| Checker reads an open-month GL cell as 0 | A false gap in the month the GL isn't closed | `IF(ISNUMBER(…))` guard; audit `REFS` lists empty targets |
| Unit cost / price missing for a SKU → $0 COGS | The margin looks great and is wrong | Proxy from a sibling SKU or the source's implied value, labelled "(implied)", and list it as a finding |
| `seed.ref()` SUMIFS on a 40-tab model | The `formulas` recalc runs for hours | `seed.cell()` direct refs |
| Raw data on a seed tab built from CSV exports | Can't refresh; the reviewer can't trace it ("where is this pulling from?") | `import_tab()` in the add-in layout + `sumifs()`; a custom import where none exists |
| Gate-clean but "extremely complex" (nested `IF(ISNUMBER)`, per-tab `IFERROR(pool*x/Σx)`, 35-term checker chains) | Nobody can audit or change it | Pool rate × base; seed the source totals; hierarchical rollup; measure formula length |
| Section note starting with "=" | Written as a formula → `#REF!` | Start notes with a word; the gate's CALC catches it |
