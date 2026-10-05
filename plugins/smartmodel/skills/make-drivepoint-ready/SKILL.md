---
name: make-drivepoint-ready
description: Take an existing Excel model as-is, audit it against what Drivepoint actually reads, and make the minimum changes so it works as a Drivepoint model — Settings tab, a formula-driven date spine on row 2 from column K, Actual/Forecast on row 3, markers and ids in columns A:B, and Drivepoint header formatting. Does not rebuild the customer's logic. Use when a user says "make this Drivepoint ready", "make this model work with Drivepoint", "add the settings tab", "fix the date spine", "why won't this tab show up / sync", "audit this model for Drivepoint", or uploads a model that already has its own logic and only needs the Drivepoint structure. For a full rebuild (Key Drivers re-derived, Budget Summary, ties) use drivepointify-models instead.
---

# Make Drivepoint Ready

**Purpose**: Keep the customer's model and its formulas. Change only the structure Drivepoint reads, then prove nothing else moved.

**Prerequisite**: load `smartmodel-protocol` for the marker strings and colours.

**Not this skill**: if the user wants their logic rebuilt into real Key Drivers / Key Results, a Budget Summary, or history stitched into one series, use `drivepointify-models`.

---

## What Drivepoint checks (the contract)

These are the rules the server enforces. A tab that breaks any one of them is silently skipped or fails plan sync.

**Settings tab** (named exactly `Settings`)
- Row 1 header in B:E is literally `id`, `Setting`, `Value`, `Description`. Column A is empty.
- Column B is the id (`settings.<name>`), C is the label, D is the value, E is the description. The server reads these columns by position.
- An id must appear once. A duplicate marks the whole tab invalid.

**Schedule tabs** (every tab that should sync or roll forward)
- The tab must not be very hidden. Hidden is fine.
- The name can't contain `Settings`, `Home`, `R - GL`, `I - Metadata`, `Key Drivers and Results` or `Drivepoint Agent Log`, and it can't start with `R -` or `F -`. These match anywhere in the name, so a tab called "Homepage Revenue" is skipped.
- **C2** is exactly `End of Period` and **C3** is exactly `Period Type`: typed text, not formulas, no extra spaces.
- **Row 2**: the dates start at **K2**. From there to the last filled cell of the row, every cell is a month-end date, one month apart, with no gaps, text or Total columns.
- **Row 2 and row 3 must be formulas.** Plan sync reads only formula results in these rows. Typed dates or typed `Actual` cells make sync fail with "row 2 must be dates, row 3 must be the Forecast/Actual markers…". The Roll Forward list accepts typed values, so a tab can show up there and still fail sync.
- **Row 3**: under every date, exactly `Actual` or `Forecast`, computed from row 2 and the ProForma Start Date. Nothing goes in row 3 to the right of the last date; any value there makes sync throw an error.
- **Columns A and B**:
  - Column A holds only `•⚡ Key Driver`, `  ⚡ Key Result` (two leading spaces), `•`, or nothing.
  - **Every non-empty cell in column B below row 3 becomes a metric id.** A label the customer typed in B turns into a junk metric.
  - Ids are unique on the tab. They contain no `.` and no `___`, because the server would read them as a setting or metadata id.
  - The friendly name the server stores for each row comes from column C.

**Workbook**
- Every formula has a cached value. The add-in reads an uncalculated cell as NaN, so the file must be recalculated and saved in Excel before upload.
- `settings.companyId` is the Drivepoint tenant id. A different tenant's id **blocks** the upload; everything else here only produces warnings.
- No hidden `Plan Settings` tab copied from another file, because it pins that file's SharePoint id.
- A missing `M - Monthly` tab is a warning, not a blocker. Say so; don't create one.

---

## Workflow

### 1. Ask (one message, wait for the answer)

1. Which tabs should Drivepoint read? List every tab with your guess: schedule, report, data, or ignore.
2. The Drivepoint company id (tenant id) and the company name.
3. The **ProForma Start Date**: the first forecast month.
4. The **Historical Start Date**: the first month of history.
5. The **3-Year Plan View Start Date**. The default is the January of the ProForma Start year.

