---
name: make-drivepoint-ready
description: Take an existing Excel model as-is and make the minimum Drivepoint structure so it connects, syncs, and rolls forward — without rebuilding the customer's formulas. Use when a user says "make this Drivepoint ready", "make this model work with Drivepoint", "add the settings tab", "fix the date spine", "why won't this tab show up / sync", or uploads a model that already has its own logic. For a full rebuild (Key Drivers re-derived, Budget Summary, ties) use drivepointify-models instead.
---

# Make Drivepoint Ready

**Purpose**: Keep the customer's model and its formulas. Any `.xlsx` already connects as a plan. Change only what stops Drivepoint from publishing or syncing, then prove nothing else moved.

**Prerequisite**: load `smartmodel-protocol` for marker spelling and the Settings header.

**Not this skill**: if the user wants their logic rebuilt into real Key Drivers / Key Results, a Budget Summary, or history stitched into one series, use `drivepointify-models`.

---

## What upload prep already does

Prep runs on upload **by default**, unless the file already has `settings.companyId` and at least one column A marker containing `Key Driver` or `Key Result`.

Prep injects only:

- a minimum `Settings` tab
- a `Key Drivers + Results` tab (this tab **is synced**; it is not on the roll-forward ignore list)
- the Drivepoint add-in web extension

Prep does **not** rewrite other customer sheets. It does not add an Index tab, insert header rows, restyle tabs, or rename `R -` sheets.

If the customer already has a tab named `Settings`, prep renames it `Settings (original)`. Blank values, and the placeholder `flavorfusion`, for `companyId`, `companyName`, and `stores` are filled from the tenant. Every other non-blank value stays.

Do not redo that work by hand. Do not delete or rewrite sheets prep left alone.

---

## What Drivepoint actually checks

### Errors — these break Drivepoint

| Break | What happens |
|---|---|
| Settings header cannot be read. Row 1 must contain the literals `id` and `Value` (capital V). A lowercase `value` makes every setting blank | Add-in reads every setting blank |
| Duplicate Settings ids | Settings tab invalid |
| A date setting stored as text (`modelStartDate`, `lastDateActuals`, and the other date ids) | Publish skipped, or the date is unreadable. Excel dates and serials are fine |
| `settings.companyId` belongs to another tenant | Sync fails (`mismatch_company_id`). A blank id only skips publish |
| Row 3 says `Actual` or `Forecast` in a column with no row-2 date | Sync fails (`unexpected_model_date_spine`) |
| Formulas have no cached values | Sync and the add-in read NaN or blank |
| Dangling pane selections | Excel repair prompt on open |

### Warnings — report them, never block and never "fix" them as if the model were broken

Missing `Settings` or `Index`. Missing protocol ids (`smartmodelSpec`, `modelVersion`, `modelName`, `modelType`, `companyName`, `author`, `authorId`). Gridlines. `#REF!` and other formula errors. Calculation mode. Freeze position (templates use K5, the layout stamper uses D5; either is fine). Tab color. A history shorter than 12 months. There is **no** 12-month history minimum.

`settings.smartmodelSpec = "6.0"` turns on v6 add-in behaviour (template skills and imports). Plan sync does not read it. A file without it still connects.

### Publish, when the errors above are clear

The plan still connects without these. Publish is skipped until they exist:

- `settings.companyId` equal to the tenant or a company-group id
- `settings.modelStartDate` as an Excel date or serial
- at least one timeseries tab

### Timeseries tabs

A timeseries tab has dates in row 2 and `Actual` / `Forecast` under those dates in row 3. Drivepoint finds schedules by the header labels `End of Period` (C2) and `Period Type` (C3), **not** only by a yellow tab. Customer schedules are often not yellow. Sync reads column A and column B on those tabs:

- Column A matches the substrings `Key Driver` and `Key Result`. The bullet, lightning, and spacing are house style.
- Column B is the metric id: unique on the tab, no `.` and no `___`. Anything else left in column B becomes a junk metric. The friendly name is column C.

Row 3 may use either date. Both pass:

- `=IF(<col>2<=Settings!<lastDateActuals>,"Actual","Forecast")` — drivepointify's formula, usually `Settings!$D$14`
- `=IF(<col>2<Settings!<modelStartDate>,"Actual","Forecast")` — usually `Settings!$D$6`

Sync parses Settings by id, not by row. Only a gap of **more than one month** between `lastDateActuals` and `modelStartDate` is flagged. Which cell Roll Forward writes is still open, so do not rewrite a working row-3 formula from one of these into the other.

These names are never timeseries: `Settings`, `Plan Settings`, `Home`, `Drivepoint Agent Log`, `Key Drivers and Results`, and any name containing `R -` or `F -`. **`Key Drivers + Results` is not on that list** — the `+` tab is the one prep adds, and it syncs.

### v6 channels

