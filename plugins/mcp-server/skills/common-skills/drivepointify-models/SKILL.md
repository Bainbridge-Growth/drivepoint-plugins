# Drivepointify Models — turn a customer's own spreadsheet into a SmartModel

How to convert a planning workbook the customer built themselves (a department budget, a channel
P&L, an inventory plan) into a Drivepoint SmartModel tab, keeping every one of their numbers,
and how to check the result with this server's model tools once it is uploaded.

Read this whenever the user uploads a non-Drivepoint Excel file and asks to "drivepointify" it,
"make it Drivepoint compatible", "turn it into a SmartModel", "add key drivers and results", or
"make it work with the add-in".

---

## What you need in this conversation

| Capability | Why | Without it |
|---|---|---|
| The uploaded .xlsx + **code execution** (Python with openpyxl) | You read the customer's cached values and write the new workbook | Plan the conversion (mapping table, drivers, findings) and hand the plan back; do not pretend to produce a file |
| The Drivepoint connector (this server) | Verify the uploaded model is read correctly (`get_valid_plan_tabs`, `list_plan_key_drivers_and_results`) and fix markers (`search_plan_row`, `mark_key_driver_or_result`) | Skip Step 6 and tell the user to verify in the add-in |
| The SmartModel plugin's `drivepointify-models` scripts (Claude Code / Desktop) | `profile_source.py`, `drivepointify_engine.py`, `validate_drivepointified.py` do Steps 1, 4 and 5 for you; `lint_xlsx.py`, `find_circular.py`, `style_gaps.py` do the Step 5 Excel-integrity checks | Write the equivalent code from the rules below |

Say "model", not "plan", to the user.

---

## The rules (a converted tab that breaks one of these is not done)

1. **One date spine, with history in it.** Row 2 from column **K**: consecutive month-end dates,
   `K2 = EOMONTH(Settings!$D$7,0)` then `=EOMONTH(<prev>2,1)`. The spine covers the customer's history
   (actuals + their current-year forecast) **and** the budget, e.g. K = Jan 2026 … AH = Dec 2027.
   History sits in the **same rows** as the budget. Never leave a "last year" / "actuals" block stacked
   under the budget. If the user asked for "the budget to start at column K" and the file has history,
   tell them up front that history must sit in the timeline, so the budget starts later (e.g. column W).
2. **Row 3** = `=IF(<col>2<=Settings!$D$14,"Actual","Forecast")` across the spine. C2 = `End of Period`,
   C3 = `Period Type`. **Nothing** in rows 2–3 right of the last date. The model sync rejects a row-3
   value without a row-2 date.
3. **No Total / LY / variance / 1H-2H columns next to the months.** Put them on a separate
   `Budget Summary` tab that SUMIFS the spine by period (FY history vs FY budget, variance, quarters,
   halves; balances take the period-end value).
4. **Rebuild the logic; do not move cells.** Test every typed budget number:
   - equals base × the same % every month → the **% is the Key Driver**, the $ row is a Key Result
   - equals base × a different round % each month → monthly % Key Driver
   - equals base × another row's monthly % → that % row is the Key Driver
   - equals same-month last year × a factor (or pastes a growth block) → **growth-factor Key Driver**
   - identical to another row → link it
   - `= last-year row + a constant` → last-year link + an **adjustment Key Driver**
   - opening balance hard-keyed → Beginning = prior month's Ending, plus an explicit adjustment row for any gap
   - flat / irregular $ the planner typed → $ Key Driver
   - totals, net, margins, KPIs → Key Results (formulas)

   Every rebuilt budget value must still equal the customer's number.
5. **Key Driver vs Key Result by meaning.** A driver is an assumption a planner changes, and its budget
   months are inputs. A result is computed, and its budget months are formulas. A driver may show its
   implied value (result ÷ base) in the history months.
6. **Columns A:B hold markers and ids only.** A = `•⚡ Key Driver` or `  ⚡ Key Result` (exact strings,
   the second with two leading spaces), B = a unique id (e.g. `whl_drWholesalePct`), C = the friendly
   name. Move labels the customer typed in column B into C. Marked rows need unique names: rename a
   second "Total" to "Total Distribution Expense". Calc and memo rows get no marker and no id.