### 2. Audit (read only, before changing anything)

Report one table per tab, with every rule above marked PASS / FAIL and the exact cells:

| Check | Result | Where / why |
|---|---|---|
| Name not on the ignore list | PASS | |
| C2 / C3 literals | FAIL | C2 is blank; dates are in row 1 |
| Spine from K2, month-end, contiguous | FAIL | Months in B1:M1, typed; a `Total` column in N |
| Row 2 / 3 are formulas | FAIL | Typed dates |
| Row 3 compares its own row-2 date with `settings.modelStartDate` | FAIL | R3 reads the `settings.lastDateActuals` cell, not `settings.modelStartDate`; W3 is typed |
| Nothing in row 3 after the last date | PASS | |
| A:B markers and ids only | FAIL | Labels in A4:A60, account codes in B |

Also report:
- The Settings tab: missing, present, or a customer tab that happens to be called `Settings`.
- Any copied `Plan Settings` tab.
- `INDIRECT` or other text-built references. These won't follow an insert; list every one.
- Anything to the right of the months (totals, notes): it stays, but rows 2 and 3 above it stay empty.

Show the audit and the planned changes, then wait for a go-ahead.

### 3. Fix, in this order

**a. Settings.**
- If there is no Settings tab, create it as the second tab, with tab colour dark grey (`404040`) and gridlines off.
- If the customer has their own tab called `Settings`, rename theirs first (for example `Model Settings`) using Excel's rename, so formulas follow the new name.
- Write or update these rows. Leave any other existing rows alone.

| id | Setting | Value |
|---|---|---|
| `settings.modelVersion` | Model Version | `1.0.0` (text, `x.y.z`) |
| `settings.modelName` | Model Name | e.g. `Acme 2027 Budget` |
| `settings.modelStartDate` | ProForma Start Date | real date, first day of the first forecast month |
| `settings.historicalStartDate` | Historical Start Date | real date, first day of the first history month |
| `settings.threeYearPlanViewStartDate` | 3 Yr Plan View Start Date | real date |
| `settings.lastDateActuals` | Last Date Actuals | real date, last day of the month before ProForma Start |
| `settings.companyId` | Company ID | tenant id (text) |
| `settings.companyName` | Company Name | text |
| `settings.stores` | Stores | Shopify store names, or the company id if none |
| `settings.currency` | Currency | `USD` |

- Dates are real Excel dates formatted `yyyy-mm-dd`, never text.
- Delete a copied `Plan Settings` tab.

**b. Make room, with Excel's own insert only.** Insert rows and columns in Excel (desktop Excel, or Office.js `range.insert(...)` through the add-in) so every formula, name, chart and validation follows. **Never use openpyxl `insert_rows` / `insert_cols` or write cells into new positions**: they don't update references, and the model breaks silently.
- If rows 1–3 are not already valid Drivepoint chrome or contain any customer content, insert 3 rows at the top. The customer's existing rows move down and stay as they were.
- If the first used column on the tab is A or B, insert columns at A until it is C.
- If the first month column is then left of K, insert columns just before it until it is K.
- If there is a Total, quarter or half-year column **between** months, stop and ask. It has to move to the right of the months, or the tab can't pass.

**c. Rows 1–3.** On each schedule tab:
- A1 `≡`. C1 is the tab's display name.
- C2 `End of Period`. K2 is `=EOMONTH(DATE(<y>,<m>,1),0)` for the tab's first month; every cell after it is `=EOMONTH(<previous>2,1)`, across exactly the month columns.
- C3 `Period Type`. Under every date: `=IF(K2<Settings!$D$<row of settings.modelStartDate>,"Actual","Forecast")`.
  - The column letter is the cell's own column, and the Settings reference is absolute.
  - The row number is the row where `settings.modelStartDate` actually sits; look it up, don't assume it.
  - Overwrite any existing row 3 formula that reads something else: a typed date, `lastDateActuals`, `TODAY()`, or another tab's row 3.