Unpicked v6 channels are hidden and zeroed in Settings (`qsPct*` and the per-channel rates). The share of the channels that were picked is rescaled. Tabs are never deleted. Create recalculates cached formula values through the SmartModel service. TikTok has no v6 schedule tab: `tiktok-revenue` can be picked, and there is no sheet to hide.

---

## Workflow

### 1. Ask (one message, wait)

1. Which tabs should Drivepoint read? Mark each schedule, report, data, or ignore. Guess from `End of Period` / `Period Type`, not from tab color.
2. The Drivepoint tenant id and company name, if they are not already in Settings.
3. The first forecast month (`modelStartDate`) and the last booked month (`lastDateActuals`), if the file does not already say.

### 2. Audit (read only)

One table. Mark each row PASS / FAIL / WARN. FAIL is only the error list above.

Also report:

- Whether prep would still run (no `companyId`, or no Key Driver / Key Result marker).
- A customer tab named `Settings`, and whether it should become `Settings (original)`.
- `companyId` / `companyName` / `stores` that are blank or `flavorfusion`.
- Which row-3 formula the file uses (`lastDateActuals` or `modelStartDate`). Leave a working one alone.
- Hidden channel tabs. Those are unpicked channels, not deleted ones. Do not unhide or delete them unless the user asked.
- A copied hidden `Plan Settings` tab (it pins another file's SharePoint id). Dropping it is safe.

Show the audit and wait for a go-ahead before editing.

### 3. Fix only FAILs, and only the cells that fail

- **Header.** If `id` / `Value` cannot be read, write the header literals `id`, `Setting`, `Value`, `Description` in B:E. Do not restyle the rest of the sheet.
- **Settings values.** Fill blank or `flavorfusion` `companyId`, `companyName`, and `stores` from the tenant. Leave every other non-blank value. Dates are Excel dates or serials, never text. Do not invent `author` / `authorId` or move `modelStartDate` to a different row to satisfy an older rule.
- **Customer Settings tab.** Rename it `Settings (original)` with Excel's rename so formulas follow. Then let the Drivepoint `Settings` tab be the one with `settings.*` ids.
- **Row 3 without a date.** Clear the stray `Actual` / `Forecast`, or give that column a real row-2 date. Do not rebuild the spine.
- **Cached values.** Recalculate and save so every formula has a cached value. On the Create path the service recalculates; a file you edit by hand still needs a real calc before upload. A LibreOffice round trip drops the web extension, so do not use one to recalc.
- **Broken panes.** Clear dangling pane selections. Do not move the freeze to K5 or D5.
- **Markers.** On rows the user wants stored, set column A to a `Key Driver` or `Key Result` marker and column B to a unique id. Move labels out of column B into C. Do not mark rows the user did not ask to store.
- **Do not** insert rows or columns, rewrite other customer sheets, add an Index, force yellow tabs, turn gridlines off, demand 12 months of history, or delete a channel tab.

If rows or columns really must move, insert them in Excel (desktop Excel, or Office.js `range.insert`) so references follow. Never use openpyxl `insert_rows` / `insert_cols`.

### 4. Re-audit and hand off

Re-run the audit. Every former FAIL is PASS. Warnings stay listed as warnings.

Tell the user:

1. What changed, tab by tab, and what prep will still inject on upload.
2. The audit table.
3. Before and after values for the totals they care about. A change is a bug in the fix.
4. How to load it: Plans → Upload Plan, with prep left on. If the Drivepoint connector is available, confirm with `get_valid_plan_tabs` and `list_plan_key_drivers_and_results` (sync reads the column A/B markers).

---

## Why it fails

| Symptom | Cause | Fix |
|---|---|---|
| Plan connects, nothing publishes | No `companyId`, no `modelStartDate`, or no timeseries tab | The publish gates above. The plan is still connected |
| Every setting blank | Header `value` is lower case, or ids are not in column B | Header literals `id` and `Value` |
| Upload blocked, company mismatch | `companyId` is another tenant, or still `flavorfusion` | Tenant id. Blank and `flavorfusion` are filled from the tenant |
| Sync throws on the date spine | `Actual` / `Forecast` in a column with no row-2 date | Clear it, or put a date above it |
| Tab missing from sync | Name is on the ignore list, or it has no `End of Period` / `Period Type` headers | It is not yellow-tab detection. `Key Drivers + Results` should be present and is not ignored |
| Hundreds of junk metrics | Labels left in column B | Move them to C. Sync reads column B as the id |
| NaN in the add-in | No cached formula values | Recalculate. Create does this through the service |
| Months don't flip on roll forward | Row 3 is typed, or it reads a date cell Roll Forward does not write | Keep whichever of the two formulas the file already uses. Do not switch a working one |
| Excel repair on open | Dangling pane selection, or a duplicate cell record | Clear the pane. Do not "fix" this by restyling |
