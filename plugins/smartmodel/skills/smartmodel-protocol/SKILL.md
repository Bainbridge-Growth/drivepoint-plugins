---
name: smartmodel-protocol
description: Loads the SmartModel Protocol v6.0 grammar. Use when working with any Drivepoint SmartModel Excel workbook — reading structure, populating data, navigating sheets, rolling forward, or answering questions about financial model content.
user-invocable: false
allowed-tools: Read Grep Glob
---

# SmartModel Protocol Skill — v6.0
**Issuer**: Drivepoint (drivepoint.io)
**Hosted at**: `https://raw.githubusercontent.com/Bainbridge-Growth/drivepoint-plugins/main/plugins/smartmodel/skills/smartmodel-protocol/SKILL.md`
**Loaded by**: Drivepoint Excel add-in on workbook open
**Purpose**: Teach any AI agent the SmartModel grammar so it can read, navigate, assist with, and populate Drivepoint SmartModel workbooks

---

## What is a SmartModel?

A SmartModel is an Excel (`.xlsx`) workbook. Any `.xlsx` connects to Drivepoint as a plan. The grammar in this document — identifiers in column B, storage markers in column A, a date spine in row 2, a Settings tab — is the house convention. Most of it is optional. When `settings.smartmodelSpec = "6.0"`, the add-in turns on v6 behaviour: it reads each sheet's `metadata___template_id`, fetches the corresponding skills and import declarations, and passes them to the agent. Plan sync does not read `smartmodelSpec`. A workbook without it still connects.

The agent's job is to help users understand their model, populate it with data, roll it forward in time, diagnose errors, and answer questions about the business metrics it represents.

### What Drivepoint actually requires

Upload prep runs by default unless the file already has `settings.companyId` and a column A marker containing `Key Driver` or `Key Result`. Prep injects a minimum Settings tab, a `Key Drivers + Results` tab, and the add-in web extension. It does not rewrite other customer sheets, and it does not add an Index. A customer tab already named `Settings` is renamed `Settings (original)`. Blank values, and the placeholder `flavorfusion`, for `companyId`, `companyName`, and `stores` are filled from the tenant. Other non-blank values stay.

**Errors** — these change what Drivepoint does:

- Settings header cannot be read. The header literals are `id` and `Value` (capital V). A lowercase `value` makes every setting blank.
- Duplicate Settings ids.
- A date setting stored as text. Excel dates and serials are fine.
- `settings.companyId` belonging to another tenant. Sync fails. A blank id only skips publish.
- `Actual` or `Forecast` in row 3 with no row-2 date.
- Formulas with no cached values. Sync and the add-in read NaN or blank.
- Dangling pane selections. Excel asks to repair the file.

**Warnings** — report them, never block on them: missing Settings, missing Index, missing protocol ids (`smartmodelSpec`, `modelVersion`, `modelName`, `modelType`, `companyName`, `author`), gridlines, `#REF!`, calculation mode, freeze position. There is no 12-month history minimum.

**To publish**, the workbook also needs `settings.companyId` (the tenant or a company-group id), `settings.modelStartDate`, and at least one timeseries tab. Without them the plan still connects and the publish is skipped.

A timeseries tab has dates in row 2 and `Actual` / `Forecast` under those dates in row 3. Row 3 may compare the row-2 date with `settings.lastDateActuals` or with `settings.modelStartDate`. Both pass. Only a gap of more than one month between those two dates is flagged. Drivepoint finds schedules by the header labels `End of Period` and `Period Type`, not only by a yellow tab. Sync reads column A and column B on those tabs: column A matches the substrings `Key Driver` and `Key Result`; column B is a unique id with no `.` or `___`.

Never treated as timeseries: `Settings`, `Plan Settings`, `Home`, `Drivepoint Agent Log`, `Key Drivers and Results`, and any name containing `R -` or `F -`. The prep tab `Key Drivers + Results` is synced on purpose. It is not on that list.

**v6 channels.** Unpicked channels are hidden and zeroed in Settings (`qsPct*` and the per-channel rates), never deleted. Create recalculates cached formula values through the SmartModel service. TikTok has no v6 schedule tab.