- Clear rows 2 and 3 from A to J (except the C labels), and everything to the right of the last month.

**d. Columns A:B.** Below row 3:
- Move anything that isn't a marker or an id out of A:B, into C or a free column on the left. Use cut and paste or insert so references follow.
- For each row the user wants stored, set the column A marker:
  - **Key Driver**: typed inputs in the forecast months.
  - **Key Result**: formulas in the forecast months.
  - Headers, blanks and memo rows get no marker and no id.
- Set the column B id, built from the label: lower case, letters, digits and `_` only, prefixed with a short tab slug (`opex_rent`). Make it unique on the tab.
- Make the column C labels of marked rows unique ("Total" → "Total Opex").

**e. Drivepoint format.**
- Row 1: fill `64B1FF`, white text.
- Row 2: black fill, white bold text, dates formatted `mmm-yy`.
- Row 3: fill `808080`, white text.
- Fill all three rows from A to the last month.
- Schedule tabs: tab colour yellow (`FFC000`), gridlines off.
- Column B: Menlo 10.
- Spine cells on marked rows:
  - Forecast inputs: blue `4472C4` on grey `F2F2F2`.
  - Actuals: orange `ED7D31`.
  - Links to another tab: green `548235`.
  - Calculations: black.
- `%` rows are italic `0.0%`.
- Don't restyle anything else the customer did.

### 4. Recalculate, re-audit, prove nothing moved

- Recalculate fully (Ctrl+Alt+F9) and save in desktop Excel.
- Re-run the step 2 audit. Every check must PASS.
- Check row 3 cell by cell on every tab. Each cell's formula reads the row 2 cell directly above it and the `settings.modelStartDate` value cell. Its result is `Actual` for every month that ends before the ProForma Start Date and `Forecast` from that month on.
- Prove row 3 follows the setting: move `settings.modelStartDate` forward one month, recalculate, and confirm exactly one more month flips to `Actual` on every tab. Then put it back.
- Compare the key totals the customer cares about (revenue, EBITDA, ending cash; ask for them in step 1 if needed) before and after. Any change is a bug in the fix, not a rounding difference.
- If the file was edited outside Excel (for example with openpyxl), run the Gate 0 checkers from `drivepointify-models/scripts/` on the exact file you hand off: `lint_xlsx.py` (no repair prompt), `find_circular.py`, `style_gaps.py`.

### 5. Hand-off

1. What changed, tab by tab: rows and columns inserted, rows marked, Settings written.
2. The audit table again, now all PASS.
3. Before and after totals.
4. What was left as-is on purpose: totals to the right of the months, `INDIRECT` formulas to check by hand, and no `M - Monthly` tab if there isn't one.
5. How to load it: upload it in the Drivepoint app (Plans → Upload Plan). If the Drivepoint MCP connector is available, confirm with `get_valid_plan_tabs` (every schedule tab is listed) and `list_plan_key_drivers_and_results` (every marked row comes back).

---

## Why it fails (seen in practice)

| Symptom | Cause | Fix |
|---|---|---|
| Tab missing from Roll Forward | Name hits the ignore list, C2/C3 text off, gap or Total in row 2, or mid-month dates | Rules above |
| Shows in Roll Forward, sync fails on "row 2 must be dates…" | Row 2 or 3 typed instead of formulas, or a value in row 3 after the last date | Formula spine; clear past the last date |
| Roll forward runs but months don't flip to Actual | Row 3 typed, or reading something other than `settings.modelStartDate` | Row 3 formula on its own row-2 date vs `settings.modelStartDate` |
| Hundreds of junk metrics after sync | Labels or codes left in column B | Move them to C |
| "Not a SmartModel" / every setting blank | Header `value` lower case, or ids not in column B | Exact header literals in B:E |
| Upload blocked "Company mismatch" | `settings.companyId` from another tenant | Set the right tenant id |
| Numbers changed after the fix | Rows or columns inserted outside Excel | Redo the inserts in Excel |
| NaN everywhere in the add-in | File saved without recalculation | Recalculate and save in Excel |