7. **History comes from a seed tab**, `D - <Company> <TAB> Seed` (D = Data: the customer's own values),
   laid out on the same spine, with ids like `seed___grossWhl` in column B. Schedule history cells read
   `=SUMIFS('D - … Seed'!K:K,'D - … Seed'!$B:$B,"seed___grossWhl")`. Never name it `R - …`: that prefix
   means an add-in import. Leave C3 blank on the seed (no `Period Type` / Actual-Forecast row) so the
   model sync and Roll Forward never treat it as a model tab.
8. **Protocol chrome.** Tabs: Index, Settings, the schedule tab(s), Budget Summary, the seed tab.
   - **Settings**: row 1 header is literally `id | Setting | Value | Description` in B:E (capital V and
     D; otherwise every setting reads blank). Required rows:

     | Cell | Setting | Value |
     |---|---|---|
     | D2 | `settings.smartmodelSpec` | `6.0`, as text |
     | D6 | `settings.modelStartDate` | first day of the transition month |
     | D7 | `settings.historicalStartDate` | first spine month |
     | D8 | `settings.companyId` | the Drivepoint tenant id (from `get_drivepoint_user` or the company context) |
     | D14 | `settings.lastDateActuals` | last booked month-end |

     Dates must be real Excel dates.
   - **Schedule tab metadata**: B9 `metadata___name`, B10 `metadata___template_id`,
     B11 `metadata___template_version`, B12 `metadata___description`, B13 `metadata___type`, with the
     values in D.
   - **Freeze and file hygiene**: freeze panes at K5. Do not copy the source's hidden `Plan Settings`
     tab; it points at the customer's original file.
9. **Formatting says what each cell is.** Input = blue on grey, actual = the workbook's actual colour,
   linked from another tab = green, calculated = black. Converting into the customer's existing
   SmartModel means **its** conventions (its Home legend: v5 actuals are gold) and its Home tab,
   copied, not rebuilt. Only a real sum is a bold total with a rule above; % rows are italic `0.0%`;
   column B is grouped; every row is formatted; every schedule ends in **End of Schedule** with a
   hyperlinked **Return to Top**.
10. **The simplest formula that works.** One formula pattern per row across the forecast months; roll
   up once (a total row per channel, or one SUMIFS on a category), never a hand-listed SUM of a dozen
   cells on other tabs; no `=+`, empty arguments or numeric literals.
11. **Inputs on the spine; no working notes.** A typed number that drives the model is a Key Driver row
   by month on the tab that uses it. No "assumption constants" blocks and no parking sections for the
   source's plugs. Labels say what the line is: no "her"/"his", "src row 79", ids like `_r79`, or file
   names. One row per GL account.
12. **Ties are proof.** Every mapped row must equal the source in every month of both years, and the
   summary must match the customer's own totals. A difference is a finding: fix yours, report theirs.
   Examples of theirs: a 1H/2H bridge that skips a line, an opening balance on a different basis, a
   sub-block dated one month off.
13. **Excel opens it clean.** The file must open in Excel without a repair prompt, without a
   circular-reference warning, and without white gaps in the header band. openpyxl and LibreOffice do
   not report any of these:
   - one cell record per address, cells in column order (a step that moves cells must merge a cell
     that lands on an occupied address: content wins);
   - deleting `calcChain.xml` also deletes its relationship and content-type override;
   - no circular reference, including through an IF branch that is never taken. Excel checks every
     reference. Budget Summary sums cover the months only (`SUMIFS($K30:$DZ30,$K$2:$DZ$2,…)`, never
     `SUMIFS(30:30,$2:$2,…)` in the same row); a checker never reads the whole column it sits in; a
     toggle never has a branch that feeds back into itself;
   - every column inside a header or section band is styled with the band, including columns a move
     left empty;
   - no external-workbook links.

---

## Steps

0. **Scope, and wait for the answer.** Ask the user, for each area of their file: keep **their tab**
   (their layout on our spine and formatting), use **our standard tab** (their numbers mapped in), or a
   **blend**. Also ask where our tab has a build their file lacks: the wholesale bottoms-up build
   (Doors × SKUs per Door × Units per SKU per Week), DTC / Amazon cohort retention and Sales by SKU,
   SKU-level product cost, headcount vs department payroll, GL-account vs vendor opex rows. Give your
   recommendation, but let the user decide. A tab with a standard name carries that tab's standard
   sections. Cohort blocks: month 0 = initial orders (100%), cohorts from the spine start.
1. **Profile.** Load the source twice with openpyxl (formulas, and `data_only=True` for values). Find
   every 12-month header row. The first block is the budget; blocks flagged Act/For or titled LY are
   history. For each typed budget row, run the rule-4 tests against every other row. List: stacked
   blocks, pasted %, growth builds, copies, `row + constant` adjustments, openings that don't roll,
   date rows that start in a different month than the header, SUM bridges that skip a row, labels in
   column B, duplicate names, the columns after the months.
2. **Spec.** One line per source row: source row → model row, Key Driver / Key Result / calc, budget
   formula or driver value, history source. Then the spine (range, budget start), every profiler
   finding with its decision, and what the Budget Summary replaces. Once the Step 0 scope is confirmed,
   show this and proceed; stop only for a genuine ambiguity.
3. **Build** with openpyxl in one script. Read the numbers from the source's cached values, never
   re-type them. Write the tabs in order: Index, Settings, schedule(s), Budget Summary, seed.
4. **Recalculate.** If a formula engine is available (for example the `formulas` package), compute and
   store cached values. Otherwise save with full-calc-on-load and tell the user to open the file in
   Excel, press Ctrl+Alt+F9 and save **before** uploading, because uncalculated formulas read as blank.
   Then add the add-in parts to the zip. openpyxl drops them, so do this after the last save:
   - `xl/webextensions/webextension1.xml` — a `we:webextension` with
     `<we:reference id="wa200007015" version="6.0.16.0" store="en-US" storeType="OMEX"/>`
   - `xl/webextensions/taskpanes.xml` — a `wetp:taskpane` (dockstate right, visibility 0, width 350)
     with a `wetp:webextensionref` to `rId1`
   - `xl/webextensions/_rels/taskpanes.xml.rels` — `rId1` → `webextension1.xml` (type
     `http://schemas.microsoft.com/office/2011/relationships/webextension`)
   - In `_rels/.rels`, add a relationship of type
     `http://schemas.microsoft.com/office/2011/relationships/webextensiontaskpanes` to
     `xl/webextensions/taskpanes.xml`.
   - In `[Content_Types].xml`, add overrides for both parts
     (`application/vnd.ms-office.webextension+xml`,
     `application/vnd.ms-office.webextensiontaskpanes+xml`).
5. **Validate before you answer.** Check in code, not by eye:
   - spine contiguous from K2, with nothing after it in rows 2–3
   - Actual months present and ending at lastDateActuals
   - no month-name / Act-For / date rows below row 4
   - nothing right of the spine
   - A:B only markers and ids
   - every Key Driver typed in every budget month, every Key Result a formula
   - no $ Key Driver that is an exact % of another row
   - unique names in C
   - every value tied to the source
   - every cell coloured for its role, no runs of bold "totals", End of Schedule + Return to Top on
     every tab, no working notes in labels, one formula pattern per row
   - rule 13, on the exact file you return, after the last save and after the add-in parts are added:
     parse each sheet's XML for duplicate or out-of-order cells; check every relationship target
     exists; build the formula dependency graph (all IF branches, ranges, whole rows and columns) and
     find its cycles; look for unstyled gaps inside fill bands. With the SmartModel plugin, run
     `lint_xlsx.py`, `find_circular.py` and `style_gaps.py`, which must all exit 0.

   Report the counts, e.g. "912 monthly values and 20 totals tie; 0 structural failures; opens without
   repair, 0 circular references". Re-run the
   whole check after every later pass on the model, not only after the first build.
6. **After the user uploads it** (Drivepoint app → Plans → Upload Plan):
   - `list_company_plans` to find the new model.
   - `get_valid_plan_tabs`: every schedule tab must be listed. If one is missing, its row 2/3 spine is
     wrong.
   - `list_plan_key_drivers_and_results` for those tabs: every marked row must come back with its id
     and name.
   - To fix a marker on the live model: `search_plan_row` finds the row, then
     `mark_key_driver_or_result` (with confirm) sets it.

## Answer format

Lead with what changed:
- the scope the user confirmed in Step 0
- the timeline (range, where the budget starts, the seed tab, the summary tab)
- the Key Drivers and Key Results per tab, naming the drivers, and which pasted values became % or
  growth drivers
- the validation counts
- what you found wrong in their file, with numbers
- how to upload it

Keep it short. The file is the deliverable.