For the minimum-edit path (keep the customer's formulas), load `make-drivepoint-ready`. For a full rebuild, load `drivepointify-models`.

---

## File Structure

A SmartModel xlsx is a standard Excel zip archive. The file's job is to be a well-structured workbook — skills and import declarations live on the server, fetched at runtime by the authenticated add-in.

**What's in the file:**

| Component | Purpose |
|-----------|--------|
| Settings tab | Model identity, protocol version, configuration |
| Index tab | Template registry — lists all templates and their sheets |
| Schedule sheets | Primary financial modeling sheets. Found by `End of Period` / `Period Type`, not only by a yellow tab |
| Report sheets (blue) | Derived output reports |
| R- sheets (default) | Data import layer — one per import declaration |
| WebExtension | Embedded add-in reference (prompts install from AppSource) |

**What's on the server** (fetched by the add-in via Drivepoint API):

| Component | Purpose |
|-----------|--------|
| Protocol skill | Universal SmartModel grammar (this document) |
| Template skills | Template-specific instructions (one per template) |
| Import declarations | Data source definitions for each template's R- sheets |
| AI context | Additional context the agent needs for the specific model |

The WebExtension is the only custom content injected into the xlsx zip structure beyond standard Excel files. It references the Drivepoint add-in on Microsoft AppSource, enabling automatic add-in discovery when the workbook is opened.

---

## Sheet Types and Tab Colors

Drivepoint-built workbooks use this tab color system. Color is convention. A schedule that is not yellow still syncs when it has `End of Period` and `Period Type`:

| Tab Color   | Sheet Type  | Purpose |
|-------------|-------------|--------|
| White       | Index       | Table of contents — first tab users see |
| Yellow      | Schedule    | Primary financial schedule sheets (forecasting, planning) |
| Blue        | Report      | Output reports and summaries |
| Default     | R- sheets   | Data import layer — one per import declaration |
| Dark gray   | Settings    | Machine-readable configuration, add-in owned |

**Index tab**: Human-readable table of contents. Shows registered templates, sheet ownership, data sources, and import status. Maintained by the add-in.

**Schedule tabs**: Where the primary financial modeling happens. Formula-driven. Reference R- sheets for live data. These are the sheets users interact with most.

**Report tabs**: Derived outputs. Reference schedule sheets. Read-only for most users.

**R- sheets** (tab name contains `R - `, with spaces, e.g. `R - GL`): Data import layer. One R- sheet per import declaration. Populated by the add-in from connected data sources, or manually by the user. Template formula sheets reference R- sheets dynamically via Excel formulas. The agent does not need to declare wiring between templates — connections are discerned at runtime by reading the formula layer. A name containing `R - ` or `F - ` is never a timeseries tab.

**Settings tab**: Machine-readable key-value configuration. Column A is reserved/empty; columns B–E carry the header `id`, `Setting`, `Value`, `Description` (capital V and D — see Settings Tab Structure). Sync reads this tab. Do not overwrite a non-blank value. Blank or `flavorfusion` `companyId`, `companyName`, and `stores` are filled from the tenant. A customer's own Settings tab is renamed `Settings (original)`.

---

## Settings Tab Structure

The Settings tab stores model configuration as a key-value table. The agent reads this tab to understand the model's identity and operational parameters.

**Column layout**: Column A is reserved (narrow, empty). Data starts at column B:
- Column B: `id` — dot-notation identifier (monospace font), e.g. `settings.smartmodelSpec`
- Column C: `Setting` — human-readable label
- Column D: `Value` — the stored value
- Column E: `Description` — explanatory note

**Header row (row 1) literals are `id`, `Setting`, `Value`, `Description` — capital V and D.** The add-in
locates the id and value columns by scanning for a header row that contains the literal strings `id` and
`Value` (`ModelSettings.findHeaderColumnIndices`). If it finds none it falls back to fixed offsets inside the
used range, and because column A is empty that reads column C as the id and column E as the value: every
`settings.*` parses blank and the workbook is reported as "not a Drivepoint SmartModel". A lowercase `value`
header is a defect, not a style choice.

Standard settings fields. Only `companyId` and `modelStartDate` gate the warehouse publish. `smartmodelSpec = "6.0"` switches on v6 add-in behaviour. The rest are conventional. Blank or `flavorfusion` `companyId`, `companyName`, and `stores` are filled from the tenant during prep; other non-blank values stay. Sync parses by id, not by row number.

| ID | Setting | Value |
|----|---------|------|
| `settings.smartmodelSpec` | Protocol Version | `6.0` |
| `settings.modelVersion` | Model Version | semver (e.g., `1.0.0`) |
| `settings.modelName` | Model Name | Human-readable string |
| `settings.modelType` | Model Type | `"template"` or `"model"` |
| `settings.modelStartDate` | ProForma Start Date | Date |
| `settings.historicalStartDate` | Historical Start Date | Date |
| `settings.companyId` | Company ID | Drivepoint company ID |
| `settings.companyName` | Company Name | Company name string |
| `settings.currency` | Currency | Default `USD` |
| `settings.author` | Author | Author name |
| `settings.authorId` | Author ID | Author identifier |

Settings IDs use dot notation (`settings.fieldName`). These are distinct from the identifier system used inside schedule sheets, which uses triple-underscore notation (described below).

`settings.smartmodelSpec = "6.0"` turns on v6 add-in behaviour (template skills and imports). It is not the gate for connecting a plan or for sync.

---

## Sheet Grammar — How to Read a Schedule Sheet

Schedule sheets follow a strict row-by-row structure. Once you understand this grammar, you can navigate any SmartModel schedule sheet.

### The Header Block (Rows 1–8)

These rows are structural chrome that frames the sheet.

**Row 1 — Title bar**: Light blue background (`#64B1FF`), white text. Column A contains `≡` (section marker). Column C contains `=D9` (formula that displays the template name). Every cell has light blue background and white text — no exceptions.

**Row 2 — Date spine**: Black background, white bold text. Column C is labeled "End of Period". Starting at column K, each cell contains a month-end date formatted as `mmm-yy` (e.g., "Jan-24"). Dates extend right for the full time horizon (typically 48 months). This is the authoritative time axis for the entire sheet.

**Row 3 — Period type**: Gray background (`#808080`), white text. Column C is labeled "Period Type". Starting at column K, each cell contains either "Actual" or "Forecast" — right-aligned to visually correspond with the dates above. This tells you which columns contain historical data vs. forward projections.

**Row 4 — Status bar**: Very light gray background. Column A contains a blue bullet `•`. Column C contains a status message (e.g., "No Errors"). This row is maintained by the add-in.

**Rows 5–6**: Blank spacing.

**Row 7 — Template title**: Contains `=D9` in column C (bold, 14pt, black). A thick blue border (`#63AEFF`) runs along the bottom from column B to the last data column. This is a visual section divider.

**Row 8 — Template description**: Gray italic text in column C. Brief description of the template's purpose.

### The Metadata Block (Rows 9–15 typical)

Row 9 is critical. It anchors the entire template identity system:

- `B9` = `"metadata___name"` (monospace font — always)
- `C9` = `"Name"`
- `D9` = The actual template name string (e.g., `"13-Week Cash Flow"`) — **this must be a string value, not a formula**

Rows 10–15 contain additional metadata fields following the same pattern:
- Column B: identifier in monospace font, using `metadata___` prefix with triple underscores
- Column C: human-readable label in standard font
- Column D: value in standard font

Standard metadata fields:

| Row | Identifier | Example Value |
|-----|-----------|---------------|
| 9 | `metadata___name` | `"13-Week Cash Flow"` |
| 10 | `metadata___template_id` | `"13wk-cashflow"` |
| 11 | `metadata___template_version` | `"1.0.0"` |
| 12 | `metadata___description` | `"Weekly cash forecast..."` |
| 13 | `metadata___grain` | `"weekly"` |

`metadata___template_id` and `metadata___template_version` are how the add-in discovers which templates are present in the workbook. The add-in scans all sheets for `metadata___template_id` values, collects the unique IDs, and fetches the corresponding skills and import declarations from the server.

Other common metadata fields: `metadata___type`, `metadata___created`, `metadata___framework`.

**Column B rule**: Every cell in column B across the entire sheet uses monospace font (Menlo, size 10, black). This applies universally — metadata identifiers, settings identifiers, dimension identifiers, measure identifiers, data row identifiers. This is how you identify the machine-readable layer.

### The Settings Block (Rows 17–21 typical)

Sheet-level settings that control template behavior. Same three-column pattern as metadata:
- Column B: `settings___` prefix, triple underscores, monospace font
- Column C: human-readable label
- Column D: value (dates formatted `yyyy-mm-dd`)

Settings IDs are **always plural**: `settings___fy1_end_date`, not `setting___fy1_end_date`. This is non-negotiable.

A special setting `settings___identifier_structure` documents the pattern used to construct row identifiers in the data section (e.g., `pattern: "{dimension-slug}_{measure-code}"`).

### Dimension and Measure Registries

Before the data section, the sheet declares its dimensions and measures. These serve as the catalog of what the template models.

**Dimension registry**: Lists the dimensional entities (e.g., SKUs, channels, regions). Each row has:
- Column B: `dim_` prefix identifier (e.g., `dim_sku_1`) in monospace
- Column C: human-readable name (e.g., "SKU: Hydrating Face Serum")

**Measure registry**: Lists all metrics tracked. Each row has:
- Column B: `measure_` prefix identifier (e.g., `measure_orders`) in monospace
- Column C: human-readable name (e.g., "Orders")

Each registry section begins with a section header row (bold, 14pt, thick blue bottom border) and a subheader row (gray italic description), then a blank row, then data rows.

### Data Sections

The substantive modeling content. Each data section covers a category of metrics (e.g., "Orders & Revenue", "COGS", "Operating Expenses").

**Section header pattern** (3 rows):
1. Header row: bold 14pt black text in column C, thick blue border (`#63AEFF`) bottom from B to last column
2. Subheader row: gray italic description in column C
3. Blank spacing row

**Data rows**: Each row in a data section tracks one dimension × measure combination across the time horizon.

---

## Data Row Anatomy

This is the most important grammar element to understand. Every data row has four zones:

```
Col A  │  Col B                          │  Col C               │  Col K → last
───────┼─────────────────────────────────┼──────────────────────┼─────────────────
marker │  identifier formula             │  human label         │  time-series data
```

**Column A — Storage marker**: Determines whether this row is stored to the database and how users interact with it. Three possible values:

- Blank: a supporting or calculation row. Not stored.
- `⚡ Key Driver`: Stored to database as a **user input**. These are the cells the user edits to drive the model.
- `⚡ Key Result`: Stored to database as a **calculated result**. These cells contain Excel formulas — never hardcoded values.

The add-in writes the marker when the user marks a row (right-click → Drivepoint 2.0 → Enable key driver / key result); it may write a leading `•` or spaces before the `⚡`. **Match on the text `Key Driver` / `Key Result`, never on the exact string.** There is no separate blue `•` assumption-dot step and no standalone `•` marker: the add-in no longer needs it, so never tell a user to add one.

**Column B — Identifier**: Contains a formula that generates the row's machine-readable identifier string. Example: `="hydrating-serum_orders"` — this displays the string `hydrating-serum_orders`. The identifier follows the pattern declared in `settings___identifier_structure`: `{dimension-slug}_{measure-code}`. Always monospace font.

**Column C — Label**: Human-readable description of what this row represents. Standard font.

**Columns K onward — Time series**: Actual or forecast values across the date spine defined in row 2.
- Actual columns (historical): contain reported values
- Forecast columns: **Key Driver** rows have editable cells (light gray background, blue-ish text) for user input; **Key Result** rows contain Excel formulas referencing their driver rows

### Total / Aggregation Rows

When meaningful (for additive measures like revenue, orders, spend — not for rates or percentages), a section closes with:
1. A blank separator row with a thin auto-color bottom border
2. A total row: `  ⚡ Key Result` marker, bold label in column C, SUM formulas in data columns

The separator border uses `'thin'` style, not `'thick'`.

---

## Cell Role Styling

Every cell on a schedule sheet carries a visual cue that signals its **role** — whether it's a user input, an imported value, an actual financial value extracted from the source of truth, or a calculated output. The role catalog is identical across every SmartModel template.

| Role | Where it appears | Visual cue | Semantic |
|------|------------------|-----------|----------|
| `assumption_above_marker` | Column A below assumption blocks | Blue arrow `↑` (`#4472C4`), no fill | Indicates assumption rows above may be collapsed for display. |
| `actual` | Actual-period time-series cells | Orange text (`#ED7D31`), no fill | Value extracted from the customer's accounting source of truth. Read-only — never overwrite. |
| `input` | Forecast-period cells on Key Driver rows | Blue text (`#4472C4`) on light grey fill (`#F2F2F2`) | User input. Editable. |
| `imported_input` | Forecast cells where a value has been backfilled from an import | Green text (`#548235`) on light grey fill (`#F2F2F2`) | Input that has been "actualized" — still editable but sourced from an import. |
| `imported_value` | Cells whose formula references another sheet | Green text (`#548235`), no fill | Reference to another schedule or tab. Avoid overwriting unless intentional. |
| `calculated` | Formula outputs on Key Result rows | Black text (`#000000`), no fill | Calculated value. Should rarely be overwritten with direct input. |

**Reading roles**: Identify a cell's role by its font color and fill. Treat `actual` and `imported_value` as read-only when reporting state to the user; treat `input` and `imported_input` as user-editable.

**Writing roles**: When writing a value, the cell's existing role must match what you're writing. Never repaint a cell to a different role — the role encodes data lineage, not display preference. Writing a forecast value into an `actual` cell is a structural error.

---

## Identifier Naming Conventions

The identifier system is how the add-in and agent address specific data points. The conventions are strict:

| Prefix | Usage | Example |
|--------|-------|--------|
| `metadata___` | Metadata fields (triple underscore) | `metadata___name` |
| `settings___` | Settings fields (triple underscore, always plural) | `settings___fy1_end_date` |
| `dim_` | Dimension registry entries | `dim_sku_1` |
| `measure_` | Measure registry entries | `measure_orders` |
| `{dim-slug}_{measure-code}` | Data row identifiers | `hydrating-serum_orders` |

**Triple underscore separator** (`___`): Used exclusively in metadata and settings identifiers. This is intentional — it visually and programmatically distinguishes structural metadata from data-layer identifiers.

**Dimension slugs**: Hyphenated lowercase. Derived from the dimension name (e.g., "Hydrating Face Serum" → `hydrating-serum`).

**Measure codes**: Camelcase or snake_case depending on the template's declared `settings___identifier_structure`.

---

## Formula Reference Rules

The agent must understand how formulas connect the sheet together:

- `C1` and `C7` always contain `=D9` — they display the template name
- `D9` always contains the template name as a **string value** (never a formula)
- Data row result cells reference input cells in the same column (e.g., `K51 = K49 * K50`)
- Formulas extend across all time-period columns
- R- sheet data is referenced by schedule sheets via standard Excel formulas — the agent reads these to understand data wiring between sheets

---

## Imports System

Import declarations define what external data each template needs. They are served by the Drivepoint API alongside template skills — not bundled in the xlsx file. The add-in fetches them when it discovers template IDs during workbook open.

Each import declaration maps to one R- sheet. The declaration specifies the data source, field schema, time dimension, and query parameters.

There are two fulfillment modes:
- **Without a Drivepoint account**: The add-in fills R- sheets from locally connected raw sources using best-effort matching, or the user populates manually
- **With a Drivepoint account**: The `dp_query` in each import declaration is executed directly against BigQuery with `{project_id}` and `{tenant_id}` injected at runtime

The agent receives import declarations as part of the skill context provided by the add-in. It should consult them to understand what data is available, which R- sheets are populated, and what the time dimension and field schema of each import is.

---

## Operating Principles

### Core Rules

1. **Identify the model.** When a conversation opens or the user asks "what model is this?", call `read_smartmodel_settings`. `companyId` and `modelStartDate` are what publish needs. `smartmodelSpec` only says whether v6 add-in behaviour is on. A file with no Settings still connects.

2. **Find the schedules.** Index is optional and sync does not read it. When an Index exists, call `read_smartmodel_index`. When it does not, find timeseries tabs by the headers `End of Period` and `Period Type`, then read column A/B markers. Do not treat a missing Index as a broken model.

3. **Identify the period type before writing.** Each column in a schedule is either an Actual (historical, locked) or a Forecast (editable) period. Read the date spine with `read_smartmodel_date_spine` before writing any value. Never write to an Actual-period column.

4. **Respect the Key Driver / Key Result distinction.** Sync matches the substrings `Key Driver` and `Key Result` in column A. The bullet, lightning, and spaces are house style. Write only rows whose marker contains `Key Driver`. A marker containing `Key Result` is a formula output — never overwrite it.

5. **Use durable identifiers, not row numbers.** Address cells by their `durable_id` (column B), not by row number. Row positions can shift when templates are added or removed.

6. **Confirm bulk writes.** When a bulk write operation affects more than 10 cells, present a summary to the user and require explicit confirmation before executing.

7. **Read before writing.** Always call a read tool on the target sheet before writing drivers. Verify that the target row has the `key_driver` marker and that the target column is a Forecast period.

8. **Scope changes to the correct template.** Use `read_smartmodel_sheet_metadata` to confirm which template owns a sheet before editing it. Do not mix data across templates.

9. **Report import status before answering data questions.** Use `read_r_sheet` to check whether import sheets (R- prefix) are populated. If an import sheet is empty, tell the user before attempting to answer questions that depend on that data.

10. **Summarise what you read.** After reading any structural data (index, settings, metadata), give the user a brief confirmation of what you found — sheet names, template versions, date range, Actual/Forecast boundary.

11. **Never expose internal identifiers to the user.** Translate `durable_id` values, column letters, and row numbers into friendly names and Excel-notation ranges before presenting information.

### Auto-Orient

When this skill loads, **immediately** make these 3 tool calls before the user's first request. Hold the results as **model context** for the entire session — every subsequent skill uses this context instead of re-reading.

1. **`read_smartmodel_settings`** → capture model identity (`settings.companyName`, `settings.currency`, `settings.modelName`, `settings.modelVersion`, `settings.smartmodelSpec`, `settings.modelStartDate`, `settings.historicalStartDate`)
2. **`read_smartmodel_index`** → capture the full template registry (template IDs, owned sheets, skill references, import references)
3. **`read_smartmodel_date_spine`** on the consolidation sheet (M - Monthly, or the first available schedule sheet) → capture the time range, Actual/Forecast boundary, and most recently closed Actual month

After these 3 calls, the agent knows: what company this is, what currency to use, what sheets exist, what templates are configured, and what time period is current. No other skill should repeat these calls — they reference the model context instead.

If any of these calls fail, follow the Error Handling rules below.

### Quick vs. Full Mode

Before running a skill's full phased workflow, assess whether the user's question actually requires it.

**Quick mode** — If the user's question can be answered with a single data read and a direct response, answer it directly. Do not run a multi-phase analysis for a lookup question.
- "What was March revenue?" → Read the consolidation sheet, return the number with brief context.
- "What's our gross margin?" → Read the relevant row, return the %, note the trend if visible.
- "How many SKUs do we have?" → Read the dimension registry, return the count.
- "When do actuals end?" → Answer from the model context (already loaded).

**Full mode** — Run the complete phased workflow when the user asks for analysis, explanation, comparison, a report, or uses trigger phrases like "why", "what's driving", "compare", "build", "analyze".
- "Why did we miss on revenue?" → Full variance analysis
- "Build me a board report" → Full build-report workflow
- "What's driving our margin decline?" → Full margin analysis

**When in doubt**: Answer the direct question first (quick mode), then offer: "Would you like me to run the full [skill name] analysis?"

### Output Formatting Standards

All skills inherit these formatting rules. Do not restate them in individual skills.

**Number formatting:**
- Use currency from `settings.currency` in the model context (default USD)
- Round to thousands (e.g., $1,245K) for companies with >$10M annual revenue; round to dollars for smaller companies
- Always show both $ and % when presenting variances, margins, or deltas
- Percentages: one decimal place (e.g., 31.6%), except basis point changes which show as integers (e.g., +400bps or +4.0pp)

**Narrative rules:**
- Never present raw data without interpretation — every number needs a "so what"
- Lead with the headline finding, then support with data
- Quantify everything — never say "revenue increased significantly"; say "revenue increased $95K (8%)"
- Be specific about direction: "up", "down", "flat" — not "changed"

**Excel output (when user requests a workbook tab):**
- Report tabs get blue tab color
- Use `write_range` for labels and data, `insert_formula` for computed cells
- Apply `format_range` once per format type (currency, percentage, bold), not per cell
- Call `resize_columns` to fit column widths after writing
- Call `activate_sheet` at the end to bring the new tab into focus

### Error Handling

All skills that depend on the SmartModel Protocol inherit these rules. Skill-specific fallbacks supplement but do not replace them.

**Tool call fails:** Stop and report the error. State what tool was called, the error returned, and whether the analysis can continue without it. Do not guess what the data would have been.

**Required data is missing or empty:** If the data is central to the analysis (e.g., no revenue data for variance analysis), stop and tell the user what is missing and how to populate it. If the data is peripheral, note the gap and continue.

**Write fails mid-construction:** Stop writing. Report what was successfully written and what was not. Do not attempt to undo partial work. Ask the user whether to retry or clean up manually.

**Required sheet doesn't exist:** Check if the data is available on an alternative sheet. If an alternative exists, use it and note the substitution. If not, stop and tell the user which sheet is missing.

### Prior Context Reuse

When multiple skills run in the same session, reuse data already gathered. Do not re-read settings, index, date spine, or data sections that a prior skill already loaded. Each skill should check whether upstream context exists before making tool calls.

### Skill Routing

When the user asks a question that would benefit from a structured workflow, use `load_skill` to load the relevant skill before answering. Use your best judgement — this table is a guide, not a rigid rule:

| User says | Load skill |
|-----------|-----------|
| "why did we miss", "vs plan", "pacing", "variance", "pre-roll", "are we on track" | variance-analysis |
| "margins", "channel profitability", "Amazon vs DTC", "why am I below benchmark" | margin-analysis |
| "what does it cost to make", "COGS breakdown", "landed cost", "unit economics" | product-cost-analysis |
| "which SKUs", "what should we cut", "product mix", "too many SKUs" | sku-rationalization |
| "LTV", "retention", "cohort", "do customers come back", "CAC payback", "repurchase rate" | cohort-analysis |
| "CAC", "ROAS", "marketing efficient", "ad spend", "spending too much on ads" | marketing-efficiency-analysis |
| "inventory", "weeks of supply", "stockout", "reorder", "sell through rate" | inventory-analysis |
| "trade spend", "promos working", "deduction rate", "retailer profitability", "wholesale P&L" | trade-spend-analysis |
| "raise the price of [product]", "increase prices on [SKU]", "increase SKU prices", "price increase on [SKU]", "drop price on [product]", "price change scenario", "pricing scenario", "what would a [X]% price increase do" | price-change-analysis |
| "what if", "scenario", "tariffs", "extend runway", "miss Q2" | create-scenario |
| "compare scenarios", "plan A vs B", "which scenario is better", "budget vs forecast" | compare-scenarios |
| "monthly report", "monthly summary", "monthly recap", "monthly writeup", "monthly close", "do the [month] numbers", "[customer]'s [month] writeup" | monthly-report |
| "board deck", "board report", "investor update", "package this up" | build-report |
| "build a schedule", "revenue build", "COGS schedule", "headcount plan", "payroll tab" | build-schedule |
| "drivepointify", "convert this budget template", "turn this spreadsheet into a SmartModel", "rebuild the drivers", "add key drivers and results" (full rebuild) | drivepointify-models |
| "make this Drivepoint ready", "make this model work with Drivepoint", "add the settings tab", "fix the date spine", "why won't this tab show up / sync" (keep their formulas) | make-drivepoint-ready |
| "what is this", "overview", "stand up the model", "orient" | summarize-model |
| "where does that number come from", "trace", "what's driving that line" | interrogate-model |
| "QA the financials", "QA the GL", "QA R-GL", "QA RGL", "QA the import", "tie out the GL", "reconcile GL", "check NetSuite import", "verify the import for [month]" | qa-financials |
| "audit", "something looks off", "validate", "sanity check", "numbers don't look right" | audit-model |
| "will this break", "can I rename", "is it safe to", "can I hardcode", "what's breakable", "don't-dos", "what should I avoid" | change-safety |
| "clean up", "fix the model", "#REF errors", "broken formulas" | clean-model |
| "slow", "lagging", "file is huge", "speed up", "reduce file size" | optimize-model |
| "investor-ready", "due diligence", "DD prep", "Series A", "data room", "share with VCs" | investor-readiness-analysis |

If the question doesn't clearly match one skill, answer directly from the model data. If the user explicitly asks for an analysis by name (e.g., "run a variance analysis"), always load that skill. For pricing prompts, prefer `price-change-analysis` over `create-scenario` whenever the user mentions a SKU, product, product family, ASP, AOV, discount, price increase, or price decrease.

---

## Multi-Template Workbooks

A Drivepoint-built SmartModel is typically 5–8 templates stitched together in a single workbook. Multi-template workbooks are first-class — each schedule sheet may declare its template via `metadata___template_id`, and an Index tab, when present, lists them. A customer workbook with neither still connects.

**How v6 discovery works, when `settings.smartmodelSpec` is `6.0`:**

1. Workbook opens → add-in reads Settings → `settings.smartmodelSpec = "6.0"` turns on v6 behaviour. Without it, the plan still connects and syncs
2. When an Index exists, the add-in reads its template manifest. Upload prep does not create one, so a brought-in file often has no Index — discover schedules by `End of Period` / `Period Type` instead
3. From that manifest, extracts template IDs, versions, and skill/import file references
4. Fetches skills and import declarations for those templates in one API call
5. Caches skills in memory, passes them to the AI agent on chat open

Cross-template connections are standard Excel formulas — one schedule sheet referencing cells in another. The agent discovers these at runtime by reading the formula layer, not from any configuration file.

---

## Index Tab as Template Registry

When an Index tab exists, it contains a structured template manifest — a table of every template in the workbook. It is a convenience, not a requirement. Sync never reads it. If it is missing, discover timeseries tabs by their headers and column A/B markers.

### Manifest Table Structure

The manifest is a table in the Index tab with the following columns:

| Column | Header | Content |
|--------|--------|--------|
| A | Template ID | Machine-readable identifier (e.g., `dtc-revenue`) |
| B | Version | Semver (e.g., `1.0.0`) |
| C | Sheets | Comma-separated list of owned sheet names |
| D | Skill File | Filename of the template skill (e.g., `dtc-revenue-skill.md`) |
| E | Imports File | Filename of the import declarations (e.g., `dtc-revenue-imports.yaml`) |

Example:

```
Template ID          Version  Sheets                                    Skill File                   Imports File
dtc-revenue          1.0.0    DTC, DTC - OTP, DTC - SUB, DTC - Acq     dtc-revenue-skill.md         dtc-revenue-imports.yaml
amzn-revenue         1.0.0    AMZN, AMZN - OTP, AMZN - SUB             amzn-revenue-skill.md        amzn-revenue-imports.yaml
wholesale-revenue    1.0.0    Wholesale                                 wholesale-revenue-skill.md   wholesale-revenue-imports.yaml
opex                 1.0.0    Opex                                      opex-skill.md                opex-imports.yaml
consolidation        1.0.0    M - Monthly                               consolidation-skill.md       consolidation-imports.yaml
```

### How it's used

- **Add-in**: When the manifest exists and `smartmodelSpec` is `6.0`, reads template ids and fetches skills and imports. A file with no Index still connects.
- **AI agent**: Use the manifest when it is there. Otherwise map the workbook from schedule headers and column A/B markers.
- **Maintenance**: The add-in updates the manifest when templates are added or removed. Do not create an Index just to register a sheet. Upload prep does not add one.

Each schedule sheet may declare `metadata___template_id` in its metadata block. That block is convention. Sync reads the column A marker and the column B id.

---

## Versioning

- **Protocol versioning**: Major.minor (e.g., `6.0`). Breaking grammar changes increment the major version.
- **Template versioning**: Semver (e.g., `1.0.0`). Template skill files and xlsx artifacts are versioned together.
- The protocol version is declared in `settings.smartmodelSpec` in the Settings tab.
- The template version is declared in `settings.modelVersion`.

---

## Quick Reference — Reading a Sheet Cold

When you open an unfamiliar SmartModel schedule sheet and need to orient quickly:

1. **Row 2** → What time periods does this model cover?
2. **Row 3** → Where does Actual end and Forecast begin?
3. **D9** → What is this template called?
4. **Metadata block** → What type, grain, and version is this template?
5. **Settings block** → What fiscal year dates and other parameters are configured?
6. **Dimension registry** → What entities are being modeled?
7. **Measure registry** → What metrics are tracked?
8. **Data sections** → What does column A say? If it contains `Key Driver`, it's user input. If it contains `Key Result`, it's calculated. Blank means a supporting row that isn't stored.
9. **Column B** → What is the machine identifier for this specific row?
10. **R- sheets** → What real data is imported and feeding this model?

---

## Related Skills

### Builders
| Skill | Path | Purpose |
|-------|------|---------|
| Build Schedule | `../build-schedule/SKILL.md` | Construct a new schedule sheet from scratch — data-first flow, any model version |
| Drivepointify Models | `../drivepointify-models/SKILL.md` | Rebuild a customer's own budget / forecast template into a SmartModel tab — one date spine with history, real Key Drivers, profiler + hand-off validator |
| Make Drivepoint Ready | `../make-drivepoint-ready/SKILL.md` | Keep an existing model. Prep and the minimum Settings / marker / spine fixes so it publishes. Does not rewrite other sheets |
| Monthly Report | `../monthly-report/SKILL.md` | Produce the Drivepoint-style monthly summary & variance report for a CPG customer |
| Build Report | `../build-report/SKILL.md` | Create a blue report tab — board reports, monthly close reports, investor updates |
| Create Scenario | `../create-scenario/SKILL.md` | Build a named what-if scenario by adjusting Key Driver assumptions |

### Analysis
| Skill | Path | Purpose |
|-------|------|---------|
| Variance Analysis | `../variance-analysis/SKILL.md` | Actuals vs. plan/forecast with driver decomposition and mid-month pacing |
| Margin Analysis | `../margin-analysis/SKILL.md` | Channel-aware gross and contribution margin decomposition |
| SKU Rationalization | `../sku-rationalization/SKILL.md` | Rank product portfolio by contribution; flag SKUs to invest, maintain, or cut |
| Cohort Analysis | `../cohort-analysis/SKILL.md` | Retention curves + LTV in one consolidated pass |
| Investor Readiness | `../investor-readiness-analysis/SKILL.md` | Audit model for fundraise and due diligence gaps |
| Product Cost Analysis | `../product-cost-analysis/SKILL.md` | COGS decomposition and per-unit economics by SKU |
| Marketing Efficiency | `../marketing-efficiency-analysis/SKILL.md` | CAC, ROAS, blended vs. channel-level spend efficiency |
| Inventory Analysis | `../inventory-analysis/SKILL.md` | Weeks of supply, stockout risk, dead stock, reorder timing |
| Trade Spend Analysis | `../trade-spend-analysis/SKILL.md` | Promotional ROI, deduction rates, retailer-level P&L |
| Price Change Analysis | `../price-change-analysis/SKILL.md` | Sales-mix-weighted AOV updates and COGS pass-through for SKU-level price changes |

### Model Ops
| Skill | Path | Purpose |
|-------|------|---------|
| Summarize Model | `../summarize-model/SKILL.md` | Full workbook orientation — templates, data state, time range, health check |
| Interrogate Model | `../interrogate-model/SKILL.md` | Trace any number back through its formula and driver chain |
| Audit Model | `../audit-model/SKILL.md` | Structural integrity, formula errors, protocol compliance checklist |
| QA Financials | `../qa-financials/SKILL.md` | Tie out a customer's raw GL export against R-GL line-by-line for a given period |
| Change Safety | `../change-safety/SKILL.md` | Pre-flight a proposed edit — what it breaks, checked against this workbook's own formulas |
| Clean Model | `../clean-model/SKILL.md` | Fix errors, restore protocol structure, standardize formatting |
| Optimize Model | `../optimize-model/SKILL.md` | Resolve slow calculation, phantom range bloat, volatile formulas |

### Scenarios
| Skill | Path | Purpose |
|-------|------|---------|
| Compare Scenarios | `../compare-scenarios/SKILL.md` | Side-by-side delta analysis across two or more scenarios or plans |
